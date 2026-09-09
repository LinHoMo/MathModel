"""M/M/c queue model — 2019_C Q1, version v1 (deliberately flawed).

缺陷设计：service_rate (mu) 故意设得过小，使 rho = lambda/(c*mu) = 1.5 >= 1，
系统不稳定。代码仍正常运行不崩溃，但 M/M/c 解析公式在 rho >= 1 时失效，
输出负值/超范围指标，并由代码自检报告 constraint_violation_max > 0。

固定 ABI：def solve(inputs: dict | None = None) -> dict
代码自包含：参数 baked in（inputs 参数仅用于覆盖默认值，subprocess 无 stdin/文件依赖）。
输出约定：stdout 最后一行为 JSON（LocalPythonAdapter 解析约定）。
仅依赖标准库 math / json。
"""
import json
import math

DEFAULT_PARAMETERS = {
    "arrival_rate": 60,   # 人/小时，乘客到达率 lambda
    "num_servers": 2,     # 辆，出租车（服务台）数量 c
    "service_rate": 20,   # 辆/小时，单车服务率 mu（故意过小 -> rho = 1.5 >= 1）
}


def solve(inputs: dict | None = None) -> dict:
    p = dict(DEFAULT_PARAMETERS)
    if inputs and "parameters" in inputs:
        p.update(inputs["parameters"])
    elif inputs:
        p.update(inputs)

    lam = float(p["arrival_rate"])
    c = int(p["num_servers"])
    mu = float(p["service_rate"])

    rho = lam / (c * mu)
    a = lam / mu  # lambda/mu

    # M/M/c 解析公式（rho >= 1 时公式失效，但仍照常计算，不抛异常）
    s = 0.0
    for n in range(c):
        s += a ** n / math.factorial(n)
    term_c = (a ** c) / (math.factorial(c) * (1.0 - rho))
    P0 = 1.0 / (s + term_c)
    Pw = (a ** c) * P0 / (math.factorial(c) * (1.0 - rho))
    Lq = Pw * rho / (1.0 - rho)
    Wq = Lq / lam

    # 代码自检：计算各约束违反量
    stability_violation = max(0.0, rho - 1.0)
    violations = {
        "stability": stability_violation,
        "utilization_lower": max(0.0, 0.0 - rho),
        "utilization_upper": max(0.0, rho - 1.0),
        "wait_nonneg": max(0.0, 0.0 - Wq),
        "queue_nonneg": max(0.0, 0.0 - Lq),
        "prob_wait_lower": max(0.0, 0.0 - Pw),
        "prob_wait_upper": max(0.0, Pw - 1.0),
    }
    constraint_violation_max = max(violations.values()) if violations else 0.0

    solver_status = "unstable" if rho >= 1.0 else "optimal"

    return {
        "avg_waiting_time": round(Wq, 8),
        "avg_queue_length": round(Lq, 8),
        "server_utilization": round(rho, 8),
        "probability_wait": round(Pw, 8),
        "constraint_violation_max": round(constraint_violation_max, 8),
        "solver_status": solver_status,
        "stability_violation": round(stability_violation, 8),
        "violations": {k: round(v, 8) for k, v in violations.items()},
    }


if __name__ == "__main__":
    result = solve()
    print(json.dumps(result, ensure_ascii=False))
