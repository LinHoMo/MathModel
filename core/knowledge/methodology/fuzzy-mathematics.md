# 模糊数学（Fuzzy Mathematics）领域知识

## 一、核心概念

### 1.1 定位
- 处理"边界不清晰"的类别与评价：优/良/中/差、适宜性等级、风险高低。
- 核心工具：**隶属函数**（把元素映射到 [0,1] 的属于程度）与**模糊综合评价**（权重 × 隶属矩阵）。
- 适用信号：题面要求"分级/评级/适宜性/风险等级"且分级边界天然模糊。

### 1.2 与综合评价法的关系
- 模糊综合评价是 `evaluation-methods.md` 家族的成员：权重可来自 AHP/熵权，隶属矩阵来自隶属函数；常与 TOPSIS 做交叉验证。

---

## 二、基本方法

### 2.1 隶属函数（常用形）

```python
import numpy as np

def tri_mu(x, a, b, c):
    """三角形隶属函数：a 起、b 峰、c 落。"""
    x = np.asarray(x, dtype=float)
    mu = np.zeros_like(x)
    m1 = (x > a) & (x <= b)
    m2 = (x > b) & (x < c)
    mu[m1] = (x[m1] - a) / (b - a)
    mu[m2] = (c - x[m2]) / (c - b)
    mu[x == b] = 1.0
    return mu

def gauss_mu(x, c, sigma):
    return np.exp(-((np.asarray(x, dtype=float) - c) ** 2) / (2 * sigma ** 2))
```

### 2.2 模糊综合评价（零依赖实现）

```python
def fuzzy_evaluation(weights: np.ndarray, R: np.ndarray,
                     method: str = "M(·,+)") -> np.ndarray:
    """weights: (m,) 归一化权重；R: (m, n) 隶属矩阵；返回各等级隶属度。
    method: 'M(·,+)' 加权平均（保留信息）；'M(∧,∨)' 主因素决定型。
    """
    w = weights / weights.sum()
    if method == "M(·,+)":
        b = w @ R
    elif method == "M(∧,∨)":
        b = np.array([max(np.minimum(w[i], R[i])) for _ in range(R.shape[1])]
                     ).reshape(-1)[:R.shape[1]]
        # 注意：严格实现需 b_j = max_i min(w_i, r_ij)
        b = np.array([max(np.minimum(w, R[:, j])) for j in range(R.shape[1])])
    else:
        raise ValueError(method)
    return b / b.sum()
```

### 2.3 完整流程
1. 因素集 U（指标）与评语集 V（等级）定义。
2. 权重：AHP（主观）或熵权（客观），最好组合赋权并对比。
3. 隶属矩阵 R：逐指标选隶属函数（边界来自标准/分位数/专家）。
4. 合成算子：优先 M(·,+)；用 M(∧,∨) 对照看结论是否翻转。
5. 定级：最大隶属度原则；**同时报隶属度向量**，避免"51% vs 49%"型边界误判。

---

## 三、竞赛应用要点

### 3.1 选型写法
- 决策树「决策分析族」：目标含主观分级 → 模糊综合评价；与 AHP 单独使用对比，说明模糊化处理了分级边界不确定性。
- 隶属函数的**参数来源必须写明**（国标、题给阈值、数据分位数），不得拍脑袋。

### 3.2 必做分析
- 权重灵敏度：权重 ±20% 扰动下等级是否翻转。
- 算子对照：M(·,+) 与 M(∧,∨) 结果并列。
- 与另一种评价法（TOPSIS/灰色关联）交叉验证排序一致性（Spearman 相关）。

### 3.3 图表规范
- 隶属函数曲线族（每个等级的 μ(x) 画在同一坐标）
- 隶属度堆叠条形图（样本 × 等级）
- 权重对比图（AHP vs 熵权）

### 3.4 LaTeX 代码

```latex
\begin{equation}
B = W \circ R,\qquad b_j = \sum_{i=1}^{m} w_i\, r_{ij},\quad
\sum_i w_i = 1
\label{eq:fuzzy}
\end{equation}
```

---

## 四、常见错误

1. **隶属函数参数无来源**: 边界凭感觉设定，评审一票否定点。
2. **最大隶属度掩盖边界样本**: 最大两个隶属度接近时必须报告并讨论。
3. **只用单一算子**: M(∧,∨) 会丢信息，只做它不做加权平均是常见缺陷。
4. **权重与隶属都主观**: 至少一侧（权重或边界）用客观数据锚定。
5. **等级排序当成连续数值**: 等级是序关系，不得对等级编号做均值/回归。

---

## 五、参考文献

1. Zadeh L A. Fuzzy sets. Information and Control, 1965, 8(3): 338-353.
2. Wang X Z. Fuzzy Sets Theory and Applications. Springer, 2013.
3. 谢季坚, 刘承平. 模糊数学方法及其应用. 华中科技大学出版社, 2013.
