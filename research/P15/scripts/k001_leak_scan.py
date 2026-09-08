#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k001_leak_scan.py — 结构案例泄漏门禁

目的：确保注入 C/D 臂的 structural case 承载的是「建模结构」而不是「答案」。

规则（见 protocol/frozen_specs/case_set.yaml#leak_gate）：
    R1 答案标记词
    R2 结果赋值（结果/答案/最优 … = 数字）
    R3 数值密度（不同数值字面量 > 10）
    R4 结果型图表引用（WARN，不阻断）

用法:
    py -3.12 research/P15/scripts/k001_leak_scan.py            # 扫描全部 structural case
    py -3.12 research/P15/scripts/k001_leak_scan.py --all      # 同时列出 solution 层（仅提示）

退出码：0 = 全部通过；1 = 存在 FAIL。
零第三方依赖（PyYAML 除外）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k001_common as K  # noqa: E402

ANSWER_MARKERS = [
    "答案为", "答案是", "最优解为", "最优解是", "最终结果为", "最终结果",
    "计算得", "计算得到", "求得", "解得", "数值结果", "仿真结果",
    "实验结果", "最优值", "答案：", "答案:", "最终答案",
]

# 否定上下文：标记词出现在「不含 / 不提供 / 无 / 没有 / 避免」等之后时属于免责声明，不算泄漏
NEGATION_CUES = ["不含", "不提供", "不包括", "无", "没有", "避免", "禁止", "不得", "而非"]
NEGATION_WINDOW = 14

RESULT_ASSIGN = re.compile(
    r"(结果|答案|最优|总计|共|得|等于)[^。；\n]{0,12}[=＝:：]\s*[-+]?\d"
)

NUMBER_LITERAL = re.compile(r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?![\w.])")
RESULT_FIGTABLE = re.compile(r"(表\s*\d|图\s*\d|见表|见图)")

MAX_NUMERIC_LITERALS = 10


def scan_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    failures, warnings = [], []

    # R1 答案标记词（否定式声明除外）
    for m in ANSWER_MARKERS:
        for mo in re.finditer(re.escape(m), text):
            prefix = text[max(0, mo.start() - NEGATION_WINDOW): mo.start()]
            if any(cue in prefix for cue in NEGATION_CUES):
                continue
            snippet = text[max(0, mo.start() - 20): mo.end() + 30].replace("\n", " ")
            failures.append({"rule": "R1_answer_marker", "value": m, "context": snippet})

    # R2 结果赋值
    for mo in RESULT_ASSIGN.finditer(text):
        failures.append({
            "rule": "R2_result_assignment",
            "value": mo.group(0),
            "context": text[max(0, mo.start() - 25): mo.end() + 25].replace("\n", " "),
        })

    # R3 数值密度
    nums = set(NUMBER_LITERAL.findall(text))
    if len(nums) > MAX_NUMERIC_LITERALS:
        sample = sorted(nums)[:15]
        failures.append({
            "rule": "R3_numeric_density",
            "value": f"{len(nums)} distinct numeric literals (max {MAX_NUMERIC_LITERALS})",
            "context": "sample=" + ",".join(sample),
        })

    # R4 结果型图表（WARN）
    for mo in RESULT_FIGTABLE.finditer(text):
        warnings.append({
            "rule": "R4_result_figure_table",
            "value": mo.group(0),
            "context": text[max(0, mo.start() - 25): mo.end() + 25].replace("\n", " "),
        })

    return {
        "path": K.rel(path),
        "exists": True,
        "numeric_literals": len(nums),
        "failures": failures,
        "warnings": warnings,
        "passed": not failures,
    }


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    show_solution = "--all" in argv

    results = []
    for pid, relp in sorted(K.case_index("structural").items()):
        p = K.ROOT / relp
        if not p.exists():
            results.append({"path": relp, "exists": False, "passed": False,
                            "failures": [{"rule": "R0_missing", "value": relp, "context": ""}],
                            "warnings": [], "numeric_literals": 0})
            continue
        results.append(scan_file(p))

    failed = [r for r in results if not r["passed"]]

    print("=" * 72)
    print("P15-K001 structural case 泄漏扫描")
    print("=" * 72)
    for r in results:
        flag = "PASS" if r["passed"] else "FAIL"
        print(f"[{flag}] {r['path']}  数值字面量={r.get('numeric_literals', '-')}")
        for f in r["failures"]:
            print(f"        ✗ {f['rule']}: {f['value']}")
            if f["context"]:
                print(f"          ctx: {f['context'][:100]}")
        for w in r["warnings"]:
            print(f"        ! {w['rule']}: {w['value']}")

    if show_solution:
        print("\n[solution 层（本轮不注入，仅提示）]")
        for pid, relp in sorted(K.case_index("solution").items()):
            p = K.ROOT / relp
            print(f"    {relp}  exists={p.exists()}")

    print("-" * 72)
    if failed:
        print(f"[FAIL] {len(failed)}/{len(results)} 份结构案例未通过泄漏门禁，禁止进入 bundle。")
        return 1
    print(f"[PASS] {len(results)}/{len(results)} 份结构案例通过泄漏门禁。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
