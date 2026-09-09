# Model Construction Gap Audit — 合成终稿（11 环节，上游 6 + 下游 5）

## 审计元信息

| 项 | 值 |
|---|---|
| 仓库路径 | `C:\Users\Lin\Desktop\Programs\MathModel` |
| HEAD | `4c80914` |
| 审计日期 | 2026-09-09 |
| 审计链 | 11 环节：1 Problem/Question · 2 Problem Analysis · 3 Method Recommendation · 4 Candidate Models · 5 Model Selection · 6 MODEL_IR · 7 Code Generation · 8 Execution · 9 Validation · 10 Evidence · 11 Revision |
| 数据来源 | `_audit_A_upstream.md`（环节 1–6）+ `_audit_B_downstream.md`（环节 7–11），两份只读证据报告 |
| 只读声明 | 本审计仅合成既有证据，未修改任何仓库文件，未执行任何 git 操作；全部 `path:line` 均出自两份证据报告，报告未给行号处仅写 `path` |

**执行摘要**：Runtime substrate 完整但 Model Construction Loop 未接通。上游 6 环节中，Problem/Question、Method Recommendation 有真实实现与测试；但 Candidate Models 只是内存对象、Selection 硬编码 `recs[0]`、MODEL_IR 零 runtime 集成、`model` artifact 仅是方法卡指针，"选型→实例化"根本不存在。下游 5 环节中，codegen / LocalPythonAdapter / ValidationReport / Evidence Graph 的底层原语真实且 demonstrated，但默认 V3 管线不接 adapter、DAG 无 code 节点、planner 不产代码，导致 `result` 恒 `not_executed`、`claim` 恒 `placeholder`；`evidence_gate` 只查边不查数值，占位链即可产出 `claims_supported=2, coverage=1.0` 骗过全部门禁。引擎的 retry/on_fail/rollback/supersede 机制真实，但默认管线零 FAIL、执行失败仍返回 PASS，"V1 FAIL→M2" 无端到端触发。结论：Registry / Evidence Graph / 引擎 / 适配器 / 校验原语这套基础设施可用，缺的是把它们接成闭环的那一层接线。

---

## 环节1 Problem / Question

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | demonstrated | `core/runtime/execution/session.py:78-83`（Question 预登记）；`core/runtime/execution/handlers.py:178-188`（`do_problem_analysis` 登记 Problem + motivates 边） |
| 2 | 入口函数 | demonstrated | `session.py:RuntimeSession.__init__`（`session.py:47`）；`handlers.py:DefaultNodeExecutor.do_problem_analysis`（`handlers.py:178`） |
| 3 | 真实输入 | demonstrated | `questions: list[str]`（仅 Q 标签字符串）；Problem title 取 `features.get("problem_title","赛题")`（`handlers.py:181`） |
| 4 | 真实输出 | demonstrated | Registry 中 problem artifact（P001）+ question artifact（Q001…）+ `problem -motivates-> question` 边（`handlers.py:185-186`）；无题面内容/子问题分解 |
| 5 | 是否真的执行 | demonstrated | `tests/integration/test_runtime_session.py:29-47` 端到端断言 types/motivates |
| 6 | 是否进入 Artifact Registry | demonstrated | `registry.create("problem"|"question", ...)`（`handlers.py:181`、`session.py:81`）；`checkpoint()` 落盘 `state/registry.json`（`session.py:143-150`） |
| 7 | 是否进入 Evidence Graph | demonstrated | motivates 注册于 `evidence_graph.py:34`；写入 `handlers.py:185-186` |
| 8 | 闭环/回退路径 | demonstrated | Question 失效时 `session.invalidate()` 全图重置（`session.py:224-227`）；该环节恒 PASS 无失败回退 |
| 9 | 假实现/占位 | instructional not enforced | Problem title 缺省硬编码 `"赛题"`（`handlers.py:181`）；`core/schemas/question_spec.schema.json` 存在但 runtime 无消费点 |
| 10 | 距真实 Model Construction 的差距 | not found | 无"题面文本→结构化 Problem/Question"解析；Q 是外部标签，P 是空壳 artifact |

**差距**：缺题面本体（文本/结构）进入 runtime 的解析环节，问题知识仍在 legacy `inputs/` 与 `problem_cards/`。

---

## 环节2 Problem Analysis（features / representation）

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | demonstrated | `handlers.py:52-62`（`features_for`）；`core/runtime/tools/orchestrator.py:349-368`（`_load_problem_features`）；`core/runtime/knowledge/intelligence.py:27-56`（`ProblemProfile`，runtime 不使用） |
| 2 | 入口函数 | demonstrated | `orchestrator.py:349` → `session.py:48` → `handlers.py:82`（存为 `self.features`） |
| 3 | 真实输入 | demonstrated | 外部 JSON（`problem_types/has_data/sample_size/time_series/objectives/uncertainty`，`retriever.py:165-178`；`high_dimensional/nonlinear/...`，`retriever.py:331-348`） |
| 4 | 真实输出 | demonstrated | 排序后 `Recommendation[]`（`retriever.py:224-234`）；features 只是内存 dict，无独立 features artifact |
| 5 | 是否真的执行 | demonstrated | 检索打分有大量单测（`test_method_cards.py`、`test_competition_intelligence.py`）；但"从问题文本提取 features" **not found**，由外部文件/调用方提供或回退 `_LEGACY`（`handlers.py:80-81`） |
| 6 | 是否进入 Artifact Registry | not found | `ProblemProfile` 不是 artifact 类型（`ids.py:19-37` 无此型） |
| 7 | 是否进入 Evidence Graph | not found | 无对应边 |
| 8 | 闭环/回退路径 | demonstrated | 无 features 时回退 `_LEGACY` 并显式打 `_features_source=legacy_default`（`handlers.py:80-81`、`orchestrator.py:384-389`）——诚实回退，但回退内容是硬编码画像 |
| 9 | 假实现/占位 | instructional not enforced | `_LEGACY` 硬编码默认画像（`handlers.py:80-81`）；`ProblemProfile` 默认值 `has_data=True, sample_size="medium"`（`intelligence.py:30-31`）可能不符真实题 |
| 10 | 距真实 Model Construction 的差距 | not found | 缺"题面→特征"解析器；`ProblemProfile` 与 features dict 两套表示并存且前者未被 runtime 使用 |

**差距**：Problem Analysis 是外部契约注入而非 runtime 内的问题分析能力，且无独立 artifact/图节点。

---

## 环节3 Method Recommendation（knowledge.py recommend + retriever）

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | demonstrated | `core/tools/knowledge.py:37,136`（CLI）；`retriever.py:162-237`（`recommend`）、`:241-319`（`_capability_match`）；`cards.py:359-387`（`load_knowledge`，19 张卡 + 失败记忆）；`packs.py:81-94,112-172`；`intelligence.py:92-112` |
| 2 | 入口函数 | demonstrated | `retriever.py:KnowledgeRetriever.recommend(features, top_k)`（`retriever.py:162`）；handler 侧 `do_literature_search` 调 `recommend(self.features, top_k=3)`（`handlers.py:190-206`） |
| 3 | 真实输入 | demonstrated | features dict；知识库 `core/knowledge/methods/cards/*.yaml`（19 张卡）、`failures/`、`patterns/`、`competition/cp-*.yaml` |
| 4 | 真实输出 | demonstrated | `Recommendation[]`（score/score_detail/matched/violations/risks/required_experiments/knowledge_refs，`retriever.py:51-112`） |
| 5 | 是否真的执行 | demonstrated | 打分规则全显式（`retriever.py:7-16`）；测试覆盖排序/排除（`test_competition_intelligence.py`、`test_method_cards.py`） |
| 6 | 是否进入 Artifact Registry | demonstrated（间接） | `do_literature_search` 把 top-3 写为 `decision` artifact（`handlers.py:196-201`）；Recommendation 对象本身不落 Registry |
| 7 | 是否进入 Evidence Graph | demonstrated | `decision -based_on-> problem`（`handlers.py:202-203`） |
| 8 | 闭环/回退路径 | demonstrated | 无候选时仍 PASS；真正的失败门在 `do_model_selection`（`SelectionError`→FAIL，`handlers.py:169-170`） |
| 9 | 假实现/占位 | contract exists runtime not demonstrated | `model_families.yaml` 18 canonical family 中 10+ 族 `cards: []`（`model_families.yaml:36,54,62,89,116,125,141,153,166,175,183`），无卡即无候选；`recommend` 只返回 `score>0`（`retriever.py:220`） |
| 10 | 距真实 Model Construction 的差距 | not found | 推荐是"卡库内匹配"非"建模方法空间"推荐；workflow 声明输出 `state/literature_evidence.json`（`core/workflows/stages/problem-analysis.yaml:16`）与真实输出（decision artifact）不一致 |

**差距**：知识覆盖 = 19 张卡 vs 18 族对齐失败，词表与卡库不对齐使多个 canonical 族永远不可被推荐。

---

## 环节4 Candidate Models

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | demonstrated | `core/runtime/modeling/candidates.py`（`Candidate` `:58-97`、`InnovationCandidate` `:26-55`、`CandidateArena` `:100-239`）；接线 `handlers.py:94`、`:244-247` |
| 2 | 入口函数 | demonstrated | `CandidateArena.generate_candidates(question, features, recs, top_cards=2)`（`candidates.py:110`）；消费方 `do_experiment_design`（`handlers.py:313-324`） |
| 3 | 真实输入 | demonstrated | `recs`（来自 `recommend_methods`，`intelligence.py:116`）或内部再检索（`candidates.py:113`）；features；pack（只读打分） |
| 4 | 真实输出 | demonstrated | `list[Candidate]`（candidate_id/kind(baseline|improved|hybrid|innovation)/composition/base_card/rationale/score/risks/...，`candidates.py:73-87`）；**只存 `DefaultNodeExecutor.shared` 内存 dict**（`handlers.py:96,245-246`），崩溃即丢 |
| 5 | 是否真的执行 | demonstrated | 确定性生成逻辑 + `test_competition_intelligence.py` 覆盖 `generate_candidates/rank_candidates`；e2e 也会生成候选 |
| 6 | 是否进入 Artifact Registry | not found | `ids.py:19-37` 无 `candidate` 类型；无 `registry.create("candidate", ...)` |
| 7 | 是否进入 Evidence Graph | not found | 无任何候选相关边 |
| 8 | 闭环/回退路径 | demonstrated | 生成异常被 `except Exception` 吞掉写入内存 `candidates_error`（`handlers.py:247-248`）；`experiment_design` 回退到 `shortlist`（`handlers.py:344-350`）——降级但不持久、不阻断 |
| 9 | 假实现/占位 | instructional not enforced | 候选分数是确定性启发式拼接（`candidates.py:147,163,184-190`：`main.score+2`、`max-2`、`+{high:6,...}-{high:4,...}`）；`_CANDIDATE_SEQ` 全局计数器（`candidates.py:23`）非会话隔离；innovation 恒 `status="hypothesis"`（`candidates.py:42,233`）；一个 batch 只保留第一个 pattern（`candidates.py:201`） |
| 10 | 距真实 Model Construction 的差距 | not found | 候选集不是一等对象（无 artifact/持久化/graph 边），且不参与选型（选型只看 `recs[0]`） |

**差距**：四型候选只服务实验计划生成，无"候选集评审→淘汰→重生成"闭环，分数非证据估计。

---

## 环节5 Model Selection（Decision artifact：alternatives/criteria/evidence/chosen）

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | demonstrated | `core/runtime/modeling/selection.py`（`MethodArena` `:40-121`，`select` `:46`）；`core/runtime/decisions/log.py`（`DecisionLog` `:114-279`）；接线 `handlers.py:87` + `do_model_selection` `:208-255`；`decision.schema.json` |
| 2 | 入口函数 | demonstrated | `MethodArena.select(question, features, top_k=3, created_by, record=True)`（`selection.py:46`）；`do_model_selection` 逐 Q 调用（`handlers.py:214`） |
| 3 | 真实输入 | demonstrated | features dict；`DecisionLog`（可空）；知识库 |
| 4 | 真实输出 | demonstrated | `SelectionOutcome{question, features, shortlist, chosen, decision_id, prior_decisions, notes}`（`selection.py:26-37`）；**chosen = `recs[0].card.card_id`（`selection.py:60`）硬编码取第一** |
| 5 | 是否真的执行 | demonstrated | `test_model_selection.py:33-85`（chosen 前缀 `mc-`、alternatives≥1、D001、旧决策自动 invalidated）；`test_decision_log.py` 全覆盖 |
| 6 | 是否进入 Artifact Registry | contract exists runtime not demonstrated | 选型 Decision 进 **DecisionLog（独立 `state/decision_log.json`，`session.py:68`）非 Registry decision artifact**；Registry 的 `decision` 只被 `do_literature_search`（`handlers.py:196`）与 `do_experiment_design`（`handlers.py:336`）使用；`model` artifact 被写入（`handlers.py:231-238`）但只是指针 |
| 7 | 是否进入 Evidence Graph | contract exists runtime not demonstrated | `selects` 边已注册（`evidence_graph.py:45` `(decision)→(model)`；`:79` 传播档 `(None,None)`），但 **core 零 `add_relation(..., "selects", ...)` 调用**；`do_model_selection` 只写 `solved_by`（`handlers.py:240`）；结构原因：`selects` 要求 from 是 Registry decision artifact，而选型决策在 DecisionLog |
| 8 | 闭环/回退路径 | demonstrated | `do_model_selection` 无 `on_fail`（`modeling.yaml:7-12`）；`SelectionError`→FAIL 走引擎重试（`handlers.py:169-170`）；`session.invalidate` 时 `reset_to("model_selection")`（`session.py:227-228`）；历史冲突只产生 note（`selection.py:77-84`），旧选型被自动 invalidate（`selection.py:113-120`） |
| 9 | 假实现/占位 | instructional not enforced | `chosen=recs[0]`（`selection.py:60`）；`criteria` 固定四词字符串（检索得分/适用条件匹配/验证代价/历史决策一致性，`selection.py:96-97`）；`confidence=0.5+0.1*score` 线性启发（`selection.py:100`）；`evidence_ids=[]` 恒空（`selection.py:103`）；`reasoning` 回退 `top.reasoning() or f"{name} 得分最高"`（`selection.py:98-99`） |
| 10 | 距真实 Model Construction 的差距 | not found | 选型 = 检索排序 + 登记，无 alternatives/criteria/evidence/chosen 的真实比较；DecisionLog 与 Registry 两套存储闭合不了，`decision→selects→model` 链从未落地 |

**差距**：无真实比较决策，决策实体与 Registry/Graph 脱节。

---

## 环节6 MODEL_IR

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | contract exists runtime not demonstrated | `research/P15/model_representation/model_ir.schema.json`（v1.0，18 个 required 顶层字段，`:7-25`）；`example_2024_A.json`（手工完整实例）；`validate_example.py`、`run_deterministic_checks.py`（独立校验脚本，硬编码本机绝对路径 `validate_example.py:7-8`，依赖 jsonschema） |
| 2 | 入口函数 | not found | core runtime 无入口；grep 全 core `model_ir`/`MODEL_IR`/`ModelIR` 零命中 |
| 3 | 真实输入 | contract exists runtime not demonstrated | JSON 实例文件 |
| 4 | 真实输出 | contract exists runtime not demonstrated | 校验通过/失败打印 |
| 5 | 是否真的执行 | contract exists runtime not demonstrated | 独立脚本可运行；无任何 pipeline 调用点；与 core/runtime（零第三方依赖）无集成 |
| 6 | 是否进入 Artifact Registry | not found | `model` artifact data 仅 `{card_id, family, shortlist}`（`handlers.py:235-237`），无 MODEL_IR 字段 |
| 7 | 是否进入 Evidence Graph | not found | MODEL_IR 的 `model_graph` 是文件内图，与 `evidence_graph.json` 无关 |
| 8 | 闭环/回退路径 | not found | MODEL_IR 不在闭环内 |
| 9 | 假实现/占位 | not found | 无 MODEL_IR builder/constructor、无 LLM→JSON 结构化出口；`model` artifact = 方法卡指针（stub）；`docs/REPOSITORY_AUDIT/STRUCTURE_NAMING_PROPOSAL.md:36,99` 曾记载该目录为空 |
| 10 | 距真实 Model Construction 的差距 | not found | 差四步：① schema 进 `core/schemas/`；② 结构化构造函数（候选/选型→变量/目标/约束/方程实例化）；③ `model` artifact 挂载 MODEL_IR payload；④ 校验器接入 `validate.py` |

**差距**：runtime 的 `model` 只是"选了哪张卡"，不是模型实例；Model Construction 环节没有 instantiate 这一步。

---

## 环节7 Code Generation

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | demonstrated | `core/runtime/execution/codegen.py`：`register_code` `:44-76`、`execute_code` `:81-131`、`run_code_pipeline` `:136-172`、CLI `:175-193`；`adapters.py:156-261`（LocalPythonAdapter）；`fidelity.py` |
| 2 | 入口函数 | demonstrated | `run_code_pipeline`（`codegen.py:136`）；CLI `main`（`codegen.py:175`）；**但 V3 DAG 无 code 节点**（`catalog/v3.yaml:24-81` 16 节点不含 code_gen）；`experiment.yaml:15` 声称产出 CODE/E artifacts，`do_experiment`（`handlers.py:362-454`）从不创建 CODE artifact |
| 3 | 真实输入 | demonstrated | `register_code(code, language, ...)` 非空校验（`codegen.py:59-62`）；`execute_code(code_artifact_id, ...)` 必须是已注册 code 类型（`codegen.py:100-101`）；`ExecutionPlan{model_id, code, inputs, timeout_seconds, workdir, env, adapter, meta}`（`adapters.py:72-83`） |
| 4 | 真实输出 | demonstrated | `code` artifact（ID 前缀 CODE，`ids.py:26`）；`execution_result` artifact（`ExecutionResultData.to_dict()`，`adapters.py:107-126`）；`run_code_pipeline` 返回 dict（`codegen.py:166-172`） |
| 5 | 是否真的执行 | demonstrated | `LocalPythonAdapter.execute` 真实 `subprocess.run`（`adapters.py:198-202`），status 由 returncode 推导（`adapters.py:206`）；`test_execution_codegen.py:60-72`、`test_execution_runtime.py:52-72`；**但生产入口不接 adapter**：`orchestrator.py:391-392` 不传 `execution_adapter`，`session.py:62` 默认 None → `_maybe_execute_experiment` 直接 return（`handlers.py:470-471`） |
| 6 | 是否进入 Artifact Registry | demonstrated | `reg.create("code", ...)`（`codegen.py:65-74`）；`reg.create("execution_result", ...)`（`codegen.py:121-126`）；落盘 `state/registry.json`（`registry.py:71-91`） |
| 7 | 是否进入 Evidence Graph | contract exists runtime not demonstrated | `execute_code` 写 `result -executed_by-> execution_result`（`codegen.py:127-129`）；**`model -implemented_by-> code` 零写入**（grep 仅 schema/legacy 注释，`evidence_graph.py:37`、`convert.py:51,74`） |
| 8 | 闭环/回退路径 | not found | codegen 是独立 CLI/库路径不在 DAG；fidelity misaligned 只影响 CLI 退出码（`codegen.py:193`），不触发引擎 rollback |
| 9 | 假实现/占位 | not found | 无 adapter 即静默降级（`handlers.py:470-477`），result 保持 `not_executed`（`handlers.py:431-432` 注明由 `register_external_artifact` 回填——**该函数不存在**，grep 零实现） |
| 10 | 距真实 Model Construction 的差距 | not found | DAG 无 code 节点；`planner.py:81-91` 的 plan `as_dict` 无 code 字段，`handlers.py:473-476` 的 `for cand in plan: if cand=="code"` 在真实 plan 上永远找不到 code；缺 `implemented_by` 边写入 |

**差距**：代码生成完全在 V3 管线之外，只能靠测试手工注入 `shared[qid]["plan"]={"code":...}`（`test_execution_runtime.py:57`）。

---

## 环节8 Execution（execution_result 一等 artifact）

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | demonstrated | `adapters.py`：`EXEC_STATUS` 六态枚举 `:37`、`EXECUTION_RESULT_FIELDS` `:40-47`、`ExecutionPlan` `:72-83`、`ExecutionResultData` `:87-130`、`ExecutionAdapter` ABC `:141-153`、`LocalPythonAdapter` `:156-261`、`get_adapter` `:264-268` |
| 2 | 入口函数 | demonstrated | 库入口 `LocalPythonAdapter.execute(plan)`（`adapters.py:177`）；session 侧 `RuntimeSession.run()`（`session.py:102`）→ `WaveExecutor.run()`（`wave_executor.py:64`）→ `do_experiment`（`handlers.py:362`）→ `_maybe_execute_experiment`（`handlers.py:456`）；生产入口 `orchestrator.py --execute`（`orchestrator.py:503-504`） |
| 3 | 真实输入 | demonstrated | `ExecutionPlan`（`adapters.py:72-83`）；session 路径 plan 来自 `ExperimentPlanner`（无 code 键）或测试注入 `{"code":...}` |
| 4 | 真实输出 | demonstrated | `ExecutionResultData`（execution_id/model_id/status/inputs/outputs/stdout/stderr/returncode/duration_ms/code_hash/environment_hash/...，`adapters.py:107-126`）；stdout 最后一块合法 JSON 为 outputs（`adapters.py:207-223`） |
| 5 | 是否真的执行 | demonstrated | adapter 层真实 subprocess + 退出码（`adapters.py:198-206`）、timeout（`:234-245`）、framework error→invalid（`:246-256`）；测试 `test_execution_runtime.py:52-84`、`test_execution_codegen.py:60-72`、`test_execution_adapter.py`；**V3 生产路径 runtime not demonstrated**：orchestrator 不传 adapter（`orchestrator.py:391-392`），默认 run 产物类型不含 execution_result（`test_runtime_session.py:37-47`） |
| 6 | 是否进入 Artifact Registry | demonstrated | `execution_result` 一等类型 ID 前缀 EXEC（`ids.py:35`）；`codegen.py:121-126`、`handlers.py:490-495` 均 `reg.create("execution_result", ...)`；`result` 同步翻状态（`handlers.py:496-499`） |
| 7 | 是否进入 Evidence Graph | demonstrated | `result -executed_by-> execution_result`（`handlers.py:503-504`、`codegen.py:127-128`；类型约束 `evidence_graph.py:48`）；**注意用户假设链 `code.executed_by→execution_result` 与 `execution_result.produces→result` 不存在**（`executed_by` from∈{result}；`produces` 仅 `(experiment)→(result)`，`evidence_graph.py:41`；execution_result 无出边） |
| 8 | 闭环/回退路径 | not found | 执行失败（failed/timeout/invalid）时 `do_experiment` 仍返回 `NodeResult(PASS)`（`handlers.py:452-454`），节点照常 completed；`do_experiment_critique` 只查终态（`handlers.py:543-547`），failed 非终态→PASS；执行失败不触发引擎 retry/on_fail |
| 9 | 假实现/占位 | contract exists runtime not demonstrated | status 真实推导非硬编码（`adapters.py:206`）；但 `registry.create("execution_result", data=任意dict)` 无 schema 门禁（`registry.py:108-145`），status 可被任意调用方伪造；`environment_hash` 是浅指纹（仅 python/platform/executable，`adapters.py:63-69`，不含包版本/种子）；默认 V3 整体不执行，result 写死 `not_executed`（`handlers.py:431-432`） |
| 10 | 距真实 Model Construction 的差距 | not found | 生产入口与执行后端未接线；plan 无 code 来源；execution_result 无 JSON Schema；失败不产生 FAIL 节点状态；`register_external_artifact` 回填路径缺失 |

**差距**：底层真执行、上层永不调用，默认 run 的"实验结果"全部为空壳。

---

## 环节9 Validation（Model-Code Fidelity + 模型验证）

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | demonstrated | `validation.py`：`run_check` 5 种确定性检查 `:104-150`、`run_checks` 三状态铁律 `:153-168`、`validate_execution` `:173-220`、`VerificationResultData` `:33-49`、`resolve_output_key` `:82-99`；`fidelity.py`：`fidelity_checks_from_ir` F1–F5 `:54-114`、`check_fidelity` `:119-157`、`verify_fidelity` `:160-213`；`evidence_gate.py:87-181`（E1–E8）；`assumption_validator.py:9-152`（V3 runtime 未调用） |
| 2 | 入口函数 | demonstrated | `run_checks(execution_data, checks)`（`validation.py:153`）/ `validate_execution`（`validation.py:173`）；`check_fidelity(model_ir, execution_data, ...)`（`fidelity.py:119`）/ `verify_fidelity`（`fidelity.py:160`）；DAG 层 `do_evidence_gate`（`handlers.py:587-597`） |
| 3 | 真实输入 | demonstrated | `checks: list[dict]`（name/kind/path/min/max/expect/names/declared；kind ∈ 5 种，`validation.py:104-150`）；fidelity 输入 MODEL_IR dict（variables/objectives/constraints/equations，`fidelity.py:54-114`）+ output_mapping |
| 4 | 真实输出 | demonstrated | `run_checks` → `(status, checks)`，status ∈ {passed, failed, invalid}（`validation.py:167-168`）；VR artifact（`validation.py:27-49`，ID 前缀 VR `ids.py:36`）；`check_fidelity` → `{status: aligned|misaligned|unverifiable, fidelity_score, passed, total, checks}`（`fidelity.py:154-157`）；fidelity 报告 `state/fidelity/<exec_id>.json`（`fidelity.py:194-213`） |
| 5 | 是否真的执行 | demonstrated | 原语层纯确定性 + 测试（`test_execution_validation.py:40-75` 三状态铁律、`:78-97` VR+边；`test_execution_fidelity.py:55-157`）；**V3 生产路径 runtime not demonstrated**：`RuntimeSession.__init__` 构造 `WorkflowEngine` 未传 validators（`session.py:84-88`；`wave_executor.py:30-31` 同样 None），`engine._run_validator`（`engine.py:169-179`）查不到绑定 validator，catalog/v3.yaml:39,43,55,62,66,80 声明的 validator 在 session 路径不执行；`do_assumption_check`（`handlers.py:294-299`）只数 assumes 边，从不调用 `AssumptionValidator` |
| 6 | 是否进入 Artifact Registry | demonstrated | VR 经 `reg.create("verification_result", ...)`（`validation.py:208-212`）；fidelity 报告写文件（`fidelity.py:194-207`） |
| 7 | 是否进入 Evidence Graph | demonstrated | `execution_result -verified_by-> verification_result`（`validation.py:217`；类型约束 `evidence_graph.py:49`）；fidelity 复用 VR 框架（`fidelity.py:188-192`）；**VR 不产生指向 model/result/claim 的边，DAG 后续节点不消费 VR** |
| 8 | 闭环/回退路径 | contract exists runtime not demonstrated | VR failed/invalid 只登记在案，无 DAG 节点读取并判 FAIL；`evidence_gate` 不查 VR；`evidence_gate`/`quality_evaluation` 的 `on_fail` 配置存在（`evidence.yaml:20,29-30`）+ 引擎 rollback（`engine.py:218-234,279-281`），但默认不触发 |
| 9 | 假实现/占位 | contract exists runtime not demonstrated | **L0–L4 五层体系不存在**：无 L0（artifact schema 校验不由 runtime 执行）、无 L3（数学正确性）、L2/L4 只是注释标签（`fidelity.py:4`、`handlers.py:588`）；**feasibility/residual/stability/domain 零实现**（runtime 只有 5 种输出检查 `validation.py:111-150`）；`plan.required_checks` 是方法卡字符串无人消费（`planner.py:123-127`）；`code_deliverables.schema.json:104-146` 的 constraint_reverification/multi_run_stats/sensitivity 是 legacy 契约；fidelity 是机械结构对比（`fidelity.py:13-14` LLM-free），F2/F3/F4 只查"声明符号可观测"不校验约束是否满足；无 FidelityReport 数据结构（只有 dict） |
| 10 | 距真实 Model Construction 的差距 | not found | 五层体系未成体系；validator 未接 engine 挂钩；VR 未进 DAG 决策；缺"执行失败/验证失败→节点 FAIL→反馈环"的语义接线 |

**差距**："变量存在"≠"约束成立"，验证深度停留在符号可观测层，且验证结果不被下游消费。

---

## 环节10 Evidence（Evidence Graph 写入与谱系）

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | demonstrated | `evidence_graph.py`：16 种 typed relation `:33-50`、STRONG 10 种 `:52-55`/WEAK 2 种 `:56`（executed_by/verified_by 单独传播档 `:82-83`）、`_PROPAGATION` 档位 `:67-84`、`add_relation` fail-closed `:163-196`、`invalidate` 不动点传播 `:326-421`、`retract_invalidated` `:290-307`、`coverage` `:275-288` |
| 2 | 入口函数 | demonstrated | `EvidenceGraph.add_relation(from_id, relation, to_id, check_types=True)`（`evidence_graph.py:163`）；session 侧 `_register_evidence`（`session.py:90-98`） |
| 3 | 真实输入 | demonstrated | `{from, relation, to}` 三元组；from/to 必须是已注册 artifact（`evidence_graph.py:159-161,177-178`）；类型必须匹配（如 executed_by from∈{result}, to∈{execution_result}，`evidence_graph.py:48`） |
| 4 | 真实输出 | demonstrated | 边记录追加（`evidence_graph.py:192-193`），持久化 `state/evidence_graph.json`（graph_version+1，`evidence_graph.py:136-155`）；Artifact contract 只读视图同步（`evidence_graph.py:437-442`） |
| 5 | 是否真的执行 | demonstrated | `test_runtime_session.py:44-47`（motivates/solved_by/assumes/validated_by/produces/visualized_by/supports/appears_in）、`test_execution_validation.py:94-97`（verified_by）、`test_execution_runtime.py:70-72`（executed_by）、`test_evidence_graph.py`（传播） |
| 6 | 是否进入 Artifact Registry | demonstrated | `set_relations_view` 同步（`evidence_graph.py:437-442` → `registry.py:305-310`） |
| 7 | 是否进入 Evidence Graph | contract exists runtime not demonstrated | 用户点名的四条链：`model -implemented_by-> code` **schema 存在但 V3 runtime 零写入**（`evidence_graph.py:37`）；`code -executed_by-> execution_result` **不存在**（实际 `result→execution_result`，`evidence_graph.py:48`）；`execution_result -produces-> result` **不存在**（produces 仅 experiment→result，`evidence_graph.py:41`，execution_result 无出边）；`result -supports-> claim` **存在**（`evidence_graph.py:43`、`handlers.py:579-580`）；**无 revision_of/supersedes 边**（16 种关系无此二类） |
| 8 | 闭环/回退路径 | contract exists runtime not demonstrated | `evidence_gate` FAIL → on_fail experiment_design（`evidence.yaml:20`）+ 引擎 rollback（`engine.py:279-281`）结构性存在；默认管线 evidence_gate 恒 PASS 未演示 |
| 9 | 假实现/占位 | instructional not enforced | claim 显式占位 `{"statement": f"{qid} 结论", ..., "placeholder": True}`（`handlers.py:569-578`）；**evidence_gate E1–E8 只查边/生命周期/tags 不查数值**（`evidence_gate.py:87-181`），默认 run 占位链即产出 `claims_supported=2, coverage=1.0`（`test_runtime_session.py:55-56`）；`retract_invalidated` 剪死边是审计保留的妥协（`evidence_graph.py:290-296`） |
| 10 | 距真实 Model Construction 的差距 | not found | `implemented_by` 无写入方；execution_result 与 result/claim 之间缺正向 evidence 边；占位 claim 不被门禁拦截；缺 revision/supersedes 类型化边；`coverage` 度量"边存在"而非"证据真实性" |

**差距**：谱系边只覆盖登记型产物，模型→代码→执行→结果的正向证据链断裂，占位 claim 可通过门禁。

---

## 环节11 Revision（M1→E1→V1 FAIL→M2 闭环）

| 问号 | 问题 | 结论 | 代码证据 |
|---|---|---|---|
| 1 | 真实存在的代码 | demonstrated | `engine._handle_failure` `:218-234`、`rollback_to/reset_to` `:262-281`、`reset_question` `:283-305`；`session.invalidate` `:196-245`、`rerun` `:247-260`、`resume` `:136-141`；DAG 反馈边：`model_critique.on_fail→model_construction`（`modeling.yaml:26`）、`experiment_critique.on_fail→experiment*`（`experiment.yaml:27`）、`evidence_gate.on_fail→experiment_design`（`evidence.yaml:20`）、`quality_evaluation.on_fail→evidence_build`（`evidence.yaml:30`）；lifecycle superseded（`lifecycle.py:21-37`）、`registry.supersede`（`registry.py:284-295`）、`registry.update` 版本历史（`registry.py:240-282`）、runs `parent_run_id`（`runs.py:117-127`） |
| 2 | 入口函数 | demonstrated | 自动 `WorkflowEngine.run`（`engine.py:210-216`）→ `_handle_failure`（`engine.py:218`）→ `rollback_to`（`engine.py:279`）；人工 `session.invalidate(artifact_id, reason)`（`session.py:196`）、`session.rerun(node_id, reason)`（`session.py:247`） |
| 3 | 真实输入 | demonstrated | `NodeResult(status="fail", reason)` + 节点 `max_retries`/`on_fail`（`dag.py:30-57`）；`artifact_id`+`reason` / `node_id`+`reason` |
| 4 | 真实输出 | demonstrated | `progress()`（completed/blocked/waiting/retries/failures，`engine.py:95-104`）；`reset_to` 返回受影响节点集合（`engine.py:262-277`）；invalidate/rerun 报告（`session.py:244-245,259-260`） |
| 5 | 是否真的执行 | demonstrated | 引擎/测试层：`test_workflow_execution.py:47-69`（重试耗尽沿 on_fail 回滚）、`test_runtime_session.py:79-104`（invalidation→局部重跑）、`:124-140`（resume 续跑）；**默认 V3 生产路径不触发**：默认管线全节点自证 PASS（`test_runtime_session.py:33-35` blocked/failures 空），无"V1 FAIL 自动升级 M1→M2"端到端演示 |
| 6 | 是否进入 Artifact Registry | demonstrated | `_supersede_question_chain` 把旧 E/R/F/C 全量 superseded（`handlers.py:521-536`）；`do_model_selection` rerun 分支 supersede 旧 model（`handlers.py:217-227`）；`registry.supersede()` 记录 `invalidation.invalidated_by=replacement`（`registry.py:284-295`） |
| 7 | 是否进入 Evidence Graph | contract exists runtime not demonstrated | 新旧谱系无类型化边（无 revision_of/supersedes）；`retract_invalidated` 剪除触及 superseded/invalidated 的边（`evidence_graph.py:290-307`），`do_evidence_gate` 执行前也先 retract（`handlers.py:590`）——M1→M2 修订谱系无法从图查询 |
| 8 | 闭环/回退路径 | contract exists runtime not demonstrated | 部分闭环可表达（`modeling.yaml:26`、`session.py:227-228`）；但执行/验证失败（环节8/9）不映射 FAIL 节点，E/V 失败无法触发 M 层回退——闭环只覆盖批判/门禁类 FAIL |
| 9 | 假实现/占位 | instructional not enforced | `force_new_lineage` 只在 `session.rerun`（`session.py:256`）与测试注入时置位；幂等复用逻辑在 rollback 后复用既有非终态实验链（`handlers.py:377-379`），只回填 tags/provenance（`handlers.py:380-402`）——修订退化为元数据修补；`quality_evaluation` WEAK/UNKNOWN 只记录 advisory（`handlers.py:601-605`） |
| 10 | 距真实 Model Construction 的差距 | not found | 缺类型化 revision/supersedes 谱系边；缺"执行失败/VR 失败→节点 FAIL→M 层回退"语义接线；缺自动 revision 端到端演示；`register_external_artifact`/真实数值回填缺失使 E1→V1 无法在数值层发生 |

**差距**：Revision 的引擎机制真实且被测试证明，但默认管线零 FAIL，反馈环从未被激活，谱系修订不可见。

---

## 假实现 / 占位 / 硬编码清单（上游 + 下游合并）

| 位置 | 类型 | 表现 | 风险 |
|---|---|---|---|
| `handlers.py:80-81` | 硬编码 | `_LEGACY` features 默认画像（`problem_types=["evaluation"]`…），仅打 `_features_source=legacy_default` 标记 | 假分析进入检索链路，污染推荐与选型 |
| `handlers.py:181` | 硬编码 | Problem title 缺省 `"赛题"` | P artifact 无题面信息 |
| `handlers.py:231-238` | 占位 | `model` artifact = 方法卡指针（`data={card_id, family, shortlist}`），全 runtime 唯一"Model 实例"无模型内容 | 下游永远拿不到可实例化的模型 |
| `handlers.py:257-280` | 假实现 | `do_model_construction` 只登记假设（assumes 边），与 workflow 声明"建立数学模型（公式/符号/边界）+ 模型 DAG"不符 | Model Construction 环节名存实亡 |
| `handlers.py:272` | 硬编码 | 无风险时固定假设文案 `"所选方法的前提条件成立（数据规模/类型/独立性）"` | 假设内容不可信 |
| `handlers.py:428-434` / `:431-432` | 占位 | `result` status 写死 `not_executed`，note 声称由 `register_external_artifact` 回填——**该函数不存在** | 默认 run 实验结果全部为空壳 |
| `handlers.py:569-578` | 占位 | claim `{"statement": f"{qid} 结论", "placeholder": True, "execution_status": "not_executed"}` | 占位 claim 可进论文且带 supports 边 |
| `selection.py:60` | 硬编码 | `chosen=recs[0].card.card_id` 直接取第一 | 选型无比较，候选集被架空 |
| `selection.py:96-97,103` | 硬编码 | `criteria` 固定四词字符串、`evidence_ids=[]` 恒空、`confidence=0.5+0.1*score` | 决策无依据、无证据绑定 |
| `candidates.py:147,163,184-190` | 硬编码启发式 | 候选分数 `+2`/`max-2`/`+{high:6,...}-{high:4,...}` | 分数非任何模型/证据估计 |
| `candidates.py:23,42,201,233` | 假实现 | `_CANDIDATE_SEQ` 全局计数器非会话隔离；innovation 恒 `hypothesis`；一个 batch 只保留第一个 pattern | 候选集不可复现、不完整 |
| `planner.py:150,180-181,241-242` | 占位 | 基线文案 `"朴素基线（均值/最近值/穷举小规模等同口径对照）"` 硬编码；`accept_if="criteria_pass"` 等占位字符串 | 计划决策规则空转 |
| `intelligence.py:161` | 硬编码 | `build_experiment_plan` 取 `cands[0]` 排名第一 | 实验计划无选择依据 |
| `handlers.py:247-248` | 静默降级 | 候选生成异常被 `except Exception` 吞掉，仅写内存 `candidates_error` | 失败不可见、不持久 |
| `research/P15/model_representation/` | 未接线 | MODEL_IR schema/example/校验脚本齐全但零 runtime 集成；`validate_example.py:7-8` 硬编码本机绝对路径 | 模型表示无落地路径 |
| `model_families.yaml:36,54,62,89,116,125,141,153,166,175,183` | 词表不对齐 | 18 canonical family 中 10+ 族 `cards: []`，无卡即无候选 | 这些族永远无法被推荐 |
| `evidence_gate.py:87-181` | 假门禁 | E1–E8 只查边存在/生命周期/tags，不查数值真实性；零数值占位链可 PASS（`claims_supported=2, coverage=1.0`） | 论文出口无数值保障 |
| `orchestrator.py:391-392` | 未接线 | `--execute` 不传 `execution_adapter`（`session.py:62` 默认 None） | 生产入口永不执行代码 |
| `session.py:84-88` / `wave_executor.py:30-31` | 未接线 | `WorkflowEngine(validators=None)` | catalog/v3.yaml 声明的 validator（:39,43,55,62,66,80）在 session 路径不执行 |
| `handlers.py:294-299` | 未接线 | `do_assumption_check` 只数 assumes 边，从不调用 `assumption_validator.py` | 假设校验空转 |
| `handlers.py:473-476` | 死代码 | `_maybe_execute_experiment` 的 code 来源 `plan["code"]` 在真实 planner 输出（`planner.py:81-91`）中永远不存在 | V3 默认管线不产生任何 EXEC |
| `validation.py:104-150` | 名不副实 | 仅 5 种输出检查；feasibility/constraint/residual/stability/domain 零实现 | 验证覆盖不足 |
| `code_deliverables.schema.json:104-146` | 契约空洞 | constraint_reverification/multi_run_stats/sensitivity 仅 legacy schema，runtime 不消费 | 声明与实现脱节 |
| `evidence_graph.py:37` | 无写入方 | `implemented_by` 边类型存在但 V3 runtime 零写入 | 模型→代码谱系断 |
| `evidence_graph.py:48,41` | 链断裂 | 用户假设链 `code.executed_by→execution_result`、`execution_result.produces→result` 不存在；execution_result 无出边 | 谱系链不通 |
| `evidence_graph.py:290-307` | 语义妥协 | `retract_invalidated` 剪死边使修订谱系在图中不可见；无 revision_of/supersedes 边 | 修订不可审计 |
| `handlers.py:377-402` | 幂等降级 | rollback 后"重跑"复用既有实验链，只回填 tags/provenance，不产生新数值 | 重跑语义退化 |
| `adapters.py:63-69` | 浅实现 | `environment_hash` 仅 python/platform/executable，无包版本/依赖/种子 | replay 归因能力有限 |
| `registry.py:108-145` | 无门禁 | `create("execution_result", data=任意dict)` 不校验 EXEC 字段/status 枚举 | status 可被伪造 |
| `core/schemas/` | 缺失 | 无 execution_result / verification_result / validation_report / result / claim 的 JSON Schema | 结构化门禁缺位 |
| `codegen.py:175-193` | 孤岛 | codegen CLI 的 fidelity 失败只改退出码，无 DAG 反馈闭环 | 生成侧与管线脱节 |
| `engine.py:45-53,169-178` vs `session.py:84-88` | 未接线 | validator 挂钩存在但 session 不传 validators | 引擎级校验永远不触发 |
| `session.py:68` vs `log.py:6-7` | doc mismatch | DecisionLog 文档写 `decisions.json`，实际路径 `decision_log.json` | 定位误导（轻微） |

---

## 关键检查点裁决

1. **Model→Code Fidelity 机械结构检查 — PARTIAL**。`fidelity.py` 是真实现（F1–F5 确定性结构对比、三状态 aligned/misaligned/unverifiable，测试 demonstrated，`test_execution_fidelity.py:55-157`），但只查"声明符号是否可观测"、不校验约束/残差，无 FidelityReport 数据结构，且只在 codegen/测试路径可达，V3 默认管线不接线。
2. **Candidate Model Set + Decision — FAIL**。候选集存在但非一等对象（无 artifact/Registry/Graph/持久化，仅内存 `shared`）；选型 `chosen=recs[0]` 硬编码；Decision 在 DecisionLog 独立存储，`selects` 边注册了但全 core 从未写入，两端闭合不了。
3. **Method Selection→Model Instantiation — FAIL**。无任何代码把方法卡实例化为变量/方程/约束；`model` artifact 只是指针，`do_model_construction`（`handlers.py:257-280`）只登记假设；MODEL_IR 无 builder/构造函数/写入路径，零 runtime 集成。
4. **Execution Success≠Model Correctness — PARTIAL**。正面保障真（`validation.py` 三状态铁律、`check_fidelity` 对非 success 返回 unverifiable，`fidelity.py:129-135`）；负面拦截缺——默认管线不执行→result 恒 `not_executed`→evidence_gate 只查边→占位 claim PASS，没有任何代码把"没有执行/没有数值"挡在论文门外。
5. **Revision 闭环 M1→E1→V1 FAIL→M2 — PARTIAL**。引擎 retry/on_fail/rollback、`session.invalidate/rerun`、superseded 生命周期、runs parent 链真实且测试 demonstrated；但默认 V3 管线零 FAIL，执行失败仍 PASS（`handlers.py:452-454`），VR failed/invalid 不被 DAG 读取，"V1 FAIL→M2"无端到端自动触发，实际依赖人工 invalidate/rerun 或测试注入 FAIL。
6. **Evidence 谱系链（implemented_by/executed_by/produces/supports 全通）— FAIL**。四条链仅 `result→supports→claim` 通；`implemented_by` 零写入；`code.executed_by→execution_result` 不存在（实际 `result→execution_result`）；`execution_result.produces→result` 不存在（execution_result 无出边）。

---

## Top 10 缺口排序（按阻断闭环程度降序）

| # | 缺口 | 影响环节 | 修复难度 |
|---|---|---|---|
| 1 | MODEL_IR 零 runtime 集成（无 builder/构造函数/写入路径，`model` artifact 只是指针） | 5/6/7 | L |
| 2 | Model Construction 环节（`handlers.py:257-280`）只登记假设，无 instantiation 步骤 | 6 | M |
| 3 | DAG 无 code 节点 + orchestrator 不接 adapter + planner 不产 code（`plan["code"]` 死代码路径） | 7/8 | M |
| 4 | DecisionLog 与 Registry 双存储，`decision→selects→model` 边全 core 零写入 | 5/10 | M |
| 5 | Candidate Model 非一等对象（无 artifact/持久化/Graph 边），选型 `chosen=recs[0]` 硬编码 | 4/5 | M |
| 6 | `evidence_gate` 假门禁：只查边不查数值，占位 claim 链可 PASS（claims_supported=2, coverage=1.0） | 9/10 | S |
| 7 | 执行失败仍返回 PASS（`handlers.py:452-454`）+ VR 不被 DAG 消费 → E/V 失败无法触发反馈 | 8/9/11 | M |
| 8 | `implemented_by` 零写入 + `executed_by`/`produces` 边方向与假设链不符，execution_result 无出边 | 7/10 | S |
| 9 | `register_external_artifact` 承诺不存在 + result 恒 `not_executed`（默认 run 零数值） | 8 | S |
| 10 | validator 挂钩未接线（`session.py:84-88` 不传 validators）+ 假设校验空转（`handlers.py:294-299`） | 9 | S |

> 说明：其余显著缺口（L0–L4 五层体系缺失、feasibility/residual/stability/domain 零实现、19 卡 vs 18 族不对齐、revision/supersedes 边缺失、environment_hash 浅指纹、EXEC 无 schema 门禁等）已并入上方占位清单，其修复难度多为 M/L，按 P1–P4 分期承接。
