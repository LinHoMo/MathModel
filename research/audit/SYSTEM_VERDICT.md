# SYSTEM VERDICT — MathModel 模型构建闭环系统裁决（Batch 0）

> **审计基线**：HEAD `d44384c`，2026-09-09
> **审计方法**：8 个独立只读审计子代理（A 架构 / B 模型构建 / C 执行 / D 证据验证 / E 修订 / F 实验 / G 测试 / H 治理），共 108 项发现，全部附磁盘证据
> **核心原则**：The Agent Is Not The State. Infrastructure ≠ Capability. 如果机器没有产生，就视为不存在。

---

## SYSTEM VERDICT

# **MODEL CONSTRUCTION LOOP = NOT REAL（当前状态）**

系统具备**真实的执行基础设施**（subprocess、fidelity、数值验证、Artifact Registry、Evidence Graph），但**模型构建闭环的核心环节存在系统性断裂**：

- 默认生产路径**不产生 MODEL_IR**（P0-05）
- Selection 是 `recs[0]` 硬编码（P0-04）
- ExecutionResult **无 schema 门禁，Agent 可伪造**（P0-01）
- Claim 是 `"{qid} 结论"` 占位符（P0-06）
- evidence_gate **零数值计算**（P0-07）
- 执行失败**不传播**（P0-08）
- Revision Loop **4/8 环节缺失**（无诊断/无提案/无比较/无决策）
- K003 实验**发生过 execution_result 伪造**（P0-02），且治理漏洞未修复

**系统当前能做的**：在外部注入完整 MODEL_IR + 代码的前提下，真实执行、真实计算 fidelity、真实数值验证、真实记录谱系边。
**系统当前不能做的**：从 Problem 自主走到 Model V2。默认路径下，"模型"是方法卡 ID 薄壳，"证据"是图边结构，"结论"是占位符，"修订"是人工脚本。

---

## REAL CAPABILITY（机械证据证明的真实能力）

| 能力 | 证据 | 状态 |
|---|---|---|
| **subprocess 执行** | `LocalPythonAdapter.execute`（adapters.py:177-261）真 `subprocess.run`，stdout/stderr/returncode 真实捕获 | ✅ REAL |
| **duration 测量** | `time.perf_counter()` 前后差值（adapters.py:186/203） | ✅ REAL |
| **code_hash 计算** | `sha256_text(plan.code)`（adapters.py:187） | ✅ REAL |
| **fidelity 计算** | fidelity.py:119-157 基于真实 outputs 机械计算 passed/total | ✅ REAL |
| **数值验证（VR）** | `run_numeric_validation`（validation.py）真算 constraint_violation_max/domain/robustness | ✅ REAL（但硬编码单问题） |
| **Artifact Registry** | registry.py 真实 CRUD + lifecycle + 哈希链 | ✅ REAL |
| **Evidence Graph** | evidence_graph.py 真实图存储 + 类型化边 + 失效传播 + 完整性检查 | ✅ REAL（但边结构极简） |
| **候选生成** | `CandidateArena.generate_candidates`（candidates.py:177-302）真实生成 2-4 个组合有差异的候选 | ✅ REAL（但生产路径生成后即弃） |
| **候选模式选型** | `do_model_selection_decision`（handlers.py:639-740）基于 VR 机械排序，decision 含 reasoning/evidence_ids | ✅ REAL（仅候选模式，需外部注入） |
| **M2 重执行** | P1 实验中 M2 经真实 subprocess 重新执行，输出修正后真实数值 | ✅ REAL |
| **revision_of 谱系边** | Evidence Graph 中 M2 -revision_of-> M1 边真实存在（p1-vs001/vs001_run 落盘实证） | ✅ REAL（但方向矛盾、生命周期未接通） |
| **DecisionLog** | decisions/log.py 真实记录 reasoning/confidence/evidence_ids | ✅ REAL |
| **Replay** | replay.py 支持运行重放/差异归因 | ✅ REAL |
| **冻结哈希** | K001/K002/K003 冻结 --check 全部 PASS，零漂移 | ✅ REAL |
| **catalog 三方一致** | catalog_check.py --check → OK | ✅ REAL |

---

## ARCHITECTURAL CAPABILITY（有架构但未证明有能力）

| 能力 | 架构存在 | 实际状态 | 缺口 |
|---|---|---|---|
| **MODEL_IR 结构** | 18 字段三层 dataclass + 完整 JSON schema | 结构完整，但**默认生产路径从不实例化**（实测 3 项目 MIR=0） | 实例化 GAP |
| **Problem Representation** | V2 question_spec.schema.json（146 行完整契约） | V3 运行时**从不读取**，只建 6 键粗画像 | 接入 GAP |
| **Candidate Evaluation** | execute_code + run_numeric_validation 管线存在 | 默认路径**无任何评估**（无 code/exec/VR） | 接线 GAP |
| **Code Generation** | codegen.py 模块存在 | 明确声明"core 永久 LLM-free，本模块不生成代码"，只做外部代码登记 | 生成 GAP |
| **Validation 分层（L0-L4）** | 21 个 validator modules（formula_checker/symbolic_verifier/...） | **全仓零 import，死代码**；validate.py 只做"类名字符串存在性"检查 | 接线 FAKE |
| **Evidence Gate** | evidence_gate.py E1-E8 八项检查 | 全部只查边/生命周期/tags，**零数值计算** | 真实性 GAP |
| **Claim 系统** | claim artifact + supports 边 + claim_quality | statement = `"{qid} 结论"` **占位符**，无任何填充逻辑 | 内容 FAKE |
| **Failure Diagnosis** | engine._handle_failure 存在 | 只做 retry→rollback，**不分析失败原因** | 诊断 GAP |
| **Revision Proposal** | revision_of 边 + registry.supersede 方法 | 无自动修订机制，M2 全部来自**预写 fixtures** | 生成 GAP |
| **M1/M2 Comparison** | 无 | **完全不存在** | GAP |
| **Accept/Reject Decision** | 无 | **完全不存在** | GAP |
| **contracts.py 契约层** | is_terminal/is_reusable/validate_node_result_outputs 谓词 | **core/ 零调用**，终态元组在 ≥10 文件内联 | 接线 GAP |
| **Schema 校验** | 27 个 JSON schema | pyproject 无 jsonschema 依赖，v3 schema **无数据校验消费方** | 接线 GAP |
| **V2 Legacy 兼容** | core/legacy/hands/ 29 agent 完整 | orchestrator --legacy 的 SKILL 路径**全部失效**（指向迁移前旧路径） | 路径断裂 |

---

## FAKE / UNVERIFIED CAPABILITY（伪装成真实能力的部分）

### 1. 默认路径"模型构建"是 FAKE
- `do_model_construction` 只登记假设，不产 MODEL_IR，节点仍 PASS（P0-05）
- Model artifact 是 `{card_id, family, shortlist}` 薄壳，provenance 为空
- 系统声称"建立数学模型（公式/符号/边界）"，实际只建了方法卡 ID 引用

### 2. 默认路径"选型"是 FAKE
- `selection.py:60` `chosen=recs[0]` 硬编码，无证据支撑（P0-04）
- confidence 由检索分换算，不是模型质量评估
- 系统无法回答"为什么选这个模型而不是另外两个"

### 3. "证据门禁"是 FAKE
- evidence_gate E1-E8 零数值计算，not_executed 链可结构 PASS（P0-07）
- "证据门禁通过"≠"有真实证据"

### 4. "结论/Claim"是 FAKE
- statement = `"{qid} 结论"` 占位符，placeholder=True 显式标记（P0-06）
- 全仓无代码填充真实结论
- 占位符经 director→narrative→projection 流入论文大纲

### 5. "六层防御验证"是 FAKE
- 21 个 validator modules 死代码，validate.py 只查类名字符串存在（P1-07）
- "L1-L6 分层验证"从未在管线中运行

### 6. K003 "外部 Agent 构造"是 FAKE
- 所有表示产物由 Organizer 脚本内嵌罐头定义生成（P0-10）
- 66 runs 仅含 24 个唯一表示（伪重复，P1-17）
- 实验 RQ1（外部 Agent 构造质量）根本没有被测量

### 7. K003 "盲评"是 FAKE
- submission ID 是 (题目,臂,seed) 确定性哈希，臂可逆向还原（P0-09）
- 盲评包文件结构本身暴露臂
- G2 校准报告显示评估者已在按臂推理

### 8. "端到端测试"是 FAKE
- e2e/test_pipeline.py 3/4 核心测试因产物不存在而 skip，注释自认"显式占位"（P1-13）
- 测试把"默认路径不产 MODEL_IR"编码为预期行为（P0-12）

### Agent 可伪造字段清单

| 字段 | 伪造路径 | 严重度 |
|---|---|---|
| **ExecutionResult.status** | `registry.create("execution_result", data=任意dict)` 无门禁 | P0 |
| **ExecutionResult.outputs** | 同上；可让 fidelity 全过 | P0 |
| **ExecutionResult.code_hash** | 同上；可骗过 replay 比对 | P0 |
| **ExecutionResult.duration_ms** | 同上；K003 旧版即写 0 | P0 |
| **ExecutionResult.stdout/stderr/returncode** | 同上 | P0 |
| **Claim.statement** | handlers.py 直接构造，占位符照过 quality 检查 | P0 |
| **Claim.claim_type** | 硬编码 "comparative" | P0 |
| **Candidate 全字段** | `external_candidates` 注入 | P1 |
| **MODEL_IR 全字段** | `external_model_irs` 注入 | P1 |
| **VR data** | registry.create 无门禁 | P1 |
| **Evidence Graph 边** | handler 可直接 graph.add_edge | P1 |
| **problem_features** | JSON 文件可任意写 | P1 |
| **decision.reasoning** | decision data 无门禁 | P2 |
| **fidelity_score（间接）** | 伪造 outputs 满足检查 | P0（间接） |

> **唯一不能直接伪造的**：subprocess returncode（由 OS 产生）、fidelity_score（由计算产生，但可被伪造 outputs 间接操纵）。

---

## P0 FINDINGS（Scientific Integrity — 12 项核心）

| ID | 问题 | 位置 |
|---|---|---|
| P0-01 | ExecutionResult 落库无 schema 门禁，Agent 可伪造 | registry.py:108-145 |
| P0-02 | K003 Generator 可直接制造 execution_result（已实际发生） | k003_formal_runner.py:690-785 |
| P0-03 | K003 runner 契约 bug，复跑会重新产出空壳 | k003_formal_runner.py:720-758 |
| P0-04 | Selection 硬编码 `chosen=recs[0]` | selection.py:60 |
| P0-05 | 默认建模节点不产 MODEL_IR 仍 PASS | handlers.py:891-930 |
| P0-06 | Claim 是 `"{qid} 结论"` 占位符，流入论文 | handlers.py:1219-1227 |
| P0-07 | evidence_gate 零数值计算，not_executed 可 PASS | evidence_gate.py:87-181 |
| P0-08 | 执行失败不传播，do_model_execution 无条件 PASS | handlers.py:525-534 |
| P0-09 | K003 盲评不盲，submission ID 可逆推臂 | k003_formal_runner.py make_submission_id |
| P0-10 | K003 无真实外部 Agent 构造，罐头定义替代 construct | k003_formal_runner.py ALL_PROBLEM_DEFS |
| P0-11 | K003 formal_results.json 被后台改写，与 run_summary 冲突 | formal_results.json |
| P0-12 | 测试把错误行为编码为预期（占位管线 validated） | test_e2e_metrics.py, test_runtime_session.py |

---

## P1 FINDINGS（Loop 断裂 — 18 项核心）

| ID | 问题 |
|---|---|
| P1-01 | K003 rebuild 不可从已提交代码重放 |
| P1-02 | K003 fidelity 报告证据剥离（score 有值 checks=[]） |
| P1-03 | MODEL_IR 无 code_mapping 字段 |
| P1-04 | Evidence Graph 无 evaluated_by/selected_from 边 |
| P1-05 | 候选分数是启发式常量，非评估结果 |
| P1-06 | 默认实验结果 not_executed 占位，可支撑 claim |
| P1-07 | 21 个 validator modules 死代码 |
| P1-08 | V3 不读题面/question_spec.json |
| P1-09 | jsonschema 未在 runtime 强制执行 |
| P1-10 | Model Artifact provenance 为空 |
| P1-11 | 候选竞技场链未接入生产 orchestrator |
| P1-12 | codegen+fidelity 是平行管线，不在生产链上 |
| P1-13 | e2e 测试是自认占位符 |
| P1-14 | claim 占位符零测试覆盖 |
| P1-15 | evidence_gate 测试只验证结构 |
| P1-16 | 21 个 validator 零测试 |
| P1-17 | K003 伪重复（66 runs = 24 唯一表示） |
| P1-18 | K003 重建产物含空时间戳/占位 ID |

---

## P2 FINDINGS（Validation / Revision 弱点 — 14 项核心）

| ID | 问题 |
|---|---|
| P2-01 | 门禁 WEAK 也被判 FAIL，语义矛盾 |
| P2-02 | Validation 分层无一完整 REAL（L0 GAP/L1 GAP/L2 FAKE/L3 GAP/L4 GAP） |
| P2-03 | run_numeric_validation 硬编码单一问题 |
| P2-04 | 无 Failure Diagnosis 代码 |
| P2-05 | 无 Revision Proposal 机制 |
| P2-06 | supersedes 边方向在两套路径中相反 |
| P2-07 | registry.supersede 已实现但 core 无调用点 |
| P2-08 | 无 M1/M2 比较逻辑 |
| P2-09 | 无 Accept/Reject 决策类型 |
| P2-10 | 无 changed_components 结构化字段 |
| P2-11 | K002 格式不对称混淆未修复 |
| P2-12 | K001 post-hoc 修正计分口径 |
| P2-13 | STATUS.md 声称 57/0/0 实测 56/1/0 |
| P2-14 | K003 G2/G4 闸门未能阻止伪造 |

---

## MODEL CONSTRUCTION LOOP STATUS（逐环节判定）

```
Problem → Representation → Candidate → Evaluation → Selection → MODEL_IR → Artifact
  GAP       GAP            REAL(条件)   FAKE(默认)    FAKE(默认)    GAP(实例化)   GAP

Code Gen → ExecPlan → Adapter → subprocess → ExecResult → Fidelity → Evidence
  GAP        REAL       REAL       REAL          GAP(门禁)     REAL        PARTIAL

Claim → Validation → Gate → Decision → FAIL → Diagnosis → Revision → M2
FAKE    REAL*(部分)  STRUCT   REAL(候选)  REAL    GAP         GAP        REAL(部分)

Re-execution → Comparison → Accept/Reject
    REAL           GAP            GAP
```

| 环节 | 状态 | 一句话 |
|---|---|---|
| Problem → Representation | **GAP** | V3 不读题面，只建 6 键粗画像 |
| Representation → Candidate | **REAL(条件)** | 候选生成真实，但生产路径生成后即弃 |
| Candidate → Evaluation | **FAKE(默认)** | 默认无任何评估；候选模式有真实 VR |
| Evaluation → Selection | **FAKE(默认)** | recs[0] 硬编码，无证据；候选模式 REAL |
| Selection → MODEL_IR | **GAP** | 结构完整但默认从不实例化（MIR=0） |
| MODEL_IR → Artifact | **GAP** | 薄壳 {card_id, family, shortlist}，provenance 空 |
| Artifact → Code Gen | **GAP** | core 不生成代码，只登记外部代码 |
| Code Gen → ExecPlan | **REAL** | 结构真实，但无"从 MODEL_IR 派生"校验 |
| ExecPlan → Adapter | **REAL** | LocalPythonAdapter 真 subprocess |
| Adapter → subprocess | **REAL** | 真 subprocess，非模拟 |
| subprocess → ExecResult | **GAP** | 真实创建点存在，但无 schema 门禁，Agent 可伪造 |
| ExecResult → Fidelity | **REAL** | 基于真实 outputs 机械计算（可被伪造 outputs 间接操纵） |
| Fidelity → Evidence | **PARTIAL** | 边真实写入，但 claim 是占位符 |
| Evidence → Claim | **FAKE** | "{qid} 结论" 占位符，流入论文 |
| Claim → Validation | **REAL*** | run_numeric_validation 真实但硬编码单问题；21 modules 死代码 |
| Validation → Gate | **STRUCTURAL** | evidence_gate 零数值计算 |
| Gate → Decision | **REAL(候选)** | 基于 VR 机械排序，reasoning 含数值；默认无 decision |
| Decision → FAIL | **REAL** | VR failed 真实判出 |
| FAIL → Diagnosis | **GAP** | 无诊断代码，只有 retry→rollback |
| Diagnosis → Revision | **GAP** | 无自动修订，M2 来自预写 fixtures |
| Revision → M2 | **REAL(部分)** | revision_of 边真实存在，但方向矛盾、生命周期未接通 |
| M2 → Re-execution | **REAL** | 真实 subprocess 重执行 |
| Re-execution → Comparison | **GAP** | 无 M1/M2 比较逻辑 |
| Comparison → Accept/Reject | **GAP** | 无决策类型 |

**闭环判定**：24 个环节中，REAL 8 个、GAP 11 个、FAKE 3 个、PARTIAL 1 个、STRUCTURAL 1 个。
**REAL 率 = 8/24 = 33%**。核心构建+验证+修订段（Representation→MODEL_IR→Evidence→Revision→Comparison）的 REAL 率更低。

---

## PROPOSED BATCH PLAN（修复批次计划）

### Batch 1：P0 Scientific Integrity（最高优先级）
**目标**：消除 Agent 伪造事实字段的能力，让执行失败真实传播。

| 修复项 | 对应发现 | 测试 | 独立复审 |
|---|---|---|---|
| ExecutionResult data schema 门禁（status 枚举/必填字段/code_hash 校验） | P0-01 | test_execution_result_schema_gate（伪造 data 必须被拒绝） | Auditor C 复审 |
| 执行失败传播（do_model_execution 失败应 FAIL；_results_of 过滤 failed） | P0-08 | test_execution_failure_propagates | Auditor C 复审 |
| evidence_gate 增加数值真实性检查（EXEC 必须存在且 success、outputs 非空） | P0-07 | test_evidence_gate_rejects_not_executed | Auditor D 复审 |
| Claim 占位符拦截（placeholder claim 不得 supported；claim_quality 检测占位符） | P0-06 | test_placeholder_claim_rejected | Auditor D 复审 |
| 修正测试中把错误行为编码为预期的断言 | P0-12 | test_e2e_metrics 修正 | Auditor G 复审 |
| K003 runner 契约修复（从 registry 读 EXEC，不用 pipe_result.get） | P0-03 | test_k003_runner_contract | Auditor F 复审 |

### Batch 2：MODEL_IR + Candidate + Selection 真实化
**目标**：让默认路径真正产生 MODEL_IR，selection 基于证据。

| 修复项 | 对应发现 | 测试 | 独立复审 |
|---|---|---|---|
| 默认路径必须产 MODEL_IR（无注入时 FAIL 或 pending_model_ir） | P0-05 | test_default_path_produces_mir | Auditor B 复审 |
| Selection 无证据时声明 UNSELECTED（不硬编码 recs[0]） | P0-04 | test_selection_requires_evidence | Auditor B 复审 |
| MODEL_IR 增加 code_mapping 字段 | P1-03 | test_model_ir_code_mapping | Auditor B 复审 |
| Evidence Graph 增加 evaluated_by/selected_from 边 | P1-04 | test_candidate_evidence_edges | Auditor B/D 复审 |
| V3 读取 question_spec.json（题面进入认知管线） | P1-08 | test_v3_reads_question_spec | Auditor B 复审 |
| 候选竞技场接入生产 orchestrator | P1-11 | test_orchestrator_uses_arena | Auditor A/B 复审 |

### Batch 3：Code Generation → Execution 接通
**目标**：MODEL_IR → Code 有真实映射，执行管线统一。

| 修复项 | 对应发现 | 测试 | 独立复审 |
|---|---|---|---|
| MODEL_IR→Code 映射校验（implementation_ref 必须指向真实 CODE artifact） | P1-03/P1-09 | test_ir_code_mapping_validated | Auditor C 复审 |
| 统一执行管线（codegen+fidelity 平行管线并入生产链） | P1-12 | test_unified_execution_pipeline | Auditor A/C 复审 |
| ExecutionPlan 增加"从 MODEL_IR 派生"校验 | P1-09 | test_execplan_derived_from_mir | Auditor C 复审 |

### Batch 4：ExecutionResult + Evidence 硬化
**目标**：Evidence 真正来自执行，provenance 完整。

| 修复项 | 对应发现 | 测试 | 独立复审 |
|---|---|---|---|
| Evidence 必须携带 execution_result_id + code_hash + output | P0-01/P0-07 | test_evidence_has_provenance | Auditor D 复审 |
| Claim 结论合成（从 result 数值生成真实 statement） | P0-06 | test_claim_synthesis | Auditor D 复审 |
| K003 rebuild 脚本提交（可复现） | P1-01/P1-18 | test_k003_rebuild_reproducible | Auditor F 复审 |
| K003 执行权限分离（独立执行进程写 execution_result） | P0-02 | test_generator_cannot_write_exec_result | Auditor F 复审 |
| K003 submission ID 随机化 + run_order 冻结 | P0-09 | test_blind_id_unlinkable | Auditor F 复审 |

### Batch 5：Validation 真实化
**目标**：L0-L4 每级真正执行计算。

| 修复项 | 对应发现 | 测试 | 独立复审 |
|---|---|---|---|
| 21 个 validator modules 接入管线或如实声明死代码 | P1-07/P1-16 | test_validators_actually_run | Auditor D 复审 |
| run_numeric_validation 通用化（不硬编码单问题键名） | P2-03 | test_validation_generic_problems | Auditor D 复审 |
| L2 Mathematical 真实接线（equation consistency/dimensional consistency） | P2-02 | test_mathematical_validation | Auditor D 复审 |
| L4 Empirical 真实计算（sensitivity/residual/error） | P2-02 | test_empirical_validation | Auditor D 复审 |
| jsonschema 实例校验接入 runtime registry | P1-09 | test_schema_enforced_at_registry | Auditor A/D 复审 |

### Batch 6：Revision Loop 真实化
**目标**：FAIL→诊断→修订→M2→比较→决策 完整闭环。

| 修复项 | 对应发现 | 测试 | 独立复审 |
|---|---|---|---|
| Failure Diagnosis 模块（基于 VR/EXEC 失败分析原因） | P2-04 | test_failure_diagnosis | Auditor E 复审 |
| Revision Proposal 生成（基于诊断 + M1 结构生成 M2 草案） | P2-05 | test_revision_proposal | Auditor E 复审 |
| supersedes 边方向统一 + registry.supersede 接入 core | P2-06/P2-07 | test_supersedes_direction | Auditor E 复审 |
| changed_components 结构化字段（M1/M2 diff） | P2-10 | test_changed_components | Auditor E 复审 |
| M1/M2 比较逻辑（指标对比 + delta 记录） | P2-08 | test_m1_m2_comparison | Auditor E 复审 |
| Accept/Reject 决策类型 | P2-09 | test_revision_accept_reject | Auditor E 复审 |

### Batch 7：完整 E2E 真实案例
**目标**：一个真实数学建模题从 Problem 走到 Model V2。

| 修复项 | 对应发现 | 测试 | 独立复审 |
|---|---|---|---|
| 选择真实题目，执行完整闭环（≥3 候选→Selection→MODEL_IR→Code→Execution→Evidence→Validation→FAIL→Revision→M2→Compare→Decision） | 全部 | e2e_real_case 测试 | 全新 Agent 独立审查 |
| 保存全部产物（problem/model_ir/candidates/selection/code/execution_result/stdout/stderr/evidence/validation/revision/comparison/decision） | 全部 | artifact_completeness 检查 | 全新 Agent 独立审查 |

### Batch 8：测试可信度审计与修复
**目标**：TEST_TRUST_SCORE 从 69.2 提升到 ≥85。

| 修复项 | 对应发现 | 测试 | 独立复审 |
|---|---|---|---|
| e2e/test_pipeline.py 从占位符改为真实执行 | P1-13 | test_e2e_actually_runs | Auditor G 复审 |
| 所有"只查字段存在"的测试增加数值断言 | P1-15 | 逐测试修正 | Auditor G 复审 |
| 21 个 validator modules 补测试 | P1-16 | test_validator_modules | Auditor G 复审 |
| claim 占位符增加测试覆盖 | P1-14 | test_claim_placeholder | Auditor G 复审 |
| 单文件运行验证（消除 import side effect 依赖） | G 审计 | test_single_file_runs | Auditor G 复审 |

### Batch 9：实验体系审计与修复
**目标**：K001/K002/K003 科学有效性达标。

| 修复项 | 对应发现 | 测试 | 独立复审 |
|---|---|---|---|
| K003 停线审查（执行权限分离+ID 去确定性+接入真实 Agent 构造） | P0-02/P0-09/P0-10 | k003_governance_gate | Auditor F 复审 |
| K003 伪重复修复（rep 真正独立构造） | P1-17 | test_replication_independence | Auditor F 复审 |
| K002 格式不对称混淆修复或如实声明 | P2-11 | k002_confound_control | Auditor F 复审 |
| K001 补充有效 block=2 敏感性分析 | P2-12 | k001_sensitivity | Auditor F 复审 |
| formal_results.json 一致性门禁 | P0-11 | test_formal_results_consistency | Auditor F/H 复审 |

### Batch 10：最终架构审计
**目标**：全新 Agent 不看之前结论，只看最终仓库，回答"系统真的能完成 Mathematical Model Construction Loop 吗？"

| 修复项 | 对应发现 | 测试 | 独立复审 |
|---|---|---|---|
| contracts.py 契约层接线（终态元组统一） | P3-03 | test_contracts_enforced | 全新 Agent |
| V2 legacy 路径修复（SKILL 路径从 catalog 派生） | P3-01/P3-02 | test_legacy_skill_paths | 全新 Agent |
| STATUS.md 数字与实测一致（含 validate.py 57 项修复） | P2-13/P4-01/P4-03 | test_status_numbers_match | 全新 Agent |
| 文档与代码一致性（README/HANDOFF/catalog 注释） | P4-02/P4-03 | docs_consistency | 全新 Agent |
| 最终全链路验证 + 独立专家攻击测试 | 全部 | full_regression + independent_audit | 全新 Agent |

---

## 对最终 10 个问题的回答

### 1. 当前系统真正能不能完成 Mathematical Model Construction？
**不能。** 默认生产路径下，Problem→Representation→Candidate→Selection→MODEL_IR 链中 4/5 环节是 GAP 或 FAKE。系统只能在外部注入完整 MODEL_IR+代码的前提下完成 Execution→Validation 段。

### 2. 哪些环节是真的，哪些只是 architecture？
- **真的**：subprocess 执行、duration、code_hash、fidelity、数值验证（单问题）、Artifact Registry、Evidence Graph（存储）、候选生成（结构）、候选模式选型、M2 重执行、revision_of 边、DecisionLog、Replay、冻结哈希
- **只是 architecture**：MODEL_IR（结构完整但不实例化）、Validation 分层（21 modules 死代码）、Evidence Gate（零数值）、Claim（占位符）、Failure Diagnosis（只有 retry）、Revision Proposal（M2 来自预写）、M1/M2 Comparison（不存在）、Accept/Reject（不存在）、contracts.py（零调用）、Schema 校验（无消费方）

### 3. 哪些地方仍然存在 fake completion 风险？
- 默认路径不产 MODEL_IR 仍 PASS（P0-05）
- Selection 硬编码 recs[0]（P0-04）
- Claim 占位符流入论文（P0-06）
- evidence_gate 零数值（P0-07）
- 执行失败不传播（P0-08）
- ExecutionResult 无门禁可伪造（P0-01）
- 测试把错误行为编码为预期（P0-12）

### 4. Agent 可以伪造哪些事实？
见上方"Agent 可伪造字段清单"。核心：ExecutionResult 全字段、Claim 全字段、Candidate/MODEL_IR/VR 全字段（通过注入）、Evidence Graph 边、problem_features。唯一不能直接伪造的是 subprocess returncode。

### 5. Execution 是否完全机械化？
**subprocess 层是**（LocalPythonAdapter 真执行），但 **ExecutionResult 落库层不是**（无 schema 门禁，Agent 可绕过 adapter 直接 registry.create）。K003 已证明这一点。

### 6. Evidence 是否来自真实执行？
**部分是**。当由 adapter 创建时，EXEC artifact 数据真实。但：(1) Agent 可伪造 EXEC；(2) evidence_gate 不验证数值真实性；(3) claim 是占位符不引用具体数值。

### 7. Validation 是否真正影响决策？
**候选模式下是**（do_model_selection_decision 基于 VR 指标排序）。**默认路径下否**（无 decision，且 evidence_gate 的 WEAK/FAIL 语义矛盾）。

### 8. Revision 是否真正存在？
**谱系记录存在，自动化闭环不存在。** revision_of 边真实落盘，M2 真实重执行。但：无诊断、无修订提案、无 M1/M2 比较、无 Accept/Reject 决策。4/8 环节缺失。

### 9. 一个真实数学建模题能否从 Problem 一直走到 Model V2？
**不能（默认路径）。** 需要人工注入 MODEL_IR + 代码 + 预写 M2 + 硬编码诊断。P1 实验证明了"注入式闭环"可行，但不是系统自驱动。

### 10. 如果现在公开这个项目，最容易被攻击的 10 个点是什么？
1. **ExecutionResult 可伪造** — registry.create 无门禁，任何 Agent 可写假执行结果（K003 已实锤）
2. **默认路径不产 MODEL_IR** — 声称"模型构建"实际只建方法卡 ID，3 个真实项目 MIR=0
3. **Selection 硬编码** — recs[0] 不是选型，是取第一个
4. **Claim 占位符流入论文** — "{qid} 结论" 出现在论文大纲"结果与分析"节
5. **evidence_gate 零数值** — "证据门禁通过"不代表有证据，not_executed 可过
6. **21 个 validator 死代码** — "六层防御验证"从未运行，validate.py 只查类名字符串
7. **Revision Loop 4 环节缺失** — 无诊断/无提案/无比较/无决策，"修订闭环"名不副实
8. **K003 实验科学失效** — 无真实外部 Agent、伪重复、盲评不盲、发生过伪造
9. **e2e 测试是占位符** — 3/4 核心 e2e 测试 skip，911 绿不代表系统工作
10. **执行失败不传播** — do_model_execution 无条件 PASS，failed 结果可支撑 claim

---

## 审计产物清单

| 产物 | 路径 |
|---|---|
| 本裁决 | `research/audit/SYSTEM_VERDICT.md` |
| 数据流地图 | `research/audit/DATAFLOW.md` |
| 发现汇总 | `research/audit/AUDIT_FINDINGS.md` |
| 修复计划 | `research/audit/IMPLEMENTATION_PLAN.md` |
| Agent A 架构审计 | `research/audit/audit_a/FINDINGS.md` |
| Agent B 模型构建审计 | `research/audit/audit_b/FINDINGS.md` |
| Agent C 执行审计 | `research/audit/audit_c/FINDINGS.md` |
| Agent D 证据验证审计 | `research/audit/audit_d/FINDINGS.md` |
| Agent E 修订审计 | `research/audit/audit_e/FINDINGS.md` |
| Agent F 实验审计 | `research/audit/audit_f/FINDINGS.md` |
| Agent G 测试审计 | `research/audit/audit_g/FINDINGS.md` |
| Agent H 治理审计 | `research/audit/audit_h/FINDINGS.md` |
