# Capability Validation Roadmap — 数学建模能力验证路线图

> 生成日期：2026-09-08 | 基于：Measurement Recovery Report + 6 个子代理审计结果
> 原则：先证明尺子是对的，再测 Agent。先单题深挖，再扩题。先跨题验证，再谈泛化。最后才谈科研迁移。

---

## 1. 当前状态（Phase 0–4 完成）

| 维度 | 状态 | 关键指标 |
|---|---|---|
| 输入真实性 | ✅ 恢复 | 5 道题真实题面，0 BLOCKED，sha256 验证 |
| 执行真实性 | ✅ 诊断 + Gated | 零 LLM 根因确认，execution_gate.py 实现，旧 B0 正确判定 INVALID |
| Artifact 完整性 | ✅ Gated | 三层 gate 设计，L1+L2 已实现，占位符黑名单 |
| 评估器有效性 | ✅ 修复 | 3 P0 bug 修复，pytest 781/11 零回归，Model Construction Evaluator 四层重设计 |
| 能力本体 | ✅ 重建 | 11 项能力地图，25 个可测量 FM，L1-L4 评分细则，5 个 Problem Card |
| 真实 LLM 执行 | ⚠️ by-design 外部化 | core/runtime 永远 LLM-free（设计要求），认知工作由外部 Agent 完成；需 6b 外部接口实现后由外部 Agent 执行 |
| 真实能力测量 | ❌ 缺失 | 无外部 Agent 真实执行产物，无法测量 Agent 真实建模能力；6c 后获得 |

**核心结论**：测量仪器已恢复可信，但执行管线不产生真实 LLM 输出。下一步的瓶颈不是"加能力"，而是"接入真实 LLM 执行"。

---

## 2. 路线图总览

```
Phase 5: Measurement Recovery          [DONE] 测量仪器恢复
    ↓
Phase 6: Fresh B0                      [NOW]  synthetic自检 → 外部接口 → 真实执行
    ├── 6a: Measurement Chain Self-Test  [IN PROGRESS]  SYNTHETIC，只验证测量链路
    ├── 6b: External-Agent Execution IF  [NEXT]  外部Agent执行接口（harness侧，零LLM）
    └── 6c: Real B0-R3 (external_agent)  [AFTER 6b]  外部Agent真实执行，第一个可信baseline
    ↓
Phase 7: Cross-family Validation        [AFTER 6c] 跨模型家族验证
    ↓
Phase 8: Targeted Intervention          [AFTER 7]  定向干预实验
    ↓
Phase 9: Generalization                 [AFTER 8]  泛化测试
    ↓
Phase 10: Research Transfer             [AFTER 9]  科研迁移
```

**架构边界**：Harness ≠ Agent。core/runtime 永远 LLM-free by design。认知工作由外部 Agent 完成，harness 提供测量与编排。

---

## 3. Phase 6: Fresh B0（当前阶段）

### Entry Criteria
- ✅ 输入真实性 PASS（5 道题真实题面）
- ✅ Execution Authenticity Gate 实现并验证
- ✅ Artifact Integrity Gate L1+L2 实现
- ✅ Evaluator P0 bug 修复
- ✅ Capability Ontology 重建
- ⏳ Mock LLM executor 实现（进行中）

### 6a: Measurement Chain Self-Test（测量链路自检，SYNTHETIC）

> **⚠️ SYNTHETIC / NOT A CAPABILITY RESULT**：本阶段使用确定性 synthetic 产物，只用于验证 gate+evaluator 链路本身工作。报告中禁止出现任何"Agent 能力"措辞。

**目标**：用 mock/synthetic executor 生成非空 artifact，跑通"输入→执行→artifact→gate→evaluator→metrics"全链路，证明测量仪器工作正常。**不证明任何 Agent 真实能力。**

**架构边界**：Harness ≠ Agent。core/runtime 永远 LLM-free by design。DefaultNodeExecutor 是 dry-run/synthetic 演练器，不是 Agent，其产物不代表任何建模能力。

**工作内容**：
- 实现 `mock_llm_executor.py`（research-layer，确定性规则生成非空 artifact，全部标记 `provenance.mock_execution=true`, `executor_type=synthetic`）
- 创建 `projects/p151-2024a-r2/` 项目
- 生成 16 个非空、结构有效的 artifact（引用 2024_A 真实变量和约束）
- 运行 execution_gate.py → 验证 Artifact Integrity 在非空 artifact 上 PASS
- 运行 e2e_metrics.py → 验证 evaluator 在非空 artifact 上输出可测量指标（不是全部 n/a）
- 生成 B0-R2 报告，**头部明确标注 SYNTHETIC / NOT A CAPABILITY RESULT**

**Exit Criteria**：
- 16 个 artifact 全部非空且包含必需字段
- execution_gate Artifact Integrity PASS（或大部分 PASS）
- e2e_metrics 输出可测量的指标（不是全部 n/a）
- B0-R2 报告明确标记为 SYNTHETIC，不声称 Agent 真实能力
- 所有 artifact 的 `executor_type=synthetic`
- pytest 781/11 不下降

**不做的事**：
- 不声称 synthetic 结果代表 Agent 真实能力
- 不修改 core/ 架构
- 不在 core 里接入 LLM
- 不把 synthetic 产物用于能力结论或干预决策

### 6b: External-Agent Execution Interface（外部 Agent 执行接口，NEW）

**目标**：设计并实现让仓库外的外部 Agent 能在 DAG 下干活、并把真实产物合规登记进来的契约 + 适配器。harness 侧做 schema 校验 + non-empty/structural/semantic gate + hash 绑定 + 溯源落盘。**不含任何 LLM 调用。**

**架构边界**：harness 提供测量与编排，cognition 在外部。真正的认知工作（读题/建模/求解/写结论）由外部 Agent（Doubao/GPT/Claude/人）完成。

**工作内容**：

1. **执行类型区分（executor_type）**：
   - `dry_run` / `synthetic`：DefaultNodeExecutor 确定性桩 / mock executor，只用于流程演练和测量链路自检；gate 对 capability scoring 自动判 INVALID/SYNTHETIC，永远不允许进入能力结论
   - `external_agent`：产物由仓库外真实 Agent 产出并登记，带完整溯源
   - 在 run record 和 artifact metadata 中强制标注 `executor_type`

2. **ExternalArtifactManifest 契约**：每个外部 Agent 提交的节点产物必须附带：
   - executor_type=external_agent, agent_identity, model_version
   - input_sha256（与冻结题面 hash 绑定，题不对直接拒）
   - node_id / DAG 位置 / prompt_or_skill_version / artifact_schema_version
   - started_at / finished_at / latency（真实 >0）/ submitted_at
   - payload（非空、过 schema、过 artifact integrity 三层 gate）
   - 可选：reproducibility（seed, temperature, parameters）

3. **提交入口（CLI）**：`register_external_artifact.py --project <项目> --manifest <path> --input-sha256 <hash>`
   - 校验 manifest + input hash 绑定
   - 将 artifact 写入 registry.json（正确格式）
   - 更新 run record（executor_type=external_agent）
   - 更新 evidence_graph 和 decision_log
   - 退出码：0=成功, 1=校验失败, 2=hash 不匹配, 3=其他错误
   - **外部 Agent 不得直接手写 registry.json**

4. **Execution Authenticity Gate 判据更新**：
   - 对 external_agent：校验 agent_identity/model_version 非空、latency>0、input_sha256 匹配、artifact 非空且 schema-valid、evidence 绑定真实
   - 对 synthetic/dry_run：一律标注 SYNTHETIC，capability scoring 自动 INVALID，报告头部明确标记 "SYNTHETIC / NOT A CAPABILITY RESULT"
   - 对 executor_type 缺失：标记 UNKNOWN，警告无法确认执行真实性

**Entry Criteria**：
- 6a Measurement Chain Self-Test 完成，测量链路验证通过
- 现有 run record / artifact registry 格式已理解

**Exit Criteria**：
- `executor_type` 字段在 run record 和 artifact metadata 中实现
- ExternalArtifactManifest 数据类 + JSON Schema + 示例 manifest 完成
- `register_external_artifact.py` CLI 可用，退出码正确
- `mark_executor_type.py` 可批量标注旧项目
- execution_gate.py 判据更新：synthetic 项目返回 SYNTHETIC 标记 + 退出码 2
- 旧 B0（p151-2024a）标注为 dry_run，mock B0-R2（p151-2024a-r2）标注为 synthetic
- 接口文档 `EXTERNAL_AGENT_EXECUTION_INTERFACE.md` 完成
- pytest 781/11 不下降

**不做的事**：
- 不在 core/runtime 里 import openai/anthropic 或内嵌 LLM 执行器
- 不新增 `--llm` 标志或 LLM provider 配置
- 不修改 v3.1.x core architecture（除非确属 core 缺陷的 minimal patch）
- 不把 synthetic 产物用于能力结论

### 6c: Real B0-R3（真实能力基线，由外部 Agent 执行）

**目标**：由**外部 Agent 作为执行体**真正去做 2024_A"板凳龙"——按 SKILL/role 指令逐节点真实读题、分解子问题、建模、求解、验证，通过 6b 的接口把真实 artifact 登记进 harness，再由 harness 的 gate/evaluator 测量，得到**第一个真实可信 baseline**。

**执行体**：外部 Agent（Doubao / GPT / Claude / human），不在 harness 内部。run record 中 `executor_type=external_agent`、`agent_identity` 如实记录。

**工作内容**：
- 创建 `projects/p151-2024a-r3/` 项目（使用真实板凳龙题面）
- 外部 Agent 按 DAG 节点逐节点执行：
  1. problem_analysis：读题、分解子问题、识别变量/参数/约束
  2. model_selection：选择合适的方法家族（与运动学/几何问题匹配）
  3. model_construction：建立数学模型（objective/constraints/variables/mechanism/assumptions/equations）
  4. experiment@Q001：设计并执行求解实验
  5. evidence_build：建立证据链
  6. paper_sections@Q001：撰写论文节
  - （其余节点可由 harness 确定性部分或外部 Agent 补充）
- 每个节点产物通过 `register_external_artifact.py` 登记进 harness（附带 ExternalArtifactManifest）
- 运行 execution_gate.py → 验证 Execution Authenticity PASS（agent_identity 非空、latency > 0、input_sha256 匹配、artifact 非空）
- 运行 e2e_metrics.py → 获取真实能力测量
- 与 Synthetic B0-R2 对比：哪些指标从 synthetic 变为真实，差异在哪里
- 生成 B0-R3 报告，明确标记为 real_execution / external_agent

**Entry Criteria**：
- 6b External-Agent Execution Interface 完成并通过验证
- 外部 Agent 可用（Doubao / GPT / Claude / human）
- 2024_A 题面真实性验证通过（sha256=9baf81fb...）
- 外部 Agent 理解 DAG 节点定义和 ExternalArtifactManifest 契约

**Exit Criteria**：
- Execution Authenticity Gate PASS（agent_identity 非空、latency > 1s、input_sha256 匹配、artifact 非空）
- Artifact Integrity L1+L2 PASS
- e2e_metrics 输出真实能力指标（sub_question decomposition, method_selection, model_correctness structural, 等）
- B0-R3 报告包含完整 provenance 链（input→execution→artifact→evaluator→evidence→claim）
- 与 Synthetic B0-R2 的对比分析
- run record 中 `executor_type=external_agent`, `agent_identity` 如实记录
- 明确标记：这是 single-problem baseline，不代表 cross-problem capability

**B0 必须回答的 7 个问题**（每项有 observable evidence / evaluator / score-status / confidence / limitations）：
1. Agent actually understood the problem?
2. Agent decomposed the problem?
3. Agent constructed a mathematically valid model?
4. Agent selected an appropriate model family?
5. Agent solved it?
6. Agent validated it?
7. Agent supported claims?

---

## 4. Phase 7: Cross-family Validation（跨模型家族验证）

**目标**：在不同模型家族的题目上验证 evaluator 的稳定性和 Agent 能力的泛化性。

**Entry Criteria**：
- 6c Real B0-R3 完成（2024_A 运动学/几何）
- 至少 3 道不同模型家族的题目有真实题面和附件

**工作内容**：
- 选择 3 道不同模型家族的题目：
  - 2022_C（数据分析/统计）
  - 2020_B（优化/决策）
  - 2018_A 或 2019_C（微分方程/排队论）
- 对每道题运行 Real B0（使用 6b 的 LLMNodeExecutor）
- 验证 evaluator 在不同模型家族上的稳定性：
  - method_selection 是否能正确识别不同方法家族
  - model_correctness structural check 是否适用于不同模型类型
  - Artifact Integrity 必需字段是否需要按模型家族调整
- 建立 cross-family capability matrix：Agent 在每个模型家族上的能力表现
- 识别 evaluator 的 model-family-specific bias（如果有）

**Exit Criteria**：
- 3 道不同模型家族题目的 Real B0 完成
- evaluator 在 3 个家族上稳定运行（无 crash、无明显 bias）
- cross-family capability matrix 建立
- 如果发现 evaluator bias，记录并修复（research-layer，不修改 core 除非确认 bug）
- 明确标记：3 题样本量小，不代表完整泛化能力

**不做的事**：
- 不马上扩到 15/30/50 题（3 题足够验证 evaluator 稳定性）
- 不因为某道题分数低就判定 Agent 能力差（先确认是 Agent 失败还是 evaluator 不适用）

---

## 5. Phase 8: Targeted Intervention（定向干预实验）

**目标**：基于真实 failure profile，设计定向干预，验证干预是否真正提升能力（而非 evaluator gaming）。

**Entry Criteria**：
- Phase 7 cross-family validation 完成
- 至少有一个 confirmed failure mode（有 evidence、measurement valid、reproducible）

**Failure Profile 建立（干预前必须）**：
每次 B0 不允许直接说 Agent weak，必须输出：
- Observed Failure（具体观察到什么）
- Evidence（artifact / run manifest / evaluator 输出）
- Failure Mode（引用 FAILURE_TAXONOMY）
- Measurement Confidence（HIGH/MEDIUM/LOW）
- Likely Layer（A. Agent Capability / B. Workflow-Skill / C. Measurement-Evaluator）

**严格区分三类失败**：
- A. Agent Capability Failure：Agent 真的不会（如 model_construction 产出无 objective）
- B. Workflow-Skill Failure：workflow 没让 Agent 做，或 skill 缺失（如 problem_analysis 节点不产出 sub_question）
- C. Measurement-Evaluator Failure：尺子不准（如 evaluator 对空 artifact 判 PASS）

**Intervention Protocol**：
1. 只有当 failure mode confirmed + measurement valid + failure reproducible 才设计 intervention
2. 干预类型：
   - A 类：skill 增强 / prompt 优化 / 方法卡补充
   - B 类：workflow 节点调整 / skill 新增 / DAG 修改
   - C 类：evaluator 修复（这不是能力提升，是测量修复）
3. 干预后必须 Fresh B0（新 run，不覆盖旧实验）
4. 对比 B0 vs B1：differential capability contribution（默认只报告差异，不声称 causal effect，除非满足 randomization + controlled intervention + pre-registered comparison）
5. 不能看到低分→加 prompt→分数提高→宣称能力提高（必须排除 evaluator gaming）

**Exit Criteria**：
- 至少 1 个 confirmed failure mode 的 intervention 实验完成
- B0 vs B1 对比报告，明确 differential contribution
- 干预效果可复现（至少 2 次独立 run）
- 明确标记：single intervention，不代表通用能力提升

---

## 6. Phase 9: Generalization（泛化测试）

**目标**：验证 Agent 的建模能力是否能跨题目、跨模型家族、跨难度泛化。

**Entry Criteria**：
- Phase 8 至少 1 个 intervention 实验完成
- 至少 5 道不同家族/难度的题目有真实题面

**工作内容**：
- 扩展到 5–10 道题（覆盖运动学/优化/统计/微分方程/决策等家族）
- 对每道题运行 Real B0（使用相同的 workflow/skill/LLM provider）
- 建立 capability generalization matrix：
  - 行：题目（家族/难度）
  - 列：11 项能力
  - 值：PASS/PARTIAL/FAIL + confidence
- 分析：
  - 哪些能力在所有题目上稳定？
  - 哪些能力只在特定家族上表现好？
  - 哪些能力是跨家族的瓶颈？
  - 难度与能力表现的关系
- Stochastic Robustness：对关键题目使用 pre-registered seeds [42,43,44,45,46] 运行 5 次，报告 mean ± std
- Determinism 与 Stochastic Robustness 分离：
  - Determinism = seed=42, same input/provider/code/environment → identical replay（针对确定性部分）
  - Stochastic Robustness = pre-registered seeds → variance/robustness（针对 LLM 输出）

**Exit Criteria**：
- 5–10 道题的 Real B0 完成
- capability generalization matrix 建立
- 跨家族能力瓶颈识别
- Stochastic Robustness 报告（至少 1 道题 5 seeds）
- 明确标记：5–10 题样本量，不代表完整泛化能力，但足以识别系统性瓶颈

---

## 7. Phase 10: Research Transfer（科研迁移）

**目标**：验证 CUMCM 建模能力是否能迁移到科研数学建模。

**Entry Criteria**：
- Phase 9 generalization 完成
- 至少 1 个科研建模问题可用（来自真实研究或公开科研数据集）

**能力迁移分析**（每项记录）：
| 能力 | 比赛特有部分 | 通用部分 | 迁移动作 |
|---|---|---|---|
| Problem Alignment | 子问题编号、A/B/C 题分类 | 问题→抽象→变量→约束 | 解耦 competition profile |
| Model Construction | 比赛常用方法库 | 11 层认知管线 | 方法库可插拔 |
| Formal Consistency | 无 | dimension/symbol/unit/equation | 直接通用 |
| Solving | 比赛时间限制 | solvability/computational reliability | 解耦时间约束 |
| Validation | 比赛评阅标准 | model validation/sensitivity | 评阅标准可配置 |
| Evidence | 无 | hash chain/provenance/replay | 直接通用 |
| Communication | 20 页论文格式 | 结果→主张→证据映射 | 格式模板可插拔 |

**工作内容**：
- 选择 1–2 个科研建模问题（如：物理系统建模、生物数据分析、工程优化）
- 使用相同的 Harness（Capability Core）运行科研问题
- 验证：
  - 哪些能力直接可用？
  - 哪些需要 adaptation？
  - 哪些是比赛特有、不适用于科研？
- 建立 research modeling benchmark（初步，1–2 题）
- 验证 Harness 的 domain-independence

**Exit Criteria**：
- 1–2 个科研建模问题的 Real B0 完成
- 能力迁移矩阵建立（7 项 Core 能力的迁移状态）
- 明确哪些能力是 domain-independent，哪些需要 adaptation
- 初步的 research modeling benchmark 建立
- 明确标记：1–2 题初步验证，不代表完整科研迁移能力

---

## 8. 关键决策点

| 决策点 | 触发条件 | 选项 | 建议 |
|---|---|---|---|
| D1: 执行体接入方式 | 6a 完成后 | A. 外部 Agent 执行接口（harness 侧零 LLM，外部 Agent 提交产物） / B. 在 core 内嵌 LLM 执行器（违反 Harness≠Agent 边界） | **A**（架构边界要求，core 永远 LLM-free） |
| D2: evaluator 稳定性 | Phase 7 跨家族验证后 | 1. evaluator 稳定 / 2. 发现 model-family bias / 3. evaluator 不适用某些家族 | 2→修复后重测 / 3→重新设计该家族的 evaluator |
| D3: 干预 vs 测量修复 | Phase 8 failure profile 后 | A. Agent capability failure → intervention / B. Workflow failure → workflow fix / C. Evaluator failure → measurement fix | C 优先（先修尺子），B 其次，A 最后 |
| D4: 扩题节奏 | Phase 9 后 | 1. 继续扩题 / 2. 深入干预 / 3. 科研迁移 | 2（深入干预比扩题更有价值），然后 3 |
| D5: core 修改门槛 | 任何 core 修改前 | 1. 真实 failure mode + minimal patch + non-regression / 2. 无 failure mode | 只允许 1，2 禁止 |

---

## 9. 不做的事（贯穿全路线图）

1. ❌ 在测量仪器未验证前跑大量题
2. ❌ 把 mock execution 结果当真实能力
3. ❌ 把 method name hit 当 model correctness
4. ❌ 为了提高分数修改 evaluator
5. ❌ 事后调整 threshold 适应结果
6. ❌ 在没有 baseline 的情况下做 intervention
7. ❌ 把论文长度当建模能力
8. ❌ 把单一题目结果当泛化能力
9. ❌ 在没有 cross-family 验证前宣称能力提升
10. ❌ 修改 v3.1.x core architecture（除非真实 failure mode + minimal patch + non-regression）
11. ❌ 删除 research evidence
12. ❌ 用 synthetic evidence 冒充 real-world evidence

---

## 10. 成功标准

这个路线图最终成功，不是因为跑了多少题、生成了多少报告，而是最终能够对任意一个数学建模能力声明：

**"Agent 的这个能力确实存在 / 不存在 / 改善了 / 没有改善。"**

同时能够给出：
- Input → Execution → Artifact → Evaluator → Evidence → Claim 完整可追溯链
- 别人可以 checkout commit → obtain frozen inputs → run same experiment → reproduce evidence → inspect evaluator → challenge conclusion
- 跨题目、跨模型家族的能力泛化证据
- 科研迁移的初步验证

---

*报告生成时间：2026-09-08 | 基于 6 个子代理的审计和修复结果 | 当前阶段：Phase 6a Mock B0-R2（进行中）*
