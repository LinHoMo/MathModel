# STRATEGIC_VERDICT — 最终架构与战略审查裁决
> Version: v1.0 | Status: Frozen | Updated: 2026-09-10

> 日期：2026-09-10 ｜ 审查方法：8 代理代码审计 + GitHub 最新仓库研究 +
> 三轮自我反驳 + 真实执行验证 ｜ 状态：**STRATEGY FROZEN**

---

## 0. 一句话裁决

**LinHoMo 应该是一个 Constructor-Independent、Runtime-First、Evidence-First
的数学建模 Lifecycle Runtime，不是一个 Agent 系统。**

MathModelAgent / Pi / Claude / OpenAI Agent 等外部 Agent 是可替换的
Constructor/Worker；LinHoMo 的不可替代资产是 Artifact Registry + Evidence
Graph + Execution Substrate + Validation Gates + Model Lifecycle State Machine。

---

## 1. 项目最终定位

### LinHoMo 应该是什么

**E. "Model Construction Runtime + Evidence Substrate + Evaluation Gate"**

不是 A（端到端 Agent），不是 B（纯 Runtime），不是 D（纯 Benchmark），而是：

```
External Constructors (可替换)
    ↓ Constructor Protocol (MODEL_IR + Code + Intent)
LinHoMo Runtime (不可替换)
    ↓ Execution Substrate (真实 subprocess)
    ↓ Fidelity Layer (L2: MODEL_IR ↔ Code)
    ↓ Evidence Graph (provenance chain)
    ↓ Validation Gates (45 项 + Evidence Gate)
    ↓ Model Lifecycle State Machine
    ↓ Revision Engine (failure → diagnosis → draft → re-execution)
```

### 为什么不自己做 Constructor

1. **K001/K002/K003 实验证明**：结构化表示的收益不在"模型构造文本质量"（L2
   实际为负），而在"验证证据的可追溯性与完备性"（L4 大幅正）。这说明 LinHoMo
   的核心价值在 Runtime/Evidence 层，不在 Constructor 层。

2. **外部 Agent 生态已经很强**：MathModelAgent（3737 stars）有桌面应用 + E2B
   沙箱 + 多 LLM 支持；Claude Code 有长时自主编码能力；OpenAI Code Interpreter
   有可靠沙箱执行。自己做一个同级 Constructor 的边际收益极低。

3. **"Agent Brain"战略已被实验否证**：K001 知识注入 Δ=+2.14 CI 触 0，方法族
   命中率仅 22%。知识卡作为 Constraint/Prior 的定位正确，但作为"让 Agent 更会
   建模"的手段无效。

---

## 2. 四张清单

### CORE（必须自己做，不可委托）

| 资产 | 为什么不可替代 |
|---|---|
| Artifact Registry | 所有产物的单一真源，不可委托给外部 |
| Evidence Graph | 溯源链，核心可信度保证 |
| Execution Substrate | 真实 subprocess 执行，状态只来自执行 |
| Validation Gates | 质量控制不可委托，外部 Agent 不能自认证 |
| Model Lifecycle State Machine | 状态推进只由系统事实驱动 |
| Replay / Reconcile | 确定性重放 + 状态对账 |
| Hash Chain Verification | 篡改检测 |
| Modeling Knowledge Governance | 知识约束 evaluation 不约束 creativity |
| Fidelity Layer (L2) | MODEL_IR ↔ Code 语义映射校验 |
| Failure Diagnosis | 机械归因，不依赖 LLM |
| Revision Engine | 失败 → 诊断 → 修订草案 → 重执行 |

### OPTIONAL（可以自己做，也可以复用）

| 资产 | 说明 |
|---|---|
| Reference Constructor | 最小参考 Constructor，用于 benchmark baseline |
| Knowledge Card System | 方法卡体系（已有 24 张，可扩展） |
| Experiment Planner | 实验规划器 |
| ~~Paper Templates~~ | ~~LaTeX 模板（标准格式）~~（已随 v3.2.2 论文链删除） |
| E2E Metrics | 八项能力指标 |

### EXTERNAL（应该复用外部）

| 能力 | 外部来源 |
|---|---|
| Sandboxed Code Execution | E2B / OpenAI Containers / Docker |
| Multi-LLM Provider Routing | litellm 或类似 |
| Web Search | Tavily / Perplexity |
| ~~Paper Formatting~~ | ~~标准 LaTeX 模板~~（已随 v3.2.2 论文链删除） |
| Desktop App UX | 参考 MathModelAgent 架构 |

### FORBIDDEN（绝对不做）

| 禁止事项 | 原因 |
|---|---|
| 自研通用 Agent Brain | 实验否证，外部 Agent 已足够强 |
| 无限增加 Agent/Skill 数量 | infra 不冒充 capability |
| 让 Agent 写 ExecutionResult | Agent Claim ≠ System Fact |
| 让 Agent 声称 PASS | 验证不可委托 |
| 把 Schema 当能力 | schema 是基础设施不是能力 |
| 把 Workflow 当能力 | workflow 是编排不是能力 |
| 把论文质量当核心 capability | 论文是投影不是建模 |
| 经验数字进入确定性评分 | 6.81% 教训 |
| Fork 外部 Agent 项目 | Adapter > Fork |
| 为了 benchmark 调参到好看 | 诚实 > 好看 |
| 用文本盲评冒充数学正确性 | 需要真实执行验证 |
| 把 Organizer 报告当事实 | Agent Claim ≠ System Fact |
| 把测试通过当生产路径接通 | 测试存在 ≠ 生产调用 |

---

## 3. 实验证据支撑

### K001 Knowledge Negative (Δ=+2.14, CI 触 0, p=1.0)

- 知识注入未产生可测量的建模能力提升
- 方法族命中率仅 22%，知识卡 barely 影响模型选择
- **结论**：知识卡作为 Constraint/Prior 定位正确，但当前实现无法证明
  "knowledge → better construction"

### K002 Representation Negative (S−F MCQ = −4.85, 显著负)

- 结构化 MODEL_IR 在无执行产物时**显著降低** MCQ 分数
- 原因：L3 层格式不对称——JSON 暴露"无执行证据"，文本可叙述性声称
- **结论**：这不是"结构化损害能力"，而是测量结构问题。但证明了一点：
  纯表示层（无执行）不产生价值

### K003 Execution Positive (S−F MCQ = +3.76, 显著正)

- 构造+执行一体化后，结构化表示产生正效应
- 但正效应**全部来自 L4 验证层**，L2 构造层实际为负
- **结论**：Runtime/Evidence 层的价值被证实；Constructor 层的价值被否定
- SV−F VAL = +39.92：验证计划的结构化大幅提高验证完备性

### 三实验综合结论

```
"结构化表示本身 ≠ 建模能力"
"验证义务 + 执行闭环可能比表示格式更重要"
"Runtime/Evidence 是 LinHoMo 的真正护城河"
```

---

## 4. 三轮自我反驳

### Round 1：证明当前架构为什么合理

- 三层架构（Epistemic/Execution/Evaluation）逻辑清晰
- Artifact Registry + Evidence Graph 提供真实溯源
- Execution Substrate 确保真实执行（status 只来自 subprocess）
- Validation Gates 机械判定，不依赖 Agent 声明
- Replay/Reconcile 支持确定性重放
- Agent Authority Model 基本正确（Agent 不能写 EXEC/VR/Evidence）

### Round 2：假设当前架构是错误的，攻击它

**攻击 1：4 个 modeling 模块是死代码**
- `knowledge_guided.py`, `diagnosis.py`, `comparison.py`, `revision.py` 在生产路径
  中零调用。这些是设计了但从未接入的模块。说明架构设计与实现之间存在断裂。

**攻击 2：Fidelity Layer 未集成**
- `fidelity.py` 只在 `codegen.py` CLI 中被调用，生产 DAG 中的 `handlers.py`
  从未调用。L2 Fidelity（MODEL_IR↔Code）是 LinHoMo 独有指标，但实际未执行。

**攻击 3：Engine Validators 未使用**
- `session.py:96` 创建 `WorkflowEngine` 时未传 `validators=` 参数。engine 的
  validator hook 机制从未在生产中使用。

**攻击 4：硬编码经验常数**
- `_decision_confidence` 使用 0.25/0.7/0.95/0.8/0.6 等无溯源的经验常数
- `integrity_gate.py` 使用 15%/20/0.999/30%/10% 等经验阈值
- 这些伪装成确定性评分，实际是"formalized false authority"

**攻击 5：K003 L4 正效应是循环论证**
- SV臂强制产出 `validation_plan.json`（5个必填字段），rubric 的 L4 维度
  恰好评这些字段。"要求产出 A → 评 A 是否存在 → A 存在 → 得分高"是同义反复

**攻击 6：κ 值持续低于项目自身阈值**
- K002 κ=0.4345, K003 κ=0.260，均 < 0.6 阈值
- 项目不断合理化低 κ（"方向一致"、"可归因"），但这是降低标准

### Round 3：综合裁决

**保留的设计**：
- 三层架构（Epistemic/Execution/Evaluation）
- Artifact Registry + Evidence Graph
- Execution Substrate（LocalPythonAdapter）
- Validation Gates（E1-E9）
- Replay/Reconcile
- Agent Authority Model（Agent Claim ≠ System Fact）
- Knowledge Governance（Constraint/Prior, not Answer）
- WorkflowEngine（DAG 调度 + 反馈环）

**必须修复的设计**：
- 4 个 dead code 模块必须接入生产路径或删除
- Fidelity Layer 必须集成到生产 DAG
- Engine Validators 必须启用或删除
- 硬编码经验常数必须标注 provenance 或移除
- κ 值必须达到 0.6 或承认测量限制

**应该删除的设计**：
- `_maybe_execute_experiment`（dead code）
- `codegen.py` 的独立路径（与 `handlers.py` 重复）
- `comparison.py` 的第一个循环（dead loop）

---

## 5. 最终回答

### Q1: LinHoMo 应不应该集成 MathModelAgent?

**是，作为 Constructor Adapter，不是核心 Agent。**

MathModelAgent 提供：模型构造 + 代码生成 + 执行（E2B/Jupyter）+ 论文生成。
LinHoMo 提供：Artifact Registry + Evidence + Validation + Lifecycle。

集成方式：MathModelAgent → Constructor Protocol → LinHoMo Runtime。

### Q2: 应不应该集成 Pi?

**否。** Pi 是消费级聊天机器人，无数学建模能力，无代码执行，无 API。
完全不适合集成。

### Q3: 是作为核心 Agent，还是 Adapter?

**Adapter。** 所有外部 Constructor（MathModelAgent, Claude Code, OpenAI Agent）
通过统一 Constructor Protocol 接入，输出 MODEL_IR + Code + Intent。

### Q4: 是否需要自研 Constructor?

**需要一个最小 Reference Constructor**，仅用于：
- Benchmark baseline
- Regression test
- Local demo
- Controlled experiment

不做几十个 Agent。只做一个最小的、确定性的、LLM-free 的参考实现。

### Q5: 是否应该继续扩 Agent/Skill?

**否。** 应该冻结 Agent/Skill 数量，转向：
- 将 4 个 dead code 模块接入生产路径
- 将 Fidelity Layer 集成到生产 DAG
- 提升实验的 κ 值到 0.6
- 设计 Constructor-independent benchmark

### Q6: 当前 Runtime 是否已经足够?

**基本足够，但有关键缺口**：
- Fidelity Layer 未集成
- Engine Validators 未启用
- 4 个 modeling 模块是死代码
- 硬编码经验常数需要 provenance

### Q7: 下一阶段最重要的 3 个工程任务

1. **集成 Fidelity Layer**：将 `fidelity.py:verify_fidelity` 接入 `handlers.py`
   的 `do_model_execution` 节点
2. **接入 4 个 dead code 模块**：`diagnosis.py` → revision flow;
   `comparison.py` → model selection; `knowledge_guided.py` → candidate generation;
   `revision.py` → revision draft
3. **Constructor Adapter 协议**：设计 `core/runtime/constructors/protocol.py`

### Q8: 下一阶段最重要的 3 个科学实验

1. **Constructor-Independent Benchmark**：同一 Runtime + 不同 Constructor，
   区分 Agent 能力 vs Runtime 增益
2. **Fidelity Measurement**：测量 MODEL_IR↔Code 的 L2 Fidelity 在真实
   构造中的分布
3. **End-to-End Competition Test**：完整 pipeline 在真实竞赛题上的表现

### Q9: 哪些现有模块应该删除?

- `handlers.py:1423` `_maybe_execute_experiment`（dead code）
- `engine.py:281` 第一个 `unblock` 定义（被 line 349 覆盖）
- `comparison.py:22-26` 第一个循环（dead loop）
- `codegen.py` 的独立路径（与 handlers 重复）

### Q10: 哪些模块应该冻结?

- Artifact Registry
- Evidence Graph
- WorkflowEngine
- WaveExecutor
- ProjectState
- Replay/Reconcile
- All validators (evidence_gate, hash_chain, integrity_gate)

### Q11: 哪些模块应该重构?

- `handlers.py`（1737 行，需要拆分）
- `knowledge_guided.py`（接入生产路径）
- `diagnosis.py`（接入 revision flow）
- `fidelity.py`（集成到 production DAG）

### Q12: LinHoMo 最终真正的核心竞争力是什么?

**Constructor-Independent Model Lifecycle Runtime**

- 不依赖特定 Agent/LLM 的模型生命周期管理
- 真实执行闭环（status 只来自 subprocess）
- 可追溯的 Evidence Graph
- 机械验证（45 项 + E1-E9 Evidence Gate）
- 确定性 Replay/Reconcile
- Model Lineage（M1 → FAIL → M2 → PASS → revision_of）
- 结构化 MODEL_IR（独有：没有任何外部系统有等价物）

如果明天 MathModelAgent 比 LinHoMo 自己的 Constructor 强 10 倍，
LinHoMo 仍然有价值——因为 LinHoMo 管理的是"模型如何被证明正确"，
而不是"模型如何被构造"。


---

## 附录：引用文件路径映射（审计可追溯性）

本文档中的模块引用使用简写（handlers.py:837 表示 837 行）。完整真实路径如下（已逐行核对）：

| 简写 | 真实路径 | 核对结果 |
|---|---|---|
| handlers.py | core/runtime/execution/handlers.py（1737 行） | L817/837/843/876/1423 全部吻合 |
| engine.py | core/runtime/execution/engine.py（417 行） | L96/281/349 吻合（L281/L349 重复 unblock 属实） |
| session.py | core/runtime/execution/session.py（298 行） | L96 吻合 |
| idelity.py | core/runtime/execution/fidelity.py（227 行） | 存在 |
| codegen.py | core/runtime/execution/codegen.py | 存在 |
| integrity_gate.py | core/validators/modules/integrity_gate.py（428 行） | L118/161/172/255/345 全部吻合 |
| indings.py | core/runtime/writing/findings.py（212 行） | L121/147/157 吻合 |
| selection.py | core/runtime/modeling/selection.py（141 行） | L60/80/108/120 吻合（chosen=recs[0] 属实） |
| comparison.py | core/runtime/modeling/comparison.py | L22 吻合 |
| knowledge_guided.py / diagnosis.py / 
evision.py / candidates.py / model_ir.py | core/runtime/modeling/ | 存在（生产零调用见正文） |
