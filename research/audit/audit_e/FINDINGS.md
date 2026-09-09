# Model Revision Loop 独立审计报告（Agent E）

- **审计日期**：2026-09-09
- **审计人**：Agent E（独立修订审计官，只读审计）
- **仓库**：`C:\Users\Lin\Desktop\Programs\MathModel`
- **审计范围**：仅追踪如下链是否真实存在并可执行：
  `FAIL → Failure Diagnosis → Revision Proposal → M2 (revision_of M1) → Re-execution → Validation → Compare(M1,M2) → Accept/Reject`
- **只读承诺**：本次审计未修改任何代码、测试或配置文件；输出仅写入本报告文件。
- **审计方法**：通读 `core/runtime/graph/evidence_graph.py`、`core/runtime/artifacts/lifecycle.py`、`core/runtime/artifacts/registry.py`、`core/runtime/execution/handlers.py`、`core/runtime/execution/engine.py`、`core/runtime/modeling/model_ir.py`、`core/runtime/modeling/selection.py`、`core/runtime/decisions/log.py`、`core/runtime/state/relations.py`、`core/runtime/execution/replay.py`、`core/tools/replay.py`；读取 P1 实验实际状态文件（`p1-vs001/project/state/registry.json`、`evidence_graph.json`、`m1/result.json`、`m2/result.json`、`replay_report.json`）、`p1_vs001_runner.py`、`_inspect.py`、`vs001_run/*`、`m3_run/*`、`m4_run/*`、`PROGRESS-P1-VS001-2026-09-09.md`、`analysis/MODEL_CONSTRUCTION_GAP_AUDIT.md`、`tests/integration/test_p1_vs001_e2e.py`。

---

## 1. 审计范围摘要

审计目标是判定 P1-VS-001 声称的「模型构造—运行—验证—失败—修正—再运行」真实闭环
（PROGRESS 文件：「LinHoMo 第一次完成『模型构造—运行—验证—失败—修正—再运行』真实闭环」）
是否成立，以及 `revision_of` / `supersedes` 谱系机制是真实可执行，还是仅声明性存在。

**核心判定原则**：如果没有 failure evidence → revision reason → changed components →
re-execution → comparison，则不得声称存在 Model Revision Loop。

**审计结论（一句话）**：**部分真实（REAL 6 环节，GAP 4 环节，无 FAKE 编造数据）；但"失败诊断 → 修订方案生成 → M1/M2 比较 → 接受/拒绝"4 个环节在当前系统中不存在自动机制，全部由实验脚本手工构造（fixtures + 硬编码字符串）或完全缺失。因此不得声称存在完整的自动化 Model Revision Loop；当前实际存在的是一个由外部 Model Constructor（人工/脚本）驱动的"谱系记录 + 重执行"闭环，而非系统自驱动的修订闭环。**

---

## 2. 发现计数

| 严重级 | 数量 | 编号 |
|---|---|---|
| **HIGH** | 7 | E-001, E-002, E-003, E-004, E-005, E-008, E-010 |
| **MEDIUM** | 5 | E-006, E-007, E-009, E-012, E-013 |
| **LOW** | 1 | E-011 |
| **合计** | **13** | E-001 … E-013 |

---

## 3. 修订链逐环节状态（REAL / GAP / FAKE）

| # | 环节 | 状态 | 依据 |
|---|---|---|---|
| 1 | **FAIL（执行/验证失败）** | **REAL** | M1 数值验证真实判 FAIL：`VR002` status=failed，4/5 检查失败，`constraint_violation_max=0.275`（p1-vs001 registry + e2e `test_05`）；M1 为真实 subprocess 执行（EXEC002 success，输出负值 Wq=-0.09） |
| 2 | **Failure Diagnosis（失败诊断）** | **GAP** | core runtime 无任何诊断代码（grep `diagnosis/corrective_action` 仅在 legacy Programmer 代码排错与实验脚本）；`engine.py:_handle_failure` 只做 retry → rollback_to/blocked，不分析失败原因；p1-vs001 的"诊断"是 runner 里**硬编码字符串**（见 E-003/E-004） |
| 3 | **Revision Proposal（修订方案生成）** | **GAP** | 无任何机制"基于失败证据生成修订方案"；M2 的 MODEL_IR 是**预写文件** `m2/model_ir_v2.json`，vs001_run 的 M2 是**预写 fixture** `vs001_fixtures.M2_DICT`；runtime 仅读取外部注入的 `revision_of` 登记谱系（E-005） |
| 4 | **M2 (revision_of M1)** | **REAL（部分）** | Evidence Graph 中 M2 -revision_of-> M1 边真实存在（p1-vs001：`MIR003 -revision_of-> MIR002`；vs001_run：`MIR002 -revision_of-> MIR001`）；但（a）runtime 路径（handlers.py）**不调用 `registry.supersede`**，旧 MIR 保持 active（vs001_run registry 实证 MIR001=active）；（b）`supersedes` 边方向在两套路径中**相反**（E-002）；（c）无 `changed_components` 结构化字段（E-006） |
| 5 | **Re-execution（M2 真实重执行）** | **REAL** | M2 经真实 subprocess（LocalPythonAdapter）重新执行：EXEC003（p1-vs001）/ EXEC002（vs001_run），输出为修正后真实数值（Wq=0.032 / body_spacing=1.65）；e2e `test_06` 断言 2 code + 2 EXEC + 2 VR |
| 6 | **Validation（M2 验证）** | **REAL** | VR003 / VR002 status=passed，6/6 检查通过（真实数值判定） |
| 7 | **Compare(M1, M2)** | **GAP** | 修订路径（p1-vs001 / vs001_run）**无任何 M1/M2 比较逻辑**——无指标对比计算、无 delta 记录、无 "M2 优于 M1 因为…" 的决策产物；m3 候选竞技场有机械比较（`do_model_selection_decision`），但那是**独立候选选型**（m3 无 revision_of 边），不是修订比较（E-008/E-009） |
| 8 | **Accept/Reject（接受/拒绝决策）** | **GAP** | 无任何"接受/拒绝 M2"的决策类型或决策产物；p1-vs001 唯一的决策 D001 是 "Revision Request"（记录型），VR003 passed 是验证结果而非决策；m3 D002 是 `kind=candidate_selection`（选型）非 Accept/Reject（E-010） |

**链整体判定**：`FAIL(REAL) → 诊断(GAP) → 提案(GAP) → M2 谱系(REAL) → 重执行(REAL) → 验证(REAL) → 比较(GAP) → 接受/拒绝(GAP)`。
按核心判定原则（缺 failure evidence / revision reason / changed components / re-execution / comparison 任一即不得声称），**该链不完整，不构成 Model Revision Loop**。当前实证链是：
`FAIL(REAL) → [人工读取失败 → 手工写 M2 + 硬编码诊断] → M2 谱系登记(REAL) → 重执行(REAL) → 验证(REAL) → [结束，无比较/无决策]`。

---

## 4. 系统能否回答「为什么 M2 比 M1 更好」

**修订路径：不能。**

- 在 p1-vs001 / vs001_run 的 revision 链中，不存在任何比较产物。证据图中只有
  `MIR002 -revision_of-> MIR001` / `MIR003 -revision_of-> MIR002` 等谱系边，
  **没有任何 artifact 记录"M2 在哪个指标上比 M1 好、好多少"**。
- 唯一的"为什么"文本是 runner 脚本里的硬编码诊断字符串（`"diagnosis": "M1 v1 的服务率参数错误（mu 过小）…"`，p1_vs001_runner.py:331-332），
  **它不在任何可查询的状态产物中**（registry 的 D001 只存了 `data` 里那份 dict——实际存了，但它是手工填的，不是由系统推导的；vs001_run 的 registry 中连 D001 都没有诊断字段，D001 是方法选型决策）。
- 从落盘状态（registry.json + evidence_graph.json）出发，审计者/系统只能回答
  "M1 VR 失败（constraint_violation_max=0.275）、M2 VR 通过（0.0）"，
  **不能回答"为什么修改 mu 就能修复"**——因为那个因果链从未被系统记录或推导。

**候选竞技场路径（m3）：部分能。**

- `do_model_selection_decision`（handlers.py:639-740）基于真实 VR 指标机械排序
  （mathematical_valid → constraint_violation_max 升序 → execution_valid → …），
  并把推理写入 decision 的 `reasoning` 字段（"chosen=MIR002 because VR002.mathematical_valid=True; MIR001(VR001.constraint_violation_max=0.275) worse than VR002.constraint_violation_max=0.0)"）。
- 但这是**独立候选选型**（m3 的 MIR001/MIR002 之间无 revision_of 边），
  与修订环是两条未接通的路径。

**结论**：系统当前**不能**从自身状态回答"为什么 M2 比 M1 更好"；该答案只存在于实验脚本作者的手写文字中。

---

## 5. Findings（逐条）

---

### E-001 — `revision_of` / `supersedes` 边类型真实存在，但为"零传播审计边"，无任何消费方

- **Severity**：HIGH（机制存在的核心证据，但语义价值未被任何下游读取）
- **File**：`core/runtime/graph/evidence_graph.py`
- **Function-Symbol**：`RELATION_TYPES` / `WEAK_RELATIONS` / `_PROPAGATION`
- **Line**：51-52（类型定义）、59（WEAK）、88-89（传播档位）
- **Observed behavior**：
  - `"revision_of": ({"model","model_ir"}, {"model","model_ir"})`、`"supersedes": (...)` 已定义；
  - 两者在 `WEAK_RELATIONS` 中；`_PROPAGATION` 中均为 `(None, None)`，注释「修订谱系：审计边，不传播」「替代谱系：审计边，不传播」；
  - 实际落盘：p1-vs001 `evidence_graph.json`（graph_version=20）含 `MIR003 -revision_of-> MIR002`、`MIR003 -supersedes-> MIR002`。
- **Expected behavior**：修订/替代谱系边应至少被某个下游机制消费（如"当前活跃模型解析""模型演进追溯查询"），否则其"审计"价值仅限于人工读文件。
- **Why it matters**：边存在但不被消费 = 声称"谱系入图"成立，但图无法驱动任何决策。
- **Evidence**：evidence_graph.py:51-52,59,88-89；p1-vs001/project/state/evidence_graph.json（16 边）。
- **Reproduction**：`py -3.12 -c "from runtime.graph.evidence_graph import EvidenceGraph; g=EvidenceGraph(); print(g.propagation('revision_of'))"` → `(None, None)`；全仓库 grep 无任何读取 revision_of 边做决策的调用点。
- **Proposed fix**：定义"活跃模型解析"（沿 supersedes/revision_of 求当前有效 MIR）并在 evidence gate / selection 消费；或至少在 validate.py 增加"revision 边两端 artifact 存在且 M1 为 superseded"的一致性校验。
- **Regression risk**：低（新增只读解析函数，不改现有边语义）。
- **Test required**：`tests/unit/test_evidence_graph.py` 增加"revision 边不参与传播但可被 lineage 查询"用例。

---

### E-002 — `supersedes` 边方向在两套官方路径中相反，语义自相矛盾

- **Severity**：HIGH（同一仓库两套实现给出互斥的谱系语义）
- **File**：`core/runtime/execution/handlers.py` vs `research/P15/experiments/p1-vs001/p1_vs001_runner.py`
- **Function-Symbol**：`_register_mir`（handlers）vs `register_revision`（runner）
- **Line**：handlers.py:204-205；p1_vs001_runner.py:129-130
- **Observed behavior**：
  - handlers.py（runtime/V3 主路径 + vs001_run + e2e）：`new -revision_of-> old` **且 `old -supersedes-> new`**（"旧模型 supersedes 新模型"）；
  - p1_vs001_runner.py（research 实验）：`new -revision_of-> old` **且 `new -supersedes-> old`**（"新模型 supersedes 旧模型"）；
  - 落盘实证：vs001_run evidence_graph 含 `MIR001 -supersedes-> MIR002`；p1-vs001 evidence_graph 含 `MIR003 -supersedes-> MIR002`。
- **Expected behavior**：谱系语义单一真源。"supersedes"应统一为"新替代旧"（new -supersedes-> old），或明确文档化两种方向的语义差异。
- **Why it matters**：任何按方向解析"谁是当前模型"的消费方（未来的 lineage 查询、论文报告、审计）会得到互斥答案；且 e2e 测试固化的是**语义反常**的方向（`test_06` 断言 `MIR1 -supersedes-> MIR2`）。
- **Evidence**：handlers.py:205 `self.graph.add_relation(rev_of, "supersedes", art.artifact_id)`；p1_vs001_runner.py:130 `g.add_relation(new_mir_id, "supersedes", old_mir_id)`；tests/integration/test_p1_vs001_e2e.py:161。
- **Reproduction**：分别运行 `p1_vs001_runner.py --stage m2` 与 `run_vs001_demo.py`，比较两 registry 的 supersedes 方向。
- **Proposed fix**：冻结方向为 `new -supersedes-> old`（与自然语义一致），修正 handlers.py:205 与 e2e:161；或修改 p1-vs001 runner 与其保持一致；在 evidence_graph 增加方向校验（不允许 old -supersedes-> new）。
- **Regression risk**：中（e2e 断言需同步修改；vs001_run 落盘数据需重新生成或显式迁移说明）。
- **Test required**：`tests/integration/test_p1_vs001_e2e.py:158-161` 断言改为 new→old；新增单测校验方向。

---

### E-003 — 引擎失败处理不含失败诊断：只有 retry → rollback/blocked

- **Severity**：HIGH（"失败诊断"环节在引擎层完全缺失）
- **File**：`core/runtime/execution/engine.py`
- **Function-Symbol**：`_handle_failure` / `rollback_to` / `reset_to`
- **Line**：218-231（_handle_failure）、262-281（reset_to/rollback_to）
- **Observed behavior**：节点 FAIL 后仅（a）计数重试（`workflow_record_retry`），（b）耗尽后 `rollback_to(node.on_fail)` 回退重置下游，或（c）无 on_fail 时 blocked。**全程无任何"分析失败原因、定位问题组件"的代码路径**。
- **Expected behavior**：失败后应至少产出结构化失败诊断（失败节点、失败检查项、疑似根因组件）供后续提案环节消费。
- **Why it matters**：引擎是 V3 主路径的唯一失败处理者；它不诊断，则"自动修订"无从谈起。
- **Evidence**：engine.py:218-231；grep 全 core 无 `diagnos` 命中（runtime 层）。
- **Reproduction**：构造任一 FAIL 节点，观察 `_handle_failure` 输出——只有 retry 计数与回退记录，无诊断记录。
- **Proposed fix**：在 `_handle_failure` 中新增可选的 `diagnose(node) -> dict` 钩子（默认记录 failed_checks/exception 摘要到 decision log 或状态 notes），不阻断既有 retry 语义。
- **Regression risk**：低（纯增量）。
- **Test required**：引擎单测新增"FAIL → 生成诊断记录"用例。

---

### E-004 — p1-vs001 的"诊断"是 runner 中硬编码字符串，非由失败证据推导

- **Severity**：HIGH（唯一的"诊断"产物是手工文本）
- **File**：`research/P15/experiments/p1-vs001/p1_vs001_runner.py`
- **Function-Symbol**：`stage_m2`
- **Line**：325-335
- **Observed behavior**：`revision_request = { "trigger": "validation_failed", "failed_checks": [来自 m1_result 的真实失败检查], "diagnosis": "M1 v1 的服务率参数错误（mu 过小）…"（字面量字符串）, "corrective_action": "修正服务率 mu 为正确值…"（字面量字符串）}`。`failed_checks` 是真实证据，但**原因与修复动作是作者手写**；没有任何代码从 `constraint_violation_max=0.275` 或失败检查项推导出"mu 过小"。
- **Expected behavior**：诊断应由失败证据（VR 字段、检查项、参数域）经可复现规则推导，或至少标注 `diagnosis_source: manual` 以诚实区分。
- **Why it matters**：PROGRESS 声称"诊断: 服务率参数过小致系统不稳定"是闭环的一环；若该环节是手写，则"闭环"是人工参与而非系统能力。
- **Evidence**：p1_vs001_runner.py:326-335；`m2/result.json` 的 `revision_request.diagnosis`。
- **Reproduction**：删除 runner 中 diagnosis 字符串，闭环仍可跑通——证明诊断不参与任何机制。
- **Proposed fix**：实现参数域诊断规则（如 rho>=1 → 参数过小/过大提示），或显式声明当前为 manual diagnosis 并纳入遗留缺口清单。
- **Regression risk**：低。
- **Test required**：单测"从 VR 失败字段推导出诊断候选"。

---

### E-005 — 无修订方案生成机制：M2 全部来自预写 fixtures / 外部注入

- **Severity**：HIGH（"Revision Proposal"环节不存在自动机制）
- **File**：`core/runtime/execution/handlers.py`（`_register_mir`）、`research/P15/vs001_run/vs001_fixtures.py`、`research/P15/experiments/p1-vs001/p1_vs001_runner.py`
- **Function-Symbol**：`_register_mir` / `M2_DICT` / `stage_m2`
- **Line**：handlers.py:188-205；vs001_fixtures.py:251（M2_DICT）；p1_vs001_runner.py:337-338
- **Observed behavior**：
  - handlers.py 只读取外部 dict 的 `revision_of`/`supersedes` 键来登记谱系边，**不生成任何修订内容**；
  - vs001_run 的 M2 是 `vs001_fixtures.M2_DICT`（修正参数 mu=40 的完整 MODEL_IR 字典）；
  - p1-vs001 的 M2 是预写文件 `m2/model_ir_v2.json`；
  - 两处都没有"M1 失败 → 生成 M2 候选"的代码。
- **Expected behavior**：修订方案生成器（LLM 或规则）消费失败诊断，产出 M2 候选；当前设计明确是"外部 Model Constructor 接手"（PROGRESS 自述），故应归为 GAP。
- **Why it matters**：核心原则要求 revision reason → changed components → 修订方案的可追溯链；当前 M2 的诞生完全在系统外。
- **Evidence**：handlers.py:189 `rev_of = external.get("revision_of") or external.get("supersedes")`；vs001_driver.py:8-12「M1/M2 MODEL_IR 与 C1/C2 代码由 vs001_fixtures 手写注入」。
- **Reproduction**：grep core 中任何生成 MODEL_IR 修订内容的代码 → 无。
- **Proposed fix**：短期在 P1 文档显式声明"M2 生成=外部人工/LLM，不在 runtime 内"；中期接入 Model Constructor（V3 Role analyst/modeler）输出 M2 候选并由 runtime 登记。
- **Regression risk**：中（涉及 role 接线，属 P1 遗留项 C6-C10）。
- **Test required**：集成测试"外部注入 M2 → runtime 完整登记谱系+重执行+验证"（已有 e2e，补充"修订内容来源"标注断言）。

---

### E-006 — M1→M2 之间无 `changed_components` 结构化记录（参数 diff 缺失）

- **Severity**：MEDIUM（"改了什么"不可从状态追溯）
- **File**：`core/runtime/modeling/model_ir.py`、`core/runtime/execution/handlers.py`、两套 runner
- **Function-Symbol**：`ModelIR` / `_register_mir`
- **Line**：model_ir.py:33-52（18 个 required 字段，无 revision 元数据）；handlers.py:190-191（仅存 `data["revision_of"]`）
- **Observed behavior**：MODEL_IR schema 无 `revision` / `changed_components` / `diff_base` 字段；M1（mu=20）与 M2（mu=40）之间的差异只存在于两个独立 MODEL_IR 字典中，**没有任何 artifact 记录"变更组件=parameters.service_rate，20→40"**；D001 的 corrective_action 是散文文本，非结构化。
- **Expected behavior**：修订链应携带结构化变更清单（哪些 L1/L2/L3 组件、哪些参数、从什么到什么），供比较与审计。
- **Why it matters**：核心原则要求 changed components 可追溯；缺失则"为什么改、改了哪"只能靠人肉 diff 两份 JSON。
- **Evidence**：p1-vs001 `m1/model_ir_v1.json` vs `m2/model_ir_v2.json`（手工对比可见 mu 20→40）；registry 中 MIR002/MIR003 的 data 均无变更字段。
- **Reproduction**：对 MIR002/MIR003 的 data 做结构化 diff 查询 → 无现成字段。
- **Proposed fix**：`_register_mir` 在 rev_of 存在时自动计算 `changed_components`（参数/方程/求解器差异）写入 MIR.data；或至少要求外部注入 `changed_components`。
- **Regression risk**：低。
- **Test required**：单测"M2 登记时自动生成与 M1 的参数 diff"。

---

### E-007 — runtime 路径不调用 `registry.supersede`：vs001_run 中 M1 与 M2 同时保持 active

- **Severity**：MEDIUM（生命周期与图谱不一致，双活模型并存）
- **File**：`core/runtime/execution/handlers.py`、`core/runtime/artifacts/registry.py`
- **Function-Symbol**：`_register_mir`（缺 supersede 调用）/ `registry.supersede`
- **Line**：handlers.py:188-205；registry.py:284-295（supersede 已实现但 core 无调用点）
- **Observed behavior**：
  - `registry.supersede` 真实存在（置 superseded + invalidated_by=replacement），**但全 core 无任何 `.supersede(` 调用**（grep 实证）；
  - vs001_run registry 实证：MIR001=active、MIR002=active（旧 MIR 未被标记 superseded），仅图谱上有 `MIR001 -supersedes-> MIR002` 边；
  - 仅 research 实验 runner（p1_vs001_runner.py:131-134）调用 `reg.supersede`，故 p1-vs001 中 MIR002=superseded/invalidated_by=MIR003 是真实的。
- **Expected behavior**：登记 revision 谱系时，旧 MIR 应同步生命周期 superseded（或图谱与生命周期至少一致），否则证据门禁会把 M1/M2 都当活跃模型计数。
- **Why it matters**：状态单一真源原则（AGENTS.md）要求 status.json/registry 与图谱一致；双活会污染覆盖率统计与选型。
- **Evidence**：vs001_run/project/state/registry.json（MIR001 active）；grep core `\.supersede\(` → 0 命中。
- **Reproduction**：运行 `run_vs001_demo.py` 后查询 MIR001.status → active。
- **Proposed fix**：在 `_register_mir` 的 `if rev_of:` 分支内补 `self.registry.supersede(rev_of, reason=..., replacement=art.artifact_id, by=created_by)`；同步修正 e2e `test_06`（其断言 M1 保持 active，与 superseded 语义冲突）。
- **Regression risk**：中（e2e 断言、evidence gate 计数可能变化，需同步）。
- **Test required**：e2e 增加"M2 登记后 M1 状态=superseded 且 invalidated_by=M2"断言。

---

### E-008 — 修订路径无 M1/M2 比较逻辑（Compare 环节缺失）

- **Severity**：HIGH（无法回答"为什么 M2 更好"）
- **File**：`research/P15/experiments/p1-vs001/p1_vs001_runner.py`、`research/P15/vs001_run/vs001_driver.py`
- **Function-Symbol**：`stage_m2` / `run_m2` / `REVISION_NODES`
- **Line**：p1_vs001_runner.py:310-407（stage_m2 全流程无比较）；vs001_driver.py:97-111
- **Observed behavior**：M2 执行验证后流程即结束；`m2/result.json` 记录了 M2 侧输出与验证，**没有任何对 M1/M2 的指标对比、delta 计算、优劣结论**；report 中 M1 FAIL vs M2 PASS 的并排展示是叙述性文字，非程序化比较。
- **Expected behavior**：Compare 环节应基于真实指标（fidelity、validation score、constraint_violation_max 等）计算 delta 并落为可查询 artifact。
- **Why it matters**：核心原则要求 comparison 存在；缺失则"接受 M2"没有任何依据可引用。
- **Evidence**：`m2/result.json`（无 comparison 字段）；vs001_run demo_summary.json 仅并排两段 summary。
- **Reproduction**：运行 p1-vs001 `--stage all`，检查输出中是否有任何 M1-vs-M2 比较产物 → 无。
- **Proposed fix**：新增 `compare_revisions(state, m1_mir, m2_mir, m1_vr, m2_vr)` 原语（对比 mathematical_valid / constraint_violation_max / 输出指标），产出 comparison artifact 并接入修订链；可复用 m3 的 `_rank_candidates` 指标表。
- **Regression risk**：低。
- **Test required**：单测 compare_revisions 对 p1-vs001 真实数据产出 delta。

---

### E-009 — m3 候选竞技场的机械比较存在但未接通修订环

- **Severity**：MEDIUM（比较能力真实，但服务于"选型"而非"修订"）
- **File**：`core/runtime/execution/handlers.py`
- **Function-Symbol**：`do_model_selection_decision` / `_rank_candidates` / `_decision_confidence`
- **Line**：639-740（decision）、596-615（rank）、617-637（confidence）
- **Observed behavior**：m3 运行真实比较两个候选（mathematical_valid → constraint_violation_max 升序 → …），产出 D002 `kind=candidate_selection`，`reasoning` 含真实指标对比；但 m3 的 MIR001/MIR002 之间**无 revision_of/supersedes 边**（registry/graph 实证），是"独立候选竞技"，不是"M1 失败→M2 修订"。
- **Expected behavior**：若修订环要复用比较逻辑，应让 M2（revision_of M1）也进入同一比较管道，统一产出"选择/接受"决策。
- **Why it matters**：两条路径（revision 谱系 vs 候选比较）各实现一半，未接线 = 声称"闭环"时比较环节实际不可达。
- **Evidence**：m3_run/project/state/evidence_graph.json（无 revision 边）；m3 demo_summary.json selection.reasoning。
- **Reproduction**：在 vs001_run 修订链中搜索任何 `_rank_candidates` 调用 → 不经过（REVISION_NODES 无 model_selection_decision）。
- **Proposed fix**：修订链末尾追加 model_selection_decision 节点（若 M2 revision_of M1 且 M1 有 VR），让 M2 的接受判定走同一比较管道。
- **Regression risk**：低-中（DAG 节点顺序变化）。
- **Test required**：集成测试"修订链 M1(M2 候选) 经 selection_decision 产出接受决策"。

---

### E-010 — 无 Accept/Reject 决策：修订结果从不被"接受/拒绝"

- **Severity**：HIGH（决策环节完全缺失）
- **File**：`core/runtime/decisions/log.py`、两套 runner
- **Function-Symbol**：`DecisionLog`（无 accept/reject 类型）
- **Line**：log.py（decision 字段：chosen/alternatives/criteria/evidence_ids/reasoning/confidence/reversible，无 accept/reject 语义）；p1_vs001_runner.py:136-140（D001 为 "Revision Request" 记录型）
- **Observed behavior**：修订链终点是 VR003 passed（验证结果），**没有任何决策 artifact 声明"M2 被接受/拒绝、理由为何、基于哪些证据"**；m3 D002 是"选型"非"接受修订"；DecisionLog 只有 invalidate（superseded by new selection）语义，无 accept/reject。
- **Expected behavior**：修订环应有决策门：M2 验证通过 + 比较通过 → Accept（记录理由+证据）；否则 Reject（可回退 M1）。
- **Why it matters**：核心原则最后环节缺失；"接受"被隐式等同于"验证通过"，两者并不等价（验证通过不代表优于 M1）。
- **Evidence**：p1-vs001 registry 唯一 decision=D001（Revision Request）；vs001_run registry 唯一 decision=D001（方法选型）；均无 accept/reject。
- **Reproduction**：查询任何 registry 中"accept/reject"kind 的 decision → 无。
- **Proposed fix**：新增 `kind="revision_acceptance"` 决策（参照 E-009 复用比较管道），字段：revision_of、decision=accept|reject、based_on=[VR1, VR2, comparison]、reasoning。
- **Regression risk**：低。
- **Test required**：单测"accept 决策必须引用 comparison 证据，否则拒绝"。

---

### E-011 — Re-execution 与 Replay 为真实实现（正面确认）

- **Severity**：LOW（记录正面事实，防误判）
- **File**：`core/runtime/execution/codegen.py`、`core/runtime/execution/replay.py`、`core/runtime/execution/adapters.py`
- **Function-Symbol**：`execute_code` / `replay_execution` / `LocalPythonAdapter`
- **Line**：codegen.py（execute_code）；replay.py（replay_execution）；vs001_driver.py:126-127
- **Observed behavior**：M1/M2 均经真实 subprocess（LocalPythonAdapter）执行，退出码/输出为真实数值；replay_report.json 2 项 `outputs_match=True, deviation=[]`；e2e `test_07` 从磁盘重建并重放一致。
- **Expected behavior**：符合（真实重执行+重放）。
- **Why it matters**：证明链的"重执行"与"可重放"两环节是真实的，问题集中在诊断/提案/比较/决策。
- **Evidence**：p1-vs001/replay_report.json；tests/integration/test_p1_vs001_e2e.py:167-194。
- **Reproduction**：`py -3.12 tests -k p1_vs001`（只读运行测试）或重跑 runner --stage replay。
- **Proposed fix**：无。
- **Regression risk**：无。
- **Test required**：已有。

---

### E-012 — `replay.py` 仅支持执行级重放，不支持修订链重放

- **Severity**：MEDIUM（"可重放"不等于"修订链可重放"）
- **File**：`core/tools/replay.py`、`core/runtime/execution/replay.py`
- **Function-Symbol**：`main`（verify/list/diff）
- **Line**：replay.py:25-67
- **Observed behavior**：CLI 支持 `verify`（确定性重放单次运行）、`list`、`diff <A> <B>`（两次运行逐字段差异+归因）；**无任何"重放 M1→M2 修订链"或"对比两个修订"的概念**；`diff` 是运行级 diff，不是修订级比较。
- **Expected behavior**：若声称"修订可重放"，应支持按 revision 谱系重放（M1 链 + M2 链）并输出修订级对比。
- **Why it matters**：PROGRESS 声称"可重放"，实际能力是执行级；文档表述易误导。
- **Evidence**：core/tools/replay.py:3-9（用法仅 verify/list/diff）；无 revision 参数。
- **Reproduction**：`py -3.12 core/tools/replay.py <p1-vs001> list` → 仅运行记录。
- **Proposed fix**：文档明示"执行级重放"；或在 replay 增加 `--revision <m2_mir>` 沿 revision_of 回溯重放。
- **Regression risk**：低。
- **Test required**：可选。

---

### E-013 — PROGRESS 文档"真实闭环"表述过强，与其自述遗留缺口并存

- **Severity**：MEDIUM（声称与证据的差距）
- **File**：`research/P15/PROGRESS-P1-VS001-2026-09-09.md`
- **Function-Symbol**：里程碑/遗留缺口
- **Line**：6（「真实闭环」）、36-37（「遗留缺口…自动 Revision」）
- **Observed behavior**：文档第 6 行宣称「第一次完成『模型构造—运行—验证—失败—修正—再运行』真实闭环」；第 36-37 行又自述「自动 Revision」未实现、RevisionRequest 由 runner 构造。两者并存：**"闭环"成立的范围是"执行-失败-谱系-重执行-验证"，不包含自动诊断/自动修订**。
- **Expected behavior**：文档应区分"谱系记录闭环（REAL）"与"自动修订闭环（GAP）"，避免将外部人工构造的 M2 描述为系统闭环。
- **Why it matters**：本审计的核心问题正是"是否可声称存在 Model Revision Loop"；文档表述是声称源头。
- **Evidence**：PROGRESS 第 6 行 vs 36-37 行；E-003~E-010 各发现。
- **Reproduction**：通读 PROGRESS 全文即可见。
- **Proposed fix**：修订 PROGRESS 表述为「谱系+重执行+验证闭环 REAL；自动诊断/提案/比较/接受决策 GAP（外部 Model Constructor 驱动）」。
- **Regression risk**：无（文档）。
- **Test required**：无（文档修订）。

---

## 6. 对九个必答问题的直接回答

| # | 问题 | 回答 |
|---|---|---|
| 1 | 系统中是否存在真实的 revision_of 关系？在哪些数据结构中？ | **是**。Evidence Graph 边（`MIR003 -revision_of-> MIR002` 等，evidence_graph.py:51 定义；p1-vs001/vs001_run 落盘实证）；artifact data 中的 `data["revision_of"]`（handlers.py:191）；p1-vs001 的 D001 provenance。生命周期无 revision 字段。 |
| 2 | 执行失败后，系统能否自动诊断失败原因？ | **不能**。engine `_handle_failure` 只 retry→rollback/blocked（engine.py:218-231）；"诊断"是 p1-vs001 runner 硬编码字符串（E-003/E-004）。 |
| 3 | Revision Proposal 是否基于失败证据？ | **部分**。`failed_checks` 来自真实 VR（E-004），但 diagnosis/corrective_action 为手写文本；M2 本体为预写 fixture/文件，无生成机制（E-005）。 |
| 4 | M2 是否通过 revision_of 边链接到 M1？ | **是（边真实）**。p1-vs001 与 vs001_run 均有 `new -revision_of-> old` 边；但 runtime 路径不置旧 MIR superseded（E-007），supersedes 方向两路径相反（E-002）。 |
| 5 | M2 是否真实重新执行（新的 execution_result）？ | **是**。EXEC003/EXEC002 为真实 subprocess 新执行（E-011）。 |
| 6 | M1/M2 比较是否基于真实指标？ | **修订路径：否（无比较）**；候选竞技场路径（m3）：是（constraint_violation_max 等机械比较）但未接线修订环（E-008/E-009）。 |
| 7 | Accept/Reject 决策是否记录理由？ | **否**。无 accept/reject 决策类型/产物（E-010）。 |
| 8 | Evidence Graph 中是否有 M2 --revision_of--> M1 边？ | **是**。p1-vs001：`MIR003 -revision_of-> MIR002`；vs001_run：`MIR002 -revision_of-> MIR001`。 |
| 9 | 若无 failure evidence / revision reason / changed components / re-execution / comparison，则不得声称存在 Model Revision Loop | **按此原则，本系统不得声称存在完整 Model Revision Loop**：failure evidence=REAL，revision reason=部分（手写），changed components=GAP，re-execution=REAL，comparison=GAP。 |

---

## 7. 结论与建议优先级

**结论**：P1-VS-001 实证了**真实的失败、真实的重执行、真实的验证、真实的谱系边、真实的重放**；
但**失败诊断、修订提案、M1/M2 比较、接受/拒绝**四个环节缺失或仅由实验脚本手工构造。
按审计核心原则，当前状态**不构成 Model Revision Loop**，应表述为：
**「外部 Model Constructor 驱动的 Model Lineage Recording + Re-execution 闭环（REAL），自动 Model Revision Loop（GAP）」**。

**修复优先级**（与 P1 遗留项 C6-C10 对齐）：
1. **P0**：统一 `supersedes` 方向并接通生命周期（E-002 + E-007）——否则谱系语义自相矛盾。
2. **P0**：修订链末尾接比较 + Accept/Reject 决策（E-008 + E-010 + E-009 复用 m3 比较管道）——补上"为什么 M2 更好"的可查询答案。
3. **P1**：诊断规则化（E-004）+ 修订内容来源显式化（E-005）+ `changed_components` 结构化（E-006）。
4. **P1**：引擎失败处理接诊断钩子（E-003）。
5. **P2**：文档表述修正（E-013）、replay 修订链能力（E-012）、revision 边消费方（E-001）。

---

*本报告由 Agent E 只读审计生成，未修改仓库任何代码/测试/配置。*
