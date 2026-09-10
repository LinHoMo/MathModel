# -*- coding: utf-8 -*-
"""P15-K005 runner 框架：Constructor × Runtime 2×2 析因 benchmark（P3-1）。

设计（预注册 `research/P15/protocol/preregistration/P15-K005-DRAFT.md`）：
- 因子：Constructor（C1 裸 Doubao / C2 MathModelAgent）× Runtime（R0/R1）
- 单元：6 题 × 5 rep = 30 块；每块 4 臂 → 120 runs
- 主终点：L6 终态（validate_against_gt + problem_cards gt l6_assertions）
- 配对差分（块内 R1−R0）+ bootstrap 95% CI + 析因分解

数据收集状态（如实）：本 runner 消费外部 Constructor 产物目录
（P2-2 adapter 契约：model_ir.json/code.py/output_mapping.json/specs.json）。
正式 120 runs 数据需外部 Constructor 会话逐题生成（裸 Doubao/MMA），
**禁止伪造/回填**；数据就绪后本脚本执行分析并出 K005_REPORT.md。

用法：
    py -3.12 research/P15/benchmark/constructor_independent/runner.py \
        --constructor-dir <产物根目录>          # 执行+分析（数据就绪后）
    py -3.12 .../runner.py --dry-run            # 检查目录结构/契约（现在）
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]  # constructor_independent/benchmark/P15/research/<repo>
if str(_REPO / "core") not in sys.path:
    sys.path.insert(0, str(_REPO / "core"))

from runtime.execution.validation import validate_against_gt  # noqa: E402

OUT = _REPO / "research" / "P15" / "benchmark" / "constructor_independent"
PROBLEMS = ["2018_A", "2018_B", "2019_C", "2020_B", "2022_C", "2024_A"]
REPS = list(range(1, 6))
ARMS = ["C1R0", "C1R1", "C2R0", "C2R1"]


def _gt_assertions(pid: str) -> dict | None:
    p = (_REPO / "research" / "P15" / "benchmark" / "problem_cards"
         / pid / "gt.json")
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get("l6_assertions")


def check_input_layout(root: Path) -> dict:
    """检查 Constructor 产物目录是否齐备（dry-run 用，如实报告缺失）。"""
    missing, ok = [], 0
    for pid in PROBLEMS:
        for rep in REPS:
            for arm in ARMS:
                d = root / pid / f"rep{rep}" / arm
                if not (d / "model_ir.json").exists() or not (
                        d / "code.py").exists():
                    missing.append(str(d))
                else:
                    ok += 1
    return {"expected_runs": len(PROBLEMS) * len(REPS) * len(ARMS),
            "present": ok, "missing": missing[:10],
            "missing_count": len(missing)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--constructor-dir", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--bootstrap", type=int, default=10000)
    args = ap.parse_args()

    if args.dry_run or not args.constructor_dir:
        root = Path(args.constructor_dir) if args.constructor_dir else OUT / "inputs"
        st = check_input_layout(root)
        print(f"[P15-K005] 布局检查：expected={st['expected_runs']} "
              f"present={st['present']} missing={st['missing_count']}")
        if st["missing_count"]:
            print("  缺失示例（前 5）:", *st["missing"][:5], sep="\n    ")
            print("  → 数据收集 BLOCKED：需外部 Constructor 会话逐题生成真实产物，"
                  "禁止伪造/回填（The Agent Is Not The State）。")
            return 1
        print("  数据齐备，可执行正式分析。")
        return 0

    # ---- 正式分析（数据就绪后） ----
    root = Path(args.constructor_dir)
    results = []
    for pid in PROBLEMS:
        gt = _gt_assertions(pid)
        for rep in REPS:
            block = {}
            for arm in ARMS:
                d = root / pid / f"rep{rep}" / arm
                er = _evaluate(d, gt)
                block[arm] = er
            results.append({"problem": pid, "rep": rep, "block": block})
    # R1 臂需要执行（本框架位置：真实执行由 Runtime 主 DAG 完成——这里
    # 调用方在数据生成时已执行；此处仅消费 execution 产物）
    deltas = []
    for r in results:
        r1 = r["block"]["C1R1"]["l6_passed"] - r["block"]["C1R0"]["l6_passed"]
        deltas.append(r1)
    n = len(deltas)
    mean = sum(deltas) / n
    random.seed(2026)
    boot = sorted(sum(random.choice(deltas) for _ in range(n)) / n
                  for _ in range(args.bootstrap))
    ci = (boot[int(0.025 * args.bootstrap)], boot[int(0.975 * args.bootstrap)])
    report = {
        "experiment": "P15-K005", "n_blocks": n,
        "delta_l6_mean": mean, "delta_l6_ci95": ci,
        "h1_supported": ci[0] > 0,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "正式 120 runs 数据由外部 Constructor 会话生成（真实执行）；"
                "本报告为执行后分析，无伪造 runs",
    }
    (OUT / "k005_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Δ_L6 mean={mean:.4f} CI=[{ci[0]:.4f},{ci[1]:.4f}] "
          f"H1={'SUPPORTED' if ci[0] > 0 else 'NOT SUPPORTED'}")
    return 0


def _evaluate(run_dir: Path, gt: dict | None) -> dict:
    """读取单个 run 的执行产物（execution_result.json 或 result.json），
    计算 L6 判定。数据生成时由 Runtime 主 DAG 真实执行并落盘。"""
    for name in ("execution_result.json", "result.json"):
        f = run_dir / name
        if f.exists():
            er = json.loads(f.read_text(encoding="utf-8"))
            er.setdefault("status", "success" if (er.get("outputs")) else "failed")
            l6 = validate_against_gt(er, gt)
            return {"l6_status": l6["status"],
                    "l6_passed": int(l6["status"] == "passed"),
                    "l6_score": l6["l6_score"]}
    return {"l6_status": "no-execution-artifact", "l6_passed": 0,
            "l6_score": None}


if __name__ == "__main__":
    sys.exit(main())
