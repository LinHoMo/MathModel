# 题型防错速查（TYPE-ANTIPATTERNS-CHECKLIST）

> 供 code-implementer / test-runner / result-verifier / guardrails-checker 读取的跨题型反模式清单。
> 来源：整合 MathModelAgent-main `math_modeling_norms.md` "题型防错速查"与"编码阶段常见错误"小节。
> 本清单按题型分类，每类列出「扣分项 → 正确做法」对，Coding 阶段逐项自检。

---

## 一、优化 / 调度 / 选址 / 路径 / 装箱类

| # | 扣分项（禁止） | 正确做法（必须） | 门禁拦截 |
|---|---|---|---|
| O1 | 漏非负约束、整数约束、容量约束、预算约束、时间窗 | 约束列出清单，代码里逐条实现并标注编号 | test-runner |
| O2 | 连续松弛后直接四舍五入取整，不管可行性 | 取整后必须重验可行性；不可行则用修复启发式（移到最近可行整数点） | test-runner |
| O3 | 非凸 / 启发式求解只跑一次就报"最优" | 多起点（≥5）或多种子，报告均值 ± 标准差 + 最优值 | result-verifier |
| O4 | 优化变量没有物理上界 | 每个变量写清物理下界 / 上界（如绳长 ≤ 离地高度），附来源 | test-runner |
| O5 | `scipy.optimize.minimize` 最大化问题未取负 | 目标函数 `f` 最大化 → 最小化 `-f`；结果记录中还原真实最大目标值 | code-implementer |
| O6 | `scipy` 约束 `fun(x) >= 0` 方向写反 | 代入边界点验证符号，输出约束值 / 边界 / 是否活跃 | test-runner |
| O7 | 只相信求解器 `success` | 必须回代所有约束，逐条报告违反量 | result-verifier |
| O8 | 最后问题目标值未比前问改善（更多资源却未更好） | 先检查：新资源是否写入目标、约束是否反、是否陷入局部最优 | result-verifier |

## 二、多阶段 / 多资源优化

| # | 扣分项 | 正确做法 | 门禁拦截 |
|---|---|---|---|
| MR1 | 后续问题目标值未改善 | 检查新资源是否在目标中被利用、约束是否限制了使用 | result-verifier |
| MR2 | 多个相同量纲目标直接加权 | 先无量纲化（Min-Max / Z-score），再加权或 Pareto | code-implementer |

## 三、多目标优化

| # | 扣分项 | 正确做法 | 门禁拦截 |
|---|---|---|---|
| MO1 | 不同量纲目标直接相加 | 各目标独立归一化后再加权或做 Pareto 前沿分析 | code-implementer |
| MO2 | 仅报告综合得分，未报告各目标分量 | 综合得分 + 各目标分量贡献度（占比 %）| result-verifier |
| MO3 | NSGA-II 参数（种群、代数）随意设置 | 说明参数选择依据，做参数敏感性（种群 50/100/200 对比） | result-verifier |

## 四、微分方程 / 动力学 / 物理仿真

| # | 扣分项 | 正确做法 | 门禁拦截 |
|---|---|---|---|
| D1 | 未声明状态变量单位、初始条件、边界条件 | 表格列出：符号 / 初值 / 单位 / 来源 | code-implementer |
| D2 | 刚性系统默认 ` odeint` 不自检 | 刚性系统用 `Radau` 或 `BDF`，输出求解器类型 | code-implementer |
| D3 | 仿真步长 / 网格未做收敛性检查 | 步长减半对比结果差异（<1% 视为收敛） | result-verifier |
| D4 | 未检查守恒量漂移 | 能量 / 质量守恒量仿真全程记录，报告漂移量 | result-verifier |

## 五、统计 / 回归 / 预测

| # | 扣分项 | 正确做法 | 门禁拦截 |
|---|---|---|---|
| S1 | 时间序列随机打乱划分训练 / 测试 | 按时间顺序划分：前 80% 训练、后 20% 测试 | code-implementer |
| S2 | 先 fit scaler 再划分数据（数据泄露） | 先划分，再在训练集 fit 后 transform 测试集 | code-implementer |
| S3 | 残差未分析 | 残差图 / Q-Q 图 / D-W 自相关检验 | result-verifier |
| S4 | 多重共线性未检查 | VIF 表（>10 为严重共线性），必要时用 Ridge / Lasso 替代 OLS | test-runner |
| S5 | 预测值超出物理边界 | 预测值裁剪到可行域（如浓度 ≥ 0、概率 ∈ [0,1]） | test-runner |
| S6 | 小样本（<15）硬套神经网络 | 改用灰色预测 GM(1,1) / 回归；样本量 < 100 不宜用 DL | model-builder |

## 六、评价 / 排名 / 决策

| # | 扣分项 | 正确做法 | 门禁拦截 |
|---|---|---|---|
| E1 | 正 / 负向指标未统一 | 指标方向表：正向 / 负向 / 区间型，标准化方法说明 | code-implementer |
| E2 | AHP 未做一致性检验 | CR < 0.1 才能通过；不通过则重构判断矩阵 | test-runner |
| E3 | TOPSIS / 熵权法未做赋权敏感性 | 至少两种赋权口径对比排名差异 | result-verifier |
| E4 | 综合得分排序只给结果未解释机制 | 每个排名给出：主驱动指标、其权重、得分贡献 | result-verifier |

## 七、图论 / 网络流 / 路径规划

| # | 扣分项 | 正确做法 | 门禁拦截 |
|---|---|---|---|
| G1 | 有负权边仍用 Dijkstra | 负权 → Bellman-Ford / SPFA；注明算法选择理由 | code-implementer |
| G2 | TSP / VRPTW 出现子回路 | 显式子回路消除约束（MTZ 或 lazy constraint） | test-runner |
| G3 | 最大流未做流量守恒验证 | 除源 / 汇外每个节点入流 = 出流 | test-runner |
| G4 | 未声明图的有向 / 无向性 | 模型建立阶段明确定义邻接矩阵 / 边集类型 | model-builder |

## 八、几何 / 空间优化 / 布局

| # | 扣分项 | 正确做法 | 门禁拦截 |
|---|---|---|---|
| GE1 | 有尺寸实体降维成中心点后做碰撞检测 | 旋转矩形用 OBB/SAT 检测；禁止 AABB 近似（除非证明等价） | code-implementer |
| GE2 | 坐标系 / 角度单位（角度 / 弧度）混用 | 代码顶部统一声明单位，所有三角函数输入统一换算 | code-implementer |
| GE3 | 遮蔽 / 覆盖函数缺少几何尺寸参数 | 参数包含完整尺寸；离散采样近似须做采样数收敛检查 | result-verifier |

## 九、机器学习 / 数据挖掘

| # | 扣分项 | 正确做法 | 门禁拦截 |
|---|---|---|---|
| ML1 | 测试集调参 / 选模型 | 严格三划分：训练 / 验证 / 测试；验证集用于调参 | code-implementer |
| ML2 | 类别不平衡未处理 | 报告类别分布；用过采样 / 欠采样 / 类别权重 | code-implementer |
| ML3 | 黑盒模型（NN/集成）未做可解释性 | SHAP 值 / 特征重要性 / 部分依赖图至少一种 | result-verifier |
| ML4 | 超参数搜索未说明范围与评估指标 | 列出搜索空间、评估指标、交叉验证方案 | code-implementer |

---

## 编码阶段通用速查（编码手必检）

| # | 考点 | 说明 |
|---|---|---|
| C1 | 随机种子 | 所有代码入口必须有 `np.random.seed(42)` 或等效设置 |
| C2 | 单位一致性 | 物理参数单位与 MODEL_SPEC 一致（米 / 秒 / 千克） |
| C3 | JSON 可追溯 | `figures/all_results.json` 每个数值可追溯到代码打印语句 |
| C4 | 列名验证 | 读 CSV / Excel 后打印 `df.columns` 确认列名正确 |
| C5 | 异常值处理决策 | 不能盲目删除必须先判断物理可能性 |
| C6 | matplotlib 中文 | 中文论文必须设置中文字体（SimHei / Microsoft YaHei）|

---

> 使用协议：
> - `code-implementer` 在 Step 2（复制模板后）按本清单过一遍所涉题型；
> - `test-runner` 在 Step 3（跑通后）按 "门禁拦截" 列做逐项检查；
> - `result-verifier` 在数值合理性校验时引用本清单 S5/O8/D3/E3 等判据；
> - `guardrails-checker` 不重复检查这些技术项，仅查文本护栏（禁用词/占位符/AI 痕迹）。
