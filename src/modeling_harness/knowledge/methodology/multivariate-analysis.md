# 多元分析方法论

> 本文件提供数学建模竞赛中常用的多元分析方法：偏最小二乘回归（PLS）、对应分析（CA）、典型相关分析（CCA）。分别解决共线性/高维小样本回归、定性变量关联可视化、两组变量整体相关性三大问题。

---

## 一、方法选择决策树

```
多元分析需求
├── 因变量连续，需预测/回归？
│   ├── 自变量共线性严重 / 样本数 < 变量数 → PLS 回归
│   │   └── 同时降维 + 回归 → PLSRegression（交叉验证选成分数）
│   ├── 无共线性、样本充足 → 多元线性回归 / 岭回归
│   └── 多因变量且相关 → 多输出回归 / PLS2
├── 变量之间相关性（两组变量）？
│   ├── 求两组变量整体线性相关 → 典型相关分析 CCA
│   │   └── sklearn.cross_decomposition.CCA（或先 PCA 正则化）
│   └── 两两相关即可 → 简单相关系数矩阵 + 热力图
└── 定性（分类）变量间关联？
    ├── 双向列联表，想看行类与列类的关联可视 → 对应分析 CA
    │   └── 卡方检验 + 对应分析双标图（biplot）
    └── 只是检验独立性 → 卡方检验即可，不必 CA
```

---

## 二、偏最小二乘回归（PLS）

### 2.1 原理

PLS 在自变量 X 与因变量 Y 中同时提取「潜在成分」（latent components），使成分**对 Y 的解释能力最强**，再用成分做回归。与 PCA+OLS 的关键区别：PLS 提成分时考虑了与 Y 的相关性，因此降维不损失预测信息。

**目标**：找到权重向量 w, c，使成分 t = Xw 与 u = Yc 的协方差最大：

```
maximize   Cov(t, u) = Cov(Xw, Yc)
s.t.       ||w|| = ||c|| = 1
```

随后迭代对残差重复提取，得到 h 个正交成分构成的回归模型：

```
Y = X·B + E,   B = W(PᵀW)⁻¹Qᵀ
```

### 2.2 适用条件

| 条件 | 说明 |
|------|------|
| 自变量间强共线性 | VIF 很大、PCA 方差无法区分 |
| 高维小样本 | p（变量数）接近或超过 n（样本数） |
| 预测导向 | 需要回归系数与预测能力，而非因果推断 |
| 多因变量 | PLS2 可同时处理多个相关因变量 |

### 2.3 建模步骤

```
1. 数据标准化（X、Y 均需中心化/标准化）
2. 交叉验证选择最优成分数 n_components
3. 拟合 PLS，查看 X/Y 载荷与得分
4. 用交叉验证 R²(Q²) 评估拟合与泛化
5. 输出 VIP（变量重要性投影）筛选关键自变量
```

### 2.4 代码要点

```python
import numpy as np
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

def pls_regression(X, y, max_components=None):
    """
    X: (n, p) 自变量矩阵；y: (n,) 或 (n, q)
    用交叉验证选择成分数并拟合
    """
    Xs = StandardScaler().fit_transform(X)
    ys = StandardScaler().fit_transform(y.reshape(-1, 1)).ravel()

    if max_components is None:
        max_components = min(X.shape[1], 10)

    best_k, best_score = 1, -np.inf
    for k in range(1, max_components + 1):
        pls = PLSRegression(n_components=k)
        # 负均方误差越大越好
        scores = cross_val_score(pls, Xs, ys, cv=5, scoring='neg_mean_squared_error')
        mean_score = scores.mean()
        if mean_score > best_score:
            best_k, best_score = k, mean_score

    pls = PLSRegression(n_components=best_k)
    pls.fit(Xs, ys)
    print(f"最优成分数: {best_k}, 交叉验证 MSE: {-best_score:.4f}")
    print(f"训练 R²: {pls.score(Xs, ys):.4f}")

    # VIP 变量重要性
    t = pls.x_scores_            # (n, k) 成分得分
    w = pls.x_weights_           # (p, k) 权重
    q = pls.y_loadings_.ravel()  # (k,) 成分对 y 的载荷
    p = Xs.shape[1]
    s = np.sum(t ** 2, axis=0)   # 每个成分的平方和
    vip = np.sqrt(p * np.sum((w ** 2).T * (q ** 2 * s), axis=1) /
                  np.sum(q ** 2 * s))
    return pls, best_k, vip
```

### 2.5 常见陷阱

| 陷阱 | 说明与对策 |
|------|-----------|
| 成分数选择 | 成分数过多会过拟合；用交叉验证 Q² 而非训练 R² 决定，Q² 明显下降即停 |
| 不标准化 | X/Y 量纲差异大时 PLS 结果偏差；务必先 StandardScaler |
| 误当因果 | PLS 只保证预测，系数不代表因果；避免过度解读 VIP 的含义 |
| 与 PCA+OLS 混淆 | PLS 成分考虑了 Y，预测通常更优；但若 Y 与 X 前几主成分无关，两者接近 |

---

## 三、对应分析（CA）

### 3.1 原理

对应分析用于**双向列联表**（两个定性变量），把行、列的类别映射到同一个低维空间，使「行-列关联」可视化为双标图（biplot）：距离近的点关联强。

**核心**：对列联表 P = (pᵢⱼ)（频率矩阵），做卡方距离下的 SVD 分解：

```
标准化残差:  S = Dr⁻¹ᐟ²·(P - r·cᵀ)·Dc⁻¹ᐟ²
SVD:         S = U·Λ·Vᵀ
行坐标:      F = Dr⁻¹ᐟ²·U·Λ     列坐标: G = Dc⁻¹ᐟ²·V·Λ
```

其中 r、c 为行、列边际频率，Dr、Dc 为对角矩阵。总惯量（inertia）= χ²/n，衡量变量关联总强度。

### 3.2 适用条件

| 条件 | 说明 |
|------|------|
| 两个定性（分类）变量 | 构成 r×c 列联表 |
| 卡方检验拒绝独立 | χ² 显著（p < 0.05）才值得做 CA |
| 类别数适中 | 类别过多（>20）时图难以解读 |
| 无结构零 | 某格频数为 0 需谨慎（可加平滑） |

### 3.3 建模步骤

```
1. 构建列联表（pd.crosstab）
2. 卡方检验独立性（scipy.stats.chi2_contingency）
3. 若不独立，做对应分析得到行/列坐标与惯量
4. 绘制前两维双标图，解读相近点关联
5. 报告各维惯量贡献率，评估二维是否失真
```

### 3.4 代码要点

```python
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

def correspondence_analysis(ct):
    """
    ct: 列联表 DataFrame，行为第一个变量，列为第二个变量
    返回行坐标、列坐标、惯量贡献率（前两个维度）
    """
    # 卡方独立性检验
    chi2, p_value, dof, _ = chi2_contingency(ct.values)
    print(f"卡方检验: χ²={chi2:.2f}, p={p_value:.4e}, 自由度={dof}")

    P = ct.values / ct.values.sum()          # 频率矩阵
    r = P.sum(axis=1, keepdims=True)         # 行边际
    c = P.sum(axis=0, keepdims=True)         # 列边际

    Dr = np.diag(r.ravel() ** -0.5)
    Dc = np.diag(c.ravel() ** -0.5)
    S = Dr @ (P - r @ c) @ Dc                # 标准化残差

    U, s, Vt = np.linalg.svd(S, full_matrices=False)
    # 各维惯量贡献率
    inertia = (s ** 2) / (chi2 / ct.values.sum())
    row_coords = Dr @ U * s
    col_coords = Dc @ Vt.T * s

    print("前两维惯量贡献率: %.1f%% + %.1f%%"
          % (inertia[0] * 100, inertia[1] * 100))
    return row_coords, col_coords, s, inertia
```

> 若需要更友好的导出（含双标图），可用 `prince.CA` 库：`prince.CA(n_components=2).fit(ct)`。

### 3.5 常见陷阱

| 陷阱 | 说明与对策 |
|------|-----------|
| 只展示前两维的失真 | 二维惯量贡献率低（<70%）时，图中距离可能误导；必须报告惯量贡献率 |
| 把「距离近」绝对化 | 应同时看行-列（biplot）而非行-行距离；行间欧氏距离在 CA 中无严格含义 |
| 未先做卡方检验 | 变量本无关联时 CA 图是噪声；先验 χ² 显著再做 |
| 类别顺序影响 | CA 忽略有序变量顺序；有序变量考虑用多重对应分析（MCA）或相关性分析 |

---

## 四、典型相关分析（CCA）

### 4.1 原理

CCA 度量**两组变量**（X: p 个，Y: q 个）之间的整体线性相关性，寻找线性组合 aᵀX、bᵀY 使相关系数最大：

```
maximize   Corr(aᵀX, bᵀY) = aᵀΣxy·b / √(aᵀΣxx·a · bᵀΣyy·b)
```

等价于广义特征值问题（Σ 为分块协方差矩阵）：

```
Σxy·Σyy⁻¹·Σyx·a = λ·Σxx·a
```

依次得到 k = min(p, q) 对典型变量，第 i 对对应典型相关系数 rᵢ = √λᵢ。对典型相关系数做假设检验判断显著对数。

### 4.2 适用条件

| 条件 | 说明 |
|------|------|
| 两组连续变量 | X、Y 均为数值型 |
| 样本量足够 | n ≥ 10×max(p, q)，否则 Σyy 病态、典型相关会退化到 1 |
| 无强共线性 | 组内变量高度相关时需正则化（先 PCA） |
| 线性关系为主 | 非线性关系需先变换或用核方法 |

### 4.3 建模步骤

```
1. 标准化两组变量
2. 若 p 或 q 接近 n → 先对组内做 PCA 降维（正则化 CCA）
3. 求解典型变量与典型相关系数
4. 对典型相关系数做显著性检验（Wilks' lambda 近似）
5. 解读显著典型变量对的载荷（结构系数）
```

### 4.4 代码要点

```python
import numpy as np
from sklearn.cross_decomposition import CCA

def canonical_correlation(X, Y, n_components=None):
    """
    X: (n, p), Y: (n, q)
    返回典型相关系数、典型变量、载荷
    注：sklearn 的 CCA 要求 n > max(p, q)，否则需正则化
    """
    n_components = n_components or min(X.shape[1], Y.shape[1])
    cca = CCA(n_components=n_components)
    cca.fit(X, Y)
    Xc, Yc = cca.transform(X, Y)

    # 典型相关系数 = 各典型变量间的皮尔逊相关
    corrs = np.array([
        np.corrcoef(Xc[:, i], Yc[:, i])[0, 1] for i in range(n_components)
    ])
    return corrs, Xc, Yc, cca
```

正则化 CCA（高维小样本时）：

```python
import numpy as np
from sklearn.decomposition import PCA

def regularized_cca(X, Y, keep_x=None, keep_y=None, n_components=2):
    """
    先对两组分别 PCA 降维再 CCA，避免 Σ 病态
    """
    from sklearn.preprocessing import StandardScaler
    Xs = StandardScaler().fit_transform(X)
    Ys = StandardScaler().fit_transform(Y)

    keep_x = keep_x or min(Xs.shape[1], 10)
    keep_y = keep_y or min(Ys.shape[1], 10)
    Xp = PCA(n_components=keep_x).fit_transform(Xs)
    Yp = PCA(n_components=keep_y).fit_transform(Ys)

    cca = CCA(n_components=min(n_components, keep_x, keep_y))
    cca.fit(Xp, Yp)
    Xc, Yc = cca.transform(Xp, Yp)
    corrs = np.array([
        np.corrcoef(Xc[:, i], Yc[:, i])[0, 1] for i in range(Xc.shape[1])
    ])
    return corrs, Xc, Yc
```

### 4.5 常见陷阱

| 陷阱 | 说明与对策 |
|------|-----------|
| 典型相关退化到 1 | n 不足或组内共线性导致 Σyy 奇异；用正则化 CCA / 先 PCA |
| 只报告第一对 | 需检验显著对数，低阶典型相关可能是噪声 |
| 载荷与系数混淆 | 局部载荷 = 典型变量与原变量相关（结构系数）；标准化前不具可比性 |
| 与 kCCA 混用 | 非线性关系应使用核 CCA，但样本内总会高估，注意交叉验证 |

---

## 五、竞赛常见场景

| 题型 | 题型含义 | 典型场景 | 推荐方法组合 |
|------|---------|---------|-------------|
| A | 物理建模 | 光谱/物理量多组变量耦合关系 | CCA（两组物理特征相关性）+ PLS 标定 |
| B | 实验设计 | 多因素工艺参数对多指标的影响 | PLS + VIP 筛选 + 方差分析 |
| C | 数据分析 | 高维少样本成分/指标预测（如成分检测） | PLS 回归（交叉验证选成分数） |
| C | 数据分析 | 问卷/列联表定性变量关联挖掘 | 卡方检验 + 对应分析双标图 |
| D | 优化调度 | 指标间耦合 → 降维后再优化 | PLS/CCA 降维 + 约束优化 |
| E | 交叉学科 | 经济-环境-社会多组指标相关 | CCA + 前两维可视化解读 |

---

## 六、参考资源

- 教材：《多元统计分析》（高惠璇）、《多元数据分析》（Lattin）
- Python 库：`sklearn.cross_decomposition`（PLSRegression / CCA）、`prince`（CA / MCA）、`scipy.stats`（卡方检验）
- 扩展：`pyrcca`（正则化 CCA）、`statsmodels`（多元检验）

### 检查清单

- [ ] 数据已标准化（PLS / CCA 必需）
- [ ] PLS 成分数由交叉验证确定，报告 Q² 而非仅 R²
- [ ] CA 前已通过卡方独立性检验，且报告前两维惯量贡献率
- [ ] CCA 在 n < 10×max(p,q) 时已做正则化（先 PCA）
- [ ] 典型相关报告了显著对数与对应载荷
- [ ] 结论未混淆相关与因果，载荷解读正确
- [ ] 随机种子固定 42，交叉验证可复现