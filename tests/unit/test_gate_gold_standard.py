# -*- coding: utf-8 -*-
"""§9.5 门禁金标准度量：启发式 vs 人工审计真值，显式引用可解析性。

金标准 tests/fixtures/param_usage_gold.json 固化三实例 46 个参数的
used 真值（人工可审计）。本测试：
  1. 每个参数的 used_in 必须全部可解析，且引用数与金标准一致；
  2. 启发式判定与金标准真值对照，误报 FP / 漏报 FN 必须为 0
     （当前语料基线；启发式规则若改动，本测试显式暴露质量漂移）；
  3. 金标准覆盖的参数集合与实例一致（防止实例增参后金标准失修）。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.validate import (  # noqa: E402
    _param_usage_corpus, _param_is_used, _resolve_used_in)

GOLD = json.loads((REPO / "tests" / "fixtures" /
                   "param_usage_gold.json").read_text(encoding="utf-8"))


def _load(proj):
    pdir = REPO / "projects" / proj
    data = json.loads((pdir / "model_ir.json").read_text(encoding="utf-8"))
    return pdir, data


def test_gold_covers_every_parameter():
    """金标准参数集合 == 实例参数集合（增删参数必须同步金标准）。"""
    for proj, table in GOLD["instances"].items():
        _, data = _load(proj)
        actual = {p["parameter_id"] for p in data.get("parameters") or []}
        assert set(table) == actual, f"{proj} 金标准与实例参数集合不一致"


def test_every_used_in_resolves_and_matches_gold_count():
    """used_in 全部可解析，且引用数 == 金标准 n_used_in。"""
    for proj, table in GOLD["instances"].items():
        pdir, data = _load(proj)
        for par in data.get("parameters") or []:
            pid = par["parameter_id"]
            n_ok, problems = _resolve_used_in(par, data, pdir)
            assert not problems, f"{proj}:{pid} 破损引用 {problems}"
            assert n_ok == table[pid]["n_used_in"], (
                f"{proj}:{pid} 引用数漂移 {n_ok} != "
                f"{table[pid]['n_used_in']}（金标准失修或声明被改）")


def test_heuristic_vs_gold_zero_fp_fn():
    """启发式对金标准的误报/漏报均为 0（度量门禁质量，锁基线）。"""
    fp, fn = [], []
    for proj, table in GOLD["instances"].items():
        pdir, data = _load(proj)
        corpus = _param_usage_corpus(pdir, data)
        for par in data.get("parameters") or []:
            pid = par["parameter_id"]
            gold_used = table[pid]["used"]
            heur = _param_is_used(par, corpus)
            if heur and not gold_used:
                fp.append(f"{proj}:{pid}")
            if gold_used and not heur:
                fn.append(f"{proj}:{pid}")
    assert not fp, f"启发式误报（把死参数判活）{fp}"
    assert not fn, f"启发式漏报（把活参数判死）{fn}"


def test_gold_all_used_baseline():
    """基线事实：三实例 46 参数全部真实使用（无死参数）。"""
    total = sum(len(t) for t in GOLD["instances"].values())
    n_used = sum(1 for t in GOLD["instances"].values()
                 for row in t.values() if row["used"])
    assert total == 46
    assert n_used == 46
