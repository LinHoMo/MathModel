# MODEL CONSTRUCTION GAP — 模型构建链路缺口终稿

> **基于 5 路独立审计 + 前期 GAP_AUDIT（HEAD 4c80914）的对照更新**。
> 当前 HEAD `022d457` 已包含 P1（C1-C10）+ audit Batch 1-10 修复。本文件回答：哪些缺口已修复，哪些仍存在，哪些是新发现。

---

## 0. 总判断

> **P1（C1-C10）修复了"原语不存在"的问题，但没有修复"生产路径不接通"的问题。** ExecutionAdapter / MODEL_IR builder / Validation / Evidence Graph / Replay 等原语是真实的，但默认 `orchestrator --execute` 从不注入 MODEL_IR/code/spec，导致生产路径仅完成 3/20 节点。vs001 的"闭环"由独立 runner 脚本驱动，不经 V3 主 DAG。当前最大缺口不是"缺少模块"，而是"模块之间没有接线"。

---

## 1. 11 环节缺口状态更新（对照前期 GAP_AUDIT）

### 环节 1：Problem / Question

| 项 | 前期（4c80914） | 当前（022d457） | 变化 |
|---|---|---|---|
| 真实代码 | demonstrated | **REAL** | 无变化 |
| 生产调用 | demonstrated | **REAL**（session.py:64 调 load_problem_representation） | 无变化 |
| 题面解析 | not found（Q 是外部标签，P 是空壳） | **仍未修复** | 无"题面文本→结构化 Problem/Question"解析 |
| 占位 | Problem title 硬编码"赛题"（handlers.py:181） | **仍存在** | 未修复 |

**状态：REAL（但轻量，无题面解析）**

### 环节 2：Problem Analysis（features / representation）

| 项 | 前期 | 当前 | 变化 |
|---|---|---|---|
| 真实代码 | demonstrated | **REAL** | 无变化 |
| 题面→特征解析 | not found（由外部文件提供或回退 _LEGACY） | **仍未修复** | 无解析器 |
| _LEGACY 硬编码 | handlers.py:80-81 | **仍存在** | 未修复 |
| ProblemProfile 不是 artifact | not found | **仍未修复** | 无独立 artifact/图节点 |

**状态：REAL（外部契约注入，非 runtime 内分析能力）**

### 环节 3：Method Recommendation

| 项 | 前期 | 当前 | 变化 |
|---|---|---|---|
| 真实代码 | demonstrated | **REAL** | 无变化 |
| 知识覆盖 | 19 张卡，10+ 族 cards:[] | **22 张卡**（新增 BZD 试点卡 5 张） | 改善 |
| 词表对齐 | 18 canonical family 中 10+ 族无卡 | **仍存在**（K001 方法族命中 0.0-0.222） | 未修复 |
| recommend 只返回 score>0 | retriever.py:220 | **仍存在** | 未修复 |

**状态：REAL（卡库内匹配，非"建模方法空间"推荐）**

### 环节 4：Candidate Models

| 项 | 前期 | 当前 | 变化 |
|---|---|---|---|
| 真实代码 | demonstrated | **REAL** | 无变化 |
| 进入 Artifact Registry | not found（无 candidate 类型） | **P1 C2 已修复**：candidate→artifact + assumes 边 | ✅ 修复 |
| 进入 Evidence Graph | not found | **P1 C2 已修复** | ✅ 修复 |
| 生产路径调用 | not found（仅内存 dict） | **仍 TEST-ONLY**：CompetitionIntelligence 0 非测试调用方，V3 DAG 无 candidate_generation 节点 | ❌ 未修复 |
| 候选分数启发式 | candidates.py:147,163,184-190 | **仍存在** | 未修复 |
| _CANDIDATE_SEQ 全局计数器 | candidates.py:23 | **仍存在**（非会话隔离） | 未修复 |

**状态：TEST-ONLY（P1 修复了持久化，但生产路径仍不调用）**

### 环节 5：Model Selection

| 项 | 前期 | 当前 | 变化 |
|---|---|---|---|
| 真实代码 | demonstrated | **REAL** | 无变化 |
| chosen=recs[0] 硬编码 | selection.py:60 | **仍存在**（selection.py:80）：evidence 存在时仍取第一 | ❌ 未修复 |
| evidence 门禁 | 无 | **P1 FIX-2.2 已添加**：无 evidence→UNSELECTED（selection.py:66-71） | ✅ 部分修复 |
| selects 边写入 | core 零调用 | **P1 C3 已修复**：handlers.py:939 真写 selects 图边 | ✅ 修复 |
| Decision 统一到 Registry | DecisionLog 独立存储 | **P1 C3 已修复** | ✅ 修复 |
| criteria 固定四词 | selection.py:96-97 | **仍存在** | 未修复 |
| confidence=0.5+0.1*score | selection.py:100 | **仍存在** | 未修复 |
| evidence_ids=[] 恒空 | selection.py:103 | **仍存在** | 未修复 |

**状态：PARTIAL（evidence 门禁已加，但选型仍=检索排序取第一；evidence 不参与排序）**

### 环节 6：MODEL_IR

| 项 | 前期 | 当前 | 变化 |
|---|---|---|---|
| schema 进 core | not found（research 独立） | **P1 C1 已修复**：core/schemas/v3/model/model_ir.schema.json + model_ir.py | ✅ 修复 |
| builder | not found | **P1 C1 已修复**：ModelIRBuilder | ✅ 修复 |
| registry 类型 | not found | **P1 C1 已修复**：model_ir 类型，ID 前缀 MIR | ✅ 修复 |
| 生产路径调用 | not found（core 零命中） | **PARTIAL**：handlers.py 只登记外部注入 MIR，无注入→FAIL no_model_ir | ⚠️ 半修复 |
| 三层独立 artifact | 文档声称 | **不成立**：runtime ModelIR 是单 artifact 内 l1/l2/l3 分组，三层只存在于 research 旧格式 | ❌ 文档与实现不一致 |
| 契约漂移 | — | **严重**：246/246 份 research model_ir.json 同时违反 runtime schema 与 research 自身 schema（0% 合规） | ❌ 新发现 |
| schema 双副本 | — | core/schemas/v3 + research/P15/model_representation 两份，字段已漂移（modeling_trace 仅 core 侧 required） | ❌ 新发现 |

**状态：PARTIAL（原语真实，但生产不产 MIR；契约 100% 漂移）**

### 环节 7：Code Generation

| 项 | 前期 | 当前 | 变化 |
|---|---|---|---|
| 真实代码 | demonstrated | **REAL** | 无变化 |
| DAG 含 code 节点 | 无（catalog/v3.yaml 16 节点不含 code_gen） | **P1 C6 已修复**：code_generation 节点已加入 DAG | ✅ 修复 |
| 生产入口接 adapter | orchestrator 不传 adapter | **仍未修复**：orchestrator.py:391 不传 execution_adapter | ❌ 未修复 |
| implemented_by 边写入 | 零写入 | **P1 C6 已修复**：handlers 写 implemented_by 边 | ✅ 修复 |
| 无注入返回 [] | handlers.py:426/431 | **仍存在**：无 external_code → no-op | ❌ 未修复（设计如此，但生产零注入） |
| planner 无 code 字段 | planner.py:81-91 | **仍存在** | 未修复 |

**状态：PARTIAL（DAG 节点已加，但生产零注入导致 no-op）**

### 环节 8：Execution

| 项 | 前期 | 当前 | 变化 |
|---|---|---|---|
| 真实 subprocess | demonstrated | **REAL**（adapters.py:198-206） | 无变化 |
| 生产入口接 adapter | orchestrator 不传 | **仍未修复**：默认 run 产物类型不含 execution_result | ❌ 未修复 |
| execution_result schema 门禁 | 无（registry.create 无 schema） | **P0 FIX-5.4 已添加**：artifact.py 校验 + 测试 15/15 通过 | ✅ 部分修复 |
| 来源鉴别 | 无 | **仍未修复**：伪造 EXEC 可通过门禁（实测） | ❌ 未修复 |
| 执行失败→节点 FAIL | 不触发（do_experiment 仍返回 PASS） | **audit FIX-4.x 已修复**：执行失败真实传播 | ✅ 修复（注入路径） |
| 0 执行=PASS | handlers.py:431-432 | **仍存在**（handlers.py:753） | ❌ 未修复 |
| environment_hash 深指纹 | 浅指纹（仅 python/platform） | **仍存在** | 未修复 |

**状态：REAL（原语）+ PARTIAL（生产不接通 + 来源鉴别缺失 + 0执行=PASS）**

### 环节 9：Validation

| 项 | 前期 | 当前 | 变化 |
|---|---|---|---|
| 真实代码 | demonstrated | **REAL**（validation.py run_checks 三状态铁律） | 无变化 |
| validator 接 engine | 未接（session 不传 validators） | **仍未修复**：实测 engine.validators={} | ❌ 未修复 |
| VR 进 DAG 决策 | 不消费 | **仍未修复**：VR failed/invalid 只登记，无 DAG 节点读取并判 FAIL | ❌ 未修复 |
| 0/0=PASS | — | **仍存在**（handlers.py:776-781，实测 0 VR 全绿） | ❌ 未修复 |
| L0-L4 五层体系 | 不存在 | **仍不存在**：feasibility/residual/stability/domain 零实现 | ❌ 未修复 |
| fidelity 接主路径 | 仅 codegen.py:155 | **仍未修复**：V3 DAG 零调用 | ❌ 未修复 |
| L2 数学检查 | 无 | **P1 FIX-5.3 已添加**：formula_checker 接线 | ✅ 修复 |
| derive checks from MODEL_IR | 无 | **P1 FIX-5.2 已添加** | ✅ 修复 |

**状态：REAL（原语）+ PARTIAL（validator 未接线 + 0验证=PASS + fidelity 未接 + L3/L4 缺失）**

### 环节 10：Evidence

| 项 | 前期 | 当前 | 变化 |
|---|---|---|---|
| implemented_by 边 | 零写入 | **P1 C6 已修复** | ✅ 修复 |
| executed_by 边 | 存在（result→EXEC） | **REAL** | 无变化 |
| revision_of/supersedes 边 | 不存在（16 种关系无此二类） | **P1/Batch6 已添加**：vs001 实验有 revision_of/supersedes 边 | ✅ 修复（但仅实验脚本手工写） |
| 占位 claim 骗过门禁 | claims_supported=2, coverage=1.0 | **FIX-1.4 已修复**：占位 claim 无 supports 边，E1/E2 拦截 | ✅ 修复 |
| evidence_gate 只查边不查数值 | E1-E8 只查边/生命周期 | **FIX-4.1 已修复**：E9 要求 exec_ref + outputs 非空 | ✅ 部分修复（但 E9 不要求 VR） |
| E9 不要求 VR | — | **仍存在**（evidence_gate.py:208-215） | ❌ 未修复 |
| coverage 度量"边存在"而非"证据真实性" | 存在 | **仍存在** | 未修复 |

**状态：REAL（边关系真实）+ PARTIAL（E9 不要求 VR + coverage 语义弱）**

### 环节 11：Revision

| 项 | 前期 | 当前 | 变化 |
|---|---|---|---|
| 引擎 retry/rollback | demonstrated | **REAL** | 无变化 |
| DAG 反馈边 | 存在（modeling.yaml:26 等） | **REAL** | 无变化 |
| 自动 M1→M2 端到端 | 不存在 | **仍不存在**：model_validation FAIL→重试耗尽→blocked，无自动诊断/修订 | ❌ 未修复 |
| diagnose_failure / build_revision_draft | 不存在 | **P1/Batch6 已添加**：revision.py + diagnosis.py | ✅ 原语修复 |
| revision/diagnosis 接主 DAG | 不存在 | **仍未接入**：仅 tests + vs001_driver.py 调用 | ❌ 未修复 |
| revision 边由 runtime 生成 | 不存在 | **仅实验脚本手工 add_relation**（p1_vs001_runner.py:126-142） | ❌ 未机械化 |
| 执行/验证失败→FAIL 节点 | 不映射 | **audit FIX 已修复**（注入路径） | ✅ 修复（注入路径） |

**状态：TEST-ONLY（原语真实，但完全不在 V3 主 DAG）**

---

## 2. 缺口汇总表

| 环节 | 前期状态 | 当前状态 | 已修复 | 未修复 |
|---|---|---|---|---|
| 1 Problem | demonstrated | REAL | — | 题面解析、硬编码标题 |
| 2 Problem Analysis | demonstrated | REAL | — | 题面→特征解析、_LEGACY 硬编码 |
| 3 Method Recommendation | demonstrated | REAL | 卡数 19→22 | 词表对齐、score>0 过滤 |
| 4 Candidate Models | not found | TEST-ONLY | 持久化+图边 | 生产路径不调用、分数启发式、全局计数器 |
| 5 Model Selection | demonstrated | PARTIAL | evidence 门禁、selects 边、Decision 统一 | chosen=recs[0]、criteria 固定、confidence 启发、evidence_ids 空 |
| 6 MODEL_IR | not found | PARTIAL | schema+builder+registry 类型 | 生产不产 MIR、100% 契约漂移、schema 双副本、三层非独立 artifact |
| 7 Code Generation | demonstrated | PARTIAL | DAG 节点、implemented_by 边 | 生产零注入、planner 无 code 字段 |
| 8 Execution | demonstrated | REAL+PARTIAL | schema 门禁、失败传播 | 生产不接 adapter、来源鉴别缺失、0执行=PASS、environment_hash 浅 |
| 9 Validation | demonstrated | REAL+PARTIAL | L2 数学检查、derive checks | validator 未接线、0验证=PASS、fidelity 未接、L3/L4 缺失 |
| 10 Evidence | demonstrated | REAL+PARTIAL | implemented_by、revision 边、占位拦截、E9 exec_ref | E9 不要求 VR、coverage 语义弱 |
| 11 Revision | not found | TEST-ONLY | 原语（revision.py + diagnosis.py） | 不接主 DAG、revision 边非机械化、无自动 M1→M2 |

---

## 3. 新发现的缺口（前期 GAP_AUDIT 未覆盖）

### N1：生产路径架构真空
`orchestrator --execute` 从不注入 external_model_irs/external_code/validation_specs（orchestrator.py:322-326,391），model_construction 必然 BLOCKED。实测仅 3/20 节点完成。这是所有下游缺口的根源。

### N2：MODEL_IR 契约 100% 漂移
246/246 份 research model_ir.json 同时违反 runtime schema 与 research 自身 schema。schema 重建即空转——没有任何一份产物通过过当前 schema。

### N3：6 个 validator 声明 0 个挂载
catalog/v3.yaml 声明 6 个 validator，session.py 构造 engine 时不传 validators，实测 engine.validators={}。所有 gate 节点 PASS 只靠 handler 内部自判。

### N4：Agent 可直接写 Validation PASS
critic SKILL.md（model-critic:63, experiment-critic:52）指令 Agent 调 mark_validated，registry 无调用方门禁。这是 Authority Matrix 的核心违规。

### N5：伪造 ExecutionResult 可通过门禁
registry.create("execution_result") 无来源鉴别，实测完整伪造可通过。K003 事故形态可复现。

### N6：fidelity 门未接主路径
fidelity.py 仅被 run_code_pipeline（独立入口）和 CLI 调用，V3 DAG 零调用。Model→Code 保真无机器检查。

### N7：20 个 validators/modules 死代码
core/validators/modules/ 下 20 个模块全仓 0 导入。V2 验证体系整体残留。

### N8：model_ir schema 双副本漂移
core/schemas/v3/model/model_ir.schema.json（19KB，含 modeling_trace required）与 research/P15/model_representation/model_ir.schema.json（29KB，不含 modeling_trace）并存且漂移。

### N9：V2 兼容层路径损坏
orchestrator.py:58-59 _skill_path 指向 core/Modeler/agents/...（不存在），正确路径是 core/legacy/hands/Modeler/agents/...。--legacy 模式当前必然失败。

### N10：bench_mmbench.py 空壳
非 dry-run 模式 prediction=""、correct=False 恒成立，accuracy 恒 0。指标虚设但"可运行"。

---

## 4. 每模块 REAL / PARTIAL / TEST-ONLY / DEAD / MISLEADING 判定

| 模块 | 判定 | 关键证据 |
|---|---|---|
| `execution/adapters.py` | **REAL** | subprocess.run 真实，status 由 returncode 推导 |
| `execution/engine.py` | **PARTIAL** | 执行机真实；validator 钩子 dead（validators 恒空） |
| `execution/session.py` | **PARTIAL** | 组装真实；waves.engine 覆盖导致 state/validators 丢失 |
| `execution/fidelity.py` | **TEST-ONLY** | 实现真实；V3 主 DAG 零调用 |
| `execution/codegen.py` | **REAL** | register_code + execute_code 真实，被 handlers/runner 调用 |
| `execution/replay.py` | **REAL** | 真实重跑，vs001 replay 2/2 match |
| `execution/validation.py` | **REAL（空转语义）** | run_checks 真实；无 spec 返回 [] → 0/0 PASS |
| `execution/dag.py` + `wave_executor.py` | **REAL（PARTIAL 组装）** | DAG 真实；内建 engine 丢失 state/validators |
| `modeling/model_ir.py` | **REAL** | 三层结构校验 + 公式检查真实 |
| `modeling/candidates.py` | **TEST-ONLY** | CompetitionIntelligence 0 非测试调用方 |
| `modeling/selection.py` | **PARTIAL** | evidence 门禁真实；有 evidence 仍 recs[0] |
| `modeling/comparison.py` | **TEST-ONLY** | 仅 vs001_driver + tests |
| `modeling/knowledge_guided.py` | **TEST-ONLY** | 仅 tests + research/m4_run |
| `modeling/revision.py` + `diagnosis.py` | **TEST-ONLY** | 仅 tests + vs001_driver；V3 DAG 无此节点 |
| `modeling/planner.py` | **REAL** | 真规划；但 card_ids[0] 隐式取主方法 |
| `modeling/problem_repr.py` | **REAL** | 真解析；无题面文本→结构化解析器 |
| `artifacts/registry.py` | **PARTIAL** | 持久化真实；EXEC 无来源鉴别、mark_validated 无门禁 |
| `graph/evidence_graph.py` | **REAL** | 边关系 + 失效传播真实；add_relation 无身份绑定 |
| `roles.py` + `core/roles/*.yaml` | **DEAD-in-prod** | 仅 DAG 校验引用；handler 不读 roles |
| `core/skills/critics/*` | **DEAD-in-prod + 权限违规** | engine 不执行；Agent 手动驱动时可写 mark_validated |
| `core/legacy/hands/`（29 agents） | **DEAD-in-prod** | V3 运行时零读取 |
| `core/validators/modules/`（20 模块） | **DEAD** | 全仓 0 导入 |
| `core/runtime/domain/` | **DEAD** | 仅 __init__.py，DEAD EVERYWHERE |
| `core/runtime/adapters/`（非 execution/adapters.py） | **DEAD** | 仅 openai.yaml，DEAD EVERYWHERE |
| `core/runtime/contracts.py` | **TEST-ONLY** | 仅 test_p7_integrity.py 引用 |
| `bench_mmbench.py` | **MISLEADING** | accuracy 恒 0 但可"运行"，掩盖测量缺失 |
| `handlers.py:_maybe_execute_experiment` | **DEAD** | 全仓 0 调用点 |

---

## 5. 最严重的 5 个缺口（按修复优先级）

1. **N1 生产路径架构真空**：orchestrator 不注入 → 3/20 节点 → 所有下游原语无法在生产中发挥作用。这是"有引擎没钥匙"的问题。
2. **N5 伪造 EXEC 可通过门禁 + N4 Agent 写 Validation PASS**：信任边界被穿透，K003 事故可复现。这是"可信 Harness"的核心承诺被破坏。
3. **N3 validator 未接线 + 环节 9 0验证=PASS**：声明的验证层是空转，"没验证=通过"。这是"Validation 是核心竞争力"的承诺被破坏。
4. **环节 11 Revision 不在主 DAG**：M1→FAIL→M2 闭环只在独立脚本中存在，生产路径失败即 blocked。这是"Revision-capable"定位的承诺被破坏。
5. **N6 fidelity 未接主路径 + 环节 6 100% 契约漂移**：Model→Code 保真无检查，MODEL_IR 契约无真实产物通过。这是"MODEL_IR 是核心契约"的承诺被破坏。

---

*本缺口分析基于 5 路独立审计的代码证据 + 前期 GAP_AUDIT 对照。所有判定附 file:line。*
