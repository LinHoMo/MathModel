# Agent D — 独立证据/验证审计报告（只读）

- **审计官**: Agent D（独立证据/验证审计官，只读，未修改任何代码/测试/配置）
- **仓库**: `C:\Users\Lin\Desktop\Programs\MathModel`
- **日期**: 2026-09-09
- **审计链**: Execution → Evidence → Claim → Validation → Gate → Decision
- **方法**: 逐文件阅读 + 全局引用/符号追踪 + 空壳模式搜索（`return {"valid": True}` / `return True` / 占位符 / default PASS）

---

## 1. 审计范围摘要

追踪以下文件的真实执行路径（是否真实写入、是否真实计算、是否真实传播）：

| 模块 | 文件 | 结论 |
|---|---|---|
| Evidence Graph | `core/runtime/graph/evidence_graph.py` | 真实图存储 + 类型化边 + 失效传播 + 完整性检查；但边结构极简 |
| Evidence Gate | `core/validators/evidence/evidence_gate.py` | **纯结构门禁（边/生命周期/标签），零数值计算**（自认） |
| Validation 分层 | `core/validators/modules/*`（21 文件） | **死代码**：未被 runtime 导入/调用；仅被 `validate.py` 以"类名字符串存在性"检查 |
| Claim | `core/runtime/execution/handlers.py:1219-1227` | **显式占位符** `"{qid} 结论"`，`placeholder: True`，无任何后续填充逻辑 |
| Decision | `core/runtime/decisions/log.py` + `handlers.py` do_model_selection_decision | 真实基于 VR 数值指标选型，记录 reasoning/confidence/evidence_ids |
| handlers.py | `core/runtime/execution/handlers.py`（1360+ 行） | 真实执行（subprocess）、真实数值验证（VR）、真实反馈环；但 claim/experiment 链存在占位与"未执行"路径 |
| quality | `core/validators/quality/*` | 真实确定性计算（7 维 findings 聚合，非黑箱分数） |

## 2. 发现计数

| Severity | 数量 | 编号 |
|---|---|---|
| Critical | 2 | D-001, D-002 |
| High | 3 | D-003, D-004, D-005 |
| Medium | 4 | D-006, D-007, D-008, D-009 |
| Info | 2 | D-010, D-011 |
| **合计** | **11** | |

## 3. 证据链逐环节状态

```
Execution ──▶ Evidence ──▶ Claim ──▶ Validation ──▶ Gate ──▶ Decision
   REAL           PARTIAL      PLACEHOLDER     REAL*      STRUCTURAL    REAL
```

- **Execution**: REAL。`LocalPythonAdapter` 真实 subprocess 执行，产出完整 `ExecutionResultData`（execution_id/model_id/status/outputs/stdout/stderr/returncode/duration_ms/code_hash/environment_hash/started_at/finished_at/provenance/code/environment_manifest）。`handlers.py:376-441`。
- **Evidence**: PARTIAL。无独立 Evidence 实体；"证据" = Registry artifact + Graph 类型化边 `{from, relation, to, at}`。EXEC artifact 层数据完整，但图边层**不携带** code_hash/output/environment（仅时间戳 `at`）。且 Agent handler 可直接创建关系（不强制 execution substrate）。
- **Claim**: **PLACEHOLDER**。`handlers.py:1219-1227` 创建 claim 时 `title/statement = "{qid} 结论"`，`claim_type="comparative"` 硬编码，`execution_status="not_executed"`，`placeholder=True`。**全仓无任何代码填充真实结论文本**。占位符经 director.py:73 → narrative_ir → projection.py:54 流入论文大纲"结果与分析"。
- **Validation**: REAL（但仅两条真实路径：`run_numeric_validation`/`run_checks` VR 框架 + fidelity 映射；21 个 `modules/*` 分层 validator 为死代码）。
- **Gate**: **STRUCTURAL ONLY**。E1–E8 全为边/生命周期/标签检查，零数值检查（代码自认："evidence_gate 只查边不查数值"，handlers.py:495、validation.py:193）。
- **Decision**: REAL（候选模式下）。基于 VR 指标（mathematical_valid / constraint_violation_max / execution_valid）排名，写 reasoning 含具体数值，confidence 计算，evidence_ids 指向 VR artifact；镜像写 DecisionLog。非候选模式不产 decision。

## 4. Validation 分层真实执行矩阵

| 层 | 声称能力 | 实际执行内容 | 判定 | 证据 |
|---|---|---|---|---|
| L0 Structural | 结构完整性 | EvidenceGate E1-E8（边/生命周期/tags）、Graph integrity_check、Registry lifecycle。**但** not_executed 结果可过、占位 claim 可过 | **GAP** | evidence_gate.py:87-181 |
| L1 Schema | jsonschema 实例校验 | `model_ir.validate_model_ir`（18 字段/类型/id 零依赖校验，真）；`validate.py check_schemas_valid` 仅 `json.loads`（JSON 语法，非实例校验）；schema 注释自曝"历史 register 从不校验" | **GAP** | model_ir.py:176-236; validate.py:160-175; model_ir.schema.json |
| L2 Mathematical | equation consistency / dimensional consistency | `formula_checker.py`（括号配对/LaTeX 语法/常见错误正则）**存在但未接线（死代码）**；无任何 equation_consistency / dimensional_consistency 真实计算 | **FAKE**（接线层面） | formula_checker.py; 无 import 命中 |
| L3 Computational | numerical stability / solver convergence | `run_numeric_validation` 真算 constraint_violation_max / domain / robustness，但**硬编码单一问题**（pair_distances/head_speeds/positions 键名），非通用层；`contract_checker/invariant_tracker/stage_gate` 框架存在但未接线 | **GAP** | validation.py:180-291 |
| L4 Empirical | ground truth / sensitivity / residual / error | `run_numeric_validation` 的 objective_sane 用 `expected ± tolerance` 比对（单问题硬编码）；`cross_model_checker/consistency_checker` 存在但未接线；sensitivity/baseline 仅以 **tags 检索**（evidence_gate E8），不计算 | **GAP** | validation.py:235-247; evidence_gate.py:167-173 |

> 结论：**没有任何一级是完整 REAL**。L0/L1/L3/L4 为 GAP（有真实组件但关键能力缺失或硬编码），L2 在接线层面为 FAKE（模块存在、有实现、但整个管线从不调用）。

---

## 5. Findings

### D-001 — Critical — evidence_gate 是纯结构门禁，零数值/真实性检查

- **File**: `core/validators/evidence/evidence_gate.py`
- **Function-Symbol**: `evaluate(registry, graph, min_coverage)`（L87-181）
- **Line**: 87-181（E1 99-102, E2 104-109, E3 111-130, E4 140-148, E5 150-158, E6 124-138, E7 160-165, E8 167-173, verdict 175-181）
- **Observed behavior**: 全部 8 项检查只查询图边存在性（supports/produces）、artifact 生命周期状态（invalidated/superseded/draft/invalidation）、tags（sensitivity/baseline）与覆盖率比率。**无任何数值计算**：不校验 execution_result 的 outputs 是否非空、不校验 code_hash、不校验结果值是否真实、不做 ground truth 比对、不计算 residual/error。仓库自身承认这一点：`handlers.py:495` 与 `validation.py:193` 注释"evidence_gate 只查边不查数值"。
- **Expected behavior**: 名为"证据门禁"的准入门禁应当校验证据的**数值真实性**（outputs 存在且非空、execution status==success、可溯源到 code_hash），而不仅是图结构。
- **Why it matters**: "证据门禁通过"被当作"有真实证据"的准入信号（evidence.yaml: evidence_gate 是论文投影前准入门禁）。一条 result 为 `not_executed`（无任何数值）的链，只要边存在、无 draft/终态、带 tag，即可 PASS——门禁无法区分"真跑过"与"没跑过"。
- **Evidence**: E4 只检查 `produces` 边（140-148）；E6 只检查 lifecycle `draft`（124-134），而 `not_executed` 是 data.status 不是 lifecycle 状态（lifecycle.py:21-22 无该状态），因此未执行结果不触发 E6；E8 只检索 tags（167-173）。
- **Reproduction**: 构造 experiment→result（data.status="not_executed"，activate=True）→claim supports 边，result 带 sensitivity/baseline tags，无 EXEC artifact → `evaluate()` 返回 PASS。
- **Proposed fix**: 增加数值真实性检查：EXEC artifact 必须存在且 `status=="success"`、outputs 非空；或 result.data.status != "not_executed" 时 E4/E2 应降级为 fail/weak；把"执行状态"纳入生命周期或门禁语义。
- **Regression risk**: 中。默认 runtime 路径大量 result 为 not_executed（handlers.py:1081-1082），加严会使默认流程门禁 FAIL → 反馈环频繁触发，需同步外部 executor 回填路径。
- **Test required**: 新增门禁单测：not_executed 链不得 PASS；EXEC 缺失不得 PASS。

---

### D-002 — Critical — Claim 是显式占位符 `"{qid} 结论"`，无任何真实结论生成

- **File**: `core/runtime/execution/handlers.py`
- **Function-Symbol**: `do_evidence_build`（L1199-1235）
- **Line**: 1219-1227
- **Observed behavior**: claim 创建时 `title=f"{qid} 结论"`、`data={"statement": f"{qid} 结论", "claim_type": "comparative", "experiment_refs": [results[-1]], "literature_refs": [], "execution_status": "not_executed", "placeholder": True}`。**`placeholder: True` 被显式标记**；全仓搜索无任何代码把 statement 替换为真实结论。claim_type 硬编码 `"comparative"`（无基线对比时也称比较型结论）。
- **Expected behavior**: claim 应当是"这个结论到底是谁产生的"的可溯源陈述，statement 应包含从 result 数值/证据推导出的具体结论（如"冲突率随人兽重叠度上升"），并带 provenance 指向具体 EXEC/VR。
- **Why it matters**: 占位符 claim 经 `director.py:73`（`statement=claim.data.get("statement") or claim.title`）流入 StoryArc → `narrative_ir.py:275/288`（findings statement 拼接）→ `projection.py:54`（论文大纲"结果与分析"节 statement）→ `do_paper_sections`（handlers.py:1337-1354）。**论文结论章节的机器可读大纲由 "{qid} 结论" 占位文本投影而成**。
- **Evidence**: `claim_quality`（evaluators.py:331）只检查 statement 非空——`"{qid} 结论"` 非空，**占位符通过 claim 质量检查**；Evidence Gate E2 只要求 supports 边存在，不检查 statement 内容。
- **Reproduction**: 运行 V3 管线任一 Question → `do_evidence_build` → claim 的 data.statement == "Q1 结论"。
- **Proposed fix**: (1) 占位 claim 不得标记为 supported/satisfy E2，需在真实实验回填后由合成层生成结论文本；(2) claim_quality 增加占位符词检测（如 statement 形如 `.*结论$` 且 == title 时判 weak/fail）；(3) 结论生成应读取 result 数值 + EXEC outputs 由确定性模板或 LLM 合成并写回。
- **Regression risk**: 高。当前整条论文投影依赖该占位文本；改为空会触发 narrative 空弧 → gate E2 FAIL，需要结论合成器先落地。
- **Test required**: claim 创建单测断言 placeholder 标志；claim_quality 单测：占位 statement 必须被标记。

---

### D-003 — High — `core/validators/modules/*` 21 个分层 validator 是死代码；validate.py 只做"类名存在"检查

- **File**: `core/tools/validate.py`（L687-892）+ `core/validators/modules/*`
- **Function-Symbol**: `check_symbol_registry` / `check_assumption_validator` / `check_type_system` / `check_formula_checker` / `check_output_validator` / `check_invariant_tracker` / `check_contract_checker` / `check_stage_gate` / `check_symbolic_verifier` / `check_cross_model_checker` / `check_consistency_checker` / `check_trust_domain` / `check_permission_guard` / `check_incremental_checker` / `check_hash_chain` / `check_error_attribution` / `check_rule_iterator`
- **Line**: validate.py:687-892（每个函数体模式相同）
- **Observed behavior**: 每个 check 读取对应 .py 文件后执行 `if "class X" not in content: return False`——只验证**源文件包含类名这一字符串**，从不导入、实例化或执行这些 validator。全局搜索确认：`validators.modules` 及所有 21 个类名在 `core/` 下**零 import 命中**（仅自身 `if __name__ == "__main__"` 自引用与 validate.py 字符串检查）。tests 也仅引用 evidence_gate 与 quality。
- **Expected behavior**: "六层防御验证"（validate.py 声称的 L1-L6）应真实执行这些 validator 对实际产物的校验。
- **Why it matters**: 57 项项目级校验中包含约 17 项**外观存在性检查**，全部恒定 PASS（类名必然存在）。这让"L1-L6 分层验证"成为装饰性审计，掩盖了公式检查、符号验证、类型系统、契约校验等能力**从未在管线中运行**的事实。AGENTS.md 宣称的"L1–L6 门禁"与 `validate.py` 输出对读者产生虚假保障。
- **Evidence**: `rg 'from validators.modules|import validators.modules|AssumptionValidator|...'` 仅在模块自身与 validate.py 字符串检查中命中；tests 目录仅 `from validators.evidence import evidence_gate` 与 `from validators.quality import ResearchQuality`。
- **Reproduction**: `py -3.12 core/tools/validate.py` 输出 "L2 公式检查器 PASS" 而公式检查器从未被调用。
- **Proposed fix**: (1) 要么把 modules 接入管线（在 DAG 相应节点真实调用），要么 (2) 把 validate.py 的这些检查改为"导入并冒烟执行"（`importlib.import_module` + 至少一次实例化/单测调用），并删除纯字符串检查；(3) 在 STATUS.md/README 中如实声明 modules 的接线状态。
- **Regression risk**: 低（修复是加固非行为变更）；若接入管线则高，需先补 tests。
- **Test required**: 断言每个 modules 模块可被 import 且核心方法可执行；validate.py 检查不得以字符串存在性代替执行。

---

### D-004 — High — 门禁 WEAK 判定也被 handler 判为 FAIL；未执行链可结构通过

- **File**: `core/runtime/execution/handlers.py` + `core/validators/evidence/evidence_gate.py`
- **Function-Symbol**: `do_evidence_gate`（handlers.py L1237-1247）、`GateReport.passed`（evidence_gate.py L62-63）
- **Line**: handlers.py:1244-1247; evidence_gate.py:62-63
- **Observed behavior**: `GateReport.passed()` 返回 `verdict == PASS`。`do_evidence_gate` 中 `if report.passed: PASS else: FAIL`。因此 **WEAK 也走 FAIL → on_fail→experiment_design 反馈环**，与 evidence_gate.py 文档（L15 "任一 weak → WEAK"，L25-26 WEAK_VERDICT）声明的"WEAK 为警告性"语义矛盾。同时默认 runtime 不执行数值计算（handlers.py:1081-1082 注释明示"确定性 runtime 不执行数值计算；真实结果须由外部 executor 回填"），result 停留 `not_executed`，而 E6 只查 lifecycle draft 不查 data.status，E8 需要 sensitivity/baseline tags（无 plan 声明则缺）→ 门禁极易 WEAK → 判 FAIL → 反馈环 → 重试耗尽后 blocked。
- **Expected behavior**: WEAK 应按文档语义为 advisory（不阻断），或文档应如实声明"WEAK 也阻断"；门禁应区分"未执行"与"已执行"。
- **Why it matters**: 判定语义与文档/契约不一致，且 WEAK 阻断会让默认路径陷入反馈环或 blocked，可能被解读为"门禁严格"而实为结构门禁在空转。
- **Evidence**: evidence_gate.py:15 文档 "任一 weak → WEAK；否则 PASS"；handlers.py:1244 `if report.passed` 仅 PASS 放行。
- **Reproduction**: 构造 E8 触发（无 sensitivity/baseline tags）→ verdict WEAK → handler 返回 NodeResult(FAIL) → engine 走 on_fail。
- **Proposed fix**: 明确 WEAK 语义（放行 + advisory 记录，或文档改声明阻断）；将"结果是否已执行"纳入 E4/E6 检查。
- **Regression risk**: 中。
- **Test required**: gate WEAK 场景的 handler 级测试，断言语义与文档一致。

---

### D-005 — High — `_clear_revalidation_marks`：重建即清除复验标记，"复验即复验通过"

- **File**: `core/runtime/execution/handlers.py`
- **Function-Symbol**: `_clear_revalidation_marks`（L1156-1169）
- **Line**: 1156-1169（注释 L1157-1161）
- **Observed behavior**: 链重建/复验时，把该问题全部活跃产物上的 `requires_revalidation`/dirty 传播标记**直接清除**（`a.clear_invalidation()`），注释自述"链重建/复验即复验通过"。这是 bookkeeping 操作，非真实复验。
- **Expected behavior**: 复验标记应由实际重新验证（重跑 gate/VR/quality）后清除；重建链条不应自动视为"复验通过"。
- **Why it matters**: Evidence Gate E6 的 invalidation 分支（evidence_gate.py:136-138）因此对重建链永不触发，失效传播的"需复查"语义被绕开。这是对"Evidence 必须回答谁产生"的不利操作：一个被清除标记的链在门禁看来无需复查。
- **Evidence**: 注释原文"E6 死循环：链重建/复验即复验通过——清除该问题活跃产物上的 requires_revalidation/dirty 传播标记"。
- **Reproduction**: 复验链 → 产物 invalidation 标记被清 → E6 invalidation 分支不触发。
- **Proposed fix**: 区分"重建"与"复验"：重建只允许从源头重跑并生成新产物（旧产物保持终态），不主动清标记；若确需清除，必须附真实复验记录（VR/重新 gate）。
- **Regression risk**: 中（该逻辑存在即为规避死循环，删除需先解决 E6 死循环根因）。
- **Test required**: 复验链单测：无真实验证不得清除 invalidation。

---

### D-006 — Medium — Evidence 并非只能由 execution substrate 创建

- **File**: `core/runtime/execution/handlers.py`
- **Function-Symbol**: `do_experiment`（L1011-1104）、`do_evidence_build`（L1199-1235）
- **Line**: 1081-1082, 1100, 1219-1230
- **Observed behavior**: `do_experiment` 由 **Agent handler** 直接创建 experiment/result/figure artifact 并写 E→R→F 关系；`do_evidence_build` 由 handler 直接写 `result -supports-> claim` 边。当无 execution_adapter 或无可执行 code 时，result 保持 `not_executed`，但 supports 边照写。adapters.py 文档宣称"Evidence 不是 Agent 写出来的，而是 execution substrate 产生的"，**实现与设计宣言不符**：handler 可直接创建证据关系，且不要求 EXEC 存在。
- **Expected behavior**: supports 边只能在真实执行（EXEC success）后由 substrate/验证层写；未执行结果不得支撑 claim。
- **Why it matters**: "这个结论到底是谁产生的"无法被图结构保证——一个从未运行的实验链可以支撑论文结论（结构上），provenance 断裂。
- **Evidence**: handlers.py:1100 `self._maybe_execute_experiment(...)` 在无 adapter 时静默返回（L1120-1121）；L1229-1230 supports 边无条件写入。
- **Reproduction**: 无 adapter 运行管线 → claim 有 supports 边、无 EXEC artifact → gate E2 通过。
- **Proposed fix**: supports 边的写入条件绑定 result.data.status=="success"（或 EXEC verified_by VR passed）；未执行链的 claim 标记 unsupported。
- **Regression risk**: 高（默认路径将大量 WEAK/FAIL，需外部 executor 回填成熟后落地）。
- **Test required**: 无 EXEC 时 claim 不得 supported。

---

### D-007 — Medium — Evidence Graph 边不携带 code_hash/output/environment，无法回答"哪个代码/环境产生此证据"

- **File**: `core/runtime/graph/evidence_graph.py`
- **Function-Symbol**: `add_relation`（L169+）、边结构 `{"from", "relation", "to", "at"}`
- **Line**: 33-57（RELATION_TYPES / EDGE_FIELDS）、169-190
- **Observed behavior**: 图边仅 `{from, relation, to, at}`。execution_result artifact 的 data 虽含 execution_id/code_hash/environment_hash/outputs/started_at/finished_at/provenance（adapters.py `ExecutionResultData.to_dict()`），但**图中没有任何字段把边与 code_hash/environment/outputs 关联**——边只有两端 artifact id。环境仅存 `environment_hash`，无 environment 描述。
- **Expected behavior**: 证据边（或关联的 EXEC artifact）应能回答"这个证据由哪段代码、哪个环境、在何时产生"。
- **Why it matters**: 审计问题 1 的答案：Evidence 对象无独立结构，图边层不含 execution_result_id/code_hash/output/environment——provenance 只在 artifact 层、且不强制。
- **Evidence**: evidence_graph.py:169-190 `add_relation` 仅存 ids + at；adapters.py ExecutionResultData 完整但仅为 EXEC artifact 内部数据。
- **Reproduction**: dump evidence_graph.json，任何边都不含 code_hash 字段。
- **Proposed fix**: 边可增加 `execution_ref`（指向 EXEC artifact id）；或门禁强制 claim 的证据闭包必须含 EXEC。
- **Regression risk**: 低。
- **Test required**: 图 schema 单测断言边可关联 EXEC。

---

### D-008 — Medium — 存在 `return {"valid": True}` 默认通过模式（空壳返回）

- **File**: `core/validators/modules/output_validator.py`、`type_system.py`、`contract_checker.py`
- **Function-Symbol**: `OutputValidator.validate_*`、`TypeSystem.validate_value`、`ContractChecker.check`（契约缺失分支）
- **Line**: output_validator.py:112, 115, 128; type_system.py:20; contract_checker.py:76
- **Observed behavior**: 未知输出类型 → `{"valid": True}`（output_validator.py:115 注释"未知类型默认通过"）；无 expected_keys 便利函数 → `{"valid": True, "issues": []}`（L128）；type None → valid True（type_system.py:20）；无契约定义 → `return True  # No contract defined, vacuously true`（contract_checker.py:76）。
- **Expected behavior**: 未知/未定义场景应 fail-closed 或显式 UNKNOWN，不应默认通过。
- **Why it matters**: 这些模块当前为死代码（D-003），一旦被接入管线，上述分支会让"未配置即通过"语义进入门禁，重现"validator 只是 return True"模式。
- **Evidence**: 全局搜索 `return {"valid": True}` 仅命中这 5 处。
- **Reproduction**: 调 `OutputValidator().validate(None, "unknown_type")` → valid True。
- **Proposed fix**: 改为 `{"valid": False, "reason": "unknown type/未配置"}` 或显式 `{"status": "UNKNOWN"}`；契约缺失时 fail-closed。
- **Regression risk**: 低（当前未接线）。
- **Test required**: 未知类型/空契约必须返回非通过。

---

### D-009 — Medium — claim_quality 无法拦截占位符；占位 statement 流入论文大纲

- **File**: `core/validators/quality/evaluators.py`、`core/runtime/writing/director.py`、`core/runtime/writing/projection.py`、`core/runtime/writing/narrative_ir.py`
- **Function-Symbol**: `claim_quality`（evaluators.py:331）、`ResearchDirector.build`（director.py:73）、`PaperProjection.project`（projection.py:54）、`build_narrative_ir`（narrative_ir.py:275/288）
- **Line**: evaluators.py:331; director.py:73; projection.py:54; narrative_ir.py:275,288
- **Observed behavior**: claim_quality 的 "What" 检查只要求 statement/title 非空——`"{qid} 结论"` 非空即过。director 用 `claim.data.get("statement") or claim.title` 作为 StoryArc.statement（占位文本），projection 把 arc.statement 直接写入论文大纲"结果与分析"节（projection.py:54），narrative_ir 把 finding statement 拼进结论文本（narrative_ir.py:275/288）。占位符**无拦截地**贯穿到论文投影。
- **Expected behavior**: 质量评估应检测占位符式 statement（如等于 title、形如"X 结论"、含 placeholder 标志）并判 weak/fail；占位 claim 不得进入 supported 叙事。
- **Why it matters**: 与 D-002 叠加：论文大纲的结论文本是占位符，而 quality/gate 均绿灯——"有证据支撑的结论"实际是"未执行的占位结论"。
- **Evidence**: evaluators.py:331 `if not (c.data.get("statement") or c.title or "").strip()`（占位符非空，不触发）；handlers.py:1227 显式 `"placeholder": True` 但无人消费该标志。
- **Reproduction**: 检查 claim.data.placeholder==True 的 claim 在 quality 报告中无任何 finding。
- **Proposed fix**: claim_quality 消费 `placeholder` 标志与 statement==title 启发式；director 对 placeholder claim 标记 unsupported。
- **Regression risk**: 中。
- **Test required**: 占位 claim 的质量 finding 单测。

---

### D-010 — Info — `run_numeric_validation` 是真实计算但硬编码单一问题

- **File**: `core/runtime/execution/validation.py`
- **Function-Symbol**: `run_numeric_validation`（L180-291）
- **Line**: 209-277
- **Observed behavior**: 该函数真实计算 constraint_violation_max（对 `outputs["pair_distances"]` 与 `spec.constraints[].reference` 的绝对差）、objective_sane（`outputs["head_speeds"]` 均值 vs expected±tol）、variable_domain_violation（`outputs["positions"]` 坐标域）、robustness（余量归一）。但**键名/结构硬编码**为单一基准问题（pair_distances/head_speeds/positions），非通用 L3/L4 层。通用层 `run_checks`（L104-168）只提供 output_field_exists/output_numeric/output_range/output_equals/output_key_exists，**无 equation consistency、无 dimensional consistency、无数值稳定性、无收敛性检查**。
- **Expected behavior**: L3 Computational 应提供通用 solver convergence / numerical stability 检查；L4 Empirical 应提供通用 ground truth 比对/残差计算。
- **Why it matters**: "数值验证真实存在"为真，但覆盖面极窄（单问题 schema + 字段存在性），不足以支撑 L3/L4 分层声称。
- **Evidence**: validation.py:209-277 全部基于 pair_distances/head_speeds/positions 键名。
- **Reproduction**: 用非该 schema 的输出调用 run_numeric_validation → constraints 空、objective 无 expected、domain 无 → 全部 trivially pass/vacuous。
- **Proposed fix**: 将数值验证泛化为 spec 驱动的通用检查（残差/稳定性/收敛由 spec 描述），保留该专用实现为基准用例。
- **Regression risk**: 中。
- **Test required**: 通用 spec 驱动的数值验证用例。

---

### D-011 — Info — Decision 链真实，但无 `supported_by` 边；非候选模式不产 decision

- **File**: `core/runtime/graph/evidence_graph.py`、`core/runtime/execution/handlers.py`
- **Function-Symbol**: `do_model_selection_decision`（handlers.py:640-740）
- **Line**: evidence_graph.py:46-47, 83-84; handlers.py:672-740
- **Observed behavior**: 决策引擎真实：候选模式下基于 VR 指标排名（`_rank_candidates`）、计算 confidence、写含具体数值的 reasoning（如 `chosen=X because VR.mathematical_valid=True; Y worse than X.constraint_violation_max=...`）、`evidence_ids` 指向 VR artifact、镜像写 DecisionLog；无证据时如实 `chosen=UNSELECTED, confidence=0`（L672-674）。图中 decision 用 `selects`（→model）与 `based_on`（→依据，传播规则 `(None,"reval")`：证据死→决策需复查）连接——**没有名为 `supported_by` 的边**。非候选（legacy 竞技场）模式下 do_model_selection_decision 不产出 decision artifact（L650-651 跳过）。
- **Expected behavior**: 审计问题 9 的答案：无 `supported_by` 边；`based_on` 承担相似语义。决策记录理由与依据为真（问题 8 答案：是）。
- **Why it matters**: 决策真实性是本链最健康的一环；但 `based_on` 只指向 VR artifact id，不指向具体 checks/数值，reasoning 为文本（不可机读复算）。
- **Evidence**: handlers.py:694-712; evidence_graph.py:46-47,83-84。
- **Proposed fix**: 将 reasoning 结构化（含每个候选的判据数值表），decision 边补充指向具体 VR check 的引用。
- **Regression risk**: 低。
- **Test required**: decision artifact 的 reasoning 可复算单测。

---

## 6. 审计问题逐条回答

1. **Evidence 对象的实际结构？** 无独立 Evidence 类。证据 = Registry artifact（EXEC/result/VR…）+ Graph 类型化边 `{from, relation, to, at}`。execution_result artifact 数据含 execution_id/code_hash/outputs/returncode/stderr/duration_ms/environment_hash/started_at/finished_at/provenance/code；图边层仅 from/relation/to/at，**不含** code_hash/output/environment（environment 只有 hash，无描述）。
2. **Evidence 是否只能由 execution substrate 创建？** 否。handler（Agent 代码）直接创建 execution_result artifact 与 supports/produces 等边；无 adapter 时 result 保持 not_executed 仍可支撑 claim（D-006）。
3. **Claim 是否有 provenance 指向具体 Evidence？** 有结构 provenance（depends_on=[results[-1]]、supports 边、experiment_refs），但 statement 是 `"{qid} 结论"` 占位符（`placeholder: True`），非由 Evidence 内容推导（D-002）。
4. **evidence_gate 到底校验了什么？是否有数值/真实性检查？** 仅校验：活跃 claim 存在（E1）、supports 边存在（E2）、链无终态（E3）、produces 边存在（E4/E5）、链无 draft/invalidation（E6）、覆盖率（E7）、sensitivity/baseline tags（E8）。**零数值/真实性检查**（D-001）。
5. **Validation 分层每级是否真实计算？** 见矩阵（§4）：L0 GAP（结构检查真实但放过未执行链/占位符）、L1 GAP（model_ir 零依赖校验真实；无 jsonschema 实例校验，历史自曝 register 从不校验）、L2 FAKE（formula_checker 未接线；无 equation/dimensional consistency 计算）、L3 GAP（run_numeric_validation 真实但硬编码单问题；无通用稳定性/收敛检查）、L4 GAP（objective_sane 单问题比对；sensitivity/baseline 仅 tags 检索不计算）。
6. **是否存在 validator 只 `return {"valid": True}`？** 是（5 处：output_validator 3 处、type_system 1 处、contract_checker vacuous pass 1 处，见 D-008）；当前均位于未接线的 modules 死代码中。
7. **Validation FAIL 是否真实传播到 Decision？** 是。gate/quality FAIL → handler 返回 NodeResult(FAIL) → engine `_handle_failure` 重试 → 耗尽走 on_fail 反馈环（experiment_design / evidence_build）或 blocked。无 default PASS 路径（engine.py:141-167 明确区分）。但 WEAK 也被判 FAIL（D-004），语义与文档矛盾。
8. **Decision 是否记录理由和依据？** 是。candidate 模式写 reasoning（含数值）、confidence、evidence_ids、alternatives/criteria，并镜像 DecisionLog（handlers.py:694-734）。
9. **Evidence Graph 中是否有 decision --supported_by--> evidence 边？** 否。relation 词表无 `supported_by`；decision 用 `based_on`（→evidence/依据，传播 `(None,"reval")`）与 `selects`（→model）。语义上"决策受证据约束"存在，但名称不同、且引用粒度到 VR artifact 而非具体 check/数值（D-011）。

---

## 7. 总体结论

证据链的**骨架真实**（执行、数值 VR、决策、反馈环、质量评估都是真代码、真计算），但**两端存在结构性缺口**：

- **上游**：Claim 是占位符（D-002），且占位符无拦截地流入论文投影；证据可由未执行的链产生（D-006）。
- **中游**：证据门禁是纯结构检查，无法回答"证据是否真实"（D-001）；21 个分层 validator 是死代码，"六层防御"名不副实（D-003）；复验标记可被重建清除（D-005）。
- **下游**：Decision 是真实且可追溯的（本链最健康环节）。

**最高优先级修复**：D-001（门禁数值真实性）、D-002（占位 claim 拦截与结论合成）、D-003（modules 接线或如实声明）。
