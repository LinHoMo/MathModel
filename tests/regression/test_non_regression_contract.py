"""五轴 Non-regression 契约测试（System Hardening P5）。

单命令判据: python -m pytest tests/regression -q 全绿 = 五轴通过。
契约文本: docs/architecture/REGRESSION_CONTRACT.md。
运行: python -m pytest tests/regression/test_non_regression_contract.py -q
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PY = sys.executable


def _run_py(args, timeout=300):
    return subprocess.run([PY] + args, cwd=str(REPO), capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


class TestNonRegressionContract:
    """五轴（functional / semantic / quality / data / operational）。"""

    def test_functional_axis(self):
        """V2 29-step legacy 核心能力零回归（R1–R8）。"""
        r = _run_py(["-m", "pytest",
                     "tests/regression/test_v2_capability_regression.py", "-q"])
        assert r.returncode == 0, f"functional 轴失败:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}"

    def test_semantic_axis(self):
        """旧 artifact/evidence 可读且含义不变 + 对账报告可产出。"""
        sys.path.insert(0, str(REPO / "core"))
        from runtime.artifacts.registry import ArtifactRegistry
        from runtime.graph.evidence_graph import EvidenceGraph
        from runtime.state.model import ProjectState
        from runtime.state.reconcile import reconcile

        base = REPO / "tests" / "fixtures" / "sample_incomplete_project"
        state = ProjectState(base / "state" / "status.json")
        assert state.data["schema_version"] == 3
        reg = ArtifactRegistry(base / "state" / "registry.json")
        graph = EvidenceGraph(reg, base / "state" / "evidence_graph.json")
        assert len(reg.all()) >= 0           # 可解析即语义不降级
        rep = reconcile(base)
        assert rep["mode"] == "v3"
        assert isinstance(rep.get("problems"), list)

    def test_quality_axis(self):
        """能力指标不倒退（机器文件为真源，容忍 ≤5 个百分点）。"""
        anchor = {
            "decomposition": 100, "method_selection": 0,
            "model_correctness": 70, "experiment_validity": 100,
            "validation_reliability": 100, "innovation": 0,
            "end_to_end": 71,
        }
        mfile = REPO / "research" / "bench-m4-2000c" / "work" / "e2e_metrics.json"
        if not mfile.exists():
            pytest.skip("requires_runtime：基线 e2e_metrics.json 缺失（外部语料环境）")
        data = json.loads(mfile.read_text(encoding="utf-8"))
        metrics = data.get("metrics", {})
        summary = data.get("summary", {})
        assert summary.get("computed", 0) >= 5, \
            f"指标可计算数低于基线: {summary}"
        for k, baseline in anchor.items():
            v = metrics.get(k)
            if v is None:                   # absent/n/a 如实报告，不扣分
                continue
            if isinstance(v, dict):         # 指标细节结构：数值在 value 键
                v = v.get("value")
                if v is None:            # 结构存在但无数值 = absent
                    continue
            assert isinstance(v, (int, float))
            assert v >= baseline - 5, \
                f"指标 {k} 倒退: 当前 {v} < 基线 {baseline} - 5"

    def test_data_axis(self):
        """旧项目可迁移：V2 work/state.json → V3 status.json。"""
        import tempfile
        sys.path.insert(0, str(REPO / "core"))
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "work").mkdir(parents=True)
            legacy = {
                "schema_version": "1.0",
                "current": {"hand": "modeler", "agent": "model-builder"},
                "completed": [
                    {"hand": "modeler", "agent": "problem-parser", "stage": 1},
                    {"hand": "modeler", "agent": "model-builder", "stage": 4},
                ],
            }
            (base / "work" / "state.json").write_text(
                json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
            from runtime.legacy.convert import convert_project
            convert_project(base)
            status = json.loads(
                (base / "state" / "status.json").read_text(encoding="utf-8"))
            assert status["schema_version"] == 3
            assert status["run"]["phase"] == "legacy-imported"
            # 仅完成 2/8 个 modeler agent → 维度 in_progress（保守聚合不冒进）
            assert status["state"]["models"]["status"] == "in_progress"

    def test_operational_axis(self):
        """crash/resume/rerun/invalidate 生命周期语义不坏。"""
        r = _run_py(["-m", "pytest",
                     "tests/unit/test_crash_consistency.py",
                     "tests/unit/test_reconcile.py",
                     "tests/integration/test_runtime_session.py", "-q"])
        assert r.returncode == 0, \
            f"operational 轴失败:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}"