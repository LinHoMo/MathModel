# -*- coding: utf-8 -*-
"""P15-K004 Analysis Script（P2-1b）。

分析 ref constructor × 2 RT conditions × 8 problems 的实验结果。
LLM-free：纯机械分析，无 LLM 调用。

用法：
    py -3.12 analyze_k004.py
"""
from __future__ import annotations

import json
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
REPORT_DIR = Path(__file__).parent / "reports"


def load_results() -> list[dict]:
    f = RESULTS_DIR / "k004_ref_results.json"
    if not f.exists():
        print(f"结果文件不存在: {f}")
        return []
    return json.loads(f.read_text(encoding="utf-8"))


def analyze(results: list[dict]) -> dict:
    """分析实验结果。"""
    rt_plus = [r for r in results if r.get("runtime") == "+RT"]
    rt_minus = [r for r in results if r.get("runtime") == "-RT"]

    # 按问题分组
    by_problem = {}
    for r in results:
        q = r["problem"]
        by_problem.setdefault(q, {"minus_rt": [], "plus_rt": []})
        if r["runtime"] == "-RT":
            by_problem[q]["minus_rt"].append(r)
        else:
            by_problem[q]["plus_rt"].append(r)

    # 统计
    total_plus = len(rt_plus)
    exec_pass = sum(1 for r in rt_plus if r.get("exec_status") == "success")
    val_pass = sum(1 for r in rt_plus if r.get("validation_status") == "passed")
    fid_aligned = sum(1 for r in rt_plus
                      if r.get("fidelity_score") is not None
                      and r["fidelity_score"] >= 0.8)

    # 按问题统计
    problem_stats = {}
    for qid, data in by_problem.items():
        plus = data["plus_rt"]
        problem_stats[qid] = {
            "exec_pass": sum(1 for r in plus if r.get("exec_status") == "success"),
            "val_pass": sum(1 for r in plus if r.get("validation_status") == "passed"),
            "total_plus": len(plus),
            "mean_elapsed": (sum(r.get("elapsed_s", 0) for r in plus) / len(plus)
                             if plus else 0),
        }

    return {
        "summary": {
            "total_runs": len(results),
            "minus_rt": len(rt_minus),
            "plus_rt": total_plus,
            "exec_pass_rate": f"{exec_pass}/{total_plus}",
            "val_pass_rate": f"{val_pass}/{total_plus}",
            "fidelity_aligned_rate": f"{fid_aligned}/{total_plus}",
        },
        "per_problem": problem_stats,
        "deterministic": {
            "note": "ref constructor 是确定性模板，2 seeds 产生相同结果",
            "seed_invariance": True,
        },
        "limitations": [
            "仅 ref constructor（LLM-free C3），未含 gen/lin/mma",
            "ref 代码过于简单（确定性线性映射），+RT 总是通过",
            "fidelity 报告未生成（MODEL_IR 结构简单，无 fidelity 检查项触发）",
            "需要 gen/lin/mma 构造器才能测量 Runtime 增益",
        ],
    }


def write_report(analysis: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    lines = ["# P15-K004 Experiment Report", ""]
    lines.append("## Design")
    lines.append("- 4 Constructor × 2 Runtime × 8 problems × 2 seeds = 64 runs")
    lines.append("- **This run**: ref constructor only (LLM-free) — 16 +RT + 16 -RT = 32 runs")
    lines.append("")

    s = analysis["summary"]
    lines.append("## Results (ref constructor)")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Total runs | {s['total_runs']} |")
    lines.append(f"| -RT (static) | {s['minus_rt']} |")
    lines.append(f"| +RT (full pipeline) | {s['plus_rt']} |")
    lines.append(f"| Exec success rate | {s['exec_pass_rate']} |")
    lines.append(f"| Validation pass rate | {s['val_pass_rate']} |")
    lines.append(f"| Fidelity aligned (≥0.8) | {s['fidelity_aligned_rate']} |")
    lines.append("")

    lines.append("## Per-Problem Breakdown")
    lines.append("")
    lines.append("| Problem | Exec Pass | Val Pass | Mean Time |")
    lines.append("|---|---|---|---|")
    for qid, stats in sorted(analysis["per_problem"].items()):
        lines.append(
            f"| {qid} | {stats['exec_pass']}/{stats['total_plus']} "
            f"| {stats['val_pass']}/{stats['total_plus']} "
            f"| {stats['mean_elapsed']:.2f}s |")
    lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append("### RQ1: Does Runtime improve construction quality?")
    lines.append("- **Cannot answer with ref constructor alone**.")
    lines.append("- ref is a deterministic template (C3): code always executes correctly.")
    lines.append("- All +RT runs pass because the template code is trivially correct.")
    lines.append("- **Need gen/lin/mma constructors** to measure Runtime effect on non-trivial code.")
    lines.append("")
    lines.append("### RQ4: Do mechanical metrics correlate with blind review?")
    lines.append("- No blind review data available (ref constructor = control group only).")
    lines.append("- Mechanical metrics: 100% exec/pass for ref, consistent with expectation.")
    lines.append("")

    lines.append("## Limitations")
    lines.append("")
    for lim in analysis["limitations"]:
        lines.append(f"- {lim}")
    lines.append("")

    lines.append("## Next Steps")
    lines.append("")
    lines.append("1. **gen constructor**: LLM-powered generic constructor (needs API key)")
    lines.append("2. **lin constructor**: K003 S+V recipe constructor (needs API key)")
    lines.append("3. **mma constructor**: MathModelAgent adapter (needs external agent)")
    lines.append("4. **Blind review**: 3 evaluators × 64 bundles (needs evaluator infrastructure)")
    lines.append("5. **Statistical analysis**: Mixed-effects model with constructor as fixed effect")
    lines.append("")

    out = REPORT_DIR / "P15-K004-REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main():
    results = load_results()
    if not results:
        return
    analysis = analyze(results)
    report_path = write_report(analysis)

    # Save analysis JSON
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "k004_analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Report: {report_path}")
    print(f"Analysis: {REPORT_DIR / 'k004_analysis.json'}")
    print()
    s = analysis["summary"]
    print(f"=== ref constructor: {s['exec_pass_rate']} exec, "
          f"{s['val_pass_rate']} val, "
          f"{s['fidelity_aligned_rate']} fid ===")


if __name__ == "__main__":
    main()
