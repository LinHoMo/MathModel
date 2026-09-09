# P1 — Model Construction 最小闭环实施计划

> **状态：✅ 全部完成（2026-09-09 收口）**。C1–C10 主线 + M3/M4 全部落地：
> VS-001 垂直切片 7/7 PASS（2024_A，M1 FAIL → M2 PASS 闭环 + Replay）→
> M3 候选竞技场（evidence-based 选型，selects 边真写入）→ M4 知识引导
> （BZD 试点卡 5 张 + 义务映射 19 项可溯源）。报告：
> P1_VS001_REPORT.md / P1_M3_REPORT.md / P1_M4_REPORT.md；
> 验证：pytest 910/4、catalog_check OK、validate 57/0。本计划正文保留为
> 历史执行蓝本（原始目标/非目标/依赖顺序），实现细节见文末里程碑记录。

- 仓库：`C:\Users\Lin\Desktop\Programs\MathModel` @ HEAD `4c80914`
- 依据：`MODEL_CONSTRUCTION_GAP_AUDIT.md`（11 环节 Gap Audit，本计划只引用其中已确认的证据）
- 平台口径：Windows 本机 `py -3.12`；禁止修改除本计划标注文件外的仓库文件，本计划本身不执行 git 操作
- 日期：2026-09-09

## 目标（P1）

把 **Candidate Model Construction → Selection Decision → MODEL_IR → Code → Execution → Validation** 接通成一条最小可运行闭环，使"给定 problem 一路跑到 validated 或明确 failed 的 execution_result，且 evidence_graph 可查询完整谱系"。Revision（V1 FAIL→M2）留 P4，本计划只保证失败**可观测**（节点 FAIL / VR failed 落盘），不实现自动重建模。

## 非目标（P1 明确不做）

- 不实现 LLM 自动写代码（代码由模板渲染 / 测试 fixture 提供）
- 不做执行完整性增强：`environment_hash` 深指纹、replay 依赖漂移检测、EXEC 全字段 schema 门禁（留 P0-E2）
- 不做语义正确性校验：约束残差 / 目标最优 / 方程数值正确性（留 P2）
- 不做 L3/L4 五层校验体系、feasibility/stability/domain 全套（留 P3）
- 不做自动 Revision 闭环：执行失败/VR failed 只判 FAIL，不自动升级 M1→M2（留 P4）

## 验收标准（一条 e2e）

`tests/integration/test_p1_closed_loop.py`：给定一个 problem（测试 fixture，含 features JSON），跑通默认 V3 管线（`orchestrator.py --execute` 语义），断言：

1. 产物链存在：`problem → question → model → model_ir → code → execution_result → verification_result → claim` 全部为已注册 artifact；
2. `execution_result.status` 为六态枚举中**真实值**（success 或明确 failed，不再是恒 `not_executed`）；
3. `evidence_graph.json` 可查询完整正向谱系：`problem -motivates-> question -solved_by-> model -implemented_by-> code -executed_by-> execution_result -verified_by-> verification_result -supports-> claim`；
4. `py -3.12 core/tools/state.py <项目> reconcile` 通过；`py -3.12 core/tools/validate.py` 无回归。

## 依赖顺序图

```
C1 MODEL_IR 升入 core（schema+builder+registry 类型）
 └─► C5 Method→Instantiation（builder 被 handler 调用，产 MODEL_IR artifact）
      └─► C6 Code 节点接入 DAG（读 MODEL_IR 渲染代码，写 implemented_by 边）
           └─► C7 Execution 生产接线（orchestrator 传 adapter，plan 产 code，写 executed_by/produces 边）
                └─► C8 Validation L0-L2 落地（VR 被 DAG 消费，执行失败映射 FAIL）
                     └─► C9 门禁硬化（evidence_gate 拒绝占位/not_executed）
                          └─► C10 e2e 闭环测试

C2 Candidate 持久化（candidate→artifact+assumes 边）
 ├─► C3 Decision 统一到 Registry（decision→artifact+selects 边）
 │    └─► C4 Selection 真实比较（候选集参与选型，criteria 打分）
 │         └─► C5（选型结果作为 MODEL_IR builder 输入）
 └─► C4（候选集可直接作为 alternatives 输入，与 C3 并行）
```

主线（红色）C1→C5→C6→C7→C8→C9→C10 即为 MVP cut；C2/C3/C4 是选型/决策的真实化，可并行推进后在 C5 前合入。

---

## C1 — `feat(p1-model): introduce MODEL_IR as first-class artifact`

- **改动文件**
  - 新增 `core/runtime/modeling/model_ir.py`（ModelIR 数据类 + builder + 校验器）
  - 新增 `core/schemas/v3/model/model_ir.schema.json`（自 `research/P15/model_representation/model_ir.schema.json` v1.0 迁移，18 required 字段：ir_version/model_id/model_family/problem_binding/assumptions/variables/parameters/objectives/constraints/mechanisms/equations/dependencies/solvers/experiments/validations/claims/model_graph/modeling_trace）
  - 修改 `core/runtime/artifacts/ids.py`（新增 `model_ir` 类型，ID 前缀 `MIR`）
  - 修改 `core/runtime/artifacts/artifact.py`（`artifact_type` 集合加入 `model_ir`，若类型为枚举/白名单）
  - 修改 `core/tools/validate.py`（把 model_ir schema 纳入项目级校验，替换 `validate_example.py` 的 jsonschema 硬编码路径）
- **新增/修改的类与函数（签名级）**
  - `model_ir.ModelIR`：dataclass，字段与 schema 18 项一一对应
  - `model_ir.ModelIRBuilder.build(candidate: Candidate | None, selection: SelectionOutcome | None, features: dict) -> ModelIR`（把候选/选型结果实例化为 variables/objectives/constraints/equations；P15 `example_2024_A.json` 作黄金样本）
  - `model_ir.validate_model_ir(instance: dict) -> tuple[bool, list[str]]`（零第三方依赖手写校验，供 runtime 使用；`core/runtime` 零第三方依赖，不引入 jsonschema）
- **测试**：`tests/unit/test_model_ir.py` + `tests/integration/test_model_ir_registry.py`
  - 断言 1：`ModelIRBuilder.build(...)` 输出 dict 通过 18 required 顶层字段校验
  - 断言 2：缺 `equations` 的 instance 校验失败并返回缺失字段名
  - 断言 3：`registry.create("model_ir", data=...)` 后 `checkpoint()` 落盘，新 session 恢复可读，ID 前缀 `MIR`
  - 断言 4：`P15/model_representation/example_2024_A.json` 可被 `validate_model_ir` 通过（黄金样本回归）
- **验收标准**：`py -3.12 -m pytest tests/unit/test_model_ir.py tests/integration/test_model_ir_registry.py -q` 全绿；`py -3.12 core/tools/validate.py` 通过
- **工作量 / 风险**：M（1–4h）。风险：core/runtime 零第三方依赖，jsonschema 校验需手写或仅放 validate.py 层；迁移 schema 时保持 P15 原文件不动（只读）。

## C2 — `feat(p1-model): persist candidate models as first-class artifacts`

- **改动文件**
  - 修改 `core/runtime/artifacts/ids.py`（新增 `candidate` 类型，ID 前缀 `CAND`）
  - 修改 `core/runtime/modeling/candidates.py`（`Candidate.to_artifact_data()` 序列化；`_CANDIDATE_SEQ` 全局计数器改为调用方/会话内 ID 源）
  - 修改 `core/runtime/execution/handlers.py`（`do_model_selection` 生成候选后逐一 `reg.create("candidate", ...)` 并写 `candidate -assumes-> assumption` 边；替代仅存 `shared[qid]["candidates"]`；`handlers.py:247-248` 的 `except Exception` 吞异常改为登记 failed 状态或显式告警）
- **新增/修改的类与函数（签名级）**
  - `Candidate.to_artifact_data() -> dict`（candidate_id/kind/composition/base_card/rationale/score/risks/required_experiments/innovations/knowledge_refs）
  - `DefaultNodeExecutor.do_model_selection(...)`（`handlers.py:208-255`）：候选生成循环内 `self.reg.create("candidate", data=..., parent=...)` + `self.reg.add_relation(cand_id, "assumes", assumption_id)`
  - `CandidateArena.generate_candidates(...)` 保持纯函数（`candidates.py:110`），持久化由 handler 负责
- **测试**：`tests/unit/test_candidate_artifacts.py`
  - 断言 1：生成 4 型候选后 Registry 出现对应 `candidate` artifact，ID 前缀 `CAND`
  - 断言 2：每个 candidate 至少一条 `assumes` 边指向已注册 assumption artifact
  - 断言 3：`checkpoint()` 后候选可从 `registry.json` 恢复（不再仅内存）
  - 断言 4：候选生成抛异常时不再静默——handler 登记显式失败记录而非仅 `candidates_error` 内存键
- **验收标准**：`py -3.12 -m pytest tests/unit/test_candidate_artifacts.py tests/unit/test_competition_intelligence.py -q` 全绿；`state.py reconcile` 通过
- **工作量 / 风险**：M（1–4h）。风险：candidates.py 被 `test_competition_intelligence.py` 覆盖，改动须保持纯函数语义向后兼容。

## C3 — `feat(p1-model): unify selection decisions into registry as first-class artifacts`

- **改动文件**
  - 新增 `core/runtime/modeling/decision_adapter.py`（DecisionLog ↔ Registry 双向同步）
  - 修改 `core/runtime/execution/handlers.py`（`do_model_selection` 用 `registry.create("decision", ...)` 写主存储，`DecisionLog.add` 降级为审计镜像）
  - 修改 `core/runtime/execution/session.py`（`decision_log.json` 保留为审计文件，路径注释修正 `session.py:68` vs `log.py:6-7` 的 doc mismatch）
  - 修改 `core/runtime/graph/evidence_graph.py`（确认 `selects` 边 from 类型 `{decision}` 可匹配 Registry decision artifact；`evidence_graph.py:45` 已注册，无需新增类型）
- **新增/修改的类与函数（签名级）**
  - `DecisionAdapter.record(selection: SelectionOutcome, registry: ArtifactRegistry, model_id: str) -> str`（创建 decision artifact + `add_relation(decision_id, "selects", model_id)`）
  - `DecisionAdapter.mirror_to_log(...)`（可选：同步写 `decision_log.json` 保持审计兼容）
  - `DefaultNodeExecutor.do_model_selection(...)`：在 `handlers.py:231-238` 创建 model artifact 后调用 `DecisionAdapter.record`
- **测试**：`tests/unit/test_decision_registry.py`（扩展 `test_model_selection.py`）
  - 断言 1：select 后 Registry 存在 decision artifact，且 evidence_graph 含 `selects` 边（decision→model）
  - 断言 2：新选型 supersede 旧决策时，旧 decision artifact lifecycle=superseded，图无孤边
  - 断言 3：decision artifact data 含 alternatives≥1，`chosen` 与 `SelectionOutcome.chosen` 一致
  - 断言 4：`decision_log.json` 仍可查询（审计兼容不回归）
- **验收标准**：`py -3.12 -m pytest tests/unit/test_decision_registry.py tests/unit/test_decision_log.py tests/unit/test_model_selection.py -q` 全绿；`state.py reconcile` 通过
- **工作量 / 风险**：M（1–4h）。风险：`test_decision_log.py` 全面覆盖旧存储行为，需保留或显式废弃其语义。

## C4 — `feat(p1-model): replace top-1 selection with criteria-based comparison`

- **改动文件**
  - 修改 `core/runtime/modeling/selection.py`（`MethodArena.select`：`chosen=recs[0]`（`:60`）改为多准则打分比较；`criteria` 从固定四词（`:96-97`）改为可计算指标；`evidence_ids`（`:103`）改为可填）
  - 修改 `core/runtime/modeling/candidates.py`（候选集作为 alternatives 输入，候选启发式分数并入 criteria 权重）
- **新增/修改的类与函数（签名级）**
  - `MethodArena.select(question, features, top_k=3, created_by, record=True, candidates: list[Candidate] | None = None) -> SelectionOutcome`
  - `MethodArena._score_candidate(rec: Recommendation, features: dict, candidates: list[Candidate]) -> dict[str, float]`（多准则加权；保持零第三方依赖）
  - `SelectionOutcome` 增加 `criteria_scores: dict[str, float]`
- **测试**：`tests/unit/test_model_selection.py`
  - 断言 1：构造"高检索分/低适用匹配"与"低检索分/高适用匹配"两个 rec，`chosen` 非恒为 `recs[0]`
  - 断言 2：`chosen` 与 `criteria_scores` 的 argmax 一致
  - 断言 3：传入候选集时 `alternatives` 包含候选项；提供实验证据时 `evidence_ids` 可被填充（非恒空）
  - 断言 4：全候选不满足阈值时抛 `SelectionError` → handler 侧 FAIL（保持 `handlers.py:169-170` 语义）
- **验收标准**：`py -3.12 -m pytest tests/unit/test_model_selection.py tests/integration/test_runtime_session.py -q` 全绿（`chosen.startswith("mc-")` 旧断言不回归）
- **工作量 / 风险**：M（1–4h）。风险：改变 chosen 语义可能影响下游 `experiment_design` 期望，需同步检查 `handlers.py:313-324` 消费路径。

## C5 — `feat(p1-model): wire model_construction node to MODEL_IR builder`

- **改动文件**
  - 修改 `core/runtime/execution/handlers.py`（`do_model_construction` `:257-280`：从"只登记假设"改为调用 `ModelIRBuilder.build` 产出 MODEL_IR artifact 并挂载到 model artifact）
  - 修改 `core/runtime/modeling/model_ir.py`（builder 消费 candidate + selection outcome + features）
  - 修改 `core/runtime/graph/evidence_graph.py`（如 `appears_in`/`derived_from` 类型不满足，注册 `model_ir -derived_from-> model` 或复用现有 `appears_in` 语义，保持 16 类型内选择）
- **新增/修改的类与函数（签名级）**
  - `DefaultNodeExecutor.do_model_construction(question_id, ...)`：读 `shared[qid]["candidates"]` 与 model artifact → `ModelIRBuilder.build(...)` → `reg.create("model_ir", ...)` → `reg.update(model_id, data={..., "model_ir_id": mir_id})` → 写 `model → model_ir` 图边；**保留**原 assumes 边登记（`handlers.py:277`）
  - `ModelIRBuilder.build(candidate, selection_outcome, features) -> ModelIR`（C1 提供，此处接线）
- **测试**：`tests/integration/test_model_construction_ir.py`
  - 断言 1：端到端跑 V3 后 Registry 有 `model_ir` artifact 且 18 required 字段齐
  - 断言 2：`model` artifact data 含 `model_ir_id` 指针（不再是纯 `{card_id, family, shortlist}`）
  - 断言 3：evidence_graph 存在 model→model_ir 边且 assumes 边仍写
  - 断言 4：无候选/选型失败时节点 FAIL 而非产出空 MODEL_IR
- **验收标准**：`py -3.12 -m pytest tests/integration/test_model_construction_ir.py -q` 全绿；`state.py reconcile` 通过
- **工作量 / 风险**：L（>4h）。风险：builder 需从候选/选型推导 variables/equations，`example_2024_A.json` 为黄金样本；handler 改动须保持 `test_runtime_session.py` 既有断言不回归（或按新语义更新）。

## C6 — `feat(p1-model): add code generation node to v3 DAG and wire implemented_by`

- **改动文件**
  - 修改 `catalog/v3.yaml`（新增 `code_gen` 节点：model_construction 之后、experiment 之前）
  - 修改 `core/runtime/modeling/planner.py`（`ExecutionPlan.as_dict()` `:81-91` 增加 `code` 字段）
  - 修改 `core/runtime/execution/handlers.py`（新增 `do_code_generation`；`_maybe_execute_experiment` `:473-476` 的 `plan["code"]` 死代码路径转为真实来源）
  - 修改 `core/runtime/execution/codegen.py`（`register_code` 增加从 MODEL_IR artifact 读取并写 `model -implemented_by-> code` 边）
  - 修改 `core/runtime/graph/evidence_graph.py`（确认 `implemented_by` 类型 `(model)→(code)` 可用，`:37` 已注册，无需新增）
- **新增/修改的类与函数（签名级）**
  - `CodeGenerator.render(model_ir: ModelIR) -> str`（零依赖模板：equations→numpy/scipy 可执行骨架）
  - `DefaultNodeExecutor.do_code_generation(question_id, ...)`：读 MODEL_IR → `CodeGenerator.render` → `reg.create("code", ...)` → `add_relation(model_id, "implemented_by", code_id)`
  - `ExperimentPlanner` / `ExecutionPlan`：增加 `code: str | None`
- **测试**：`tests/integration/test_codegen_dag.py`
  - 断言 1：V3 管线（传 adapter 后）产物类型含 `code`
  - 断言 2：evidence_graph 含 `model -implemented_by-> code` 边
  - 断言 3：真实 plan 输出含 `code` 键（修复 `handlers.py:473-476` 死代码路径）
  - 断言 4：code artifact data 含 `sha256`（沿用 `codegen.py:69-73` 契约）
- **验收标准**：`py -3.12 -m pytest tests/integration/test_codegen_dag.py tests/integration/test_execution_codegen.py -q` 全绿；`state.py reconcile` 通过
- **工作量 / 风险**：L（>4h）。风险：v3.yaml 与 catalog 三方一致性（`catalog_check.py --check`）需同步；planner 改动影响 `experiment_design` 消费者。

## C7 — `feat(p1-model): wire default execution to LocalPythonAdapter`

- **改动文件**
  - 修改 `core/runtime/tools/orchestrator.py`（`_execute_v3` `:391-392` 传入 `execution_adapter=get_adapter("local_python")`）
  - 修改 `core/runtime/execution/session.py`（`RuntimeSession` 默认 `execution_adapter` 从 None 改为可注入并透传）
  - 修改 `core/runtime/execution/handlers.py`（`_maybe_execute_experiment` `:456-504`：从 `plan.code` 构造 `ExecutionPlan` 调 `execute_code`；失败 → `NodeResult(FAIL)` 替代 `handlers.py:452-454` 的恒 PASS）
  - 修改 `core/runtime/graph/evidence_graph.py`（注册 `code -executed_by-> execution_result` 与 `execution_result -produces-> result` 类型；注意现有 `executed_by` from∈{result}（`:48`）与 `produces` 仅 (experiment)→(result)（`:41`），需扩 from/to 集合或新增正向边）
- **新增/修改的类与函数（签名级）**
  - `DefaultNodeExecutor._maybe_execute_experiment(question_id, plan, ...)`：`ExecutionPlan(model_id=..., code=plan["code"], adapter=...)` → `adapter.execute` → `reg.create("execution_result", ...)`（沿用 `ExecutionResultData.to_dict()`，`adapters.py:107-126`）→ 写 `code -executed_by-> execution_result`、`execution_result -produces-> result`（新正向边；旧 `result→execution_result` 反向边保留兼容或迁移）
  - `EvidenceGraph`：`executed_by` from 集合扩为 `{result, code}`；`produces` from 集合扩为 `{experiment, execution_result}`（或新增正向边类型）
- **测试**：`tests/integration/test_execution_production.py`
  - 断言 1：默认 orchestrator 语义下产生 `execution_result`，status ∈ 六态枚举真实值（非恒 `not_executed`）
  - 断言 2：result artifact status 由 returncode 推导（success/failed）
  - 断言 3：evidence_graph 含 `code→execution_result` 与 `execution_result→result` 正向边
  - 断言 4：执行失败时 `do_experiment` 返回 FAIL（修复 `handlers.py:452-454`），节点可被引擎识别
- **验收标准**：`py -3.12 -m pytest tests/integration/test_execution_production.py tests/integration/test_execution_runtime.py -q` 全绿；`state.py reconcile` 通过
- **工作量 / 风险**：L（>4h）。风险：修改 `executed_by`/`produces` 类型集合会影响 `evidence_graph` 校验与既有测试断言（`test_execution_runtime.py:70-72` 断言 result→execution_result，需保持或迁移）。

## C8 — `feat(p1-model): consume validation report in DAG and extend fidelity checks`

- **改动文件**
  - 修改 `core/runtime/execution/handlers.py`（`do_experiment_critique`/`do_evidence_gate` 读取 VR 状态：VR failed/invalid → 节点 FAIL；`handlers.py:543-547` 终态判断扩展）
  - 修改 `core/runtime/execution/fidelity.py`（F2/F3/F4 从"符号可观测"扩展约束方向：输出 key 存在 + value_range 数值范围，`fidelity.py:54-114`）
  - 修改 `core/runtime/execution/validation.py`（`run_check` 新增 kind：`output_residual` / `output_feasibility`，`validation.py:104-150`）
  - 修改 `core/runtime/execution/session.py`（`WorkflowEngine` 构造传入 validators，激活 `engine._run_validator` `:169-179`）
- **新增/修改的类与函数（签名级）**
  - `validation.run_check(execution_data, check: dict)`：新增 `output_residual`（残差超阈值→failed）、`output_feasibility`（约束违例→failed）
  - `fidelity.fidelity_checks_from_ir(model_ir: dict)`：输出含约束方向检查（F2/F3 扩展）
  - `DefaultNodeExecutor.do_evidence_gate(...)`：读 `verification_result` artifact，`status == "failed"` → `NodeResult(FAIL)`
- **测试**：`tests/integration/test_validation_dag.py`
  - 断言 1：VR failed 时 evidence_gate 节点 FAIL（状态可查）
  - 断言 2：约束不满足（残差超限）时 fidelity 状态为 misaligned → VR failed
  - 断言 3：执行失败产生的 execution_result 被 VR 引用（`verified_by` 边存在，`validation.py:217` 语义保留）
  - 断言 4：L0 门禁生效：`execution_result`/`verification_result` 过 JSON Schema（补 `core/schemas/` 缺失项）
- **验收标准**：`py -3.12 -m pytest tests/integration/test_validation_dag.py tests/integration/test_execution_validation.py tests/integration/test_execution_fidelity.py -q` 全绿；`py -3.12 core/tools/validate.py` 通过
- **工作量 / 风险**：M–L（1–4h+）。风险：engine validators 激活可能改变既有节点执行路径，需逐步开启并保持默认 PASS 场景不回归；五层体系完整落地超出 P1，本 commit 只做 L0–L2 最小集。

## C9 — `fix(p1-model): harden evidence gate against placeholder claims`

- **改动文件**
  - 修改 `core/validators/evidence/evidence_gate.py`（E1–E8 增加：`claim.placeholder==True` 拒绝、`result.status=="not_executed"` 拒绝、`execution_result` 存在性检查）
  - 修改 `core/runtime/execution/handlers.py`（实现或删除 `register_external_artifact` 承诺——`handlers.py:432` note 指向的函数不存在，二选一：实现回填函数，或删除 note 并把占位回填改为显式失败）
  - 修改 `core/runtime/execution/handlers.py`（`do_evidence_build` `:569-578`：无数值时不再创建 `placeholder: True` 的 claim 及其 supports 边，改为登记 blocked 状态）
- **新增/修改的类与函数（签名级）**
  - `EvidenceGate` 新增检查 `_check_numeric_backing(...)`（或 E9：claim 必须有非占位 result + execution_result 支撑）
  - `register_external_artifact(project_dir, registry, artifact_data: dict) -> str`（实现：校验 + `reg.create` + evidence 回填；若选择删除则同步清理 note）
- **测试**：`tests/unit/test_evidence_gate.py`
  - 断言 1：`placeholder: True` 的 claim 链 → gate FAIL（反转 `test_runtime_session.py:55-56` 的 `claims_supported=2, coverage=1.0` 场景）
  - 断言 2：`result.status=="not_executed"` → gate FAIL
  - 断言 3：`register_external_artifact` 存在且回填后 result 翻为 executed（若实现）
  - 断言 4：占位 claim 不产生 supports 边
- **验收标准**：`py -3.12 -m pytest tests/unit/test_evidence_gate.py tests/integration/test_runtime_session.py -q` 全绿——注意：本 commit 会改变默认 run 的 gate 语义，`test_runtime_session.py` 中占位场景断言需同步更新为新语义（占位→FAIL）
- **工作量 / 风险**：M（1–4h）。风险：主动打破既有"占位即 PASS"断言，属预期行为变更，须在 commit 内同步更新测试并说明。

## C10 — `test(p1-model): end-to-end minimal closed loop`

- **改动文件**
  - 新增 `tests/integration/test_p1_closed_loop.py`（验收标准 e2e）
  - 新增测试 fixture：`tests/fixtures/p1_problem/features.json` + `problem.yaml`（最小可运行 problem）
  - 修改 `core/tools/validate.py`（如 C1 未完成，注册 model_ir schema 校验项）
- **新增/修改的类与函数（签名级）**
  - `test_p1_closed_loop.py::test_minimal_closed_loop`（主场景：problem→…→verified 谱系全通）
  - `test_p1_closed_loop.py::test_execution_failure_observable`（失败场景：代码制造 failed execution_result，断言节点 FAIL 可观测）
- **测试断言**
  - 断言 1：给定 problem 跑通后，`execution_result.status` 为 success 或明确 failed，且 `verification_result` 存在（validated 或 failed 二选一）
  - 断言 2：`evidence_graph.json` 可查询完整正向谱系（问题→模型→代码→执行→验证→claim 全链）
  - 断言 3：`state.py reconcile` 通过（Registry/Graph/状态三源一致）
  - 断言 4：`validate.py` 全绿（57 项不回归）
- **验收标准**：`py -3.12 -m pytest tests/integration/test_p1_closed_loop.py -q` + `py -3.12 core/tools/validate.py` + `py -3.12 core/tools/state.py <项目> reconcile`
- **工作量 / 风险**：M（1–4h）。风险：依赖 C1–C9 全绿；fixture 需避开真实赛题数据以免引入外部依赖。

---

## 最小闭环路径（MVP cut）

只做 **C1 + C5 + C6 + C7 + C10**（选型/决策真实化 C2–C4 后置）：

- 产出：给定 problem → MODEL_IR artifact（18 字段齐）→ code artifact（模板渲染）→ 真实 `execution_result`（subprocess 退出码推导）→ e2e 谱系查询全通。
- 可演示结果：一条 `test_p1_closed_loop.py` 端到端测试 + `evidence_graph.json` 中可见 `problem→question→model→model_ir→code→execution_result` 全链；`result.status` 不再是恒 `not_executed`。
- 代价：C2–C4 未做时选型仍是 `recs[0]`（可接受，P1 目标是"接通"而非"选型最优"）；C8/C9 未做时占位 claim 仍可通过 evidence_gate——因此 **正式交付建议 MVP 后补 C9**，否则"占位链可骗过门禁"的结论在 P1 结束时依然成立。

## 与 P0-E2 / P2 / P3 / P4 的边界

- **P0-E2**：执行完整性细节——`environment_hash` 深指纹（包版本/依赖/种子）、replay 依赖漂移检测、EXEC 全字段 schema 门禁、`register_external_artifact` 的完整回填语义，本计划不做。
- **P2**：语义保真（semantic fidelity）——约束残差/目标最优/方程数值正确性、L3 数学语义校验、fidelity 从"符号可观测"升级为"数值满足"，本计划只在 C8 埋 `output_residual`/`output_feasibility` 两个原语，不做全套。
- **P3**：L3/L4 校验体系——feasibility/stability/domain 全套检查、五层 L0–L4 统一分层落地，本计划仅做 L0（schema 门禁）与 L1/L2 最小集。
- **P4**：Revision 闭环——"V1 FAIL→M2" 端到端自动触发、revision_of/supersedes 类型化边、幂等复用语义修正（`handlers.py:377-402`），本计划只保证失败可观测（节点 FAIL/VR failed），不实现自动重建模。


---

## P1 里程碑执行记录（VS-001 / M3 / M4 追加）

> 本节为 P1 后续里程碑在实施过程中对原计划的追加记录（2026-09-09），原计划 C1–C10
> 保留为历史规划；实际交付以各里程碑 REPORT 为准。

### M1 / VS-001（可执行模型闭环）— 已完成
- 落地：C1 MODEL_IR 升入 core（model_ir.py 18 字段）+ C5 外部 MODEL_IR 登记（instantiates 边）
  + C6 Code 节点（implemented_by 边，固定 ABI `def solve(inputs) -> outputs`）
  + C7 真 subprocess 执行（executed_by/produces 边，status 来自真实退出码）
  + C8 数值验证（verified_by 边，VR 四字段）+ C10 e2e 闭环（revision lineage 不覆盖 M1）
- 证据：`research/P15/analysis/P1_VS001_REPORT.md`；演示 `research/P15/vs001_run/`

### M3（Candidate Competition + Evidence-based Selection）— 已完成
- 落地：多候选独立链 MIR-i→CODE-i→EXEC-i→R-i→VR-i；`do_model_selection` 消除 recs[0]
  假选型（容器登记）；新增 `model_selection_decision` 节点做 VR 机械指标排序
  （mathematical_valid 优先 → constraint_violation_max 升序 → … → model_id tie-break）；
  decision 全字段（alternatives/criteria/evidence_ids/chosen/confidence/reasoning）；
  首次真正写入 `decision -selects-> model` 边；无证据如实 UNSELECTED。
- 证据：`research/P15/analysis/P1_M3_REPORT.md`；演示 `research/P15/m3_run/`

### M4（Knowledge-guided Construction）— 已完成（本计划收尾）
- 落地：知识义务显式贯穿（`candidates.map_card_obligations`：card.validation/risks/requires
  /required_conditions → 候选 validations/assumptions/risks/dependencies，每项带
  source_card 可溯源）；BZD 试点知识卡 5 张（`core/knowledge/methods/cards/mc-bzd-*.yaml`，
  source_type=BZD，可被 retriever 检索）；知识引导 vs 无引导对比 demo（义务完备度可测量）。
- 结果摘要：引导候选义务 19 项（validations 8 / assumptions 5 / risks 6，来源 2 张 BZD 卡）
  vs 无引导候选 2 项；两候选共用同一正确求解器，EXEC/VR 数值一致（均 PASS、cv=0.0），
  选型平局按确定性 tie-break——如实展示"义务完备度差异可测量，执行/验证无差异"
  （不预设"知识必胜"）。
- 证据：`research/P15/analysis/P1_M4_REPORT.md`；演示 `research/P15/m4_run/`
- 验证数字：pytest 910 passed / 4 skipped；catalog_check OK；validate 57/0。

### P1 结论（三里程碑合流）
`Problem → Knowledge Retrieval → Candidate Models → Execution → Validation → Evidence
→ Selection` 全链已接通：知识（BZD 试点卡）→ 候选（义务声明，可溯源）→ 执行/验证
（真实数值裁决）→ 证据（VR）→ 选型（机械排序 + selects 边）。K002 可在此链上测量
"知识是否提升建模能力"（义务完备度已可量化）。
