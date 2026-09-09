# Model Construction Gap Audit — 下游半段（环节7–11）

- 审计对象：`C:\Users\Lin\Desktop\Programs\MathModel`（HEAD 4c80914，只读审计）
- 审计日期：2026-09-09
- 审计范围：环节7 Code Generation / 环节8 Execution / 环节9 Validation / 环节10 Evidence / 环节11 Revision
- 证据约定：`path:line` 为代码证据；`tests/...:line` 为测试断言证据；无证据一律标注 `not found / not demonstrated`
- 所有路径相对仓库根；Python 运行口径 `py -3.12`（本次未执行任何仓库内脚本，仅静态取证）

---

## 环节7 Code Generation

### 1. 真实存在什么代码？
- `core/runtime/execution/codegen.py`（P0-E7）：
  - `register_code(project_dir, code, ...)` — `codegen.py:44-76`，把外部 Agent 产出的 code 登记为 `code` 一等 artifact（data 含 code/language/framework/model_id/solver_id/output_mapping/sha256，`codegen.py:69-73`）。
  - `execute_code(project_dir, code_artifact_id, ...)` — `codegen.py:81-131`，从 CODE artifact 取代码经 `ExecutionAdapter` 真实执行，登记 `execution_result`（EXEC）并写 `executed_by` 边（`codegen.py:127-128`）。
  - `run_code_pipeline(...)` — `codegen.py:136-172`，register→execute→verify_fidelity 端到端。
  - CLI `main` — `codegen.py:175-193`。
- 执行后端：`core/runtime/execution/adapters.py` `LocalPythonAdapter`（`adapters.py:156-261`，真实 subprocess）。
- fidelity 校验：`core/runtime/execution/fidelity.py`（详见环节9）。
- 调用关系：`codegen.main → run_code_pipeline → register_code → execute_code → LocalPythonAdapter.execute → verify_fidelity`；`run_code_pipeline` 内部 import fidelity（`codegen.py:155`）。

### 2. 入口函数是什么？
- 代码级入口：`run_code_pipeline`（`codegen.py:136`）；CLI 入口 `main`（`codegen.py:175`，`python -m runtime.execution.codegen <项目> <model_ir.json> <code.py>`）。
- V3 DAG 中没有 code generation 节点：`catalog/v3.yaml:24-81` 的 16 个节点不含 code_gen；`experiment` 节点描述虽写"产出 CODE/E artifacts"（`core/workflows/stages/experiment.yaml:15`），但 handler `do_experiment`（`handlers.py:362-454`）只创建 experiment/result/figure，**从不创建 CODE artifact**。即生成侧完全在 V3 管线之外。

### 3. 真实输入是什么？
- `register_code`：`code: str`、`language: str`（非空校验 `codegen.py:59-62`）、`framework/model_id/solver_id/output_mapping/title/created_by/question`（`codegen.py:44-52`）。
- `execute_code`：`code_artifact_id: str`（必须为已注册的 `code` 类型，`codegen.py:100-101`）、`inputs: dict`、`adapter`、`timeout_seconds`、`result_id`。
- `ExecutionPlan` 契约：model_id/code/inputs/timeout_seconds/workdir/env/adapter/meta（`adapters.py:72-83`）。
- 无正式 JSON Schema 文件约束这些输入（见 Q4/环节9 Q1；`core/schemas/` 下无 code/execution_result schema）。

### 4. 真实输出是什么？
- `register_code` → `Artifact`（type=code，ID 前缀 CODE，`ids.py:26`）。
- `execute_code` → `Artifact`（type=execution_result，data 为 `ExecutionResultData.to_dict()`：execution_id/model_id/status/inputs/outputs/stdout/stderr/returncode/duration_ms/code_hash/environment_hash/started_at/finished_at/provenance/code/environment_manifest，`adapters.py:107-126`）。
- `run_code_pipeline` → dict `{code_id, exec_id, exec_status, verification_id, fidelity_status, fidelity_score, fidelity_report}`（`codegen.py:166-172`）。

### 5. 是否真的执行？
- **demonstrated**：`LocalPythonAdapter.execute` 用 `subprocess.run([python, script], capture_output=True, timeout=...)` 真实执行（`adapters.py:198-202`），status 由 `proc.returncode` 推导（`adapters.py:206`）。
- 测试证明：`tests/integration/test_execution_codegen.py:60-72`（success/failed 断言）、`tests/integration/test_execution_runtime.py:52-72`（真实执行 + executed_by 边）。
- 但 V3 生产入口 **不接 adapter**：`orchestrator._execute_v3` 构造 `RuntimeSession(project_dir, questions, max_workers=1, features=features)`（`core/tools/orchestrator.py:391-392`）未传 `execution_adapter`，`RuntimeSession.__init__` 默认 `execution_adapter=None`（`session.py:62`），导致 `_maybe_execute_experiment` 直接 return（`handlers.py:470-471`）。**默认 V3 管线不执行任何代码**。

### 6. 输出是否进入 Artifact Registry？
- 是：`register_code` 经 `reg.create("code", ...)`（`codegen.py:65-74`）；`execute_code` 经 `reg.create("execution_result", ...)`（`codegen.py:121-126`）；registry 持久化 `state/registry.json`（`registry.py:71-91`）。

### 7. 是否进入 Evidence Graph？
- 部分：`execute_code` 在 `result_id` 给定且存在时写 `result --executed_by--> execution_result`（`codegen.py:127-129`）。
- **`model --implemented_by--> code` 边从未被任何 V3 路径写入**：全仓 grep 显示 `implemented_by` 只出现在 schema/evidence_graph 定义与 legacy convert.py 注释（`core/runtime/legacy/convert.py:51,74`），没有任何 `add_relation(..., "implemented_by", ...)` 调用。即"模型被代码实现"这一核心谱系边在 V3 runtime 中 **contract exists, runtime not demonstrated**。

### 8. 该环节失败后能否回到 Model 层面继续？
- **否（V3 内无闭环）**：codegen 是独立 CLI/库路径，不在 DAG 中。fidelity misaligned 只影响 CLI 退出码 `return 0 if out["fidelity_status"]=="aligned" else 1`（`codegen.py:193`），不触发任何引擎 rollback。没有"code 不合格 → 回 model_construction 重建模"的路径。

### 9. 有没有假实现/placeholder/hardcoded default？
- 无明显假执行：`execute_code` 空 code 抛 ValueError（`codegen.py:59-62`、`execute_code:104-105`）。
- **但存在"无 adapter 即不执行"的静默降级**：`handlers.py:470-477` 在 `execution_adapter is None` 或 plan 无 `code` 时静默 return，result 保持 `not_executed`（`handlers.py:431-432` 明写 note"确定性 runtime 不执行数值计算；真实结果须由外部 executor 经 register_external_artifact 回填后翻为 executed"）。
- **`register_external_artifact` 不存在**：全仓 grep 仅命中该 note（`handlers.py:432`），无实现——回填路径是文档承诺，非代码。
- V3 默认管线：实验/结果/图/claim 全部是"登记型"产物（见环节8/10），数值从未产生。

### 10. 距离"真实 Model Construction"还差什么？
- DAG 中无 code generation 节点：`experiment_design` 输出声明 `[state/experiment_plan.json]`（`experiment.yaml:11`），但 plan 无 code 字段（`planner.py:81-91` 的 `as_dict` 只有 methods/required_checks/preflight_guards/failure_watchlist/baseline_comparison/sensitivity/entries），`_maybe_execute_experiment` 的 `for cand in plan: if cand=="code"`（`handlers.py:473-476`）在真实 plan 上永远找不到 code。
- 缺 `model.implemented_by→code` 边写入；缺"生成代码 ↔ MODEL_IR 声明"的端到端 DAG 节点；缺可执行代码的自动来源（目前只能靠测试里手工注入 `shared[qid]["plan"]={"code": ...}`，`tests/integration/test_execution_runtime.py:57`）。

---

## 环节8 Execution（P0-E execution_result 一等 artifact）

### 1. 真实存在什么代码？
- `core/runtime/execution/adapters.py`：`EXEC_STATUS`（六态枚举，`adapters.py:37`）、`EXECUTION_RESULT_FIELDS`（`adapters.py:40-47`）、`ExecutionPlan`（`adapters.py:72-83`）、`ExecutionResultData`（`adapters.py:87-130`）、`ExecutionAdapter`（ABC，`adapters.py:141-153`）、`LocalPythonAdapter`（`adapters.py:156-261`）、`get_adapter`（`adapters.py:264-268`）。
- 接入点：`codegen.execute_code`（`codegen.py:81-131`）；`handlers._maybe_execute_experiment`（`handlers.py:456-504`）。
- 引擎/调度：`engine.py` `WorkflowEngine`（`engine.py:44-367`）、`wave_executor.py` `WaveExecutor`（`wave_executor.py:25-95`）、`session.py` `RuntimeSession`（`session.py:44-268`）。

### 2. 入口函数是什么？
- 库入口：`LocalPythonAdapter.execute(plan)`（`adapters.py:177`）；session 侧入口 `RuntimeSession.run()`（`session.py:102`）→ `WaveExecutor.run()`（`wave_executor.py:64`）→ `DefaultNodeExecutor.do_experiment`（`handlers.py:362`）→ `_maybe_execute_experiment`（`handlers.py:456`）。
- CLI/生产入口：`orchestrator.py --execute`（`orchestrator.py:503-504`）→ `_execute_v3`（`orchestrator.py:370-412`）；`python -m runtime.execution.codegen`（`codegen.py:175`）。

### 3. 真实输入是什么？
- `ExecutionPlan`：model_id / code / inputs / timeout_seconds / workdir / env / adapter / meta（`adapters.py:72-83`）。
- session 路径输入：`plan` dict（来自 `ExperimentPlanner`，无 code 键，见环节7 Q10）或测试注入的 `{"code": ...}`。
- `execution_result` artifact 的 data schema 由 `EXECUTION_RESULT_FIELDS` 定义（`adapters.py:40-47`）。

### 4. 真实输出是什么？
- `ExecutionResultData`：execution_id / model_id / status / inputs / outputs / stdout / stderr / returncode / duration_ms / code_hash / environment_hash / started_at / finished_at / provenance / code / environment_manifest（`adapters.py:107-126`）。
- 结构化输出约定：stdout 最后一块合法 JSON 为 outputs，否则 `{"stdout_tail": ...}`（`adapters.py:207-223`）。

### 5. 是否真的执行？
- **demonstrated（adapter 层）**：真实 subprocess + 真实退出码（`adapters.py:198-206`）；timeout（`adapters.py:234-245`）；framework error→invalid（`adapters.py:246-256`）。测试：`test_execution_runtime.py:52-84`、`test_execution_codegen.py:60-72`、`tests/unit/test_execution_adapter.py`。
- **V3 生产路径：runtime not demonstrated**：orchestrator 不传 adapter（`orchestrator.py:391-392`），默认 run 下 `execution_result` 数量为 0（`test_runtime_session.py:37-47` 断言产物类型不含 execution_result；`test_execution_runtime.py:37-50` 断言无 adapter 时 result=not_executed 且无 EXEC artifact）。

### 6. 输出是否进入 Artifact Registry？
- 是：`execution_result` 是注册表一等类型，ID 前缀 EXEC（`ids.py:35`），`codegen.py:121-126`、`handlers.py:490-495` 均 `reg.create("execution_result", ...)`。
- `result` artifact 同步翻状态：`r_art.data["status"] = xr.status; r_art.data["execution_ref"] = xart.artifact_id`（`handlers.py:496-499`）。

### 7. 是否进入 Evidence Graph？
- 是（`executed_by` 边）：`handlers.py:503-504`（result→execution_result）、`codegen.py:127-128`。类型约束 `(result)→(execution_result)`（`evidence_graph.py:48`）。
- **注意**：用户假设链中的 `code.executed_by→execution_result` 与 `execution_result.produces→result` **不存在**——`executed_by` 的 from 类型是 `{result}` 而非 `{code}`；`produces` 仅允许 `(experiment)→(result)`（`evidence_graph.py:41`），execution_result 没有任何出边类型。执行记录通过反向边 `result→execution_result` 挂链。

### 8. 该环节失败后能否回到 Model 层面继续？
- **否**：`_maybe_execute_experiment` 执行失败（failed/timeout/invalid）时 `do_experiment` 仍返回 `NodeResult(PASS, ...)`（`handlers.py:452-454`），节点照常 completed；`do_experiment_critique` 只检查 result 是否终态（`handlers.py:543-547`），failed 不是终态 → PASS。**执行失败不会触发引擎 retry/on_fail**。测试仅证明 adapter 异常被降级为 invalid EXEC（`handlers.py:483-489`），不证明任何回退。

### 9. 有没有假实现/placeholder/hardcoded default？
- **status 是真实推导**：`"success" if proc.returncode == 0 else "failed"`（`adapters.py:206`）；timeout/invalid 各有真实路径。非硬编码。
- **但 status 可被任意调用方伪造**：`registry.create("execution_result", data=...)` 接受任意 dict（`registry.py:108-145` 只做 Artifact 通用校验，不校验 EXEC 字段/状态枚举），无 schema 门禁。
- **environment_hash 是"浅指纹"**：仅 python 版本 + platform + executable（`adapters.py:63-69`），**不含包版本/依赖/随机种子**；文档自述"未来将演化"（`adapters.py:55-58`）。不是硬编码，但 replay 归因能力有限。
- duration_ms 为 `time.perf_counter` 实测（`adapters.py:186,203`），非硬编码。
- **默认 V3 管线整体不执行**：result 创建时写死 `"status": "not_executed"` + 说明 note（`handlers.py:431-432`），这是诚实的占位，但意味着默认 run 的"实验结果"全部为空壳。

### 10. 距离"真实 Model Construction"还差什么？
- 生产入口（orchestrator）与执行后端（adapter）未接线；plan 无 code 来源（planner 不产代码）；execution_result 无 JSON Schema 约束；失败不产生 FAIL 节点状态；`register_external_artifact` 回填路径缺失。

---

## 环节9 Validation（含 Model-Code Fidelity + 模型验证）

### 1. 真实存在什么代码？
- `core/runtime/execution/validation.py`（P0-E5）：`run_check`（5 种确定性检查，`validation.py:104-150`）、`run_checks`（三状态铁律，`validation.py:153-168`）、`validate_execution`（VR 注册 + verified_by 边，`validation.py:173-220`）、`VerificationResultData`（`validation.py:33-49`）、`resolve_output_key`（`validation.py:82-99`）。
- `core/runtime/execution/fidelity.py`（P0-E6）：`fidelity_checks_from_ir`（F1–F5 检查生成，`fidelity.py:54-114`）、`check_fidelity`（`fidelity.py:119-157`）、`verify_fidelity`（VR + 报告文件，`fidelity.py:160-213`）。
- `core/validators/evidence/evidence_gate.py`：E1–E8 检查（`evidence_gate.py:87-181`）。
- `core/validators/modules/assumption_validator.py`：`AssumptionValidator`（关键词对矛盾检测，`assumption_validator.py:9-152`）——**但 V3 runtime 未调用它**（见 Q5）。
- 引擎 validator 挂钩：`engine._run_validator`（`engine.py:169-179`）、`_post_execute`（`engine.py:138-167`）。

### 2. 入口函数是什么？
- 校验原语入口：`run_checks(execution_data, checks)`（`validation.py:153`）/ `validate_execution(project_dir, exec_id, checks, provenance)`（`validation.py:173`）。
- fidelity 入口：`check_fidelity(model_ir, execution_data, ...)`（`fidelity.py:119`）/ `verify_fidelity`（`fidelity.py:160`）。
- DAG 层：`evidence_gate` 节点绑定 validator `evidence-gate`（`catalog/v3.yaml:60-63`），handler `do_evidence_gate`（`handlers.py:587-597`）。

### 3. 真实输入是什么？
- `checks: list[dict]`，每个 `{name, kind, path, min, max, expect, names, declared}`；kind ∈ {output_field_exists, output_numeric, output_range, output_equals, output_key_exists}（`validation.py:104-150`）。
- fidelity 输入：MODEL_IR dict（variables/objectives/constraints/equations 的 name/symbol/variables_refs/value_range，`fidelity.py:54-114`）+ execution_data + output_mapping（`fidelity.py:119-127`）。
- MODEL_IR 无正式 schema：`core/schemas/` 下无 model_ir schema（有 `model_artifact.schema.json`、`model_spec.schema.json`，但 fidelity 不消费它们）。

### 4. 真实输出是什么？
- `run_checks` → `(status, checks)`，status ∈ {passed, failed, invalid}（`validation.py:167-168`）。
- `VerificationResultData` → 注册为 `verification_result` artifact（VR，`ids.py:36`），含 verification_id/execution_id/status/checks/evidence_refs/started_at/finished_at/provenance（`validation.py:27-49`）。
- `check_fidelity` → `{status: aligned|misaligned|unverifiable, fidelity_score, passed, total, checks}`（`fidelity.py:154-157`）。
- `verify_fidelity` → VR artifact + `state/fidelity/<exec_id>.json` 报告（`fidelity.py:194-213`）。

### 5. 是否真的执行？
- **demonstrated（primitive 层）**：`run_check`/`run_checks` 是纯确定性函数，测试覆盖三状态铁律（`test_execution_validation.py:40-75`）；fidelity 测试覆盖 aligned/misaligned/unverifiable（`test_execution_fidelity.py:55-157`）；VR 注册 + verified_by 边（`test_execution_validation.py:78-97`）。
- **V3 生产路径：runtime not demonstrated**：`RuntimeSession.__init__` 构造 `WorkflowEngine` 时**未传 validators**（`session.py:84-88` 只传 state/on_success；`wave_executor.py:30-31` 同样 validators=None），因此 `engine._run_validator`（`engine.py:169-179`）永远查不到绑定 validator，**DAG 节点上声明的 validator 名（catalog/v3.yaml:39,43,55,62,66,80）在 session 路径不执行**。门禁实际由 handler 内部自行 FAIL 实现（如 `do_evidence_gate`、`do_model_critique`），绕过引擎 validator 挂钩。
- `assumption_validator.py` 被 catalog 注册（`catalog/v3.yaml:101-103`）但 `do_assumption_check`（`handlers.py:294-299`）只数"每模型≥1 条 assumes 边"，**从不调用 AssumptionValidator**。

### 6. 输出是否进入 Artifact Registry？
- 是：VR artifact 经 `reg.create("verification_result", ...)`（`validation.py:208-212`）；fidelity 报告写 `state/fidelity/<exec_id>.json`（`fidelity.py:194-207`）。

### 7. 是否进入 Evidence Graph？
- 是：`execution_result --verified_by--> verification_result`（`validation.py:217`；类型约束 `evidence_graph.py:49`）。`fidelity.py` 复用 VR 框架（`fidelity.py:188-192`），provenance.engine="execution.fidelity"（`fidelity.py:25,189`）。
- **验证结果与 claim 链无关联**：VR 不产生任何指向 model/result/claim 的边，DAG 后续节点（evidence_gate/quality_evaluation）**不消费 VR**。

### 8. 该环节失败后能否回到 Model 层面继续？
- **否**：VR failed/invalid 只登记在案，无任何 DAG 节点读取 VR 状态并把节点判 FAIL（grep 确认 VR 只在 `validation.py:217` 写边；`evidence_gate` 不查 VR）。模型验证失败 → 无回退路径。
- 例外：`evidence_gate` FAIL 时 DAG 配置了 `on_fail: experiment_design`（`evidence.yaml:20`）与 `quality_evaluation on_fail: evidence_build`（`evidence.yaml:29-30`），引擎 `_handle_failure` 重试耗尽后 `rollback_to`（`engine.py:218-234,279-281`）——这是**存在但默认不触发**的反馈环（见环节11）。

### 9. 有没有假实现/placeholder/hardcoded default？
- **没有 L0–L4 分层**：`validation.py` 只有 execution 层校验原语；L2/L4 字样散落注释（`fidelity.py:4`、`codegen.py:7`、`handlers.py:295,588`），无枚举、无注册表、无 dispatch。用户点名的 L0 schema / L1 execution / L2 fidelity / L3 mathematical / L4 empirical 五层**不存在为统一分层**：无 L0（artifact schema 校验不由 runtime 执行）、无 L3（无任何数学/解析正确性校验）、L4 仅为 evidence_gate 的注释标签。
- **无 feasibility / residual / stability / baseline / domain 等检查实现**：runtime 只有 5 种输出检查（`validation.py:111-150`）。plan 的 `required_checks` 是方法卡字符串（`planner.py:123-127`），没有任何 runtime 消费执行它们；`code_deliverables.schema.json` 声明了 `constraint_reverification`/`multi_run_stats`/`sensitivity`（`code_deliverables.schema.json:104-146`）——**contract exists, runtime not demonstrated**（legacy Programmer 侧 SKILL 指令，非本仓 runtime 代码）。
- **fidelity 是机械结构对比，不是 LLM reviewer**：`fidelity.py:13-14` 自述"LLM-free、确定性、可归因"；F1–F5 全部基于输出 key 存在性/数值范围（`fidelity.py:76-113`）。**没有 FidelityReport 数据结构**（无 dataclass/class），只有 dict + JSON 报告文件（`fidelity.py:197-208`）。
- 注意 fidelity 的边界：F2/F3/F4 只检查"约束/目标引用变量的输出 key 可观测"，**不校验约束表达式是否被满足**（无残差/可行性检查）——即"变量存在"≠"约束成立"。

### 10. 距离"真实 Model Construction"还差什么？
- 五层校验体系（L0–L4）尚未成体系；validator 未接入 engine 挂钩；VR 未进入 DAG 决策；缺数学正确性（L3）与实证充分性（L4 数值层）的真实实现；缺"执行失败/验证失败→节点 FAIL→反馈环"的语义接线。

---

## 环节10 Evidence（Evidence Graph 写入与谱系）

### 1. 真实存在什么代码？
- `core/runtime/graph/evidence_graph.py`：
  - `RELATION_TYPES` — **16 种** typed relation（非用户所述 14 种）：motivates / solved_by / assumes / implemented_by / validated_by / tests / uses / produces / visualized_by / supports / appears_in / selects / based_on / derived_from / executed_by / verified_by（`evidence_graph.py:33-50`）。
  - `STRONG_RELATIONS`（10 种，`evidence_graph.py:52-55`）/ `WEAK_RELATIONS`（2 种，`evidence_graph.py:56`）——**executed_by / verified_by 既不在强边也不在弱边集合**，但 `_PROPAGATION` 表为其单独定义了传播档位（`evidence_graph.py:82-83`）。
  - `_PROPAGATION` 档位表（`evidence_graph.py:67-84`）；`add_relation` fail-closed 校验（`evidence_graph.py:163-196`）；`invalidate` 不动点传播（`evidence_graph.py:326-421`）；`retract_invalidated` 剪死边（`evidence_graph.py:290-307`）；`coverage`（`evidence_graph.py:275-288`）。
- 写入方：handlers（`handlers.py:185-187,240,277,342,357,439-443,504,579-580,694-703`）、codegen（`codegen.py:127-128`）、validation（`validation.py:217`）、session._register_evidence（`session.py:90-98`）。
- schema：`core/schemas/v3/evidence/graph.schema.json:35`（关系枚举）。

### 2. 入口函数是什么？
- `EvidenceGraph.add_relation(from_id, relation, to_id, check_types=True)`（`evidence_graph.py:163`）；session 侧 `RuntimeSession._register_evidence`（`session.py:90-98`）在节点 PASS 后把 `outputs.evidence` 批量入图；`graph.invalidate`（`evidence_graph.py:326`）经 `session.invalidate`（`session.py:196-245`）触发。

### 3. 真实输入是什么？
- `{from, relation, to}` 三元组；from/to 必须是已注册 artifact ID（`_type_of` 校验，`evidence_graph.py:159-161,177-178`）；relation 必须在 `RELATION_TYPES`；类型必须匹配（如 `executed_by`: from∈{result}, to∈{execution_result}，`evidence_graph.py:48`）；自环/重复拒绝（`evidence_graph.py:174-191`）。

### 4. 真实输出是什么？
- 边记录 `{from, relation, to, at}` 追加到 `relations`（`evidence_graph.py:192-193`），持久化 `state/evidence_graph.json`（graph_version 每次 +1，`evidence_graph.py:136-155`）；Artifact contract 的 `relations` 只读视图同步（`evidence_graph.py:437-442`）。

### 5. 是否真的执行？
- **demonstrated**：`test_runtime_session.py:44-47` 断言 motivates/solved_by/assumes/validated_by/produces/visualized_by/supports/appears_in 入图；`test_execution_validation.py:94-97` 断言 verified_by 边；`test_execution_runtime.py:70-72` 断言 executed_by 边；`tests/unit/test_evidence_graph.py` 覆盖传播。

### 6. 输出是否进入 Artifact Registry？
- 间接：`add_relation` 同步 `set_relations_view`（`evidence_graph.py:437-442` → `registry.py:305-310`），Registry 是节点事实源；边本身存 graph 文件。

### 7. 是否进入 Evidence Graph？
- 是（本环节即图写入）。用户点名的四条链逐条核对：
  - `model --implemented_by--> code`：**schema/类型存在（`evidence_graph.py:37`），但 V3 runtime 无任何写入方**（grep 全仓仅 schema/注释命中，见环节7 Q7）。
  - `code --executed_by--> execution_result`：**不存在**；实际为 `result --executed_by--> execution_result`（`evidence_graph.py:48`；写入 `handlers.py:503-504`、`codegen.py:127-128`）。
  - `execution_result --produces--> result`：**不存在**；`produces` 仅 `(experiment)→(result)`（`evidence_graph.py:41`）。execution_result 只有入边（executed_by/verified_by），无出边。
  - `result --supports--> claim`：**存在**（`evidence_graph.py:43`；写入 `handlers.py:579-580`）。
- **无 revision_of / supersedes 边**：RELATION_TYPES 不含任何"修订/替代"关系；grep `revision_of|supersedes|superseded_by` 在 core/runtime 零命中。修订谱系只能靠 lifecycle 状态（superseded 终态，`lifecycle.py:21-37`）+ `supersede()` 的 `invalidation.invalidated_by=replacement` 字段（`registry.py:284-295`）+ runs 的 `parent_run_id`（`runs.py:117-127`）间接表达，且 `retract_invalidated` 会剪掉触及终态产物的边（`evidence_graph.py:290-307`），使旧链在图中不可见。

### 8. 该环节失败后能否回到 Model 层面继续？
- 结构性存在：`evidence_gate` FAIL → on_fail experiment_design（`evidence.yaml:20`）；引擎 rollback（`engine.py:279-281`）。但默认管线 evidence_gate 恒 PASS（见 Q9/环节11），该回退未在默认 run 中演示。

### 9. 有没有假实现/placeholder/hardcoded default？
- **claim 是显式占位**：`do_evidence_build` 创建 claim 时 `data={"statement": f"{qid} 结论", "claim_type": "comparative", ..., "execution_status": "not_executed", "placeholder": True}`（`handlers.py:569-578`）——默认管线每条 claim 都是 placeholder，且带 supports 边。
- **evidence_gate 不校验数值真实性**：E1–E8 只查边存在性/生命周期/tags（`evidence_gate.py:87-181`），不检查 result.data 是否有值、claim 是否 placeholder。默认 run 中 `claims_supported=2, coverage=1.0`（`test_runtime_session.py:55-56`），即**零数值计算的占位 claim 链即可通过证据门禁**。
- `retract_invalidated` 剪边是"审计保留"语义的妥协（`evidence_graph.py:290-296`）：健康链重建依赖剪死边，但谱系可见性随之丢失。

### 10. 距离"真实 Model Construction"还差什么？
- `implemented_by` 无写入方；execution_result 与 result/claim 之间缺正向 evidence 边（无 `execution_result→result` 推导链）；占位 claim 不被门禁拦截；缺 revision/supersedes 类型化边；`coverage` 指标度量的是"边存在"而非"证据真实性"。

---

## 环节11 Revision（M1→E1→V1 FAIL→M2 闭环）

### 1. 真实存在什么代码？
- 引擎反馈环：`engine._handle_failure`（重试计数，`engine.py:218-234`）、`rollback_to/reset_to`（`engine.py:262-281`）、`reset_question`（`engine.py:283-305`）。
- session 失效/重跑：`RuntimeSession.invalidate`（`session.py:196-245`）、`rerun`（`session.py:247-260`，`force_new_lineage` 强制新建谱系）、`resume`（`session.py:136-141`）。
- DAG 反馈边（YAML 配置）：`model_critique.on_fail: model_construction`（`modeling.yaml:26`）、`experiment_critique.on_fail: experiment*`（`experiment.yaml:27`）、`evidence_gate.on_fail: experiment_design`（`evidence.yaml:20`）、`quality_evaluation.on_fail: evidence_build`（`evidence.yaml:30`）。
- 谱系表达：lifecycle superseded 终态（`lifecycle.py:21-37`）、`registry.supersede`（`registry.py:284-295`）、`registry.update` 版本历史（`registry.py:240-282`）、runs `parent_run_id`（`session.py:113-131`、`runs.py:117-127`）。

### 2. 入口函数是什么？
- 自动：`WorkflowEngine.run`（`engine.py:210-216`）→ `_handle_failure`（`engine.py:218`）→ `rollback_to`（`engine.py:279`）。
- 人工/失效：`session.invalidate(artifact_id, reason)`（`session.py:196`）、`session.rerun(node_id, reason)`（`session.py:247`）。

### 3. 真实输入是什么？
- 引擎：`NodeResult(status="fail", reason)` + 节点 `max_retries`/`on_fail`（`dag.py:30-57`）。
- session：`artifact_id` + `reason`（invalidate）；`node_id` + `reason`（rerun）。

### 4. 真实输出是什么？
- 引擎：`progress()` 报告 completed/blocked/waiting/retries/failures（`engine.py:95-104`）；`reset_to` 返回受影响节点集合（`engine.py:262-277`）。
- session：`{"invalidation": report, "reset_nodes": [...], "resume_ready": [...]}`（`session.py:244-245`）；`{"reset_nodes", "reason", "resume_ready"}`（`session.py:259-260`）。

### 5. 是否真的执行？
- **demonstrated（引擎/测试层）**：`test_workflow_execution.py:47-69`（重试耗尽沿 on_fail 回滚）、`test_runtime_session.py:79-104`（result/model invalidation → 局部重跑至全完成）、`test_runtime_session.py:124-140`（resume 断点续跑）。
- **默认 V3 生产路径：不会触发**：确定性默认管线中所有门禁节点自证 PASS（`test_runtime_session.py:33-35`：blocked/failures 均为空），`_handle_failure` 反馈环在默认 run 中从未被激活；触发 revision 只能靠外部注入 FAIL（测试）或人工 `invalidate/rerun`。**没有"V1 FAIL 自动升级 M1→M2"的端到端演示**。

### 6. 输出是否进入 Artifact Registry？
- 是：`_supersede_question_chain` 把旧 E/R/F/C 全量 transition("superseded")（`handlers.py:521-536`）；`do_model_selection` rerun 分支 supersede 旧 model（`handlers.py:217-227`）；新节点 `reg.create` 生成全新 artifact ID。Registry 的 `supersede()` 记录 `invalidation.invalidated_by=replacement`（`registry.py:284-295`）。

### 7. 是否进入 Evidence Graph？
- **间接、且会被剪断**：新旧谱系之间无类型化边（无 revision_of/supersedes，见环节10 Q7）；`retract_invalidated` 会把触及 superseded/invalidated 的边全部剪除（`evidence_graph.py:290-307`），旧链在图中不再可见。`do_evidence_gate` 执行前也会先 `retract_invalidated`（`handlers.py:590`）。因此 **M1→M2 的"修订谱系"无法从 Evidence Graph 查询**。

### 8. 该环节失败后能否回到 Model 层面继续？
- 部分闭环可表达：`model_critique.on_fail→model_construction`（`modeling.yaml:26`）即"V1 模型批判失败 → 回到 Model 构建重来"；`session.invalidate(model)` → `engine.reset_to("model_selection")`（`session.py:227-228`）。但执行/验证失败（环节8/9）不映射到任何 FAIL 节点，因此 **E/V 失败无法触发 M 层回退**——闭环只覆盖批判/门禁类 FAIL，不覆盖执行失败与 VR 失败。

### 9. 有没有假实现/placeholder/hardcoded default？
- `force_new_lineage` 只在 `session.rerun`（`session.py:256`）与测试注入时置位；默认 run 无。
- 幂等复用逻辑（`handlers.py:376-406`）在 rollback 后**复用既有非终态实验链**（`handlers.py:377-379`），即"重跑"可能不产生新数值、只回填 tags/provenance——修订语义退化为元数据修补（`handlers.py:380-402`）。
- `quality_evaluation` 的 WEAK/UNKNOWN 只记录 advisory 不阻断（`handlers.py:601-605`），FAIL 才反馈（`handlers.py:625-631`）——默认 run 无 FAIL。

### 10. 距离"真实 Model Construction"还差什么？
- 缺类型化的 revision/supersedes 谱系边；缺"执行失败/VR 失败→节点 FAIL→M 层回退"的语义接线；缺自动 revision 的端到端演示（默认管线零 FAIL）；`register_external_artifact`/真实数值回填缺失使"E1→V1"无法在数值层发生。

---

## 下游关键检查点结论

### ① Model→Code Fidelity：fidelity.py 真实实现了什么？
- **是确定性机械结构对比，不是 LLM reviewer**：`fidelity.py:13-14` 自述 LLM-free。把 MODEL_IR 的 variables/objectives/constraints/equations 声明转为 5 族检查（F1 变量可观测 / F2 目标引用变量可观测 / F3 约束引用变量可观测 / F4 方程引用变量可观测 / F5 value_range 数值范围，`fidelity.py:54-114`），对 execution 输出做 key 解析（name/symbol/output_mapping 翻译，`fidelity.py:30-51`、`validation.py:82-99`）。
- **有 FidelityReport 吗**：无——没有 dataclass/class，只有返回 dict `{status, fidelity_score, passed, total, checks}`（`fidelity.py:156-157`）+ JSON 报告文件 `state/fidelity/<exec_id>.json`（`fidelity.py:197-208`）。
- 覆盖字段：仅"声明项的符号是否出现在输出、数值是否在声明范围内"。**不覆盖**：约束是否被满足、目标函数值是否最优、方程残差、求解器选择、数值正确性。
- 是真跑：测试 demonstrated（`test_execution_fidelity.py:62-105,161-183`）；但仅在 codegen/测试路径可到达，V3 默认管线不接线。

### ② Execution：engine/session/wave_executor 是否真的 subprocess？
- **adapter 层是真的**：`LocalPythonAdapter.execute` 真实 subprocess + 退出码推导 status（`adapters.py:198-206`）；timeout/invalid 真实路径（`adapters.py:234-256`）。
- **V3 默认管线不执行**：orchestrator `--execute` 不传 execution_adapter（`orchestrator.py:391-392`）→ `_maybe_execute_experiment` 直接 return（`handlers.py:470-471`）→ result 保持 `not_executed`（`handlers.py:431`）。engine/session/wave_executor 本身不 subprocess，只调度 handler；handler 只在 adapter 存在且 plan 含 code 时才执行。
- `execution_result.status`：在 adapter 路径由真实 returncode 推导（`adapters.py:206`）；但 `registry.create("execution_result", data=...)` 无 schema 门禁，**任意调用方都可写入任意 status**（`registry.py:108-145`）——"不可被任意设置"不成立，只是 adapter 自己不伪造。
- `environment_hash`：真采集但浅（python/platform/executable，`adapters.py:63-69`），不含依赖/种子；`duration_ms` 真实计时（`adapters.py:203`）。非硬编码。

### ③ Execution Success ≠ Model Correctness：是否有地方把 success 当正确？
- **fidelity 与 validation 明确区分**（`validation.py:1-17` 铁律、`fidelity.py:4-7`），`check_fidelity` 在 status!=success 时返回 unverifiable（`fidelity.py:129-135`）。
- **但 V3 默认管线整体绕开了这条铁律**：不执行 → result 永远 not_executed → evidence_gate 只查边不查数值（`evidence_gate.py:87-181`）→ 占位 claim 链照常 PASS（`test_runtime_session.py:55-56`）。**没有任何代码把 execution.status==success 当 model 正确**，但同样地，**也没有任何代码把"没有执行/没有数值"挡在论文门外**——铁律的正面保障存在，负面拦截缺失。
- **L0–L4 分层：不存在统一实现**。L2 只是注释标签（`fidelity.py:4`）；L4 只是 evidence_gate 注释标签（`handlers.py:588`）；无 L0 schema 门禁、无 L3 数学校验、L1 execution 即 `validation.py` 原语。engine validators 挂钩未接线（`session.py:84-88` 未传 validators）。

### ④ Validation Suite：feasibility/constraint/residual/sensitivity/stability/baseline/domain 是否真实？
- **runtime 层全部 not implemented**：`validation.py:104-150` 只有 output_field_exists/output_numeric/output_range/output_equals/output_key_exists 五种。feasibility、constraint checks、residual、stability、domain 无任何实现。
- sensitivity/baseline 只有"tag 打标"（`handlers.py:384-386,415-417`）与 planner 字符串（`planner.py:121-133,149-155`）；`code_deliverables.schema.json:104-146` 的 constraint_reverification/multi_run_stats/sensitivity 是 legacy schema 契约，runtime 不消费。
- 结论：**只有名字/接口与 schema 契约，无 runtime 实现**（contract exists, runtime not demonstrated）。

### ⑤ Revision 闭环：M1→E1→V1 FAIL→M2 谱系可表达吗？
- **部分可表达**：artifact 版本（`registry.update` 版本历史，`registry.py:240-282`）+ lifecycle superseded 终态 + `supersede().invalidation.invalidated_by=replacement`（`registry.py:284-295`）+ runs `parent_run_id` 链（`runs.py:117-127`）+ `engine.reset_to`/`reset_question`（`engine.py:262-305`）。
- **Evidence Graph 不可表达**：无 revision_of/supersedes 边（16 种关系无此二类），且 `retract_invalidated` 剪除死边（`evidence_graph.py:290-307`），旧链不可查询。
- **有 runtime 路径真的触发 revision**：引擎 retry/on_fail（`engine.py:218-234`）、`session.invalidate`（`session.py:196-245`）、`session.rerun`（`session.py:247-260`）、handlers 的 `_supersede_question_chain`（`handlers.py:521-536`）与 `force_new_lineage`（`handlers.py:217-227`）——**代码存在且测试 demonstrated**（`test_workflow_execution.py:47-69`、`test_runtime_session.py:79-104`）。
- **但默认 V3 管线从不触发**：所有节点自证 PASS（`test_runtime_session.py:33-35`），执行失败/VR 失败也不产生 FAIL（环节8 Q8、环节9 Q8），因此 **"V1 FAIL→M2"没有端到端自动演示，实际 revision 依赖人工 invalidate/rerun 或测试注入 FAIL**。

### ⑥ Replay：replay.py 是真重放还是 diff 元数据？
- **两层语义**：
  - run 级 `verify`（`replay.py:46-113`）：**只 diff 元数据/哈希**（input/workflow/skill/tool/artifact/evidence/decision_log 哈希 + state reconcile），不重跑。
  - execution 级 `replay_execution`（`replay.py:166-249`）：**真重放**——取 artifact 中保存的 code 经 `get_adapter("local_python")` 真实 subprocess 重建（`replay.py:193-206`），逐项报偏差（status/code_hash/environment_hash/outputs，`replay.py:212-233`）。测试 demonstrated（`test_replay_execution.py:37-80`）。
- 局限：依赖 artifact 保存 code 本体（缺则报错 + code_override，`replay.py:187-192`）；environment 指纹浅（不含包版本），无法检测依赖级漂移；`verify` 的 tool_version 依赖 `git rev-parse HEAD`（`runs.py:80-94`）。

---

## 下游假实现/占位清单

| # | 位置 | 类型 | 说明 |
|---|---|---|---|
| 1 | `handlers.py:431-432` | 占位 | result 创建时 status 写死 `not_executed`，note 声称由 `register_external_artifact` 回填——该函数**不存在**（grep 零实现） |
| 2 | `handlers.py:569-578` | 占位 | claim 创建时 `placeholder: True` + `execution_status: "not_executed"`，且能通过 evidence_gate |
| 3 | `evidence_gate.py:87-181` | 假门禁 | E1–E8 只查边/生命周期/tags，不查数值真实性；零数值的占位链可 PASS |
| 4 | `handlers.py:473-476` | 死代码 | `_maybe_execute_experiment` 的 code 来源 `plan["code"]` 在真实 planner 输出（`planner.py:81-91`）中永远不存在；V3 默认管线不产生任何 EXEC |
| 5 | `orchestrator.py:391-392` | 未接线 | `--execute` 不传 `execution_adapter` → 生产入口永不执行代码 |
| 6 | `session.py:84-88` / `wave_executor.py:30-31` | 未接线 | `WorkflowEngine(validators=...)` 恒为 None → DAG 声明的 validator（catalog/v3.yaml:39,43,55,62,66,80）在 session 路径不执行 |
| 7 | `handlers.py:294-299` | 未接线 | `do_assumption_check` 不调用 `assumption_validator.py`（catalog 注册的 runtime validator） |
| 8 | `validation.py:104-150` | 名不副实 | 只有 5 种输出检查；feasibility/constraint/residual/stability/domain 零实现（仅 schema/plan 字符串存在） |
| 9 | `code_deliverables.schema.json:104-146` | 契约空洞 | constraint_reverification/multi_run_stats/sensitivity 仅 legacy schema，runtime 不消费 |
| 10 | `evidence_graph.py:37` | 无写入方 | `implemented_by` 边类型存在但 V3 runtime 零写入 |
| 11 | `evidence_graph.py:48,41` | 链断裂 | 用户假设链 `code.executed_by→execution_result`、`execution_result.produces→result` 不存在；execution_result 无出边 |
| 12 | `evidence_graph.py:290-307` | 语义妥协 | `retract_invalidated` 剪死边使修订谱系在图中不可见；无 revision_of/supersedes 边 |
| 13 | `handlers.py:377-402` | 幂等降级 | rollback 后"重跑"复用既有实验链，只回填 tags/provenance，不产生新数值 |
| 14 | `adapters.py:63-69` | 浅实现 | environment_hash 仅 python/platform/executable，无包版本/依赖/种子（文档自认待演化） |
| 15 | `registry.py:108-145` | 无门禁 | `create("execution_result", data=...)` 不校验 EXEC 字段/status 枚举，status 可被任意调用方伪造 |
| 16 | `core/schemas/` | 缺失 | 无 execution_result / verification_result / validation_report / result / claim 的 JSON Schema（仅通用 artifact schema） |
| 17 | `codegen.py:175-193` | 孤岛 | codegen CLI 的 fidelity 失败只改退出码，无 DAG 反馈闭环 |

---

## 附：证据文件索引（本次取证读取）

- `core/runtime/execution/{codegen,fidelity,validation,engine,session,wave_executor,dag,composer,handlers,adapters,replay,__init__}.py`
- `core/runtime/graph/evidence_graph.py`；`core/runtime/artifacts/{artifact,registry,lifecycle,ids}.py`
- `core/runtime/state/{runs,reconcile,relations}.py`；`core/runtime/contracts.py`；`core/runtime/roles.py`
- `core/runtime/modeling/planner.py`；`core/validators/evidence/evidence_gate.py`；`core/validators/modules/assumption_validator.py`
- `core/tools/{orchestrator,replay,validate}.py`；`catalog/v3.yaml`；`core/workflows/{base.yaml,stages/*.yaml}`
- `core/schemas/{code_deliverables,model_artifact,...}.schema.json`（Glob 全量 26 个，确认无 execution/validation 专属 schema）
- `tests/integration/{test_execution_codegen,test_execution_fidelity,test_execution_validation,test_execution_runtime,test_replay_execution,test_runtime_session,test_workflow_execution}.py`（仅读断言，未跑 pytest）
