"""P7 Runtime Integrity & Contract Freeze 验收测试（A–K 清单）。

运行: python -m pytest tests/integration/test_p7_integrity.py -q
对照 docs/architecture/RUNTIME_CONTRACTS.md 的验收映射。
"""

import json
import sys
import tempfile
import threading
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.artifacts.lifecycle import LifecycleError  # noqa: E402
from runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from runtime.contracts import (  # noqa: E402
    can_enter_paper, can_support_claim, is_reusable, is_terminal,
    validate_node_result_outputs,
)
from runtime.decisions.log import DecisionLog  # noqa: E402
from runtime.execution.engine import FAIL, PASS, NodeResult, WorkflowEngine  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402


def _new(tmp_path, questions=("Q001", "Q002"), max_workers=1):
    return RuntimeSession(tmp_path / "proj", list(questions),
                          max_workers=max_workers)


def _snapshot(session):
    """registry/graph/state 拓扑快照（可比较，不含时间戳）。"""
    return {
        "artifacts": sorted(
            (a.artifact_id, a.type, a.status) for a in session.registry.all()),
        "relations": sorted(
            (r["from"], r["relation"], r["to"]) for r in session.graph.relations),
        "questions": {qid: q["status"]
                      for qid, q in session.state.data["state"]["questions"].items()},
        "claims": session.state.data["state"]["evidence"]["claims_total"],
    }


# ============================================================
# A. Fresh Run — 15/15
# ============================================================

class TestAFreshRun:
    def test_fresh_run_completes(self, tmp_path):
        s = _new(tmp_path)
        rep = s.run()
        assert len(rep["progress"]["completed"]) == rep["progress"]["total"]
        assert rep["progress"]["blocked"] == {}


# ============================================================
# B. Wave Execution — 并行 + 依赖序
# ============================================================

class TestBWaveExecution:
    def test_dependency_ordering_preserved_under_parallelism(self, tmp_path):
        s = _new(tmp_path, max_workers=4)
        order = []
        lock = threading.Lock()
        base_exec = s.executor_impl

        def tracing_executor(nid, ctx):
            with lock:
                order.append((nid, frozenset(ctx["completed"])))
            return base_exec(nid, ctx)

        s.engine.executor = tracing_executor
        rep = s.engine.run()
        dag = s.engine.dag
        for nid, done in order:
            for dep in dag.nodes[nid].depends_on:
                assert dep in done, f"{nid} 先于依赖 {dep} 执行"
        assert len(rep["completed"]) == rep["total"]

    def test_parallel_no_duplicate_ids(self, tmp_path):
        """并行波次下多节点同型登记：ID 不重复（P7-并发契约）。"""
        s = _new(tmp_path, questions=("Q001", "Q002", "Q003", "Q004"),
                 max_workers=4)
        s.run()
        ids = [a.artifact_id for a in s.registry.all()]
        assert len(ids) == len(set(ids)), "并行登记产生重复 ID"


# ============================================================
# C + D. Crash / Resume — 无重复完成、无丢失产物、无丢失证据
# ============================================================

class TestCrashResume:
    def test_crash_at_wave_and_resume_consistent(self, tmp_path):
        """跑到一半崩溃（只保留进度文件）→ resume → 世界状态与一次跑完一致。"""
        # 基准：一次跑完
        s_ref = RuntimeSession(tmp_path / "ref", ["Q001", "Q002"])
        s_ref.run()
        ref = _snapshot(s_ref)

        # 崩溃体：跑到 model_selection 完成即"死"
        s = _new(tmp_path / "proj" and tmp_path / "crash", ["Q001", "Q002"])
        for nid in ("problem_analysis", "literature_search", "model_selection"):
            s.engine.step(nid)
        s.engine.save_progress(s.project_dir / "state" / "engine_progress.json")
        s.checkpoint()

        # 重启进程 = 全新会话对象，同项目目录
        s2 = RuntimeSession(s.project_dir, ["Q001", "Q002"])
        s2.resume()
        got = _snapshot(s2)

        # D1: 已完成节点不重复执行（registry 无重复产物，数量一致）
        assert len(got["artifacts"]) == len(ref["artifacts"])
        assert got["artifacts"] == ref["artifacts"]
        # D2: 证据无丢失
        assert got["relations"] == ref["relations"]
        # D3: 状态不倒退
        assert got["questions"] == ref["questions"]
        assert got["claims"] == ref["claims"]

    def test_resume_never_reexecutes_completed_nodes(self, tmp_path):
        s = _new(tmp_path, questions=("Q001",))
        s.run()
        log_len = len(s.engine.log)
        exec_nodes = [e["node"] for e in s.engine.log if e["status"] == "pass"]

        s2 = RuntimeSession(s.project_dir, ["Q001"])
        s2.resume()
        reexecuted = [e["node"] for e in s2.engine.log[log_len:]
                      if e["status"] == "pass"]
        assert not reexecuted, f"resume 重跑了已完成节点: {reexecuted}"
        assert exec_nodes  # 原本确实执行过


# ============================================================
# E. Retry（已在 engine 测试覆盖，此处验端到端闭环）
# ============================================================

class TestERetry:
    def test_retry_loop_converges_to_pass(self, tmp_path):
        s = _new(tmp_path, questions=("Q001",))
        calls = {"n": 0}
        orig = s.executor_impl.do_assumption_check

        def flaky(node_id):
            calls["n"] += 1
            if calls["n"] < 3:
                return NodeResult(FAIL, "暂时性故障")
            return orig(node_id)

        s.executor_impl.do_assumption_check = flaky
        rep = s.run()
        assert calls["n"] == 3
        assert len(rep["progress"]["completed"]) == rep["progress"]["total"]


# ============================================================
# F. Rerun — 显式重跑产生新谱系，旧谱系 superseded 审计保留
# ============================================================

class TestFRerun:
    def test_explicit_rerun_creates_new_lineage(self, tmp_path):
        s = _new(tmp_path, questions=("Q001",))
        s.run()
        old_exp = {a.artifact_id for a in s.registry.list_by_type("experiment")}
        old_claims = {a.artifact_id for a in s.registry.list_by_type("claim")}

        rep = s.rerun("experiment@Q001", reason="参数调整")
        assert "experiment@Q001" in rep["reset_nodes"]

        s.run()   # 补跑受影响下游
        new_exp = {a.artifact_id for a in s.registry.list_by_type("experiment")}
        # 新谱系出现
        assert new_exp - old_exp, "rerun 应产生新实验 Artifact"
        # 旧谱系 superseded（非 invalidated）且保留在 Registry
        for aid in old_exp:
            assert s.registry.get(aid).status == "superseded"
        # 旧 claim 同样被新 claim 替代（链上重跑）
        new_claims = {a.artifact_id for a in s.registry.list_by_type("claim")}
        assert new_claims - old_claims
        for aid in old_claims:
            assert s.registry.get(aid).status in ("superseded", "invalidated")
        # 终态：全图回到一致
        assert len(s.engine.completed) == len(s.engine.dag.nodes)
        st = s.state.data["state"]["evidence"]
        assert st["claims_supported"] == st["claims_total"]

    def test_rerun_vs_recompute_distinct_trigger_semantics(self, tmp_path):
        """Rerun → superseded；Recompute(invalidate) → invalidated。"""
        s = _new(tmp_path, questions=("Q001",))
        s.run()
        # recompute 路径
        r = s.registry.list_by_type("result")[0]
        s.invalidate(r.artifact_id, reason="数据勘误")
        assert s.registry.get(r.artifact_id).status == "invalidated"
        s.run()
        # rerun 路径
        old_e = [a for a in s.registry.list_by_type("experiment")
                 if a.status not in ("invalidated", "superseded",
                                     "deprecated")]
        s.rerun("experiment@Q001")
        s.run()
        for a in old_e:
            assert s.registry.get(a.artifact_id).status == "superseded"


# ============================================================
# G + H. Invalidation / Partial Rebuild
# ============================================================

class TestGInvalidation:
    def test_downstream_claim_unusable(self, tmp_path):
        s = _new(tmp_path, questions=("Q001", "Q002"))
        s.run()
        result = next(a for a in s.registry.list_by_type("result")
                      if a.question == "Q001")
        claim = next(a for a in s.registry.list_by_type("claim")
                     if a.question == "Q001")
        s.invalidate(result.artifact_id, reason="勘误")
        assert is_terminal(s.registry.get(claim.artifact_id).status)
        # 死 claim 不再支撑论文（J 联动）
        assert not can_support_claim(s.registry.get(claim.artifact_id).status)


class TestHPartialRebuild:
    def test_only_affected_branch_reruns(self, tmp_path):
        s = _new(tmp_path, questions=("Q001", "Q002"))
        s.run()
        untouched_nodes = {nid for nid in s.engine.dag.nodes
                           if nid.endswith("@Q002")}
        done_before = set(s.engine.completed)

        r = next(a for a in s.registry.list_by_type("result")
                 if a.question == "Q001")
        s.invalidate(r.artifact_id, reason="勘误")
        # Q002 分支不受影响
        assert {nid for nid in untouched_nodes if nid in done_before} \
            == untouched_nodes
        s.run()
        assert len(s.engine.completed) == len(s.engine.dag.nodes)


# ============================================================
# I. Supersession — 旧谱系审计保留，永不可再成为活跃证据
# ============================================================

class TestISupersession:
    def test_terminal_is_immutable_and_non_reusable(self, tmp_path):
        reg = ArtifactRegistry(tmp_path / "r.json")
        reg.project = "t"
        a = reg.create("result", title="x", activate=True)
        a.transition("superseded", by="t", reason="test")
        # 终态不可转出（lifecycle 状态机）
        with pytest.raises(LifecycleError):
            reg.get(a.artifact_id).transition("active", by="t")
        with pytest.raises(LifecycleError):
            reg.get(a.artifact_id).transition("validated", by="t")
        # 契约谓词
        assert not is_reusable("superseded")
        assert not is_reusable("invalidated")
        assert not is_reusable("deprecated")
        assert is_reusable("active") and is_reusable("validated")
        assert not can_support_claim("superseded")
        assert not can_enter_paper("invalidated")

    def test_superseded_lineage_retained_for_audit(self, tmp_path):
        s = _new(tmp_path, questions=("Q001",))
        s.run()
        old = {a.artifact_id for a in s.registry.list_by_type("experiment")}
        s.rerun("experiment@Q001")
        s.run()
        for aid in old:
            art = s.registry.get(aid)     # 仍在 Registry
            assert art.status == "superseded"
            assert art.lifecycle_history, "审计历史保留"


# ============================================================
# J. Paper Projection — 只有活跃证据能进入叙事
# ============================================================

class TestJPaperProjection:
    def test_only_active_evidence_enters_narrative(self, tmp_path):
        s = _new(tmp_path, questions=("Q001", "Q002"))
        s.run()
        result = next(a for a in s.registry.list_by_type("result")
                      if a.question == "Q001")
        s.invalidate(result.artifact_id, reason="勘误")
        s.run()
        from runtime.writing.director import ResearchDirector
        nar = ResearchDirector(s.registry, s.graph).build()
        active_claims = {a.artifact_id for a in s.registry.list_by_type("claim")
                         if not is_terminal(a.status)}
        terminal_claims = {a.artifact_id for a in s.registry.list_by_type("claim")
                           if is_terminal(a.status)}
        # 冻结语义：director 保留死弧供审计（status=dead ↔ claim 终态），
        # 活弧必须指向活跃 claim；死弧被投影排除（不得进入章节）
        for arc in nar.arcs:
            if arc.status == "dead":
                assert arc.claim_id in terminal_claims
            else:
                assert arc.claim_id in active_claims
        from runtime.writing.projection import PaperProjection
        outline = PaperProjection(s.registry, s.graph).project(nar)
        placed = set()
        for sec in outline["sections"]:
            for c in sec.get("claims", []):
                placed.add(c["claim"] if isinstance(c, dict) else c)
        assert not (placed & terminal_claims), "终态 claim 不得进入投影"


# ============================================================
# K. Deterministic Replay — 同输入 → 同拓扑
# ============================================================

class TestKReplay:
    def test_same_input_same_topology(self, tmp_path):
        snaps = []
        for i in range(2):
            s = RuntimeSession(tmp_path / f"run{i}", ["Q001", "Q002"])
            s.run()
            snaps.append(_snapshot(s))
        assert snaps[0] == snaps[1], "确定性输入必须产出相同图/状态拓扑"


# ============================================================
# 契约本身（NodeResult / 锁）
# ============================================================

class TestContracts:
    def test_node_result_output_contract(self):
        assert validate_node_result_outputs({}) == []
        assert validate_node_result_outputs(
            {"evidence": [{"from": "A", "relation": "supports", "to": "B"}],
             "metrics": {"latency_ms": 1}}) == []
        problems = validate_node_result_outputs({"bogus": 1})
        assert any("bogus" in p for p in problems)
        problems = validate_node_result_outputs(
            {"evidence": [{"from": "A"}]})
        assert any("relation" in p for p in problems)

    def test_concurrent_id_allocation_no_duplicates(self, tmp_path):
        """多线程同时 create：ID 零重复（P7-并发契约）。"""
        reg = ArtifactRegistry(tmp_path / "r.json")
        reg.project = "t"
        errors = []

        def worker():
            try:
                for _ in range(50):
                    reg.create("result", title="x", activate=True)
            except Exception as e:      # pragma: no cover
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, errors[:3]
        ids = [a.artifact_id for a in reg.all()]
        assert len(ids) == 400 == len(set(ids))

    def test_concurrent_relations_and_decisions(self, tmp_path):
        reg = ArtifactRegistry(tmp_path / "r.json")
        reg.project = "t"
        for i in range(3):
            reg.create("result", title=f"r{i}", activate=True)
        graph = EvidenceGraph(reg)
        dlog = DecisionLog(tmp_path / "d.json")
        errors = []

        from runtime.graph.evidence_graph import GraphError

        def worker(i):
            for j in range(30):
                try:
                    graph.add_relation("R001", "derived_from", "R002")
                except GraphError:
                    pass              # 重复边被 fail-closed 拒绝 = 契约行为
                except Exception as e:  # pragma: no cover
                    errors.append(e)
                try:
                    dlog.add(f"Q{j % 3}", f"choice-{i}-{j}", ["a", "b"],
                             ["c"], "r", 0.9, True, "t")
                except Exception as e:  # pragma: no cover
                    errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, errors[:3]
        # derived_from 重复边被拒绝 → 只剩 0 条重复 + 决策 120 条不丢
        assert len(dlog.decisions) == 120
        rels = [(r["from"], r["relation"], r["to"]) for r in graph.relations]
        assert len(rels) == len(set(rels)), "重复边进入图"
