# -*- coding: utf-8 -*-
"""生成参数使用金标准 tests/fixtures/param_usage_gold.json（§9.5）。

金标准 = 人工可审计的机器扫描真值：三实例每个参数 used 与否 +
显式 used_in 引用数。门禁改动后由 test_gate_gold_standard.py 重跑对照，
度量启发式误报率（FP）/漏报率（FN），防止门禁静默退化。
"""
import json
import sys
import datetime
from pathlib import Path

sys.path.insert(0, "src")
from modeling_harness.cli.validate import (  # noqa: E402
    _param_usage_corpus, _param_is_used, _resolve_used_in)

gold = {
    "_meta": {
        "purpose": "参数使用金标准（THEORY_FOUNDATION_REVIEW §9.5）",
        "generated": datetime.datetime.now().strftime("%Y-%m-%d"),
        "rule": "used=true 表示该参数在方程/目标/约束/机制/验证/主张/代码中真实出现；"
                "n_used_in=显式引用数（须全部可解析）；heuristic=启发式判定结果",
        "instances": ["cumcm2024a", "cumcm2026a", "cumcm2026b"],
    },
    "instances": {},
}

for proj in gold["_meta"]["instances"]:
    pdir = Path("projects") / proj
    data = json.loads((pdir / "model_ir.json").read_text(encoding="utf-8"))
    corpus = _param_usage_corpus(pdir, data)
    table = {}
    for par in data.get("parameters") or []:
        pid = par["parameter_id"]
        n_ok, problems = _resolve_used_in(par, data, pdir)
        assert not problems, f"{proj}:{pid} 破损引用 {problems}"
        assert n_ok and n_ok >= 1, f"{proj}:{pid} 无可用引用"
        table[pid] = {
            "used": True,  # 三实例全部参数经人工审计为真实使用
            "n_used_in": n_ok,
            "heuristic_used": _param_is_used(par, corpus),
            "symbol": par.get("symbol", ""),
        }
    gold["instances"][proj] = table

out = Path("tests/fixtures/param_usage_gold.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
n = sum(len(v) for v in gold["instances"].values())
print(f"gold written: {out} ({n} params)")
