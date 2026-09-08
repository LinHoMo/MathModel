# Three-Layer Architecture — 三层架构与治理门禁（2026-09-09 P0-E 跃迁后 v3）

> **版本演化**：v1（2026-09-06）"Agent Brain 主战场"旧三层已废弃；v2（审计后）确立
> Epistemic/Execution/Evaluation 三层；**v3（P0-E 完成后）**：定位升级为
> **最小可执行 Mathematical Modeling Runtime**，核心对象明确为 **Model Lifecycle**。
>
> **上游裁决**：`research/REPOSITORY_AUDIT/FINAL_REPORT.md` + `CROSS_REPO_AUDIT.md`（BZD=Knowledge System、
> MathModelAgent=Execution System、LinHoMo=Epistemic System；三者互补非竞争）+ 用户战略裁决
> （2026-09-09 两轮：P0-E 执行闭环 + 本文件五级正确性/三状态/Fidelity）。

---

## 0. 一句话定位（写死，v3 更新）

> **LinHoMo 已形成最小真实执行闭环（P0-E，commit ad917d2）——Model Artifact 可以进入
> 计算世界并产生带身份/来源/生命周期的 ExecutionResult。但这是"能运行模型"，
> 不是"能可靠地运行一个模型"，更不是"因此更会建模"。**
>
> **边界（必须严格分开）**：P0-E 证明的是"Model Artifact 可以进入真实执行闭环"；
> **没有证明"系统因此更会建模"**。没有任何被审计仓库（含 LinHoMo）已被实验证明
> 拥有更强的数学建模能力。

三仓库真实层次：

| 仓库 | 核心对象 | 系统类型 | 回答的问题 | 缺失 |
|---|---|---|---|---|
| BZD | Knowledge / Review Rule | Knowledge System | "怎么评价" | execution + causal capability evidence |
| MathModelAgent | Agent / Workflow / Code Execution | Execution System | "怎么做完" | model semantics + epistemic state |
| **LinHoMo** | **Model Artifact / Execution / Evidence / State** | **Model Lifecycle Runtime** | "怎么证明" | Model→Code 语义保真；Execution→Validation→Model Correctness |

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
- **Execution Status ≠ Model Status ≠ Evidence Status**（P0-E 后新铁律，见 §2.6）

### 2.5 Model Lifecycle（v3 核心对象，写死）

> LinHoMo 的核心不是 Agent / Workflow / MODEL_IR，而是 **Model Lifecycle**：

```text
Problem → Model Construction → Model Artifact → Implementation → Execution →
Evidence → Validation → Evaluation → Model Revision → New Model Version
```

execution_result 一等 artifact（EXEC）+ `implemented_by`（model→code）与
`executed_by`（result→execution_result）两条关系使 **implementation 与 execution
明确分离**：模型不变、实现变、环境变、结果变——真实的实验谱系（lineage）由此成立。

### 2.6 三状态分离铁律（"真执行 + 假模型"防线）

**execution_status = success 绝不推出 model_status = correct。** 下一阶段最危险的
风险是"真执行 + 假模型"：代码跑通（success）但模型数学假设错误/变量语义错误/
目标函数错误/约束遗漏/单位错误/边界错误/代码与模型不一致。

完整链条（任何一步失败不得越级）：

```text
Code executed successfully
  → ExecutionResult valid
  → Evidence generated
  → Validation performed
  → Model passes validation
  → Claim supported
```

### 2.7 五级正确性（L0–L4，替代单一 validator=PASS）

| 级 | 回答 | 含义 |
|---|---|---|
| L0 Syntax | Artifact 合法吗？ | schema/结构校验 |
| L1 Execution | 代码跑了吗？ | execution_result.status（真实执行） |
| **L2 Model Fidelity** | 跑的是声明的模型吗？ | MODEL_IR 声明 ↔ 代码语义映射一致（目标/约束/变量/方程） |
| L3 Mathematical Validity | 数学推导/模型逻辑正确吗？ | 推导、量纲、边界、一致性 |
| L4 Empirical Adequacy | 现实数据/实验支持它吗？ | 数据拟合、预测、可验证性 |

**Model-to-Execution Fidelity（L2）是 LinHoMo 独有核心指标**：例——MODEL_IR 声明
`objective=minimize total cost; constraints x+y≥10`，代码却 `minimize(x+y); x+y≤10`：
execution success=1，但 model fidelity=0。K002 起该指标进入测量。

### 2.8 Replay 定义（P0-E4）

- **不是**"再次运行代码"（rerun）。
- **是**"在相同声明环境下重建一次 execution，并报告偏差"（reproducibility）。
- `environment_hash` 将演化为 **Execution Environment Manifest**（random seed /
  package version / OS / floating-point / external data / current time / network /
  nondeterministic solver），否则 replay 只是 rerun。
- 支撑字段已就绪：execution_id / code_hash / environment_hash / inputs / outputs /
  started_at / finished_at / provenance。

---

## 3. 路线图（P0-E 后定稿，用户 2026-09-09）

```text
K001 Knowledge Negative（✅）
  → Repository Audit（✅）
  → P0-E Execution Runtime（✅ ad917d2：真实执行闭环）
  → P0-E4 Replay / Provenance（🔄 本轮）
  → Validation（Execution → Model Correctness）
  → Code Generation（MODEL_IR → code，语义保真——第二扇门）
  → K002 Dry Run → Measurement Gate（五 Gate）→ K002 Frozen
  → Representation Effect → P16
```

**两扇门（打通后才算"能可靠地运行一个模型"）**：
1. **Model → Code 语义保真**（L2 Fidelity）：生成代码执行的是 MODEL_IR 声明的模型。
2. **Execution → Validation → Model Correctness**（L3/L4）：执行成功 → 验证 → 模型正确。
再往后 K002 回答：结构化 Model Artifact 是否真的让系统构造出更好的数学模型。

**主线（死守）**：`Representation → Execution → Evidence → Validation → Capability`

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
