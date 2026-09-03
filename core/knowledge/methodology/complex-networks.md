# 复杂网络（Complex Networks）领域知识

## 一、核心概念

### 1.1 定位
- 以图结构承载交互关系的系统建模：传播、级联失效、关键节点识别、社区结构。
- 与经典图论（最短路/流）的区别：复杂网络关注**统计结构与涌现性质**（度分布、聚集、社区、鲁棒性），而非单一组合优化。

### 1.2 关键指标
| 指标 | 定义要点 | 用途 |
|---|---|---|
| 度分布 P(k) | 幂律 ⇒ 无标度 | 识别枢纽节点、传播阈值 |
| 聚类系数 | 邻居互联程度 | 社区性、传播聚集 |
| 平均路径长度 | 小世界性 | 信息/病毒扩散速度 |
| 介数中心性 | 经过节点的最短路比例 | 关键节点/瓶颈识别 |
| 模块度 Q | 社区划分质量 | 社区检测评价 |

---

## 二、基本方法

### 2.1 网络生成（零第三方依赖）

```python
import numpy as np

def ws_small_world(n: int, k: int, p: float, seed: int = 42) -> set[tuple[int, int]]:
    """Watts-Strogatz 小世界网络：环形最近邻 + 概率 p 重连。"""
    rng = np.random.default_rng(seed)
    edges = set()
    for i in range(n):
        for j in range(1, k // 2 + 1):
            a, b = i, (i + j) % n
            if rng.random() < p:
                b = int(rng.integers(0, n))
                if b == a:
                    b = (i + j) % n
            edges.add((min(a, b), max(a, b)))
    return edges

def ba_scale_free(n: int, m: int, seed: int = 42) -> set[tuple[int, int]]:
    """Barabasi-Albert 无标度网络：优先连接。"""
    rng = np.random.default_rng(seed)
    edges, targets = set(), list(range(m))
    repeated = list(range(m))
    for new in range(m, n):
        chosen = set(rng.choice(repeated, size=m, replace=False))
        for old in chosen:
            edges.add((min(new, old), max(new, old)))
        repeated.append(new)
        repeated.extend(chosen)
    return edges
```

### 2.2 网络上的传播（SIR）
- 与 `agent-based-simulation.md` 的 ABM 框架相同，但接触结构换成真实/拟合网络。
- **传播阈值**: 无标度网上流行阈值趋于 0（枢纽节点驱动），与均匀混合模型差异显著——论文要强调这点。

### 2.3 关键节点识别
- 度中心性（快、粗）→ 介数中心性（准、O(VE)）→ k-core / PageRank（有向）。
- 鲁棒性实验：按度/介数**蓄意攻击**与**随机失效**下的最大连通分量衰减曲线对比。

### 2.4 社区检测
- 贪心模块度（Louvain 思想）或标签传播（零依赖可实现）；评价用模块度 Q 与 NMI（有真值时）。

---

## 三、竞赛应用要点

### 3.1 选型写法
- 题给关系数据（航线、社交、电网、引用）或需要"关键节点/脆弱性/扩散"结论时用。
- 必须交代网络构建口径：节点/边的定义、加权与否、去重与自环处理。

### 3.2 验证
- 生成网络要对照理论指标（BA 网度分布斜率 ≈ -3；WS 在 p 小时高聚集短路径）。
- 真实网络的幂律拟合须做统计检验（对数似然比或 KS），不能只画双对数直线。

### 3.3 图表规范
- 网络可视化（节点大小 ∝ 度，枢纽着色）
- 度分布双对数图 + 拟合线
- 攻击鲁棒性曲线（蓄意 vs 随机）
- 社区着色图 + 模块度表

### 3.4 LaTeX 代码

```latex
\begin{equation}
P(k) \sim k^{-\gamma},\qquad
C = \frac{1}{n}\sum_i \frac{2e_i}{k_i(k_i-1)}
\label{eq:network}
\end{equation}
```

---

## 四、常见错误

1. **双对数图"目测"幂律**: 无统计检验的幂律断言是评审常见质疑点。
2. **网络构建口径不清**: 边的定义模糊导致全部结论存疑。
3. **介数中心性跑大图**: O(VE) 在 10⁵ 边上不可行，需采样近似并说明。
4. **把生成网络当真实结构**: 用 BA/WS 做敏感性可以，替代真实网络须论证。

---

## 五、参考文献

1. Newman M E J. Networks. Oxford University Press, 2018.
2. Barabasi A L, Albert R. Emergence of scaling in random networks. Science, 1999, 286: 509-512.
3. Watts D J, Strogatz S H. Collective dynamics of 'small-world' networks. Nature, 1998, 393: 440-442.
4. Clauset A, Shalizi C R, Newman M E J. Power-law distributions in empirical data. SIAM Review, 2009, 51(4): 661-703.
