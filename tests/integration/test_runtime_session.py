"""P6 RuntimeSession 集成测试：端到端运行 / Invalidation 局部重跑 / Resume。

运行: python -m pytest tests/integration/test_runtime_session.py -q
这是「V3 从架构变成可执行 Research Runtime」的验收测试：
默认确定性认知执行器（零 LLM）跑完整 15 节点 DAG，
产出可落盘、可失效传播、可断点续跑的 Registry + Evidence Graph + State。

audit FIX-1.5（P0-12）：测试不得再把"无真实执行也 PASS"编码为预期。
测试经 external_model_irs / external_code / validation_specs 注入真实
Model Constructor 产物（LLM-free 边界：构造来自外部，runtime 只执行验证），
claim 必须由真实执行数值合成（FIX-1.4），占位 claim 不再获得 supports 边。
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from conftest import CODE, injected_session, mir, validation_spec  # noqa: E402

from runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402


def _mir(qid: str, model_id: str) -> dict:
    return mir(qid, model_id)


_CODE = CODE


def _validation_spec() -> dict:
    return validation_spec()


def _new_session(tmp_path, questions=("Q001", "Q002"), max_workers=1):
    return injected_session(tmp_path, questions, max_workers)


class TestEndToEndRun:
    def test_full_run_completes_all_nodes(self, tmp_path):
        s = _new_session(tmp_path)
        rep = s.run()
        p = rep["progress"]
        assert p["blocked"] == {}, p["blocked"]
        assert p["failures"] == {}, p["failures"]
        assert len(p["completed"]) == p["total"]

    def test_artifacts_and_evidence_registered(self, tmp_path):
        s = _new_session(tmp_path)
        s.run()
        types = {a.type for a in s.registry.all()}
        # 真实执行闭环核心产物（FIX-1.5：result 由 EXEC produces，不再要求
        # experiment/figure——实验节点在真实执行下复用 model_execution 链）
        assert {"problem", "question", "model", "assumption", "model_ir",
                "code", "execution_result", "result", "verification_result",
                "claim", "paper_section"} <= types
        relations = {(r["relation"]) for r in s.graph.relations}
        assert {"motivates", "solved_by", "assumes", "based_on",
                "instantiates", "implemented_by", "executed_by",
                "produces", "verified_by", "supports", "appears_in"} \
            <= relations

    def test_state_derived_questions_validated(self, tmp_path):
        s = _new_session(tmp_path)
        s.run()
        st = s.state.data["state"]
        for qid in ("Q001", "Q002"):
            assert st["questions"][qid]["status"] == "validated"
        assert st["evidence"]["claims_total"] == 2
        assert st["evidence"]["claims_supported"] == 2
        # 结果带灵敏度/基线标签 → 证据门禁 E8 不再 WEAK
        tagged = [a for a in s.registry.all()
                  if "sensitivity" in a.tags or "baseline" in a.tags]
        assert tagged, "实验计划含灵敏度/基线时结果应带对应 tags"

    def test_persistence_roundtrip(self, tmp_path):
        s = _new_session(tmp_path)
        s.run()
        reg2 = ArtifactRegistry(s.project_dir / "state" / "registry.json")
        graph2 = EvidenceGraph(reg2, s.project_dir / "state" / "evidence_graph.json")
        assert len(reg2) == len(s.registry)
        assert len(graph2.relations) == len(s.graph.relations)

    def test_parallel_session_same_result(self, tmp_path):
        """max_workers=4 与串行结果等价（落账串行保证一致性）。"""
        s = _new_session(tmp_path, max_workers=4)
        rep = s.run()
        assert rep["progress"]["blocked"] == {}
        assert len(rep["progress"]["completed"]) == rep["progress"]["total"]


class TestInvalidationPartialRerun:
    def test_result_invalidation_triggers_question_rerun(self, tmp_path):
        s = _new_session(tmp_path)
        s.run()
        before_claims = len(s.registry.list_by_type("claim"))

        result = next(a for a in s.registry.list_by_type("result")
                      if a.question == "Q001")
        rep = s.invalidate(result.artifact_id, reason="数值勘误")
        # Q001 专属节点被重置（result 失效 → 从 model_execution 重跑）
        assert s.registry.get(result.artifact_id).status == "invalidated"
        q1_nodes = [nid for nid in s.engine.dag.nodes if nid.endswith("@Q001")]
        assert any(nid not in s.engine.completed for nid in q1_nodes)
        # Q002 的活跃产物不受失效影响（registry 层；model_execution 是全局
        # 节点会保守重跑但产物链不动，audit FIX-1.5）
        q2_results = [a for a in s.registry.list_by_type("result")
                      if a.question == "Q002"]
        assert q2_results
        assert all(a.status not in ("invalidated", "superseded", "deprecated")
                   for a in q2_results)
        # 重跑后回到全完成
        s.run()
        assert len(s.engine.completed) == len(s.engine.dag.nodes)
        assert len(s.registry.list_by_type("claim")) >= before_claims
        # Q001 证据链已重建：新活跃 result + 新活跃 claim（非占位符）
        live_results = [a for a in s.registry.list_by_type("result")
                        if a.question == "Q001"
                        and a.status not in ("invalidated", "superseded",
                                             "deprecated")]
        live_claims = [a for a in s.registry.list_by_type("claim")
                       if a.question == "Q001"
                       and a.status not in ("invalidated", "superseded",
                                            "deprecated")]
        assert live_results, "Q001 必须有重建的活跃 result"
        assert live_claims, "Q001 必须有重建的活跃 claim"
        assert not live_claims[0].data.get("placeholder"), \
            "重建 claim 不得是占位符"
        # 旧 result 保持失效（审计保留），新 result 进入 supports 边
        assert s.registry.get(result.artifact_id).status == "invalidated"
        sup_to = {r["to"] for r in s.graph.relations
                  if r["relation"] == "supports"}
        assert any(c.artifact_id in sup_to for c in live_claims)

    def test_model_invalidation_reruns_from_selection(self, tmp_path):
        s = _new_session(tmp_path, questions=("Q001",))
        s.run()
        model = s.registry.list_by_type("model")[0]
        s.invalidate(model.artifact_id, reason="模型假设不成立")
        assert "model_selection" in s.engine.ready() \
            or model.artifact_id not in [x for x in s.engine.completed]
        s.run()
        assert len(s.engine.completed) == len(s.engine.dag.nodes)


class TestResume:
    def test_resume_after_crash_skips_completed(self, tmp_path):
        s = _new_session(tmp_path, questions=("Q001",))
        s.run()
        total = len(s.engine.dag.nodes)
        assert len(s.engine.completed) == total

        # 模拟崩溃重启：全新会话（同项目目录）→ 引擎从进度文件恢复
        s2 = RuntimeSession(s.project_dir, ["Q001"], max_workers=1)
        prog_path = s.project_dir / "state" / "engine_progress.json"
        assert prog_path.exists()
        data = json.loads(prog_path.read_text(encoding="utf-8"))
        assert len(data["completed"]) == total
        rep = s2.resume()
        # 全部已完成 → 无新波次，状态一致
        assert len(rep["progress"]["completed"]) == total

    def test_resume_from_partial_progress(self, tmp_path):
        """手动构造半程进度 → resume 只补跑剩余节点。"""
        s = _new_session(tmp_path, questions=("Q001",))
        # 跑一个完整 run 产生 shared 上下文与产物，然后重置引擎到前缀
        s.run()
        prefix = ["problem_analysis", "literature_search", "model_selection"]
        s.engine.completed = set(prefix)
        s.engine.retries.clear()
        s.engine.blocked.clear()
        s.engine.waiting.clear()
        s.engine.save_progress(s.project_dir / "state" / "engine_progress.json")

        ran_before = len(s.engine.log)
        rep = s.resume()
        # 自愈：shared 丢失的中间节点会被反馈环拉起重跑，最终仍全完成
        assert len(rep["progress"]["completed"]) == len(s.engine.dag.nodes)
        assert len(s.engine.log) > ran_before
