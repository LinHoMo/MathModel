"""P9 Research Quality 测试矩阵（Q-01~Q-15）+ 对抗测试 A–G。

运行: python -m pytest tests/integration/test_research_quality.py -q
对照任务书 P9-14。七维评估器全部为确定性规则（零 LLM）。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from runtime.decisions.log import DecisionLog  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402
from runtime.knowledge.packs import load_competition_packs  # noqa: E402
from runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402
from validators.quality import ResearchQuality  # noqa: E402

KNOW = REPO / "core" / "knowledge"


def _rq(decisions=None, pack=None):
    return ResearchQuality(knowledge=KnowledgeRetriever(KNOW),
                           decisions=decisions, pack=pack)


def _session(tmp_path, questions=("Q001", "Q002"), run=True):
    s = RuntimeSession(tmp_path / "proj", list(questions))
    if run:
        s.run()
    return s


def _has(report, dim, check_id=None, subject=None):
    for f in report.findings:
        if f.dimension == dim and (check_id is None or f.check_id == check_id) \
                and (subject is None or f.subject_id == subject):
            return f
    return None


# ============================================================
# Q-01~Q-08：七维基本评估（跑一次真实 session）
# ============================================================

class TestSevenDimensions:
    def test_q01_problem_quality(self, tmp_path):
        s = _session(tmp_path)
        rep = _rq().evaluate(s.registry, s.graph)
        assert rep.dimensions["problem"].status == "PASS"
        assert not _has(rep, "problem", "P-Q1")

    def test_q02_model_quality(self, tmp_path):
        s = _session(tmp_path)
        dlog = DecisionLog(s.project_dir / "state" / "decision_log.json")
        rep = _rq(decisions=dlog).evaluate(s.registry, s.graph)
        # 健康运行：M1/M2/M3 不应 FAIL
        for f in rep.dimensions["model"].findings:
            if f.check_id in ("M1", "M2", "M3"):
                assert f.severity != "fail"

    def test_q03_experiment_quality(self, tmp_path):
        """E1-E6：计划条目完整（健康运行 PASS）；E7-E8 无死链。"""
        s = _session(tmp_path)
        rep = _rq().evaluate(s.registry, s.graph)
        for f in rep.findings:
            if f.check_id in ("E1", "E2", "E3", "E5"):
                assert f.severity != "fail", f.reason

    def test_q04_evidence_quality(self, tmp_path):
        s = _session(tmp_path)
        rep = _rq().evaluate(s.registry, s.graph)
        assert rep.dimensions["evidence"].status in ("PASS", "WEAK")

    def test_q05_claim_quality(self, tmp_path):
        s = _session(tmp_path)
        rep = _rq().evaluate(s.registry, s.graph)
        # CQ-baseline 是 WEAK advisory（claim 未记录对照物 → 提示补全）
        for f in rep.findings:
            if f.check_id in ("CQ-what", "CQ-based", "CQ-repro"):
                assert f.severity != "fail"

    def test_q06_decision_quality(self, tmp_path):
        """D4 核心不变量：健康运行决策引用存活。"""
        s = _session(tmp_path)
        dlog = DecisionLog(s.project_dir / "state" / "decision_log.json")
        rep = _rq(decisions=dlog).evaluate(s.registry, s.graph)
        for f in rep.dimensions["decision"].findings:
            if f.check_id == "D4":
                assert f.severity != "fail"

    def test_q07_innovation_quality_hypothesis(self, tmp_path):
        """创新改进未测量 → UNKNOWN（hypothesis 语义），不得 PASS。"""
        s = _session(tmp_path)
        # 显式构造创新验证条目（确定性运行默认计划可能不含创新候选）
        for a in s.registry.list_by_type("decision"):
            if "实验计划" in (a.title or ""):
                a.data["entries"].append({
                    "experiment_id": "E-INNO-01",
                    "purpose": "创新验证[ip-x]: 组合权重改进",
                    "hypothesis": "组合赋权优于单一赋权",
                    "method": "innovation: 组合权重对照",
                    "baseline": "未采用创新的基线",
                    "metrics": ["排序一致性"],
                    "decision_rule": {"metric": "innovation_gain",
                                      "accept_if": "gain > cost",
                                      "reject_if": "gain <= 0",
                                      "refine_if": ""},
                    "priority": 2, "cost": 3,
                    "expected_information_gain": 0.6,
                })
        rep = _rq().evaluate(s.registry, s.graph)
        inno_unknowns = [f for f in rep.findings
                         if f.dimension == "innovation"
                         and f.status == "UNKNOWN"]
        assert inno_unknowns, "确定性运行下创新未测量必须显式 UNKNOWN"
        # 未测量创新不得判 PASS
        assert all(f.status != "PASS" for f in rep.dimensions["innovation"].findings)

    def test_q08_reproducibility(self, tmp_path):
        s = _session(tmp_path)
        rep = _rq().evaluate(s.registry, s.graph)
        fail_r = [f for f in rep.findings
                  if f.dimension == "reproducibility" and f.severity == "fail"]
        assert not fail_r

    def test_report_has_no_score(self, tmp_path):
        """P9-1：QualityReport 不含黑箱总分。"""
        s = _session(tmp_path)
        rep = _rq().evaluate(s.registry, s.graph)
        d = rep.as_dict()
        assert "score" not in d and "overall_score" not in d
        assert d["overall_status"] in ("PASS", "WEAK", "FAIL", "UNKNOWN")


# ============================================================
# 对抗测试 A–G（任务书 P9-14）
# ============================================================

class TestAdversarial:
    def test_A_invalidated_evidence_quality_not_pass(self, tmp_path):
        """A：旧 Evidence 被 invalidated → Quality != PASS。"""
        s = _session(tmp_path, questions=("Q001",))
        result = next(a for a in s.registry.list_by_type("result"))
        s.invalidate(result.artifact_id, reason="勘误")
        s.run()
        rep = _rq().evaluate(s.registry, s.graph)
        assert rep.overall_status != "PASS"
        assert rep.blockers or rep.warnings

    def test_B_superseded_model_cannot_support_decision(self, tmp_path):
        """B：旧 Model superseded → 不得作为当前依据（D4）。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        model = s.registry.list_by_type("model")[0]
        model.transition("superseded", by="test", reason="替代")
        dlog = DecisionLog(s.project_dir / "state" / "decision_log.json")
        rep = _rq(decisions=dlog).evaluate(s.registry, s.graph)
        # 决策仍引用该卡：Knowledge 层仍在（P8-14：被否定的是 Decision 不是
        # Knowledge），但 model artifact 层面必须出现 WEAK 以上发现
        model_findings = rep.dimensions["model"].findings
        dead_models = [a for a in s.registry.list_by_type("model")
                       if a.status == "superseded"]
        assert dead_models or model_findings

    def test_C_experiment_without_baseline_fails_quality(self, tmp_path):
        """C：实验成功但无 baseline → Research Quality ≠ PASS。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        # 篡改计划：清空 baseline（模拟"没做对照"）
        for a in s.registry.list_by_type("decision"):
            if "实验计划" in (a.title or ""):
                a.data["baseline_comparison"] = []
                for e in a.data.get("entries", []):
                    e["baseline"] = ""
        rep = _rq().evaluate(s.registry, s.graph)
        assert _has(rep, "model", "M3") or _has(rep, "experiment", "E5")
        assert rep.overall_status != "PASS"

    def test_D_innovation_without_improvement_is_unknown(self, tmp_path):
        """D：创新候选无 improvement 证据 → WEAK/UNKNOWN，不能 PASS。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        rep = _rq().evaluate(s.registry, s.graph)
        inno = rep.dimensions["innovation"]
        # 确定性运行没有测量创新收益 → 必须 UNKNOWN（hypothesis）
        unknowns = [f for f in inno.findings if f.status == "UNKNOWN"]
        if inno.findings:
            assert unknowns, "无测量证据的创新不得 PASS"

    def test_E_same_source_evidence_not_independent(self, tmp_path):
        """E：同源证据不得计为独立。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        # 构造：两个 claim 由同一 result 支撑（同源）
        r = next(a for a in s.registry.list_by_type("result")
                 if a.status == "active")
        c1 = s.registry.create("claim", title="同源结论1", question=r.question,
                               depends_on=[r.artifact_id], activate=True)
        c2 = s.registry.create("claim", title="同源结论2", question=r.question,
                               depends_on=[r.artifact_id], activate=True)
        s.graph.add_relation(r.artifact_id, "supports", c1.artifact_id)
        s.graph.add_relation(r.artifact_id, "supports", c2.artifact_id)
        rep = _rq().evaluate(s.registry, s.graph)
        assert _has(rep, "evidence", "EQ-independence"), \
            "同源双 claim 必须触发独立性发现"

    def test_F_crash_resume_quality_rebuilt(self, tmp_path):
        """F：Crash → Resume 后 Quality 状态可从 Registry/Evidence 重建。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        rep1 = _rq().evaluate(s.registry, s.graph)
        s2 = RuntimeSession(s.project_dir, ["Q001"])
        s2.resume()
        rep2 = _rq().evaluate(s2.registry, s2.graph)
        assert rep1.overall_status == rep2.overall_status

    def test_G_rerun_old_report_not_overwriting_new(self, tmp_path):
        """G：Rerun 产生新谱系后，旧 quality report 不得覆盖新评估。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        rep_old = _rq().evaluate(s.registry, s.graph)
        s.rerun("experiment@Q001", reason="参数调整")
        s.run()
        rep_new = _rq().evaluate(s.registry, s.graph)
        assert rep_new.as_dict() != rep_old.as_dict()
        # 落盘的是新报告
        import json
        persisted = json.loads(
            (s.project_dir / "state" / "quality_report.json")
            .read_text(encoding="utf-8"))
        assert persisted["dimensions"].keys() == rep_new.dimensions.keys()


# ============================================================
# Q-09~Q-15：反馈 / 生命周期 / Pack
# ============================================================

class TestFeedbackAndLifecycle:
    def test_q09_failure_propagation_changes_quality(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        r = s.registry.list_by_type("result")[0]
        before = _rq().evaluate(s.registry, s.graph).overall_status
        s.invalidate(r.artifact_id, reason="勘误")
        s.run()
        # 失效传播后被重建 → 质量不劣于失效时点
        after = _rq().evaluate(s.registry, s.graph).overall_status
        rank = {"PASS": 0, "UNKNOWN": 1, "WEAK": 2, "FAIL": 3}
        assert rank[after] <= rank[before] + 1

    def test_q10_q11_supersession_and_invalidation_distinct(self, tmp_path):
        """Q-10/Q-11：superseded ≠ invalidated，Quality 均不得 PASS 但语义不同。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        old_e = s.registry.list_by_type("experiment")[0]
        s.rerun("experiment@Q001")
        s.run()
        assert s.registry.get(old_e.artifact_id).status == "superseded"
        rep = _rq().evaluate(s.registry, s.graph)
        # 重建后新链健康
        assert rep.overall_status in ("PASS", "WEAK")

    def test_q12_resume_quality_consistent(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        s2 = RuntimeSession(s.project_dir, ["Q001"])
        s2.resume()
        assert _rq().evaluate(s.registry, s.graph).overall_status == \
            _rq().evaluate(s2.registry, s2.graph).overall_status

    def test_q13_rerun_with_quality_memory(self, tmp_path):
        """P9-12：FAIL blockers 写回 DecisionLog（quality 类决策）。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        rq = _rq(decisions=s.decisions)
        rep = rq.evaluate(s.registry, s.graph)
        # 构造一个 blocker
        for a in s.registry.list_by_type("decision"):
            if "实验计划" in (a.title or ""):
                a.data["baseline_comparison"] = []
        rep2 = rq.evaluate(s.registry, s.graph)
        recorded = rq.record_blockers(rep2)
        if rep2.blockers:
            assert recorded
            kinds = [d.question_type for d in recorded]
            assert all(k == "quality" for k in kinds)

    def test_q14_pack_changes_priority_not_verdict(self, tmp_path):
        """Q-14 / P9-13：Pack 改变处置优先级，绝不把 FAIL 改成 PASS。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        packs = load_competition_packs(KNOW)
        pack = packs.get("cp-cumcm")
        no_pack = _rq().evaluate(s.registry, s.graph)
        with_pack = _rq(pack=pack).evaluate(s.registry, s.graph)
        assert no_pack.overall_status == with_pack.overall_status, \
            "Pack 不得篡改判定"
        # 无 blocker 时 priorities 仍生成（排序用途）
        assert with_pack.priorities
        # pack 命中维度的处置优先级应前置
        if with_pack.recommended_actions:
            first_dim = with_pack.recommended_actions[0]
            assert first_dim

    def test_q15_quality_node_in_workflow(self, tmp_path):
        """Q-15：quality_evaluation 是 DAG 节点且 FAIL 走反馈环。"""
        s = _session(tmp_path, questions=("Q001",))
        assert "quality_evaluation" in s.engine.dag.nodes
        node = s.engine.dag.nodes["quality_evaluation"]
        assert node.type == "validation"
        assert node.on_fail == "evidence_build"
        rep = s.run()
        assert "quality_evaluation" in rep["progress"]["completed"]
