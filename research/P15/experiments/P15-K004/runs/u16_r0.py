"""M/M/c queue model — V6 — M1-wrong（K004 u16）。

错误注入说明（机械确定性）：service_rate=40 → rho=1.250
（不稳定 > 1，cvm>0，预期 L6 FAIL）。
固定 ABI：def solve(inputs) -> dict；仅标准库。
"""
import json
import math
import random


def solve(inputs: dict | None = None) -> dict:
    random.seed(42)
    lam = float(250)
    c = int(5)
    mu = float(40)
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
    violations = {
        "stability": stability_violation,
        "utilization_leq_1": max(0.0, rho - 1.0),
    }
    cvm = max(violations.values())
    out = {
        "avg_waiting_time": Wq,
        "avg_queue_length": Lq,
        "server_utilization": rho,
        "probability_wait": Pw,
        "constraint_violation_max": cvm,
        "solver_status": "optimal" if cvm == 0 else "infeasible",
        "stability_violation": stability_violation,
        "violations": violations,
        "rho": rho,
    }
    print(json.dumps(out))
    return out


if __name__ == "__main__":
    solve()
