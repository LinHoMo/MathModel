# P1-VS-001 决策记录：Executable Model Construction Loop（2026-09-09）

> 来源：用户对三仓库 GitHub 现状 + P15/P0-E/Gap Audit 合并复核后的最终指令
> 状态：**已批准执行** · K002 继续暂停（Runtime 成熟前不做测量）
> 核心：**不要再扩展架构。让 Model Construction Loop 第一次被真实数学模型踩起来。**

## 一、最终判断

- 三仓库定位（用户结论）：
  - BZD = Epistemic / Reviewer System（知识、评审、适配）→ **knowledge/reviewer substrate，不复制**
  - MathModelAgent = Agentic Production Pipeline（Agent 编排、Code Interpreter、论文生产）→ **可接入的 model-construction executor，不复制**
  - LinHoMo = Scientific Modeling Runtime（Artifact/Evidence/DAG/Replay/可审计状态）→ **独立于任何 Agent 的科学运行时**
- LinHoMo 最大危险：**架构已比能力超前**（infra 不冒充 capability 反转为工程纪律）
- 下一步 = **Vertical Slice First**：真实数学建模闭环 M1→RUN1→FAIL→REVISION→M2→RUN2→PASS

## 二、P1-VS-001 目标

> 给 LinHoMo 一道真实数学建模题：产生 MODEL_IR → 生成代码 → 运行 → 真实数值 → 验证 → 发现问题 → 修改模型 → 再运行；全过程可从 Artifact/Evidence Graph/Replay 复原。

### 7 条验收（硬标准）

1. [ ] Problem 有稳定 Artifact ID
2. [ ] M1 是真实 MODEL_IR（Executable Model Specification），而非 model_family 标签
3. [ ] Code 由 M1 生成并实际执行
4. [ ] ExecutionResult 含真实数值输出
5. [ ] Validation 能基于真实数值判 FAIL
6. [ ] M2 与 M1 存在 revision lineage（supersedes/revision_of 边）
7. [ ] Replay 能从 M1 重现 RUN1/RUN2

## 三、MODEL_IR 三层（一刀切：从 Model Description 升级为 Executable Model Specification）

- **L1 Semantic Model**：entities / variables(domain) / parameters——"现实问题是什么"
- **L2 Mathematical Model**：objective(sense/expression) / constraints / nonnegativity——"数学上是什么"
- **L3 Computational Model**：solver(family/backend/method) / execution(language/timeout)——"计算机怎么算"

现实 → 数学 → 计算。禁止只有 model_family 标签的"伪 MODEL_IR"。

## 四、Codegen 契约（反 MathModelAgent：固定 ABI，不是随便写 notebook）

```
input.json → run_model.py → output.json → ExecutionResult
```

Generated Code 必须满足固定 ABI：`def solve(inputs) -> outputs`。ExecutionAdapter 才有意义。

## 五、ExecutionResult → Computational Evidence

status 之外必须携带：outputs（真实数值）、checks（constraint_violation_max / variable_domain_violation）、diagnostics（solver_status / iterations）。exit code=0 ≠ 模型正确。

## 六、Validation（LinHoMo 区别于 MMA 之处）

- L0 Syntax → L1 Execution → L2 Mathematical（约束满足）→ L3 Empirical（参数稳定）→ L4 Robustness（敏感性）
- ValidationResult{execution_valid, mathematical_valid, empirical_valid, robustness}；全过才允许 ModelState=VALIDATED
- 禁止"LLM 说结果看起来合理"

## 七、Revision（Agent Loop 的正确语义）

- **Model Revision** ≠ retry/fix：代码错与模型错必须区分
- M2 supersedes M1（revision lineage 边），**禁止 overwrite model.json**
- Evidence Graph 最终形态：Problem→motivates→M1→implements→C1→executed_by→R1→produces→E1→checked_by→V1→FAIL→RV1→M2→…→V2→PASS

## 八、里程碑（M3/M4 本轮不做）

| 里程碑 | 内容 | 本轮 |
|---|---|---|
| M0 | Executable Model Contract：手写 LP 模型跑通 runtime | ✅ 包含 |
| M1 | One Real Problem：仓库内真实题 + MODEL_IR → codegen→exec→valid→evidence | ✅ 包含 |
| M2 | Model Revision：故意 FAIL → Revision → M2 → PASS（首个智能建模闭环） | ✅ 包含 |
| M3 | Candidate Competition（Arena 基于 Evidence 选择，非 recs[0]） | 下一轮 |
| M4 | Knowledge-guided Construction（接 BZD knowledge → 此时 K002 才有意义） | 下一轮 |

## 九、边界（硬性禁止）

- ❌ 新增 Agent / Skill / 知识库 / 论文模块 / 前端 / 无关 schema
- ❌ 架构扩展（Gap Audit 已列出缺口，只做闭环必需的最小修改）
- ❌ core 内 LLM 执行器（LLM-free 铁律；MODEL_IR/Code 由外部 Model Constructor——Human/LLM/MMA——产出）
- ❌ formalized false authority（BZD 经验数值不得进 runtime 当 truth；只吸收 applicability/assumptions/failure modes/validation obligations）

## 十、吸收关系（本轮背景）

```
Model Constructor（Human / GPT / Claude / MMA / BZD-agent）
        │ proposes MODEL_IR（三层）
        ▼
LinHoMo Runtime（Execute → Validate → Evidence → Revise → Replay）
```

- MathModelAgent = 未来可接入的 ExecutionAdapter（本地 Jupyter / E2B / Daytona），不 fork
- BZD = knowledge/reviewer substrate（M4 再接）

## 十一、验收后

- P1-VS-001 PASS → 才进入 M3（Candidate Arena 基于 Evidence）/ M4（知识引导）/ K002（测量）
- K002 是 Runtime 成熟后的 capability experiment，不是驱动 Runtime 设计的因素
