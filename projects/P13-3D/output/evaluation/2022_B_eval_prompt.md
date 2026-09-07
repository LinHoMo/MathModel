# Paper Quality Evaluation — 2022_B (两库水资源)

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

题目 2022_B


## 论文 X

# 建模论文

## 一、问题重述

本题围绕美国科罗拉多河流域 Mead（米德）与 Powell（鲍威尔）两座水库的联合调度展开研究。具体子问题包括：

1. **抽水决策与耗尽时间**：在固定需求和无来水基线情景下，确定最优抽水策略，估算两库耗尽时间及所需补水量。
2. **竞争利益准则**：用水需求与发电需求之间存在竞争，需建立显式、可审计的决策准则（如帕累托前沿），向决策者呈现完整的权衡面。
3. **短缺政策**：当水资源不足以满足全部需求时，制定短缺时的优先级分配规则。
4. **需求增长情景**：在需求增长、可再生能源占比变化、节水措施等情景下，分析系统行为的变化。

本模型将四问统一为一个逐期滚动线性规划（LP）框架。

## 二、假设

基于建模产物，本文采用以下假设：

| 假设编号 | 内容 | 合理性说明 |
|---------|------|-----------|
| A1 | Powell→Mead 单向输水，无逆向 | 工程设定 |
| A2 | 月步长滚动，期内流量均匀 | 离散化近似 |
| A3 | 发电量 $\propto$ 过水流量 $\times$ 水头（水头由水位决定） | 水电常识 |

## 三、符号说明

### 变量

| 符号 | 名称 | 描述 | 单位 | 类型 | 定义域 |
|------|------|------|------|------|--------|
| $M_t$ | Mead 水位（第 $t$ 期） | 状态 | ft | 状态变量 | [死水位, 防洪上限] |
| $P_t$ | Powell 水位（第 $t$ 期） | 状态 | ft | 状态变量 | [死水位, 防洪上限] |
| $x_{P,t}$ | Powell 期抽水量 | 决策 | acre-ft | 决策变量 | $\geq 0$ |
| $x_{M,t}$ | Mead 期抽水量 | 决策 | acre-ft | 决策变量 | $\geq 0$ |
| $\text{short}_t$ | 第 $t$ 期短缺量 | 需求未满足部分 | acre-ft | 派生变量 | $\geq 0$ |

### 参数

| 符号 | 名称 | 取值来源 | 单位 |
|------|------|---------|------|
| $p_1$ | 容量曲线 $V(\cdot)$ | 题目附表插值 | acre-ft |
| $p_2$ | 死水位/发电最低水位 | 工程规范（题面附表） | ft |
| $p_3$ | 需求 $D_w$, $D_e$ | 题面给定（Q1 固定；Q4 情景缩放） | acre-ft/yr |
| $p_4$ | 发电效率系数 | 水电常识值 | 1 |

## 四、模型建立

### 4.1 目标函数

本模型采用**加权和法**处理多目标优化，并通过 $\lambda$ 扫描生成帕累托前沿。

**目标 O1 —— 缺水率与发电量的加权和**：

$$\min \quad \lambda \sum_{t} \text{short}_t - (1-\lambda) \sum_{t} E_t$$

其中 $E_t$ 为第 $t$ 期发电量，$\lambda \in [0,1]$ 为用水-发电权重参数。

**目标 O2 —— 耗尽时间**（估计量）：

$$T_{\text{exhaust}} = \min\{t : M_t \text{ 或 } P_t \text{ 触及死水位}\}$$

**目标 O3 —— 补水量**（估计量）：

$$\Delta W = \sum_{t} \text{需求缺口（无来水情景下维持需求的累积补水量）}$$

### 4.2 约束条件

| 约束编号 | 表达式 | 物理/工程解释 |
|---------|--------|-------------|
| C1 | $V_P(t+1) = V_P(t) - x_{P,t}$；$V_M(t+1) = V_M(t) - x_{M,t} + x_{P,t}$ | 两库水量守恒 |
| C2 | 死水位 $\leq M_t, P_t \leq$ 防洪上限 | 水位安全边界 |
| C3 | $x_{M,t} + x_{P,t} + \text{short}_t = D_w + D_e$（Q3 短缺放开前取 $\text{short}=0$） | 需求平衡 |
| C4 | $x_{P,t} \leq$ 输水管道通过能力 | 工程能力约束 |

### 4.3 机理方程

**M1 —— 水位-库容关系**：水位与水量通过容量曲线线性插值：

$$V(M_t), \quad V(P_t) \quad \text{由附表插值得到}$$

**M2 —— 守恒滚动**：见约束 C1，逐期 LP 更新状态。

**M3 —— 发电量公式**：

$$E_t = \eta \cdot \rho \cdot g \cdot H(M_t) \cdot x_{M,t}$$

其中水头 $H(M_t)$ 由水位决定，水头随水位下降而衰减——这是发电与用水竞争的数学根源。

**M4 —— 需求演化（Q4）**：

$$D_w(t) = D_{w0} \cdot (1+g)^t \cdot (1-c)$$

$$D_e(t) = D_{e0} \cdot (1-\eta_{\text{ren}}(t)) \cdot (1+g_e)^t$$

其中增长率 $g$、节水率 $c$、可再生占比 $\eta_{\text{ren}}$ 为情景参数。

### 4.4 模型选择理由

| 候选模型 | 优点 | 缺点 | 选用情况 |
|---------|------|------|---------|
| 逐期 LP（本模型） | 全局最优 + 帕累托前沿可参数化 | 线性近似蒸发/水头 | **选用** |
| 动态规划 | 非线性水头处理 | 维数灾难 | 未选用 |
| NSGA-II | 非凸前沿 | 无全局最优保证 | 未选用 |

选用逐期 LP 的理由：约束线性；加权和法透明且满足 Q2 "Explicitly state criteria" 的可审计要求；帕累托前沿给决策者完整权衡面。

### 4.5 不确定性处理

| 不确定性来源 | 处理方式 | 影响 |
|-------------|---------|------|
| 蒸发与渗漏 | 情景分析 | 耗尽时间下界修正 |
| 来水（降水） | 情景分析 | Q1 基线为零来水、扩展情景补来水 |
| 需求增长率 $g$ | 传播分析 | Q4 等高线 |
| 可再生占比 $\eta_{\text{ren}}(t)$ | 传播分析 | Q4 发电需水下降 |

## 五、求解方法

本模型采用逐期滚动线性规划求解，具体步骤如下：

**步骤 1：参数初始化**

- 读取容量曲线 $V(\cdot)$（附表插值）
- 设定死水位、防洪上限、需求基线 $D_w$, $D_e$
- 初始化 $M_0$, $P_0$

**步骤 2：建立逐期 LP**

对于每个时期 $t$，求解如下线性规划：

$$\min \quad \lambda \cdot \text{short}_t - (1-\lambda) \cdot E_t$$

$$\text{s.t.} \quad \begin{cases} V_P(t+1) = V_P(t) - x_{P,t} \\ V_M(t+1) = V_M(t) - x_{M,t} + x_{P,t} \\ \text{死水位} \leq M_t, P_t \leq \text{防洪上限} \\ x_{M,t} + x_{P,t} + \text{short}_t = D_w + D_e \\ x_{P,t} \leq \text{输水管道通过能力} \end{cases}$$

**步骤 3：滚动求解**

从 $t=0$ 开始，逐期求解 LP，更新状态 $(M_{t+1}, P_{t+1})$，直到触及死水位或达到规划期末。

**步骤 4：帕累托前沿生成**

对 $\lambda$ 在 $[0, 1]$ 上均匀取值（如 21 个点），对每个 $\lambda$ 重复步骤 2-3，记录缺水总量与总发电量，绘制帕累托前沿。

**步骤 5：敏感性分析**

| 参数 | 扫描范围 | 观测指标 |
|------|---------|---------|
| 需求 $D_w/D_e$ | $\pm 20\%$ | $T_{\text{exhaust}}$ / $\Delta W$ |
| 初始水位 $M_0/P_0$ | $\pm 10\%$ | $T_{\text{exhaust}}$ |
| $\lambda$（用水-发电权重） | $0$-$1$ 扫描 | 帕累托前沿 |
| 可再生占比 $\eta_{\text{ren}}$ | 初始值至 $50\%$ | $D_e$ 下降与 $T_{\text{exhaust}}$ 延长 |


## 论文 Y

# 建模论文

## 一、问题重述

本题围绕科罗拉多河流域 Mead（米德）与 Powell（鲍威尔）两座水库的联合调度展开研究。四问同源于一个两库随机滚动调度框架：

1. **Q1（抽水决策/耗尽时间/补水量）**：在固定需求、零来水基线情景下，确定最优抽水策略，估算两库耗尽时间，计算维持零短缺所需的外部补水量。
2. **Q2（竞争利益准则）**：建立显式、可审计的决策准则，解决用水需求与发电需求之间的竞争。
3. **Q3（短缺政策）**：当水资源不足以满足全部需求时，制定规则化的短缺降级策略。
4. **Q4（需求增长情景）**：在需求增长、可再生能源占比变化、节水措施等情景下，分析系统行为的变化（耗尽时间曲面与短缺频率）。

成功标准：四问各自能指认到框架中的决策变量、约束或目标；所有工程边界（死水位、输水能力、蒸发）显式入模。

## 二、假设

基于建模产物，本文采用以下假设：

| 假设编号 | 内容 | 合理性说明 |
|---------|------|-----------|
| A1 | Powell→Mead 单向输水，通过能力上限 $C_{\text{pipe}}$（工程参数，情景化） | 题面工程设定 + 干预②：能力上限显式入模 |
| A2 | 月步长；月内流量均匀；蒸发为水位与表面积的函数 $E(t) = e_0 \cdot A_{\text{surf}}(M_t, P_t)$（情景开关） | 离散化 + 干预②：蒸发不可静默省略 |
| A3 | 发电量 $E_t = \eta \cdot \rho \cdot g \cdot H(M_t) \cdot q_t$，水头 $H$ 随水位下降而衰减；发电需水量 $D_e$ 为保证电网基荷的过水需求 | 水电工程常识 + 题面 |
| A4 | Q1 基线：零来水、需求固定；不确定性经由来水/需求情景分支进入 | 题面 Q1 显式条件 |

## 三、符号说明

### 变量

| 符号 | 名称 | 描述 | 单位 | 类型 | 定义域 |
|------|------|------|------|------|--------|
| $M_t$ | Mead 水位 | 状态 | ft | 状态变量 | $[M_{\text{dead}}, M_{\text{max}}]$ |
| $P_t$ | Powell 水位 | 状态 | ft | 状态变量 | $[P_{\text{dead}}, P_{\text{max}}]$ |
| $x_{P,t}$ | Powell 抽水量 | 决策 | acre-ft/月 | 决策变量 | $[0, C_{\text{pipe}}]$ |
| $x_{M,t}$ | Mead 抽水量 | 决策 | acre-ft/月 | 决策变量 | $\geq 0$ |
| $s_{w,t}$ | 用水短缺 | 居民/工业/农业合计短缺 | acre-ft/月 | 派生变量 | $\geq 0$ |
| $s_{e,t}$ | 发电短缺 | 发电过水缺口 | acre-ft/月 | 派生变量 | $\geq 0$ |
| $q_t$ | 发电过流量 | 经过水轮机的流量 | acre-ft/月 | 决策变量 | $\geq 0$ |

### 参数

| 符号 | 名称 | 取值来源 | 单位 |
|------|------|---------|------|
| $p_1$ | 容量曲线 $V_M(\cdot)$, $V_P(\cdot)$ | 题面附表分段线性插值 | acre-ft |
| $p_2$ | 死水位 $M_{\text{dead}}$, $P_{\text{dead}}$ 与上限 $M_{\text{max}}$, $P_{\text{max}}$ | 工程规范/题面附表 | ft |
| $p_3$ | 需求基线 $D_{w0}$, $D_{e0}$ 及增长率 $g$、节水率 $c$、可再生占比 $\eta_{\text{ren}}(t)$ | 题面 Q4 情景参数 | 混合 |
| $p_4$ | 蒸发系数 $e_0$ | 湖泊蒸发文献典型值（情景开关） | ft/月 |
| $p_5$ | 输水能力 $C_{\text{pipe}}$ | 工程参数（情景） | acre-ft/月 |
| $p_6$ | 发电效率 $\eta$ 与水电转换系数 | 水电工程典型值 | 1 |
| $p_7$ | 短缺优先级序 | 水法惯例：residential > industrial > agricultural > hydropower | 1 |

## 四、模型建立

### 4.1 目标函数

**目标 O1 —— Q2 竞争利益准则（字典序 + 加权和对照）**：

采用字典序（lexicographic）优化，准则显式、可审计：

$$\text{第一优先级：} \quad \text{residential 全满足}$$

$$\text{第二优先级：} \quad \text{industrial 缺口最小化}$$

$$\text{第三优先级：} \quad \text{agricultural 缺口最小化}$$

$$\text{第四优先级：} \quad \text{在剩余水中最大化发电} \quad \max \sum_t E_t$$

同时提供 $\lambda$ 加权作为字典序的连续化对照并给出帕累托前沿：

$$\min \quad \lambda_1 s_{\text{res},t} + \lambda_2 s_{\text{ind},t} + \lambda_3 s_{\text{agr},t} - (1-\lambda_4) E_t$$

**目标 O2 —— 耗尽时间**（Q1 估计量）：

$$T_{\text{exhaust}} = \min\{t : M_t = M_{\text{dead}} \text{ 或 } P_t = P_{\text{dead}}\}$$

**目标 O3 —— 补水量**（Q1 估计量）：

$$\Delta W(T) = \sum_{t \leq T} (s_{w,t} + s_{e,t}) \text{ 的反解——维持零短缺所需的外部补水量}$$

**目标 O4 —— Q4 情景读数**：

$$T_{\text{exhaust}}(g, c, \eta_{\text{ren}}) \text{ 曲面与短缺频率}$$

### 4.2 约束条件

| 约束编号 | 表达式 | 物理/工程解释 |
|---------|--------|-------------|
| C1 | $V_P(t+1) = V_P(t) - x_{P,t} - E_P(t)$；$V_M(t+1) = V_M(t) + x_{P,t} - x_{M,t} - E_M(t)$ | 两库水量守恒（蒸发显式入模，可关） |
| C2 | $M_{\text{dead}} \leq M_t \leq M_{\text{max}}$；$P_{\text{dead}} \leq P_t \leq P_{\text{max}}$ | 死水位（不可再取）与防洪上限 |
| C3 | $x_{M,t} + s_{w,t} = D_w(t)$；$q_t + s_{e,t} = D_e(t)$ | 需求平衡（短缺显式变量） |
| C4 | $0 \leq x_{P,t} \leq \min(C_{\text{pipe}}, V_P(t) - V_P(P_{\text{dead}}))$ | 输水能力 + 不可抽取死水位以下水量 |
| C5 | $q_t \leq x_{M,t} + s_{e,t}$ 且 $q_t$ 的水头 $H(M_t) \geq H_{\text{min,power}}$ | 发电过水与最低发电水位 |
| C6 | 短缺分层：$s_{w,t}$ 按优先级序从最低层开始累积（agricultural 先于 industrial 先于 residential），residential 短缺仅在前两层用尽后发生 | Q3 政策的形式化（优先级字典序） |

### 4.3 机理方程

**M1 —— 水位-库容关系**：

$$V_M(M_t), \quad V_P(P_t) \quad \text{：附表分段线性插值}$$

**M2 —— 两库守恒滚动（含蒸发）**：

$$V_P(t+1) = V_P(t) - x_{P,t} - E_P(t)$$

$$V_M(t+1) = V_M(t) + x_{P,t} - x_{M,t} - E_M(t)$$

其中蒸发量 $E_M(t) = e_0 \cdot A_{\text{surf}}(M_t)$，表面积由容量曲线反推。

**M3 —— 发电-水位耦合**：

$$E_t = \eta \cdot \rho \cdot g \cdot H(M_t) \cdot q_t$$

$$H(M_t) = M_t - H_{\text{tail}}$$

水头衰减使"多抽水"与"多发电"在低水位下冲突——这是 Q2 竞争的数学根源。

**M4 —— 短缺分层实现**：

$$s_{w,t} = s_{\text{agr}} + s_{\text{ind}} + s_{\text{res}}$$

按 C6 字典序逐层累积。LP 可线性化：分层短缺变量 + 优先级权重 $M$ 大数法或分阶段 LP。

**M5 —— Q4 情景传播**：

$$D_w(t) = D_{w0}(1+g)^t(1-c)$$

$$D_e(t) = D_{e0}(1+g_e)^t(1-\eta_{\text{ren}}(t))$$

增长率、节水、可再生三参数独立扫描。

### 4.4 模型选择理由

| 候选模型 | 优点 | 缺点 | 选用情况 |
|---------|------|------|---------|
| 分层字典序 LP + 情景滚动（本框架） | 准则可审计、短缺显式、工程边界全入模 | 字典序需分阶段 LP | **选用** |
| 加权和单层 LP | 单次求解 | $\lambda$ 无从取值时准则不可审计 | 未选用 |
| 随机动态规划（来水不确定） | 来水随机最优 | 维数灾难；Q1 基线为零来水确定情景，本轮不需要 | 未选用 |

选用分层字典序 LP 的理由：Q2 明确要求显式准则——字典序比加权和更可审计；短缺必须作为显式变量才能承载 Q3；工程边界（C2/C4/C5）全入模后 Q1 的耗尽时间才是物理可达的读数。

### 4.5 不确定性处理

| 不确定性来源 | 处理方式 | 影响 |
|-------------|---------|------|
| 蒸发 $e_0$ | 情景分析 | $T_{\text{exhaust}}$ 下界修正（开关对照） |
| 输水能力 $C_{\text{pipe}}$ | 情景分析 | 抽水可行性边界 |
| 需求增长 $g$ / 节水 $c$ | 传播分析 | $T_{\text{exhaust}}$ 曲面（Q4） |
| 可再生占比 $\eta_{\text{ren}}(t)$ | 传播分析 | 发电需水下降 → $T_{\text{exhaust}}$ 延长（Q4） |
| 字典序 vs 加权和的准则选择 | 情景分析 | 帕累托前沿对照（Q2 双准则稳健性） |

## 五、求解方法

本模型采用分层字典序线性规划 + 情景滚动框架求解，具体步骤如下：

**步骤 1：参数初始化**

- 读取容量曲线 $V_M(\cdot)$, $V_P(\cdot)$（附表分段线性插值）
- 设定死水位、上限、需求基线、蒸发系数、输水能力等参数
- 初始化 $M_0$, $P_0$

**步骤 2：字典序分阶段 LP**

对于每个时期 $t$，按优先级分阶段求解 LP：

- **阶段 1**：最小化 residential 短缺 $s_{\text{res},t}$（目标：$s_{\text{res},t} = 0$）
- **阶段 2**：在 $s_{\text{res},t} = 0$ 的约束下，最小化 industrial 短缺 $s_{\text{ind},t}$
- **阶段 3**：在前两阶段最优值约束下，最小化 agricultural 短缺 $s_{\text{agr},t}$
- **阶段 4**：在前三阶段最优值约束下，最大化发电量 $E_t$

每个阶段求解如下 LP：

$$\min \quad \text{当前阶段短缺变量}$$

$$\text{s.t.} \quad \begin{cases} \text{C1: 两库水量守恒（含蒸发）} \\ \text{C2: 水位安全边界} \\ \text{C3: 需求平衡（含短缺变量）} \\ \text{C4: 输水能力约束} \\ \text{C5: 发电过水与最低水位约束} \\ \text{前阶段最优值约束} \end{cases}$$

**步骤 3：滚动求解**

从 $t=0$ 开始，逐期求解字典序 LP，更新状态 $(M_{t+1}, P_{t+1})$，直到触及死水位或达到规划期末。

**步骤 4：帕累托前沿生成（$\lambda$ 加权对照）**

对 $\lambda$ 在 $[0, 1]$ 上均匀取值，对每个 $\lambda$ 求解加权和 LP，记录各类短缺总量与总发电量，绘制帕累托前沿，与字典序结果对照。

**步骤 5：敏感性分析**

| 参数 | 扫描范围 | 观测指标 |
|------|---------|---------|
| 需求增长率 $g$ | $-2\%$ 至 $+3\%$/yr | $T_{\text{exhaust}}$ 曲面（Q4） |
| 节水率 $c$ | $0$-$30\%$ | $T_{\text{exhaust}}$ 延长量 |
| 可再生占比 $\eta_{\text{ren}}$ | 初始值 $\to 50\%$ | $D_e$ 下降与短缺频率 |
| 蒸发开关 $e_0$ | $0$ vs 文献典型值 | $T_{\text{exhaust}}$ 差（蒸发重要性定级） |
| 输水能力 $C_{\text{pipe}}$ | $\pm 50\%$ | 可行域与短缺频率 |

**步骤 6：Q1 基线情景读数**

在零来水、需求固定条件下，运行框架得到：

- 最优抽水策略 $(x_{P,t}^*, x_{M,t}^*)$
- 耗尽时间 $T_{\text{exhaust}}$
- 维持零短缺所需外部补水量 $\Delta W$


## 论文 Z

# 建模论文

## 一、问题重述

本题围绕美国科罗拉多河流域两座水库——Mead（米德）水库与 Powell（鲍威尔）水库的水资源联合调度问题展开。具体子问题包括：

1. **抽水决策**：在满足固定用水需求（农业、工业、居民）和发电需求的前提下，确定从两库分别抽取多少水量是最优的。
2. **耗尽时间估算**：在无额外来水的基线情景下，两库各自可以维持多久，何时触及死水位。
3. **补水量测算**：为维持两库系统长期运行，需要补充多少水量。
4. **竞争利益准则**：用水需求与发电需求之间存在竞争，需要建立明确的决策准则来解决这一冲突。

## 二、假设

基于建模产物，本文采用以下假设：

| 假设编号 | 内容 | 合理性说明 |
|---------|------|-----------|
| A1 | 两库水量仅通过抽水管道交换（Powell→Mead），无其他联通 | 题面设定 |
| A2 | 需求（农业/工业/居民用水 + 发电用水）为固定常量 | 题面 Q1 固定需求设定 |
| A3 | 无额外来水（降雨等）作为 Q1 基线情景 | 题面 Q1 显式条件 |

## 三、符号说明

### 变量

| 符号 | 名称 | 描述 | 单位 | 类型 | 定义域 |
|------|------|------|------|------|--------|
| $M$ | Mead 水位 | 水库水位高度 | ft | 状态变量 | $\geq 0$ |
| $P$ | Powell 水位 | 水库水位高度 | ft | 状态变量 | $\geq 0$ |
| $x_P$ | 从 Powell 抽水量 | 决策变量 | acre-ft/yr | 决策变量 | $\geq 0$ |
| $x_M$ | 从 Mead 抽水量 | 决策变量 | acre-ft/yr | 决策变量 | $\geq 0$ |
| $D_w$ | 用水总需求 | 农业+工业+居民 | acre-ft/yr | 输入参数 | $>0$ |
| $D_e$ | 发电需水量 | 发电所需过水量 | acre-ft/yr | 输入参数 | $>0$ |

### 参数

| 符号 | 名称 | 取值来源 | 单位 |
|------|------|---------|------|
| $p_1$ | 库容-水位转换系数 | 题目附表（容量曲线） | acre-ft/ft |
| $p_2$ | 初始水位 $M_0$, $P_0$ | 题面条件 | ft |

## 四、模型建立

### 4.1 目标函数

本模型目标为：**求最小抽水代价下满足需求，并推算两库耗尽时间**。

目标函数（Q1）：

$$\min \quad \text{总抽水量} = x_P + x_M$$

$$\text{s.t.} \quad x_P + x_M \geq D_w + D_e$$

耗尽时间估计量：

$$T_{\text{exhaust}} = \min\{t : M(t) = 0 \text{ 或 } P(t) = 0\}$$

其中 $M(t)$ 和 $P(t)$ 为第 $t$ 期两库水位。

### 4.2 约束条件

| 约束编号 | 表达式 | 物理/工程解释 |
|---------|--------|-------------|
| C1 | $x_P + x_M \geq D_w + D_e$ | 需求满足：总抽水量须覆盖用水与发电需求 |

### 4.3 机理方程

**M1 —— 库容折算**：水位与水量通过容量曲线转换：

$$V(M) = f_{\text{cap}}(M), \quad V(P) = f_{\text{cap}}(P)$$

其中 $f_{\text{cap}}$ 由题目附表的容量曲线查得。

**M2 —— 水量守恒**：逐期水量滚动关系：

$$V_P(t+1) = V_P(t) - x_P$$

$$V_M(t+1) = V_M(t) - x_M + x_P$$

即 Powell 抽出的水一部分直接供水需求，一部分通过管道注入 Mead。

### 4.4 模型选择理由

| 候选模型 | 优点 | 缺点 | 选用情况 |
|---------|------|------|---------|
| 线性规划 + 水量守恒 | 简单 | 未考虑发电水位约束 | **选用** |
| 动态规划 | 可处理时序 | 状态维数高 | 未选用 |

选用线性规划（LP）的理由：约束线性、目标明确，LP 足够满足 Q1 基线情景下的求解需求。

### 4.5 不确定性处理

| 不确定性来源 | 处理方式 | 影响 |
|-------------|---------|------|
| 需求变化 | 定性分析 | Q4 讨论 |
| 蒸发损失 | 忽略 | 未建模 |

## 五、求解方法

本模型采用线性规划方法求解，具体步骤如下：

**步骤 1：参数初始化**

读取题目附表中的容量曲线 $f_{\text{cap}}$，获取初始水位 $M_0$ 和 $P_0$，以及固定需求 $D_w$ 和 $D_e$。

**步骤 2：建立线性规划模型**

决策变量为 $x_P$ 和 $x_M$，目标函数为最小化总抽水量，约束为需求满足条件。

**步骤 3：求解最优抽水方案**

调用线性规划求解器（如单纯形法或内点法），得到最优抽水策略 $(x_P^*, x_M^*)$。

**步骤 4：滚动仿真计算耗尽时间**

基于最优抽水策略，按水量守恒方程逐期滚动：

$$V_P(t+1) = V_P(t) - x_P^*$$

$$V_M(t+1) = V_M(t) - x_M^* + x_P^*$$

当任一库容降至零时停止，记录耗尽时间 $T_{\text{exhaust}}$。

**步骤 5：补水量估算**

在零来水基线情景下，维持需求 $D_w + D_e$ 所需的外部补水量为：

$$\Delta W = (D_w + D_e) \times T_{\text{exhaust}} - (V_P(M_0) + V_M(M_0))$$

其中 $V_P(M_0)$ 和 $V_M(M_0)$ 为初始库容。

**敏感性分析**：对需求 $D$ 进行 $\pm 20\%$ 扰动，观测耗尽时间 $T_{\text{exhaust}}$ 的变化。


## 匿名建模产物（仅供参考）


### 产物 X

```json
{
  "problem_id": "2022_B",
  "mma_raw_output": {
    "eda": "本题属机理/优化混合题（水位与库容为状态常量表，需求为给定值），EDA 聚焦：① 容量曲线（水位-库容）的关系提取与插值方案；② 初始水位 M0/P0 与死水位、发电最低水位的物理一致性验证；③ 需求 D_w/D_e 的量纲核对；④ 不做描述性统计。可视化：水位-库容曲线插值图。",
    "ques1": "问题类型判断：优化类（线性约束下的资源调度）+ 仿真（水位演化）。模型选择：线性规划 LP（决策变量为各期 x_P, x_M），备选动态规划；选择理由：约束与需求均线性，LP 有全局最优保证。建模思路：以月为步长，两库水量守恒 + 需求约束 + 水位安全边界约束（死水位/防洪位），LP 逐期求解，直到水位触及死水位判定耗尽。求解方法：单纯形法逐期滚动。验证策略：守恒方程残差检查 + 边界情形（零抽水）对照。可视化：两库水位时序曲线 + 耗尽时间随需求敏感度折线。",
    "ques2": "问题类型判断：多目标优化。模型选择：加权和法（用水满足度 + 发电量两个目标），备选 NSGA-II；选择理由：两目标可量化且决策者可给定权重，加权和更透明。建模思路：目标1=缺水率最小，目标2=发电量（过水流量×水头）最大；权重 λ 扫描给出帕累托前沿。求解方法：LP 参数化扫描。验证策略：帕累托前沿凸性检查。可视化：帕累托前沿图。",
    "ques3": "问题类型判断：短缺政策（约束不可行情形）。模型选择：优先级分层约束（residential > industrial > agricultural > 发电用水顺位削减），备选比例削减。选择理由：优先级分层贴近实际水法与伦理惯例，规则透明。建模思路：当可用水量 < 总需求时按优先级自下而上削减，发电转为缺口报告。求解方法：分层 LP。验证策略：短缺情景全覆盖测试。可视化：不同短缺程度下各部门供水量堆叠图。",
    "ques4": "问题类型判断：情景/敏感性分析。模型选择：需求增长/收缩、可再生能源占比上升、节水措施三组情景滚动 LP。建模思路：需求 D_w(t) 按增长率 g 缩放；可再生能源占比上升削减发电需水量 D_e；节水措施按比例压缩 D_w。求解方法：多情景滚动 LP。验证策略：情景矩阵全覆盖。可视化：耗尽时间随 g 与节水比例的等高线热力图。",
    "sensitivity_analysis": "关键参数：需求 D_w/D_e（±20%）、初始水位 M0/P0（±10%）、发电权重 λ（0-1 扫描）、可再生能源占比。评估指标：耗尽时间、缺水率、发电量、帕累托前沿移动。可视化：龙卷风图 + 等高线热力图。鲁棒性验证：极端情景（连续枯水、需求激增）压力测试。"
  },
  "problem_interpretation": "两库系统的逐期 LP 调度框架：决策变量为逐期抽水量，约束为水量守恒+水位安全边界+需求满足，多目标（缺水率/发电量）以加权和+帕累托前沿呈现，短缺按优先级分层削减，四问同源于滚动 LP。",
  "assumptions": [
    {
      "id": "A1",
      "statement": " Powell→Maid 单向输水，无逆向",
      "justification": "工程设定"
    },
    {
      "id": "A2",
      "statement": "月步长滚动，期内流量均匀",
      "justification": "离散化近似"
    },
    {
      "id": "A3",
      "statement": "发电量 ∝ 过水流量 × 水头（水头由水位决定）",
      "justification": "水电常识"
    }
  ],
  "variables": [
    {
      "id": "M_t",
      "name": "Mead 水位（第 t 期）",
      "description": "状态",
      "unit": "ft",
      "role": "state",
      "domain": "[死水位, 防洪上限]"
    },
    {
      "id": "P_t",
      "name": "Powell 水位（第 t 期）",
      "description": "状态",
      "unit": "ft",
      "role": "state",
      "domain": "[死水位, 防洪上限]"
    },
    {
      "id": "x_P,t",
      "name": "Powell 期抽水量",
      "description": "决策",
      "unit": "acre-ft",
      "role": "decision",
      "domain": "≥0"
    },
    {
      "id": "x_M,t",
      "name": "Mead 期抽水量",
      "description": "决策",
      "unit": "acre-ft",
      "role": "decision",
      "domain": "≥0"
    },
    {
      "id": "short_t",
      "name": "第 t 期短缺量",
      "description": "需求未满足部分",
      "unit": "acre-ft",
      "role": "derived",
      "domain": "≥0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "容量曲线 V(·)",
      "value_or_source": "题目附表插值",
      "unit": "acre-ft",
      "source": "data"
    },
    {
      "id": "p2",
      "name": "死水位/发电最低水位",
      "value_or_source": "工程规范（题面附表）",
      "unit": "ft",
      "source": "data"
    },
    {
      "id": "p3",
      "name": "需求 D_w, D_e",
      "value_or_source": "题面给定（Q1 固定；Q4 情景缩放）",
      "unit": "acre-ft/yr",
      "source": "data"
    },
    {
      "id": "p4",
      "name": "发电效率系数",
      "value_or_source": "水电常识值",
      "unit": "1",
      "source": "literature"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "V_P(t+1) = V_P(t) − x_P,t（含蒸发修正可选项）；V_M(t+1) = V_M(t) − x_M,t + x_P,t",
      "rationale": "两库水量守恒"
    },
    {
      "id": "C2",
      "expression": "死水位 ≤ M_t, P_t ≤ 防洪上限",
      "rationale": "水位安全边界"
    },
    {
      "id": "C3",
      "expression": "x_M,t + x_P,t + short_t = D_w + D_e（Q3 短缺放开前取 short=0）",
      "rationale": "需求平衡"
    },
    {
      "id": "C4",
      "expression": "x_P,t ≤ 输水管道通过能力",
      "rationale": "工程能力约束"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "min Σ_t short_t（缺水率）与 max Σ_t 发电量 的加权和 λ 扫描",
      "kind": "minimize",
      "rationale": "Q2 显式准则：λ 公开且做帕累托前沿"
    },
    {
      "id": "O2",
      "expression": "T_exhaust = min{t: M_t 或 P_t 触及死水位}",
      "kind": "estimand",
      "rationale": "Q1 耗尽时间"
    },
    {
      "id": "O3",
      "expression": "ΔW = Σ_t 需求缺口（无来水情景下维持需求的累积补水量）",
      "kind": "estimand",
      "rationale": "Q1 补水量"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "水位-库容",
      "equation": "V(M_t), V(P_t) 由容量曲线线性插值",
      "derivation_notes": "附表插值"
    },
    {
      "id": "M2",
      "name": "守恒滚动",
      "equation": "见 C1",
      "derivation_notes": "逐期 LP"
    },
    {
      "id": "M3",
      "name": "发电量",
      "equation": "E_t = η·ρ·g·H(M_t)·x_M,t（水头 H 由水位定）",
      "derivation_notes": "水头随水位下降而衰减——发电与水位耦合"
    },
    {
      "id": "M4",
      "name": "需求演化（Q4）",
      "equation": "D_w(t) = D_w0·(1+g)^t·(1−c)；D_e(t) = D_e0·(1−η_ren(t))·(1+g_e)^t",
      "derivation_notes": "增长率 g、节水 c、可再生占比 η_ren 为情景参数"
    }
  ],
  "candidate_models": [
    {
      "model": "逐期 LP（本模型）",
      "pros": "全局最优+帕累托前沿可参数化",
      "cons": "线性近似蒸发/水头"
    },
    {
      "model": "动态规划",
      "pros": "非线性水头处理",
      "cons": "维数灾难"
    },
    {
      "model": "NSGA-II",
      "pros": "非凸前沿",
      "cons": "无全局最优保证"
    }
  ],
  "selected_model": "逐期 LP + 加权和帕累托扫描 + 分层短缺政策",
  "selection_reason": "约束线性；加权和法透明且满足 Q2 'Explicitly state criteria' 的可审计要求；帕累托前沿给决策者完整权衡面",
  "uncertainties": [
    {
      "source": "蒸发与渗漏",
      "handling": "scenario",
      "effect": "耗尽时间下界修正"
    },
    {
      "source": "来水（降水）",
      "handling": "scenario",
      "effect": "Q1 基线为零来水、扩展情景补来水"
    },
    {
      "source": "需求增长率 g",
      "handling": "propagated",
      "effect": "Q4 等高线"
    },
    {
      "source": "可再生占比 η_ren(t)",
      "handling": "propagated",
      "effect": "Q4 发电需水下降"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "需求 D_w/D_e",
      "range": "±20%",
      "metric": "T_exhaust / ΔW"
    },
    {
      "parameter": "初始水位 M0/P0",
      "range": "±10%",
      "metric": "T_exhaust"
    },
    {
      "parameter": "λ（用水-发电权重）",
      "range": "0-1 扫描",
      "metric": "帕累托前沿"
    },
    {
      "parameter": "可再生占比 η_ren",
      "range": "初始值至 50%",
      "metric": "D_e 下降与 T_exhaust 延长"
    }
  ]
}
```

### 产物 Y

```json
{
  "problem_id": "2022_B",
  "problem_interpretation": "四问同源于一个两库随机滚动调度框架：Q1 的抽水决策/耗尽时间/补水量是框架在固定需求、零来水基线下的读数；Q2 的竞争利益准则必须显式（分层/加权）且可审计；Q3 的短缺政策是约束不可行时的规则化降级；Q4 的需求增长/可再生/节水是参数化情景在框架上的传播。成功标准：四问各自能指认到框架中的决策变量、约束或目标；所有工程边界（死水位、输水能力、蒸发）显式入模。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "Powell→Mead 单向输水，通过能力上限 Cap_pipe（工程参数，情景化）",
      "justification": "题面工程设定 + 干预②：能力上限显式入模"
    },
    {
      "id": "A2",
      "statement": "月步长；月内流量均匀；蒸发为水位与表面积的函数 E(t) = e_0·A_surf(M_t, P_t)（情景开关）",
      "justification": "离散化 + 干预②：蒸发不可静默省略"
    },
    {
      "id": "A3",
      "statement": "发电量 E_t = η·ρ·g·H(M_t)·q_t，水头 H 随水位下降而衰减；发电需水量 D_e 为保证电网基荷的过水需求",
      "justification": "水电工程常识 + 题面"
    },
    {
      "id": "A4",
      "statement": "Q1 基线：零来水、需求固定；不确定性经由来水/需求情景分支进入（见 uncertainties）",
      "justification": "题面 Q1 显式条件"
    }
  ],
  "variables": [
    {
      "id": "M_t",
      "name": "Mead 水位",
      "description": "状态",
      "unit": "ft",
      "role": "state",
      "domain": "[M_dead, M_max]"
    },
    {
      "id": "P_t",
      "name": "Powell 水位",
      "description": "状态",
      "unit": "ft",
      "role": "state",
      "domain": "[P_dead, P_max]"
    },
    {
      "id": "x_P,t",
      "name": "Powell 抽水量",
      "description": "决策",
      "unit": "acre-ft/月",
      "role": "decision",
      "domain": "[0, Cap_pipe]"
    },
    {
      "id": "x_M,t",
      "name": "Mead 抽水量",
      "description": "决策",
      "unit": "acre-ft/月",
      "role": "decision",
      "domain": "≥0"
    },
    {
      "id": "s_w,t",
      "name": "用水短缺",
      "description": "居民/工业/农业合计短缺",
      "unit": "acre-ft/月",
      "role": "derived",
      "domain": "≥0"
    },
    {
      "id": "s_e,t",
      "name": "发电短缺",
      "description": "发电过水缺口",
      "unit": "acre-ft/月",
      "role": "derived",
      "domain": "≥0"
    },
    {
      "id": "q_t",
      "name": "发电过流量",
      "description": "经过水轮机的流量",
      "unit": "acre-ft/月",
      "role": "decision",
      "domain": "≥0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "容量曲线 V_M(·), V_P(·)",
      "value_or_source": "题面附表分段线性插值",
      "unit": "acre-ft",
      "source": "data"
    },
    {
      "id": "p2",
      "name": "死水位 M_dead, P_dead 与上限 M_max, P_max",
      "value_or_source": "工程规范/题面附表",
      "unit": "ft",
      "source": "data"
    },
    {
      "id": "p3",
      "name": "需求基线 D_w0, D_e0 及增长率 g、节水率 c、可再生占比 η_ren(t)",
      "value_or_source": "题面 Q4 情景参数",
      "unit": "混合",
      "source": "assumed"
    },
    {
      "id": "p4",
      "name": "蒸发系数 e_0",
      "value_or_source": "湖泊蒸发文献典型值（情景开关）",
      "unit": "ft/月",
      "source": "literature"
    },
    {
      "id": "p5",
      "name": "输水能力 Cap_pipe",
      "value_or_source": "工程参数（情景）",
      "unit": "acre-ft/月",
      "source": "assumed"
    },
    {
      "id": "p6",
      "name": "发电效率 η 与水电转换系数",
      "value_or_source": "水电工程典型值",
      "unit": "1",
      "source": "literature"
    },
    {
      "id": "p7",
      "name": "短缺优先级序",
      "value_or_source": "水法惯例：residential > industrial > agricultural > hydropower",
      "unit": "1",
      "source": "literature"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "V_P(t+1) = V_P(t) − x_P,t − E_P(t)；V_M(t+1) = V_M(t) + x_P,t − x_M,t − E_M(t)",
      "rationale": "两库水量守恒（蒸发显式入模，可关）"
    },
    {
      "id": "C2",
      "expression": "M_dead ≤ M_t ≤ M_max；P_dead ≤ P_t ≤ P_max",
      "rationale": "死水位（不可再取）与防洪上限"
    },
    {
      "id": "C3",
      "expression": "x_M,t + s_w,t = D_w(t)；q_t + s_e,t = D_e(t)",
      "rationale": "需求平衡（短缺显式变量而非隐式缺额）"
    },
    {
      "id": "C4",
      "expression": "0 ≤ x_P,t ≤ min(Cap_pipe, V_P(t) − V_P(P_dead))",
      "rationale": "输水能力 + 不可抽取死水位以下水量（干预②：物理可行性）"
    },
    {
      "id": "C5",
      "expression": "q_t ≤ x_M,t + s_e,t 且 q_t 的水头 H(M_t) ≥ H_min_power",
      "rationale": "发电过水与最低发电水位"
    },
    {
      "id": "C6",
      "expression": "短缺分层：s_w,t 按优先级序从最低层开始累积（agricultural 先于 industrial 先于 residential），residential 短缺仅在前两层用尽后发生",
      "rationale": "Q3 政策的形式化（优先级字典序）"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "Q2 竞争利益准则（显式、可审计）：字典序 lexicographic——第一优先 residential 全满足，第二 industrial，第三 agricultural 缺口最小化，第四在剩余水中最大化发电 E_t；λ 加权作为字典序的连续化对照并给帕累托前沿",
      "kind": "lexicographic + weighted",
      "rationale": "Q2 要求 Explicitly state criteria——字典序声明即准则，帕累托前沿给权衡面"
    },
    {
      "id": "O2",
      "expression": "T_exhaust = min{t: M_t = M_dead 或 P_t = P_dead}（零来水基线）",
      "kind": "estimand",
      "rationale": "Q1 耗尽时间"
    },
    {
      "id": "O3",
      "expression": "ΔW(T) = Σ_{t≤T} (s_w,t + s_e,t) 的反解——维持零短缺所需的外部补水量",
      "kind": "estimand",
      "rationale": "Q1 补水量"
    },
    {
      "id": "O4",
      "expression": "Q4 读数：T_exhaust(g, c, η_ren) 曲面与短缺频率",
      "kind": "estimand",
      "rationale": "Q4 情景传播"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "水位-库容",
      "equation": "V_M(M_t), V_P(P_t)：附表分段线性插值",
      "derivation_notes": "p1"
    },
    {
      "id": "M2",
      "name": "两库守恒滚动（含蒸发）",
      "equation": "见 C1；E_M(t) = e_0·A_surf(M_t)",
      "derivation_notes": "蒸发与表面积（由容量曲线反推）耦合"
    },
    {
      "id": "M3",
      "name": "发电-水位耦合",
      "equation": "E_t = η·ρ·g·H(M_t)·q_t，H(M_t) = M_t − H_tail",
      "derivation_notes": "水头衰减使'多抽水'与'多发电'在低水位下冲突——Q2 竞争的数学根源"
    },
    {
      "id": "M4",
      "name": "短缺分层实现",
      "equation": "s_w,t = s_agr + s_ind + s_res，按 C6 字典序逐层累积",
      "derivation_notes": "LP 可线性化：分层短缺变量 + 优先级权重 M 大数法或分阶段 LP"
    },
    {
      "id": "M5",
      "name": "Q4 情景传播",
      "equation": "D_w(t) = D_w0(1+g)^t(1−c)；D_e(t) = D_e0(1+g_e)^t(1−η_ren(t))",
      "derivation_notes": "增长率、节水、可再生三参数独立扫描"
    }
  ],
  "candidate_models": [
    {
      "model": "分层字典序 LP + 情景滚动（本框架）",
      "pros": "准则可审计、短缺显式、工程边界全入模",
      "cons": "字典序需分阶段 LP"
    },
    {
      "model": "加权和单层 LP",
      "pros": "单次求解",
      "cons": "λ 无从取值时准则不可审计"
    },
    {
      "model": "随机动态规划（来水不确定）",
      "pros": "来水随机最优",
      "cons": "维数灾难；Q1 基线为零来水确定情景，本轮不需要"
    }
  ],
  "selected_model": "分层字典序 LP + 情景滚动（λ 加权对照）",
  "selection_reason": "Q2 明确要求显式准则——字典序比加权和更可审计；短缺必须作为显式变量才能承载 Q3；工程边界（C2/C4/C5）全入模后 Q1 的耗尽时间才是物理可达的读数",
  "uncertainties": [
    {
      "source": "蒸发 e_0",
      "handling": "scenario",
      "effect": "T_exhaust 下界修正（开关对照）"
    },
    {
      "source": "输水能力 Cap_pipe",
      "handling": "scenario",
      "effect": "抽水可行性边界"
    },
    {
      "source": "需求增长 g / 节水 c",
      "handling": "propagated",
      "effect": "T_exhaust 曲面（Q4）"
    },
    {
      "source": "可再生占比 η_ren(t)",
      "handling": "propagated",
      "effect": "发电需水下降 → T_exhaust 延长（Q4）"
    },
    {
      "source": "字典序 vs 加权和的准则选择",
      "handling": "scenario",
      "effect": "帕累托前沿对照（Q2 双准则稳健性）"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "需求增长率 g",
      "range": "−2% 至 +3%/yr",
      "metric": "T_exhaust 曲面（Q4）"
    },
    {
      "parameter": "节水率 c",
      "range": "0-30%",
      "metric": "T_exhaust 延长量"
    },
    {
      "parameter": "可再生占比 η_ren",
      "range": "初始值 → 50%",
      "metric": "D_e 下降与短缺频率"
    },
    {
      "parameter": "蒸发开关 e_0",
      "range": "0 vs 文献典型值",
      "metric": "T_exhaust 差（蒸发重要性定级）"
    },
    {
      "parameter": "输水能力 Cap_pipe",
      "range": "±50%",
      "metric": "可行域与短缺频率"
    }
  ]
}
```

### 产物 Z

```json
{
  "problem_id": "2022_B",
  "problem_interpretation": "Mead（M）与 Powell（P）两库在固定供水/供电需求下的抽水决策：抽多少、多久耗尽、需补多少水，以及竞争利益（用水 vs 发电）的解决准则与短缺政策。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "两库水量仅通过抽水管道交换（Powell→Mead），无其他联通",
      "justification": "题面设定"
    },
    {
      "id": "A2",
      "statement": "需求（农业/工业/居民用水 + 发电用水）为固定常量",
      "justification": "题面 Q1 固定需求设定"
    },
    {
      "id": "A3",
      "statement": "无额外来水（降雨等）作为 Q1 基线情景",
      "justification": "题面 Q1 显式条件"
    }
  ],
  "variables": [
    {
      "id": "M",
      "name": "Mead 水位",
      "description": "水库水位高度",
      "unit": "ft",
      "role": "state",
      "domain": "≥0"
    },
    {
      "id": "P",
      "name": "Powell 水位",
      "description": "水库水位高度",
      "unit": "ft",
      "role": "state",
      "domain": "≥0"
    },
    {
      "id": "x_P",
      "name": "从 Powell 抽水量",
      "description": "决策变量",
      "unit": "acre-ft/yr",
      "role": "decision",
      "domain": "≥0"
    },
    {
      "id": "x_M",
      "name": "从 Mead 抽水量",
      "description": "决策变量",
      "unit": "acre-ft/yr",
      "role": "decision",
      "domain": "≥0"
    },
    {
      "id": "D_w",
      "name": "用水总需求",
      "description": "农业+工业+居民",
      "unit": "acre-ft/yr",
      "role": "input",
      "domain": ">0"
    },
    {
      "id": "D_e",
      "name": "发电需水量",
      "description": "发电所需过水量",
      "unit": "acre-ft/yr",
      "role": "input",
      "domain": ">0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "库容-水位转换系数",
      "value_or_source": "题目附表（容量曲线）",
      "unit": "acre-ft/ft",
      "source": "data"
    },
    {
      "id": "p2",
      "name": "初始水位 M0, P0",
      "value_or_source": "题面条件",
      "unit": "ft",
      "source": "data"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "x_P + x_M ≥ D_w + D_e",
      "rationale": "需求满足"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "求最小抽水代价下满足需求，并推算两库耗尽时间",
      "kind": "simulate",
      "rationale": "Q1"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "库容折算",
      "equation": "水量 V(M) 由容量曲线查得",
      "derivation_notes": "水位↔水量"
    },
    {
      "id": "M2",
      "name": "水量守恒",
      "equation": "V_P(t+1) = V_P(t) − x_P；V_M(t+1) = V_M(t) − x_M + x_P",
      "derivation_notes": "Powell 抽水入 Mead"
    }
  ],
  "candidate_models": [
    {
      "model": "线性规划 + 水量守恒",
      "pros": "简单",
      "cons": "未考虑发电水位约束"
    },
    {
      "model": "动态规划",
      "pros": "可处理时序",
      "cons": "状态维数高"
    }
  ],
  "selected_model": "线性规划 + 水量守恒",
  "selection_reason": "约束线性、目标明确，LP 足够",
  "uncertainties": [
    {
      "source": "需求变化",
      "handling": "qualitative",
      "effect": "Q4 讨论"
    },
    {
      "source": "蒸发损失",
      "handling": "ignored",
      "effect": "未建模"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "需求 D",
      "range": "±20%",
      "metric": "耗尽时间"
    }
  ]
}
```