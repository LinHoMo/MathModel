# Playbook: MCM C 大数据/预测建模

> **题型**: MCM C 题 — 大数据 + 预测 + 集成学习
> **核心方法**: 集成学习 + 特征工程 + 时序预测
> **难度**: ★★★☆☆（数据驱动，重在特征工程和模型融合）

---

## 1. 问题拆解

```json
{
  "problem": "MCM C 大数据建模（典型：预测/分类/推荐）",
  "sub_questions": [
    {"id": "Q1", "desc": "数据探索与特征工程", "type": "eda", "depends_on": []},
    {"id": "Q2", "desc": "建立预测/分类模型", "type": "prediction", "depends_on": ["Q1"]},
    {"id": "Q3", "desc": "模型融合与不确定性量化", "type": "ensemble", "depends_on": ["Q2"]},
    {"id": "Q4", "desc": "策略建议与可视化呈现", "type": "recommendation", "depends_on": ["Q3"]}
  ]
}
```

## 2. 类型判定

| 维度 | 判定 |
|------|------|
| 题型 | **MCM C**（大数据/预测） |
| 核心建模 | ML 预测 + 集成 |
| 求解类型 | 监督学习 |
| 方法方向 | XGBoost + LSTM + Stacking |

## 3. 候选模型对比

| 方法 | 适用场景 | 推荐度 |
|------|---------|--------|
| **XGBoost + Stacking** | 结构化数据预测 | ★★★★★ |
| LSTM/GRU | 时序预测 | ★★★★☆ |
| Random Forest | 基线/特征重要性 | ★★★★☆ |
| Prophet | 季节性+节假日 | ★★★☆☆ |
| 深度学习 | 非结构化/图像 | ★★★☆☆ |

## 4. 模型建立

### 4.1 特征工程流水线
```
原始数据 → 清洗 → 特征构造 → 特征选择 → 模型训练
   │          │         │            │
   │       缺失值     时间特征     递归消除
   │       异常值     统计特征     SHAP排序
   │       编码       交叉特征
   │       归一化     滞后特征
```

### 4.2 Stacking 集成
$$\hat{y} = w_1 \hat{y}_{\text{XGB}} + w_2 \hat{y}_{\text{RF}} + w_3 \hat{y}_{\text{LSTM}}$$
权重由验证集 OOF 预测回归得到。

### 4.3 不确定性量化
$$\hat{y} \pm 1.96 \cdot \hat{\sigma}, \quad \hat{\sigma} = \text{std of base model predictions}$$

## 5. 代码实现

```python
"""MCM C 大数据预测 — 集成学习 + 不确定性"""
import numpy as np
import json

np.random.seed(42)

# === 模拟数据 ===
N = 2000
N_FEATURES = 20
X = np.random.randn(N, N_FEATURES)
# 非线性目标
y = (3 * np.sin(X[:, 0]) + 2 * X[:, 1]**2 - X[:, 2] * X[:, 3]
     + np.random.randn(N) * 0.5)

# === 特征工程 ===
def feature_engineering(X):
    """构造高阶特征"""
    feats = [X]
    # 平方项
    feats.append(X[:, :5]**2)
    # 交叉项
    for i in range(min(4, X.shape[1])):
        for j in range(i+1, min(5, X.shape[1])):
            feats.append((X[:, i] * X[:, j]).reshape(-1, 1))
    # 统计量
    feats.append(X.mean(axis=1, keepdims=True))
    feats.append(X.std(axis=1, keepdims=True))
    return np.hstack(feats)

# === 基模型（简化版） ===
class RidgeModel:
    def __init__(self, alpha=1.0):
        self.alpha = alpha
    def fit(self, X, y):
        I = np.eye(X.shape[1])
        self.w = np.linalg.solve(X.T @ X + self.alpha * I, X.T @ y)
    def predict(self, X):
        return X @ self.w

class SimpleTreeEnsemble:
    """简化版树集成"""
    def __init__(self, n_estimators=50):
        self.n = n_estimators
        self.models = []
    def fit(self, X, y):
        for _ in range(self.n):
            features = np.random.choice(X.shape[1], min(8, X.shape[1]), replace=False)
            model = RidgeModel(alpha=0.1)
            model.fit(X[:, features], y)
            self.models.append((features, model))
    def predict(self, X):
        preds = np.zeros((len(X), self.n))
        for k, (features, model) in enumerate(self.models):
            preds[:, k] = model.predict(X[:, features])
        return preds.mean(axis=1), preds.std(axis=1)

# === 主程序 ===
if __name__ == "__main__":
    print("=== MCM C 大数据预测 ===")

    X_eng = feature_engineering(X)

    # 划分
    n_train = int(0.8 * N)
    idx = np.random.permutation(N)
    X_tr, X_te = X_eng[idx[:n_train]], X_eng[idx[n_train:]]
    y_tr, y_te = y[idx[:n_train]], y[idx[n_train:]]

    # 模型 1: Ridge
    ridge = RidgeModel(alpha=1.0)
    ridge.fit(X_tr, y_tr)
    y_ridge = ridge.predict(X_te)

    # 模型 2: Tree Ensemble
    ensemble = SimpleTreeEnsemble(n_estimators=50)
    ensemble.fit(X_tr, y_tr)
    y_ens_mean, y_ens_std = ensemble.predict(X_te)

    # Stacking: 简单加权平均
    w1, w2 = 0.4, 0.6
    y_stack = w1 * y_ridge + w2 * y_ens_mean

    # 评估
    rmse_ridge = np.sqrt(np.mean((y_ridge - y_te)**2))
    rmse_ens = np.sqrt(np.mean((y_ens_mean - y_te)**2))
    rmse_stack = np.sqrt(np.mean((y_stack - y_te)**2))

    # 不确定性
    coverage_95 = np.mean(np.abs(y_te - y_stack) < 1.96 * y_ens_std)

    results = {
        "Q1_features": {
            "original": N_FEATURES,
            "engineered": X_eng.shape[1],
            "augmentation_ratio": round(X_eng.shape[1] / N_FEATURES, 1)
        },
        "Q2_prediction": {
            "ridge_rmse": round(float(rmse_ridge), 4),
            "ensemble_rmse": round(float(rmse_ens), 4),
            "best_single": "ensemble" if rmse_ens < rmse_ridge else "ridge"
        },
        "Q3_ensemble": {
            "stacking_rmse": round(float(rmse_stack), 4),
            "improvement_over_best": round(float(
                min(rmse_ridge, rmse_ens) - rmse_stack), 4),
            "95pct_coverage": round(float(coverage_95), 3)
        },
        "Q4_recommendation": "Stacking 集成最优，建议结合 SHAP 解释关键特征"
    }

    with open("figures/all_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"特征: {N_FEATURES} → {X_eng.shape[1]}")
    print(f"Ridge RMSE = {rmse_ridge:.4f}")
    print(f"Ensemble RMSE = {rmse_ens:.4f}")
    print(f"Stacking RMSE = {rmse_stack:.4f}")
    print(f"95% 覆盖率 = {coverage_95:.3f}")
    print("结果已保存至 figures/all_results.json")
```

## 6. 结果验证

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| 数据泄露 | 时间切分/索引检查 | 无泄露 |
| 交叉验证 | 5 折 CV 一致性 | 标准差 < 5% |
| 基线对比 | 优于均值/中位数基线 | 提升 > 20% |
| 校准曲线 | 预测分位数 vs 实际 | 覆盖率接近标称值 |

## 7-9. 论文结构/图表/LaTeX

关键图表：特征重要性条形图、预测散点图、残差分布图、集成权重饼图、不确定性带预测图。
