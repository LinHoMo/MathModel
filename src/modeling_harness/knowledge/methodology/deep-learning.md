# 深度学习（Deep Learning）领域知识

## 一、核心概念

### 1.1 定位
- 深度学习是表示学习的分支：用多层非线性变换自动学特征，替代手工特征工程。
- 竞赛定位：**备选而非默认**。样本少（<1000）、可解释性要求高时，传统统计/树模型更稳；数据量大、结构信号强（时序/图像/文本）时深度模型优势明显。

### 1.2 常用架构速查
| 架构 | 适用信号 | 竞赛典型任务 |
|---|---|---|
| MLP | 表格特征 | 回归/分类基线 |
| CNN | 空间/图像 | 缺陷识别、图像分割 |
| LSTM / GRU | 时序 | 负荷预测、销量预测 |
| TCN / 1D-CNN | 长时序 | 训练更快，替代 LSTM |
| Transformer（自注意力） | 长依赖序列 | 多步预测、文本 |
| U-Net | 图像分割 | 区域提取 |

### 1.3 正则化与防过拟合（必做）
- Dropout、权重衰减、早停（监控验证集）
- 数据增强（时序：加噪/滑窗；图像：翻转/裁剪）
- 训练/验证/测试切分必须按时间顺序（时序禁止随机切分，防未来信息泄漏）

---

## 二、基本方法

### 2.1 时序预测骨架（PyTorch 风格，可降级为 numpy 手写）

```python
def make_windows(series, lookback=24, horizon=1):
    """滑窗构造监督样本；时序切分必须按时间顺序。"""
    X, y = [], []
    for i in range(len(series) - lookback - horizon + 1):
        X.append(series[i:i + lookback])
        y.append(series[i + lookback:i + lookback + horizon])
    return np.array(X), np.array(y)

# 切分：前 70% 训练，中 15% 验证（调早停），后 15% 测试（只跑一次）
```

### 2.2 评估口径（多指标，铁律联动）
- 回归：RMSE / MAE / MAPE / R² 全报；单报 R² 会掩盖量纲问题。
- 分类：Accuracy + F1 + AUC；类别不平衡必须报 F1/混淆矩阵。
- 预测类必须与至少一个非深度基线（ARIMA、线性回归、树模型）对比——评审只看"深度"而无基线是反模式。

### 2.3 无 GPU 环境降级
- 小网络（1-2 层、≤128 单元）+ 小批量 + ≤100 epoch 在 CPU 可行；报告训练耗时。
- 或改用 `sklearn` 的 MLPRegressor/MLPClassifier（零依赖路线）。

---

## 三、竞赛应用要点

### 3.1 论文写法
- 结构图 + 超参数表（层数、单元数、优化器、学习率、batch、早停轮次）必须完整，保证可复现。
- 必须写"为什么选深度模型而不是传统方法"（数据量、非线性、特征维度三条理由至少一条可量化）。

### 3.2 可复现（铁律 P1）
```python
import torch
torch.manual_seed(42)
np.random.seed(42)
torch.backends.cudnn.deterministic = True  # 若用 GPU
```

### 3.3 图表规范
- 训练/验证损失曲线（判断过拟合）
- 预测值 vs 真实值对比图 + 残差图
- 多模型对比条形图（RMSE/MAE，配数值表）

### 3.4 LaTeX 代码

```latex
\begin{equation}
h_t = \sigma(W_x x_t + W_h h_{t-1} + b),\quad
\hat{y}_{t+k} = W_o h_t
\label{eq:lstm}
\end{equation}
```

---

## 四、常见错误

1. **时序随机切分**: 未来值泄漏进训练集，测试指标虚高——评审常见识破点。
2. **无基线对比**: 深度模型必须与统计基线对比，否则选型正当性不成立。
3. **只报最优一次运行**: 必须固定种子；启发式/随机初始化须多次运行报均值±标准差。
4. **过拟合不自检**: 训练误差 →0 而验证误差不降，论文仍声称"拟合良好"。
5. **超参数不写**: 复现性缺失直接扣分。

---

## 五、参考文献

1. Goodfellow I, Bengio Y, Courville A. Deep Learning. MIT Press, 2016.
2. LeCun Y, Bengio Y, Hinton G. Deep learning. Nature, 2015, 521: 436-444.
3. Hochreiter S, Schmidhuber J. Long short-term memory. Neural Computation, 1997, 9(8): 1735-1780.
4. 周志华. 机器学习. 清华大学出版社, 2016.
