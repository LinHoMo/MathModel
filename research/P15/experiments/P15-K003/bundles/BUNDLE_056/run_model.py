"""2017_B 拍照赚钱任务定价 — Logistic回归+定价优化（自包含，纯标准库）。"""
import json
import math
import random

def solve(inputs: dict) -> dict:
    random.seed(42)
    # 生成合成数据（模拟附件一：任务位置、定价、完成情况）
    n_tasks = 200
    data = []
    for i in range(n_tasks):
        # 任务到最近会员的距离（km）
        distance = random.expovariate(1.0 / 2.0)  # 均值2km
        distance = min(distance, 15.0)
        # 会员密度（附近会员数）
        member_density = max(1, int(random.gauss(10, 4)))
        # 原定价（元）
        price = round(15 + distance * 2 + random.gauss(0, 3), 1)
        price = max(5, price)
        # 完成概率（真实模型：价格越高、距离越近、会员越多→越可能完成）
        p_complete = 1.0 / (1.0 + math.exp(-(
            -2.0 + 0.08 * price - 0.15 * distance + 0.05 * member_density
        )))
        completed = 1 if random.random() < p_complete else 0
        data.append({
            "task_id": i, "distance_km": round(distance, 2),
            "member_density": member_density, "price": price,
            "completed": completed
        })

    # Logistic回归（梯度下降，纯Python）
    # 特征: [1, price, distance, member_density]
    def sigmoid(z):
        if z >= 0:
            return 1.0 / (1.0 + math.exp(-z))
        else:
            ez = math.exp(z)
            return ez / (1.0 + ez)

    def predict(x, beta):
        z = sum(b * xi for b, xi in zip(beta, x))
        return sigmoid(z)

    # 标准化特征
    prices = [d["price"] for d in data]
    distances = [d["distance_km"] for d in data]
    densities = [d["member_density"] for d in data]
    p_mean, p_std = sum(prices) / len(prices), (sum((p - sum(prices)/len(prices))**2 for p in prices) / len(prices))**0.5 or 1
    d_mean, d_std = sum(distances) / len(distances), (sum((d - sum(distances)/len(distances))**2 for d in distances) / len(distances))**0.5 or 1
    m_mean, m_std = sum(densities) / len(densities), (sum((m - sum(densities)/len(densities))**2 for m in densities) / len(densities))**0.5 or 1

    X = []
    y = []
    for d in data:
        X.append([
            1.0,
            (d["price"] - p_mean) / p_std,
            (d["distance_km"] - d_mean) / d_std,
            (d["member_density"] - m_mean) / m_std,
        ])
        y.append(d["completed"])

    # 梯度下降
    beta = [0.0, 0.0, 0.0, 0.0]
    lr = 0.1
    n_epochs = 500
    losses = []
    for epoch in range(n_epochs):
        grad = [0.0, 0.0, 0.0, 0.0]
        loss = 0.0
        for xi, yi in zip(X, y):
            pred = predict(xi, beta)
            error = pred - yi
            loss -= yi * math.log(max(pred, 1e-15)) + (1 - yi) * math.log(max(1 - pred, 1e-15))
            for j in range(4):
                grad[j] += error * xi[j]
        for j in range(4):
            beta[j] -= lr * grad[j] / len(X)
        losses.append(round(loss / len(X), 6))

    # 模型评估
    correct = 0
    for xi, yi in zip(X, y):
        pred = predict(xi, beta)
        if (pred >= 0.5 and yi == 1) or (pred < 0.5 and yi == 0):
            correct += 1
    accuracy = correct / len(X)

    # 实际完成率
    actual_completion = sum(d["completed"] for d in data) / len(data)

    # 定价优化：最大化期望利润 = price * P(完成|price, distance=均值, density=均值)
    best_price = 0
    best_profit = -1
    profit_curve = []
    for price_test in [5, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40]:
        x_test = [
            1.0,
            (price_test - p_mean) / p_std,
            0.0,  # 距离均值
            0.0,  # 密度均值
        ]
        p = predict(x_test, beta)
        profit = price_test * p
        profit_curve.append({"price": price_test, "completion_prob": round(p, 4),
                             "expected_profit": round(profit, 2)})
        if profit > best_profit:
            best_profit = profit
            best_price = price_test

    return {
        "n_tasks": n_tasks,
        "actual_completion_rate": round(actual_completion, 4),
        "model_accuracy": round(accuracy, 4),
        "logistic_coefficients": {
            "intercept": round(beta[0], 4),
            "price": round(beta[1], 4),
            "distance": round(beta[2], 4),
            "member_density": round(beta[3], 4),
        },
        "coefficient_interpretation": {
            "price": "正系数→价格越高完成概率越高（在合理范围内）",
            "distance": "负系数→距离越远完成概率越低",
            "member_density": "正系数→会员越多完成概率越高",
        },
        "optimal_price": best_price,
        "optimal_expected_profit": round(best_profit, 2),
        "profit_curve": profit_curve,
        "loss_final": losses[-1] if losses else None,
        "feature_standardization": {
            "price_mean": round(p_mean, 2), "price_std": round(p_std, 2),
            "distance_mean": round(d_mean, 2), "distance_std": round(d_std, 2),
        },
    }

if __name__ == "__main__":
    print(json.dumps(solve({}), ensure_ascii=False))
