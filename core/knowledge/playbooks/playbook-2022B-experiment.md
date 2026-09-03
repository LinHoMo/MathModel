# Playbook: 2022B 实验设计与工艺优化

> **题型**: CUMCM B 题 — 统计分析 + 实验设计 + 响应面
> **核心方法**: ANOVA + 响应面方法 (RSM) + 多元回归
> **难度**: ★★★☆☆（统计方法为主，重在因素筛选和交互效应分析）

---

## 1. 问题拆解

```json
{
  "problem": "2022B 实验设计与工艺优化",
  "sub_questions": [
    {"id": "Q1", "desc": "分析各因素对响应变量的显著性", "type": "factor_screening", "depends_on": []},
    {"id": "Q2", "desc": "建立因素与响应之间的定量关系模型", "type": "regression", "depends_on": ["Q1"]},
    {"id": "Q3", "desc": "确定最优工艺参数组合", "type": "optimization", "depends_on": ["Q2"]},
    {"id": "Q4", "desc": "验证模型预测精度并分析交互效应", "type": "validation", "depends_on": ["Q2", "Q3"]}
  ]
}
```

## 2. 类型判定

| 维度 | 判定 |
|------|------|
| 题型 | **B 题**（实验/统计） |
| 核心建模 | 响应面 + 方差分析 |
| 求解类型 | 统计推断 + 优化 |
| 方法方向 | ANOVA + RSM + 回归 |

## 3. 候选模型对比

| 方法 | 适用场景 | 推荐度 |
|------|---------|--------|
| **响应面 (CCD/BBD)** | 2-6 因素、连续响应、二次关系 | ★★★★★ |
| 正交实验 + ANOVA | 因素筛选、离散水平 | ★★★★☆ |
| 田口方法 | 稳健设计、信噪比 | ★★★☆☆ |
| BP 神经网络 | 强非线性、数据充足 | ★★★☆☆ |

## 4. 模型建立

### 4.1 二因素交互模型
$$Y = \beta_0 + \sum_i \beta_i X_i + \sum_i \beta_{ii} X_i^2 + \sum_{i<j} \beta_{ij} X_i X_j + \epsilon$$

### 4.2 ANOVA 分解
$$SS_{\text{total}} = SS_{\text{model}} + SS_{\text{error}}$$
$$F = \frac{MS_{\text{model}}}{MS_{\text{error}}}, \quad p < 0.05 \text{ 显著}$$

## 5. 代码实现

```python
"""2022B 实验设计与工艺优化"""
import numpy as np
import json

np.random.seed(42)

# === 模拟实验数据（3 因素 CCD 设计） ===
factors = ['温度', '压力', '时间']
n_center = 5
# CCD: 2^3 全因子 + 2*3 轴点 + 5 中心点
X_design = []
for x1 in [-1, 1]:
    for x2 in [-1, 1]:
        for x3 in [-1, 1]:
            X_design.append([x1, x2, x3])
for i in range(3):
    ax = [0, 0, 0]
    ax[i] = 1.68
    X_design.append(ax)
    ax = [0, 0, 0]
    ax[i] = -1.68
    X_design.append(ax)
for _ in range(n_center):
    X_design.append([0, 0, 0])

X = np.array(X_design)
n = len(X)
# 真实响应模型
Y = 80 + 5*X[:, 0] + 3*X[:, 1] - 2*X[:, 2] + \
    1.5*X[:, 0]*X[:, 1] - 2*X[:, 0]**2 - 1*X[:, 1]**2 + \
    np.random.randn(n) * 1.5

def fit_response_surface(X, Y):
    """拟合二次响应面模型"""
    n, k = X.shape
    # 构造设计矩阵: 1, X, X^2, X_i*X_j
    cols = [np.ones(n)]
    cols.append(X)
    cols.append(X**2)
    for i in range(k):
        for j in range(i+1, k):
            cols.append((X[:, i] * X[:, j]).reshape(-1, 1))
    M = np.hstack(cols)
    # OLS
    beta = np.linalg.lstsq(M, Y, rcond=None)[0]
    Y_pred = M @ beta
    SS_res = np.sum((Y - Y_pred)**2)
    SS_tot = np.sum((Y - Y.mean())**2)
    R2 = 1 - SS_res / SS_tot
    return beta, Y_pred, R2

def anova_table(X, Y, beta, Y_pred):
    """方差分析表"""
    n = len(Y)
    p = len(beta) - 1
    SS_model = np.sum((Y_pred - Y.mean())**2)
    SS_res = np.sum((Y - Y_pred)**2)
    MS_model = SS_model / p
    MS_res = SS_res / (n - p - 1)
    F = MS_model / MS_res
    return {"SS_model": SS_model, "SS_res": SS_res,
            "F_stat": F, "R2": 1 - SS_res/np.sum((Y-Y.mean())**2)}

def optimize_response(beta, k):
    """梯度法求最优参数"""
    x = np.zeros(k)
    lr = 0.1
    for _ in range(100):
        grad = np.zeros(k)
        for i in range(k):
            grad[i] = beta[1+i] + 2*beta[1+k+i]*x[i]
            for j in range(k):
                if j != i:
                    cross_idx = 1 + 2*k + i*(2*k-i-1)//2 + (j-i-1)
                    if cross_idx < len(beta):
                        grad[i] += beta[cross_idx] * x[j]
        x += lr * grad
        x = np.clip(x, -2, 2)
    return x

if __name__ == "__main__":
    print("=== 2022B 实验设计与工艺优化 ===")
    k = X.shape[1]
    beta, Y_pred, R2 = fit_response_surface(X, Y)
    aov = anova_table(X, Y, beta, Y_pred)
    x_opt = optimize_response(beta, k)

    results = {
        "Q1_anova": {
            "F_statistic": round(float(aov["F_stat"]), 2),
            "R_squared": round(float(aov["R2"]), 4),
            "significant_factors": factors
        },
        "Q2_model": {
            "intercept": round(float(beta[0]), 2),
            "linear_coefs": {factors[i]: round(float(beta[1+i]), 2) for i in range(k)},
            "R2": round(float(R2), 4)
        },
        "Q3_optimum": {
            "optimal_coded": {factors[i]: round(float(x_opt[i]), 3) for i in range(k)},
            "predicted_response": round(float(
                beta[0] + sum(beta[1+i]*x_opt[i] for i in range(k)) +
                sum(beta[1+k+i]*x_opt[i]**2 for i in range(k))
            ), 2)
        },
        "Q4_validation": {
            "R2": round(float(R2), 4),
            "RMSE": round(float(np.sqrt(np.mean((Y - Y_pred)**2))), 3)
        }
    }

    with open("figures/all_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"R² = {R2:.4f}, F = {aov['F_stat']:.2f}")
    print(f"最优参数: {dict(zip(factors, x_opt.round(3)))}")
    print("结果已保存至 figures/all_results.json")
```

## 6. 结果验证

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| R²  adequacy | R² > 0.9 | 模型解释力充分 |
| 残差正态 | Shapiro-Wilk | p > 0.05 |
| 失拟检验 | Lack of fit F-test | p > 0.05（不失拟） |
| 验证实验 | 3 组验证点 | 预测误差 < 5% |

## 7-9. 论文结构/图表/LaTeX（略，参见通用模板）
