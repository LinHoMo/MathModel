# 集成学习（Ensemble Learning）领域知识

## 一、核心概念

### 1.1 定义
- 训练并结合多个基学习器，获得优于单一模型的泛化性能。
- 两大流派：**Bagging**（并行独立训练，降方差，代表 Random Forest）与 **Boosting**（串行纠错，降偏差，代表 AdaBoost / GBDT / XGBoost / LightGBM）。
- **Stacking**：用元学习器组合异质基模型的输出，竞赛提分常用但须防泄漏。

### 1.2 适用场景
- 表格数据回归/分类（XGBoost/LightGBM 通常是强基线）
- 模型组合降方差：多种预测方法的加权融合（时序预测类论文常见）
- 特征重要性解释（配合 SHAP/置换重要性）

---

## 二、基本方法

### 2.1 简单加权融合（零依赖实现）

```python
def weighted_blend(preds: dict[str, np.ndarray], weights: dict[str, float],
                   y_true: np.ndarray | None = None) -> np.ndarray:
    """多模型预测融合；权重可由验证集误差倒数确定。"""
    if y_true is not None:
        errs = {k: np.mean((p - y_true) ** 2) for k, p in preds.items()}
        inv = {k: 1.0 / (e + 1e-9) for k, e in errs.items()}
        tot = sum(inv.values())
        weights = {k: v / tot for k, v in inv.items()}
    total_w = sum(weights.values())
    return sum(w / total_w * preds[k] for k, w in weights.items())
```

### 2.2 sklearn 路线（有依赖时）

```python
# Bagging
from sklearn.ensemble import RandomForestRegressor
rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
# Boosting
from sklearn.ensemble import GradientBoostingRegressor
gb = GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, random_state=42)
```

### 2.3 Stacking 的正确姿势
- 元模型输入必须用 **out-of-fold 预测**（K 折交叉生成），否则元层泄漏。
- 基模型要**异质且有差异**（差异小的模型集成收益趋零）。
- 论文中 Stacking 必须画结构图并给每折的划分方式。

---

## 三、竞赛应用要点

### 3.1 选型写法
集成是"在选定基模型族之上的组合策略"——决策树定位到监督学习族后，集成作为候选之一与单模型对比，不是免检通道。

### 3.2 特征重要性与解释
```python
# 置换重要性（不依赖 shap 包也可做）
def permutation_importance(model, X, y, n_repeats=10, seed=42):
    rng = np.random.default_rng(seed)
    base = np.mean((model.predict(X) - y) ** 2)
    imp = {}
    for j, col in enumerate(X.columns if hasattr(X, "columns") else range(X.shape[1])):
        scores = []
        for _ in range(n_repeats):
            Xp = X.copy() if hasattr(X, "copy") else X.values.copy()
            col_idx = j if not hasattr(X, "columns") else X.columns.get_loc(col)
            Xp[:, col_idx] = rng.permutation(Xp[:, col_idx]) if not hasattr(X, "columns") else rng.permutation(X[col].values)
            scores.append(np.mean((model.predict(Xp) - y) ** 2) - base)
        imp[str(col)] = float(np.mean(scores))
    return imp
```

### 3.3 图表规范
- 基模型 vs 集成模型的多指标对比条形图（RMSE/MAE/R²）
- 特征重要性条形图（前 10 个特征，数值进表格）
- 预测-真实散点 + 45° 参考线

### 3.4 LaTeX 代码

```latex
\begin{equation}
F_M(x) = \sum_{m=1}^{M} \nu\, h_m(x),\qquad
h_m = \arg\min_h \sum_i L\bigl(y_i, F_{m-1}(x_i) + h(x_i)\bigr)
\label{eq:gbdt}
\end{equation}
```

---

## 四、常见错误

1. **Stacking 泄漏**: 用全量训练预测喂元模型，测试虚高。
2. **同质集成**: 三棵参数略不同的决策树"集成"，无实质差异（违反候选实质差异要求）。
3. **不报单模型对比**: 集成必须展示它相对最佳单模型的增益，否则选型无据。
4. **特征重要性当因果**: 重要性是相关贡献，不得写成"导致"。
5. **权重拍脑袋**: 融合权重应有验证集依据（误差倒数/最优化），并做权重灵敏度分析。

---

## 五、参考文献

1. Breiman L. Random forests. Machine Learning, 2001, 45(1): 5-32.
2. Friedman J H. Greedy function approximation: A gradient boosting machine. Annals of Statistics, 2001, 29(5): 1189-1232.
3. Chen T, Guestrin C. XGBoost: A scalable tree boosting system. KDD, 2016.
4. 周志华. 机器学习. 清华大学出版社, 2016.（第 8 章 集成学习）
