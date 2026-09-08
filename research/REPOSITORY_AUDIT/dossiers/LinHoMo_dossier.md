# LinHoMo / MathModel — 证据级深度技术审计档案

> 审计对象：`C:\Users\Lin\Desktop\Programs\MathModel`（本地权威副本，GitHub 可能滞后，最近 push `de15d96`，以本地为准）
> 审计日期：2026-09-08 ｜ 审计人：MainAgent（三仓库对比审计之 LinHoMo 卷）
> 方法：本地 Read/Grep/Glob 直读源码 + 运行工具内省 + P15-K001 实验档案引用。全部关键判断标注证据分级：
> **IMPLEMENTED**（代码有真实 runtime 路径/测试证据）｜**CONTRACT_ONLY**（有 schema/interface，无 runtime 执行证据）｜**DOC_CLAIM**（文档声称，代码证据不足）｜**INSTRUCTIONAL**（仅 prompt/skill 文本要求，无机械强制）

---

## 1. 仓库概览

### 1.1 定位

MathModel（LinHoMo）是一个面向**数学模型构建、验证与"模型→论文"传输**的"可信 Harness（马具/夹具）"。核心叙事是：**Agent / LLM 只是 Executor，状态真源是 Artifact Registry + Evidence Graph + Research State**（`AGENTS.md`）。仓库自述为"V3 认知工作流运行时 + V2 四手 29 agent 兼容层"。

### 1.2 规模（实测）

| 项 | 数值 | 证据 |
|---|---|---|
| `core/` Python 源码行数 | **36,144 行**（递归全量） | `(Get-ChildItem core -Recurse -Filter *.py \| Get-Content \| Measure-Object -Line).Lines` |
| `tests/` 测试行数 | **9,203 行** | 同上 |
| 方法卡数量 | **19 张**（`core/knowledge/methods/cards/*.yaml`） | 目录列出 mc-ahp … mc-xgboost |
| 校验模块 | **21 个**（`core/validators/modules/`） | symbol_registry / formula_checker / hash_chain / type_system … |
| pytest 基线 | **774 passed / 11 skipped**（任务给定工程验证事实） | 工程验证章节 |
| catalog 一致性 | `catalog_check.py --check` OK（任务给定） | 工程验证章节 |

### 1.3 五层目录结构（AGENTS.md 定义）

| 层 | 位置 | 实测内容 |
|---|---|---|
| product | `core/` | runtime / roles / workflows / validators / schemas / evaluation / tools / skills / knowledge / env / templates / adapters |
| legacy | `core/legacy/hands/` | Modeler(8) / Programmer(6) / Writer(7) / Reviewer(8) = 29 agents（实测目录确认 8+6 名） |
| benchmark | `core/tools/evaluation/` | 评分链 / 五维评分卡 |
| research | `research/` | P13-3D 系列、P15-K001、REPOSITORY_AUDIT |
| instance | `projects/` | 用户运行实例（仅 `new_project.py` 创建） |

### 1.4 技术栈

- Python 3.12（Windows 本机 `py -3.12`，AGENTS.md 明确 3.14/3.13 安装损坏）
- YAML/JSON schema（JSON Schema 校验、YAML 方法卡）
- 零第三方运行时依赖（核心 runtime 为纯 stdlib 确定性 Python；`matplotlib` 仅用于 diagram_gen）
- LaTeX（11 套竞赛模板：cumcm/mcm/apmcm/diangong/huashu/huawei/mathorcup/renzhengbei/shuweibei/antipatterns）
- **无 LLM SDK 依赖**（见 §2.8）

### 1.5 V3 runtime vs V2 legacy 兼容层实际状态

- **V3 运行时**：`core/runtime/`（execution / artifacts / graph / state / modeling / knowledge / synthesis / writing / legacy / decisions），已冻结（THREE_LAYER_ARCHITECTURE "Research Runtime 冻结"）。**默认模式**：`orchestrator.py` 默认即 V3 DAG 干跑。
- **V2 legacy**：`core/legacy/hands/*/agents/*/SKILL.md`（29 个指令文件）+ `state.py` 推进 + `gate.py` 门禁，标注"只读兼容不新增"，但 `orchestrator.py --legacy` 仍可一键执行 29 步流水线（见 §2.7）。
- **状态桥**：`core/tools/state.py` 的 `cmd_v3` → `runtime/legacy/convert.py`（V2 产物 → V3 artifact/evidence 导入）。

### 1.6 最近 commit（实测 `git log`）

本地最近提交（含 `de15d96` 及之后）以 P15-K001 冻结、HARDENING P0–P6、STATE_TRUTH、P13-3D 系列为主；`git status` 无未提交污染（本次审计不修改任何源码）。

---

## 2. 真实 Runtime Pipeline 重建

### 2.1 入口协议（AGENTS.md 五步，全部 IMPLEMENTED）

```
1. 读状态    python core/tools/state.py <项目> status
2. 看计划    python core/tools/orchestrator.py <项目>          # V3 DAG 干跑
3. 执行      python core/tools/orchestrator.py <项目> --execute  # RuntimeSession
4. 对账      python core/tools/state.py <项目> reconcile
5. 门禁      python core/tools/validate.py                     # 57 项
```

### 2.2 用户输入一道题后，V3 模式的逐环节真实执行链

以 `RuntimeSession(project_dir, questions, features, ...)`（`core/runtime/execution/session.py`）为准：

| # | 环节 | 谁做（代码路径） | 产物 | 类型标注 |
|---|---|---|---|---|
| 1 | DAG 生成 | `WorkflowComposer(REPO/"core"/"workflows").compose_executable(questions)`（session.py:66） | executable DAG（按 question 展开 `problem_analysis_Qi` 等节点） | Python function call → workflow state |
| 2 | 预登记问题 | `registry.create("question", ...)`（session.py:74-78） | Question Artifact（ID Q001…） | filesystem artifact |
| 3 | 波次执行 | `WaveExecutor(dag, DefaultNodeExecutor, max_workers=1)`（session.py:81） | 节点 NodeResult | Python function call |
| 4 | 节点处理器 | `DefaultNodeExecutor.do_<node>`（`core/runtime/execution/handlers.py`） | Artifact / Evidence | Python function call |
| 5 | 证据登记 | `_register_evidence` → `graph.add_relation(rel["from"], rel["relation"], rel["to"])`（session.py:85-93） | Evidence Graph 边 | Python function call → graph state |
| 6 | 落盘 | `checkpoint()` = registry.save → graph.save → decisions.save → `state.refresh_from` → state.save（session.py:138-145） | 4 个状态文件原子写 | filesystem artifact |
| 7 | RunRecord | `emit_run_record`（session.py:108-129，best-effort 不阻断） | run record | filesystem artifact |
| 8 | 项目门禁 | `python core/tools/validate.py` | 57 项校验报告 | CLI |

### 2.3 逐问"谁理解题目/判定类型/生成候选/选择/构造/写码/跑实验/验证/找错/改错/评价/写论文"

**关键前置事实**：V3 默认执行器 `DefaultNodeExecutor` **是零 LLM 的确定性节点执行器**（orchestrator.py 文档字符串原文："默认确定性节点执行器（零 LLM）：知识检索 → 方法竞技场 → 实验规划 → 实验/结果登记 → 证据门禁 → 研究叙事 → 论文投影 → 判审"）。因此以下"谁"的答案在 V3 模式下基本都是**默认参数 + 台账登记**，真实认知发生在**外部 Agent**（见 §2.8）。

| 认知环节 | V3 零 LLM 执行器实际行为 | legacy 29-agent 对应 | 证据分级 |
|---|---|---|---|
| 谁理解题目 | **没有**。`do_problem_analysis` 用 `self.features.get("problem_title", qid)` 创建 problem artifact（handlers.py:173-176）；特征来自外部传入 `features`，**默认硬编码 `{"problem_types": ["evaluation"], "has_data": True, "sample_size": "medium"}`**（handlers.py:75-76） | problem-parser（INSTRUCTIONAL：外部 agent 读题面写 question_spec.json） | IMPLEMENTED（默认值）+ INSTRUCTIONAL（真理解靠外部） |
| 谁判定类型 | **没有**。直接进入 `do_model_selection`，用 `features` 喂 `retriever.recommend(features, top_k=3)`（handlers.py:187）；类型判定是 external features 的输入契约 | type-classifier（INSTRUCTIONAL） | IMPLEMENTED（检索）+ INSTRUCTIONAL（类型判定） |
| 谁生成候选 | `MethodArena`（`core/runtime/modeling/selection.py`）：基于 features 对知识卡打分排序，产出 shortlist | method-matcher（INSTRUCTIONAL，要求 ≥2 候选 + 五维评分） | IMPLEMENTED（V3）/ INSTRUCTIONAL（legacy） |
| 谁选择 | `do_model_selection` 取 arena 结果创建 model artifact：`registry.create("model", title=card.get("name"), data={"card_id":…, "family":…, "shortlist":…})`（handlers.py:203-…）——**只登记选择结果，不含模型本体** | method-matcher 五维评分 `fivedim_score` 取最高 | IMPLEMENTED |
| 谁构造模型 | **没有**。`do_model_construction` 仅把卡片的 `risks` 转成 assumptions artifact（"将选中卡的 risks 转 assumptions"），不产生任何公式/方程/约束 | model-builder（INSTRUCTIONAL：Actor-Critic 环写 model_draft.md） | IMPLEMENTED（台账）+ INSTRUCTIONAL（构造） |
| 谁写代码 | **没有**。`do_experiment` 创建 experiment/result/figure 三个 artifact，result 的 claim 语句为字面量 `f"{qid} 结论"`（占位符） | code-implementer（INSTRUCTIONAL） | IMPLEMENTED（占位）+ INSTRUCTIONAL（真写码） |
| 谁跑实验 | **没有计算**。"实验执行（确定性仿真）：E→R→F 证据链"只创建 artifact 链，result 无任何数值（与 §3 Model 无数值一致） | test-runner / result-verifier（门禁只查文件存在 + JSON 合法） | IMPLEMENTED（台账，非计算） |
| 谁验证 | Evidence Gate（`core/validators/evidence/evidence_gate.py`）：E1–E4 检查**结构性**证据边（claim 有 supports 边、experiment 有 produces 边等），**不校验数值正确性** | validate.py 57 项（文件/结构/数值追溯） | IMPLEMENTED（结构门禁） |
| 谁发现错误 | **V3 runtime 无错误发现机制**（门禁只查结构）；错误发现落在外部 LLM/评审（P15 盲评 3 evaluator 发现 FAIL runs） | reviewer 手（scorer-* 8 agents，INSTRUCTIONAL） | 缺失（runtime 层） |
| 谁修改 | `session.invalidate(artifact_id)` → graph 失效传播 → `engine.reset_to(...)`（session.py:191-240）：**只触发节点重跑，不产生新认知** | revision-executor（INSTRUCTIONAL） | IMPLEMENTED（调度）/ INSTRUCTIONAL（修改内容） |
| 谁评价 | 外部（P15 盲评：3 独立 evaluator + 评分标准 rubric） | scorer-academic / scorer-judge 等（INSTRUCTIONAL） | IMPLEMENTED（P15 实验）/ INSTRUCTIONAL（生产路径） |
| 谁写论文 | `PaperProjection.project(narrative)`（`core/runtime/writing/projection.py`）：从 narrative arcs 生成**结构化大纲**（章节/claim/图表归属），不写散文 | writer 手 7 agents（INSTRUCTIONAL 写 paper/main.tex） | IMPLEMENTED（大纲投影）/ INSTRUCTIONAL（正文） |

### 2.4 每个箭头的类型标注（汇总）

- `state.py status` → **CLI → ProjectState 投影读取**
- `orchestrator.py`（默认）→ **CLI → WorkflowComposer 静态 DAG**
- `--execute` → **RuntimeSession.run() → WaveExecutor → DefaultNodeExecutor.do_* → ArtifactRegistry/EvidenceGraph/DecisionLog/ProjectState**
- node → artifact：**filesystem artifact（JSON 原子写）**
- node → evidence：**graph.add_relation（typed edge）**
- PASS 判定：**EvidenceGate 结构校验 + engine validators hook**
- 下游消费：**PaperProjection（narrative → outline）+ validate.py（57 项）**

### 2.5 V2 legacy 29-agent 流水线是否仍可执行？

**是，仍可执行**（IMPLEMENTED）：

- `orchestrator.py --legacy` 一键跑 29 步；
- `state.py <项目> advance <hand> <agent> --output <路径>` 逐步推进；
- `gate.py <项目> <hand> <agent>` 单步门禁，`GATES` 字典覆盖全部 29 agent（实测 modeler 8 个 gate 定义齐全）；
- 门禁性质：**文件存在 + JSON 合法 + schema 校验 + guardrails 文本扫描 + risk_probe**，是机械存在性断言，**不判数学内容正确性**。

### 2.6 core 永久无 LLM 执行器——边界在代码中如何体现

1. **THREE_LAYER_ARCHITECTURE.md**（治理文档）："Agent Brain = `core/<Hand>/agents/*/SKILL.md`（29 agent 指令）+ knowledge 层；Research Runtime 与 Guardrails 全部为确定性 Python（零 LLM 调用）；Brain 的智能由外部 LLM 对话按 SKILL.md 执行。因此让 Brain 变聪明的工作 = 改进指令与知识层 + 用真实赛题测量外部 LLM 在此脚手架上的解题表现。"
2. **RuntimeSession.run_meta**（session.py:56-58）："Hardening P3：外部 executor 溯源（model_provider/model_version/token_cost/decision）；additive，None 时记录为 null"——**"外部 executor" 作为一等概念写入会话**。
3. **P15-K001 run manifest**（`runs/*/manifest.json`）：`"generator": ["claude", "claude-manual", "console"]`，prompt 由 bundle（prompt_bundle_sha256）打包，成本字段 prompt_tokens/completion_tokens/latency——**实验生成侧明确是"人在控制台的 Claude 会话"**。
4. **core 依赖零 LLM SDK**：36k 行 core 无任何 `openai`/`anthropic` import（依赖清单仅 stdlib + matplotlib）。

### 2.7 V3 vs V2 关系总结

V2 legacy 是"外部 agent 按指令产出文件、门禁查文件"的**流程状态机**；V3 是把同一认知过程**骨架化为 artifact/evidence 台账**的**确定性运行时**。V3 不替代 V2 的认知来源，只是把 V2 的产物纳入 Registry/Graph/State 三真源并加失效传播与重放。

---

## 3. "Model" 到底是什么

### 3.1 Artifact Registry 中 Model Artifact 的 schema

- V3 通用 artifact schema：`core/schemas/v3/artifact/artifact.schema.json`。字段为 artifact_id / type / title / status / payload / data / lineage / created_by / activate / tags 等**通用字段，无模型专属字段**。
- "Model" 在 V3 中 = `type: "model"` 的通用 artifact，其数学内容只存在于 `payload`（文件路径）或 `data`（内联 dict）。V3 零 LLM 路径创建的 model artifact 的 `data` 仅含 `{"card_id", "family", "shortlist"}`（handlers.py `do_model_selection`）——**是"选择记录"而非"数学模型对象"**。
- legacy 侧有专门的 `core/schemas/model_spec.schema.json`（MODEL_SPEC：`required = [problem_understanding, assumptions, symbols, models, sub_problems, verification]`）与 `core/schemas/model_artifact.schema.json`（v1 评分契约，见 3.2）。
- P15 实验侧有最丰富的模型表示：`research/P15/model_representation/model_ir.schema.json`（MODEL IR v1.0，见 3.4）。

### 3.2 MODEL_ARTIFACT v1 契约逐字段对照（P13-3C 评分契约，`core/schemas/model_artifact.schema.json`）

| 维度 | schema 字段 | 实测 |
|---|---|---|
| assumptions | `assumptions` | ✅ 有 |
| variables | `variables` | ✅ 有 |
| parameters | `parameters` | ✅ 有 |
| constraints | `constraints` | ✅ 有 |
| objective | `objective` | ✅ 有 |
| mechanism | `mechanism` | ✅ 有 |
| candidate alternatives | `candidate_models` + `selected_model` + `selection_reason` | ✅ 有 |
| uncertainty | `uncertainties` | ✅ 有 |
| sensitivity | `sensitivity_plan` | ✅ 有（**仅计划**，非结果） |
| validation | ❌ 无字段 | 缺失 |
| failure conditions | ❌ 无字段 | 缺失 |
| downstream dependencies | ❌ 无字段（依赖关系在 model_dag.schema.json 承载） | 分离 |

**关键判断**：该 schema 是 **P13-3D/P15 的评分契约**，不是 V3 runtime 的 model artifact 契约。V3 runtime 的 `type:"model"` artifact 不含以上任何字段。

### 3.3 Model 是否 typed object？有哪些 schema？

- legacy：`model_spec.schema.json`（MODEL_SPEC，六段：problem_understanding/assumptions/symbols/models/sub_problems/verification）+ `model_dag.schema.json`（model_dag：问题/子问题/模型/假设/求解节点 + 边，含 `model_dag.svg` 产物要求）。
- V3：**无 typed model**——只有通用 artifact + `data` dict。
- P15：`model_ir.schema.json`（MODEL IR v1.0）是**唯一 typed、可机检的模型对象**，含 `model_family.primary/secondary`、`problem_binding`、`assumptions[]`、`variables[]`、`parameters[]`、`objectives[]`、`constraints[]`、`mechanisms[]`、`equations[]`（LaTeX + derivation_trace）、`dependencies[]`、`solvers[]`、`experiments[]`、`validations[]`、`claims[]`、`model_graph`、`modeling_trace`。

### 3.4 Model 可否：修改/比较/追踪/验证/重放/复用/组合/回滚/failure attribution？

| 能力 | 证据 | 分级 |
|---|---|---|
| 修改 | `RuntimeSession.invalidate()` → 失效传播 → 引擎局部重置（model/assumption → reset_to("model_selection")） | IMPLEMENTED |
| 比较 | P15 实验对候选模型族评分（L2 盲评）；legacy method_candidates 候选对比（INSTRUCTIONAL） | 部分 |
| 追踪 | Artifact lineage（父/子）+ Evidence Graph typed edges（assumes/validates/…）+ run record | IMPLEMENTED |
| 验证 | EvidenceGate 结构校验；validate.py 数值追溯（论文数值必须解析到 validated result artifact） | IMPLEMENTED（结构） |
| 重放 | `core/tools/replay.py`（运行重放/差异归因） | IMPLEMENTED |
| 复用 | Artifact Registry 跨 run 引用（knowledge_root 共享；run_meta._parent_run_id） | IMPLEMENTED（台账层） |
| 组合 | V3 DAG 不支持模型组合原语；`declare_cross_relation` 支持 compares/extends/derived_from（跨问题关系） | 部分 |
| 回滚 | `rerun(node_id)` 重置节点+下游，旧产物 superseded（审计保留） | IMPLEMENTED |
| failure attribution | legacy `core/validators/modules/error_attribution.py`；P15 `FAILURE_TAXONOMY.md`（FM-XX-NNN）；V3 引擎 `failures` 记录 | IMPLEMENTED（legacy/P15）/ CONTRACT_ONLY（V3 归因闭环） |

### 3.5 Model 与论文文字是否解耦？

- **部分解耦**。`PaperProjection.project(narrative)`（projection.py）从 claim→evidence 结构生成大纲：模型章节 = 按 question 的 model + `assumes` 边收集假设（projection.py:32-41）；结果章节 = supported claims + figures（`appears_in` 边回写，未回写标 `pending_placement` 由 narrative-critic 拦截）。死主张（dead arc）**禁止投影**（projection.py:47）。
- `paper/main.tex` 由外部 writer agent 按大纲与 `core/templates/latex/*` 模板撰写；`validate.py` 强制论文数值必须追溯到 `figures/all_results.json`（validated result artifact），禁止论文阶段重估。
- **结论**：论文大纲是 Model/Evidence 的结构投影，正文文字仍是外部 LLM 产物。解耦是"结构性"的，不是"语义性"的。

---

## 4. Model Selection 机制

### 4.1 catalog 中的 model family taxonomy

- `catalog.yaml`（根）：29 legacy agents（hands 节）+ `v3:` 视图。
- `catalog/v3.yaml`：15 节点 + 5 Role（analyst/modeler/experimenter/critic/writer）+ 7 validators（其中 model-critic / experiment-critic 为 `kind: skill` 指向 `core/skills/critics/*/SKILL.md`——**指令型**；evidence-gate / research-quality / narrative-critic / judge-critic / assumption-checker 为 `kind: runtime`）。
- 方法卡 taxonomy：19 张卡的 `family` 字段（实测：dynamic_programming / numerical_pde / queuing_theory / unsupervised / metaheuristics / statistical / optimization…），家族枚举未在 catalog 中统一声明（见 §12）。

### 4.2 method-matcher / knowledge.py recommend 的实际工作方式

- `core/tools/knowledge.py`：CLI 包装，`recommend --types <题型>` → `core/runtime/knowledge/retriever.py`。
- `retriever.recommend(features, top_k)`：基于 `problem_types / has_data / sample_size / time_series / objectives / uncertainty` 六个特征键打分排序（实测读 `core/knowledge/methods/features.yaml` 类型命中权重）。
- **致命边界**：`features` 不自动从题面推导。V3 runtime 默认 `{"problem_types": ["evaluation"]}`（handlers.py:75-76）——**任何题默认按"评价类"检索**，除非外部传入 features。`features_for()`（handlers.py:52-62）只做 per-question 键覆盖，不做特征提取。
- legacy method-matcher（INSTRUCTIONAL）：要求每子问题 ≥2 候选（env `modeling.min_candidate_models`=2）、五维评分（假设30%/结构25%/变量20%/动力15%/可解10%，fivedim_score）、避档检查（AHP/灰色预测/模糊评价）、风险探针（P2-3，`work/risk_probe.json`，verdict=pass 才可进编码，gate 强制 `check_risk_probe`）。

### 4.3 是否有 candidate generation / suitability analysis / decision rules？

- **V3**：`MethodArena`（selection.py）= candidate generation（从知识库 top-k）+ suitability（卡内 scoring 字段）；decision rule = 取 arena 排序第一。**决策依据是 features 而非题面文本**。
- **legacy**：candidate generation + 五维 suitability + decision rule（加权总分最高，差距<0.5 进双候选）——全部 INSTRUCTIONAL，由外部 agent 执行，gate 只查产物结构。

### 4.4 allowed_modeling_structures vs core_methods

- `MODELING_KNOWLEDGE_GOVERNANCE.md` 明确：benchmark 用 **allowed_modeling_structures**（允许的建模结构）而非 core_methods/gold method（core_methods 仅历史追溯）。实测 P15 `problem_set.yaml` 每题的 `allowed_model_families` 即该口径（如 2020_B: `[dynamic_programming, optimization, game_theory, graph_algorithm, markov_decision_process]`）。
- 这是"多解模型原则"的落地：**允许结构清单 ≠ 黄金方法**。

### 4.5 是否存在 Problem type → keyword → model name 的 routing？

- **legacy**：存在且文档化——`core/knowledge/methodology/METHOD-DECISION-TREE.md/.json`（Q1–Q8 决策树）+ `CUMCM-HMML.md`（12 领域/38 子领域/96 方法节点）+ `METHOD-MAPPING.md`。但全部是 **INSTRUCTIONAL**（外部 agent 阅读的检索指南），无机械路由代码。
- **V3**：无 routing；只有 features → retriever 评分。

### 4.6 out_of_catalog 模型如何处理？

- 治理原则：**"out_of_catalog 不自动判错"**（The LLM constructs models；Knowledge constrains and informs）。实测 P15 将 2024_A 标记 `out_of_catalog: true`（无专卡，retriever top-1 弱匹配，仅作泛化观察，不进主检验 p 值）——**实现了"不自动判错"，同时用实验隔离而非放行**。

---

## 5. Model Construction 机制

### 5.1 model-builder role 的实际工作方式

- **legacy**（`core/legacy/hands/Modeler/agents/model-builder/SKILL.md`）：Actor 推导 → Critic 批判 → Improvement 改进的迭代环（借鉴 MM-Agent/NeurIPS 2025），默认 1 轮（env `modeling.problem_modeling_round`）最多 3 轮；产出 `work/model_draft.md` + `work/model_draft_critique.md`；Step 2-6 要求从基本定律推导、SymbolRegistry 注册、FormulaChecker 校验、列边界条件；Step 6.5 写"代码实现任务清单"（任务/输入/输出/方法/校验五列）；Step 6.7 按 TYPE-ANTIPATTERNS-CHECKLIST 做题型防错。**全部 INSTRUCTIONAL**——gate 只查 `model_draft.md` 存在（gate.py `("modeler","model-builder"): [check_files_exist]`）。
- **V3**：`do_model_construction` 只把选中卡 risks 转 assumptions（见 §2.3），**不构造模型**。

### 5.2 Model Spec → Model Artifact 的转化路径

- legacy：MODEL_SPEC_TEMPLATE.md（草稿形态）→ spec-auditor 渲染为 `output/MODEL_SPEC.md`（gate 查文件存在 + guardrails 允许内部路径）→ Programmer 消费。**转化是"模板渲染"，无类型化中间表示**。
- V3：无转化路径——model artifact 与 MODEL_SPEC.md 无程序关联（除非通过 `runtime/legacy/convert.py` 导入，属实验性桥接）。

### 5.3 assumption-validator / spec-auditor 的实际执行

- `assumption-validator`：SKILL.md 要求给假设打必要性分（≥6.0 阈值，env `modeling.assumption_score_threshold`）；`core/validators/modules/assumption_validator.py` 存在（IMPLEMENTED 校验器，validate.py 引用）；但 gate 对 assumption-validator **只查 `work/assumption_validation.json` 存在 + JSON 合法**——打分内容由外部 agent 生成（INSTRUCTIONAL）。
- `spec-auditor`：SKILL.md 要求检查 MODEL_SPEC 对齐 schema；gate 查 `output/MODEL_SPEC.md` 存在 + guardrails 文本扫描（INSTRUCTIONAL + 文本级机械检查）。

### 5.4 DAG builder 如何构造模型依赖图

- **V3**：`WorkflowComposer.compose_executable`（`core/runtime/execution/composer.py`）从 `core/workflows/` 基础 DAG + 竞赛模板按 question 展开——**控制流 DAG，非模型依赖图**。
- **legacy**：`dag-builder` agent（INSTRUCTIONAL）产出 `work/model_dag.json`（model_dag.schema.json：问题/子问题/模型/假设/求解节点+边）+ `model_dag.svg`；gate 查两文件存在 + JSON schema 合法。
- **P15**：MODEL IR 内嵌 `model_graph`（mechanism→equation→solver→objective 的有向图）——是**模型依赖图**的 typed 形态，但只在实验表示层存在。

---

## 6. Knowledge 的地位

### 6.1 Governance 落地（`docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md`）

核心哲学（v1.1 冻结）：**The LLM constructs models. Knowledge constrains and informs construction. Evidence decides whether the construction survives.**
- LLM = Model Generator（自由建模，方法卡不是执行器）
- Knowledge = Constraint / Prior（不指定"必须用 X"）
- Evidence = Adjudication（实验证据决定模型存亡）

治理原则（全文要点）：Knowledge coverage must constrain evaluation, not constrain creativity；benchmark 用 allowed_modeling_structures；结构覆盖优先于算法覆盖；Tier 0-3 先 3 张校准样本验证 schema，再 Fresh B0，再决定扩卡。

### 6.2 方法卡 schema（`core/schemas/v3/knowledge/method_card.schema.json` + 实际卡）

- 理论 schema：`constraint / prior / validation` 三类知识 + `mechanism / formulations / solvers / requires / risks`。
- 实际卡（mc-dp.yaml 实测字段）：`name / family / mechanism（含 governing_principle）/ formulations / solvers / requires / risks / validation / anti_patterns / known_failures / structure_signals`——**比 schema 更丰富**（anti_patterns/known_failures/structure_signals 为实际卡独有）。

### 6.3 Knowledge → Agent → Model 因果链：有无强制注入机制？

**无强制注入**（关键判断）：

- V3：`DefaultNodeExecutor.__init__` 自动实例化 retriever 并调用 `recommend(features)`，但 features 默认硬编码，且推荐结果**只是选择记录的 card_id/family**——知识确实进入了选择台账，但**不进入模型内容**（模型内容本就不在 runtime）。
- legacy：knowledge.py recommend 是外部 agent 可选的 CLI；SKILL.md 要求检索 CUMCM-HMML/METHOD-DECISION-TREE，但 gate 只查 method_candidates.json 存在 + risk_probe——**知识消费无机械强制**（INSTRUCTIONAL）。
- P15-K001：注入通过 **prompt bundle 全卡文本注入**（frozen_specs/knowledge_set.yaml：`injection_mode: full_card_text`，禁止摘要裁剪）——注入是**实验操作**，不是 runtime 能力。

### 6.4 Tier 0-3 核心覆盖实际状态

- 三张校准样本卡**存在且结构完整**：`mc-dp.yaml`（family: dynamic_programming）、`mc-numerical-pde.yaml`（family: numerical_pde）、`mc-queuing-theory.yaml`（family: queuing_theory）——即 P15-K001 三个主检验题的专卡（人工指定）。
- 其余 16 张卡（kmeans/ga/ahp/grey/lstm/nsga2/pso/xgboost…）为扩展卡；2022_C/2024_A 走 retriever 检索路径（非人工指定）。
- **校准状态**：3 张卡已在 P15-K001 中作为注入材料完成一轮实验（Δ_K negative，见 §10）；governance 所述"先 3 张校准样本验证 schema，再 Fresh B0"的**验证已发生**（P15-K001 即该验证）。

### 6.5 P15-K001 对 Knowledge Causal Effect 的启示

- Δ_K = +2.14（95% CI [+0.00, +6.41]）→ **未能排除零**；Δ_Sham = +3.42（CI 跨 0）> Δ_K 点估计。
- **解读**：知识注入的效果点估计为正但统计上不显著（block=3 功效不足，最小 p=0.25）；而"无关上下文的 Sham"点估计更高——**"更多上下文"假说无法排除，真正的知识因果效应未被证明**。这不是"知识无效"（22/33 runs 使用了注入知识、21 次调整、11 次拒绝；Sham 11/11 被正确拒绝=不盲从），而是**效应量小、功效不足、注入剂量有限（1 卡）、主终点粒度粗**（见 §10）。

---

## 7. Verification / Evidence / Reproducibility

### 7.1 validate.py 57 项校验的实际内容与覆盖

`core/tools/validate.py` 定义约 60 个 `check_*` 函数（实测函数清单），项目级 57 项，覆盖类别：
- **仓库结构**：目录结构、catalog.yaml 解析、agents 目录/数量/frontmatter/self-check、知识完备性、test coverage、随机种子
- **论文结构**：min_pages 17 / min_words 13000 / min_figures 6 / min_tables 4 / min_equations 15 / min_references 10、章节结构、itemize 不在正文、figure 非主语、连续开头雷同检测、PDF min bytes、近期引用比例、表格行数
- **数值可追溯**：论文数值解析到 `figures/all_results.json`（validated artifact）、结果账本
- **文本护栏**：禁止占位符/AI 痕迹/伪造引用、内部路径、guardrails
- **模型正确性探针**：assumption_validator / formula_checker / symbolic_verifier / invariant_tracker / cross_model_checker / physics model / sensitivity analysis 存在性

**性质判断**：这些是"存在性 + 结构 + 文本模式 + 数值追溯"校验。`check_physics_model` 等**不能判定数学模型本身对错**（对错需语义理解，见 §11 Risk 1）。

### 7.2 gate.py 单步门禁

- `GATES` 字典（29 agent 全覆盖）+ gatelib 断言（check_files_exist / check_json_valid / check_schema / check_guardrails / check_risk_probe / check_rubric_alignment）。
- HARD 失败 = 阻塞；WARN = 可推进；退出码 0/1/2/3。
- 设计初衷（docstring）：把 V2 Self-Check 的 `[ ]` 复选框变成**可执行断言**，"任何 runtime 都能 python gate.py"。

### 7.3 Evidence Graph 实现（`core/runtime/graph/evidence_graph.py`）

- **14 种 typed 关系**：motivated_by / solved_by / assumes / implemented_by / validated_by / tests / uses / produces / visualized_by / supports / appears_in / selects / based_on / derived_from。
- 强弱关系分级 + 失效传播 tier（invalidation propagation）；coverage 指标 `claims_supported / claims_total`。
- 关系写入点：`_register_evidence`（session.py）、`invalidate`、`declare_cross_relation`。

### 7.4 hash_chain 验证

- `core/validators/modules/hash_chain.py` 存在，且被 `validate.py` 引用（IMPLEMENTED——项目校验路径真实调用 `hash_chain.verify_chain()`）。

### 7.5 state.py reconcile 状态对账

- `core/runtime/state/reconcile.py`（只读对账器）：比较 questions/models/evidence 聚合/D1 依赖双写/engine_progress 存在性；不比较 workflow/run/review 等会话态字段（防假阳性）；退出码 0/1。
- STATE_TRUTH.md 给出真源分层：Event Log → Content Truth（registry/graph/decision_log）→ Process Projection（status.json，**仅** `ProjectState.refresh_from` 派生）→ Resume Truth（engine_progress）。

### 7.6 replay.py 运行重放

- `core/tools/replay.py <项目> [<run_id> [diff <run_id>]]`：运行重放/差异归因（IMPLEMENTED，docstring 说明）。

### 7.7 随机种子 42 / multi_run_count 5

- env `core/env/config.yaml`（`code.random_seed 42 / multi_run_count 5 / cv_threshold 0.10 / max_fix_rounds 3 / sensitivity_range 0.20`）→ `core/env/schema.yaml` 定义 → `core/env/loader.py` 注入（零依赖）。
- legacy SKILL.md 要求多种子 ≥5 次运行、报告均值±标准差（INSTRUCTIONAL）；P15-K001 实测 seeds [42,43,44] × block 配对（experiment manifest 中 seed=42 记录）。

### 7.8 pytest 774 passed / 11 skipped 测试结构

- `tests/` 9,203 行，覆盖：unit（crash_consistency、run_provenance、parallel isolation）、integration（test_structure、test_pipeline）、e2e benchmark baseline 等。
- 已修复 bug 证据：`tests/integration/test_structure.py` 的 ROOT 少一层 dirname 曾生成 `tests/tests/fixtures/` 垃圾目录（commit e693f0f 修复）——**测试自身曾污染仓库，已修复**（任务给定事实）。
- 注意：测试数字口径经 STATE_TRUTH.md §5 统一为"仅三条机器命令（pytest/validate/catalog_check）+ commit hash"，消除 228/16、574/11、751/11、758/11 四套历史口径。

---

## 8. Software Architecture

### 8.1 V3 五层认知架构

```
Workflow DAG（控制层：base + competition + project state → executable workflow）
   └─ 调度 → State Model（questions/models/…）
            Artifact Registry（产物：ID/版本/生命周期/lineage）
            Evidence Graph（typed relations + invalidation）
            Roles/Agents（Runtime Executor）→ Skills（Capability）→ Knowledge Base（方法卡/失败案例/模式）
            Paper Projection（Research State 的投影）
```
（`docs/architecture/V3.1_ARCHITECTURE.md` 核心倒置："V2 是流水线产出文件，Paper 是终点；V3 是研究产出 Artifact，Workflow 调度认知过程，Paper 只是投影"）

### 8.2 5 Role vs 29 agent

- V3 5 Role：analyst / modeler / experimenter / critic / writer（`core/roles/*.yaml`，角色=能力组合命名模板 + DAG 节点 role 引用校验）。
- V2 29 agent：legacy 兼容层（只读不新增）。**官方口径（AGENTS.md）：agent 数量不再作为架构质量指标。**

### 8.3 env/config.yaml 阈值注入机制

- `core/env/config.yaml`（值）→ `core/env/schema.yaml`（契约）→ `core/env/loader.py`（零依赖 `get("paper.min_pages")`）→ 消费方（writer/programmer/modeler/reviewer/runtime）。IMPLEMENTED。

### 8.4 扩展性

- 新增知识卡 = 加 YAML（19→N，P15 已验证 3 张校准卡工作流）。
- 新增节点 = `handlers.py` 加 `do_<node>` + workflows DAG 注册 + catalog/v3.yaml 登记（validator hook 可挂）。
- 新增竞赛 = 新模板目录（已有 11 套）。
- **天花板**：认知能力不在 core 内，扩展"智能"只能通过指令/知识/外部 Agent（§9）。

---

## 9. 工程哲学分类

### 9.1 A. Knowledge Engineering / B. Agent Engineering / C. Scientific Runtime Engineering？

**判断：核心是 C. Scientific Runtime Engineering，叠加 A. Knowledge Engineering 的知识资产，而非 B. Agent Engineering。**

证据：
- Runtime + Guardrails 是**零 LLM 的确定性"研究操作系统"**（Registry/Graph/State/DAG/失效传播/重放/对账）——这是典型的 scientific runtime（如气流/nextflow 风格的 provenance 运行时，但面向"认知过程"）。
- 知识层（19 方法卡 + HMML + failure taxonomy + decision log）是 A 的成分。
- **不是** B：29 个 agent 没有独立执行器、没有记忆、没有工具循环——它们是**指令文件**（INSTRUCTIONAL），由外部 LLM 消费。官方 THREE_LAYER_ARCHITECTURE 承认"Brain 的智能由外部 LLM 对话按 SKILL.md 执行"。

### 9.2 Agent 被当作 system / worker / executor / plugin 中的哪一种？

**executor（执行器/工人）**，且是**外部 executor**：core 记录其 provenance（`run_meta.model_provider/model_version/token_cost`），调度其产物（filesystem artifacts），但**不承载其推理**。P15 manifest `generator: claude/claude-manual/console` 是最直接证据。

### 9.3 模型被当作 text / output / artifact / executable scientific object 中的哪一种？

**artifact（且偏向台账记录）**：V3 runtime 的 model artifact = 选择记录（card_id/family/shortlist）；MODEL_IR（P15）是 typed 但只在实验层；legacy MODEL_SPEC.md 是 text。**不是 executable scientific object**——没有可执行的模型对象被 runtime 加载、运行、求解（实验节点只建台账，result 无数值）。这是与 MathModelAgent（若有 code interpreter）的核心分野之一。

### 9.4 状态被当作 chat history / workflow context / persistent state 中的哪一种？

**persistent state（持久化多真源状态）**：Event Log → Content Truth（registry/graph/decision_log 原子写）→ Process Projection（status.json 可重建）→ Resume Truth（engine_progress）。**不是** chat history（外部 agent 的对话历史不在 core），也不是易失 workflow context（每步 checkpoint + resume）。

### 9.5 是否真正拥有 evidence / decision / failure lifecycle？

- **evidence lifecycle**：✅ 有（registration → typed edges → invalidation propagation → retraction → coverage）。
- **decision lifecycle**：✅ 有（DecisionLog `core/runtime/decisions/log.py`；knowledge 运营与评审消费；decision_log.json 为真源之一）。
- **failure lifecycle**：⚠️ 部分有。发现 = 外部（评审/P15 盲评）；记录 = P15 FAILURE_TAXONOMY + error_attribution.py + 引擎 failures；**修正 = 外部 agent**；runtime 只提供失效传播与重跑调度。**闭环缺失在"自动发现与自动修正"**。

---

## 10. P15-K001 深度批判分析

### 10.1 实验设计回顾（预注册 `research/P15/protocol/preregistration/P15-K001-v1.0.md`）

2×2 Knowledge×Case 因子 + Sham 负控制，55 runs（3 主检验题 × 3 rep × 5 arms 中的 blocked 配对 + 2 泛化题），主终点 = Model Construction Quality / L2 composite（机制/方程/约束/目标正确性，盲评 3 evaluator 独立评分）。

### 10.2 关键数字（正式报告 `P15-K001-REPORT.md`，精确引用）

| 量 | 值 |
|---|---|
| Δ_K（Knowledge vs 对照） | **+2.14，95% CI [+0.00, +6.41]**，block=3，sign-permutation p=1.0 → **negative result**，不进 P15.2 |
| Δ_C（Case vs 对照） | +2.14，CI [+0.00, +6.41] |
| Δ_I（K×C 交互） | -2.56，CI [-12.82, +5.13] |
| Δ_Sham（无关上下文 vs 对照） | **+3.42，CI [-2.56, +12.82]**（点估计 > Δ_K） |
| 2019_C | **全部 arms = 87.18（零变异）** |
| 2020_B | A=87.18，B=C=D=100，E=87.18（效应由 A/E 臂 Q1-only 罕见失败驱动） |
| 2018_A | A=87.18，B=84.62，C=84.62，D=87.18，E=87.18（噪声） |
| RQ5 方法族命中率 | A=0 / B=0.222 / C=0 / D=0.222 / E=0 |
| 知识利用 | 注入 33 runs：使用 22/33，调整 21，拒绝 11；Sham 11/11 被拒绝（不盲从） |

### 10.3 这个实验证明了什么 / 没有证明什么

**证明了**：
1. 预注册 + 盲评 + 冻结 + 泄漏扫描的可执行实验基础设施**可行**（55/55 REGISTERED、55/55 盲评、DATA FREEZE 165 文件、冻结校验 PASS、44 规格文件零漂移）。
2. 知识注入**不会造成盲从**（Sham 11/11 拒绝 = 注入不产生"服从偏差"）。
3. 注入知识**被实质消费**（22/33 使用、21 调整、11 拒绝——"知识作为 Constraint 而非 Dictation"的治理假设在行为层面成立）。
4. **主终点测量是可信的**（evaluator 间一致性 + 证据指针强制 + 评分标准 v1.0）。

**没有证明**：
1. **知识注入提升模型构造质量**（Δ_K 的 CI 下界 = 0.00，无法排除零效应）。
2. **没有证明知识无效**（CI 上界 +6.41，点估计为正；且 2019_C 零变异 + 2020_B 单事件驱动说明是**测量与功效问题**，不是零效应）。
3. **Knowledge Causal Effect 未与"更多上下文"效应分离**（Δ_Sham 点估计更高）。

### 10.4 五层区分（必须分开的维度）

| 维度 | 结论 | 证据 |
|---|---|---|
| Knowledge Ontology（本体是否合理） | 结构丰富（mechanism/formulations/solvers/requires/risks/anti_patterns/known_failures） | mc-dp.yaml 实测 |
| Knowledge Utilization（是否被消费） | 是，非盲从 | 22/33 使用、Sham 11/11 拒绝 |
| Knowledge Causal Effect（是否因果提升质量） | **未证实**（Δ_K negative） | CI [+0.00,+6.41] |
| Measurement Validity（测量是否有效） | 主终点有效但有**天花板/粒度问题**：2019_C 全 87.18 零变异（评分工具有饱和点）；L2 混合"结构完备+内容正确" | REPORT + ATTRIBUTION |
| Evaluation Power（统计功效） | **不足**：block=3，最小 p=0.25，检测不出 <~6.4 分的真实效应 | ATTRIBUTION "统计功效" 节 |

### 10.5 为什么 Δ_K>0 但仍是 negative result？

预注册决策门是**频率学 CI**：Δ_K 的 95% CI 下界恰好 = 0.00（不严格含 0 但贴 0），sign-permutation p=1.0 因 block 数太少（3）无法产生显著置换。**点估计为正 ≠ 因果效应为正**——在功效不足的设计里，+2.14 与 0 不可区分。negative 的正确读法 = "**未能证明**"，不是"证明无"。

### 10.6 为什么 Sham>K 是重要信号？

Sham（无关上下文，如与题无关的说明文字）点估计 +3.42 > 知识 +2.14，说明**存在一条非知识路径可产生等量甚至更高的质量提升**："更多上下文/更长的提示包"本身可能改善 LLM 表现（更充分的思考预算、更完整的题面上下文）。**若不加 Sham 负控制，Δ_K 会被误读为知识效应**——这正是该实验设计最值得肯定的一点。

### 10.7 为什么"更多上下文"与"真正的建模知识效应"必须分离？

因为两者的**干预含义完全不同**：若提升来自"更多上下文"，则优化方向是 prompt/上下文工程（加长题面、加示例、加推理预算）；若来自"知识卡语义"，则优化方向是知识工程（卡内容/结构/检索）。P15-K001 的结论是：**在当前注入方式（1 卡全文、中等剂量）下，无法将两者分开**——这直接为 P15.2 的剂量/机制设计提供依据（ATTRIBUTION 建议：分层剂量、过程追踪、L3/L4 终点）。

### 10.8 为什么 measurement failure（RQ5 词表错位）必须和 capability failure 分离？

RQ5 方法族命中 A=0 / B=0.222…表面上是"LLM 识别方法族的能力差"。但实测盲评样本（`06cb0fb3`）的 MODEL IR：`model_family.primary = "discrete_recurrence"`、**`secondary = ["dynamic_programming"]`**——生成侧**正确识别了 DP**，只是把 primary 字段填成了 schema 枚举里的 `discrete_recurrence`。而 RQ5 指标代码（`paired_analysis.py:194`）`ok = r["method_family"] in allowed` 只取 `deterministic.method_family_identified`（= primary），**不看 secondary**。因此：
- 词表错位：`model_ir.schema.json` 的 family 枚举（含 discrete_recurrence）与 `problem_set.yaml` 的 `allowed_model_families`（含 dynamic_programming）**两套受控词表不一致**；
- 指标设计：只比对 primary 单串，丢弃 secondary/描述语义；
- **结论**：RQ5 测的是"词表对齐度"，不是"方法族识别能力"。混为一谈会得出错误的 capability 结论。这是 tertiary measurement limitation（任务给定定性），不影响主终点。

### 10.9 禁止写"知识卡无效"

实验证据明确不支持该结论：Δ_K CI 上界 +6.41、2019_C 零变异（测量天花板）、2020_B 由单事件驱动、block=3 功效不足、注入剂量仅 1 卡、主终点 L2 粒度粗。**正确表述：knowledge causal effect 未被证实，且与 more-context 效应未分离；需更大功效 + 更细终点 + 剂量梯度才能裁决。**

---

## 11. LinHoMo 六大风险逐条证据回应

### Risk 1 Formalized nonsense（schema 合法 + graph 完整 + validator PASS 但模型本身错误）

**回应：防护机制部分存在，但语义空白是结构性的。**

- 存在的防护：formula_checker（括号/LaTeX 完整性）、symbol_registry（符号一致性）、assumption_validator（必要性评分）、symbolic_verifier / invariant_tracker / cross_model_checker / physics_model（validate.py 引用）——全部是**语法/结构/一致性**校验。
- 证据缺口：V3 runtime 的 experiment 节点产出的 result artifact 是**无数值占位**（claim 字面量 `"{qid} 结论"`），EvidenceGate E1-E4 只查**边存在**——**一个 result artifact 含错误数值也能 PASS 门禁**（E4 只要求"实验有 produces 结果产物"）。
- P15 盲评证实了形式化无法防住内容错误：FAIL runs（如 06cb0fb3 只绑定 Q1）在 schema/结构上合法，**只有人类 evaluator 按 rubric 逐维评分才发现覆盖失败**。
- **结论**：防护网防"形式非法"，不防"内容错误"。这是 formal verification 对语义理解的天花板，当前架构把语义裁决完全外包给外部 LLM/人类评审——**Risk 1 成立且未闭环**。

### Risk 2 Over-formalization（变成 research process management system 而非数学建模引擎）

**回应：部分成立，且项目自己承认。**

- 证据：V3 runtime 36k 行中，绝大多数是**过程管理**（registry/graph/state/dag/invalidation/replay/reconcile/projection），数学构造/求解**不在 runtime 内**（§2.3、§9.3）。
- THREE_LAYER_ARCHITECTURE 自述："继续向下挖掘会得到一个'科研操作系统'而不是'数模 Agent'"——**作者已自我警觉**并把 P13-P17 主战场改为 Agent Brain。
- P15-K001 的 Δ_K negative 与"过程管理不提升模型质量"一致（但注意：P15 测的是**知识注入**，不是**runtime 本身**——runtime 对质量的影响未被因果实验测过）。
- **结论**：当前仓库 = 研究过程管理基础设施 + 知识资产 + 测量实验；数学建模引擎（模型构造/求解/验证的计算能力）**在外部 Agent 里**。Over-formalization 风险**真实存在**，治理文档已用"三层冻结"部分对冲。

### Risk 3 Infrastructure without capability gain（schema/contract/graph/validator 增多但质量未提升）

**回应：这是 P15-K001 最直接的判决点——但注意实验测的是知识注入，不是基础设施。**

- 证据：Δ_K = +2.14 CI [+0.00,+6.41] negative——**知识注入这一条能力路径未显示显著质量提升**。
- 但必须公平：①基础设施（冻结/盲评/盲评密钥/泄漏扫描）**本身让"质量测量"变得可信**——没有它，任何 Δ 都是不可信的；②2019_C 全臂 87.18 零变异说明 **L2 评分工具有天花板**，可能掩盖真实差异；③该实验**没有**对比"无基础设施的裸 LLM"vs"有基础设施"，因此不能判定基础设施零增益。
- **结论**：尚无证据证明 formal runtime 提升 Model Construction Quality；有证据证明它提升了**测量质量与过程可信度**。Risk 3 的"质量未提升"部分**未被证伪也未证实**，方向值得警惕。

### Risk 4 False scientific confidence（状态/证据/契约完善 → 错误的安全感）

**回应：真实存在，且已有反例。**

- 证据 1：2019_C 全臂 87.18 零变异——"所有条件都 87.18" 若被解读为"模型质量稳定良好"就是 false confidence；正确解读是**评分饱和**。
- 证据 2：RQ5 的 A=0 命中率若被解读为"LLM 识别方法族能力为零"就是 false confidence；正确解读是词表错位。
- 证据 3：EvidenceGate 全绿 + 55/55 REGISTERED 容易给人"实验完整"的安全感，但 **REGISTERED ≠ 模型正确**（FAIL runs 结构合法）。
- 缓解机制：STATE_TRUTH 把状态限定为"投影可重建"，reconcile 只读对账、P15 归因报告明确写"tertiary measurement limitation"——**项目有自我批判机制，但使用者的安全感可能越过这些细节**。
- **结论**：Risk 4 成立；缓解靠的是"数字只来自机器命令 + commit hash"的口径纪律，而非机制本身免疫。

### Risk 5 Execution weakness（理论/认知架构强于实际 execution substrate）

**回应：成立，且是跨仓库对比中最明显的短板。**

- 证据：V3 runtime **不做任何数值计算**（实验节点只建台账）；代码执行（code/main.py）、实验运行（multi_run 5 次）、结果验证**全部在外部 Agent 的 sandbox 中发生**，core 只接收文件产物。
- 对比 MathModelAgent（若具 code interpreter / 多 agent 协作 / 实际代码执行）：LinHoMo 的 core **没有 code interpreter、没有 agent 间消息传递、没有工具循环**——29 个 agent 之间**无运行时互操作**（它们只是 SKILL.md 文档，通过 filesystem 交接产物）。
- "多 Agent 协作"在 LinHoMo = **文件的顺序/条件流转**（gate 判定），不是并发智能体协商。
- **结论**：epistemic 架构（provenance/evidence/gate）显著强于 execution substrate（计算/求解/执行）。这是其作为"研究基础设施"合理、作为"数模求解 Agent"不足的根源。

### Risk 6 Ontology weakness（model family/mechanism/method/solver/implementation 未完全分离）

**回应：成立，RQ5 即实证。**

- 证据 1：`discrete_recurrence`（model_ir.schema.json 的 family 枚举）vs `dynamic_programming`（problem_set.yaml 的 allowed_model_families）——**同一建模思想两种命名**，且 RQ5 指标只比对 primary 单串。
- 证据 2：MODEL IR 里 `model_family`（family）、`mechanisms[]`（机理）、`equations[]`（结构）、`solvers[]`（求解器）、`experiments[]`（实现/实验）**在实验层已分列**——但 runtime 层 model artifact 只有 `family` 一个串。
- 证据 3：方法卡的 `family` 字段是自由字符串（19 张卡无统一枚举注册）。
- **结论**：实验表示层（MODEL IR）已接近 concept/mechanism/family/method/solver 分离；**runtime 层与受控词表层严重不足**——RQ5 的错位正是 ontology 未收敛的直接后果（详见 §12）。

---

## 12. Model Ontology 深挖（围绕 RQ5）

### 12.1 为什么 dynamic_programming 和 discrete_recurrence 会成为两个不同字符串？

三方独立定义、无统一注册表：
1. `research/P15/model_representation/model_ir.schema.json` 的 `model_family.primary` 枚举示例含 `discrete_recurrence`（生成侧按 schema 引导填 primary）；
2. `research/P15/benchmark/problem_cards/2020_B/card.yaml` 的 `allowed_model_families: [dynamic_programming, …]`（受控词表，人工编写）；
3. `core/knowledge/methods/cards/mc-dp.yaml` 的 `family: dynamic_programming`（方法卡词表）。

三者**没有共享枚举**。生成侧把 primary 填为 schema 示例串 `discrete_recurrence`（secondary 仍含 `dynamic_programming`），而指标只比对 primary → 命中率为 0。**字符串分叉 = 词汇表分叉，不是概念分叉。**

### 12.2 model_family.primary 字段的 ontology 是否太弱？

**是**。单字符串无法区分：思想（Bellman 最优性）／机制（逐日递推）／方法族（DP）／求解算法（反向递推）／实现（Python 填表）。MODEL IR 用 `mechanisms[]/equations[]/solvers[]/experiments[]` 分散承载了其余维度，但 `model_family` 作为**一级识别字段**仍被 RQ5 用作唯一比对对象——**字段弱 + 指标只读该字段 = 双重薄弱**。

### 12.3 更严格的本体是否应拆成 concept / mechanism / model_family / method / solver / implementation？

**应**。实测拆分度：

| 层次 | MODEL IR（P15 实验层） | runtime 层（type:"model" artifact） | 受控词表层（allowed_model_families） |
|---|---|---|---|
| concept（思想） | 无显式字段（隐含于 mechanism） | ❌ | ❌ |
| mechanism（机理） | `mechanisms[]`（含 governing_principle） | ❌ | ❌ |
| model_family（族） | `model_family.primary/secondary` | `data.family`（单串） | ✅ 词表 |
| method（方法） | `equations[].type`（state_transition/recurrence…） | ❌ | ❌ |
| solver（求解器） | `solvers[]`（name/type/method/convergence_criteria） | ❌ | ❌ |
| implementation（实现） | `experiments[]`（parameters/run_metadata） | ❌ | ❌ |

**结论**：实验层已 6 层分离的 5/6；runtime 层与词表层只留 model_family 一维。RQ5 的错误在词表层+指标层，但根因是**runtime 未采用实验层的多维多阶本体**——"表示层领先、生产层滞后"。

### 12.4 当前 schema 中这些层次分离到了什么程度？

- 最好的：`model_ir.schema.json`（实验契约，6 维中 5 维显式）。
- 次之：`model_spec.schema.json`（legacy，problem_understanding/assumptions/symbols/models/sub_problems/verification——**无 mechanism/solver/implementation 维度**）。
- 最弱：V3 artifact（通用 data dict）+ 方法卡 `family` 自由字符串。
- **建议方向（证据指向）**：以 MODEL IR 的多维模型为运行时一等对象，`model_family` 降级为派生索引，`allowed_model_families` 与 schema 枚举合并为单一注册表（如 `catalog/model_families.yaml`），RQ5 类指标改为"任一次级/机制/solver 命中即算族命中"。

---

## 13. 关键文件路径索引

| 判断 | 路径 | 类/函数/schema |
|---|---|---|
| V3 会话/执行 | `core/runtime/execution/session.py` | `RuntimeSession`（run/resume/checkpoint/invalidate/rerun/declare_dependency/declare_cross_relation） |
| V3 节点执行器 | `core/runtime/execution/handlers.py` | `DefaultNodeExecutor`、`features_for`、`do_problem_analysis`、`do_model_selection`、`do_experiment` |
| V3 引擎/波次 | `core/runtime/execution/engine.py`、`wave_executor.py`、`composer.py`、`dag.py` | `WorkflowEngine`、`WaveExecutor`、`WorkflowComposer.compose_executable`、`WorkflowDAG` |
| V3 状态 | `core/runtime/state/model.py`、`reconcile.py`、`runs.py`、`dependencies.py`、`relations.py` | `ProjectState.refresh_from`、`reconcile`、`emit_run_record`、`declare_dependency` |
| Artifact Registry | `core/runtime/artifacts/registry.py`、`artifact.py`、`lifecycle.py` | `ArtifactRegistry.create/save`、`Artifact` |
| Evidence Graph | `core/runtime/graph/evidence_graph.py` | `EvidenceGraph.add_relation/invalidate/coverage`（14 关系） |
| 决策日志 | `core/runtime/decisions/log.py` | `DecisionLog` |
| 知识检索/选择 | `core/runtime/knowledge/retriever.py`、`core/runtime/modeling/selection.py`、`candidates.py`、`planner.py` | `recommend`、`MethodArena`、`CandidateArena`、`ExperimentPlanner` |
| 方法卡 | `core/knowledge/methods/cards/*.yaml`、`core/schemas/v3/knowledge/method_card.schema.json` | mc-dp/mc-numerical-pde/mc-queuing-theory 等 19 卡 |
| 论文投影 | `core/runtime/writing/projection.py`、`director.py`、`narrative_ir.py`、`fact_check.py` | `PaperProjection.project` |
| 证据门禁 | `core/validators/evidence/evidence_gate.py` | E1–E4（`EvidenceGate`） |
| 项目校验 | `core/tools/validate.py` | `check_*` × ~60（57 项） |
| 单步门禁 | `core/tools/gate.py`、`gatelib.py` | `GATES`（29 agent） |
| 状态推进 | `core/tools/state.py` | `cmd_v3`→`runtime/legacy/convert.py` |
| 重放 | `core/tools/replay.py` | 运行重放/差异归因 |
| 知识 CLI | `core/tools/knowledge.py` | `recommend --types` |
| schema | `core/schemas/model_spec.schema.json`、`model_artifact.schema.json`、`model_dag.schema.json`、`v3/artifact/*`、`v3/evidence/graph.schema.json`、`v3/workflow/dag.schema.json`、`v3/state/status.schema.json` | MODEL_SPEC / MODEL_ARTIFACT / MODEL_DAG / ARTIFACT / REGISTRY / GRAPH / DAG / STATUS |
| 治理文档 | `docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md`、`THREE_LAYER_ARCHITECTURE.md`、`V3.1_ARCHITECTURE.md`、`HARDENING_PROGRAM.md`、`STATE_TRUTH.md`、`RUNTIME_CONTRACTS.md` | — |
| P15-K001 | `research/P15/protocol/preregistration/P15-K001-v1.0.md`、`analysis/reports/P15-K001-REPORT.md`、`P15-K001-ATTRIBUTION.md`、`analysis/scripts/paired_analysis.py`、`protocol/frozen_specs/*.yaml`、`model_representation/model_ir.schema.json`、`capability/MODEL_CONSTRUCTION_RUBRIC.md`、`capability/FAILURE_TAXONOMY.md` | 主报告数字 / RQ5 指标（paired_analysis.py:194） |

---

## 14. 优势与风险（证据级）

### 14.1 最核心的差异化优势

1. **可执行的科学测量基础设施（唯一能给出"知识因果效应"数据的数模仓库）**：预注册 + 盲评（3 evaluator 独立、Generator≠Evaluator 隔离、泄漏扫描 PASS）+ 冻结（165 文件、44 规格零漂移）+ 55/55 REGISTERED——**把"模型构造质量"变成了可审计、可复制的测量对象**。P15-K001 的 negative result 本身就是稀缺资产：它证明了该仓库能产出**可信的否定结论**，而绝大多数同类项目只有无法证伪的宣称。
2. **多真源状态架构**（Event Log → Content Truth → Process Projection → Resume Truth）+ 失效传播 + 原子写 + 对账器——把"研究过程"变成**可重放、可对账、可崩溃恢复**的确定性运行时。
3. **知识治理哲学**（LLM 构造模型 / 知识约束与告知 / 证据裁决 + out_of_catalog 不自动判错 + allowed_modeling_structures）——方法论上**防住了"知识卡=金科玉律"的反模式**，且 P15 实测"注入不产生盲从"。

### 14.2 最大风险

**是否已证明 formal scientific runtime 可以提升 Model Construction Quality？——没有。**

- P15-K001（唯一直接测量）给出 Δ_K=+2.14 CI [+0.00,+6.41]：**知识注入路径未证实**；runtime 本身对质量的影响**从未被因果测量**（无"裸 LLM vs 带 harness"对比臂）。
- 因此，**它是"更好的数学建模系统"还是"更好的数学建模研究基础设施"？答案是后者**：
  - 作为**研究基础设施**：证据充分（测量、冻结、盲评、provenance、对账——全部 IMPLEMENTED 且经 55-run 实验验证）。
  - 作为**数学建模系统**：证据不足（runtime 不构造/不求解/不验证模型内容；构造质量由外部 LLM 决定；知识因果效应未证实）。
- **风险排序**：Risk 5（execution weakness）> Risk 1（formalized nonsense）> Risk 2（over-formalization）> Risk 4（false confidence）> Risk 6（ontology）> Risk 3（infra without capability gain，当前证据不足以定罪，但方向需警惕）。

---

## 15. 一句话工程哲学描述

**"把数学建模做成一台可重放、可对账、可判审的科学研究运行时：LLM 构造模型，知识约束与告知，证据裁决存亡，论文只是投影——其第一性优化目标不是'构造更好的模型'，而是'让模型构造过程与结论变得可测量、可审计、可证伪'。"**

---

### 附：证据分级汇总表（关键判断）

| 判断 | 分级 |
|---|---|
| V3 零 LLM 确定性节点执行器 | IMPLEMENTED（handlers.py + orchestrator.py docstring） |
| 实验节点不产生数值计算（占位 result） | IMPLEMENTED（handlers.py `do_experiment`，claim=`"{qid} 结论"`） |
| features 默认硬编码 evaluation | IMPLEMENTED（handlers.py:75-76） |
| model artifact = 选择记录（card_id/family/shortlist） | IMPLEMENTED（handlers.py `do_model_selection`） |
| 29 agent 无运行时互操作（仅文件流转+gate） | IMPLEMENTED（gate.py GATES / SKILL.md 文件契约） |
| EvidenceGate 只查结构不查语义 | IMPLEMENTED（evidence_gate.py E1–E4） |
| P15 生成侧 = 外部 Claude console 会话 | IMPLEMENTED（runs/*/manifest.json generator 字段） |
| 知识消费无强制注入（runtime 层） | IMPLEMENTED（默认 features / gate 无知识检查） |
| 方法卡知识被 P15 注入消费（22/33 使用、Sham 11/11 拒） | IMPLEMENTED（REPORT 数字） |
| 知识因果效应未证实 | IMPLEMENTED（Δ_K CI [+0.00,+6.41]） |
| RQ5 词表错位（primary=discrete_recurrence，secondary=dynamic_programming） | IMPLEMENTED（盲评样本 06cb0fb3 + paired_analysis.py:194） |
| MODEL IR 六维本体仅存在于实验层 | IMPLEMENTED（model_ir.schema.json vs runtime artifact） |
| 方法卡 family 自由字符串无统一枚举 | IMPLEMENTED（19 卡 family 字段实测） |
| legacy 29 步流水线仍可执行 | IMPLEMENTED（orchestrator --legacy / state.py advance / gate.py） |
| 论文数值可追溯 all_results.json | IMPLEMENTED（validate.py numeric traceability） |
| 状态多真源 + 原子写 + 对账 | IMPLEMENTED（STATE_TRUTH.md + reconcile.py + 原子写实测） |
