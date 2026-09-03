# 代理模型（Surrogate Models）领域知识

## 一、核心概念

### 1.1 定义
- 用廉价近似模型（代理）替代昂贵仿真/实验，在设计空间内做预测与寻优。
- 典型链路：**试验设计（采样）→ 拟合代理 → 代理上寻优 → 加点精化**。
- 适用：单次仿真耗时分钟级以上、黑箱、无梯度。

### 1.2 常见代理类型
| 类型 | 特点 | 适用 |
|---|---|---|
| 响应面（多项式） | 简单、可外推弱 | 低维、光滑响应（见 response-surface.md） |
| RBF 径向基 | 插值型、局部强 | 中等维、样本适中 |
| Kriging / 高斯过程 | 带不确定度估计 | 样本少（<100）、需探索-利用权衡 |
| 神经网络代理 | 大样本、高维 | 数据充足 |

---

## 二、基本方法

### 2.1 RBF 插值代理（零依赖实现）

```python
import numpy as np

class RbfSurrogate:
    """高斯径向基插值代理：f(x) = Σ w_i φ(||x - x_i||)。"""

    def __init__(self, eps: float = 1.0):
        self.eps = eps

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.X, self.y = np.asarray(X), np.asarray(y)
        D = np.linalg.norm(self.X[:, None, :] - self.X[None, :, :], axis=-1)
        Phi = np.exp(-(self.eps * D) ** 2)
        self.w = np.linalg.solve(Phi + 1e-8 * np.eye(len(Phi)), self.y)
        return self

    def predict(self, Xq: np.ndarray) -> np.ndarray:
        Xq = np.asarray(Xq)
        D = np.linalg.norm(Xq[:, None, :] - self.X[None, :, :], axis=-1)
        return np.exp(-(self.eps * D) ** 2) @ self.w
```

### 2.2 Kriging / 高斯过程要点
- 核函数常用平方指数核：`k(x, x') = σ² exp(-||x-x'||² / (2ℓ²))`。
- 输出含**预测均值 + 方差**：方差是采样准则（EI/LCB）的核心。
- 超参数（ℓ、σ）用最大边际似然估计；样本 <10 时不稳定，慎用。

### 2.3 采样设计（试验设计）
- 拉丁超立方采样（LHS）是默认选择：分层均匀，维度无关。
```python
def latin_hypercube(n: int, d: int, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    unit = np.zeros((n, d))
    for j in range(d):
        unit[:, j] = (rng.permutation(n) + rng.random(n)) / n
    return unit
```
- 加点准则：期望改进（EI，单目标）、下置信界（LCB，带探索）。

---

## 三、竞赛应用要点

### 3.1 何时引入
- 题目含"仿真昂贵/实验次数有限/黑箱目标函数"信号时使用；否则直接优化原函数即可，不要为用而用。
- 论文必须给出代理精度验证：留出点上的 R² / RMSE / 最大绝对误差。

### 3.2 与决策树的关系
- 决策树「机理+数据混合族」的替代口径：机理仿真昂贵时，代理模型 + 优化 = 双层结构。
- 必须报告：采样点数、代理类型与超参、代理误差、最优解处的真实函数复核值。

### 3.3 图表规范
- 1-2 维时画代理曲面 + 采样点 + 真实函数对照
- 收敛曲线：真实评估次数 vs 当前最优值（代理寻优的证据）
- 预测-真实散点图（留出验证）

### 3.4 LaTeX 代码

```latex
\begin{equation}
\hat{f}(x) = \sum_{i=1}^{n} w_i \exp\bigl(-\varepsilon^2 \|x - x_i\|^2\bigr)
\label{eq:rbf}
\end{equation}
```

---

## 四、常见错误

1. **代理误差不验证**: 直接在代理上宣布最优解，未用真实函数复核最优点。
2. **样本点太少硬拟合高维**: 维数灾难，样本应 ≥10d 量级。
3. **外推当内插用**: 代理只在采样域内可信，超出边界的"最优"无效。
4. **不固定采样设计种子**: LHS/加点序列必须可复现（铁律 P1）。

---

## 五、参考文献

1. Rasmussen C E, Williams C K I. Gaussian Processes for Machine Learning. MIT Press, 2006.
2. Jones D R, Schonlau M, Welch W J. Efficient global optimization of expensive black-box functions. Journal of Global Optimization, 1998, 13: 455-492.
3. Forrester A I J, Sobester A, Keane A J. Engineering Design via Surrogate Modelling. Wiley, 2008.
4. 韩忠华, 高正红. 基于代理模型的设计优化方法研究进展. 航空学报, 2012.
