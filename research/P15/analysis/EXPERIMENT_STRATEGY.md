# EXPERIMENT STRATEGY — 实验体系重构与 Constructor-independent Benchmark 设计

> **基于 K001/K002/K003 实验科学审计**。核心问题：当前实验测的是"表示/知识→文本质量"（L1/L2），而 LinHoMo 真正想证明的是"Runtime 带来的建模增益"（L4/L5/L6）。

---

## 1. 当前实验体系的根本问题

### 1.1 测错了层级

| 实验 | 主终点 | 实际测量层 | 目标层 | 差距 |
|---|---|---|---|---|
| K001 | MCQ 盲评总分 | L1/L2（文本质量） | L4/L5/L6 | 差 3 层 |
| K002 | MCQ 盲评总分（S−F） | L1/L2 + L3"声明" | L4/L5/L6 | 差 2-3 层 |
| K003 | MCQ 盲评总分（+执行事实） | L1/L2 + L3 真实执行 | L4/L5/L6 | 差 1-2 层 |
| vs001 | 闭环 PASS/FAIL | L3/L4/L5（真实） | L4/L5/L6 | 接近，但 n=1 |

**文本盲评天花板**：盲评能可靠测量 L1（问题理解）和 L2（构造结构），L3（执行）及以上必须由机械执行证据承载。K001/K002 的全部主终点都在盲评可测区，这是它们双双 NEGATIVE 的测量根源。

### 1.2 缺裸 Constructor 对照臂

K001/K002/K003 都是"加 harness 指令的 Agent 内部比格式"，没有"不带 harness 的 Agent"对照（R0 臂）。因此即使 K003 出 positive，也只能说"该格式在该 Agent 上有益"，不能回答"LinHoMo Runtime 带来多少增益"。

arena 还把 F 臂（自由文本）排除出候选池（arena_runner.py:79-82），连"裸自由文本+代码执行质量"都没测。

### 1.3 主终点不是"建模能力"

| 维度 | 是否建模能力 | 当前是否测量 |
|---|---|---|
| 文本质量 | ❌（可声明污染） | ✅ 主终点 |
| 结构质量 | 必要非充分 | ✅ |
| 执行成功（二元） | ❌（饱和） | ✅ K003 66/66 |
| **首次执行失败率** | ✅ | ❌ 恒 0，未真正被测 |
| **修正轮数** | ✅ | ❌ vs001 仅 1 题 |
| **M1→M2 success** | ✅ | ❌ vs001 仅 1 题 |
| Fidelity | 部分（当前退化） | ⚠️ K003 有但同题同分 |
| **数学正确性（L6）** | ✅（最终目标） | ❌ 从未机械测量 |
| 最终可复现性 | 必要非充分 | ⚠️ vs001 replay 2/2 |

### 1.4 benchmark 体系虚设

- `bench_mmbench.py`：空壳执行器，accuracy 恒 0
- e2e 八项指标：覆盖 L1/L2 结构 + 论文层为主，L3 执行真实性、L5 修订、L6 数值正确性不在其内
- `model_correctness` 无外部响应时退化为 MODEL_IR 字段存在性检查（结构检查非语义正确性）
- `validation_reliability`：占位 claim 可通过（GAP_AUDIT 环节 10）
- arena：真实执行+机械选型，但明确"无 GT 数值对照"

### 1.5 调参风险（中高）

| 事件 | 性质 |
|---|---|
| K002 G2 κ=0.401 FAIL → 锚定澄清切换评分对象 → κ=0.4345 仍 <0.6 → 以"分歧可归因"放行 | 后验调整评分口径 |
| rubric v1.0→v1.1 因 L2 天花板零区分度增加判据 | 观察到无差异后改仪器 |
| K003 冻结后 v0.2 修改冻结项 schema（FIX-5.3/5.4） | 冻结纪律被打破 |
| structure_alignment 以维护者定义的 allowed_modeling_structures 为唯一评分依据 | 若按已知答案扩展可系统性抬高 |

---

## 2. L1-L6 层次定义与测量策略

```
L1 Representation   问题/条件/交付要求/模型族的表示
L2 Construction     变量/参数/假设/目标/约束/机理/方程
L3 Execution        代码真实执行、数值产出
L4 Validation       对照/灵敏度/极限/证据-主张对应
L5 Revision         执行/验证失败 → 模型修正 → 再执行闭环
L6 Final Correctness 最终数值结果与客观参考（GT）的吻合度
```

### 各层测量方法

| 层 | 测量方法 | 机械/盲评 | 当前状态 |
|---|---|---|---|
| L1 | decomposition_coverage + 盲评 L1 维度 | 机械 + 盲评 | ✅ 可测 |
| L2 | structure_alignment + 盲评 L2 维度 + MODEL_IR 字段完备性 | 机械 + 盲评 | ✅ 可测（有天花板风险） |
| L3 | 首次执行失败率 + execution_success + code_hash | **机械** | ✅ K003 首次真实测量 |
| L4 | VR pass/fail + fidelity + sensitivity_coverage | **机械** | ⚠️ 原语存在但未接主路径 |
| L5 | 修正轮数分布 + M1→M2 success rate + 修正后 L6 提升 | **机械** | ❌ 仅 vs001 n=1 |
| L6 | 输出 vs GT 数值断言比对（误差/命中率） | **机械** | ❌ 从未测量 |

### "建模增益"的操作性定义

> **LinHoMo Runtime 的建模增益** = 在**同一 Constructor** 上，加入 Runtime（契约 + 真实执行 + 机械验证 + 修订闭环）后，以下机械终点相对于裸构造的变化量（block=题，配对差分）：
> 1. **L6 最终数值正确率** ↑
> 2. **首次执行失败率** ↓
> 3. **达到正确模型的修正轮数** ↓
> 4. **最终 fidelity** ↑
> 5. **可复现性**（replay match）↑
>
> **排除项**：文本质量（可声明污染）、执行成功与否（二元饱和）、结构完备性（天花板化）。MCQ 盲评降级为 L1/L2 辅助终点。

---

## 3. Constructor-independent Benchmark 设计

### 3.1 核心思想

K 系列把"Constructor（外部 Agent）"与"表示格式（Runtime 契约）"混在一起，测到的是联合效应。**2×2 析因设计**分离两者：

| 因子 | 水平 |
|---|---|
| **Constructor C** | C1=外部通用 Agent（裸 Doubao，零 harness 适配）/ C2=MathModelAgent / C3=第二家通用模型（如 GPT，独立对照）/ C4=自研最小 Constructor |
| **Runtime R** | R0=裸（自由生成 model_doc + 代码，无契约、无 harness 执行反馈）/ R1=+LinHoMo Runtime（MODEL_IR 契约 + harness 真实执行 + VR 机械反馈 + revision 循环允许） |

### 3.2 实验设计

**主检验**：C1×C2 两个 Constructor × R0/R1 = 4 臂 × 6 题 × 5 rep = **120 runs**
- C3/C4 为外部队列，逐步扩展
- 泛化：2 题 × 2 rep（每臂）

**题集**：沿用 K003 8 题（主检验 6 + 泛化 2），**必须为每题补充可执行的 GT 数值断言**（problem_cards/*/gt.json 已存在，需要机械化消费）

**重复**：seed 42 固定 + 4 个变化种子；同一题同一臂内 block 配对

### 3.3 测量指标（分层终点）

| 终点 | 层 | 类型 | 定义 |
|---|---|---|---|
| **L6 数值正确率** | L6 | **主终点** | 输出 vs GT 断言比对（误差/命中率） |
| 首次执行失败率 | L3 | 过程终点 | 第一次执行即 rc=0 的比例（当前恒 0，需构造更难的题） |
| 达到 PASS 的修正轮数 | L5 | 过程终点 | 从初始模型到 validation PASS 的修订次数 |
| 最终 fidelity | L4 | 过程终点 | model↔code 一致性（需修复同题同分退化） |
| replay match | 可复现性 | 过程终点 | 重跑输出一致性 |
| MCQ 盲评总分 | L1/L2 | 辅助终点 | 对照 K 系列口径 |

### 3.4 统计方法

- block（题）级配对差 + bootstrap 95% CI（沿用 K 系列决策门 CI 下界>0）
- **析因分解**：
  - Runtime 主效应 = 各 Constructor 内 (R1−R0) 的均值
  - Constructor 主效应 = 各 Runtime 内 C2−C1
  - 交互项 = Runtime 增益是否依赖 Constructor
- **报告 Δ_score 而非单臂绝对分**

### 3.5 如何分离"Runtime 增益"与"Constructor 增益"

1. **配对差分**：增益定义为同一 Constructor 内 R1−R0（block=题），Constructor 能力被差分配对消掉——这是与 K 系列的本质区别
2. **析因主效应与交互项**：若 Runtime 主效应 >0 且交互不显著 → 增益是 harness 的普适贡献；若交互显著 → 增益依赖 Constructor 能力
3. **机械终点防污染**：L6/L3/L5 全部由 harness 机械判定，不用盲评——避免 K002 的"声明 vs 事实"混淆
4. **R0 臂必须同样进 arena 真实重跑**：K003 arena 把 F 臂排除出候选池是设计缺陷，R0 的执行质量必须测量

---

## 4. 下一阶段 3 个科学实验

### 实验 1：Constructor × Runtime 2×2 析因 benchmark（最高优先级）

**目标**：回答"LinHoMo Runtime 带来多少建模增益"——这是唯一能证明产品价值的实验。

**设计**：按 §3 执行，C1（裸 Doubao）×C2（MathModelAgent）×R0/R1，6 题 × 5 rep = 120 runs。

**主终点**：L6 数值正确率（R1−R0 配对差分）

**前置依赖**：
- Constructor Protocol 层（P0）：至少 LocalAgentAdapter + OpenAIAdapter 可用
- L6 数值判定层（实验 2）：GT 断言机械化
- orchestrator 注入通道（P0 工程）：R1 臂能真正接通 Runtime

**成功标准**：Runtime 主效应 Δ_L6 的 95% CI 下界 > 0（positive）或 < 0（negative，同样有价值）

### 实验 2：L6 数值正确性机械判定层 + fidelity 退化修复

**目标**：建立"最终数学正确性"的机械测量能力，修复 fidelity 同题同分退化。

**内容**：
1. 把 8 题 `problem_cards/*/gt.json` 机械化为可执行的数值断言（输出键→参考值/不等式/误差范围）
2. 接入 arena 的 VR 管线，使"数学正确性"成为可自动计算、可复现、不可被盲评污染的终点
3. 修复 fidelity 退化：当前只查"声明符号可观测"（GAP_AUDIT 环节 9），升级为"校验约束/残差/目标值"
4. 建立 L6 判定的 fail-closed 语义：无 GT 断言的题 → L6=unverifiable（不编造分数）

**成功标准**：8/8 题有可执行 GT 断言；fidelity 对同题不同构造有区分度（不再全同分）；L6 判定接入 arena 报告

### 实验 3：L5 Revision 端到端度量实验

**目标**：把 vs001 的 M1→FAIL→M2 闭环从单题扩展到系统实验，量化"验证义务→修正→最终正确"的因果增益。

**设计**：
- 6 题 × 多 rep（沿用 K003 题集）
- 每构造故意引入 1-2 个可检测错误（如 vs001 的 ρ=1.5 超稳定域）
- 测量：验证失败触发修正的概率、修正轮数分布、修正后 L6 提升量
- 对照臂：无 revision 循环（失败即终止）vs 有 revision 循环

**主终点**：修正后 L6 提升量（有 revision − 无 revision）

**前置依赖**：Revision 接入主 DAG（P1 工程）

**承接**：直接验证 K002 SV−F(VAL)=+4.81 与敏感性 A（SV−S MCQ=+5.15）的未决假设——"验证义务是否真的导致修正并提升最终正确性"

---

## 5. 实验治理纪律（写死）

1. **预注册 = 证伪承诺**：评分口径、阈值、维度在实验前冻结；RUNNING 阶段不修改冻结项（K003 v0.2 修改 schema 是违规，不得再犯）
2. **CI 下界>0 才 positive**：保守决策门，不接受"趋势性 positive"
3. **negative result 有效且如实记录**：K001/K002 双 NEGATIVE 是有价值的测量结论，不是失败
4. **机械终点优先**：L3+ 必须由机械证据承载，不用盲评冒充
5. **Constructor-independent**：任何声称"LinHoMo 有增益"的结论必须有裸 Constructor 对照臂
6. **不为 benchmark 调参**：allowed_modeling_structures 等评分依据冻结并审计变更
7. **数据冻结后不改**：FROZEN 后修改 = new revision，旧版作废；不回溯修改实验数据
8. **盲评隔离**：GENERATOR≠EVALUATOR；评分污染必须自曝（K002 检出 7 份污染评分是正面案例）
9. **功效分析前置**：block 数、rep 数在实验前计算，不接受"跑完了才发现功效不足"
10. **K003 结论未出前不得引用**：盲评进行中，不虚构结论

---

## 6. K001/K002/K003 的科学意义重新定位

| 实验 | 测到了什么 | 没测到什么 | 对产品定位的影响 |
|---|---|---|---|
| K001 | 知识注入机制链工作正常；词表错位（measurement failure）；Sham 对照失效；功效不足 | 知识是否提升建模能力（L4+） | 知识层不是能力放大器，是 Constructor 上下文供给 |
| K002 | L3 格式不对称是负效应主因（测量伪影）；SV−F(VAL) 正（验证义务在文本层有相对收益）；κ=0.4345 信度不足 | 结构化表示是否提升建模能力（L4+） | 表示格式是工程契约，不是能力放大器；验证义务值得进一步测（L4/L5） |
| K003 | 66/66 真实执行（工程成熟度）；fidelity misaligned 59%（代码与模型声明不一致）；G2 κ=0.712（L3 判据切执行事实有效） | 执行+验证闭环是否提升最终正确性（L5/L6）；盲评结果未出 | 执行层已修好；下一步必须测 L5/L6 |
| vs001 | M1 FAIL→M2 PASS 闭环真实存在；replay 2/2 match；Validation 真实拦截 | 系统效应（n=1 题） | 闭环可工作，但需扩展到系统实验 |

**综合结论**：K001/K002 双 NEGATIVE 不是"LinHoMo 无效"，而是"在 L1/L2 文本层做文章找不到收益"。K003 把 L3 拉到真实执行，但 L5/L6 仍全空。**实验体系必须从"文本质量测量"转向"执行-验证-修正-最终正确性的闭环增益测量"。**

---

## 7. 当前 benchmark 体系改造清单

| 组件 | 问题 | 改造 |
|---|---|---|
| `bench_mmbench.py` | 空壳，accuracy 恒 0 | 实现为真实 benchmark 或删除 |
| e2e 八项指标 | 覆盖 L1/L2 + 论文，缺 L3/L5/L6 | 增加 L6 数值正确率、L5 修正轮数、L3 首次失败率 |
| `model_correctness` | 退化为字段存在性检查 | 有 GT 时用 L6 机械判定，无 GT 时标 unverifiable |
| `validation_reliability` | 占位 claim 可通过 | 要求 VR 存在 + exec_ref |
| arena | 无 GT 数值对照；F 臂排除 | 接入 L6 判定；R0 臂同样进 arena |
| rubric v1.1 | L1/L2 天花板风险 | 冻结为 L1/L2 辅助工具，不作主终点 |
| `structure_alignment` | 维护者定义 allowed 集 | 冻结 + 变更审计 |

---

*本策略基于 K001/K002/K003 实验科学审计 + 5 路代码审计。所有实验数据如实引用，K003 盲评结果未出不虚构。*
