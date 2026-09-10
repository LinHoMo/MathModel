# -*- coding: utf-8 -*-
"""P2-4：V2 兼容层路径修复验收测试。"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core" / "tools"))

import orchestrator  # noqa: E402


class TestV2LegacySkillPath:
    def test_skill_path_points_to_legacy_hands(self):
        p = orchestrator._skill_path("modeler", "model-builder")
        assert "legacy" in str(p) and "hands" in str(p)
        assert p.exists()

    def test_skill_path_all_four_hands_resolve(self):
        for hand, agent in [("modeler", "model-builder"),
                            ("programmer", "code-implementer"),
                            ("writer", "section-writer"),
                            ("reviewer", "scorer-academic")]:
            p = orchestrator._skill_path(hand, agent)
            assert p.exists(), f"{hand}/{agent} SKILL.md 必须存在"
