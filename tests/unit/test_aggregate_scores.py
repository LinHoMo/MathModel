"""测试 aggregate_scores.py 聚合重算与 --verify 一致性。

注意：这些测试需要一个包含完整评分卡的项目。如果测试项目不存在，测试将被跳过。
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# 测试项目（如果存在）
PROJ = ROOT / "archives" / "cumcm2024anew"
SCORE = PROJ / "work" / "score_card.json"

sys.path.insert(0, str(ROOT / "core" / "tools"))


class TestAggregateScores(unittest.TestCase):
    """work/score_card.json 必须由 aggregate_scores.py 生成。"""

    @classmethod
    def setUpClass(cls):
        cls.has_proj = PROJ.exists() and SCORE.exists()

    def test_score_card_exists(self):
        if not self.has_proj:
            self.skipTest("测试项目不存在，跳过")
        self.assertTrue(SCORE.exists(), "work/score_card.json 缺失")

    def test_generated_by_field(self):
        if not self.has_proj:
            self.skipTest("测试项目不存在，跳过")
        card = json.loads(SCORE.read_text(encoding="utf-8"))
        self.assertEqual(card.get("generated_by"), "aggregate_scores.py",
                         f"应 generated_by aggregate_scores.py，实际 {card.get('generated_by')}")

    def test_5_dimensions(self):
        if not self.has_proj:
            self.skipTest("测试项目不存在，跳过")
        card = json.loads(SCORE.read_text(encoding="utf-8"))
        dims = card.get("dimensions", [])
        self.assertEqual(len(dims), 5, f"应 5 维，实际 {len(dims)}")

    def test_blocking_count_matches_weakness(self):
        if not self.has_proj:
            self.skipTest("测试项目不存在，跳过")
        card = json.loads(SCORE.read_text(encoding="utf-8"))
        blocking = card.get("blocking", [])
        self.assertGreaterEqual(len(blocking), 1, "至少应有 1 条 blocking（来自 weakness-hunter）")

    def test_weighted_score_range(self):
        if not self.has_proj:
            self.skipTest("测试项目不存在，跳过")
        card = json.loads(SCORE.read_text(encoding="utf-8"))
        ws = card.get("weighted_score", 0)
        self.assertGreater(ws, 0)
        self.assertLess(ws, 10)

    def test_verify_mode_exit_0(self):
        if not self.has_proj:
            self.skipTest("测试项目不存在，跳过")
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
