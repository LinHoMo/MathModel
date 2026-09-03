"""测试 gate.py 正确接入 validate_project.py 的版面阈值，拦截不达标论文。"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJ = ROOT / "projects" / "cumcm2024a"
GATE_PY = ROOT / "core" / "tools" / "gate.py"


class TestGatePaperThresholds(unittest.TestCase):
    """cumcm2024a（9 页 / 3656 字 / 3 表）应被 gate.py 拦截。"""

    def test_gate_all_exit_nonzero(self):
        """gate.py cumcm2024a all 必须 EXIT != 0（应硬失败）。"""
        import subprocess
        r = subprocess.run(
            [sys.executable, str(GATE_PY), "cumcm2024a", "all"],
            cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        self.assertNotEqual(r.returncode, 0,
                            "cumcm2024a 不应全绿通过：9 页 < 25 页 min")

    def test_gate_hard_fail_paper_dimensions(self):
        """硬失败必须含 paper pages / paper words 等版面阈值。"""
        import subprocess
        r = subprocess.run(
            [sys.executable, str(GATE_PY), "cumcm2024a", "all"],
            cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        combined = (r.stdout or "") + (r.stderr or "")
        self.assertIn("paper pages", combined,
                       "gate.py 应报告 paper pages 硬失败")
        self.assertIn("paper words", combined,
                       "gate.py 应报告 paper words 硬失败")


if __name__ == "__main__":
    unittest.main()
