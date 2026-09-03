# Playbook 索引（端到端例题）

> 每个 Playbook 覆盖「拆题 → 建模 → 代码 → 验证 → 论文」全流程，可直接作为竞赛参考模板。
> 共 12 篇：国赛 9 篇（A/B/C/D/E 五题型覆盖）+ 美赛 3 篇（A 连续 / B 离散 / C 数据）。

## 国赛（CUMCM）

| 文档 | 年份/题号 | 题型 | 核心方法 | 关键词 |
|---|---|---|---|---|
| [playbook-2024A-bench-dragon.md](playbook-2024A-bench-dragon.md) | 2024 A | 机理/运动学 | 多体递推+悬链线+微分几何 | 板凳龙、螺旋运动、调头 |
| [playbook-2023B-production.md](playbook-2023B-production.md) | 2023 B | 组合优化 | 0-1 整数规划+GA+仿真 | 生产决策、调度、资源分配 |
| [playbook-2023C-ml-prediction.md](playbook-2023C-ml-prediction.md) | 2023 C | 数据分析/预测 | XGBoost+LSTM+特征工程 | 机器学习、时序预测、分类 |
| [playbook-2022B-experiment.md](playbook-2022B-experiment.md) | 2022 B | 统计/实验 | ANOVA+响应面+回归 | 实验设计、工艺优化、因素分析 |
| [playbook-2021D-transportation.md](playbook-2021D-transportation.md) | 2021 D | 网络/运筹 | 图论+VRP+启发式 | 路径规划、车辆调度、网络流 |
| [playbook-2020E-environment.md](playbook-2020E-environment.md) | 2020 E | 跨学科/评价 | 系统动力学+AHP+仿真 | 生态环境、政策评估、可持续发展 |
| [playbook-2019A-heat.md](playbook-2019A-heat.md) | 2019 A | 机理/PDE | 有限差分+热传导+参数反演 | 温度场、逆问题、数值模拟 |
| [playbook-2018B-scheduling.md](playbook-2018B-scheduling.md) | 2018 B | 调度/仿真 | 事件驱动仿真+SA+排队论 | RG V 调度、碰撞检测、排队 |
| [playbook-2017C-data.md](playbook-2017C-data.md) | 2017 C | 数据/统计 | 聚类+回归+时间序列 | 数据挖掘、特征工程、趋势分析 |

## 美赛（MCM/ICM）

| 文档 | 年份/题号 | 题型 | 核心方法 | 关键词 |
|---|---|---|---|---|
| [playbook-mcm-A-continuous.md](playbook-mcm-A-continuous.md) | MCM A | 连续/机理 | ODE/PDE+数值方法+优化 | 物理建模、微分方程、参数估计 |
| [playbook-mcm-B-discrete.md](playbook-mcm-B-discrete.md) | MCM B | 离散/图论 | 图论+网络流+启发式 | 组合优化、网络设计、调度 |
| [playbook-mcm-C-data.md](playbook-mcm-C-data.md) | MCM C | 大数据/预测 | ML+时序+集成学习 | 数据驱动、预测模型、特征选择 |

## Playbook 标准结构

每个 Playbook 包含以下 9 个模块：

```
1. 问题拆解 (Problem Decomposition)    — 结构化 JSON，子问依赖关系
2. 类型判定 (Type Classification)       — A/B/C/D/E 分类 + 方法方向
3. 候选模型对比 (Candidate Comparison)  — ≥3 候选方法，优劣对比表
4. 模型建立 (Model Derivation)          — 完整数学推导，符号/假设/边界
5. 代码实现 (Code Implementation)       — 完整可运行 Python 代码
6. 结果验证 (Validation Report)         — 灵敏度/交叉验证/数值一致性
7. 论文结构 (Paper Structure)           — 章节规划 + 字数分配
8. 关键图表 (Key Figures)               — 必做图表清单 + 生成代码
9. LaTeX 源码 (LaTeX Source)            — 可直接编译的论文片段
```

## 使用方式

- **赛前训练**：按题型选 2-3 个 Playbook 精读，掌握全流程
- **赛中参考**：快速定位同题型 Playbook，复用代码框架和论文结构
- **方法选型**：对比候选模型表，选择最适合当前问题的方法组合
