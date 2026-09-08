# Three-Layer Architecture — 三层架构与治理门禁（2026-09-09 审计后重写 v2）

> **版本演化**：v1（2026-09-06）为"Agent Brain 主战场"时代的旧三层（Agent Brain / Research Runtime / Guardrails），
> 已随定位收束（Model Construction=What / Model Representation=How / Harness=How do we know）与
> 三仓库代码级审计（2026-09-09）**废弃**。本文件 v2 为当前唯一治理版本。
>
> **上游裁决**：`research/REPOSITORY_AUDIT/FINAL_REPORT.md` + `CROSS_REPO_AUDIT.md`（BZD=Knowledge System、
> MathModelAgent=Execution System、LinHoMo=Epistemic System；三者互补非竞争）。

---

## 0. 一句话定位（写死）

> **LinHoMo 当前是"科学建模系统的操作语义设计 + 受控实验平台"，还不是一个完成的 Mathematical Modeling Engine。
> 没有任何一个被审计仓库（包括 LinHoMo）已被实验证明拥有更强的数学建模能力。**

这句结论是 2026-09-09 审计后锁定的项目自我认知，任何宣传、README、论文表述不得越过它。

三仓库真实层次：

| 仓库 | 系统类型 | 回答的问题 | 缺失（本轮审计确认） |
|---|---|---|---|
| BZD | Knowledge System（评审知识） | "怎么评价" | execution + causal capability evidence |
| MathModelAgent | Execution System（agent 流水线） | "怎么做完" | model semantics + epistemic state |
| **LinHoMo** | Epistemic System（科研运行时） | "怎么证明" | **actual computational execution** |

三个缺口互补。LinHoMo 的战略不是"战胜"另外两者，而是**把它们的优势放进正确的层**：
BZD → Evaluation 层（reviewer/rubric/knowledge provider）；MathModelAgent → Execution 层参考（Execution Primitive）。

---

## 1. 三层结构（v2 正式固化）

```text
              ┌───────────────────────────────────────────┐
              │  Layer 1 · Epistemic Layer（核心创新）      │
              │  Problem / Knowledge / Model Artifact /    │
              │  Assumption / Decision / Evidence / Critic │
              └──────────────────┬────────────────────────┘
                                 │  Model Artifact（typed, 非文本）
              ┌──────────────────▼────────────────────────┐
              │  Layer 2 · Execution Layer（吸收 MMA 原语） │
              │  Code / Solver / Simulation / Optimization │
              │  Statistics / Numerical computation        │
              └──────────────────┬────────────────────────┘
                                 │  Result / Evidence（真实数值）
              ┌──────────────────▼────────────────────────┐
              │  Layer 3 · Evaluation Layer（吸收 BZD 思想） │
              │  Model Quality / Evidence Quality /         │
              │  Validation / Failure Attribution /         │
              │  Blind Evaluation / Benchmark               │
              └──────────────────┬────────────────────────┘
                                 │  Model State
                                 ▼
                              revision
```

**层间数据流（真实数据流，不是逻辑图）**：Epistemic 产出 Model Artifact → Execution 消费并产生带真实数值的
ExecutionResult/Evidence → Evaluation 依据 Evidence 判定 Model State → 判定结果回流 revision。

### 1.1 Execution Primitive（从 MathModelAgent 只吸收这个，不吸收 workflow）

```text
ModelArtifact → ExecutionPlan → Code → Code Interpreter → ExecutionResult → Evidence
```

- MathModelAgent 的闭环是 `Code → Result → Writer`；LinHoMo 必须升级为
  `Code → Execution → Typed Result → Evidence → Evidence Gate → Model State`。
- **执行必须产生真实数值**：任何 experiment 节点未真正执行时，产物状态必须为 `not_executed`，
  禁止用 `"{qid} 结论"` 一类假占位 claim 冒充执行结果（对应 P0 工程项①）。

### 1.2 BZD 资产归位（Evaluation 层，不进入 core/model）

- 吸收：评审逻辑 / 原子扣分 / 模型适用性判断 / 建模规范 / reviewer knowledge / 数模经验
  → 成为 `ReviewerPolicy` / `ModelingRubric` / `CriticSkill` / `EvaluationRule`。
- BZD 的 5713 条字典不得直接成为"系统真理"；每条知识必须携带
  `knowledge_id / source / scope / confidence / provenance / applicability / evidence_requirement`，
  把知识从 authority 变成 **testable knowledge**。

---

## 2. 治理原则（审计后升级）

### 2.1 最高原则：infra 不冒充 capability（四红线之首）

> 大量 schema + artifact + evidence + validator ≠ 科学。
> `result = "{qid} 结论"` 时，任何"很科学"的外观都是 false confidence（R4）。

任何新增基础设施必须回答：**它改变了哪个可测量的 Model Construction behavior？**
回答不了，不得包装成 capability improvement。能力证据只能是受控实验的 Δ（K001 negative 是基准）。

### 2.2 formalized false authority 禁令（BZD 6.81% 教训）

> 无可靠来源的经验判断（如 6.81%、30–50%、advisor_multiplier）经确定性脚本"机械化、结构化"
> 后会伪装成客观测量结果——这比 LLM hallucination 更危险（systematic false authority）。

Evidence/Provenance 层**明确禁止**：
- 无 provenance 的常数进入确定性评分/判定代码；
- 社区经验被写成官方规则（official/community 必须分开标注，UNCERTAIN 就标 UNCERTAIN）；
- 知识卡/字典中的 claim 不携带来源与置信度。

### 2.3 ontology 与 string vocabulary 分离（RQ5 教训升格为架构原则）

不修 `dynamic_programming` vs `discrete_recurrence` 这一个 bug，而是规定模型本体层级：

```text
Concept → Mechanism → Model Family → Model → Method → Solver → Implementation
```

例：`recursive optimization → optimal substructure → dynamic programming → Bellman recurrence
→ backward induction → custom DP solver → Python implementation`。

- Evaluator 不得问 `model_family.primary == "dynamic_programming"`；
  应问 **该模型的 structural concept / mechanism / family 是否属于预注册 taxonomy**。
- 生成侧与评分侧必须共享**单一受控词表**（`catalog/model_families.yaml`，P0 工程项②），
  族命中判定为 `primary OR secondary OR mechanism OR solver`。

### 2.4 三层层的知识分离

- Knowledge claim ≠ empirical fact（BZD 教训）
- Model Knowledge ≠ Model Capability（K001：知识注入 Δ=+2.14 CI 触 0）
- Schema Validity ≠ Mathematical Correctness（R1）
- Evidence Recording ≠ Evidence of Correctness（R4 反例：2019_C 评分饱和）
- Formalization ≠ Truth
- More Context ≠ More Knowledge（K001 Sham=+3.42 > Δ_K：Sham 假说未排除）

---

## 3. 路线图（审计后压缩为四段）

```text
P15  Research Instrument（✅ 已收口：K001 CLOSED，negative result 按决策门记录）
  ↓
P0   Real Execution（进行中：result 占位符治理 → 词表收敛 → Code Interpreter adapter）
  ↓
K002 Representation Effect（DRAFT v0.3：3 臂主实验 + block≥6 + L3/L4 终点）
  ↓
P16+ Capability Validation（Evidence / Critic / Verification / Replay 逐项 ablation）
```

**不是**：P15 → 继续加 schema → 继续加 Skill → 继续加 Agent。
**是**：STOP BUILDING ABSTRACT INFRA → MAKE MODEL EXECUTE → PRODUCE REAL RESULT
→ BUILD REAL EVIDENCE → BLINDLY EVALUATE → SHOW REPRESENTATION IMPROVES MODEL CONSTRUCTION。

### 3.1 成功标准（写死）

只有当 K002 证明 `MODEL_IR + Validation > Free Text`，且排除以下解释：
更多 token / 更多上下文 / 更长 prompt / evaluator 偏好 / 写作改善——
**且提升确实是 Model Construction Quality**，LinHoMo 才有资格宣称：
"我们不是更复杂的 agent workflow，而是能改变数学建模能力边界的 modeling runtime。"

---

## 4. 三项目哲学定义（审计后正式措辞）

| 项目 | 哲学 | 已解决 | 未证明 |
|---|---|---|---|
| BZD | 将优秀数学建模者的隐性评审知识显式化 | What should a good model look like? | Does giving this knowledge improve model construction? |
| MathModelAgent | 将数学建模团队的工作流自动化 | How can an Agent complete the modeling workflow? | What exactly is the model, and how does the system know it is correct? |
| LinHoMo | 将建模过程变成可表示、可执行、可验证、可归因、可重放的研究状态 | How should modeling exist as a scientific computational process? | This representation actually produces better models. |
