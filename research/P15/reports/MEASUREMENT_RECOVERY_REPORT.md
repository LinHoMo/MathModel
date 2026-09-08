# Measurement Recovery Report — P15.1 测量仪器恢复报告

> 生成日期：2026-09-08 | 基线 commit：`af1bbd5`（Tier 0 删除 + P0 修复后）
> 任务：重新建立可信、可审计、可复现的数学建模能力测量系统
> 原则：先证明尺子是对的，再测 Agent

---

## 1. 执行摘要

上一轮审计发现 2024_A B0 measurement = INVALID（输入污染 + 未真实执行 + evaluator 放过空壳）。本轮测量恢复工作完成了以下关键修复：

| 维度 | 修复前 | 修复后 | 状态 |
|---|---|---|---|
| **输入真实性** | 2024_A 题面错误（防空导弹=2025_A），4/5 题 BLOCKED | 5 道题全部恢复真实题面，0 BLOCKED，sha256 验证 | ✅ RECOVERED |
| **执行真实性** | V3/V2/RC-S1 三条路径全部零 LLM，latency=0.06s, provider=null | 根因确认（DefaultNodeExecutor 确定性管线），execution_gate.py 实现，mock executor 方案 D | ✅ DIAGNOSED + GATED |
| **Artifact 完整性** | 16/16 空壳 artifact（payload=[]）全 PASS | 三层 gate 设计（non-empty/structural/semantic），execution_gate.py 实现 L1+L2，旧 B0 正确判定 INVALID | ✅ GATED |
| **评估器有效性** | 3 P0 bug（空壳 PASS / method_selection 字符串匹配 / model_correctness 依赖外部输入） | e2e_metrics.py minimal patch 修复全部 3 P0，pytest 781/11 零回归 | ✅ FIXED |
| **能力本体** | C0–C15 仅 5/16 有闭环，Failure Taxonomy 7/22 空 | 11 项能力地图，25 个可测量 FM（A/B/C 分类），L1-L4 评分细则，5 个 Problem Card | ✅ REBUILT |
| **Benchmark Schema** | core_methods 可能唯一答案，无 allowed_model_families | Problem Card 含 allowed_model_families + acceptable_solution_variants + known_invalid_model_patterns | ✅ UPGRADED |

**核心结论**：测量仪器已恢复可信状态。输入真实、gate 有效、evaluator 修复、能力本体重建。剩余瓶颈是执行管线不产生真实 LLM 输出（零 LLM 设计），需通过方案 A（core minimal patch 接入 LLM）或方案 D（mock executor 验证链路）解决。

---

## 2. 输入真实性恢复（Phase 1）

### 2.1 2024_A 题面污染修复

**问题**：`examples/problems/cumcm2024A.txt` 内容是"防空导弹拦截弹道目标"，实为 **2025_A** 题面被错误标记为 2024_A。sha256 与 run manifest 匹配，pipeline 确实收到错误题面。

**修复**：
- 真实 2024_A"板凳龙闹元宵"题面从 2 个独立来源交叉验证：
  - 来源 1（Level 1 高校 PDF）：哈尔滨信息工程学院基础部
  - 来源 2（Level 3 CSDN）：weixin_66547608 博客
  - 辅助验证（Level 2）：中国大学生在线 A 题讲评（复旦蔡志杰）
- 真实题面保存到 `research/P15/benchmark/problem_cards/2024_A/problem_statement.txt`（4990 bytes, sha256=9baf81fb40f82f77...）
- 复制到 `examples/problems/cumcm2024A.txt` 和 `projects/p151-2024a/inputs/cumcm2024A.txt`
- sha256 验证与 `input_manifest.json` 一致

### 2.2 5 道 benchmark 题全部恢复

| problem_id | 标题 | 状态 | SHA256 (前16位) | 大小 |
|---|---|---|---|---|
| 2024_A | 板凳龙闹元宵 | verified | 9baf81fb40f82f77 | 4990B |
| 2022_C | 古代玻璃制品的成分分析与鉴别 | verified | ec5e098f9dbe858e | 3878B |
| 2020_B | 穿越沙漠 | verified | a2d0867169b94c59 | 4275B |
| 2018_A | 高温作业专用服装设计 | verified | 6b4062dcd020bd6b | 1519B |
| 2019_C | 机场的出租车问题 | verified | 4fc950a9a2251043 | 2557B |

**0 BLOCKED**。每题均满足至少 2 个独立来源交叉验证，题面文本已剥离解题内容，仅保留问题陈述。

### 2.3 论文规范核验（官方来源 mcm.edu.cn）

| 规范项 | 内容 | 来源 |
|---|---|---|
| 页数 | 2026 修订稿正文**不超过 30 页**（硬上限）；2023/2024 版为"尽量控制在 20 页以内"（软目标） | mcm.edu.cn 官方 |
| 摘要 | 第三页专用，不超过一页，无需英译 | 官方 |
| 匿名 | 全文不得出现身份/学校/赛区信息 | 官方 |
| 附录 | 页数不限，必须含全部可运行源码 | 官方 |
| 评阅四标准 | 假设合理性、建模创造性、结果正确性、表述清晰程度 | 官方 |

**注意**：之前简报中的"30 页"和上一轮审计中的"20 页"都不完全错——取决于年份。当前 env `min_pages: 17` 合理。

---

## 3. 执行真实性恢复（Phase 2）

### 3.1 零 LLM 根因确认（代码级证据）

**三条执行路径全部零 LLM**：

| 路径 | LLM 调用? | 关键证据 |
|---|---|---|
| V3 (`orchestrator --execute`) | 否 | `handlers.py:13-15` 明确声明"确定性认知管线（零 LLM）"；全 `core/` 目录 `import openai`/`client.chat` 为 **0 匹配** |
| V2 (`orchestrator --legacy`) | 否 | `_execute_step` 解析 SKILL.md 但从不发送给 LLM，只跑门禁 + 推进状态 |
| RC-S1 | 否 | RunRecord `model_provider=null`, latency=0.07s, 16 nodes — 与 B0 完全相同 |

**调用链**：`orchestrator.py --execute` → `_execute_v3()` → `RuntimeSession` → `DefaultNodeExecutor`（16 节点依次执行，全部内存操作）

**latency=0.06s**：16 节点 × ~0.004s 纯内存操作 = 0.06s。真实 LLM 执行通常 > 10s。

**"TOPSIS 选择"来源**：`handlers.py:75-79` 硬编码默认 features `{"problem_types": ["evaluation"], ...}`，`KnowledgeRetriever.recommend()` 基于此返回 mc-topsis 为 top-1。**从未读取赛题文本**。

**唯一的 LLM 可插拔点（从未被调用）**：`core/runtime/writing/paragraphs.py:403-425` 的 `ControlledRenderer` — `llm_fn` callable 注入接口，有后验校验，但 `RuntimeSession`/`DefaultNodeExecutor` 从未实例化它。

### 3.2 Execution Authenticity Gate（已实现）

`research/P15/measurement_recovery/execution_gate.py`（40KB，零依赖）实现 13 项 EAG 检查：
- model/provider 非空、model version 非空、skill version 非空
- execution timestamp 合理、latency > 0（排除模板初始化）
- input hash 与 manifest 一致、workflow hash 与 DAG 定义一致
- tool invocation 记录存在、artifact count > 0、artifact payload non-empty
- decision log 非空、execution-result binding

**对旧 B0 项目实测**：8 INVALID / 5 PASS，Artifact Integrity 16/16 INVALID（0% pass rate）。Overall: INVALID。✅ 正确判定。

### 3.3 Artifact Integrity Gate（三层设计）

- **Layer 1 Non-Empty（deterministic）**：每种 artifact type 有必需字段，payload=[] / 空字符串 / placeholder 判定 FAIL
- **Layer 2 Structurally Valid（deterministic）**：JSON 可解析、必需字段存在、字段类型正确、引用一致性（variable 引用在 model 中定义）
- **Layer 3 Semantically Populated（semantic/LLM judge）**：内容不是模板默认值、变量/约束/目标与题面相关。仅在 L1+L2 PASS 后执行。

占位符模式黑名单：节标题-only、方法卡 ID-only、空结论、模板默认值等。

---

## 4. 评估器有效性恢复（Phase 3）

### 4.1 全量审计结果

34 个 evaluator 全量审计，发现 **12 个 bug**（3 P0 / 8 P1 / 1 P2）：

| 严重度 | 数量 | 代表问题 |
|---|---|---|
| P0 测量无效 | 3 | 空壳 artifact 判全 PASS / model_correctness 依赖外部输入 / method_selection 纯字符串匹配 |
| P1 测量不可靠 | 8 | decomposition count-ratio 退化口径 / experiment_validity 仅查 tags / paper.exists()=1.0 / score_compute 关键词可游戏化 / fidelity_gate 空 artifact→1.0 |
| P2 测量不完整 | 1 | 缺少 cross-question consistency 检查 |

**Validity Status**：VALID 8 (24%) / PARTIALLY_VALID 20 (59%) / INVALID 2 (6%) / NEEDS_REDESIGN 4 (12%)。

### 4.2 P0 修复（e2e_metrics.py minimal patch）

| Bug | 修复 |
|---|---|
| EVAL-BUG-001 空壳 PASS | 新增 `_is_empty_artifact()`，评分前过滤 payload=[] 且 data={} 的空壳，报告标记排除数量 |
| EVAL-BUG-003 method_selection 字符串匹配 | 改为方法家族适用性检查，从 CUMCM-Bench-v2.json 加载 core_methods，标记 alternative_method，保留向后兼容 |
| EVAL-BUG-002 model_correctness 依赖外部输入 | 缺失时标记 UNAVAILABLE 不参与均分；新增 objective/constraints/variables 结构检查（structural PASS/FAIL，非语义正确性） |

**验证**：pytest 781 passed / 11 skipped（零回归），catalog_check PASS，validate.py 56/57（预期失败），import OK，sha256 双文件校验一致。

### 4.3 Model Construction Evaluator 重设计

四层架构（L1 20% + L2 35% + L3 25% + L4 20%），共 28 个 check（22 deterministic + 6 semantic-judge）：

- **L1 Problem Understanding**：sub-question coverage / required deliverables / variable identification / parameter identification / constraint identification / evaluation target alignment
- **L2 Model Construction**：variable semantics / objective clarity / constraint validity / mechanism / assumptions / equation structure / boundary conditions / units / index consistency / problem alignment
- **L3 Solving**：solver appropriateness / feasibility / convergence / numerical stability / repeatability / local-global optimum claims
- **L4 Validation**：baseline / sensitivity / robustness / uncertainty / counterfactual / failure cases

**3 个熔断 check**：objective_clarity / constraint_validity / equation_structure 任一 FAIL → 总分上限 40。

**Method Selection Quality 独立四维**：方法适用性、目标回答性、数学合理性、替代方法可行性——gold=TOPSIS, agent=AHP 不自动判 wrong。

---

## 5. 能力本体重建（Phase 4）

### 5.1 Capability Map（11 项能力）

| 能力 | 测量状态 | 置信度 | 科研迁移 |
|---|---|---|---|
| Problem Understanding | UNMEASURED | LOW | DIRECTLY_TRANSFERABLE |
| Problem Alignment | PARTIALLY_MEASURED | MEDIUM | NEEDS_ADAPTATION |
| Model Construction | PARTIALLY_MEASURED | MEDIUM | DIRECTLY_TRANSFERABLE |
| Formal Consistency | MEASURED | HIGH | DIRECTLY_TRANSFERABLE |
| Method Selection | MEASURED（修复后） | MEDIUM | NEEDS_ADAPTATION |
| Solving | PARTIALLY_MEASURED | MEDIUM | DIRECTLY_TRANSFERABLE |
| Validation | PARTIALLY_MEASURED | MEDIUM | DIRECTLY_TRANSFERABLE |
| Sensitivity-Robustness | UNMEASURED | LOW | DIRECTLY_TRANSFERABLE |
| Evidence | MEASURED | HIGH | DIRECTLY_TRANSFERABLE |
| Claim Support | MEASUREMENT_INVALID | LOW | DIRECTLY_TRANSFERABLE |
| Communication | MEASURED | MEDIUM | COMPETITION_SPECIFIC |

Method Selection 提升为独立维度，不再作为 Alignment 的代理。

### 5.2 Failure Taxonomy（25 个可测量 FM）

严格区分三类：
- **A. Agent Capability Failure**（16 个）：wrong abstraction, wrong mechanism, wrong causal structure, wrong objective, wrong constraints, missing variables, dimension inconsistency, symbol inconsistency, unit inconsistency, infeasible solution, non-convergence, missing validation, wrong validation target, overfitting, unsupported claim, missing provenance
- **B. Workflow-Skill Failure**（2 个 + 5 个 A+B 混合）：workflow skip, skill missing
- **C. Measurement-Evaluator Failure**（3 个）：evaluator bug, threshold manipulation, empty artifact passing

每个 FM 均有 definition / observable evidence / counterexample / measurement rule。旧 taxonomy 中 7 个空 FM 全部移除或重新定义。新增 Method Selection 类别（含 method_name_trap——TOPSIS 数学正确但问题错配的教科书级案例）。

### 5.3 Problem Cards（5 个）

2024_A 完整卡片：5 个子问题、14 个关键变量（含题面给定值）、8 项约束、5 种已知无效模型模式（含 TOPSIS for kinematics 实锤）、6 条禁止误解、6 项验证期望。

其他 4 题（2022_C/2020_B/2018_A/2019_C）为骨架卡片，待真实执行后填充。

---

## 6. 执行管线调查与执行模型纠偏

### 6.1 调查结论

整个 MathModel Harness **从未实际调用过 LLM**。所有"执行"都是确定性模板初始化。

**⚠️ 架构纠偏（2026-09-08）："整个 core 零 LLM 调用"不是缺陷，是设计要求。**

- **Harness ≠ Agent**：本项目不做 Agent，只做 Harness。真正的认知工作（读题/建模/求解/写结论）由外部 Agent（Doubao/GPT/Claude/人）在这个 harness 之下完成。harness 本身保持 LLM-free。
- `core/runtime` 永远不应该 import openai/anthropic 或内嵌 LLM 执行器。
- **真正的缺陷不是"core 不调 LLM"**，而是：`orchestrator --execute` 的确定性 `DefaultNodeExecutor`（模板/演练桩，产出空壳）被误当成一次真实 Agent 运行并进入了能力评分。
- **DefaultNodeExecutor 是 dry-run/synthetic 演练器，不是 Agent，其产物不代表任何建模能力。**

这意味着：
- 所有过去 B0/B1/MMA 测量都是基于确定性模板输出，不是真实 LLM 推理
- P13-3D 实验中 B1 > MMA > B0 是比较不同确定性模板，不是 LLM 能力
- 要获得真实能力测量，必须由**外部 Agent** 作为执行体，通过 External-Agent Execution Interface 提交真实产物

### 6.2 执行模型：External-Agent Execution Interface（替换原方案 A）

**撤销**：原方案 A（LLMNodeExecutor 进 core）——不在 core/runtime 里内嵌 LLM 执行器，不加 `--llm` 标志，不加 LLM provider/api_key 配置。

**正确方向**：harness 提供让外部 Agent 能在 DAG 下干活、并把真实产物合规登记进来的契约 + 适配器。

**两类执行器区分（executor_type）**：
- `dry_run` / `synthetic`：DefaultNodeExecutor 确定性桩 / mock executor，只用于流程演练和测量链路自检；gate 对 capability scoring 自动判 INVALID/SYNTHETIC，永远不允许进入能力结论
- `external_agent`：产物由仓库外真实 Agent 产出并登记，带完整溯源（agent_identity, model_version, input_sha256 绑定, latency > 0）

**ExternalArtifactManifest 契约**：每个外部 Agent 提交的节点产物必须附带 executor_type / agent_identity / model_version / input_sha256 / node_id / latency / payload 等字段，harness 侧做 schema 校验 + non-empty/structural/semantic gate + hash 绑定 + 溯源落盘。

**提交入口**：`register_external_artifact.py --project <项目> --manifest <path> --input-sha256 <hash>`，外部 Agent 逐节点登记产物，不得直接手写 registry.json。

### 6.3 测量仪器验证

`test_measurement_pipeline.py` 7/7 PASS：gate 能正确区分空壳/非空 artifact、零 LLM/真实 LLM 特征，score_compute 对最小论文给出合理评分（academic=4.5, eng=3.9, judge=4.75）。

**瓶颈不在测量仪器，在执行管线不产生非空内容——而这需要外部 Agent 作为执行体来解决。**

---

## 7. P0 修复验证汇总

| 检查 | 结果 | 基线 | 状态 |
|---|---|---|---|
| pytest tests -q | 781 passed, 11 skipped (32.76s→修复后) | 781 passed / 11 skipped | ✅ 零回归 |
| catalog_check.py --check | OK — v3 双视图三方一致 | — | ✅ PASS |
| validate.py | 56 passed, 1 failed（无用户.tex，预期） | — | ✅ 预期失败 |
| import e2e_metrics | OK | — | ✅ |
| sha256 题面校验 | 双文件与 manifest 一致 | — | ✅ |
| execution_gate 对旧 B0 | INVALID（8/13 EAG, 0/16 artifact） | — | ✅ 正确判定 |
| run_evaluation.ps1 编排 | p151 INVALID → 跳过评分 | — | ✅ 正确编排 |
| test_measurement_pipeline.py | 7/7 PASS | — | ✅ |

---

## 8. 局限性与下一步

### 8.1 当前局限性

1. **执行管线零 LLM（by-design）**：core/runtime 永远 LLM-free 是架构边界要求，不是缺陷。认知工作必须由外部 Agent 完成。当前缺少外部 Agent 执行接口（6b 建设中）。
2. **synthetic execution 即将验证**：B0-R2 使用 mock executor 生成非空 artifact（executor_type=synthetic），只能证明测量仪器工作正常，不能证明 Agent 能力。报告必须标注 SYNTHETIC / NOT A CAPABILITY RESULT。
3. **4 个 Problem Card 为骨架**：2022_C/2020_B/2018_A/2019_C 待真实执行后填充
4. **附件数据未恢复**：5 道题的题面文本已恢复，但附件数据（Excel/PDF）尚未获取和验证
5. **semantic evaluation 未实现**：Artifact Integrity Layer 3（semantic populated）需要独立 LLM judge，当前未接入

### 8.2 下一步（按优先级）

1. **6a Measurement Chain Self-Test**（进行中）：mock executor 生成非空 artifact，跑通 gate→evaluator→metrics 全链路，明确标注 SYNTHETIC
2. **6b External-Agent Execution Interface**（建设中）：实现 executor_type 区分 + ExternalArtifactManifest 契约 + register_external_artifact.py 提交入口 + gate 判据更新。harness 侧零 LLM 调用。
3. **6c Real B0-R3（external_agent）**：由外部 Agent（Doubao/GPT/Claude/human）作为执行体真正做 2024_A，通过 6b 接口登记真实 artifact，获得第一个真实可信 baseline。run record 中 executor_type=external_agent。
4. **附件数据恢复**：获取 5 道题的附件数据（Excel/PDF），计算 attachment_sha256
5. **4 个骨架 Problem Card 填充**：基于真实执行结果填充
6. **Cross-family B0**：在 2024_A（运动学）验证后，扩展到 2022_C（数据分析）、2020_B（优化）等不同模型家族
7. **semantic LLM judge**：实现 Artifact Integrity Layer 3 的独立 LLM judge（由外部 Agent 执行，不在 core 内）

---

*报告生成时间：2026-09-08 | 基于 6 个子代理的审计和修复工作 | 下一步：B0-R2 mock execution 全链路验证*
