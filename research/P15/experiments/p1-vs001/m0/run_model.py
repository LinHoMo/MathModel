"""M0 LP demo — 工厂两产品生产计划。

固定 ABI：def solve(inputs: dict | None = None) -> dict
代码自包含：参数 baked in（inputs 参数仅用于覆盖默认值，subprocess 无 stdin/文件依赖）。
输出约定：stdout 最后一行为 JSON（LocalPythonAdapter 解析约定）。
"""
import json
from itertools import combinations

DEFAULT_PARAMETERS = {
    "profit_A": 3, "profit_B": 5,
    "machine_time_A": 2, "machine_time_B": 3, "machine_capacity": 100,
    "labor_time_A": 1, "labor_time_B": 2, "labor_capacity": 60,
}


def solve(inputs: dict | None = None) -> dict:
    p = dict(DEFAULT_PARAMETERS)
    if inputs and "parameters" in inputs:
        p.update(inputs["parameters"])
    elif inputs:
        p.update(inputs)

    cA = float(p["profit_A"]); cB = float(p["profit_B"])
    aA = float(p["machine_time_A"]); aB = float(p["machine_time_B"])
    bA = float(p["labor_time_A"]); bB = float(p["labor_time_B"])
    mcap = float(p["machine_capacity"]); lcap = float(p["labor_capacity"])

    # 约束行：A_i * x_A + B_i * x_B <= rhs_i
    rows = [
        (aA, aB, mcap, "machine_cap"),
        (bA, bB, lcap, "labor_cap"),
        (-1.0, 0.0, 0.0, "nonneg_A"),
        (0.0, -1.0, 0.0, "nonneg_B"),
    ]

    def feasible(x, y):
        return all(a * x + b * y <= rhs + 1e-9 for a, b, rhs, _ in rows)

    vertices = []
    for (a1, b1, r1, _), (a2, b2, r2, _) in combinations(rows, 2):
        det = a1 * b2 - a2 * b1
        if abs(det) < 1e-12:
            continue
        x = (r1 * b2 - r2 * b1) / det
        y = (a1 * r2 - a2 * r1) / det
        if feasible(x, y):
            vertices.append((round(x, 6), round(y, 6)))
    vertices = list(dict.fromkeys(vertices))

    best_x, best_y, best_obj = 0.0, 0.0, float("-inf")
    for x, y in vertices:
        obj = cA * x + cB * y
        if obj > best_obj:
            best_obj, best_x, best_y = obj, x, y

    violations = {}
    for a, b, rhs, name in rows:
        v = a * best_x + b * best_y - rhs
        violations[name] = round(max(0.0, v), 8)
    max_violation = max(violations.values()) if violations else 0.0

    return {
        "x_A": best_x,
        "x_B": best_y,
        "objective_value": round(best_obj, 6),
        "constraint_violation_max": max_violation,
        "solver_status": "optimal",
        "vertices_checked": len(vertices),
        "violations": violations,
    }


if __name__ == "__main__":
    result = solve()
    print(json.dumps(result, ensure_ascii=False))
