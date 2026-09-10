# 基于智能体的仿真（Agent-Based Simulation）领域知识

## 一、核心概念

### 1.1 定义与思想
- **定义**: 用大量遵循局部规则的自主个体（agent）交互，涌现出宏观现象的自底向上建模方法。
- **核心思想**: 宏观规律不预设，由微观交互涌现（emergence）。
- **与系统动力学的区别**: 系统动力学是宏观聚合量（存量-流量）；ABM 是异质个体的显式交互，适合空间分布、网络接触、个体差异显著的场景。

### 1.2 适用场景
- 传染病传播（接触网络上的感染扩散）
- 交通流、人群疏散、舆论传播
- 市场经济中异质主体行为（消费、迁徙）
- 生态系统（捕食者-猎物、植被演替）

### 1.3 ODD 协议（必写）
论文描述 ABM 应遵循 ODD（Overview-Design-Details）：
1. **Overview**: 目的、实体与状态变量、时空尺度。
2. **Design**: 过程调度、初始化、输入数据、子模型。
3. **Details**: 状态变量更新规则、随机性来源、交互规则。

---

## 二、基本方法

### 2.1 最小实现（零第三方依赖）

```python
import numpy as np

def sir_abm(n_agents: int, beta: float, gamma: float, days: int,
            seed: int = 42, adjacency: np.ndarray | None = None) -> dict:
    """网格/网络上的 SIR 智能体仿真。
    adjacency: 接触邻接表（None 时用完全混合近似）。
    """
    rng = np.random.default_rng(seed)
    state = np.zeros(n_agents, dtype=int)  # 0=S,1=I,2=R
    state[rng.integers(0, n_agents, size=max(1, n_agents // 100))] = 1
    history = {"S": [], "I": [], "R": []}
    for _ in range(days):
        infect = np.zeros(n_agents, dtype=bool)
        for i in np.where(state == 1)[0]:
            neighbors = (range(n_agents) if adjacency is None
                         else adjacency[i])
            for j in neighbors:
                if state[j] == 0 and rng.random() < beta:
                    infect[j] = True
        state[infect] = 1
        recovered = (state == 1) & (rng.random(n_agents) < gamma)
        state[recovered] = 2
        history["S"].append(int((state == 0).sum()))
        history["I"].append(int((state == 1).sum()))
        history["R"].append(int((state == 2).sum()))
    return history
```

### 2.2 空间与网络
- **网格空间**: 细胞自动机式邻接（von Neumann / Moore 邻域），适合空间扩散。
- **网络接触**: WS 小世界 / BA 无标度网络上的传播；接触结构显著改变流行阈值。
- **连续空间**: 个体位置 + 移动核（movement kernel），距离衰减接触概率。

### 2.3 校准与验证
- **校准**: 用真实曲线（如感染人数）反推参数（beta/gamma），可用 ABC（近似贝叶斯计算）或网格搜索。
- **验证**: 极端情形（beta=0 不传播、gamma=1 立即康复）；守恒检查（S+I+R=N）；与解析模型（SIR 微分方程）在大 N 极限下对比。

---

## 三、竞赛应用要点

### 3.1 选型理由写法
说明"个体异质性/空间结构/局部交互"为何使聚合方程失效，是 ABM 的正当性来源。

### 3.2 铁律联动
- **固定随机种子**（铁律 P1）：`rng = np.random.default_rng(42)`，启发式结论须 ≥5 次独立运行报均值±标准差。
- **规模控制**: N 与仿真天数做权衡；报告单次运行耗时，证明时限内可完成。

### 3.3 图表规范
- 时间序列：S/I/R 曲线（多随机种子叠加半透明带）。
- 空间快照：网格状态热图，标注时间点。
- 相图：感染峰值随 β 变化（体现阈值效应）。

### 3.4 LaTeX 代码

```latex
\begin{equation}
P(i \to I \mid t) = 1 - (1-\beta)^{k_i(t)}
\label{eq:abm_infect}
\end{equation}
其中 $k_i(t)$ 为 $t$ 时刻与个体 $i$ 接触的感染者数量。
```

---

## 四、常见错误

1. **无校准直接用文献参数**: 参数必须与本题数据/尺度匹配，否则结论不可信。
2. **单次运行下结论**: 随机仿真必须多种子统计（均值、方差、分位数）。
3. **宏观量不守恒未检查**: S+I+R≠N 说明状态机实现有 bug。
4. **忽视计算规模**: N=10⁶ + 完全混合邻接 = O(N²) 每步，时限内跑不完；必须改稀疏邻接或抽样接触。

---

## 五、参考文献

1. Bonabeau E. Agent-based modeling: Methods and techniques for simulating human systems. PNAS, 2002, 99(suppl 3): 7280-7287.
2. Grimm V, Railsback S F. Individual-based Modeling and Ecology. Princeton University Press, 2005.
3. Grimm V, et al. The ODD protocol: A review and first update. Ecological Modelling, 2010, 221(23): 2760-2768.
4. Newman M E J. Networks. Oxford University Press, 2018.
