# -*- coding: utf-8 -*-
"""L4 门禁 fail-closed 语义测试：model_ir.json 存在但损坏 → FAIL，不得静默放行。

背景（fail-open 缺陷）：三个 L4 门禁在 model_ir.json 无法解析时
`except Exception: continue`，把「门禁无法核验」当成「无需核验」——损坏的输入
被静默放行，与「门禁」语义矛盾。涉及：
  * check_parameter_provenance（参数来源，L4）
  * check_evidence_obligations（证据义务矩阵，L4/G4）
  * check_parsimony_budget（复杂度预算，L4/G5）

契约（本次加固）：
  * 活跃实例的 model_ir.json 存在但损坏（非法 JSON / 不可解码）→ FAIL，
    消息须指名实例目录与原因；
  * 活跃实例本就无 model_ir.json（非建模产出）→ 跳过，不误伤（既有语义）；
  * projects/ 无活跃实例（库模式）→ 跳过（既有语义）。

这些测试先于实现（RED）：当前实现在损坏 JSON 下返回 PASS，故
test_corrupt_model_ir_fails_closed 会在加固前失败。
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.validate import (  # noqa: E402
    check_evidence_obligations,
    check_parameter_provenance,
    check_parsimony_budget,
)

_CHECKS = [
    ("check_parameter_provenance", check_parameter_provenance),
    ("check_evidence_obligations", check_evidence_obligations),
    ("check_parsimony_budget", check_parsimony_budget),
]


def _corrupt_mir_proj(root):
    """活跃实例 projects/t 存在，model_ir.json 内容为非法 JSON。"""
    proj = root / "projects" / "t"
    proj.mkdir(parents=True)
    (proj / "model_ir.json").write_text("{ 这不是合法 JSON", encoding="utf-8")
    return root


def _missing_mir_proj(root):
    """活跃实例 projects/t 存在，但无 model_ir.json（非建模产出）。"""
    (root / "projects" / "t").mkdir(parents=True)
    return root


def _empty_projects(root):
    """库模式：projects/ 存在但无活跃实例。"""
    (root / "projects").mkdir(parents=True)
    return root


def test_corrupt_model_ir_fails_closed(tmp_path):
    """活跃实例的 model_ir.json 损坏 → 三个门禁均 FAIL（指名文件与原因）。"""
    for label, fn in _CHECKS:
        root = tmp_path / label
        ok, msg = fn(_corrupt_mir_proj(root))
        assert not ok, f"[{label}] 损坏的 model_ir.json 不得放行：{msg}"
        assert "model_ir.json" in msg, f"[{label}] 消息须指名文件：{msg}"
        assert "t" in msg, f"[{label}] 消息须指名实例：{msg}"


def test_missing_model_ir_is_skipped(tmp_path):
    """活跃实例无 model_ir.json → 跳过（既有语义，不误伤）。"""
    for label, fn in _CHECKS:
        root = tmp_path / label
        ok, msg = fn(_missing_mir_proj(root))
        assert ok, f"[{label}] 无 model_ir.json 应跳过而非失败：{msg}"


def test_no_active_instance_is_skipped(tmp_path):
    """库模式（projects/ 无活跃实例）→ 跳过（既有语义）。"""
    for label, fn in _CHECKS:
        root = tmp_path / label
        ok, msg = fn(_empty_projects(root))
        assert ok, f"[{label}] 无活跃实例应跳过：{msg}"


def test_live_instances_not_affected():
    """回归护栏：真实 live 实例（cumcm*）不得被误伤（损坏才 FAIL，完好仍 PASS）。"""
    for label, fn in _CHECKS:
        ok, msg = fn(REPO)
        assert ok, f"[{label}] live 实例被误判失败：{msg}"
