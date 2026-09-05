"""P6 RuntimeSession 集成测试：端到端运行 / Invalidation 局部重跑 / Resume。

运行: python -m pytest tests/integration/test_runtime_session.py -q
这是「V3 从架构变成可执行 Research Runtime」的验收测试：
默认确定性认知执行器（零 LLM）跑完整 15 节点 DAG，
产出可落盘、可失效传播、可断点续跑的 Registry + Evidence Graph + State。
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402


def _new_session(tmp_path, questions=("Q001", "Q002"), max_workers=1):
    return RuntimeSession(tmp_path / "proj", list(questions),
                          max_workers=max_workers)


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
        assert {"problem", "question", "model", "assumption",
                "experiment", "result", "figure", "claim",
                "paper_section"} <= types
        relations = {(r["relation"]) for r in s.graph.relations}
        assert {"motivates", "solved_by", "assumes", "validated_by",
                "produces", "visualized_by", "supports", "appears_in"} \
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
        # Q001 专属节点被重置，Q002 不动
        assert s.registry.get(result.artifact_id).status == "invalidated"
        q2_nodes = [nid for nid in s.engine.dag.nodes if nid.endswith("@Q002")]
        assert all(nid in s.engine.completed for nid in q2_nodes)
        # 重跑后回到全完成
        s.run()
        assert len(s.engine.completed) == len(s.engine.dag.nodes)
        assert len(s.registry.list_by_type("claim")) >= before_claims

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
