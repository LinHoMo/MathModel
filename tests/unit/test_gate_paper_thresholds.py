# -*- coding: utf-8 -*-
"""gate.py 论文版面阈值接线的回归测试。

背景：gate.py 此前完全不读 env 的 min_pages/min_words/min_tables/page_fill_ratio，
一篇 9 页 2738 字的论文因此拿到「全链路 79 通过 / 0 硬失败 / EXIT 0」，
而 validate_project.py 对同一产物报 10 个 HARD。本测试锁住接线，防止再次脱落。
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import gate  # noqa: E402
import gatelib as G  # noqa: E402
import state as S  # noqa: E402
import validate_project as VP  # noqa: E402

FINAL_VALIDATOR = ("writer", "final-validator")


@pytest.fixture(autouse=True)
def _clean_vp_results():
    """VP 用模块级 results 全局通信，测试之间必须清空。"""
    VP.results.clear()
    gate._VP_INIT_DONE.clear()
    yield
    VP.results.clear()
    gate._VP_INIT_DONE.clear()


# ---------------------------------------------------------------- 接线完整性


def test_all_vp_paper_checks_are_wired():
    """_VP_PAPER_CHECKS 列出的 8 项必须全部出现在 final-validator 门禁里。

    这条测试是接线脱落的主要防线：删掉任何一条 lambda 就会红。
    """
    import inspect

    lambdas = gate.GATES[FINAL_VALIDATOR]
    wired = set()
    for fn in lambdas:
        src = inspect.getsource(fn)
        for name in gate._VP_PAPER_CHECKS:
            if f'"{name}"' in src:
                wired.add(name)
    assert wired == set(gate._VP_PAPER_CHECKS), (
        f"未接线的版面检查: {set(gate._VP_PAPER_CHECKS) - wired}"
    )


def test_vp_checks_run_after_latex_compile():
    """版面检查必须排在 _check_latex_compiles 之后。

    check_paper_pages 与 check_page_fill_ratio 读编译产生的 main.log，
    顺序颠倒会让二者恒判「无 main.log」。
    """
    import inspect

    lambdas = gate.GATES[FINAL_VALIDATOR]
    sources = [inspect.getsource(fn) for fn in lambdas]
    compile_idx = next(i for i, s in enumerate(sources)
                       if "_check_latex_compiles" in s)
    first_vp_idx = next(i for i, s in enumerate(sources)
                        if "_vp_check" in s)
    assert first_vp_idx > compile_idx, "版面检查跑在 LaTeX 编译之前，main.log 尚不存在"


def test_vp_check_names_are_in_lite_soften():
    """8 项版面检查发出的判定名必须都在 LITE_SOFTEN 里，否则 lite 模式会硬阻塞弱模型。"""
    expected = {"paper pages", "page fill ratio", "paper words", "paper tables",
                "paper figures", "paper equations", "paper references",
                "pdf compile chain"}
    assert expected <= gate.LITE_SOFTEN, f"缺失: {expected - gate.LITE_SOFTEN}"


def test_vp_paper_checks_names_match_validate_project():
    """_VP_PAPER_CHECKS 里的函数名必须真实存在于 validate_project，防止改名后静默失效。"""
    for name in gate._VP_PAPER_CHECKS:
        assert callable(getattr(VP, name, None)), f"validate_project 无 {name}"


# ---------------------------------------------------------------- 适配器语义


def test_vp_check_maps_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(VP, "check_paper_tables",
                        lambda p: VP._pas("paper tables", "4 tables (>= 4)"))
    r = gate._vp_check(tmp_path, "check_paper_tables")
    assert r.ok is True and r.name == "paper tables"


def test_vp_check_maps_hard(tmp_path, monkeypatch):
    monkeypatch.setattr(VP, "check_paper_tables",
                        lambda p: VP._hard("paper tables", "3 tables (< 4)"))
    r = gate._vp_check(tmp_path, "check_paper_tables")
    assert r.ok is False and r.hard is True


def test_vp_check_maps_warn_to_soft_fail(tmp_path, monkeypatch):
    """WARN 必须映射为不阻塞失败，否则无 main.log 的历史项目会被硬卡。"""
    monkeypatch.setattr(VP, "check_paper_pages",
                        lambda p: VP._warn("paper pages", "无 main.log"))
    r = gate._vp_check(tmp_path, "check_paper_pages")
    assert r.ok is False and r.hard is False


def test_vp_check_picks_most_severe(tmp_path, monkeypatch):
    """一个检查发多条判定时取最严重的（HARD > WARN > PASS）。"""
    def _multi(p):
        VP._pas("x", "ok")
        VP._warn("x", "hmm")
        VP._hard("paper words", "3656 < 18000")
    monkeypatch.setattr(VP, "check_paper_words", _multi)
    r = gate._vp_check(tmp_path, "check_paper_words")
    assert r.ok is False and r.hard is True and r.name == "paper words"


def test_vp_check_resets_results(tmp_path, monkeypatch):
    """适配器必须复位 VP.results，否则跨调用累积会串数据。"""
    monkeypatch.setattr(VP, "check_paper_tables",
                        lambda p: VP._pas("paper tables", "ok"))
    gate._vp_check(tmp_path, "check_paper_tables")
    gate._vp_check(tmp_path, "check_paper_tables")
    assert len(VP.results) == 0, f"VP.results 未复位，累积了 {len(VP.results)} 条"


def test_vp_check_unknown_function(tmp_path):
    r = gate._vp_check(tmp_path, "check_no_such_thing")
    assert r.ok is False and "无此检查函数" in r.detail


def test_vp_check_exception_is_soft_fail(tmp_path, monkeypatch):
    """单个检查抛异常不应中断整条门禁。"""
    def _boom(p):
        raise RuntimeError("炸了")
    monkeypatch.setattr(VP, "check_paper_tables", _boom)
    r = gate._vp_check(tmp_path, "check_paper_tables")
    assert r.ok is False and r.hard is False and "炸了" in r.detail
    assert len(VP.results) == 0


# ---------------------------------------------------------------- 真实端到端


def test_vp_check_real_tables_below_threshold(tmp_path):
    """不 stub：真跑 check_paper_tables，3 个表 < env 的 min_tables=4 → 硬失败。"""
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "main.tex").write_text(
        "\\documentclass{article}\\begin{document}"
        + "\\begin{table}t\\end{table}" * 3
        + "\\end{document}", encoding="utf-8")
    r = gate._vp_check(tmp_path, "check_paper_tables")
    assert r.ok is False, "3 个表应当不达标"
    assert r.name == "paper tables"


def test_vp_check_real_tables_meets_threshold(tmp_path):
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "main.tex").write_text(
        "\\documentclass{article}\\begin{document}"
        + "\\begin{table}t\\end{table}" * 6
        + "\\end{document}", encoding="utf-8")
    r = gate._vp_check(tmp_path, "check_paper_tables")
    assert r.ok is True, f"6 个表应当达标，实得: {r}"


def test_real_project_gate_blocks_thin_paper():
    """对仓库内真实产物 cumcm2024a 跑版面检查，必须拦住这篇 9 页论文。

    这是本次修复的原始症状：论文 9 页 / 2738 中文字符 / 3 表，
    而 env 阈值是 25 页 / 18000 字 / 4 表。若此测试变绿说明门禁又脱落了。
    """
    proj = G.project_dir("cumcm2024a")
    if not (proj / "paper" / "main.tex").exists():
        pytest.skip("cumcm2024a 产物不在仓库内")
    words = gate._vp_check("cumcm2024a", "check_paper_words")
    tables = gate._vp_check("cumcm2024a", "check_paper_tables")
    assert words.ok is False, f"3656 字符应判不达标，实得 {words}"
    assert tables.ok is False, f"3 个表应判不达标，实得 {tables}"


# ---------------------------------------------------------------- state.py help


def test_state_help_lists_all_four_hands(capsys, monkeypatch):
    """state.py --help 必须列出全部四手；此前漏写 reviewer。"""
    monkeypatch.setattr(sys, "argv", ["state.py", "--help"])
    with pytest.raises(SystemExit):
        S.main()
    out = capsys.readouterr().out
    hands = {h for h, _a, _s in S.PIPELINE}
    assert hands == {"modeler", "programmer", "writer", "reviewer"}
    for h in hands:
        assert h in out, f"--help 未提及 {h}"
