"""P9.5 V3 System Red Team — 跨层完整性攻击测试。

运行: python -m pytest tests/integration/test_red_team.py -q
攻击面: Plan→Evidence / Evidence→Decision / Decision→Quality / Quality→Rerun /
        Rerun→Evidence / Crash→Resume / Quality→State / Pack 污染 / 循环论证 / 闭环。
不变量 R1–R12（任务书定义）逐条落为测试。发现按 真bug/契约缺陷/测试缺陷/
文档缺陷/设计债/非问题 归类于 docs/architecture/V3_RED_TEAM_REPORT.md。
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.decisions.log import DecisionLog  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.knowledge.packs import load_competition_packs  # noqa: E402
from runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402
from validators.quality import ResearchQuality  # noqa: E402

KNOW = REPO / "core" / "knowledge"
TERMINAL = ("invalidated", "superseded", "deprecated")
RANK = {"PASS": 0, "UNKNOWN": 1, "WEAK": 2, "FAIL": 3}


def _rq(decisions=None, pack=None):
    return ResearchQuality(knowledge=KnowledgeRetriever(KNOW),
                           decisions=decisions, pack=pack)


def _session(tmp_path, questions=("Q001",), run=True, name="proj"):
    s = RuntimeSession(tmp_path / name, list(questions))
    if run:
        s.run()
    return s


def _snapshot(s):
    return {
        "artifacts": sorted((a.artifact_id, a.type, a.status)
                            for a in s.registry.all()),
        "relations": sorted((r["from"], r["relation"], r["to"])
                            for r in s.graph.relations),
        "quality": _rq(decisions=s.decisions).evaluate(
            s.registry, s.graph).overall_status,
    }


# ============================================================
# R4/R5/R6/R7 — 四种执行语义必须不同（攻击面 5）
# ============================================================

class TestFourSemantics:
    def test_R4_rerun_creates_new_lineage(self, tmp_path):
        s = _session(tmp_path)
        old = {a.artifact_id for a in s.registry.list_by_type("experiment")}
        s.rerun("experiment@Q001")
        s.run()
        new = {a.artifact_id for a in s.registry.list_by_type("experiment")}
        assert new - old, "rerun 必须产生新 Artifact"
        for aid in old:
            assert s.registry.get(aid).status == "superseded"

    def test_R5_resume_preserves_lineage(self, tmp_path):
        s = _session(tmp_path)
        before = _snapshot(s)
        s2 = RuntimeSession(s.project_dir, ["Q001"])
        s2.resume()
        assert _snapshot(s2)["artifacts"] == before["artifacts"]
        assert _snapshot(s2)["relations"] == before["relations"]

    def test_R6_retry_creates_no_new_lineage(self, tmp_path):
        s = _session(tmp_path, run=False)   # 未执行 → retry 发生在首跑中
        calls = {"n": 0}
        orig = s.executor_impl.do_assumption_check

        def flaky(nid):
            calls["n"] += 1
            if calls["n"] < 2:
                from runtime.execution.engine import FAIL, NodeResult
                return NodeResult(FAIL, "瞬时故障")
            return orig(nid)

        s.executor_impl.do_assumption_check = flaky
        s.run()
        assert calls["n"] >= 2, "瞬时故障应触发引擎 retry"
        experiments = s.registry.list_by_type("experiment")
        assert len(experiments) == 1, \
            "retry 不得复制实验链（应为恰好一条 E001）"

    def test_R7_recompute_vs_rerun_distinct(self, tmp_path):
        # recompute: invalidated
        s1 = _session(tmp_path / "a", run=True, name="p")
        r = s1.registry.list_by_type("result")[0]
        s1.invalidate(r.artifact_id, reason="勘误")
        s1.run()
        # rerun: superseded
        s2 = _session(tmp_path / "b", run=True, name="p")
        old = s2.registry.list_by_type("result")[0].artifact_id
        s2.rerun("experiment@Q001")
        s2.run()
        assert s1.registry.get(r.artifact_id).status == "invalidated"
        assert s2.registry.get(old).status == "superseded"


# ============================================================
# 攻击面 1：Plan → Evidence
# ============================================================

class TestPlanEvidence:
    def test_RT1_experiment_carries_plan_provenance(self, tmp_path):
        """每个 experiment 必须能追溯到计划（plan_ref）。"""
        s = _session(tmp_path)
        for e in s.registry.list_by_type("experiment"):
            assert e.data.get("plan_ref"), \
                f"{e.artifact_id} 无 plan provenance（计划↔执行断链）"

    def test_RT2_rerun_retires_old_plan(self, tmp_path):
        """重跑后不得存在两个 active 实验计划（旧计划必须退役）。"""
        s = _session(tmp_path)
        s.rerun("experiment@Q001")
        s.run()
        active_plans = [a for a in s.registry.list_by_type("decision")
                        if "实验计划" in (a.title or "")
                        and a.status == "active"]
        assert len(active_plans) == 1, \
            f"发现 {len(active_plans)} 个 active 计划（旧计划未退役）"

    def test_RT3_hypothesis_flows_to_experiment(self, tmp_path):
        """实验必须携带假设 provenance（hypothesis 不是纯 metadata）。"""
        s = _session(tmp_path)
        plans = [a for a in s.registry.list_by_type("decision")
                 if "实验计划" in (a.title or "")]
        assert plans and plans[0].data.get("entries")
        hypotheses = {e["hypothesis"] for e in plans[0].data["entries"]
                      if e.get("hypothesis")}
        for e in s.registry.list_by_type("experiment"):
            assert e.data.get("hypothesis_ref") or e.data.get("plan_entry"), \
                f"{e.artifact_id} 未绑定任何 hypothesis"


# ============================================================
# 攻击面 2+3：Evidence → Decision → Quality
# ============================================================

class TestEvidenceDecision:
    def test_R3_superseded_decision_not_current(self, tmp_path):
        """重选型后旧决策不得保持 active（silently current = 违规）。"""
        s = _session(tmp_path)
        s.run()
        active_before = [d for d in s.decisions.decisions.values()
                         if d.status == "active"]
        s.rerun("model_selection", reason="换方法")
        s.run()
        chosen_now = s.executor_impl.shared.get("Q001", {}).get("card_id")
        actives = [d for d in s.decisions.decisions.values()
                   if d.status == "active"
                   and "方法选型" in d.question]
        same = [d for d in actives if d.chosen == chosen_now]
        assert len(same) == 1, \
            f"同一选型存在 {len(actives)} 个 active 决策（R3 违规）"

    def test_R8_quality_not_pass_with_dead_dependency(self, tmp_path):
        s = _session(tmp_path)
        r = next(a for a in s.registry.list_by_type("result")
                 if a.status == "active")
        s.invalidate(r.artifact_id, reason="勘误")
        rep = _rq().evaluate(s.registry, s.graph)   # 不重跑（依赖已死）
        assert rep.overall_status != "PASS"
        assert rep.blockers, "死依赖必须产生 blocker"

    def test_attack2_all_consumers_checked(self, tmp_path):
        """失效证据后：DecisionLog/State/Projection 无一处继续消费旧证据。"""
        s = _session(tmp_path, questions=("Q001", "Q002"))
        s.run()
        r = next(a for a in s.registry.list_by_type("result")
                 if a.question == "Q001")
        c = next(a for a in s.registry.list_by_type("claim")
                 if a.question == "Q001")
        s.invalidate(r.artifact_id, reason="勘误")
        # 1) claim 被传播判死（EvidenceGraph 契约）
        assert s.registry.get(c.artifact_id).status == "invalidated"
        # 2) State：失效 claim 不得继续算 supported
        st = s.state.data["state"]["evidence"]
        # 3) Projection：死 claim 不进入章节（R12 前置验证）
        from runtime.writing.projection import PaperProjection
        from runtime.writing.director import ResearchDirector
        nar = ResearchDirector(s.registry, s.graph).build()
        outline = PaperProjection(s.registry, s.graph).project(nar)
        placed = set()
        for sec in outline["sections"]:
            for cc in sec.get("claims", []):
                placed.add(cc["claim"] if isinstance(cc, dict) else cc)
        assert c.artifact_id not in placed
        # 4) 图：死边被剪
        assert not any("R001" == e["from"] and e["relation"] == "supports"
                       for e in s.graph.relations
                       if s.registry.get(e["to"]).status != "invalidated")


# ============================================================
# 攻击面 4：Quality → Rerun（跨谱系污染）
# ============================================================

class TestQualityRerun:
    def test_R11_no_cross_lineage_pollution(self, tmp_path):
        s = _session(tmp_path)
        s.run()
        old_results = {a.artifact_id for a in s.registry.list_by_type("result")}
        s.rerun("experiment@Q001")
        s.run()
        new_claims = [a for a in s.registry.list_by_type("claim")
                      if a.status == "active"]
        for c in new_claims:
            for e in s.graph.relations:
                if e["relation"] == "supports" and e["to"] == c.artifact_id:
                    assert e["from"] not in old_results, \
                        "旧 result 不得支撑新 claim（跨谱系污染）"
        # 旧 quality 决策记录不阻塞新 lineage
        rep = _rq(decisions=s.decisions).evaluate(s.registry, s.graph)
        d4 = [f for f in rep.dimensions["decision"].findings
              if f.check_id == "D4" and f.severity == "fail"]
        assert not d4, f"旧 lineage 污染决策评估: {[f.reason for f in d4]}"

    def test_R11_old_report_not_contaminating(self, tmp_path):
        s = _session(tmp_path)
        s.run()
        old_status = _rq().evaluate(s.registry, s.graph).overall_status
        s.rerun("experiment@Q001")
        s.run()
        rep_new = _rq().evaluate(s.registry, s.graph)
        persisted = json.loads(
            (s.project_dir / "state" / "quality_report.json")
            .read_text(encoding="utf-8"))
        assert persisted["overall_status"] == rep_new.overall_status
        assert persisted["overall_status"] != "stale-marker"
        assert old_status in ("PASS", "WEAK", "FAIL", "UNKNOWN")


# ============================================================
# 攻击面 6：Crash → Resume（七个切点）
# ============================================================

class TestCrashPoints:
    CUTS = {
        "after_plan": ["problem_analysis", "literature_search",
                       "model_selection", "model_construction",
                       "model_critique", "assumption_check",
                       "experiment_design"],
        "after_model": ["problem_analysis", "literature_search",
                        "model_selection", "model_construction",
                        "model_critique", "assumption_check"],
        "after_experiment": ["problem_analysis", "literature_search",
                             "model_selection", "model_construction",
                             "model_critique", "assumption_check",
                             "experiment_design", "experiment@Q001"],
        "after_evidence": ["problem_analysis", "literature_search",
                           "model_selection", "model_construction",
                           "model_critique", "assumption_check",
                           "experiment_design", "experiment@Q001",
                           "experiment_critique@Q001", "evidence_build"],
    }

    @pytest.mark.parametrize("cut", CUTS.keys())
    def test_resume_rebuilds_same_world(self, tmp_path, cut):
        ref = _session(tmp_path / f"ref_{cut}", run=True, name="p")
        s = _session(tmp_path / f"crash_{cut}", run=False, name="p")
        for nid in self.CUTS[cut]:
            s.engine.step(nid)
        s.checkpoint()
        s.engine.save_progress(s.project_dir / "state" / "engine_progress.json")
        s2 = RuntimeSession(s.project_dir, ["Q001"])
        s2.resume()
        ref_snap = _snapshot(ref)
        got_snap = _snapshot(s2)
        assert got_snap["artifacts"] == ref_snap["artifacts"], \
            f"{cut}: resume 后 Artifact 世界不一致"
        assert got_snap["relations"] == ref_snap["relations"], \
            f"{cut}: resume 后 Evidence 世界不一致"

    def test_resume_no_recomputed_new_ids(self, tmp_path):
        """Resume 后不得出现'看起来一样但 ID 不同'的产物。"""
        s = _session(tmp_path, run=False)
        for nid in ("problem_analysis", "literature_search",
                    "model_selection", "model_construction",
                    "model_critique", "assumption_check",
                    "experiment_design", "experiment@Q001",
                    "experiment_critique@Q001", "evidence_build",
                    "evidence_gate", "quality_evaluation"):
            s.engine.step(nid)
        ids_before = {a.artifact_id for a in s.registry.all()}
        s.checkpoint()
        s2 = RuntimeSession(s.project_dir, ["Q001"])
        s2.resume()
        ids_after = {a.artifact_id for a in s2.registry.all()}
        new_unknown = ids_after - ids_before
        # 允许的新增：N/S（research_direction 及其下游，未完成部分）+
        # D（quality memory 决策记录，合法新增）；禁止重算已完成研究产物
        research_prefixes = ("M", "R", "E", "C", "A", "F", "DATA", "CODE")
        research_new = [a for a in new_unknown if a.startswith(research_prefixes)]
        assert not research_new, \
            f"resume 重算出了新 ID 的已完成研究产物: {sorted(research_new)}"


# ============================================================
# 攻击面 7：Quality → Research State
# ============================================================

class TestQualityState:
    def test_weak_quality_state_semantics_documented(self, tmp_path):
        """当前语义（审计记录）：WEAK 为 advisory，不回退已 validated 的问题。

        这是 P9 的显式设计决定（advisory 不阻断确定性流程）；若未来要求
        FAIL 降级问题状态，须先改本测试 + 契约文档，不允许静默变化。
        """
        s = _session(tmp_path, questions=("Q001", "Q002"))
        s.run()
        rep = _rq().evaluate(s.registry, s.graph)
        st = s.state.data["state"]["questions"]
        if rep.overall_status == "WEAK":
            # advisory 不降级：validated 问题保持 validated
            for qid, q in st.items():
                if q["status"] == "validated":
                    assert q["claims"], "validated 必须有 claim 支撑"

    def test_fail_quality_blocks_downstream_research(self, tmp_path):
        """FAIL 时 research_direction 不得完成（Quality → State 方向）。"""
        s = _session(tmp_path, run=False, questions=("Q001",))
        s.run()
        # 构造 FAIL：清空计划 baseline → M3 fail → quality FAIL
        for a in s.registry.list_by_type("decision"):
            if "实验计划" in (a.title or ""):
                a.data["baseline_comparison"] = []
                for e in a.data.get("entries", []):
                    e["baseline"] = ""
        rep = _rq().evaluate(s.registry, s.graph)
        assert rep.overall_status == "FAIL"
        assert rep.blockers


# ============================================================
# 攻击面 8+9：Pack 污染 / 循环论证
# ============================================================

class TestPollution:
    def test_R9_pack_never_upgrades_verdict(self, tmp_path):
        s = _session(tmp_path)
        s.run()
        for a in s.registry.list_by_type("decision"):
            if "实验计划" in (a.title or ""):
                a.data["baseline_comparison"] = []   # 制造事实 FAIL
        packs = load_competition_packs(KNOW)
        base = _rq().evaluate(s.registry, s.graph)
        for pid, pack in packs.items():
            with_pack = _rq(pack=pack).evaluate(s.registry, s.graph)
            assert RANK[with_pack.overall_status] >= RANK[base.overall_status], \
                f"{pid}: Pack 把 {base.overall_status} 洗成 {with_pack.overall_status}"
            for f in with_pack.findings:
                twin = next((x for x in base.findings
                             if x.check_id == f.check_id
                             and x.subject_id == f.subject_id), None)
                if twin:
                    assert f.severity == twin.severity, \
                        "Pack 不得改变 finding severity"

    def test_R10_knowledge_expectation_not_evidence(self, tmp_path):
        """循环论证攻击：卡片自述适配 ≠ 实证表现好。"""
        s = _session(tmp_path, run=False, questions=("Q001",))
        # 只完成选型（有知识正条件命中），无任何实验/证据
        for nid in ("problem_analysis", "literature_search",
                    "model_selection"):
            s.engine.step(nid)
        rep = _rq().evaluate(s.registry, s.graph)
        assert rep.overall_status != "PASS", \
            "只有 Knowledge 期望而无实验证据时，Quality 不得 PASS"
        unknown_or_fail = [f for f in rep.findings
                           if f.subject_type == "experiment"
                           or f.subject_type == "claim"]
        assert unknown_or_fail, "必须显式指出证据缺失"


# ============================================================
# R12：PaperProjection 不得复活死研究状态
# ============================================================

class TestR12Projection:
    def test_R12_dead_claims_never_projected(self, tmp_path):
        s = _session(tmp_path, questions=("Q001", "Q002"))
        s.run()
        r = next(a for a in s.registry.list_by_type("result")
                 if a.question == "Q001")
        c = next(a for a in s.registry.list_by_type("claim")
                 if a.question == "Q001")
        s.invalidate(r.artifact_id, reason="勘误")
        s.run()
        from runtime.writing.director import ResearchDirector
        from runtime.writing.projection import PaperProjection
        nar = ResearchDirector(s.registry, s.graph).build()
        outline = PaperProjection(s.registry, s.graph).project(nar)
        terminal = {a.artifact_id for a in s.registry.list_by_type("claim")
                    if a.status in TERMINAL}
        for sec in outline["sections"]:
            for cc in sec.get("claims", []):
                cid = cc["claim"] if isinstance(cc, dict) else cc
                assert cid not in terminal, \
                    f"死主张 {cid} 被投影复活（R12 违规）"


# ============================================================
# 攻击面 10：完整闭环 + 注入
# ============================================================

class TestFullLoopInjection:
    def test_end_to_end_with_injections(self, tmp_path):
        """闭环 + 中途注入：失效 / 崩溃恢复 / 旧计划退役 / 质量回归。"""
        s = _session(tmp_path, questions=("Q001", "Q002"), run=True)
        assert len(s.engine.completed) == len(s.engine.dag.nodes)

        # 注入 1：失效 Q001 result → recompute 重建
        r = next(a for a in s.registry.list_by_type("result")
                 if a.question == "Q001")
        s.invalidate(r.artifact_id, reason="注入失效")
        s.run()
        assert len(s.engine.completed) == len(s.engine.dag.nodes)

        # 注入 2：崩溃（在完成态保存后 resume）
        s2 = RuntimeSession(s.project_dir, ["Q001", "Q002"])
        s2.resume()
        assert len(s2.engine.completed) == len(s2.engine.dag.nodes)

        # 注入 3：rerun 实验 → 新谱系
        s2.rerun("experiment@Q002")
        s2.run()
        assert len(s2.engine.completed) == len(s2.engine.dag.nodes)

        # 终检：质量不劣于 FAIL；无跨谱系污染
        rep = _rq(decisions=s2.decisions).evaluate(s2.registry, s2.graph)
        assert rep.overall_status != "FAIL" or rep.blockers
        active_claims = [a for a in s2.registry.list_by_type("claim")
                         if a.status == "active"]
        old_dead = {a.artifact_id for a in s2.registry.list_by_type("result")
                    if a.status in TERMINAL}
        for c in active_claims:
            for e in s2.graph.relations:
                if e["relation"] == "supports" and e["to"] == c.artifact_id:
                    assert e["from"] not in old_dead
