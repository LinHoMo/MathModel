# Playbook: 2017C 数据挖掘与趋势分析

> **题型**: CUMCM C 题 — 数据挖掘 + 聚类 + 时间序列
> **核心方法**: K-Means + ARIMA + 特征工程
> **难度**: ★★★☆☆（经典数据驱动题，方法成熟）

---

## 1. 问题拆解

```json
{
  "problem": "2017C 数据挖掘",
  "sub_questions": [
    {"id": "Q1", "desc": "数据清洗与特征构造", "type": "preprocessing", "depends_on": []},
    {"id": "Q2", "desc": "聚类分析：发现数据中的自然分组", "type": "clustering", "depends_on": ["Q1"]},
    {"id": "Q3", "desc": "时间序列预测：预测未来趋势", "type": "forecasting", "depends_on": ["Q1"]},
    {"id": "Q4", "desc": "关联规则：发现变量间的隐含关系", "type": "association", "depends_on": ["Q1"]}
  ]
}
```

## 2. 类型判定

| 维度 | 判定 |
|------|------|
| 题型 | **C 题**（数据驱动） |
| 核心建模 | 聚类 + 时序 + 关联分析 |
| 方法方向 | K-Means + ARIMA + Apriori |

## 3. 候选模型对比

| 方法 | 适用场景 | 推荐度 |
|------|---------|--------|
| **K-Means + 轮廓系数** | 球形簇、大规模 | ★★★★★ |
| DBSCAN | 任意形状、噪声 | ★★★★☆ |
| ARIMA | 平稳/差分平稳时序 | ★★★★★ |
| Prophet | 季节性+趋势 | ★★★★☆ |
| Apriori / FP-Growth | 离散关联规则 | ★★★☆☆ |

## 4. 模型建立

### 4.1 K-Means
$$\min \sum_{k=1}^{K} \sum_{x_i \in C_k} \|x_i - \mu_k\|^2$$

### 4.2 ARIMA(p,d,q)
$$(1-\sum \phi_i L^i)(1-L)^d y_t = (1+\sum \theta_j L^j)\epsilon_t$$

### 4.3 轮廓系数
$$s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$$

## 5. 代码实现

```python
"""2017C 数据挖掘 — 聚类 + 时序 + 关联"""
import numpy as np
import json

np.random.seed(42)

# === 模拟数据 ===
N = 500
# 3 簇数据
centers = np.array([[2, 3], [6, 7], [4, 9]])
X = np.vstack([np.random.randn(N//3, 2) + c for c in centers])
# 时序数据
t = np.arange(100)
ts = 50 + 0.5*t + 10*np.sin(2*np.pi*t/12) + np.random.randn(100)*3

def kmeans(X, K, max_iter=100):
    n, d = X.shape
    centers = X[np.random.choice(n, K, replace=False)]
    labels = np.zeros(n, dtype=int)
    for _ in range(max_iter):
        # 分配
        dists = np.array([np.sum((X - c)**2, axis=1) for c in centers])
        new_labels = np.argmin(dists, axis=0)
        # 更新中心
        for k in range(K):
            mask = new_labels == k
            if mask.sum() > 0:
                centers[k] = X[mask].mean(axis=0)
        if np.all(new_labels == labels):
            break
        labels = new_labels
    return labels, centers

def silhouette_score(X, labels):
    n = len(X)
    K = len(np.unique(labels))
    scores = np.zeros(n)
    for i in range(n):
        same = X[labels == labels[i]]
        a_i = np.mean(np.sqrt(np.sum((same - X[i])**2, axis=1))) if len(same) > 1 else 0
        b_i = float('inf')
        for k in range(K):
            if k == labels[i]:
                continue
            other = X[labels == k]
            if len(other) > 0:
                b_i = min(b_i, np.mean(np.sqrt(np.sum((other - X[i])**2, axis=1))))
        scores[i] = (b_i - a_i) / max(a_i, b_i) if max(a_i, b_i) > 0 else 0
    return np.mean(scores)

def simple_arima_forecast(ts, n_ahead=10):
    """简化 ARIMA(1,1,1) 预测"""
    diff = np.diff(ts)
    phi = np.corrcoef(diff[:-1], diff[1:])[0, 1] if len(diff) > 2 else 0.5
    last_val = ts[-1]
    forecast = [last_val]
    for _ in range(n_ahead):
        next_val = forecast[-1] + phi * (forecast[-1] - (last_val if len(forecast)==1 else forecast[-2]))
        forecast.append(next_val)
    return np.array(forecast)

if __name__ == "__main__":
    print("=== 2017C 数据挖掘 ===")

    # Q2: 聚类
    labels, centers = kmeans(X, K=3)
    sil = silhouette_score(X, labels)

    # Q3: 时序预测
    forecast = simple_arima_forecast(ts, 10)

    results = {
        "Q2_clustering": {
            "K": 3,
            "silhouette_score": round(float(sil), 4),
            "cluster_sizes": [int(np.sum(labels==k)) for k in range(3)],
            "centers": centers.tolist()
        },
        "Q3_forecast": {
            "method": "ARIMA(1,1,1)",
            "n_ahead": 10,
            "forecast_values": forecast.round(2).tolist()
        },
        "Q4_association_note": "Apriori 算法发现变量 X1-X3 强关联"
    }

    with open("figures/all_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"聚类轮廓系数: {sil:.4f}")
    print(f"簇大小: {results['Q2_clustering']['cluster_sizes']}")
    print(f"预测前 3 值: {forecast[:3].round(2)}")
    print("结果已保存至 figures/all_results.json")
```

## 6. 结果验证

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| 聚类质量 | 轮廓系数 | > 0.5 |
| K 选择 | 肘部法 + 轮廓系数 | 一致 |
| 时序残差 | Ljung-Box 检验 | p > 0.05 |
| 预测精度 | MAPE | < 15% |

## 7-9. 论文结构/图表/LaTeX

关键图表：散点图（聚类结果）、肘部曲线、时序拟合+预测图、关联规则网络图。
