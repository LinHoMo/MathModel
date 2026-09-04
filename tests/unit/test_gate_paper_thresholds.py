"""测试 gate.py 正确接入 validate_project.py 的版面阈值，拦截不达标论文。"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# 使用新建的测试项目（不达标论文，用于验证 gate 拦截）
PROJ = ROOT / "projects" / "cumcm2024anew"
GATE_PY = ROOT / "core" / "tools" / "gate.py"


class TestGatePaperThresholds(unittest.TestCase):
    """新建项目（无完整论文）应被 gate.py 拦截。"""

    @classmethod
    def setUpClass(cls):
        cls.has_proj = PROJ.exists()
        cls.has_paper = (PROJ / "paper" / "main.tex").exists()

    def test_gate_all_exit_nonzero(self):
        """gate.py cumcm2024anew --level all 必须 EXIT != 0（应硬失败）。"""
        if not self.has_proj:
            self.skipTest("测试项目不存在，跳过")
        import subprocess
        r = subprocess.run(
            [sys.executable, str(GATE_PY), str(PROJ), "--level", "all"],
            cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        self.assertNotEqual(r.returncode, 0,
                            "新建项目不应全绿通过：缺少论文产物")

    def test_gate_hard_fail_paper_dimensions(self):
        """硬失败必须含 paper pages / paper words 等版面阈值。"""
        if not self.has_proj or not self.has_paper:
            self.skipTest("测试项目或论文不存在，跳过")
        import subprocess
        r = subprocess.run(
            [sys.executable, str(GATE_PY), str(PROJ), "--level", "all"],
            cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        combined = (r.stdout or "") + (r.stderr or "")
        self.assertIn("paper pages", combined,
                       "gate.py 应报告 paper pages 硬失败")
        self.assertIn("paper words", combined,
                       "gate.py 应报告 paper words 硬失败")


if __name__ == "__main__":
    unittest.main()
