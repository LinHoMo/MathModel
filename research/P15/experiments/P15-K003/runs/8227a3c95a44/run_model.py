"""2019_C 机场出租车决策 — M/M/1排队模型+收益比较（自包含，纯标准库）。"""
import json
import math

def solve(inputs: dict) -> dict:
    # 系统参数
    lambda_pass = 30.0    # 乘客到达率（人/分钟）
    mu_taxi = 40.0        # 出租车服务率（辆/分钟，含上车时间）
    avg_fare_queue = 80.0  # 排队载客平均车费（元）
    avg_fare_city = 50.0   # 放空回市区拉客平均车费（元）
    waiting_cost = 1.5     # 等待时间成本（元/分钟，含燃油+机会成本）
    empty_cost = 25.0      # 放空回市区成本（元，含燃油+时间）
    fuel_idle = 0.5        # 怠速燃油成本（元/分钟）
    n_taxis_pool = 50      # 蓄车池已有出租车数

    # M/M/1 排队分析
    rho = lambda_pass / mu_taxi
    if rho >= 1.0:
        W_q = float("inf")
        L_q = float("inf")
        queue_stable = False
    else:
        W_q = 1.0 / (mu_taxi - lambda_pass)  # 平均等待时间（分钟）
        L_q = lambda_pass / (mu_taxi - lambda_pass)  # 平均排队长度
        queue_stable = True

    # 排队策略期望收益
    profit_queue = avg_fare_queue - (waiting_cost + fuel_idle) * W_q

    # 放空回市区策略期望收益
    time_city = 20.0  # 回市区+拉客平均时间（分钟）
    profit_city = avg_fare_city - empty_cost - waiting_cost * time_city

    # 决策
    if profit_queue > profit_city:
        decision = "queue"
        decision_cn = "前往到达区排队等待载客"
    else:
        decision = "return"
        decision_cn = "直接放空返回市区拉客"

    # 临界到达率（排队收益=放空收益时的lambda）
    # profit_queue = fare_q - (wc+fi)/(mu-lambda) = profit_city
    # => 1/(mu-lambda) = (fare_q - profit_city)/(wc+fi)
    diff = avg_fare_queue - profit_city
    if diff > 0 and (waiting_cost + fuel_idle) > 0:
        lambda_crit = mu_taxi - (waiting_cost + fuel_idle) / diff
    else:
        lambda_crit = 0.0

    # 不同到达率下的决策扫描
    scan = []
    for lam in [10, 15, 20, 25, 28, 30, 32, 35, 38]:
        if lam < mu_taxi:
            w = 1.0 / (mu_taxi - lam)
            pq = avg_fare_queue - (waiting_cost + fuel_idle) * w
        else:
            w = float("inf")
            pq = float("-inf")
        scan.append({
            "lambda": lam,
            "wait_min": round(w, 2) if w != float("inf") else None,
            "profit_queue": round(pq, 2) if pq != float("-inf") else None,
            "profit_city": round(profit_city, 2),
            "optimal": "queue" if pq > profit_city else "return"
        })

    return {
        "optimal_decision": decision,
        "optimal_decision_cn": decision_cn,
        "profit_queue": round(profit_queue, 2),
        "profit_city": round(profit_city, 2),
        "profit_diff": round(profit_queue - profit_city, 2),
        "expected_wait_min": round(W_q, 2) if queue_stable else None,
        "queue_length_avg": round(L_q, 2) if queue_stable else None,
        "rho_utilization": round(rho, 4),
        "queue_stable": queue_stable,
        "lambda_critical": round(lambda_crit, 2),
        "n_taxis_in_pool": n_taxis_pool,
        "decision_scan": scan,
    }

if __name__ == "__main__":
    print(json.dumps(solve({}), ensure_ascii=False))
