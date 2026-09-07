# Paper Quality Evaluation — 2021_C (亚洲大黄蜂)

你是一个数学建模论文盲评评委。请对以下三份论文进行独立评分。

## 评分维度（每项 0-100 分）

1. **Mathematical correctness**（数学正确性）：公式/推导/量纲是否正确
2. **Problem alignment**（问题对齐）：论文是否回答了题目要求的所有子问题
3. **Completeness**（完整性）：模型组件覆盖度（变量/约束/目标/假设/方程）
4. **Communication**（表达质量）：结构清晰度、可读性、图表规范性

## 输出格式（严格 JSON）

```json
{
  "papers": [
    {
      "id": "X",
      "scores": {
        "math_correctness": <0-100>,
        "problem_alignment": <0-100>,
        "completeness": <0-100>,
        "communication": <0-100>
      },
      "comments": "<中文评语>"
    },
    {
      "id": "Y",
      "scores": {...},
      "comments": "..."
    },
    {
      "id": "Z",
      "scores": {...},
      "comments": "..."
    }
  ],
  "mutation_audit": [
    {
      "paper_id": "<X/Y/Z>",
      "mutations": [
        {
          "type": "<deletion/addition/modification/renaming/semantic_drift>",
          "severity": "<critical/major/minor>",
          "category": "<variables/constraints/objective/mechanism/assumptions>",
          "affected_object": "<具体对象>",
          "description": "<描述>"
        }
      ]
    }
  ]
}
```

## 注意事项

- 论文已匿名化（X/Y/Z），请勿猜测作者身份
- 只评分论文内容，不评分排版格式
- 每份论文独立评分，不要互相比较
- 输出纯 JSON，不要其他文字


## 题目原文

题目 2021_C


## 论文 X

# 建模论文

## 1 问题重述

本题围绕 4440 条亚洲大黄蜂公众目击报告，要求构建一条完整的证据链，依次回答五个子问题：

1. **扩散可否预测**：评估亚洲大黄蜂时空扩散的可预测性，给出预测精度的置信区间。
2. **误报概率**：在类别极不平衡条件下，估计每条报告的误报概率（真阳性概率的补）。
3. **调查优先级**：在调查预算约束下，确定调查队列以最大化期望阳性发现数。
4. **模型更新**：在新数据到达时，确定模型更新频率的最优权衡。
5. **根除证据**：在检测努力不下降的前提下，判定大黄蜂是否已被根除。

五个子问题共享一条证据链：报告流 →（纠正报告偏差与标签删失）→ 误报概率 →（预算约束）→ 调查优先级 →（检测努力对照下）→ 根除判定。模型构造的成功标准：五问中的每一问都能指认到本框架中的具体变量或方程，且所有不确定性显式传播。

## 2 基本假设

| 编号 | 假设陈述 | 合理性说明 |
|:---:|---|---|
| A1 | Lab Status $\in$ {Positive, Negative} 为金标准标签；Unprocessed/Unverified 为删失观测（非随机缺失，倾向新近报告），训练仅用金标准但删失比例进入偏差敏感性 | 官方分类可靠；删失机制显式建模而非简单剔除 |
| A2 | 公众报告强度 $\lambda_{\text{report}}(t) = \kappa \cdot A(t) \cdot e(t)$：与丰度 $A$ 和公众注意力 $e(t)$（媒体报道驱动的季节性）成正比 | 报告率 $\neq$ 丰度是本题首要混杂，需在观测层显式建模 |
| A3 | 目击空间坐标经州政府地址转换，误差为各向同性小噪声 | 数据说明，空间坐标误差可忽略 |
| A4 | 调查预算 $B$ 为每期硬约束；检测努力（监测强度）在根除判定期不下降 | 题面 limited resources + 根除判定的前提条件 |

## 3 符号说明

### 3.1 变量

| 符号 | 名称 | 描述 | 单位 | 定义域 | 角色 |
|:---:|---|---|---|---|---|
| $\text{feat}$ | 报告特征向量 | 经纬度、月份、年、报告滞后 $\Delta$ = Submission − Detection、是否附图、文本 TF-IDF | 1 | 混合类型 | 输入 |
| $y$ | 金标准标签 | Positive=1 / Negative=0（仅金标准子集有定义） | 1 | $\{0,1\}$ | 输入 |
| $\hat{p}$ | 真阳性概率 | 纠正报告偏差后的后验概率 | 1 | $[0,1]$ | 导出 |
| $S$ | 调查队列 | 当期选送实验室的报告集合 | set | $|S| \leq B$ | 决策 |
| $A_t$ | 隐丰度场 | 时空格点上的丰度强度（潜变量） | count | $\geq 0$ | 状态 |
| $D_t$ | 累计检测努力 | 累积调查/监测工时（根除判定的对照变量） | hr | 单调递增 | 状态 |

### 3.2 参数

| 符号 | 名称 | 值或来源 | 单位 | 来源类型 |
|:---:|---|---|---|---|
| $B$ | 调查预算 | 每期可送检数量（情景设定） | count/期 | assumed |
| $w_{\text{pos}}$ | 类别权重 | $n_{\text{neg}}/n_{\text{pos}}$ 的平方根 | 1 | data |
| $\kappa$ | 报告偏差系数区间 | 媒体报道强度文献代理，$[0.5, 2]$ | 1 | literature |
| $(k, \alpha)$ | 根除判定参数 | $k=3$ 年、$\alpha=0.05$ | 1 | assumed |
| $\theta$ | 分类器超参数 | 分层 5 折交叉验证网格最优 | 1 | calibrated |
| 带宽 | 时空核带宽 | k-距离/Scott 规则 | km | calibrated |

## 4 模型建立

### 4.1 目标函数与估计量

**Q1 扩散可预测性**：

$$
O_1: \quad \text{可预测性} = \text{前滚验证下 } \hat{S}_t \text{（时空密度前沿）与实测的 CRPS} + \text{扩散速度估计的 CI}
$$

采用连续排序概率评分（CRPS）评估概率预测质量，而非单点误差。

**Q2 误报模型**：

$$
O_2: \quad \max \; \text{PR-AUC（主指标）} + \text{Brier（校准）}
$$

极不平衡下 PR-AUC 为主指标，Brier 分数衡量概率校准质量。

**Q3 调查优先级**：

$$
O_3: \quad \max \; \sum_{i \in S} \hat{p}_i, \quad |S| \leq B
$$

期望阳性发现最大化，空间分散作为 tie-break。

**Q4 模型更新**：

$$
O_4: \quad \min \; \text{argmin（漂移风险, 实验室吞吐成本）}
$$

更新频率作为漂移风险与实验室吞吐成本的权衡优化。

**Q5 根除判定**：

$$
O_5: \quad \mathbb{P}(\lambda_{\text{true}} < \lambda_{\text{thresh}} \mid D_t \text{ 不降, 连续 } k=3 \text{ 年零阳性}) \geq 1 - \alpha
$$

根除是"检测努力对照下"的统计判定。

### 4.2 约束条件

| 编号 | 表达式 | 物理/工程解释 |
|:---:|---|---|
| C1 | $\hat{p} \in [0,1]$（校准输出经 Platt/isotonic 校准） | 概率量且需校准才可作决策权重 |
| C2 | $|S| \leq B$，$S \subseteq$ 未审报告集 | 预算硬约束 |
| C3a | 训练集仅 Lab Status $\in$ {Positive, Negative} | 标签可得性约束 |
| C3b | 时间前滚切分（训练期 < 验证期） | 防时间泄漏 |
| C4 | $A_t \geq 0$（用对数高斯过程/泊松自回归保证非负） | 丰度非负，随机实现不得违反变量域 |
| C5 | 根除判定前提：$D_t$ 在判定窗口内单调不降 | 无检测努力对照的零阳性不构成证据 |

### 4.3 机理方程

**M1 报告观测模型（偏差纠正）**：

$$
\text{reports}_t \sim \text{Poisson}(\kappa \cdot e(t) \cdot A_t); \quad \log A_t = x_t
$$

其中 $x_t$ 为时空高斯过程，对数链接保证 $A_t \geq 0$。报告偏差系数 $\kappa$ 与公众注意力函数 $e(t)$ 将"报告率 $\neq$ 丰度"做成显式观测层。

**M2 时空扩散（可预测性）**：

$$
\log A_{t+1}(x) = \rho \cdot \log A_t(x) + v \cdot \nabla_x \log A_t + w_t
$$

平流-扩散核描述丰度场的时空演化。扩散速度 $v$ 与方向可估计并给出置信区间，为 Q1 的"精度"提供落点。

**M3 误报分类（删失感知）**：

$$
\hat{p} = \mathbb{P}(y=1 \mid \text{feat}) = \sigma(f_\theta(\text{feat}))
$$

训练于金标准子集，类别加权 $w_{\text{pos}}$。SHAP 输出特征重要性；Platt 校准确保输出满足约束 C1。

**M4 优先级决策**：

$$
S^* = \arg\max_{|S| \leq B} \sum_{i \in S} \hat{p}_i - \lambda_{\text{disp}} \sum_{i,j \in S} K_{\text{spatial}}(i,j)
$$

空间分散惩罚项 tie-break 防扎堆；贪心最优性由次模性近似保证。

**M5 根除判定（努力对照）**：

$$
\mathbb{P}(\lambda_{\text{true}} \leq \lambda^* \mid \text{reports}=0, D_t) = 1 - e^{-\lambda^* D_{t,\text{eff}}}
$$

连续 $k$ 年零阳性且上界 $< \lambda^*$ 判定成立。零阳性只有在检测努力对照下才是证据——$D_{t,\text{eff}}$ 进入判定。

**M6 更新机制（双轨触发）**：

$$
\text{每周增量更新}; \quad \text{PSI}(\text{feat 分布}) > 0.2 \text{ 或 PR-AUC 降幅} > 0.05 \rightarrow \text{全量重训}
$$

更新频率 = 吞吐成本与漂移风险的显式权衡。

### 4.4 模型选择理由

| 候选模型 | 优点 | 缺点 | 选择状态 |
|---|---|---|---|
| 泊松观测层 + 平流-扩散丰度场 + 删失感知分类（本框架） | 五问同源、偏差显式、判据含努力对照 | 潜变量推断实现成本高 | **选中** |
| XGBoost 时空 + 随机森林分类（轻量替代） | 工程简单 | 报告偏差只能情景化、根除判定缺努力对照 | 未选 |
| 图像 CNN 辅助 | 图像误报信号 | 仅部分记录附图且标注成本高，列为扩展 | 未选 |

选择候选 1 的理由：五问同源一根证据链；报告偏差与检测努力两个混杂被显式建模而非讨论；每个对齐点有承载方程。

## 5 求解方法

### 5.1 扩散预测求解（Q1）

1. 构建时空格点，将目击报告聚合到格点单元。
2. 设定泊松观测模型 $\text{reports}_t \sim \text{Poisson}(\kappa \cdot e(t) \cdot A_t)$。
3. 利用对数高斯过程或泊松自回归推断隐丰度场 $A_t$。
4. 拟合平流-扩散核参数 $(\rho, v)$，外推下一时段丰度场。
5. 前滚验证：留出最近一年数据，计算 CRPS 与扩散速度 CI。

### 5.2 误报分类求解（Q2）

1. 以 Lab Status 为标签，构建金标准训练集。
2. 提取特征向量 $\text{feat}$（经纬度、月份、年、报告滞后、是否附图、文本 TF-IDF）。
3. 训练删失感知分类器，启用类别加权 $w_{\text{pos}} = \sqrt{n_{\text{neg}}/n_{\text{pos}}}$。
4. Platt/isotonic 校准输出概率至 $[0,1]$。
5. SHAP 分析特征重要性。
6. 交叉验证选择超参数 $\theta$，输出每条报告的 $\hat{p}$。

### 5.3 预算排序求解（Q3）

1. 对所有未审报告计算校准后的 $\hat{p}$。
2. 按 $\hat{p}$ 降序排列。
3. 加入空间分散惩罚项，贪心选取前 $B$ 条组成 $S^*$。
4. 次模性近似保证贪心解接近最优。

### 5.4 更新频率求解（Q4）

1. 监控特征分布漂移指标 PSI。
2. 每周增量更新模型参数。
3. 当 PSI $> 0.2$ 或 PR-AUC 降幅 $> 0.05$ 时触发全量重训练。
4. 在漂移风险与实验室吞吐成本之间寻找最优更新频率。

### 5.5 根除判定求解（Q5）

1. 统计连续 $k$ 年的阳性发现数与累计检测努力 $D_t$。
2. 利用 Poisson 后验计算 $\mathbb{P}(\lambda_{\text{true}} \leq \lambda^* \mid \text{reports}=0, D_t)$。
3. 要求后验概率 $\geq 1 - \alpha$ 且 $D_t$ 在判定窗口内单调不降。
4. 功效分析给出所需的最小监测强度。

### 5.6 灵敏度分析计划

| 参数 | 变化范围 | 评估指标 |
|---|---|---|
| 报告偏差 $\kappa$ | $[0.5, 2]$（情景） | 丰度场 CRPS、扩散速度 CI 宽度 |
| 删失比例 | 实际值 $\pm 50\%$ | PR-AUC 下界 |
| 分类阈值 / 预算 $B$ | 阈值 $0.3 \sim 0.7 \times B \; 50 \sim 500$ 网格 | 期望阳性发现数曲线 |
| 判定参数 $(k, \alpha)$ | $k \in \{2,3,4\}$, $\alpha \in \{0.01, 0.05\}$ | 所需监测强度 $D_{t,\text{eff}}$ |
| 时空核带宽 | Scott 规则 $\pm 50\%$ | 前沿稳定性 |

对每个参数在给定范围内扫描，固定其余参数于基准值，观察各指标变化趋势，识别对模型性能影响最大的参数并评估模型稳健性。


## 论文 Y

# 建模论文

## 1 问题重述

本题围绕 4440 条亚洲大黄蜂公众目击报告，构建以监督分类（误报概率）为核心、时空扩散预测为背景、预算约束排序为决策出口的一体化框架，回答以下五个子问题：

1. **扩散可否预测**：利用时空特征预测未来大黄蜂扩散范围与强度，评估预测精度。
2. **误报概率**：训练分类器区分真实目击与误报，输出每条报告的阳性概率。
3. **调查优先级**：在调查预算约束下，最大化期望阳性发现数，确定调查队列。
4. **模型更新**：建立模型在线更新机制，应对数据分布漂移。
5. **根除证据**：在监测努力不下降的前提下，判定大黄蜂是否已被根除。

## 2 基本假设

| 编号 | 假设陈述 | 合理性说明 |
|:---:|---|---|
| A1 | Lab Status 为金标准标签，Unprocessed/Unverified 剔除 | 官方分类可靠，未经验证的记录不纳入训练 |
| A2 | 报告时空特征携带可学习信号（报告行为与真实分布相关） | 分类可行的前提，公众报告行为与大黄蜂真实分布存在统计关联 |
| A3 | 调查预算 $B$ 为硬约束 | 题面限定 limited resources，调查资源存在上限 |

## 3 符号说明

### 3.1 变量

| 符号 | 名称 | 描述 | 单位 | 定义域 | 角色 |
|:---:|---|---|---|---|---|
| $\text{feat}$ | 报告特征向量 | 经纬度、月份、年度、滞后天数、是否附图、文本 TF-IDF | 1 | 混合 | 输入 |
| $y$ | 标签 | Lab Status 二值化（Positive=1） | 1 | $\{0,1\}$ | 输入 |
| $\hat{p}$ | 阳性概率 | 分类器输出 | 1 | $[0,1]$ | 导出 |
| $S$ | 选中的调查集合 | 预算内报告子集 | set | $|S| \leq B$ | 决策 |
| $c_t$ | 年度阳性计数 | 扩散序列 | count | $\geq 0$ | 状态 |

### 3.2 参数

| 符号 | 名称 | 值或来源 | 单位 | 来源类型 |
|:---:|---|---|---|---|
| $B$ | 调查预算 | 情景设定 | count | assumed |
| $w_{\text{pos}}$ | 类别权重 | 按类频率反比 | 1 | data |
| $\varepsilon$ | DBSCAN 邻域 | k-距离图肘点 | km | calibrated |
| $k$ | 根除阈值 | 情景设定 3 年 | yr | assumed |
| $\theta$ | XGBoost 超参 | 交叉验证网格 | 1 | calibrated |

## 4 模型建立

### 4.1 目标函数与估计量

**Q1 扩散预测**：最小化扩散外推误差。

$$
O_1: \quad \min \; \mathbb{E}\left[|c_t - \hat{c}_t|\right]
$$

其中 $c_t$ 为实际年度阳性计数，$\hat{c}_t$ 为模型预测值。

**Q2 误报分类**：最大化分类性能。

$$
O_2: \quad \max \; \text{AUC-ROC} \; / \; \text{PR-AUC}
$$

以 PR-AUC 为主指标（类别不平衡场景），AUC-ROC 为辅助指标。

**Q3 优先级排序**：最大化预算内期望阳性发现。

$$
O_3: \quad \max \; \mathbb{E}\left[\sum_{i \in S} y_i\right]
$$

**Q5 根除判定**：根除判据为统计检验。

$$
O_4: \quad \text{根除判定} = \mathbb{P}(\text{阳性率} < \text{阈值} \mid \text{监测努力}) > 0.95 \text{ 连续 3 年}
$$

### 4.2 约束条件

| 编号 | 表达式 | 物理/工程解释 |
|:---:|---|---|
| C1 | $0 \leq \hat{p} \leq 1$ | 阳性概率为概率量，须落在 $[0,1]$ 区间 |
| C2 | $|S| \leq B$ 且 $S \subseteq$ 待审报告集 | 调查资源硬约束，选中集合不得超出预算 |
| C3 | 训练集仅含 Lab Status $\in$ {Positive, Negative} | 标签可得性约束，Unprocessed/Unverified 剔除 |

### 4.3 机理方程

**M1 时空扩散预测**：采用 XGBoost + DBSCAN 组合模型。

$$
\hat{c}_{t+1} = \text{XGBoost}(\text{feat}_{\leq t}) + \text{DBSCAN 加权重心外推}
$$

利用历史特征训练 XGBoost 模型预测未来扩散，同时通过 DBSCAN 聚类识别空间聚集区域，用加权重心外推空间前沿。采用留一年验证防数据泄漏。

**M2 误报分类**：采用随机森林 + 类别加权。

$$
\hat{p} = \mathbb{P}(y=1 \mid \text{feat})
$$

以类别不平衡场景下的 PR-AUC 为主指标，通过类别加权处理正负样本比例失衡。

**M3 预算排序**：贪心最优排序。

$$
S^* = \arg\max_{|S| \leq B} \sum p_{\hat{i}}, \quad \text{空间覆盖 tie-break}
$$

按阳性概率降序选取，当概率相同时以空间覆盖作为平局打破准则，确保调查队列的空间多样性。

**M4 更新机制**：双轨触发更新。

$$
\text{周级增量再训练} + \text{PSI} > 0.2 \text{ 触发全量重训}
$$

每周进行增量更新以适应新数据；当特征分布漂移指标 PSI 超过 0.2 时，触发全量重训练。

**M5 根除证据**：零阳性 + 努力对照。

$$
\text{零阳性 } k=3 \text{ 年 且 阳性率 95\% 置信上界} < \text{检出阈值（努力对照）}
$$

采用零膨胀计数模型与功效分析，要求连续 3 年无阳性发现且检测努力不下降。

### 4.4 模型选择理由

| 候选模型 | 优点 | 缺点 | 选择状态 |
|---|---|---|---|
| XGBoost + DBSCAN（时空）+ 随机森林（分类） | 非线性 + 可解释重要性 | 调参成本 | **选中** |
| ARIMA（纯时间）+ Logistic | 简单 | 丢失空间结构 | 未选 |
| 图像 CNN 辅助分类 | 图像信号 | 仅 5% 记录附图，标注成本高 | 未选（扩展） |

选择 XGBoost + DBSCAN 时空扩散 + 随机森林误报分类 + 预算贪心排序 + 触发式更新的组合框架，理由为：多因素非线性时空扩散需树模型 + 聚类；类别极不平衡决定以 PR-AUC 为主指标与类别加权；预算排序的期望效益目标使 $\hat{p}$ 排序成为可证明的贪心最优；图像仅覆盖少数记录，首轮不引入 CNN。

## 5 求解方法

### 5.1 扩散预测求解

1. 从数据中提取各年度阳性计数 $c_t$ 与时空特征 $\text{feat}$。
2. 训练 XGBoost 回归模型，输入历史特征，输出下一年度阳性计数预测。
3. 利用 DBSCAN 对空间坐标聚类，计算各簇加权重心，外推空间扩散前沿。
4. 留出最近一年数据作为验证集，评估预测精度。

### 5.2 误报分类求解

1. 以 Lab Status 为标签，将 Positive 标为 1，Negative 标为 0。
2. 构建特征向量 $\text{feat}$（经纬度、月份、年度、滞后天数、是否附图、文本 TF-IDF）。
3. 训练随机森林分类器，启用类别加权 $w_{\text{pos}}$。
4. 交叉验证选择超参数，输出每条报告的 $\hat{p}$。

### 5.3 预算排序求解

1. 对所有待审报告计算 $\hat{p}$。
2. 按 $\hat{p}$ 降序排列。
3. 取前 $B$ 条报告组成调查队列 $S^*$；当概率相同时以空间距离最大化作为 tie-break。

### 5.4 灵敏度分析计划

| 参数 | 变化范围 | 评估指标 |
|---|---|---|
| 分类阈值 | $0.3 \sim 0.7$ | 查全率 @ 预算 $B$ |
| 预算 $B$ | $50 \sim 500$ | 期望阳性发现数曲线 |
| 类别权重 $w_{\text{pos}}$ | $\sqrt{\text{ratio}}$ 至 $\text{ratio}$ | PR-AUC |
| DBSCAN $\varepsilon$ | k-距离肘点 $\pm 50\%$ | 簇数/前沿稳定性 |
| 报告率放大系数 | $0.5\times \sim 2\times$ | 扩散速度估计 |

逐参数扫描，固定其余参数于基准值，观察各指标变化趋势，识别对模型性能影响最大的参数。


## 论文 Z

# 建模论文

## 1 问题重述

本题围绕 4440 条亚洲大黄蜂公众目击报告，要求回答以下五个子问题：

1. **扩散可否预测**：利用年度阳性目击数时间序列，拟合增长趋势并外推，评估扩散预测的可行性。
2. **误报概率**：对每条报告估计其为误判的概率，量化分类器输出的误报概率。
3. **调查优先级**：在调查资源有限的条件下，按误报概率降序排列，确定调查队列的优先顺序。
4. **模型更新**：在新数据到达时如何更新模型参数（该子问题的模型待补充）。
5. **根除证据**：判断亚洲大黄蜂是否已被根除（该子问题的模型待补充）。

## 2 基本假设

| 编号 | 假设陈述 | 合理性说明 |
|:---:|---|---|
| A1 | Positive ID 的目击记录代表真实大黄蜂活动 | 官方实验室分类为金标准，Positive ID 记录经专业鉴定，可认为真实存在大黄蜂活动 |
| A2 | 目击报告率与实际种群规模成正比 | 公众报告量可作为种群丰度的代理指标，报告量增加反映大黄蜂出现频率上升 |

## 3 符号说明

| 符号 | 名称 | 描述 | 单位 | 定义域 |
|:---:|---|---|---|---|
| $N_{\text{pos}}$ | 年度阳性目击数 | 每年 Positive ID 记录数 | count/yr | $\geq 0$ 整数 |
| $\text{lon}$ | 目击经度 | 报告地点经度 | deg | 华盛顿州范围 |
| $\text{lat}$ | 目击纬度 | 报告地点纬度 | deg | 华盛顿州范围 |
| $t$ | 报告时间 | Detection Date | date | 2019–2021 |
| $\hat{p}$ | 误报概率 | 报告为误判的概率 | 1 | $[0,1]$ |
| $r$ | 扩散速率 | 由年度阳性数拟合 | 1/yr | — |

## 4 模型建立

### 4.1 目标函数与估计量

**Q1 扩散预测**：拟合 $N_{\text{pos}}(t)$ 增长曲线并外推。

$$
O_1: \quad \text{拟合 } N_{\text{pos}}(t) \text{ 增长曲线并外推}
$$

采用指数增长模型作为拟合目标：

$$
N_{\text{pos}}(t+1) = N_{\text{pos}}(t) \cdot e^{r}
$$

其中 $r$ 为扩散速率参数，由年度阳性数据拟合得到。

**Q2/Q3 误报分类与优先级排序**：训练分类器输出 $\hat{p}$ 并按其排序调查队列。

$$
O_2: \quad \text{训练分类器输出 } \hat{p} \text{ 并按其排序调查队列}
$$

### 4.2 约束条件

| 编号 | 表达式 | 物理/工程解释 |
|:---:|---|---|
| C1 | $0 \leq \hat{p} \leq 1$ | 误报概率为概率量，必须落在 $[0,1]$ 区间内 |

### 4.3 机理方程

**M1 种群扩散**：采用指数拟合模型（备选 Logistic 模型）。

$$
N_{\text{pos}}(t+1) = N_{\text{pos}}(t) \cdot e^{r}
$$

该方程描述种群数量在相邻时间步之间的指数增长关系。指数模型假设种群增长率恒定，适用于种群建立初期资源充足的场景。备选的 Logistic 模型可刻画环境容纳量限制，但本模型以指数拟合为主。

**M2 误报分类**：采用 Logistic 回归模型。

$$
\hat{p} = \text{LogisticRegression}(\text{lat}, \text{lon}, \text{month})
$$

以 Lab Status 为标签，输入目击报告的经纬度和月份特征，输出报告为误判的概率。

**M3 优先级排序**：按误报概率降序排列。

$$
\text{priority} = \hat{p} \text{（降序）}
$$

概率排序即为调查优先级，$\hat{p}$ 越高的报告越优先安排调查。

### 4.4 模型选择理由

| 候选模型 | 优点 | 缺点 | 选择状态 |
|---|---|---|---|
| 指数/Logistic 扩散拟合 | 简单 | 未考虑空间异质性 | **选中** |
| Logistic 回归误报分类 | 可解释 | 线性决策面 | **选中** |

选择指数扩散 + Logistic 回归 + 概率排序的组合模型，理由为：数据量小、特征少，简单模型优先。在数据有限的条件下，复杂模型容易过拟合，简单模型具有更好的泛化能力和可解释性。

## 5 求解方法

### 5.1 扩散预测求解

1. 从数据中提取每年的 $N_{\text{pos}}$ 时间序列。
2. 对 $\ln N_{\text{pos}}(t)$ 进行线性回归，拟合扩散速率 $r$：
   $$
   \ln N_{\text{pos}}(t) = \ln N_{\text{pos}}(0) + r \cdot t
   $$
3. 利用拟合的 $r$ 外推未来年份的 $N_{\text{pos}}$ 值。

### 5.2 误报分类求解

1. 以 Lab Status 为标签，将 Positive 记录标为 1，Negative 记录标为 0。
2. 提取经纬度和月份特征，构建特征矩阵。
3. 训练 Logistic 回归模型，输出每条报告的 $\hat{p}$。
4. 按 $\hat{p}$ 降序排列，得到调查优先级队列。

### 5.3 灵敏度分析计划

| 参数 | 变化范围 | 评估指标 |
|---|---|---|
| 扩散速率 $r$ | $\pm 20\%$ | 外推 $N_{\text{pos}}$ |
| 分类阈值 | $0.3 \sim 0.7$ | 查全率/查准率 |

对扩散速率 $r$ 在 $\pm 20\%$ 范围内扰动，观察外推结果的变化幅度；对分类阈值在 $0.3$ 至 $0.7$ 之间扫描，绘制查全率-查准率曲线，评估分类器在不同阈值下的性能。


## 匿名建模产物（仅供参考）


### 产物 X

```json
{
  "problem_id": "2021_C",
  "problem_interpretation": "五问共享一条证据链：报告流 →（纠正报告偏差与标签删失）→ 误报概率 →（预算约束）→ 调查优先级 →（检测努力对照下）→ 根除判定。模型构造的成功标准：五问中的每一问都能指认到本框架中的具体变量/方程（对齐点→变量承载），且所有不确定性显式传播。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "Lab Status ∈ {Positive, Negative} 为金标准标签；Unprocessed/Unverified 为删失观测（非随机缺失，倾向新近报告），训练仅用金标准但删失比例进入偏差敏感性",
      "justification": "官方分类 + 删失机制显式建模"
    },
    {
      "id": "A2",
      "statement": "公众报告强度 λ_report(t) = κ·A(t)·e(t)：与丰度 A 和公众注意力 e(t)（媒体报道驱动的季节性）成正比——报告率≠丰度是本题首要混杂",
      "justification": "报告行为偏差的结构化表述"
    },
    {
      "id": "A3",
      "statement": "目击空间坐标经州政府地址转换，误差为各向同性小噪声",
      "justification": "数据说明"
    },
    {
      "id": "A4",
      "statement": "调查预算 B 为每期硬约束；检测努力（监测强度）在根除判定期不下降",
      "justification": "题面 limited resources + 根除判定的前提"
    }
  ],
  "variables": [
    {
      "id": "feat",
      "name": "报告特征向量",
      "description": "经纬度、月份、年、报告滞后 Δ=Submission−Detection、是否附图、文本 TF-IDF",
      "unit": "1",
      "role": "input",
      "domain": "混合类型"
    },
    {
      "id": "y",
      "name": "金标准标签",
      "description": "Positive=1 / Negative=0（仅金标准子集有定义）",
      "unit": "1",
      "role": "input",
      "domain": "{0,1}"
    },
    {
      "id": "p_hat",
      "name": "真阳性概率",
      "description": "纠正报告偏差后的后验概率",
      "unit": "1",
      "role": "derived",
      "domain": "[0,1]"
    },
    {
      "id": "S",
      "name": "调查队列",
      "description": "当期选送实验室的报告集合",
      "unit": "set",
      "role": "decision",
      "domain": "|S| ≤ B"
    },
    {
      "id": "A_t",
      "name": "隐丰度场",
      "description": "时空格点上的丰度强度（潜变量）",
      "unit": "count",
      "role": "state",
      "domain": "≥0"
    },
    {
      "id": "D_t",
      "name": "累计检测努力",
      "description": "累积调查/监测工时（根除判定的对照变量）",
      "unit": "hr",
      "role": "state",
      "domain": "单调递增"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "调查预算 B",
      "value_or_source": "每期可送检数量（情景设定）",
      "unit": "count/期",
      "source": "assumed"
    },
    {
      "id": "p2",
      "name": "类别权重 w_pos",
      "value_or_source": "n_neg/n_pos 的平方根（不平衡折中）",
      "unit": "1",
      "source": "data"
    },
    {
      "id": "p3",
      "name": "报告偏差系数 κ 区间",
      "value_or_source": "媒体报道强度文献代理，[0.5, 2] 情景",
      "unit": "1",
      "source": "literature"
    },
    {
      "id": "p4",
      "name": "根除判定参数 (k, α)",
      "value_or_source": "k=3 年、α=0.05（功效分析给出）",
      "unit": "1",
      "source": "assumed"
    },
    {
      "id": "p5",
      "name": "分类器超参数 θ",
      "value_or_source": "分层 5 折交叉验证网格最优",
      "unit": "1",
      "source": "calibrated"
    },
    {
      "id": "p6",
      "name": "时空核带宽",
      "value_or_source": "k-距离/规则带宽（Scott）",
      "unit": "km",
      "source": "calibrated"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "p_hat ∈ [0,1]（校准输出经 Platt/isotonic 校准）",
      "rationale": "概率量且需校准才可作决策权重"
    },
    {
      "id": "C2",
      "expression": "|S| ≤ B，S ⊆ 未审报告集",
      "rationale": "预算硬约束"
    },
    {
      "id": "C3",
      "expression": "训练集 C3a：仅 Lab Status ∈ {Positive,Negative}；C3b：时间前滚切分（训练期 < 验证期）",
      "rationale": "标签可得性 + 防时间泄漏"
    },
    {
      "id": "C4",
      "expression": "A_t ≥ 0（用对数高斯过程/泊松自回归保证非负）",
      "rationale": "丰度非负——随机实现不得违反变量域"
    },
    {
      "id": "C5",
      "expression": "根除判定前提：D_t 在判定窗口内单调不降",
      "rationale": "无检测努力对照的零阳性不构成证据"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "Q1 可预测性 = 前滚验证下 Ŝ_t（时空密度前沿）与实测的 CRPS + 扩散速度估计的 CI",
      "kind": "estimand",
      "rationale": "Q1 要求'可否预测及精度'——用 CRPS 而非单点误差"
    },
    {
      "id": "O2",
      "expression": "Q2 误报模型 = max PR-AUC（主指标）+ Brier（校准）",
      "kind": "maximize",
      "rationale": "极不平衡下 PR-AUC 为主、概率校准为排序的前提"
    },
    {
      "id": "O3",
      "expression": "Q3 优先级 = argmax_{|S|≤B} Σ_{i∈S} p_hat_i，空间分散 tie-break",
      "kind": "maximize",
      "rationale": "期望阳性发现最大化"
    },
    {
      "id": "O4",
      "expression": "Q4 更新 = 增量后验更新频率 argmin（漂移风险, 实验室吞吐成本）",
      "kind": "minimize",
      "rationale": "Q4 更新频率作为权衡而非拍定"
    },
    {
      "id": "O5",
      "expression": "Q5 根除 = P(λ_true < λ_thresh | D_t 不降, 连续 k=3 年零阳性) ≥ 1−α",
      "kind": "estimand",
      "rationale": "根除是'检测努力对照下'的统计判定"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "报告观测模型（偏差纠正）",
      "equation": "reports_t ~ Poisson(κ·e(t)·A_t)；log A_t = x_t（时空高斯过程，非负由对数链接保证）",
      "derivation_notes": "干预②③：κ 与 e(t) 把'报告率≠丰度'做成显式观测层；对数链接满足 C4"
    },
    {
      "id": "M2",
      "name": "时空扩散（可预测性）",
      "equation": "log A_{t+1}(x) = ρ·log A_t(x) + v·∇_x log A_t + w_t（平流-扩散核）",
      "derivation_notes": "扩散速度 v 与方向可估计并给 CI（Q1 的'精度'落点）"
    },
    {
      "id": "M3",
      "name": "误报分类（删失感知）",
      "equation": "p_hat = P(y=1|feat) = σ(f_θ(feat))，训练于金标准子集，类别加权 w_pos",
      "derivation_notes": "SHAP 输出特征重要性；Platt 校准到 C1"
    },
    {
      "id": "M4",
      "name": "优先级决策",
      "equation": "S* = argmax_{|S|≤B} Σ_{i∈S} p_hat_i − λ_disp·Σ_{i,j∈S} K_spatial(i,j)",
      "derivation_notes": "空间分散惩罚项 tie-break 防扎堆；贪心最优性由次模性近似保证"
    },
    {
      "id": "M5",
      "name": "根除判定（努力对照）",
      "equation": "P(λ_true ≤ λ* | reports=0, D_t) 用 Poisson 后验：1−e^{−λ*D_t_eff}；连续 k 年零阳性且上界 < λ* 判定成立",
      "derivation_notes": "干预②③：零阳性只有在检测努力对照下才是证据——D_t_eff 进入判定"
    },
    {
      "id": "M6",
      "name": "更新机制（双轨触发）",
      "equation": "每周增量更新；PSI(feat 分布) > 0.2 或 PR-AUC 降幅 > 0.05 → 全量重训",
      "derivation_notes": "更新频率 = 吞吐成本与漂移风险的显式权衡（O4）"
    }
  ],
  "candidate_models": [
    {
      "model": "泊松观测层 + 平流-扩散丰度场 + 删失感知分类（本框架）",
      "pros": "五问同源、偏差显式、判据含努力对照",
      "cons": "潜变量推断实现成本高"
    },
    {
      "model": "XGBoost 时空 + 随机森林分类（轻量替代）",
      "pros": "工程简单",
      "cons": "报告偏差只能情景化、根除判定缺努力对照"
    },
    {
      "model": "图像 CNN 辅助",
      "pros": "图像误报信号",
      "cons": "仅 3305/4440 部分记录附图且标注成本高，列为扩展"
    }
  ],
  "selected_model": "候选1（泊松观测 + 平流-扩散 + 删失感知分类 + 预算决策 + 努力对照根除判定）",
  "selection_reason": "五问同源一根证据链；报告偏差与检测努力两个混杂被显式建模而非讨论；每个对齐点有承载方程",
  "uncertainties": [
    {
      "source": "报告偏差系数 κ 与注意力 e(t)",
      "handling": "propagated",
      "effect": "丰度估计与扩散速度的区间（Q1 精度口径）"
    },
    {
      "source": "标签删失比例",
      "handling": "scenario",
      "effect": "分类器 PR-AUC 的下界敏感性"
    },
    {
      "source": "分类器 θ（交叉验证）",
      "handling": "propagated",
      "effect": "p_hat 的折间分布 → 排序稳健性"
    },
    {
      "source": "扩散参数 (ρ, v, w)",
      "handling": "propagated",
      "effect": "Q1 的 CRPS 与前沿区间"
    },
    {
      "source": "根除判定 (k, α, λ*)",
      "handling": "scenario",
      "effect": "功效分析给出需要的监测强度"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "报告偏差 κ",
      "range": "[0.5, 2]（情景）",
      "metric": "丰度场 CRPS、扩散速度 CI 宽度"
    },
    {
      "parameter": "删失比例",
      "range": "实际值 ±50%",
      "metric": "PR-AUC 下界"
    },
    {
      "parameter": "分类阈值/预算 B",
      "range": "阈值 0.3-0.7 × B 50-500 网格",
      "metric": "期望阳性发现数曲线"
    },
    {
      "parameter": "判定参数 (k, α)",
      "range": "k∈{2,3,4}, α∈{0.01,0.05}",
      "metric": "所需监测强度 D_t_eff"
    },
    {
      "parameter": "时空核带宽",
      "range": "Scott 规则 ±50%",
      "metric": "前沿稳定性"
    }
  ]
}
```

### 产物 Y

```json
{
  "problem_id": "2021_C",
  "mma_raw_output": {
    "eda": "本题属数据驱动题（4440 条目击报告 + 3305 张图像），EDA 涵盖：① Lab Status 四类（Positive/Negative/Unprocessed/Unverified）的类别分布与不平衡分析；② Detection Date 与 Submission Date 的时间分布（报告滞后分析）；③ 时空散点图（经纬度分布、年度扩散趋势）；④ 图像-记录映射表的覆盖率；⑤ 缺失值（Lab Comments）与异常值（重复报告、坐标出界）处理策略。",
    "ques1": "问题类型判断：预测类（时空预测）。模型选择：XGBoost（特征：经纬度、月份、年度、报告滞后天数）+ 空间聚类（DBSCAN 提取扩散簇），备选 ARIMA（仅时间边缘）与空间 logistic 扩散核；选择理由是扩散受时空与报告行为多因素影响且非线性。建模思路：以年度阳性记录为序列拟合扩散速度与方向（加权重心轨迹），DBSCAN 识别集群扩张前沿。求解方法：滑动窗口外推 2022 年分布。验证策略：留一年交叉验证，MAE/RMSE 与方向误差。可视化：加权重心轨迹图 + 扩散前沿年际对比图。",
    "ques2": "问题类型判断：分类类（有标签）。模型选择：随机森林（特征：经纬度、月份、文本线索 TF-IDF、图像是否提供），备选 XGBoost/SVM；选择理由：类别不平衡（Positive 极少）且需特征重要性解释。建模思路：以 Lab Status ∈ {Positive, Negative} 为标签（剔除 Unprocessed/Unverified），输出误判概率 p_hat。求解方法：SMOTE/类别加权处理不平衡。验证策略：分层 5 折交叉验证，AUC-ROC 与 PR-AUC（不平衡主指标）、SHAP 特征重要性。可视化：PR 曲线 + SHAP 汇总图。",
    "ques3": "问题类型判断：排序/决策类。模型选择：p_hat 期望效益排序 + 资源约束贪心；备选为期望信息增益排序。建模思路：调查预算 B（可查数目上限）下按 p_hat 降序选报告，使期望阳性发现数最大；加入空间覆盖 tie-break 避免扎堆。求解方法：贪心 + 预算约束。验证策略：历史回放——按该规则选出的报告中真实 Positive 占比 vs 随机调查基线。可视化：不同预算下的查全率曲线。",
    "ques4": "问题类型判断：更新机制。模型选择：滚动再训练 + 触发式更新双轨。建模思路：实验室每确认一批新标签即增量更新分类器（周级）；分布漂移监测（PSI>0.2 触发全量重训）。求解方法：增量学习。验证策略：时间前滚验证。可视化：模型 AUC 随更新次数曲线。",
    "ques5": "问题类型判断：统计检验。模型选择：零膨胀计数模型 + 监测努力对照下的假设检验。建模思路：根除证据 = 在监测努力不降的前提下，连续 k 年阳性数为 0 且负二项模型的阳性率上置信界低于检出阈值。求解方法：设定 k=3、显著性 0.05。验证策略：功效分析。可视化：年度阳性计数与阈值带。",
    "sensitivity_analysis": "关键参数：分类阈值（0.3-0.7）、不平衡处理权重、DBSCAN 邻域参数 ε、扩散速度估计、预算 B。评估指标：AUC-ROC/PR-AUC、查全率、期望阳性发现数。可视化：热力图（阈值×预算→查全率）。鲁棒性：时间前滚 + Bootstrap。"
  },
  "problem_interpretation": "以监督分类（误报概率）为核心、时空扩散预测为背景、预算约束排序为决策出口的五问一体化框架。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "Lab Status 为金标准标签，Unprocessed/Unverified 剔除",
      "justification": "官方分类"
    },
    {
      "id": "A2",
      "statement": "报告时空特征携带可学习信号（报告行为与真实分布相关）",
      "justification": "分类可行的前提"
    },
    {
      "id": "A3",
      "statement": "调查预算 B 为硬约束",
      "justification": "题面 limited resources"
    }
  ],
  "variables": [
    {
      "id": "feat",
      "name": "报告特征向量",
      "description": "经纬度、月份、年度、滞后天数、是否附图、文本 TF-IDF",
      "unit": "1",
      "role": "input",
      "domain": "混合"
    },
    {
      "id": "y",
      "name": "标签",
      "description": "Lab Status 二值化（Positive=1）",
      "unit": "1",
      "role": "input",
      "domain": "{0,1}"
    },
    {
      "id": "p_hat",
      "name": "阳性概率",
      "description": "分类器输出",
      "unit": "1",
      "role": "derived",
      "domain": "[0,1]"
    },
    {
      "id": "S",
      "name": "选中的调查集合",
      "description": "预算内报告子集",
      "unit": "set",
      "role": "decision",
      "domain": "|S| ≤ B"
    },
    {
      "id": "c_t",
      "name": "年度阳性计数",
      "description": "扩散序列",
      "unit": "count",
      "role": "state",
      "domain": "≥0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "调查预算 B",
      "value_or_source": "题面 limited resources，情景设定",
      "unit": "count",
      "source": "assumed"
    },
    {
      "id": "p2",
      "name": "类别权重 w_pos",
      "value_or_source": "按类频率反比",
      "unit": "1",
      "source": "data"
    },
    {
      "id": "p3",
      "name": "DBSCAN 邻域 ε",
      "value_or_source": "k-距离图肘点",
      "unit": "km",
      "source": "calibrated"
    },
    {
      "id": "p4",
      "name": "根除阈值 k 年",
      "value_or_source": "情景设定 3 年",
      "unit": "yr",
      "source": "assumed"
    },
    {
      "id": "p5",
      "name": "XGBoost 超参",
      "value_or_source": "交叉验证网格",
      "unit": "1",
      "source": "calibrated"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "0 ≤ p_hat ≤ 1",
      "rationale": "概率量"
    },
    {
      "id": "C2",
      "expression": "|S| ≤ B 且 S ⊆ 待审报告集",
      "rationale": "调查资源硬约束"
    },
    {
      "id": "C3",
      "expression": "训练集仅含 Lab Status ∈ {Positive, Negative}",
      "rationale": "标签可得性（Unprocessed/Unverified 剔除）"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "min E[|c_t − ĉ_t|]（扩散外推误差）",
      "kind": "minimize",
      "rationale": "Q1"
    },
    {
      "id": "O2",
      "expression": "max AUC-ROC / PR-AUC（误报判别）",
      "kind": "maximize",
      "rationale": "Q2"
    },
    {
      "id": "O3",
      "expression": "max E[Σ_{i∈S} y_i]（预算内期望阳性发现）",
      "kind": "maximize",
      "rationale": "Q3"
    },
    {
      "id": "O4",
      "expression": "根除判定 = P(阳性率 < 阈值 | 监测努力) > 0.95 连续 3 年",
      "kind": "estimand",
      "rationale": "Q5"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "时空扩散预测",
      "equation": "ĉ_{t+1} = XGBoost(feat_{≤t}) + DBSCAN 加权重心外推",
      "derivation_notes": "留一年验证防泄漏"
    },
    {
      "id": "M2",
      "name": "误报分类",
      "equation": "p_hat = P(y=1 | feat)，随机森林 + 类别加权",
      "derivation_notes": "不平衡主指标 PR-AUC"
    },
    {
      "id": "M3",
      "name": "预算排序",
      "equation": "S* = argmax_{|S|≤B} Σ p_hat_i，空间覆盖 tie-break",
      "derivation_notes": "贪心最优性由排序可加性保证"
    },
    {
      "id": "M4",
      "name": "更新机制",
      "equation": "周级增量再训练 + PSI>0.2 触发全量重训",
      "derivation_notes": "双轨触发"
    },
    {
      "id": "M5",
      "name": "根除证据",
      "equation": "零阳性 k=3 年 且 阳性率 95% 置信上界 < 检出阈值（努力对照）",
      "derivation_notes": "零膨胀计数 + 功效分析"
    }
  ],
  "candidate_models": [
    {
      "model": "XGBoost+DBSCAN（时空）+ 随机森林（分类）",
      "pros": "非线性+可解释重要性",
      "cons": "调参成本"
    },
    {
      "model": "ARIMA（纯时间）+ Logistic",
      "pros": "简单",
      "cons": "丢失空间结构"
    },
    {
      "model": "图像 CNN 辅助分类",
      "pros": "图像信号",
      "cons": "3305 张标注成本高、仅 5% 记录附图"
    }
  ],
  "selected_model": "XGBoost+DBSCAN 时空扩散 + 随机森林误报分类 + 预算贪心排序 + 触发式更新",
  "selection_reason": "多因素非线性时空扩散需树模型+聚类；类别极不平衡决定以 PR-AUC 为主指标与类别加权；预算排序的期望效益目标使 p_hat 排序成为可证明的贪心最优；图像仅覆盖少数记录，首轮不引入 CNN",
  "uncertainties": [
    {
      "source": "报告行为偏差（公众报告率≠丰度）",
      "handling": "scenario",
      "effect": "报告率放大系数情景"
    },
    {
      "source": "标签缺失（Unprocessed/Unverified）",
      "handling": "scenario",
      "effect": "删失比例敏感性"
    },
    {
      "source": "分类器超参与不平衡权重",
      "handling": "propagated",
      "effect": "交叉验证分布"
    },
    {
      "source": "扩散外推",
      "handling": "propagated",
      "effect": "Bootstrap 区间"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "分类阈值",
      "range": "0.3-0.7",
      "metric": "查全率@预算 B"
    },
    {
      "parameter": "预算 B",
      "range": "50-500",
      "metric": "期望阳性发现数曲线"
    },
    {
      "parameter": "类别权重 w_pos",
      "range": "√ratio 至 ratio",
      "metric": "PR-AUC"
    },
    {
      "parameter": "DBSCAN ε",
      "range": "k-距离肘点 ±50%",
      "metric": "簇数/前沿稳定性"
    },
    {
      "parameter": "报告率放大系数",
      "range": "0.5×-2×",
      "metric": "扩散速度估计"
    }
  ]
}
```

### 产物 Z

```json
{
  "problem_id": "2021_C",
  "problem_interpretation": "利用 4440 条公众目击报告（含官方实验室分类）回答：扩散可否预测、误报概率、调查优先级、模型更新、根除证据五问。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "Positive ID 的目击记录代表真实大黄蜂活动",
      "justification": "官方分类为金标准"
    },
    {
      "id": "A2",
      "statement": "目击报告率与实际种群规模成正比",
      "justification": "公众报告量代理丰度"
    }
  ],
  "variables": [
    {
      "id": "N_pos",
      "name": "年度阳性目击数",
      "description": "每年 Positive ID 记录数",
      "unit": "count/yr",
      "role": "state",
      "domain": "≥0 整数"
    },
    {
      "id": "lon",
      "name": "目击经度",
      "description": "报告地点",
      "unit": "deg",
      "role": "input",
      "domain": "华盛顿州范围"
    },
    {
      "id": "lat",
      "name": "目击纬度",
      "description": "报告地点",
      "unit": "deg",
      "role": "input",
      "domain": "华盛顿州范围"
    },
    {
      "id": "t",
      "name": "报告时间",
      "description": "Detection Date",
      "unit": "date",
      "role": "input",
      "domain": "2019-2021"
    },
    {
      "id": "p_hat",
      "name": "误报概率",
      "description": "报告为误判的概率",
      "unit": "1",
      "role": "derived",
      "domain": "[0,1]"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "扩散速率",
      "value_or_source": "由年度阳性数拟合",
      "unit": "1/yr",
      "source": "data"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "0 ≤ p_hat ≤ 1",
      "rationale": "概率量"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "拟合 N_pos(t) 增长曲线并外推",
      "kind": "estimand",
      "rationale": "Q1"
    },
    {
      "id": "O2",
      "expression": "训练分类器输出 p_hat 并按其排序调查队列",
      "kind": "maximize",
      "rationale": "Q2/Q3"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "种群扩散",
      "equation": "N_pos(t+1) = N_pos(t)·e^{r}（指数拟合，备选 Logistic）",
      "derivation_notes": "计数直接拟合"
    },
    {
      "id": "M2",
      "name": "误报分类",
      "equation": "p_hat = LogisticRegression(lat, lon, month)",
      "derivation_notes": "以 Lab Status 为标签"
    },
    {
      "id": "M3",
      "name": "优先级排序",
      "equation": "priority = p_hat 降序",
      "derivation_notes": "概率排序即优先级"
    }
  ],
  "candidate_models": [
    {
      "model": "指数/Logistic 扩散拟合",
      "pros": "简单",
      "cons": "未考虑空间异质性"
    },
    {
      "model": "Logistic 回归误报分类",
      "pros": "可解释",
      "cons": "线性决策面"
    }
  ],
  "selected_model": "指数扩散 + Logistic 回归 + 概率排序",
  "selection_reason": "数据量小、特征少，简单模型优先",
  "uncertainties": [
    {
      "source": "Unprocessed/Unverified 记录",
      "handling": "ignored",
      "effect": "仅用已分类样本训练"
    },
    {
      "source": "报告率≠丰度",
      "handling": "qualitative",
      "effect": "讨论局限"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "扩散速率 r",
      "range": "±20%",
      "metric": "外推 N_pos"
    },
    {
      "parameter": "分类阈值",
      "range": "0.3-0.7",
      "metric": "查全/查准"
    }
  ]
}
```