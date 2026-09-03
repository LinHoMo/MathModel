# Cookbook: 统计推断类模型

> 适用场景：假设检验、置信区间、方差分析、回归诊断、因果推断、贝叶斯分析。各题型辅助验证高频。

---

## 1. 参数/非参数假设检验

| 检验 | 适用场景 | 假设 | 代码模板 |
|------|----------|------|----------|
| **t检验 (单样本/双样本/配对)** | 均值比较、正态/近似正态、σ未知 | 正态性、独立性、方差齐性(双样本) | `ttest_template.py` |
| **Z检验** | 样本大(n>30)或σ已知 | 正态性、σ已知 | `ztest_template.py` |
| **卡方检验 (拟合优度/独立性/同质性)** | 分类频数、列联表 | 期望频数≥5、独立 | `chisq_template.py` |
| **F检验** | 方差比较、ANOVA | 正态性、独立性 | `ftest_template.py` |
| **Wilcoxon 符号秩秩** | 配对非正态 | 对称分布、独立 | `wilcoxon_template.py` |
| **Mann-Whitney U** | 两独立样本非正态 | 独立、序数/连续 | `mannwhitney_template.py` |
| **Kruskal-Wallis** | 多独立样本非正态 | 独立、同形状 | `kruskal_template.py` |
| **Kolmogorov-Smirnov** | 分布拟合/两样本分布差异 | 连续分布 | `ks_template.py` |

**效应量**：Cohen's d / η² / r / Cliff's delta —— **必须报告**，不仅看 p 值

**代码模板目录**：
```
core/Programmer/knowledge/code-templates/statistical/
├── ttest_template.py
├── ztest_template.py
├── chisq_template.py
├── ftest_template.py
├── wilcoxon_template.py
├── mannwhitney_template.py
├── kruskal_template.py
├── ks_template.py
├── anova_template.py
├── ancova_template.py
├── regression_diagnostics.py
├── causal_inference.py
├── bayesian_template.py
├── bootstrap_template.py
├── monte_carlo_template.py
├── survival_template.py
├── meta_analysis.py
└── power_analysis.py
```

---

## 2. 方差分析 (ANOVA) / 协方差分析 (ANCOVA)

| 类型 | 适用场景 | 模型 | 代码模板 |
|------|----------|------|----------|
| **单因素 ANOVA** | 一个分类自变量、连续因变量 | `y_ij = μ + α_i + ε_ij` | `anova_template.py` |
| **双因素/多因素 ANOVA** | 多因素、交互作用 | `y_ijk = μ + α_i + β_j + (αβ)_ij + ε_ijk` | `anova_two_way.py` |
| **重复测量 ANOVA** | 同受试者多条件/时间点 | 球形假设/Greenhouse-Geisser 校正 | `anova_repeated.py` |
| **MANOVA** | 多个相关因变量 | 多元正态、协方差矩阵齐 | `manova_template.py` |
| **ANCOVA** | 协变量控制、调整组间差异 | 回归斜率齐性 | `ancova_template.py` |

**事后比较**：Tukey HSD / Bonferroni / Scheffé / Dunnett / Games-Howell (方差不齐)

**验证清单**：✅ 正态性(Shapiro-Wilk/QQ图) ✅ 方差齐性(Levene/Bartlett) ✅ 独立性 ✅ 事后比较校正 ✅ 效应量报告

---

## 3. 回归分析与诊断

| 模型 | 适用场景 | 关键假设 | 代码模板 |
|------|----------|----------|----------|
| **线性回归 (OLS)** | 连续因变量、线性关系 | 线性、独立、同方差、正态、无多重共线性 | `regression_ols.py` |
| **广义线性模型 (GLM)** | 二项/泊松/Gamma 族、链接函数 | 指数族分布、链接函数正确 | `regression_glm.py` |
| **混合效应/多层模型** | 聚类/层次/重复测量 | 随机效应正态、残差独立 | `regression_mixed.py` |
| **量化回归** | 条件分位数、异方差/重尾 | 无分布假设 | `regression_quantile.py` |
| **稳健回归** | 异常值/杠杆点影响大 | Huber/Tukey/M-estimator | `regression_robust.py` |

**诊断必做**：
1. 残差 vs 拟合值 (非线性/异方差)
2. QQ 图 (正态性)
3. Scale-Location (同方差)
4. Cook's Distance / Leverage (异常/影响点)
5. VIF (多重共线性, >5/10 警告)
6. Durbin-Watson (自相关)
7. Rainbow/RESET (线性)

---

## 4. 贝叶斯统计

| 方法 | 适用场景 | 先验选择 | 代码模板 |
|------|----------|----------|----------|
| **贝叶斯线性回归** | 参数不确定性、小样本、先验知识 | 共轭先验/弱信息先验(正态/半柯西/马蹄) | `bayesian_linear.py` (PyMC/NumPyro) |
| **贝叶斯分层模型** | 多层/分组/部分池化 | 组级超先验 | `bayesian_hierarchical.py` |
| **贝叶斯模型选择** | 模型比较/平均 | WAIC/LOO-CV/Bayes Factor | `bayesian_model_select.py` |
| **变分推断 (VI)** | 大数据/复杂模型、MCMC 慢 | 均场/正态近似 | `bayesian_vi.py` |

**收敛诊断**：R̂ < 1.01、ESS > 400、迹图平稳、分位数覆盖

---

## 5. 因果推断

| 方法 | 适用场景 | 核心假设 | 代码模板 |
|------|----------|----------|----------|
| **倾向得分匹配 (PSM)** | 观测研究、混杂因子可观测 | 强可忽略性、共同支撑 | `causal_psm.py` |
| **反事实/潜在结果框架** | 个体因果效应、CATE | SUTVA、一致性、可忽略性 | `causal_potential.py` |
| **工具变量 (IV/2SLS)** | 内生性、不可观测混杂 | 相关性、排他性、单调性 | `causal_iv.py` |
| **断点回归 (RDD/RDiT)** | 阈值政策/规则、连续赋值变量 | 局部随机化、带宽选取 | `causal_rdd.py` |
| **双重差分 (DID)** | 面板/政策冲击、平行趋势 | 平行趋势、无溢出 | `causal_did.py` |
| **综合控制法 (SCM)** | 单一处理单元、捐赠池丰富 | 加权重构、预测期拟合好 | `causal_scm.py` |

---

## 6. 重采样 / 蒙特卡洛

| 方法 | 用途 | 代码模板 |
|------|------|----------|
| **Bootstrap (非参数/参数/残差/野/区块)** | 置信区间/标准误/假设检验/模型选择 | `bootstrap_template.py` |
| **Jackknife** | 偏差估计/方差/影响函数 | `jackknife_template.py` |
| **排列检验** | 精确 p 值、分布自由 | `permutation_test.py` |
| **蒙特卡洛积分/仿真** | 复杂概率/积分/风险度量 | `monte_carlo_template.py` |
| **重要性采样/MCMC** | 稀有事件/后验采样 | `importance_sampling.py` |

---

## 7. 生存分析 / 可靠性

| 方法 | 适用场景 | 代码模板 |
|------|----------|----------|
| **Kaplan-Meier** | 生存曲线估计、中位生存时间 | `survival_km.py` |
| **Cox 比例风险模型** | 协变量效应、风险比 | `survival_cox.py` |
| **参数生存模型** | Weibull/指数/对数正态/广义 Gamma | `survival_parametric.py` |
| **竞争风险 / 多状态模型** | 多种终点事件 | `survival_competing.py` |

---

## 8. 元分析 / 研究综合

| 方法 | 适用场景 | 代码模板 |
|------|----------|----------|
| **固定/随机效应模型** | 效应量合成、异质性检验 | `meta_analysis.py` |
| **亚组分析 / 元回归** | 异质性来源探索 | `meta_regression.py` |
| **发表偏倚检测** | 漏斗图、Egger/Egger/Test、Trim-and-fill | `meta_bias.py` |

---

## 9. 功效分析 / 样本量计算

| 场景 | 参数 | 代码模板 |
|------|------|----------|
| t检验/ANOVA/回归/比例/生存 | α=0.05, 功效=0.8, 效应量, 分配比 | `power_analysis.py` |

---

## 10. 选型决策树 (统计类)

```
研究目的？
├─ 比较均值/比例 → 数据分布？
│   ├─ 正态/大样本 → t/Z/ANOVA → 首选
│   └─ 非正态/小样本 → Wilcoxon/Mann-Whitney/Kruskal → 首选
├─ 关系/预测 → 因变量类型？
│   ├─ 连续 → 线性/GLM/混合/量化/稳健 → 按假设/结构选
│   ├─ 二分类 → Logistic/Probit/贝叶斯 → 首选
│   ├─ 计数 → Poisson/负二项/零膨胀 → 首选
│   └─ 生存时间 → Cox/参数生存/竞争风险 → 首选
├─ 因果效应 → 设计类型？
│   ├─ RCT → ITT/Per-protocol/中介分析
│   ├─ 观测/面板 → PSM/IV/RDD/DID/SCM → 按假设可行性选
│   └─ 单一处理单元 → SCM → 首选
├─ 不确定性量化 → Bootstrap/蒙特卡洛/贝叶斯 → 必做
└─ 样本量规划 → 功效分析 → 赛前必做
```

**铁律**：
- 所有检验 **必须报告效应量 + 置信区间**，不仅 p 值
- 多重比较 **必须校正** (FDR/Bonferroni/Holm)
- 假设检验 **前置功效分析**，事后不补
- 贝叶斯 **必须报告收敛诊断** (R̂, ESS, 迹图)
- 因果推断 **必须明确识别假设** 并做敏感性分析

---

## 11. 竞赛实战提示

| 竞赛 | 题型 | 推荐首选 | 避坑指南 |
|------|------|----------|----------|
| 通用 | 模型验证/灵敏度 | Bootstrap/蒙特卡洛/回归诊断 | 所有关键结果给 CI、效应量 |
| CUMCM C | 数据分析 | 回归/GLM/时序分解/因果 | 滞后特征防泄露、交叉验证 |
| MCM 通用 | 论证支撑 | 贝叶斯/因果/元分析 | 假设显性化、敏感性分析 |

---

*版本：1.0 | 更新：2026-09-01 | 维护：Modeler 手*