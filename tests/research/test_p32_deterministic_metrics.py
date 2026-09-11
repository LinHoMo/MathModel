# -*- coding: utf-8 -*-
"""P3-2 验收：确定性指标（claim-evidence 机械遍历 + baseline 数值比较）。

验收标准（ROADMAP P3-2）：
1. claim_evidence_coverage 在真实 registry+graph 上机械报告：claim 被
   真实证据链支撑（supports 边 + 证据终端真实），unsupported 如实列出。
2. baseline_comparison 纯数值确定性比较（tie/different/incomparable）。
3. 无 LLM 调用、无人工推断：全部输出来自 registry + graph 真实数据。
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.evaluation.deterministic_metrics import (  # noqa: E402
    baseline_comparison, claim_evidence_coverage)


def _mini_graph(tmp_path, with_real_evidence=True):
    """最小但真实的 registry+graph：claim + supports 边 + 证据终端。

    - 真实证据：execution_result 带 execution_token（P0-3 语义）+
      result 带数值 outputs + supports 边（exec_ref 指向 EXEC）。
    - 假证据对照：result 无 outputs → 不算真实支撑。
    """
    from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
    from modeling_harness.runtime.graph.evidence_graph import EvidenceGraph
    from modeling_harness.runtime.execution.execution_auth import issue_token

    reg = ArtifactRegistry(tmp_path / "state" / "registry.json")
    reg.project = "p32"
    reg.create("question", artifact_id="Q001", title="Q", activate=True)
    reg.create("problem", title="P", artifact_id="P001", activate=True)
    reg.create("model", title="M", artifact_id="M001", activate=True)
    reg.create("claim", title="C001", artifact_id="C001", activate=True)
    tok = issue_token("c" * 64, "local", "2026-09-10T00:00:00")
    reg.create("execution_result", title="EXEC", artifact_id="EXEC001",
               question="Q001", activate=True,
               data={"status": "success", "returncode": 0,
                     "outputs": {"objective": 12.5},
                     "execution_token": tok,
                     "code_hash": "c" * 64, "environment_hash": "e" * 64,
                     "started_at": "2026-09-10T00:00:00",
                     "provenance": {"adapter": "local"}})
    reg.create("result", title="R001", artifact_id="R001", activate=True,
               data={"outputs": {"objective": 12.5}})
    reg.create("result", title="R002", artifact_id="R002", activate=True,
               data={})  # 假证据：无 outputs

    g = EvidenceGraph(reg, path=tmp_path / "state" / "evidence_graph.json")
    g.add_relation("EXEC001", "produces", "R001")
    g.add_relation("R001", "supports", "C001", exec_ref="EXEC001")
    if not with_real_evidence:
        reg.create("claim", title="C002", artifact_id="C002", activate=True)
        g.add_relation("R002", "supports", "C002")
    return reg, g


class TestClaimEvidenceCoverage:
    def test_supported_by_real_evidence(self, tmp_path):
        _, g = _mini_graph(tmp_path)
        rep = claim_evidence_coverage(g)
        assert rep["total_claims"] == 1
        assert rep["supported_claims"] == 1
        assert rep["coverage_ratio"] == 1.0
        assert rep["unsupported"] == []
        assert rep["evidence_types"].get("result") == 1
        assert rep["with_exec_ref"] == 1

    def test_fake_evidence_not_supported(self, tmp_path):
        _, g = _mini_graph(tmp_path, with_real_evidence=False)
        reg = g.registry
        rep = claim_evidence_coverage(g)
        assert rep["total_claims"] == 2
        assert rep["supported_claims"] == 1
        assert rep["unsupported"] == ["C002"], \
            "无 outputs 的 result 支撑的 claim 必须如实 unsupported"

    def test_empty_graph(self, tmp_path):
        from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
        from modeling_harness.runtime.graph.evidence_graph import EvidenceGraph
        reg = ArtifactRegistry(tmp_path / "e" / "registry.json")
        g = EvidenceGraph(reg, path=tmp_path / "e" / "graph.json")
        rep = claim_evidence_coverage(g)
        assert rep["total_claims"] == 0
        assert rep["coverage_ratio"] == 1.0


class TestBaselineComparison:
    def test_tie_within_tolerance(self):
        r = baseline_comparison({"y": 10.0, "z": 1.0}, {"y": 10.0, "z": 1.0})
        assert r["better"] == "tie"
        assert r["compared_keys"] == 2

    def test_different_values(self):
        # ADR-0013：旧实现只报 "different"（回答不了「谁更好」）；现按目标方向判定。
        # 默认 direction="minimize" ⇒ y 越小越好 ⇒ b(50) 优于 a(100)。
        r = baseline_comparison({"y": 100.0}, {"y": 50.0})
        assert r["better"] == "b"
        assert r["max_rel_diff"] == pytest.approx(0.5)
        # 同一组数字换方向即翻转结论 —— 这正是旧实现无法回答的问题
        assert baseline_comparison({"y": 100.0}, {"y": 50.0},
                                   direction="maximize")["better"] == "a"

    def test_missing_keys_incomparable(self):
        r = baseline_comparison({"y": 1.0}, {"z": 2.0})
        assert r["better"] == "incomparable"
        assert r["compared_keys"] == 0

    def test_deterministic_pure_numeric(self):
        """同一输入两次调用输出逐位一致（确定性，无随机/无 LLM）。"""
        a = baseline_comparison({"y": 3.14}, {"y": 2.71}, tolerance=1e-6)
        b = baseline_comparison({"y": 3.14}, {"y": 2.71}, tolerance=1e-6)
        assert a == b
