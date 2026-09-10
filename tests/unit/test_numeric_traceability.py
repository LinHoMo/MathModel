# -*- coding: utf-8 -*-
"""数值追溯门禁（check_numeric_traceability）的溯源目标语义测试。

背景（projects 反馈）：
  cumcm2026a 从 v1.0 指数近似边界升级为 v1.1 附件实测数据驱动后，model.md 中的
  题面给定物理常数（如 3850 / 650）无法追溯到 all_results.json（它们来自题面附录，
  不是计算结果），导致追溯比例被误压低。修复：题面输入 inputs/problem.txt 给出的
  常数同样是合法溯源目标（结果→all_results.json，题面常数→inputs/problem.txt）。

验收语义：
  * 仅出现在题面的常数 → 可追溯（不误杀）
  * 结果数字 → 可追溯到 all_results.json
  * 伪造数字（结果与题面都没有）→ 拉低比例 → 失败（不放过）
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.validate import check_numeric_traceability  # noqa: E402


def _make_project(tmp_path, *, md_text, results, problem_text=""):
    proj = tmp_path / "projects" / "testproj"
    (proj / "inputs").mkdir(parents=True)
    (proj / "inputs" / "problem.txt").write_text(problem_text, encoding="utf-8")
    import json
    (proj / "all_results.json").write_text(
        json.dumps(results, ensure_ascii=False), encoding="utf-8")
    (proj / "model.md").write_text(md_text, encoding="utf-8")
    return tmp_path


def test_results_numbers_trace(tmp_path):
    """结果数字溯源到 all_results.json。"""
    root = _make_project(
        tmp_path,
        md_text="烘干时长 57.17 h，最终半径 1.20 cm。",
        results={"drying_time_h": 57.1722, "final_radius_cm": 1.200},
    )
    ok, msg = check_numeric_traceability(root)
    assert ok, msg


def test_problem_statement_constants_trace(tmp_path):
    """仅出现在题面的物理常数可追溯（不因升级边界条件而误杀）。"""
    root = _make_project(
        tmp_path,
        md_text=(
            "扩散系数 D = 2.4e-3 e^{-0.45/C} e^{-3850/T}，"
            "密度 ρ = 650 + 128 C，热导率 k = 0.21 + 0.38 C/(C+1)。"
        ),
        results={"drying_time_h": 57.1722},
        problem_text=(
            "ρ = 650 + 128 C ... k = 0.21 + 0.38·C/(C+1) ... "
            "D = 2.4e-3 e^(−0.45/C) e^(−3850/T)"
        ),
    )
    ok, msg = check_numeric_traceability(root)
    assert ok, f"题面常数应可追溯，实际: {msg}"


def test_fabricated_number_fails(tmp_path):
    """伪造数字（结果与题面都没有）拉低比例 → 失败。"""
    # 10 个数字中只有 1 个能追溯 → 比例 10% < 90%
    md = " ".join(str(1000 + i * 7) for i in range(9)) + " 57.1722"
    root = _make_project(tmp_path, md_text=md, results={"drying_time_h": 57.1722})
    ok, msg = check_numeric_traceability(root)
    assert not ok, "伪造数字必须触发失败"
    assert "数值追溯比例" in msg
