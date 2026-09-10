# -*- coding: utf-8 -*-
"""P1-4 验收：经验常数 advisory 标注 + 不参与 PASS/FAIL 判定。

验收语义（ROADMAP P1-4）：
  * 所有 confidence 值标注为 advisory（grep 可审计）
  * 选型/门禁的 PASS/FAIL 不依赖经验置信度数值
  * integrity_gate 政策阈值有来源声明（非无溯源外推）
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


class TestAdvisoryConstants:
    """P1-4 验收。"""

    def test_handlers_confidence_docstring_advisory(self):
        s = _read("core/runtime/execution/handlers.py")
        assert "advisory 置信度" in s, \
            "_decision_confidence 必须声明 advisory"
        assert "不参与任何 PASS/FAIL 判定" in s, \
            "必须声明 confidence 不参与判定"

    def test_findings_confidence_annotated(self):
        s = _read("core/runtime/writing/findings.py")
        assert s.count("advisory（经验常数）") >= 3, \
            "findings.py 三处 confidence 必须标注 advisory"

    def test_selection_confidence_annotated(self):
        s = _read("core/runtime/modeling/selection.py")
        assert "advisory（经验常数）" in s, \
            "selection.py confidence 必须标注 advisory"
        assert "最终选型由执行证据裁决" in s

    def test_integrity_gate_policy_threshold_declared(self):
        s = _read("core/validators/modules/integrity_gate.py")
        assert "政策阈值" in s and "非经验外推" in s, \
            "integrity_gate 必须声明政策阈值来源"

    def test_confidence_not_gating_decision(self):
        """选型 decision 的 PASS/FAIL 由 VR 证据驱动，不依赖 confidence。

        直接验证 decision 构建路径：confidence 仅写入展示字段，
        状态由候选验证证据决定。
        """
        s = _read("core/runtime/execution/handlers.py")
        # confidence 赋值处上下文：chosen 由 VR 证据决定，confidence 仅作展示
        assert "chosen = best_mir" in s
        # PASS/FAIL 判定节点（do_model_validation）不含 confidence 读取
        v = s.index("def do_model_validation")
        seg = s[v:s.index("def _diagnose_and_draft", v)]
        assert "confidence" not in seg, \
            "验证判定路径不得读取经验置信度"
