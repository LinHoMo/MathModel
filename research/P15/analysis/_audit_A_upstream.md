# Model Construction Gap Audit — 上游半段（环节 1–6）

- 审计对象：`C:\Users\Lin\Desktop\Programs\MathModel` @ HEAD `4c80914`（只读审计，未改动任何仓库文件）
- 审计范围：环节1 Problem/Question → 环节6 MODEL_IR，逐环节回答 10 问
- 方法：逐文件读源码 + grep 调用点 + 读测试断言；只引用可指到 `file:line` / 函数签名的证据；无证据处明确标注 `not found / not demonstrated`
- 运行平台：Windows，`py -3.12`（未执行全量 pytest）

---

## 环节1 Problem / Question

1. **真实存在的代码**：`core/runtime/execution/session.py:78-83`（Question 预登记，`registry.create("question", title=q, activate=True, created_by="session")`）；`core/runtime/execution/handlers.py:178-188`（`DefaultNodeExecutor.do_problem_analysis`：登记 Problem artifact + `motivates` 边）。调用链：`RuntimeSession.__init__` → 预登记 Q → `WorkflowEngine/WaveExecutor` 按 DAG 执行 → `do_problem_analysis`。
2. **入口函数**：`RuntimeSession.__init__`（`session.py:47`，`questions: list[str]` 由调用方传入）与 `do_problem_analysis`（`handlers.py:178`）。
3. **真实输入**：`questions: list[str]` —— 只是 **Q 标签字符串**（如 `"Q001"`），不是题面文本/结构。Problem artifact 的 title 取 `features.get("problem_title", "赛题")`（`handlers.py:181`，缺省硬编码 `"赛题"`）。
4. **真实输出**：Registry 中一个 `problem` artifact（P001）+ N 个 `question` artifact（Q001…），以及 `problem -motivates-> question` 边（`handlers.py:185-186`）。无题面内容、无子问题分解、无 `question_spec` 结构（`core/schemas/question_spec.schema.json` 存在但 runtime 无消费点，`not demonstrated`）。
5. **是否真的执行**：**demonstrated**。`tests/integration/test_runtime_session.py:29-47` 端到端跑通，断言 `{"problem","question",...} <= types`、`motivates in relations`。
6. **是否进入 Artifact Registry**：**是**。`registry.create("problem"|"question", ...)`（`handlers.py:181`、`session.py:81`），`checkpoint()` 落盘 `state/registry.json`（`session.py:143-150`）。
7. **是否进入 Evidence Graph**：**是**，边类型 `motivates`（`handlers.py:185-186`；关系注册见 `evidence_graph.py:34`）。
8. **闭环/回退路径**：Problem/Question 无失败回退（`do_problem_analysis` 恒 PASS）；Question 失效时 `session.invalidate()` 全图重置（`session.py:224-227`）。分析层面无"回到 Model 层"的路径，因为该环节本身不产生模型。
9. **假实现/占位**：Question 只是标签（无题面存储）；Problem title 缺省 `"赛题"`（`handlers.py:181`）。`question_spec.schema.json`（L1 契约）无人消费。
10. **距真实 Model Construction 的差距**：没有"题面文本 → 结构化 Problem/Question"的解析环节；Q 是外部传入的标签，P 是空壳 artifact。真正的问题本体只在 legacy `inputs/` 与 `problem_cards/` 里，V3 runtime 不读。

---

## 环节2 Problem Analysis（features / representation）

1. **真实存在的代码**：`core/runtime/execution/handlers.py:52-62`（`features_for`：全局 features 与 `features["per_question"][qid]` 合并）；`core/runtime/tools/orchestrator.py:349-368`（`_load_problem_features`：从 `<project>/problem_features.json` 或 `<project>/inputs/problem_features.json` 读 features）；`core/runtime/knowledge/intelligence.py:27-56`（`ProblemProfile` dataclass + `as_features()`，**但 runtime handlers 不使用它**）。features 消费者：`KnowledgeRetriever.recommend`（`retriever.py:162-237`）。
2. **入口函数**：`orchestrator._load_problem_features`（`orchestrator.py:349`）→ `RuntimeSession(features=...)`（`session.py:48`）→ `DefaultNodeExecutor` 存为 `self.features`（`handlers.py:82`）。
3. **真实输入**：外部 JSON 文件，键为 `problem_types/has_data/sample_size/time_series/objectives/uncertainty`（`retriever.py:165-178` 文档化）＋ `_capability_match` 消费的 `high_dimensional/nonlinear/interpretability_required/mechanism_known`（`retriever.py:331-348`）。
4. **真实输出**：排序后的 `Recommendation` 列表（`retriever.py:224-234`）。无独立 features artifact；features 只是内存 dict。
5. **是否真的执行**：**demonstrated**（检索打分有大量单元测试，`tests/unit/test_method_cards.py`、`tests/unit/test_competition_intelligence.py`；`knowledge.py recommend` CLI 可独立运行）。但"从问题文本提取 features"这一步 **not found** —— features 是外部文件/调用方提供，或回退 `_LEGACY` 默认（`handlers.py:80-81`：`{"problem_types":["evaluation"],"has_data":True,"sample_size":"medium","_features_source":"legacy_default"}`）。
6. **是否进入 Artifact Registry**：**否**。features 不进 Registry（`ProblemProfile` 不是 artifact 类型，`ids.py:19-37` 无此型）。
7. **是否进入 Evidence Graph**：**否**，无对应边。
8. **闭环/回退路径**：无 features 时回退 `_LEGACY` 并显式打 `_features_source=legacy_default` 标记（`handlers.py:80-81`、`orchestrator.py:384-389`）——诚实的回退，但回退内容本身是硬编码画像。
9. **假实现/占位**：`_LEGACY` 硬编码默认画像（`handlers.py:80-81`）；`ProblemProfile` 的默认值 `has_data=True, sample_size="medium"`（`intelligence.py:30-31`）可能与真实题不符。
10. **差距**：Problem Analysis 是"外部契约注入"，不是 runtime 内的问题分析能力。`ProblemProfile` 与 `features` dict 两套表示并存（前者未被 runtime 使用），缺少"题面 → 特征"的解析器。

---

## 环节3 Method Recommendation（knowledge.py recommend + knowledge retriever）

1. **真实存在的代码**：`core/tools/knowledge.py`（CLI，`cmd_recommend` `:37`、`main` `:136`）；`core/runtime/knowledge/retriever.py:162-237`（`recommend`）、`:241-319`（`_capability_match`）；`core/runtime/knowledge/cards.py:359-387`（`load_knowledge`，fail-closed 加载 19 张卡 + 失败记忆 + 创新模式）；`core/runtime/knowledge/packs.py:81-94`（Competition Pack）、`:112-172`（冲突检测）；`core/runtime/knowledge/intelligence.py:92-112`（`search_methods/recommend_methods` 包装）。
2. **入口函数**：CLI `cmd_recommend`；runtime 内 `KnowledgeRetriever.recommend(features, top_k)`（`retriever.py:162`）；handler 侧 `do_literature_search`（`handlers.py:190-206`）调用 `self.retriever.recommend(self.features, top_k=3)`。
3. **真实输入**：features dict（见环节2）；知识库 `core/knowledge/methods/cards/*.yaml`（19 张卡）、`failures/`、`patterns/`、`competition/cp-*.yaml`。
4. **真实输出**：`Recommendation[]`（含 `score/score_detail/matched/violations/risks/required_experiments/knowledge_refs`，`retriever.py:51-112`）。CLI 打印人类可读建议包。
5. **是否真的执行**：**demonstrated**。打分规则全显式（`retriever.py:7-16` 注释），测试覆盖推荐排序/排除（`test_competition_intelligence.py`、`test_method_cards.py`）。
6. **是否进入 Artifact Registry**：**是（间接）**。`do_literature_search` 把 top-3 建议写成 `decision` artifact（title="文献检索与证据提取"，`handlers.py:196-201`）。但检索本身（Recommendation 对象）不落 Registry。
7. **是否进入 Evidence Graph**：**是**，`decision -based_on-> problem`（`handlers.py:202-203`）。
8. **闭环/回退路径**：`recommend` 无候选时 `do_literature_search` 仍 PASS（空列表也登记 decision）；真正的失败门在 `do_model_selection`（`SelectionError` → FAIL，`handlers.py:169-170`）。方法推荐本身没有"回到 Model 层"的迭代环。
9. **假实现/占位**：`model_families.yaml`（18 canonical families）中大量 family `cards: []`（如 `markov_decision_process`、`ode_models`、`game_theory`、`graph_algorithm`、`kinematic_geometry`、`simulation` 等，`model_families.yaml:36,54,116,125,166,175`）——这些族无法被 `recommend` 推荐出来（无卡即无候选），词表与卡库不对齐。`recommend` 只返回 `score>0` 的卡（`retriever.py:220`）。
10. **差距**：推荐是"卡库内匹配"，不是"建模方法空间"的推荐；知识覆盖 = 19 张卡，距离 18-family 全覆盖差距明显；`literature_search` 的 workflow 声明输出 `state/literature_evidence.json`（`core/workflows/stages/problem-analysis.yaml:16`）与真实输出（decision artifact）不一致。

---

## 环节4 Candidate Models

1. **真实存在的代码**：`core/runtime/modeling/candidates.py`（`Candidate` `:58-97`、`InnovationCandidate` `:26-55`、`CandidateArena` `:100-239`：`generate_candidates` `:110`、`rank` `:237`）。runtime 接线：`handlers.py:94`（`CandidateArena(self.retriever, _pack)`）、`handlers.py:244-247`（`do_model_selection` 内生成候选并存入 `self.shared[qid]["candidates"]`）。
2. **入口函数**：`CandidateArena.generate_candidates(question, features, recs, top_cards=2)`（`candidates.py:110`）；消费方 `do_experiment_design` 经 `self.shared[qid]["candidates"]` 读取（`handlers.py:313-324`）。
3. **真实输入**：`recs`（来自 `recommend_methods`，`intelligence.py:116`）或内部再检索（`candidates.py:113`）；`features`；`pack`（只读打分）。
4. **真实输出**：`list[Candidate]`，每个含 `candidate_id/kind(baseline|improved|hybrid|innovation)/composition/base_card/rationale/score/risks/required_experiments/innovations/knowledge_refs`（`candidates.py:73-87`）。**候选永不落 Registry/Graph**，只存在于 `DefaultNodeExecutor.shared` 内存 dict（`handlers.py:96,245-246`）；崩溃即丢（`model.data.shortlist` 持久化了，`candidates` 没有）。
5. **是否真的执行**：**demonstrated**（确定性生成逻辑 + `tests/unit/test_competition_intelligence.py` 覆盖 `generate_candidates/rank_candidates`）；`test_runtime_session.py` 端到端跑时也会生成候选。
6. **是否进入 Artifact Registry**：**否**。`ids.py:19-37` 无 `candidate` artifact 类型；没有 `registry.create("candidate", ...)` 调用。
7. **是否进入 Evidence Graph**：**否**。
8. **闭环/回退路径**：候选生成失败被 `except Exception` 吞掉并写入 `shared[qid]["candidates_error"]`（`handlers.py:247-248`）——降级但不持久、不阻断，`experiment_design` 回退到 `shortlist` 直接规划（`handlers.py:344-350`）。候选集没有"评审→淘汰→重生成"的闭环。
9. **假实现/占位**：候选分数是**确定性启发式拼接**（`candidates.py:147,163,184-190`：`main.score + 2`、`max-2`、`+{high:6,...}-{high:4,...}`），不是任何模型/证据的估计；`_CANDIDATE_SEQ` 是模块级全局计数器（`candidates.py:23`），非会话隔离；innovation 候选永远 `status="hypothesis"`（`candidates.py:42,233`），且一个 batch 只保留第一个 pattern（`candidates.py:201` `break`）。
10. **差距**：候选集存在但**不是一等对象**（无 artifact、无持久化、无 graph 边），"baseline/improved/hybrid/innovation"四型候选只服务实验计划生成，不参与选型（选型只看 `recs[0]`，见环节5）。

---

## 环节5 Model Selection（Decision artifact，alternatives/criteria/evidence/chosen）

1. **真实存在的代码**：`core/runtime/modeling/selection.py`（`MethodArena` `:40-121`，`select` `:46`）；`core/runtime/decisions/log.py`（`DecisionLog` `:114-279`：`add` `:169`、`invalidate` `:222`、`query` `:256`、`save` `:144`）；handler 接线 `handlers.py:87` + `do_model_selection` `:208-255`；schema `core/schemas/v3/decision/decision.schema.json`；runtime 决策落盘 `projects/<p>/state/decision_log.json`（`session.py:68`）。
2. **入口函数**：`MethodArena.select(question, features, top_k=3, created_by, record=True)`（`selection.py:46`）；handler `do_model_selection` 逐 Q 调用（`handlers.py:214`）。
3. **真实输入**：features dict；`DecisionLog`（可空）；知识库。
4. **真实输出**：`SelectionOutcome{question, features, shortlist, chosen, decision_id, prior_decisions, notes}`（`selection.py:26-37`）。**chosen = `recs[0].card.card_id`（`selection.py:60`）—— 硬编码取检索第一名**，MethodArena 自身不做任何比较；`DecisionLog.add` 登记 `alternatives`（落选者 + 理由）、`criteria`（固定四词：检索得分/适用条件匹配/验证代价/历史决策一致性，`selection.py:96-97`）、`reasoning`、`confidence`（`0.5+0.1*score`，`selection.py:100`）。
5. **是否真的执行**：**demonstrated**。`tests/unit/test_model_selection.py:33-85` 断言 `chosen.startswith("mc-")`、`alternatives>=1`、`decision_id=="D001"`、旧决策自动 invalidated；`test_decision_log.py` 全行为覆盖。
6. **是否进入 Artifact Registry**：**部分**。选型 Decision 进入 **DecisionLog（独立文件 decision_log.json）**，**不是 Registry 的 decision artifact**；Registry 里的 `decision` 类型只被 `do_literature_search`（`handlers.py:196`）与 `do_experiment_design`（`handlers.py:336`）使用。选型同时把 `model` artifact 写入 Registry（`handlers.py:231-238`，`data={card_id, family, shortlist}`）。
7. **是否进入 Evidence Graph**：**关键缺口**。`selects` 边已注册（`evidence_graph.py:45` `"selects": ({"decision"}, {"model"})`；`:79` 传播档 `(None,None)`），但 **core 中没有任何 `add_relation(..., "selects", ...)` 调用**（grep 全 core 仅 `evidence_graph.py` 自身注册表与 docstring）。`do_model_selection` 只写 `solved_by`（`handlers.py:240`）。原因结构性成立：`selects` 要求 from 是 **Registry 的 decision artifact**，而选型决策存在 **DecisionLog**（非 artifact），两端无法闭合。
8. **闭环/回退路径**：`do_model_selection` 无 `on_fail`（workflow `modeling.yaml:7-12`）；`SelectionError` → FAIL 走引擎重试（`handlers.py:169-170`）；`session.invalidate` 对 model/assumption 失效时 `reset_to("model_selection")`（`session.py:227-228`）。历史决策冲突只产生 note（`selection.py:77-84`），不阻断；旧选型被新选型自动 `invalidate`（`selection.py:113-120`）。
9. **假实现/占位**：`chosen=recs[0]`（`selection.py:60`）即"直接选第一个"；`criteria` 是固定字符串数组非真实评估；`confidence` 是线性启发；`evidence_ids=[]`（`selection.py:103`）——决策无证据绑定；`reasoning` 回退 `top.reasoning() or f"{name} 得分最高"`（`selection.py:98-99`）。
10. **差距**：选型 = 检索排序 + 登记，没有"候选集 + alternatives/criteria/evidence/chosen"的真正比较决策；Decision 实体与 Registry/Graph 脱节（DecisionLog 与 Registry 是两套存储），`decision→selects→model` 链从未落地。

---

## 环节6 MODEL_IR

1. **真实存在的代码**：**不在 core runtime**。`research/P15/model_representation/model_ir.schema.json`（v1.0，18 个 required 顶层字段：`ir_version/model_id/model_family/problem_binding/assumptions/variables/parameters/objectives/constraints/mechanisms/equations/dependencies/solvers/experiments/validations/claims/model_graph`，`model_ir.schema.json:7-25`）；`research/P15/model_representation/example_2024_A.json`（手工填写的完整实例，含 5 假设/变量/目标/约束/机理/方程/依赖/solver/实验/验证/claim/图，非模板）；`validate_example.py`、`run_deterministic_checks.py`（独立校验脚本，**硬编码本机绝对路径** `validate_example.py:7-8`，依赖 `jsonschema` 库）。
2. **入口函数**：无 runtime 入口。仅独立脚本 `validate_example.py` 主流程。grep 全 core：**`model_ir` / `MODEL_IR` / `ModelIR` 零命中**（仅 catalog 注释与文档提及）。
3. **真实输入**：JSON 实例文件。
4. **真实输出**：校验通过/失败打印。
5. **是否真的执行**：**contract/script exists, runtime not demonstrated**。脚本可独立运行，但无任何 pipeline 调用点；与 `core/runtime`（零第三方依赖）无集成。
6. **是否进入 Artifact Registry**：**否**。`model` artifact 的 `data` 只有 `{card_id, family, shortlist}`（`handlers.py:235-237`），无 MODEL_IR 字段。
7. **是否进入 Evidence Graph**：**否**（MODEL_IR 的 model_graph 是文件内图，与 `evidence_graph.json` 无关）。
8. **闭环/回退路径**：无（MODEL_IR 不在闭环内）。
9. **假实现/占位**：MODEL_IR 本体是研究期产物；`docs/REPOSITORY_AUDIT/STRUCTURE_NAMING_PROPOSAL.md:36,99` 曾记载 `research/P15/model_representation/` 为空、规范未落盘——现已落盘但未进 runtime。`model` artifact = 方法卡指针（stub），不是模型实例。
10. **差距**：**没有 MODEL_IR builder/constructor，也没有 LLM→JSON 的结构化出口**。距离"Model Construction 产出 MODEL_IR"还差：① schema 进 `core/schemas/`；② 结构化构造函数（候选/选型 → 变量/目标/约束/方程实例化）；③ `model` artifact 挂载 MODEL_IR payload；④ 校验器接入 `validate.py`。目前 runtime 的 `model` 只是"选了哪张卡"。

---

## 上游关键检查点结论

### 检查点1：Candidate Model Set —— "单模型"还是"候选集 + Decision(alternatives/criteria/evidence/chosen)"？

- **候选集存在但非一等对象**：`CandidateArena.generate_candidates` 真实生成 baseline/improved/hybrid/innovation 四型候选（`candidates.py:110-217`），但只进内存 `self.shared[qid]["candidates"]`（`handlers.py:245-246`），**无 artifact 类型（`ids.py:19-37`）、无 Registry、无 Graph 边、不持久化**。
- **选型是"单模型"**：`MethodArena.select` 的 `chosen=recs[0].card.card_id`（`selection.py:60`）——候选集不参与选型，选型直接取检索第一名；`CandidateArena` 生成的四型候选仅被 `do_experiment_design` 消费来生成实验计划（`handlers.py:313-324`）。
- **Decision(alternatives/criteria/evidence/chosen) 存在但残缺**：`DecisionLog.add` 写入 alternatives/criteria/reasoning/confidence（`selection.py:89-109`），**criteria 是固定四词字符串、evidence_ids 恒空**（`selection.py:96-97,103`），且决策实体在 DecisionLog（独立存储），不是 Registry decision artifact。

### 检查点2：Method Selection → Model Instantiation —— 真实存在吗？

- **不存在"Problem features → candidate methods → structural compatibility → candidate models → instantiate MODEL_IR"链**。
- 实际链是：features → `recommend`（`retriever.py:162`）→ `chosen=recs[0]`（`selection.py:60`）→ 创建 `model` artifact（`data={card_id, family, shortlist}`，`handlers.py:231-238`）→ `do_model_construction` **只登记假设**（`handlers.py:257-280`，`assumes` 边）。
- **没有 instantiation 步骤**：无任何代码把方法卡实例化为变量/方程/约束（`core/runtime/modeling/` 下仅 selection/planner/candidates 三个模块，无 builder）。workflow `modeling.yaml:13-18` 声称 model_construction"建立数学模型（公式/符号/边界）+ 模型依赖 DAG"，与实际 handler（仅假设登记）**不符**。

### 检查点3：MODEL_IR —— schema 字段、builder、生成方式？

- schema 字段：18 个 required 顶层字段（`model_ir.schema.json:7-25`），含 assumptions/variables/parameters/objectives/constraints/mechanisms/equations/dependencies/solvers/experiments/validations/claims/model_graph/modeling_trace。
- **builder/constructor：not found**（core 无任何 MODEL_IR 构造代码）。
- **生成方式：既不是 LLM 直接吐 JSON（无该路径），也没有结构化构造函数（无该路径）**。只有研究目录里的手工 example（`example_2024_A.json`）+ 独立校验脚本（`validate_example.py`）。`model` artifact 的 data 不含 MODEL_IR 任何字段（`handlers.py:235-237`）。

### 检查点4：Decision artifact —— `decision→selects→model` 边真实注册并写入吗？log.py 是真写还是占位？

- **边注册：真**。`"selects": ({"decision"}, {"model"})`（`evidence_graph.py:45`），强边集合含 selects（`:54`），传播档 `(None,None)`（`:79`）。
- **边写入：从未**。全 core grep：`add_relation` 调用仅 6 处（`convert.py:75,98`、`handlers.py:503`、`session.py:95`、`codegen.py:128`、`validation.py:217`），**无一处 `selects`**。端到端测试断言的 relations 集合也不含 selects（`test_runtime_session.py:44-47`：motivates/solved_by/assumes/validated_by/produces/visualized_by/supports/appears_in）。
- **`log.py` 是真写**：`DecisionLog.add/invalidate/query/save` 全实现（`log.py:144-279`），原子写落盘 `decision_log.json`，`test_decision_log.py` 全面覆盖。**但它是独立于 Registry/Graph 的存储**——DecisionLog 的决策 ID（`D001`）不是 Registry artifact ID，因此 `selects`（要求 from 是 registry decision artifact，`evidence_graph.py:177-188`）在结构上写不出来。

---

## 上游假实现/占位清单

1. **`handlers.py:80-81`** — `_LEGACY` 硬编码 features 默认值（`problem_types=["evaluation"]`…），显式打 `_features_source=legacy_default` 标记但仍是"假分析"。
2. **`handlers.py:181`** — Problem title 缺省 `"赛题"` 硬编码。
3. **`handlers.py:231-238`** — `model` artifact = 方法卡指针 stub（`data={card_id, family, shortlist}`），无模型内容；**这是 runtime 里唯一的"Model 实例"**。
4. **`handlers.py:257-280`** — `do_model_construction` 只是登记假设，不构建模型；与 workflow 声明（公式/符号/边界 + 模型 DAG）不符。
5. **`handlers.py:272`** — 无风险时硬编码假设文案 `"所选方法的前提条件成立（数据规模/类型/独立性）"`。
6. **`handlers.py:428-434`** — `result` artifact `data.status="not_executed"` 占位（注明须由外部 executor 回填）。
7. **`handlers.py:569-578`** — **claim 占位 `data={"statement": f"{qid} 结论", ..., "placeholder": True}`**（用户点名的 `"{qid} 结论"` 占位）。
8. **`selection.py:60`** — `chosen=recs[0].card.card_id` 直接选第一名（无比较）。
9. **`selection.py:96-97,103`** — `criteria` 固定四词、`evidence_ids=[]` 恒空。
10. **`candidates.py:147,163,184-190`** — 候选分数为启发式加减（`+2`/`max-2`/`+{high:6,...}`），非证据估计。
11. **`planner.py:150`** — 基线文案 `"朴素基线（均值/最近值/穷举小规模等同口径对照）"` 硬编码；`DecisionRule` 的 `accept_if="criteria_pass"` 等为占位字符串（`planner.py:180-181,241-242`）。
12. **`intelligence.py:161`** — `build_experiment_plan` 取 `cands[0]`（排名第一），无选择依据。
13. **`handlers.py:247-248`** — 候选生成异常被 `except Exception` 吞掉，仅写内存 `candidates_error`，不持久不告警。
14. **MODEL_IR（环节6）** — 研究期产物，schema/example/校验脚本齐全但零 runtime 集成；`validate_example.py:7-8` 硬编码本机绝对路径。
15. **`model_families.yaml`** — 18 个 canonical family 中 10+ 个 `cards: []`，词表与卡库不对齐（`model_families.yaml:36,54,62,89,116,125,141,153,166,175,183`）。
16. **`session.py:68` vs `log.py:6-7`** — DecisionLog 文档写 `decisions.json`，实际路径 `decision_log.json`（轻微 doc mismatch）。
17. **`engine.py:45-53,169-178`** — validator 挂钩存在，但 `RuntimeSession` 不传 `validators`（`session.py:84-88`），catalog/v3.yaml 声明的 skill validator（`model-critic` 等）未在引擎层执行（handler 内确定性检查兜底）。

---

## 附录：上游各环节"真/假"速览

| 环节 | 有真实代码 | 已执行(demonstrated) | 进 Registry | 进 Evidence Graph | 假实现/占位 |
|---|---|---|---|---|---|
| 1 Problem/Question | ✅ | ✅ (e2e) | ✅ P/Q | ✅ motivates | 标签化，无题面 |
| 2 Problem Analysis | ✅ | ✅ (打分) | ❌ | ❌ | `_LEGACY` 回退/外部注入 |
| 3 Method Recommendation | ✅ | ✅ | ✅(decision) | ✅ based_on | 19 卡 vs 18 族不对齐 |
| 4 Candidate Models | ✅ | ✅ | ❌ | ❌ | 内存对象+启发式分数 |
| 5 Model Selection | ✅ | ✅ | 部分(model) / DecisionLog | ❌ selects 从未写 | top-1 硬编码 |
| 6 MODEL_IR | 仅 research/ | ❌ runtime | ❌ | ❌ | 无 builder |

关键证据文件索引：`handlers.py`（节点接线）、`session.py`（会话/落盘）、`selection.py`/`candidates.py`/`planner.py`（modeling 三件套）、`retriever.py`/`cards.py`/`intelligence.py`（knowledge 层）、`evidence_graph.py`（边注册表）、`log.py`（DecisionLog）、`model_ir.schema.json`（研究期 MODEL_IR）。
