# IMPLEMENTATION_PLAN — MathModel 模型构建闭环修复实施计划

> **基线**：HEAD `d44384c`，Batch 0 审计产物 `research/audit/`
> **原则**：每个修复必须包含 Finding → Design → Files → API change → Migration → Tests → Integration test → Failure test → Regression test → Commit
> **纪律**：不要为了通过测试而修改测试语义；不要因为文档声称完成就认为完成；不要扩张无关功能。

---

## Batch 1：P0 Scientific Integrity（阻断级）

### FIX-1.1：ExecutionResult data schema 门禁

| 项 | 内容 |
|---|---|
| **Finding** | P0-01（C-001）：`registry.create("execution_result", data=任意dict)` 无 schema 门禁，Agent 可伪造 |
| **Design** | 在 `Artifact.validate()` 中增加按 type 分发的 data schema 校验。execution_result 必须校验：status ∈ {success,failed,timeout,invalid,not_executed}、execution_id 非空、code_hash == sha256(code)（当 code 存在时）、duration_ms ≥ 0、outputs 为 dict。引入 `core/schemas/v3/execution_result.schema.json`。 |
| **Files** | `core/runtime/artifacts/artifact.py`（validate 增加 type dispatch）、`core/schemas/v3/execution_result.schema.json`（新建）、`core/runtime/artifacts/registry.py`（create 时调用增强 validate） |
| **API change** | `Artifact.validate()` 返回从 bool 改为 `ValidationResult(valid: bool, errors: list[str])`；`registry.create()` 在 validation fail 时 raise `ArtifactSchemaError` |
| **Migration** | 现有 registry.json 中的 EXEC artifact 需通过 schema；K003 重建产物已含真实字段应通过；旧空壳产物（dad33cd 版本）应 fail-closed，需在迁移脚本中标记为 invalid |
| **Tests** | `test_execution_result_schema_gate`：伪造 data（status="fake"/outputs="not dict"/code_hash 不匹配）必须被拒绝 |
| **Integration test** | 完整执行链：adapter 真实执行 → registry.create → 验证通过；伪造路径 → registry.create → 验证拒绝 |
| **Failure test** | subprocess 失败（returncode≠0）→ EXEC status=failed → schema 通过（failed 是合法状态）；timeout → status=timeout → 通过 |
| **Regression test** | 现有 911 测试全绿（可能需修正依赖空壳 EXEC 的测试）；`py -3.12 -m pytest tests -q` |
| **Commit** | `fix(exec): execution_result schema gate — reject fabricated data` |
| **独立复审** | Auditor C 重新审查：确认 Agent 无法绕过 adapter 直接创建合法 EXEC |

### FIX-1.2：执行失败真实传播

| 项 | 内容 |
|---|---|
| **Finding** | P0-08（C-007/C-008）：`do_model_execution` 无条件 PASS；`_results_of` 不过滤 failed |
| **Design** | `do_model_execution` 在 EXEC status != success 时返回 FAIL（含失败原因）；`_results_of` 增加 `include_failed=False` 参数，claim 构建默认排除 failed 结果；增加 `execution_failure` 反馈环触发。 |
| **Files** | `core/runtime/execution/handlers.py:525-534`（do_model_execution）、`handlers.py` `_results_of`、`core/runtime/execution/engine.py`（on_fail 接线） |
| **API change** | `_results_of(registry, qid, include_failed=False)` 新签名；`do_model_execution` 返回 NodeResult FAIL 时含 `exec_id` 和 `stderr_tail` |
| **Migration** | 现有依赖"执行恒 PASS"的下游节点需处理 FAIL 路径；DAG 的 on_fail 已接线（engine._handle_failure），需确认 model_execution 节点的 on_fail 指向合理节点 |
| **Tests** | `test_execution_failure_propagates`：注入 raise 代码 → 执行 → do_model_execution 返回 FAIL → claim 不包含该结果 |
| **Integration test** | 完整链：坏代码 → EXEC failed → 节点 FAIL → 反馈环 → retry → blocked（耗尽后） |
| **Failure test** | timeout 代码 → EXEC timeout → 节点 FAIL；invalid 语法 → EXEC invalid → 节点 FAIL |
| **Regression test** | 好代码路径仍 PASS；911 测试全绿 |
| **Commit** | `fix(exec): propagate execution failure — do_model_execution fails on non-success` |
| **独立复审** | Auditor C 重新审查：确认 execution failed → validation FAIL → decision FAIL 传播链完整 |

### FIX-1.3：evidence_gate 增加数值真实性检查

| 项 | 内容 |
|---|---|
| **Finding** | P0-07（D-001）：E1-E8 零数值计算，not_executed 链可结构 PASS |
| **Design** | 增加 E9（数值真实性）：claim 支撑链中必须存在 EXEC artifact 且 status=="success"、outputs 非空；result.data.status=="not_executed" 时 E4 降级为 fail；E6 增加 data.status 检查（不仅 lifecycle draft）。 |
| **Files** | `core/validators/evidence/evidence_gate.py:87-181`（evaluate 增加 E9 + 增强 E4/E6） |
| **API change** | `GateReport` 增加 `numerical_authenticity: bool` 字段；E9 失败时 verdict 至少 WEAK |
| **Migration** | 默认 runtime 路径大量 result 为 not_executed，加严后门禁会 FAIL → 需同步 FIX-1.5（修正测试）和 Batch 2（默认路径产真实 MIR/执行） |
| **Tests** | `test_evidence_gate_rejects_not_executed`：构造 not_executed 链 → evaluate → FAIL/WEAK；`test_evidence_gate_passes_real_execution`：真实 EXEC → PASS |
| **Integration test** | 完整链：真实执行 → evidence_build → gate → PASS；无执行 → gate → FAIL |
| **Failure test** | EXEC status=failed → gate → FAIL（claim 不能由失败执行支撑） |
| **Regression test** | 现有 evidence_gate 测试需更新断言（not_executed 不再 PASS）；911 测试 |
| **Commit** | `fix(evidence): gate numerical authenticity — reject not_executed chains` |
| **独立复审** | Auditor D 重新审查：确认 gate 能区分"真跑过"与"没跑过" |

### FIX-1.4：Claim 占位符拦截 + 结论合成

| 项 | 内容 |
|---|---|
| **Finding** | P0-06（D-002）：claim statement = "{qid} 结论" 占位符，流入论文 |
| **Design** | (1) 占位 claim（placeholder=True）不得获得 supports 边标记为 supported；(2) claim_quality 增加占位符词检测（statement 形如 `.*结论$` 且 == title 时判 weak/fail）；(3) 增加 `synthesize_claim` 函数：从 EXEC outputs + VR 结果由确定性模板生成真实 statement（如"模型预测 y=13.2，约束违反度=0.0"）。 |
| **Files** | `core/runtime/execution/handlers.py:1219-1227`（do_evidence_build）、`core/validators/quality/evaluators.py:331`（claim_quality）、新建 `core/runtime/execution/claim_synthesis.py` |
| **API change** | `do_evidence_build` 在无真实结果时创建 placeholder claim 但不写 supports 边；`synthesize_claim(exec_id, vr_id) -> statement` 新函数 |
| **Migration** | 现有论文投影路径（director→narrative→projection）需处理 placeholder claim（跳过或标记"待回填"） |
| **Tests** | `test_placeholder_claim_rejected`：占位 claim → claim_quality → weak/fail；`test_claim_synthesis`：真实 EXEC+VR → synthesize → statement 含具体数值 |
| **Integration test** | 完整链：真实执行 → evidence_build → synthesize → claim statement 含数值 → gate → PASS |
| **Failure test** | 无 EXEC → claim 保持 placeholder → gate → FAIL（由 FIX-1.3 保证） |
| **Regression test** | 911 测试（test_runtime_session 的 claims_supported=2 断言需修正） |
| **Commit** | `fix(evidence): block placeholder claims + add deterministic claim synthesis` |
| **独立复审** | Auditor D 重新审查：确认论文大纲不再含 "{qid} 结论" 占位符 |

### FIX-1.5：修正测试中把错误行为编码为预期的断言

| 项 | 内容 |
|---|---|
| **Finding** | P0-12（G-002）：test_e2e_metrics 断言 legacy pointer → structural_pass is None；test_runtime_session 断言 claims_supported=2 |
| **Design** | 修改测试断言为正确行为：无 MIR 应 FAIL（非 None）；占位 claim 不应 supported。这不是"修改测试使其通过"，而是修正测试以匹配正确的系统行为（配合 FIX-1.1~1.4 的代码修复）。 |
| **Files** | `tests/e2e/test_e2e_metrics.py`、`tests/integration/test_runtime_session.py` |
| **API change** | 无（仅测试断言修正） |
| **Migration** | 无 |
| **Tests** | 修正后的测试本身 |
| **Integration test** | 修正后测试在修复后的代码上通过 |
| **Failure test** | 在未修复代码上，修正后的测试应 FAIL（证明测试能捕捉问题） |
| **Regression test** | 911 测试全绿 |
| **Commit** | `test: fix assertions that encoded broken behavior as expected` |
| **独立复审** | Auditor G 重新审查：确认测试不再把占位/缺失编码为正确 |

### FIX-1.6：K003 runner 契约修复

| 项 | 内容 |
|---|---|
| **Finding** | P0-03（C-002）：k003_formal_runner.py 用 pipe_result.get("outputs"/...) 但 run_code_pipeline 不返回这些 key |
| **Design** | 删除 runner 中所有 `pipe_result.get("outputs"/"duration_ms"/"code_hash"/...)`，改为从 registry 读 EXEC 数据（照抄 precheck k003_runner.py:348-367 的正确写法）。或扩展 run_code_pipeline 返回完整字段。 |
| **Files** | `research/P15/experiments/P15-K003/k003_formal_runner.py:720-758` |
| **API change** | 无（research 脚本内部修复）；或 `run_code_pipeline` 返回增加 outputs/duration_ms/code_hash 等字段 |
| **Migration** | 现有 66 份产物已由 rebuild 修复（d44384c），runner 修复后复跑应产出一致结果 |
| **Tests** | `test_k003_runner_contract`：mock run_code_pipeline 返回 7 字段 → 断言落盘文件不含空壳 |
| **Integration test** | 单题单臂复跑 → execution_result 含真实 outputs/duration/hash |
| **Failure test** | run_code_pipeline 返回空 → runner 应从 registry 读（而非写空壳） |
| **Regression test** | K003 precheck runner 仍工作 |
| **Commit** | `fix(k003): runner contract — read exec data from registry not pipe_result` |
| **独立复审** | Auditor F 重新审查：确认 runner 复跑不再产出空壳 |

---

## Batch 2：MODEL_IR + Candidate + Selection 真实化

### FIX-2.1：默认路径必须产 MODEL_IR

| 项 | 内容 |
|---|---|
| **Finding** | P0-05（B-002）：do_model_construction 无注入时只登记假设，不产 MIR，节点 PASS |
| **Design** | 无外部注入时，`do_model_construction` 应基于选中方法卡 + problem features 生成最小可用 MODEL_IR（至少含 problem_binding/assumptions/variables/objectives/equations/solvers），或明确返回 FAIL（`pending_model_ir`）。不允许"只登记假设就 PASS"。 |
| **Files** | `core/runtime/execution/handlers.py:891-930`、`core/runtime/modeling/model_ir.py`（增加 from_method_card 构造器） |
| **API change** | `ModelIR.from_method_card(card, features) -> ModelIR` 新类方法；`do_model_construction` 返回 FAIL 时含 `reason="no_model_ir"` |
| **Migration** | 现有 3 个真实项目的 registry 无 MIR，重跑后应产生 MIR 或明确 FAIL |
| **Tests** | `test_default_path_produces_mir`：无注入运行 → registry 含 MIR artifact 或节点 FAIL |
| **Integration test** | orchestrator --execute → state/registry.json 含 MIR |
| **Failure test** | 方法卡信息不足 → MIR 构造失败 → 节点 FAIL（非 PASS） |
| **Regression test** | 候选模式（外部注入）仍工作 |
| **Commit** | `fix(model): default path must produce MODEL_IR or fail` |
| **独立复审** | Auditor B 重新审查：确认默认路径 MIR>0 |

### FIX-2.2：Selection 无证据时声明 UNSELECTED

| 项 | 内容 |
|---|---|
| **Finding** | P0-04（B-001）：selection.py:60 chosen=recs[0] 硬编码 |
| **Design** | `MethodArena.select` 在无 VR/执行证据时返回 `chosen="UNSELECTED", confidence=0.0, selection_status="pending_evidence"`（候选模式已实现此语义，handlers.py:672-674）。默认路径应复用此语义，不硬编码 recs[0]。 |
| **Files** | `core/runtime/modeling/selection.py:46-121` |
| **API change** | `SelectionOutcome` 增加 `selection_status` 字段；无证据时 chosen="UNSELECTED" |
| **Migration** | 下游依赖 model.card_id 的节点需处理 UNSELECTED |
| **Tests** | `test_selection_requires_evidence`：无 VR → chosen=UNSELECTED；有 VR → 基于指标选择 |
| **Integration test** | 默认路径 → selection_status=pending_evidence |
| **Failure test** | 空 recs → 不崩溃，返回 UNSELECTED |
| **Regression test** | 候选模式选型仍工作 |
| **Commit** | `fix(model): selection requires evidence — UNSELECTED when no VR` |
| **独立复审** | Auditor B 重新审查：确认系统能回答"为什么选这个模型" |

### FIX-2.3：MODEL_IR 增加 code_mapping 字段

| 项 | 内容 |
|---|---|
| **Finding** | P1-03（B-003）：全仓 code_mapping 0 匹配 |
| **Design** | ModelIR 增加 `code_mapping: dict[str, str]` 字段（equation_id → code section/symbol），schema 同步更新。codegen 登记代码时校验 implementation_ref 指向真实 CODE artifact。 |
| **Files** | `core/runtime/modeling/model_ir.py:70-99`、`core/schemas/v3/model/model_ir.schema.json` |
| **API change** | ModelIR dataclass 增加 code_mapping 字段（可选，默认 {}） |
| **Migration** | 现有 fixtures 需补 code_mapping（或留空 {}） |
| **Tests** | `test_model_ir_code_mapping`：MIR 含 code_mapping → schema 校验通过 |
| **Integration test** | MIR → code 登记 → implementation_ref 校验 |
| **Failure test** | implementation_ref 指向不存在的 CODE → 校验失败 |
| **Regression test** | 现有 MIR 测试通过 |
| **Commit** | `feat(model): add code_mapping to MODEL_IR` |
| **独立复审** | Auditor B 重新审查 |

### FIX-2.4：Evidence Graph 增加 evaluated_by/selected_from 边

| 项 | 内容 |
|---|---|
| **Finding** | P1-04（B-004）：RELATION_TYPES 无 evaluated_by/selected_from |
| **Design** | 增加 `evaluated_by`（candidate → VR/EXEC）和 `selected_from`（selected_model → candidate）边类型。do_model_selection_decision 写入这些边。 |
| **Files** | `core/runtime/graph/evidence_graph.py:33-53`、`core/runtime/execution/handlers.py:639-740` |
| **API change** | RELATION_TYPES 增加两个边；传播语义均为弱边（不传播失效） |
| **Migration** | 现有 graph 无这些边，不影响旧数据 |
| **Tests** | `test_candidate_evidence_edges`：候选评估后 → graph 含 evaluated_by；选型后 → 含 selected_from |
| **Integration test** | 候选竞技场全流程 → graph 含完整边 |
| **Failure test** | 无 |
| **Regression test** | 现有 graph 测试通过 |
| **Commit** | `feat(evidence): add evaluated_by/selected_from edge types` |
| **独立复审** | Auditor B/D 重新审查 |

### FIX-2.5：V3 读取 question_spec.json

| 项 | 内容 |
|---|---|
| **Finding** | P1-08（B-007）：V3 不读题面，只建 6 键粗画像 |
| **Design** | RuntimeSession 初始化时读取项目 `inputs/question_spec.json`（或题面文本），解析为结构化 representation（background/problems/constraints/data/delivery），传入 features 和后续建模节点。 |
| **Files** | `core/runtime/execution/session.py`、`core/runtime/execution/handlers.py:778-788`（do_problem_analysis） |
| **API change** | `ProblemRepresentation` dataclass（新建）；session 增加 `problem_repr` 属性 |
| **Migration** | 现有项目无 question_spec.json 时回退到 features 粗画像（但标记 source=legacy_fallback） |
| **Tests** | `test_v3_reads_question_spec`：有 spec → problem_repr 含题面内容 |
| **Integration test** | orchestrator --execute → registry Question artifact 含题面 |
| **Failure test** | spec 格式错误 → 明确报错（非静默回退） |
| **Regression test** | 无 spec 时回退路径工作 |
| **Commit** | `feat(model): V3 reads question_spec into structured representation` |
| **独立复审** | Auditor B 重新审查 |

---

## Batch 3：Code Generation → Execution 接通

### FIX-3.1：MODEL_IR→Code 映射校验
- **Finding**：P1-03/P1-09
- **Design**：codegen.register_code 校验 MIR.solvers[].implementation_ref 指向已登记的 CODE artifact；code_hash 与 MIR.code_mapping 一致
- **Files**：`core/runtime/execution/codegen.py`
- **Tests**：`test_ir_code_mapping_validated`
- **Commit**：`fix(exec): validate MODEL_IR→CODE mapping`

### FIX-3.2：统一执行管线
- **Finding**：P1-12（A-005）：codegen+fidelity 平行管线不在生产链
- **Design**：将 codegen.run_code_pipeline 的能力并入 handlers.do_model_execution（或反向），消除双轨
- **Files**：`core/runtime/execution/handlers.py`、`core/runtime/execution/codegen.py`
- **Tests**：`test_unified_execution_pipeline`
- **Commit**：`refactor(exec): unify codegen and handler execution paths`

---

## Batch 4：ExecutionResult + Evidence 硬化

### FIX-4.1：Evidence 必须携带 execution provenance
- **Finding**：P0-01/P0-07
- **Design**：Evidence（claim + supports 边）必须引用具体 EXEC artifact_id；graph 边增加 `exec_ref` 字段；无 EXEC 引用的 evidence 不被 gate 认可
- **Files**：`core/runtime/graph/evidence_graph.py`、`core/runtime/execution/handlers.py`
- **Tests**：`test_evidence_has_provenance`
- **Commit**：`fix(evidence): require execution provenance on all evidence`

### FIX-4.2：K003 rebuild 脚本提交
- **Finding**：P1-01/P1-18（C-003/F-005）
- **Design**：提交 rebuild 脚本（读 registry → 重写 per-run execution_result.json/fidelity_report.json），记录脚本 commit hash
- **Files**：`research/P15/experiments/P15-K003/scripts/rebuild_execution_results.py`（新建）
- **Tests**：`test_k003_rebuild_reproducible`
- **Commit**：`feat(k003): commit rebuild script for reproducible execution results`

### FIX-4.3：K003 执行权限分离
- **Finding**：P0-02（F-001）
- **Design**：拆分执行为独立脚本，以只读方式接收表示产物，仅该进程可写 execution_result；增加 execution_result 与 registry 一致性校验
- **Files**：`research/P15/experiments/P15-K003/`（拆分 runner）
- **Tests**：`test_generator_cannot_write_exec_result`
- **Commit**：`fix(k003): separate execution writer from generator`

### FIX-4.4：K003 submission ID 随机化
- **Finding**：P0-09（F-002）
- **Design**：改用 uuid4；run_order 在 FROZEN 阶段生成并哈希冻结
- **Files**：`k003_formal_runner.py` make_submission_id、freeze 配置
- **Tests**：`test_blind_id_unlinkable`
- **Commit**：`fix(k003): randomize submission IDs + freeze run_order`

---

## Batch 5：Validation 真实化

### FIX-5.1：21 个 validator modules 接入或如实声明
- **Finding**：P1-07（D-003/G-006/H-004）
- **Design**：二选一：(a) 将 modules 中可复用的（formula_checker/symbolic_verifier/type_system）接入 DAG 对应节点；(b) 将 validate.py 的字符串存在性检查改为 import+冒烟执行，并在 STATUS.md 如实声明接线状态
- **Files**：`core/tools/validate.py:687-892`、`core/validators/modules/`
- **Tests**：`test_validators_actually_run`
- **Commit**：`fix(validation): wire validators into pipeline or declare dead code honestly`

### FIX-5.2：run_numeric_validation 通用化
- **Finding**：P2-03（D 审计）
- **Design**：从 MODEL_IR 的 variables/constraints/objectives 动态派生验证键名，不硬编码 pair_distances/head_speeds/positions
- **Files**：`core/runtime/execution/validation.py:180-291`
- **Tests**：`test_validation_generic_problems`
- **Commit**：`fix(validation): generic numeric validation from MODEL_IR`

### FIX-5.3：L2 Mathematical 真实接线
- **Finding**：P2-02
- **Design**：formula_checker（括号配对/LaTeX 语法）接入 MODEL_IR 校验节点；增加 dimensional consistency 检查
- **Files**：`core/validators/modules/formula_checker.py`、`core/runtime/execution/handlers.py`
- **Tests**：`test_mathematical_validation`
- **Commit**：`feat(validation): wire L2 mathematical validation`

### FIX-5.4：jsonschema 实例校验接入 registry
- **Finding**：P1-09（B-008/A-004）
- **Design**：pyproject 增加 jsonschema 依赖；registry.create 时按 type 加载对应 schema 做实例校验
- **Files**：`pyproject.toml`、`core/runtime/artifacts/registry.py`、`core/schemas/v3/`
- **Tests**：`test_schema_enforced_at_registry`
- **Commit**：`fix(schema): enforce jsonschema validation at registry.create`

---

## Batch 6：Revision Loop 真实化

### FIX-6.1：Failure Diagnosis 模块
- **Finding**：P2-04（E-001/E-003）
- **Design**：新建 `core/runtime/modeling/diagnosis.py`：基于 VR failed 项 + EXEC stderr + constraint_violation 分析失败原因，输出结构化 diagnosis（failed_components/root_cause/suggested_fixes）
- **Files**：新建 `core/runtime/modeling/diagnosis.py`、`core/runtime/execution/engine.py`（_handle_failure 调用 diagnosis）
- **Tests**：`test_failure_diagnosis`
- **Commit**：`feat(revision): add failure diagnosis module`

### FIX-6.2：Revision Proposal 生成
- **Finding**：P2-05（E-003/E-005）
- **Design**：基于 diagnosis + M1 MODEL_IR 结构生成 M2 草案（修改参数/方程/假设），标记 changed_components
- **Files**：新建 `core/runtime/modeling/revision.py`
- **Tests**：`test_revision_proposal`
- **Commit**：`feat(revision): generate revision proposal from diagnosis`

### FIX-6.3：supersedes 方向统一 + registry.supersede 接入
- **Finding**：P2-06/P2-07（E-002/E-007）
- **Design**：统一为"新 supersedes 旧"方向；handlers 调用 registry.supersede 标记旧 MIR 为 superseded
- **Files**：`core/runtime/execution/handlers.py`、`core/runtime/graph/evidence_graph.py`、`core/runtime/artifacts/registry.py`
- **Tests**：`test_supersedes_direction`
- **Commit**：`fix(revision): unify supersedes direction + wire registry.supersede`

### FIX-6.4：M1/M2 比较 + Accept/Reject 决策
- **Finding**：P2-08/P2-09/P2-10（E-008/E-009/E-010）
- **Design**：新建 comparison 逻辑（VR 指标 delta、fidelity delta、constraint_violation delta）；增加 revision_acceptance decision 类型（accept/reject + reasoning）
- **Files**：新建 `core/runtime/modeling/comparison.py`、`core/runtime/decisions/log.py`
- **Tests**：`test_m1_m2_comparison`、`test_revision_accept_reject`
- **Commit**：`feat(revision): M1/M2 comparison + accept/reject decision`

---

## Batch 7：完整 E2E 真实案例

### FIX-7.1：真实题目端到端闭环
- **Finding**：全部
- **Design**：选择一个真实数学建模题（如排队论/优化题），执行完整闭环：Problem→Representation→≥3 候选→Selection→MODEL_IR→Code→subprocess→ExecutionResult→Fidelity→Evidence→Validation→FAIL→Diagnosis→Revision→M2→Re-execution→Compare→Decision。保存全部产物到 `research/audit/e2e_real_case/`。
- **Files**：新建 `research/audit/e2e_real_case/`（全部产物）
- **Tests**：`test_e2e_real_case`（断言每环节产物存在且非占位）
- **Commit**：`feat(e2e): real mathematical problem end-to-end construction loop`
- **独立复审**：全新 Agent 不看之前结论，只看最终仓库和 e2e 产物

---

## Batch 8：测试可信度修复

### FIX-8.1：e2e 测试真实化
- **Finding**：P1-13（G-001）
- **Design**：test_pipeline.py 从 skip 改为真实执行（使用 FIX-7.1 的 e2e 路径）
- **Files**：`tests/e2e/test_pipeline.py`
- **Tests**：修正后的 e2e 测试
- **Commit**：`test(e2e): replace placeholder skips with real execution`

### FIX-8.2："只查字段存在"测试增加数值断言
- **Finding**：P1-15（G-004）
- **Design**：逐测试审查，对 evidence_gate/model_selection 等测试增加数值/内容断言
- **Files**：`tests/unit/test_evidence_gate.py`、`tests/unit/test_model_selection.py` 等
- **Tests**：修正后的测试
- **Commit**：`test: add numerical assertions to field-existence tests`

### FIX-8.3：TEST_TRUST_SCORE 提升到 ≥85
- **Design**：全部修复后重新运行 G 审计方法论，确认信任分提升
- **Commit**：`test: audit trust score ≥ 85`

---

## Batch 9：实验体系修复

### FIX-9.1：K003 停线审查
- **Finding**：P0-02/P0-09/P0-10（F-001/F-002/F-003）
- **Design**：执行权限分离（FIX-4.3）+ ID 随机化（FIX-4.4）+ 接入真实外部 Agent 构造（非罐头定义）。三者不解决则 K003 结果不可发布。
- **Commit**：`fix(k003): governance overhaul — execution separation + blind IDs + real agent`

### FIX-9.2：K003 伪重复修复
- **Finding**：P1-17（F-004）
- **Design**：每个 rep 为独立外部 Agent 构造（同一题同臂下不同构造尝试）
- **Commit**：`fix(k003): ensure independent replication per rep`

### FIX-9.3：K002 混淆控制
- **Finding**：P2-11（F-008）
- **Design**：呈现层统一（F/S/SV 臂输出格式一致），或如实声明格式不对称为混淆变量
- **Commit**：`fix(k002): control format confound or declare`

### FIX-9.4：formal_results.json 一致性门禁
- **Finding**：P0-11（H-002）
- **Design**：增加 formal_results.json 与 run_summary.json 一致性校验，纳入 freeze
- **Commit**：`fix(k003): formal_results consistency gate`

---

## Batch 10：最终架构审计

### FIX-10.1：contracts.py 接线
- **Finding**：P3-03（A-003）
- **Design**：终态元组统一从 contracts.py import，删除 ≥10 处内联；契约谓词在 session/engine 中调用
- **Commit**：`fix(arch): wire contracts.py — eliminate inline terminal tuples`

### FIX-10.2：V2 legacy 路径修复
- **Finding**：P3-01/P3-02（A-001/A-002）
- **Design**：_skill_path 从 catalog.yaml 派生，不硬编码
- **Commit**：`fix(legacy): derive SKILL paths from catalog.yaml`

### FIX-10.3：STATUS.md 数字修复
- **Finding**：P2-13/P4-01/P4-03（H-001/H-009/H-006）
- **Design**：validate.py 57 项修复（fixture PDF 入库或阈值调整）；测试基线更新为 911/4；README/HANDOFF 与 STATUS 统一
- **Commit**：`fix(docs): STATUS.md numbers match actual — validate 57/0, tests 911/4`

### FIX-10.4：最终全链路验证 + 独立专家攻击测试
- **Design**：全新 Agent 不看之前结论，只看最终仓库，回答"系统真的能完成 Mathematical Model Construction Loop 吗？"；模拟数学建模/Agent/软件工程专家攻击测试
- **Commit**：`audit(final): independent re-audit after all fixes`

---

## 修复优先级总表

| Batch | 主题 | 修复项数 | 阻断级 | 预计测试增量 |
|---|---|---|---|---|
| 1 | P0 Scientific Integrity | 6 | 是 | +12 |
| 2 | MODEL_IR + Candidate + Selection | 5 | 是 | +10 |
| 3 | Code Gen → Execution | 2 | 否 | +4 |
| 4 | ExecutionResult + Evidence | 4 | 是 | +8 |
| 5 | Validation 真实化 | 4 | 否 | +8 |
| 6 | Revision Loop | 4 | 是 | +8 |
| 7 | E2E 真实案例 | 1 | 是 | +1 |
| 8 | 测试可信度 | 3 | 否 | 修正现有 |
| 9 | 实验体系 | 4 | 是（K003） | +4 |
| 10 | 最终架构 | 4 | 否 | +2 |
| **合计** | | **37** | | **+57** |

---

## 不可违反的修复纪律

1. **不要为了通过测试而修改测试语义** — FIX-1.5 是修正错误断言，不是降低标准
2. **不要因为文档声称完成就认为完成** — 每个修复必须有磁盘证据
3. **不要扩张无关功能** — 只修审计发现的问题
4. **不要新增 Agent/Skill/Frontend 掩盖 Core Loop 缺失** — 修复在 core/ 层
5. **不要重新包装成 workflow orchestration** — 核心是让每一步有机械证据
6. **每个 Batch 完成后必须独立复审** — P0 修完→Auditor C/D 复审；Execution 修完→Auditor C 复审；Evidence 修完→Auditor D 复审；Revision 修完→Auditor E 复审
7. **每个 Batch 必须全量回归** — `py -3.12 -m pytest tests -q` 全绿方可 commit
8. **如果某一步无法真正实现，必须明确标记 BLOCKED / NOT IMPLEMENTED** — 不用 mock/placeholder/fallback 伪装
