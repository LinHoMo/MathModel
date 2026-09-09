# Audit B — 模型构建链独立审计报告（Model Construction Chain Audit）

**审计官**：Agent B（独立模型构建审计官，只读）
**审计日期**：2026-09-09
**仓库**：`C:\Users\Lin\Desktop\Programs\MathModel`
**审计范围**：`Problem → Representation → Candidate Generation → Candidate Evaluation → Selection → MODEL_IR → Model Artifact` 全链逐环节验证（只读，未修改任何代码/测试/配置）
**验证方式**：源码精读 + 全仓 Grep + 真实项目产物（`projects/*/state/registry.json`、`evidence_graph.json`）实测 + 关键测试运行（`py -3.12 -m pytest`，20 passed）

---

## 一、审计范围摘要

追踪模型构建链每个环节的**实际数据结构、创建者、是否真实执行计算、决策是否可追溯**。重点验证三项怀疑：
1. `selection.py` 约 60 行存在 `chosen = recs[0]` 硬编码 —— **已确认（精确行 60）**
2. `handlers.py` 的 `do_model_construction` 只登记假设不产 MODEL_IR —— **已确认（函数实际在 891 行，非提示的 257-280 行；无外部注入时确实不产 MODEL_IR）**
3. MODEL_IR 只是方法卡名称包装 —— **不成立（结构上是完整 18 字段三层规范）；但默认生产路径从不实例化它（另一种形态的 GAP）**

**核心结论**：系统存在**两条并行的建模链**——
- **默认生产链**（`core/tools/orchestrator.py --execute` 实际走的路径）：Selection = `recs[0]` 硬编码（无证据），Candidate Evaluation 完全不存在，MODEL_IR 从不生成，Model Artifact 仅为 `{card_id, family, shortlist}` 薄壳，实验结果为 `not_executed` 占位。
- **P1-M3 候选竞技场链**（仅由 `research/P15/m3_run/m3_driver.py` / `vs001_run/vs001_driver.py` 及测试注入外部 fixtures 触发）：多候选真实执行 + 数值验证 + 机械排序选型，链上每个环节 REAL。**但该链在生产 orchestrator 中零接线，无任何生产代码注入 `external_candidates`。**

---

## 二、发现计数（按 severity）

| Severity | 数量 | Finding ID |
|---|---|---|
| Critical | 2 | B-001, B-002 |
| High | 3 | B-003, B-004, B-005 |
| Medium | 7 | B-006, B-007, B-008, B-009, B-010, B-011, B-012 |
| **合计** | **12** | |

---

## 三、模型构建链逐环节状态（REAL / GAP / FAKE）

| 环节 | 状态 | 一句话结论 |
|---|---|---|
| Problem → Representation | **GAP** | V3 运行时只建 `features` 粗画像 + 纯标题 Question artifact；从不读题面/`question_spec.json`；结构化表示仅在 legacy V2 路径存在且未接入 V3 |
| Candidate Generation | **REAL（有条件）** | `CandidateArena.generate_candidates` 真实生成 2–4 个组合有实质差异的候选；但生产路径生成后即弃（仅 top-1 用于实验规划），且候选分数是启发式 |
| Candidate Evaluation | **FAKE（默认）/ REAL（候选模式）** | 默认路径无任何评估（无 code/exec/VR）；候选模式有真实数值验证（`run_numeric_validation`） |
| Selection | **FAKE（默认）/ REAL（候选模式）** | 默认 `chosen=recs[0]` 硬编码、无证据；候选模式基于 VR 机械指标排序、decision 带 evidence_ids/reasoning |
| MODEL_IR | **REAL（结构）/ GAP（实例化）** | 18 字段三层 dataclass + schema 完整；但生产默认运行 MIR=0（实测三个真实项目均为 0 个 MIR） |
| Model Artifact | **GAP** | V3 model artifact 是薄壳（`{card_id, family, shortlist}`），provenance 空；V2 `model_artifact.schema.json` 全仓无强制执行点 |

---

## 四、必须回答的 8 个问题（附证据）

### Q1. Problem Representation 的实际数据结构是什么？谁创建它？
- **V3 运行时**：`features` dict（`core/runtime/execution/handlers.py:55-65`，六键画像：`problem_types/has_data/sample_size/problem_title/...`）+ Question artifact（`core/runtime/execution/session.py:78-83`，`title=q` 纯标签，无题面内容）。Problem artifact 由 `do_problem_analysis`（`handlers.py:778-788`）以 `title=self.features.get("problem_title", "赛题")` 创建。
- **创建者**：orchestrator 加载 `problem_features.json`（`core/tools/orchestrator.py:349-392`）；缺失时回退 `_LEGACY` 默认画像并打 `_features_source=legacy_default` 标记（`handlers.py:83-85`）。
- **结构化表示（V2 legacy）**：`core/schemas/question_spec.schema.json`（metadata/background/problems[输入输出变量]/constraints/data/delivery，146 行完整契约），由 legacy `problem-parser` agent（LLM）产出 `work/question_spec.json`；`core/validators/modules/problem_spec_parser.py` 提供确定性解析器。
- **GAP**：V3 运行时**从不读取** `question_spec.json` / `inputs/`（全仓 Grep `core/runtime` 仅 domain 文档字符串提及，无代码引用）。问题本体从未进入 V3 认知管线。

### Q2. Candidate Generation 是否真的能生成 ≥2 个不同的候选模型？候选之间是否有实质差异？
- **能**：`CandidateArena.generate_candidates`（`core/runtime/modeling/candidates.py:177-302`）生成最多 4 个候选：`CAxxx-A baseline`（单方法）/ `CAxxx-B improved`（主方法+推荐增强+兼容方法）/ `CAxxx-C hybrid`（top1×top2 组合）/ `CAxxx-D innovation`（主方法+创新模式）。composition 有实质差异。
- **但**：候选 `score` 全部由检索分派生 + 硬编码增量：baseline `score=main.score`（197 行）、improved `score=main.score + (2 if boost else 0)`（220 行）、hybrid `score=max(main.score, alt.score) - 2`（241 行）、innovation `score=main.score + novelty 加分 + fit 调整 - cost 扣分`（265-271 行）。**分数不是任何模型执行/评估的结果。**
- 生产路径下候选生成后仅 `shared[qid]["candidates"]` 缓存，被 `do_experiment_design` 取 `cands[0]`（`handlers.py:966`）做实验规划，**无评估、无选型消费**。

### Q3. Candidate Evaluation 是否执行了真实计算？还是只返回默认分数？
- **默认路径：无评估**。`do_code_generation`/`do_model_execution`/`do_model_validation` 在无外部注入时均为 no-op（`handlers.py:512-561`，`generate_code` 无注入返回 `[]`）。
- **候选模式：真实计算**。`execute_code`（`handlers.py:376-441`）用 `LocalPythonAdapter` 真 subprocess 执行（status 只来自真实退出码）；`_register_vr`（`handlers.py:457-489`）调 `run_numeric_validation`（`core/runtime/execution/validation.py`）对真实 outputs 计算 `mathematical_valid / constraint_violation_max / objective_value / variable_domain_violation` 等。测试实测：坏候选 VR 判 `mathematical_valid=False, constraint_violation_max=0.275`（`tests/integration/test_p1_m3_competition.py:135-148`）。
- **结论**：评估逻辑 REAL 但仅存在于候选模式；默认分数（`candidates.py` 的 score）是启发式，非计算。

### Q4. Selection 决策是否可追溯？系统能否回答"为什么选这个模型而不是另外两个"？
- **默认路径：不可追溯（无证据）**。`MethodArena.select`（`selection.py:46-121`）`chosen=recs[0].card.card_id`（**60 行硬编码**），confidence 由检索分换算 `min(0.5+0.1*top.score, 0.95)`（100 行）。"为什么选 A 不选 B/C"只能回答"因为 A 检索得分最高"，**不是证据**。落选理由仅存 `alternatives`（`[r.card.card_id（score=..）...]`，92-95 行）。
- **候选模式：可追溯**。`do_model_selection_decision`（`handlers.py:639-740`）产出 decision artifact，含 `alternatives/criteria/evidence_ids/chosen/confidence/reasoning/ranked/candidate_vr`；reasoning 引用真实 VR id 与数值（如 `"chosen=MIR002 because VR002.mathematical_valid=True"`，682-693 行）。测试断言 `d["chosen"] == min(cv, key=cv.get)`（`test_p1_m3_competition.py:109`）。
- **但**：候选模式的 selection 可追溯性存在于 decision artifact 的 data 字段，**没有落成 typed graph 边**（见 B-004）。

### Q5. MODEL_IR 是否包含 equations、mechanism、solver、validation_plan 等建模必需字段？
- **包含**：`ModelIR` dataclass（`core/runtime/modeling/model_ir.py:70-99`）18 个 required 字段，三层视图：L1 `problem_binding/assumptions/variables/parameters`、L2 `objectives/constraints/mechanisms/equations/dependencies`、L3 `solvers/experiments/validations`，外加 `claims/model_graph/modeling_trace`。
- schema 嵌套契约完整：`equations[]` 需 `latex/type/variables_refs/derivation_trace/sub_question_binding`（`core/schemas/v3/model/model_ir.schema.json:418-480`），`solvers[]` 需 `method/implementation_ref`（488-529 行），`validations[]` 需 `type/method/targets_refs`（605-662 行）。
- **但无 `validation_plan` 字段**（runtime MODEL_IR 用 `validations[]`；K002 的 `validation_plan`（limit_tests/multi_seed/sensitivity/ambiguity_handling/claim_evidence_map）是 research 层独立概念，见 `research/P15/scripts/k002_register.py:48-57`）。
- **且**：默认生产路径**从不实例化 MODEL_IR**（见 B-002）；唯一真实实例是 research fixtures（`research/P15/vs001_run/vs001_fixtures.py`，含 latex 方程与可执行代码）与测试。

### Q6. MODEL_IR → Code 的映射是否存在？（code_mapping 字段）
- **`code_mapping` 字段不存在**：全仓 Grep `code_mapping` 0 匹配（见 B-003）。
- 映射的实际载体：
  1. Graph 边 `implemented_by`（`model_ir → code`，`evidence_graph.py:38`）；
  2. schema 层 `solvers[].implementation_ref`（字符串引用，如 fixture 中 `"CODE001"`，`vs001_fixtures.py:136`）；
  3. `codegen.py` 的 `model_id/solver_id/output_mapping`（`core/runtime/execution/codegen.py:44-76`，由外部 agent 声明）。
- **注意**：`implementation_ref` 是自由字符串，runtime **不校验**它是否指向真实 CODE artifact；且 codegen.py 明确"core 永久 LLM-free：本模块不生成代码"（`codegen.py:4-5`），即 **MODEL_IR→Code 没有自动生成，只有外部注入+登记**。

### Q7. Model Artifact 是否包含完整的 provenance（从 problem 到 model 的完整谱系）？
- **不包含**。V3 model artifact 的 `data` 仅 `{card_id, family, shortlist}`（`handlers.py:865-872`）或候选容器 `{card_id:"candidate_competition", shortlist, competition, selection_status}`（827-835 行）。`registry.create` 调用均未传 `provenance` 参数 → 真实项目中 provenance 为 `{}`/`None`（实测 `projects/v3-real-2024a-g7test-A/state/registry.json`：`M001 provenance={}`）。
- Artifact contract 虽有 `provenance` 字段（`artifact.py:53`），但默认空。谱系只能沿 graph 边隐式重建（`problem -motivates-> question -solved_by-> model`），不是 artifact 内嵌字段。
- V2 `model_artifact.schema.json`（P13-3C 冻结评分契约）要求 `problem_id/problem_interpretation/.../candidate_models(minItems=2)/selected_model/selection_reason(minLength=30)`，**也没有 provenance 字段**，且该 schema **全仓无强制执行点**（见 B-010）。

### Q8. Evidence Graph 中是否记录了 candidate --evaluated_by--> evidence 和 selected_model --selected_from--> candidate 边？
- **否**。`evaluated_by` 与 `selected_from` 在 `core/runtime/graph/evidence_graph.py:33-53` 的 `RELATION_TYPES` 中**均不存在**，全仓 Grep 0 匹配（见 B-004）。
- 实际存在的相关边：`verified_by`（EXEC→VR，50 行）、`selects`（decision→model，46 行）、`instantiates`（MIR→model，37 行）、`implemented_by`（model/MIR→code，38 行）、`executed_by`（code/result→EXEC，49 行）、`produces`（EXEC→result，42 行）。
- 候选评估证据挂在 VR artifact 上（`verified_by` 边），选型可追溯性挂在 decision artifact 的 data 字段（`alternatives/evidence_ids/reasoning`），**未实体化为候选→证据、选中模型→候选的 typed 边**。`_candidate_vr_table`（`handlers.py:570-594`）通过 `verified_by` 边 + `EXEC.data.model_id` 反查候选归属。

---

## 五、Findings 明细

### B-001 [Critical] 默认选型硬编码 `chosen = recs[0]`，无证据支撑
- **File**: `core/runtime/modeling/selection.py`
- **Function-Symbol**: `MethodArena.select`
- **Line**: 60（另见 88 行 `top = recs[0]`）
- **Observed behavior**: `outcome = SelectionOutcome(..., chosen=recs[0].card.card_id)` —— 直接取检索推荐第一名作为选中方法；confidence = `min(0.5 + 0.1 * top.score, 0.95)`（100 行）由检索分换算。
- **Expected behavior**: 选型应基于候选模型的实际评估证据（如数值验证结果），或至少声明"无证据、未选型"（候选模式已实现此语义：无 VR 证据时 `chosen="UNSELECTED", confidence=0.0`，`handlers.py:672-674`）。
- **Why it matters**: 生产默认路径的"为什么选这个模型"只能回答"检索得分最高"，不是模型质量的证据。与 AGENTS.md"Evidence decides whether the construction survives"哲学直接冲突。
- **Evidence**: `selection.py:60`；`handlers.py:848-849`（生产路径调用 `self.arena.select(qid, qf)` 后取 `outcome.chosen_card` 建 model）。
- **Reproduction**: 运行 `py -3.12 core/tools/orchestrator.py <任意项目> --execute` 后查看 `state/registry.json` 的 model `data.card_id`，与 `core/knowledge` 方法卡检索 top1 一致；实测 `projects/v3-real-2024a/state/registry.json`：`M001 card_id=mc-topsis`。
- **Proposed fix**: 默认路径若无执行证据，应像候选模式一样声明 `UNSELECTED/pending_evidence`（`handlers.py:834` 已有此模式），或由 orchestrator 接入候选竞技场（注入 fixtures/外部 Model Constructor 产物）。
- **Regression risk**: 低-中（会改变默认路径产物形态，可能 FAIL 下游依赖 model.card_id 的节点/校验）。
- **Test required**: 断言默认路径（无注入）下 model `selection_status == "pending_evidence"` 且无 `selects` 边。

### B-002 [Critical] `do_model_construction` 默认只登记假设，从不产 MODEL_IR，节点仍 PASS
- **File**: `core/runtime/execution/handlers.py`
- **Function-Symbol**: `DefaultNodeExecutor.do_model_construction`
- **Line**: 891-930（注意：怀疑提示的"257-280"是 `_exec_workdir`/`_code_for_mir`，实际函数在 891 行）
- **Observed behavior**: 循环内仅 (1) 从方法卡 risks 登记 assumption artifact + `assumes` 边（905-916 行）；(2) 调 `construct_candidate_mirs(qid)`/`construct_model_ir(qid)`——两者都依赖 `shared["external_candidates"]`/`shared["external_model_irs"]` 注入（218-232、208-216 行），**无注入时返回 None/[]，不产生任何 MODEL_IR**。节点以 `PASS("登记 N 条假设")` 结束（926-930 行）。DAG 描述却写"建立数学模型（公式/符号/边界）+ 模型依赖 DAG，产出 M artifacts"（`core/workflows/stages/modeling.yaml`）。
- **Expected behavior**: 建模节点应产出可执行模型规范（MODEL_IR）或至少 FAIL（无模型规范 = 建模未完成）。
- **Why it matters**: 生产链路中"模型"只是方法卡 ID 薄壳；MODEL_IR 18 字段契约在默认路径永远不被满足。实测三个真实项目 MIR 数均为 0（`v3-real-2024a`、`v3-real-2024a-g7test-A`、`v3-real-2024a-g8test-B` 的 registry.json）。
- **Evidence**: `handlers.py:918-925`；`projects/v3-real-2024a-g7test-A/state/registry.json`（types 中无 `model_ir`）。
- **Reproduction**: `py -3.12 core/tools/orchestrator.py <项目> --execute` → `state/registry.json` 无 MIR artifact。
- **Proposed fix**: 默认路径建模节点应 FAIL 直到 MODEL_IR 存在（fail-closed），或 orchestrator 显式接入外部 Model Constructor 产物注入。
- **Regression risk**: 高（默认路径会断链，需同步提供 MODEL_IR 生产来源）。
- **Test required**: 无注入时 `do_model_construction` 返回 FAIL；有注入时返回 PASS 且 MIR 落盘。

### B-003 [High] MODEL_IR 无 `code_mapping` 字段；MODEL_IR→Code 映射依赖外部声明且不校验
- **File**: `core/runtime/modeling/model_ir.py` / `core/schemas/v3/model/model_ir.schema.json` / `core/runtime/execution/codegen.py`
- **Function-Symbol**: `MODEL_IR_REQUIRED_FIELDS` / schema `required` / `register_code`
- **Line**: `model_ir.py:33-52`；`model_ir.schema.json:7-26`；`codegen.py:44-76`
- **Observed behavior**: 18 个 required 字段无 `code_mapping`（全仓 Grep `code_mapping` 0 匹配）。映射载体为 `solvers[].implementation_ref`（自由字符串）与 graph `implemented_by` 边；`codegen.py` 不生成代码，只登记外部 agent 产出的 code。
- **Expected behavior**: MODEL_IR 应含可机检的 code 映射（如 `code_mapping: {equation_id/solver_id → code symbol}`）并校验 `implementation_ref` 指向真实 CODE artifact。
- **Why it matters**: 模型规范与实现之间无自动、可验证的映射；"代码是否执行了 MODEL_IR 声明的模型"只能靠 `fidelity.py`（`output_mapping` 声明）事后对账。
- **Evidence**: `model_ir.py:33-52`；全仓 Grep `code_mapping` → 0 results；`vs001_fixtures.py:136`（`"implementation_ref": "CODE001"` 未校验）。
- **Reproduction**: 构造 `implementation_ref="不存在的ID"` 的 MODEL_IR，`_register_mir` 不会报错。
- **Proposed fix**: schema 增 `code_mapping`（或对 `implementation_ref` 做引用完整性校验）。
- **Regression risk**: 低。
- **Test required**: 断言 `solvers[].implementation_ref` 必须解析到已登记 CODE artifact。

### B-004 [High] Evidence Graph 无 `evaluated_by` / `selected_from` 边类型
- **File**: `core/runtime/graph/evidence_graph.py`
- **Function-Symbol**: `RELATION_TYPES`
- **Line**: 33-53
- **Observed behavior**: 18 种 typed relation 中无 `evaluated_by`（candidate→evidence）与 `selected_from`（selected_model→candidate）。全仓 Grep `evaluated_by|selected_from` 0 匹配。候选评估证据经 `verified_by`（EXEC→VR）挂载；选型可追溯性埋在 decision artifact 的 data 字段（`alternatives/evidence_ids/ranked`）。
- **Expected behavior**: 审计问题要求的 `candidate --evaluated_by--> evidence`、`selected_model --selected_from--> candidate` 边应存在，使图查询可直接回答"哪个候选被评估过、选中模型来自哪个候选"。
- **Why it matters**: 图级 traceability 不完整；`do_model_selection_decision` 的 evidence 只通过 decision.data 暴露，graph 查询（`out_edges/in_edges/evidence_chain`）无法沿边恢复候选→证据→选型链。
- **Evidence**: `evidence_graph.py:33-53`；`handlers.py:694-713`（decision.data 承载，graph 只写 `selects` 边）。
- **Reproduction**: 候选模式运行后 `graph.in_edges(M001)` 不含任何指向候选 MIR 的"选自"边。
- **Proposed fix**: 新增 `evaluated_by: ({"model_ir"}, {"verification_result"})` 与 `selected_from: ({"model"}, {"model_ir"})`（或 decision）边，并写传播档位。
- **Regression risk**: 中（边类型变更影响 `integrity_check` 与既有测试断言集合）。
- **Test required**: 断言候选模式运行后存在 `MIR-i -evaluated_by-> VR-i` 与 `M001 -selected_from-> MIR002` 边。

### B-005 [High] Candidate 分数是启发式常量，不是评估结果
- **File**: `core/runtime/modeling/candidates.py`
- **Function-Symbol**: `CandidateArena.generate_candidates`
- **Line**: 192-302（分数：197/220/241/265-271 行）
- **Observed behavior**: 候选分数 = 主方法检索分 ± 硬编码增量（boost +2；hybrid −2；innovation +novelty(2-6) −cost(0-4) +fit(±2)）；Competition Pack 再 ±5/±8（289-301 行）。分数不依赖任何模型执行/数值验证。
- **Expected behavior**: 候选评估分数应来自执行证据（如 VR 指标）或明确标注为"启发式预估"。
- **Why it matters**: `do_experiment_design` 取 `cands[0]`（`handlers.py:966`）作为最优候选规划实验——"最优"是启发式伪最优；且 `CandidateArena` 生成后在生产路径无任何消费评估。
- **Evidence**: `candidates.py:196-197,220,241,265-271`；`handlers.py:963-974`。
- **Reproduction**: 对同一问题调用 `generate_candidates`，分数仅随检索分/卡片字段变化，与执行结果无关。
- **Proposed fix**: 将候选评估改为消费 VR 证据（候选模式已存在 `_rank_candidates`），或把启发式分数标记为 `heuristic` 不参与选型。
- **Regression risk**: 中。
- **Test required**: 断言候选模式中 `_rank_candidates` 排序与 `Candidate.score` 解耦。

### B-006 [High] 生产实验结果为 `not_executed` 占位，Claim 可由未执行结果支撑
- **File**: `core/runtime/execution/handlers.py`
- **Function-Symbol**: `do_experiment`
- **Line**: 1078-1084（result data `status:"not_executed", note:"确定性 runtime 不执行数值计算；真实结果须由外部 executor...回填"`）
- **Observed behavior**: orchestrator 不传 execution_adapter（`orchestrator.py:391-392`）→ `_maybe_execute_experiment` 直接 return（`handlers.py:1120-1121`）→ result 永远 `not_executed`。但 `do_evidence_build` 仍可用该 result `supports` claim（实测 `v3-real-2024a-g7test-A` 的 `R001 -supports-> C001`）。
- **Expected behavior**: 无真实数值的结果不应支撑 claim（或 claim 状态应标 pending/未验证）。
- **Why it matters**: 论文数值必须来自 validated Result Artifact（AGENTS.md 铁律），而默认路径 result 无数值。
- **Evidence**: `handlers.py:1078-1084`；实测 registry（`R001 data.status=not_executed` 且存在 `supports` 边）。
- **Reproduction**: 默认路径运行后检查 result 的 `status` 与 claim 的 `supports` 边。
- **Proposed fix**: evidence gate 增加"result 必须 executed 才能 supports claim"门禁。
- **Regression risk**: 高（默认路径 claim 链会断）。
- **Test required**: 断言未执行 result 不能支撑 claim。

### B-007 [Medium] runtime 登记 MODEL_IR 不执行完整 jsonschema 校验
- **File**: `core/runtime/modeling/model_ir.py` / `core/runtime/execution/handlers.py` / `research/P15/scripts/k002_register.py`
- **Function-Symbol**: `validate_model_ir` / `_register_mir` / `main`
- **Line**: `model_ir.py:176-236`；`handlers.py:176-182`；`k002_register.py:122-133`
- **Observed behavior**: runtime 路径只用零依赖 `validate_model_ir`（18 顶层字段 + 数组非空 + id 字段存在），**不做**嵌套契约校验（如 `equations[].latex`、`solvers[].implementation_ref`、`parameters[].source` enum）。完整 jsonschema 仅在 research K002 登记脚本执行。
- **Expected behavior**: `_register_mir` 应按 `core/schemas/v3/model/model_ir.schema.json` 做真实 jsonschema 校验（schema 自述"使 jsonschema 校验成为真实可执行的门槛"，`model_ir.schema.json:5`）。
- **Why it matters**: schema 承诺与 runtime 门禁不一致；缺 latex/derivation_trace 的"空壳 MODEL_IR"可通过 runtime 校验。
- **Evidence**: `model_ir.py:179`（"不做 jsonschema 全量语义"）；`k002_register.py:31,122-133`（唯一真实 jsonschema 执行点）。
- **Reproduction**: 构造 equations=[] 或缺 latex 的 18 字段 MODEL_IR，`_register_mir` 通过（`validate_model_ir` 只查非空+id）。
- **Proposed fix**: `_register_mir` 接入 jsonschema（或至少按 schema 嵌套 required 补强 `validate_model_ir`）。
- **Regression risk**: 中。
- **Test required**: 断言缺 `equations[].latex` 的 MODEL_IR 被 `_register_mir` 拒绝。

### B-008 [Medium] V3 运行时从不读取题面/`question_spec.json`；Problem Representation 仅为粗画像
- **File**: `core/runtime/execution/session.py` / `handlers.py` / `core/tools/orchestrator.py`
- **Function-Symbol**: `RuntimeSession.__init__` / `features_for` / `_load_problem_features`
- **Line**: `session.py:78-83`；`handlers.py:55-65`；`orchestrator.py:349-392`
- **Observed behavior**: V3 管线输入为 `features` dict（最多六键）与 question 标签；无任何代码读取 `inputs/` 原始题面或 `work/question_spec.json`（Grep `core/runtime` 0 引用）。问题本体从未进入运行时。
- **Expected behavior**: Problem→Representation 环节应有题面解析/结构化表示接入 V3（`core/validators/modules/problem_spec_parser.py` 已存在但未接线）。
- **Why it matters**: 模型构建的"Problem"端是空壳——MODEL_IR 的 `problem_binding.problem_sha256` 无运行时校验对象。
- **Evidence**: `orchestrator.py:383-392`（仅 features）；`session.py:78-83`（question 纯标题）。
- **Proposed fix**: orchestrator 加载题面并解析为 `problem_binding`（sha256 + sub_question 列表）注入 runtime。
- **Regression risk**: 低-中。
- **Test required**: 断言 runtime 初始化时 problem 的 sha256 绑定存在。

### B-009 [Medium] Model Artifact 的 provenance 为空
- **File**: `core/runtime/execution/handlers.py` / `core/runtime/artifacts/artifact.py`
- **Function-Symbol**: `do_model_selection` / `_register_mir` / `Artifact`
- **Line**: `handlers.py:865-872, 192-200`（registry.create 未传 provenance）；`artifact.py:53`
- **Observed behavior**: 所有 `registry.create("model"/"model_ir"/...)` 调用均未传 `provenance` 参数 → artifact.provenance 默认 `{}`。实测真实项目 `M001 provenance={}`。
- **Expected behavior**: 模型产物应记录 `{node, session, tool, prompt_ref, model_version, ...}` 溯源。
- **Why it matters**: 审计问题 7（完整 provenance 谱系）不满足；模型来源无法从 artifact 自证。
- **Evidence**: `projects/v3-real-2024a-g7test-A/state/registry.json`（`M001 provenance={}`）；`handlers.py:865-872`。
- **Proposed fix**: handlers 创建 model/MIR 时传 `provenance={"node": node_id, "session": ...}`。
- **Regression risk**: 低。
- **Test required**: 断言 model artifact 的 provenance 非空且含节点来源。

### B-010 [Medium] `model_artifact.schema.json`（V2 冻结契约）无强制执行点
- **File**: `core/schemas/model_artifact.schema.json` / `core/runtime/artifacts/registry.py`
- **Function-Symbol**: `ArtifactRegistry.create` / schema
- **Line**: `registry.py:108-145`（只做 `art.validate()` 结构化校验，不校验 data 对 JSON Schema）；`model_artifact.schema.json:1-133`
- **Observed behavior**: schema 要求 `candidate_models.minItems=2`、`selected_model`、`selection_reason.minLength=30`、`problem_interpretation.minLength=50` 等；全仓无代码引用该 schema（domain/__init__.py 仅文档字符串标注"V2 冻结实验用"）。registry.create 对 `data` 不做任何 JSON Schema 校验。
- **Expected behavior**: Model Artifact 应满足其声明契约（或 schema 应接入 runtime 校验）。
- **Why it matters**: "Model Artifact 包含什么字段"无契约约束；生产 model 薄壳与 V2 契约（候选≥2、选择理由≥30 字）完全不符。
- **Evidence**: 全仓 Grep `model_artifact\.schema` → 仅 `domain/__init__.py:36` 文档提及；`registry.py:133-135`（校验范围仅 ID/类型/状态/引用）。
- **Proposed fix**: 明确 V3 model artifact 契约并接入校验，或废弃 V2 schema 声明。
- **Regression risk**: 中。
- **Test required**: 断言 runtime 产出的 model artifact 通过其声明 schema。

### B-011 [Medium] `_execution_inputs` 硬编码仿真时间点
- **File**: `core/runtime/execution/handlers.py`
- **Function-Symbol**: `_execution_inputs`
- **Line**: 327（`out["times"] = [0, 60, 120, 180, 240, 300]`）
- **Observed behavior**: 执行输入派生自 MODEL_IR parameters，但时间点数组硬编码为 2024_A 板凳龙题的时间采样（0-300s）。与 `experiments[].parameters.times`（fixture 中显式声明）重复且不一致时以硬编码为准。
- **Expected behavior**: 执行输入应来自 MODEL_IR `experiments[].inputs`/`parameters`，或至少与声明的实验参数一致。
- **Why it matters**: 非 2024_A 题执行会得到错误的时间输入；硬编码破坏通用性。
- **Evidence**: `handlers.py:318-328`。
- **Proposed fix**: 从 MODEL_IR experiments/parameters 读取 times，缺省才回退。
- **Regression risk**: 低（候选模式测试需同步 fixture）。
- **Test required**: 断言 `_execution_inputs` 使用 MODEL_IR 声明的 times。

### B-012 [Medium] 候选竞技场（P1-M3）未接入生产 orchestrator——默认路径为死代码
- **File**: `core/tools/orchestrator.py` / `core/runtime/execution/handlers.py`
- **Function-Symbol**: `orchestrator.execute` / `DefaultNodeExecutor`
- **Line**: `orchestrator.py:383-392`（无注入）；`handlers.py:819`（`_external_candidates(qid)` 恒空）
- **Observed behavior**: 唯一写 `shared["external_candidates"]`/`external_model_irs` 的地方是 `research/P15/m3_run/m3_driver.py:55` 与 `vs001_run/vs001_driver.py:66-68`（研究脚本+测试）。生产 orchestrator 从不注入 → `do_model_selection` 永远走 `arena.select`（recs[0] 硬编码），`do_model_selection_decision` 因 `n==0` 跳过（`handlers.py:736-738`）。
- **Expected behavior**: 证据化选型链应在生产路径可达（由外部 Model Constructor 或内置构造器提供候选）。
- **Why it matters**: 系统最完整的证据链（B-001~B-005 的"REAL 侧"）只活在研究脚本与测试里，生产运行时实际行为与 AGENTS.md 承诺不符。
- **Evidence**: `research/P15/m3_run/m3_driver.py:52-59`；`orchestrator.py:383-392`；实测 `v3-real-2024a-g7test-A/state/evidence_graph.json` 无 `instantiates/implemented_by/verified_by/selects` 边。
- **Proposed fix**: orchestrator 提供候选注入入口（CLI/配置文件），或默认走 evidence-based 选型语义（无证据 → UNSELECTED）。
- **Regression risk**: 高。
- **Test required**: orchestrator e2e 断言候选模式下 `selects` 边存在。

---

## 六、重点怀疑核验结论

| 怀疑 | 结论 | 证据 |
|---|---|---|
| `selection.py` 约 60 行存在 `chosen = recs[0]` 硬编码 | **确认**（精确行 60） | `selection.py:60` |
| `handlers.py` 约 257-280 行的 `do_model_construction` 只登记假设不产 MODEL_IR | **确认（行号有误，实质成立）**：函数在 891-930 行；无外部注入时只登记假设，MODEL_IR 不产生，节点 PASS | `handlers.py:891-930` |
| MODEL_IR 只是方法卡名称包装 | **不成立（结构层面）**：18 字段三层结构完整含 equations/mechanisms/solvers/validations；**但生产默认路径从不实例化**（MIR=0），且无 `code_mapping` | `model_ir.py:33-99`；实测 registry MIR=0 |

---

## 七、附：验证命令与输出

```
# 测试验证（候选竞技场 + MODEL_IR + 知识义务映射）：
py -3.12 -m pytest tests/integration/test_p1_m3_competition.py tests/runtime/test_model_ir.py tests/runtime/test_knowledge_obligation_mapping.py -q
# → 20 passed in 2.06s

# 真实项目产物实测（三个 V3 项目均 MIR=0 / VR=0）：
projects/v3-real-2024a/state/registry.json          → types 无 model_ir/verification_result；M001 card_id=mc-topsis provenance={}
projects/v3-real-2024a-g7test-A/state/registry.json → MIR count: 0；VR count: 0；graph 无 instantiates/implemented_by/verified_by/selects 边
projects/v3-real-2024a-g8test-B/state/registry.json → MIR count: 0；VR count: 0

# 全仓 Grep：
evaluated_by|selected_from|code_mapping → 0 匹配
```
