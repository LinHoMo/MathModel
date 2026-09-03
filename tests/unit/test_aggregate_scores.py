"""测试 aggregate_scores.py 聚合重算与 --verify 一致性。"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJ = ROOT / "projects" / "cumcm2024a"
SCORE = PROJ / "work" / "score_card.json"

sys.path.insert(0, str(ROOT / "core" / "tools"))


class TestAggregateScores(unittest.TestCase):
    """work/score_card.json 必须由 aggregate_scores.py 生成。"""

    def test_score_card_exists(self):
        self.assertTrue(SCORE.exists(), "work/score_card.json 缺失")

    def test_generated_by_field(self):
        card = json.loads(SCORE.read_text(encoding="utf-8"))
        self.assertEqual(card.get("generated_by"), "aggregate_scores.py",
                         f"应 generated_by aggregate_scores.py，实际 {card.get('generated_by')}")

    def test_5_dimensions(self):
        card = json.loads(SCORE.read_text(encoding="utf-8"))
        dims = card.get("dimensions", [])
        self.assertEqual(len(dims), 5, f"应 5 维，实际 {len(dims)}")

    def test_blocking_count_matches_weakness(self):
        """blocking 数组至少含 weakness 卡的 blocking 项。"""
        card = json.loads(SCORE.read_text(encoding="utf-8"))
        blocking = card.get("blocking", [])
        # weakness-hunter 实测 blocking=1
        self.assertGreaterEqual(len(blocking), 1, "至少应有 1 条 blocking（来自 weakness-hunter）")

    def test_weighted_score_range(self):
        card = json.loads(SCORE.read_text(encoding="utf-8"))
        ws = card.get("weighted_score", 0)
        self.assertGreater(ws, 0)
        self.assertLess(ws, 10)

    def test_verify_mode_exit_0(self):
        """aggregate_scores.py --verify 必须 EXIT 0。"""
        import subprocess
        r = subprocess.run(
            [sys.executable, str(ROOT / "core" / "tools" / "aggregate_scores.py"),
             str(PROJ), "--verify"],
            cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0,
                         f"--verify EXIT {r.returncode}: {r.stdout}{r.stderr}")


if __name__ == "__main__":
    unittest.main()
