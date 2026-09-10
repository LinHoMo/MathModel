# -*- coding: utf-8 -*-
"""P15-K004 runner：L5 Revision 闭环端到端度量实验（预注册协议 v1.0）。

18 单元（6 变体 × 3 种子）× 两臂（R0 无 revision / R1 有 revision）。
模板：P1-VS-001 M/M/c 排队（2019_C Q1）。错误注入机械确定性
（service_rate 错误值 → rho>1 → cvm>0 → L6 FAIL）；修订注入正确 M2。
执行：真实 subprocess（stdout 末行 JSON 约定，仅标准库）。

用法：
    py -3.12 research/P15/scripts/k004_runner.py            # 全 18 单元
    py -3.12 research/P15/scripts/k004_runner.py --units 3  # 仅前 3 单元（调试）
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from modeling_harness.runtime.execution.validation import validate_against_gt  # noqa: E402

OUT = _REPO / "research" / "P15" / "experiments" / "P15-K004"
GT_PATH = (_REPO / "research" / "P15" / "benchmark" / "problem_cards"
           / "2019_C" / "gt.json")

# 6 变体：不同 (arrival_rate, num_servers)。错误版 service_rate 使 rho>1，
# 正确版使 rho<1（错误/正确参数为模板内机械推导，非编造数值）。
VARIANTS = [
    {"arrival_rate": 60, "num_servers": 2, "wrong_mu": 20, "right_mu": 40},
    {"arrival_rate": 90, "num_servers": 3, "wrong_mu": 20, "right_mu": 40},
    {"arrival_rate": 120, "num_servers": 3, "wrong_mu": 30, "right_mu": 50},
    {"arrival_rate": 150, "num_servers": 4, "wrong_mu": 25, "right_mu": 50},
    {"arrival_rate": 200, "num_servers": 5, "wrong_mu": 30, "right_mu": 50},
    {"arrival_rate": 250, "num_servers": 5, "wrong_mu": 40, "right_mu": 60},
]

SEEDS = [42, 43, 44]

MODEL_TEMPLATE = '''"""M/M/c queue model — {variant} — {label}（K004 {unit}）。

错误注入说明（机械确定性）：service_rate={mu} → rho={rho:.3f}
（{rho_note}）。
固定 ABI：def solve(inputs) -> dict；仅标准库。
"""
import json
import math
import random


def solve(inputs: dict | None = None) -> dict:
    random.seed({seed})
    lam = float({lam})
    c = int({c})
    mu = float({mu})
    rho = lam / (c * mu)
    a = lam / mu
    s = 0.0
    for n in range(c):
        s += a ** n / math.factorial(n)
    term_c = (a ** c) / (math.factorial(c) * (1.0 - rho))
    P0 = 1.0 / (s + term_c)
    Pw = (a ** c) * P0 / (math.factorial(c) * (1.0 - rho))
    Lq = Pw * rho / (1.0 - rho)
    Wq = Lq / lam
    stability_violation = max(0.0, rho - 1.0)
    violations = {{
        "stability": stability_violation,
        "utilization_leq_1": max(0.0, rho - 1.0),
    }}
    cvm = max(violations.values())
    out = {{
        "avg_waiting_time": Wq,
        "avg_queue_length": Lq,
        "server_utilization": rho,
        "probability_wait": Pw,
        "constraint_violation_max": cvm,
        "solver_status": "optimal" if cvm == 0 else "infeasible",
        "stability_violation": stability_violation,
        "violations": violations,
        "rho": rho,
    }}
    print(json.dumps(out))
    return out


if __name__ == "__main__":
    solve()
'''


def _exec_code(code: str, workdir: Path, tag: str) -> dict:
    """真实 subprocess 执行；stdout 末行 JSON 为 outputs。"""
    script = workdir / f"{tag}.py"
    script.write_text(code, encoding="utf-8", newline="\n")
    r = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=60, cwd=str(workdir))
    outputs = {}
    for line in reversed(r.stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                outputs = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    return {
        "tag": tag, "returncode": r.returncode, "stdout_tail": r.stdout[-200:],
        "stderr_tail": r.stderr[-200:], "outputs": outputs,
        "executed": r.returncode == 0 and bool(outputs),
    }


def l6_status(result: dict, gt_assertions: dict) -> dict:
    er = {"status": "success" if result.get("executed") else "failed",
          "outputs": result.get("outputs") or {},
          "constraint_violation_max": (result.get("outputs") or {})
          .get("constraint_violation_max"),
          "objective_value": (result.get("outputs") or {}).get("rho"),
          "objective_sane": True}
    return validate_against_gt(er, gt_assertions)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", type=int, default=18)
    args = ap.parse_args()

    gt_assertions = json.loads(GT_PATH.read_text(encoding="utf-8")) \
        .get("l6_assertions")
    workdir = OUT / "runs"
    workdir.mkdir(parents=True, exist_ok=True)

    units: list[dict] = []
    n_units = min(args.units, 18)
    for idx in range(n_units):
        variant = VARIANTS[idx // 3]
        seed = SEEDS[idx % 3]
        unit_id = f"u{idx+1:02d}"
        # R0：错误版孤跑
        rho_wrong = variant["arrival_rate"] / (variant["num_servers"]
                                            * variant["wrong_mu"])
        rho_right = variant["arrival_rate"] / (variant["num_servers"]
                                               * variant["right_mu"])
        wrong_code = MODEL_TEMPLATE.format(
            variant=f"V{(idx//3)+1}", label="M1-wrong", unit=unit_id,
            mu=variant["wrong_mu"], rho=rho_wrong,
            rho_note=("不稳定 > 1，cvm>0，预期 L6 FAIL" if rho_wrong > 1
                      else "稳定 < 1，cvm=0，预期 L6 PASS"),
            seed=seed, lam=variant["arrival_rate"], c=variant["num_servers"])
        r0 = _exec_code(wrong_code, workdir, f"{unit_id}_r0")
        l6_0 = l6_status(r0, gt_assertions)
        # R1：错误版 + revision 闭环（注入正确 M2 并重跑）
        right_code = MODEL_TEMPLATE.format(
            variant=f"V{(idx//3)+1}", label="M2-right", unit=unit_id,
            mu=variant["right_mu"], rho=rho_right,
            rho_note=("不稳定 > 1，cvm>0，预期 L6 FAIL" if rho_right > 1
                      else "稳定 < 1，cvm=0，预期 L6 PASS"),
            seed=seed, lam=variant["arrival_rate"], c=variant["num_servers"])
        r1_m1 = _exec_code(wrong_code, workdir, f"{unit_id}_r1_m1")
        l6_1_m1 = l6_status(r1_m1, gt_assertions)
        r1_m2 = _exec_code(right_code, workdir, f"{unit_id}_r1_m2")
        l6_1_m2 = l6_status(r1_m2, gt_assertions)
        revision_needed = l6_1_m1["status"] != "passed"
        revision_rounds = 1 if (revision_needed
                                and l6_1_m2["status"] == "passed") else (
            1 if l6_1_m2["status"] == "passed" else 0)
        unit = {
            "unit_id": unit_id, "variant": (idx // 3) + 1, "seed": seed,
            "r0": {"executed": r0["executed"], "l6_status": l6_0["status"],
                   "l6_score": l6_0["l6_score"], "cvm": (r0.get("outputs")
                   or {}).get("constraint_violation_max")},
            "r1": {"m1_l6": l6_1_m1["status"], "m2_l6": l6_1_m2["status"],
                   "m2_l6_score": l6_1_m2["l6_score"],
                   "m2_executed": r1_m2["executed"]},
            "delta_l6_passed": int(l6_1_m2["status"] == "passed")
            - int(l6_0["status"] == "passed"),
            "revision_rounds": revision_rounds,
            "m1_failed_as_expected": l6_0["status"] == "failed",
            "replay_ok": r1_m2["executed"],
        }
        units.append(unit)
        print(f"{unit_id} V{(idx//3)+1} seed={seed}: "
              f"R0={l6_0['status']} R1(M1)={l6_1_m1['status']} "
              f"R1(M2)={l6_1_m2['status']} Δ={unit['delta_l6_passed']:+d}")

    # ---- 分析 ----
    n = len(units)
    deltas = [u["delta_l6_passed"] for u in units]
    mean_delta = sum(deltas) / n
    m1_fail = sum(u["m1_failed_as_expected"] for u in units)
    m2_pass = sum(1 for u in units if u["r1"]["m2_l6"] == "passed")
    replay_ok = sum(u["replay_ok"] for u in units)
    rounds = [u["revision_rounds"] for u in units]

    # bootstrap 95% CI（配对差分，10000 次）
    random.seed(2026)
    boot = []
    for _ in range(10000):
        sample = [random.choice(deltas) for _ in range(n)]
        boot.append(sum(sample) / n)
    boot.sort()
    ci = (boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot))])

    report = {
        "experiment": "P15-K004",
        "protocol": "research/P15/protocol/preregistration/P15-K004-DRAFT.md",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "units": units,
        "summary": {
            "n_units": n,
            "delta_l6_mean": mean_delta,
            "delta_l6_ci95": ci,
            "m1_failed_as_expected": f"{m1_fail}/{n}",
            "m2_passed": f"{m2_pass}/{n}",
            "replay_ok": f"{replay_ok}/{n}",
            "revision_rounds_mean": round(sum(rounds) / n, 3),
            "h1_supported": ci[0] > 0,
        },
    }
    (OUT / "k004_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n===== K004 summary =====")
    print(f"Δ_L6 mean={mean_delta:.4f}  95% CI=[{ci[0]:.4f}, {ci[1]:.4f}]  "
          f"H1={'SUPPORTED' if ci[0] > 0 else 'NOT SUPPORTED'}")
    print(f"M1 失败真实性 {m1_fail}/{n} ｜ M2 通过 {m2_pass}/{n} ｜ "
          f"Replay {replay_ok}/{n} ｜ 修正轮数均值 {report['summary']['revision_rounds_mean']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
