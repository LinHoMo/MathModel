# 三仓库数学建模系统深度技术审计 —— 最终综合报告

- **审计对象**：BZD（`BZDmathclub/bzd-math-modeling-skills`）/ MathModelAgent（`jihe520/MathModelAgent`）/ LinHoMo（`C:\Users\Lin\Desktop\Programs\MathModel`，本地权威副本）
- **证据来源**：三份证据档案（`research/REPOSITORY_AUDIT/dossiers/{BZD,MathModelAgent,LinHoMo}_dossier.md`），全部精读完毕；本报告为综合、裁决、批判性整合，非三档案拼接
- **证据分级约定（贯穿全文）**：`IMPLEMENTED`（有 runtime 路径/测试证据）｜`CONTRACT_ONLY`（有 schema/interface 无 runtime）｜`DOC_CLAIM`（文档声称代码证据不足）｜`INSTRUCTIONAL`（仅 prompt 要求，无机械强制执行）
- **研究立场（贯穿全文）**：Model Quality ≠ Paper Quality；Model Knowledge ≠ Model Capability；Schema Validity ≠ Mathematical Correctness；Workflow Completion ≠ Scientific Validity；More Context ≠ More Knowledge；Evidence Recording ≠ Evidence of Correctness；Formalization ≠ Truth；Agent Intelligence ≠ System Reliability

---

## Executive Verdict

- **BZD**：评委经验提示词工程（Knowledge Engineering）。把近五年国赛评阅细则蒸馏成高度规则化的评审 Skill + 5,713 条模型字典 + 5 个确定性边缘脚本；"评审"是它真正会做的事，建模与执行全部外包。核心能力完全押注 LLM 对提示词的自律执行。
- **MathModelAgent**：LLM 文本接力流水线（Agent Engineering）。Coordinator→Modeler→Coder→Writer 四段顺序执行，用真实 Code Interpreter 作为唯一机械反馈回路；Model 自始至终只是流转在 Agent 之间的字符串，系统对"成功"的定义 = 流水线跑完 + 论文编译通过。
- **LinHoMo**：科学研究运行时（Scientific Runtime Engineering）。把数学建模做成可重放、可对账、可判审的确定性运行时（Artifact Registry + Evidence Graph + 多真源 State + DAG + 门禁），并拥有三者中**唯一**的预注册受控实验（P15-K001）；但 runtime 本身不构造、不求解、不验证模型内容——数学认知全部在外部 LLM，且知识因果效应未证实（Δ_K=+2.14，CI 下界贴 0）。
- **三者核心分歧**：**Model 是什么**。BZD 视 Model 为字典记录 + 论文散文（无绑定）；MathModelAgent 视 Model 为 Agent 间流转的文本；LinHoMo 视 Model 为 artifact（运行时层仅为选择记录，typed 的 MODEL_IR 只存在于实验层）。分歧的根源是三者对"系统边界"的定义不同：BZD 的边界是评审、MathModelAgent 的边界是论文工作流、LinHoMo 的边界是可证伪的研究过程。

---

## 1. Real Runtime Reconstruction

### 1.1 BZD：无 runtime，纯 prompt 注入

BZD 不存在统一 runtime：没有可执行入口、没有 orchestrator、没有状态机、没有 schema 校验器、没有测试（全仓零测试，目录树无 `test/spec/pytest` 命中）。"流程"全部表达为 SKILL.md 提示词，由宿主（Codex / Claude Code）注入上下文后由 LLM 执行。**唯一真 runtime 是 5 个 Python 脚本**，承担位次/竞争校准/字典/学校查询四个边缘函数（`IMPLEMENTED`，本审计实测全部可执行）。

数据流图（箭头 = 传输介质）：

```
用户赛题
  │  [prompt injection：SKILL.md + references/*.md 注入宿主上下文]
  ▼
bzd-problem-translator（INSTRUCTIONAL）──[Agent message / filesystem artifact：.md 题解报告]
  │  拆分子问题（句子单元切分规则，INSTRUCTIONAL）
  ▼
bzd-modeling-ideas（INSTRUCTIONAL）──[Agent message / markdown 候选表]
  │  生成 ≥2 候选 + 比较表 + 推荐理由
  ▼
bzd-model-dictionary──[tool invocation：query_dictionary.py 机械查 5713 条 JSON（IMPLEMENTED）]
  │  11 维适配判定（INSTRUCTIONAL，LLM 执行 fit-assessment.md）
  ▼
【模型构造】──[N/A：workflow 明示 "pass to the user's modeling agent"，显式外包]
  ▼
【写码/跑实验】──[N/A：仓库无任何运行代码能力]
  ▼
8 个章节 checker（INSTRUCTIONAL）──[Agent message：分级问题清单]
  ▼
bzd-review-paper──[rubric 构建/打分：INSTRUCTIONAL；位次/竞争校准：IMPLEMENTED 脚本]
  ▼
HTML 报告（filesystem artifact，模板 IMPLEMENTED / 填充 LLM）
```

**逐环节"谁"**：谁理解题目 = translator（prompt）；谁拆分子问题 = translator（prompt）；谁判定类型 = A–E 题号→信号表（INSTRUCTIONAL，letter-based heuristic）；谁生成候选 = modeling-ideas（prompt 强制 ≥2）；谁选择 = LLM 依 fit-assessment 主观判定；谁构造 = **仓库外**；谁写码/跑实验 = **仓库外**；谁验证 = checker 的 prompt 级"核验"（无机械验证器）；谁发现错误 = checker 输出问题清单（LLM 自审）；谁修改 = 建议性（INSTRUCTIONAL）；谁评价 = 评审主 Skill（打分 INSTRUCTIONAL + 位次脚本 IMPLEMENTED）；谁写论文 = **不存在**（只有模板）。

### 1.2 MathModelAgent：顺序函数调用的 LLM 文本流水线（V2）+ Harness 驱动 Skill（V3）

V2 是**真实存在的运行时**（`IMPLEMENTED`）：FastAPI → `process_task`（asyncio.wait_for 18000s）→ `Flows._process_task` → `MathModelWorkFlow.execute()` 顺序执行 4 Agent。数据流图：

```
用户赛题
  │  [HTTP REST / JSON schema（schemas/request.py: Problem）]
  ▼
modeling_router.create_modeling_task ──[Python asyncio task / workflow state]──▶ process_task
  ▼
CoordinatorAgent.run ──[Agent message / prompt injection：题面原样塞入 user message]
  │  → LLM 返回 JSON {questions}，json.loads（MAX_JSON_RETRIES=3）
  ▼
ModelerAgent.run ──[Agent message / JSON string]
  │  → {questions_solution: {问题: 模型文本}}（Model = 字符串值）
  ▼
for 每个子问题：CoderAgent.run
  │  ──[tool invocation（execute_code_tools JSON schema）]──▶ CodeInterpreterFactory
  │       └─▶ LocalCodeInterpreter（jupyter_client 真内核）或 E2BCodeInterpreter（云沙箱）
  │  ──[filesystem artifact：notebook.ipynb / 图片 / 结果文件]
  │  ──[Agent message：stdout/stderr/error → get_reflection_prompt 反思 → 重试，上限 MAX_CHAT_TURNS=30]
  ▼
for 每个论文小节：WriterAgent.run ──[tool invocation：search_papers → OpenAlex（IMPLEMENTED）]
  ▼
UserOutput.write_paper ──[filesystem artifact：字符串拼接出 paper.md/.tex]
```

**逐环节"谁"**：理解题目 = Coordinator（prompt 摘录题面，无语义理解层）；拆分子问题 = Coordinator 的 JSON questions（无机械校验）；判定类型 = Modeler（prompt 内嵌 cookbook 决策树）；生成候选 = **没有**（一次 prompt 直接给最终模型）；选择 = Modeler（cookbook 关键词路由）；构造 = Modeler（纯文本）；写码 = CoderAgent（LLM 生成 code 字符串 → 解释器真实执行）；跑实验 = Code Interpreter（**真实执行，唯一 IMPLEMENTED 的计算环节**）；验证 = **无独立验证器**（唯一反馈 = stderr）；发现错误 = CoderAgent 反射循环（LLM 自读报错）；修改 = CoderAgent 自重试；评价 = **无**（Evaluator 在 roadmap）；写论文 = WriterAgent + 字符串拼接。

V3 是纯 SKILLS（`1start→2analysis→3coding→4drawio→5writing→6verity`），运行时 = Claude Code/Codex 本身；唯一机械步骤是 `6verity/scripts/writing_check.sh`（占位符/泄漏/章节编号/图片存在性等文本门禁，`IMPLEMENTED`）；数值一致性为 WARN 子串检查；PDF 视觉检查为条件性 INSTRUCTIONAL。

### 1.3 LinHoMo：确定性零 LLM 认知运行时 + 外部 Agent 认知源

V3 默认执行器 `DefaultNodeExecutor` 是**零 LLM 的确定性节点执行器**（orchestrator.py docstring 原文）。数据流图：

```
用户赛题（questions, features 由外部传入）
  │  [CLI：python core/tools/orchestrator.py <项目> --execute]
  ▼
RuntimeSession.run
  ├─ WorkflowComposer.compose_executable ──[Python function call → workflow state：DAG]
  ├─ registry.create("question", ...)      ──[filesystem artifact：Question Artifact]
  ├─ WaveExecutor(max_workers=1)           ──[Python function call]
  │    └─ DefaultNodeExecutor.do_<node>
  │         ├─ do_model_selection → MethodArena.recommend(features, top_k=3) → model artifact
  │         │     （data 仅 {card_id, family, shortlist}——选择记录，非模型本体）
  │         ├─ do_model_construction → 只把卡片 risks 转 assumptions artifact（不构造模型）
  │         ├─ do_experiment → 创建 experiment/result/figure 三 artifact
  │         │     （result claim 字面量 "{qid} 结论"——无数值占位）
  │         └─ do_* → artifact / evidence
  ├─ _register_evidence → graph.add_relation ──[Python function call → graph state：typed edges]
  ├─ checkpoint() = registry.save + graph.save + decisions.save + state.refresh_from + state.save
  │     ──[filesystem artifact：4 个状态文件原子写]
  └─ emit_run_record（best-effort）         ──[filesystem artifact：run record]
        │
        ▼
python core/tools/validate.py（57 项项目级门禁，CLI）
```

**逐环节"谁"**（V3 零 LLM 模式）：理解题目 = **没有**（do_problem_analysis 用 `features` 默认硬编码 `{"problem_types":["evaluation"],"has_data":True,"sample_size":"medium"}`，handlers.py:75-76）；判定类型 = **没有**（features 是外部输入契约）；生成候选 = MethodArena（基于 features 对知识卡打分排序，`IMPLEMENTED`）；选择 = 取 arena 第一（`IMPLEMENTED`）；构造 = **没有**（只转 risks→assumptions）；写码 = **没有**（只建台账）；跑实验 = **没有计算**（E→R→F 证据链只建 artifact，result 无数值）；验证 = EvidenceGate E1–E4 **结构性**检查（边存在性，不校验数值正确性）；发现错误 = **runtime 无此机制**（落在外部 LLM/盲评 evaluator）；修改 = `invalidate()` 失效传播 → `rerun()` 重跑（只触发节点重跑，不产生新认知）；评价 = 外部（P15 盲评 3 evaluator + rubric，`IMPLEMENTED` 实验路径）；写论文 = `PaperProjection.project(narrative)` 生成结构化大纲（`IMPLEMENTED`），正文由外部 writer agent 按 `core/templates/latex/*` 撰写。

V2 legacy 29-agent 流水线**仍可执行**（`IMPLEMENTED`：`orchestrator.py --legacy`、`state.py advance`、`gate.py` 覆盖全部 29 agent），但 29 个 agent 之间**无运行时互操作**——它们是 SKILL.md 指令文件，通过 filesystem 产物 + gate 判定交接。core 36k 行零 LLM SDK 依赖，P15 manifest 的 `generator: ["claude","claude-manual","console"]` 直接证明生成侧是外部 Claude 会话。

### 1.4 三者的传输介质对比（裁决表）

| 环节 | BZD | MathModelAgent | LinHoMo |
|---|---|---|---|
| 题面进入 | prompt injection | HTTP + prompt injection | CLI 参数 + features 契约 |
| 子问题拆分 | Agent message（.md） | JSON string（json.loads） | DAG 按 question 展开 |
| 候选生成 | markdown 表（LLM） | 无 | MethodArena 打分（机械） |
| 模型传递 | 无（外包） | JSON string 接力 | artifact data dict |
| 代码执行 | 无 | **真解释器**（local/e2b） | 无（外部 sandbox） |
| 验证 | prompt 级 | stderr + 文本门禁 | EvidenceGate 结构门禁 |
| 状态 | 无 | workflow 内存态 + Redis | **持久化多真源** |
| 论文 | 模板（不写） | 字符串拼接（V2）/ 章节文件（V3） | 大纲投影 + 外部正文 |

**裁决**：三者中只有 MathModelAgent 拥有"真实计算"的机械反馈回路，只有 LinHoMo 拥有"可对账持久状态"，BZD 两者皆无——但 BZD 拥有三者中最强的"评审规则算术层"。

---

## 2. What Is a Model?

### 2.1 三者的 Model 定义

| 维度 | BZD | MathModelAgent | LinHoMo |
|---|---|---|---|
| Model 是什么 | 三种载体并存：JSON 字典记录（5713 条）/ markdown 候选表 / 论文散文，**无绑定** | `questions_solution: dict[str,str]` 中的**字符串值**（V2）；`ANALYSIS_MODELING_REPORT.md` 的 markdown 小节（V3） | `type:"model"` 的通用 artifact（运行时层，data 仅 {card_id, family, shortlist}）；MODEL_IR（实验层，typed） |
| 载体本质 | 知识库记录 + LLM 输出文本 | 流转文本 | 台账记录（运行时）/ typed 对象（实验层） |
| 证据分级 | 字典 IMPLEMENTED / 表格 INSTRUCTIONAL | V2 IMPLEMENTED（字符串接力）/ V3 INSTRUCTIONAL | 运行时 IMPLEMENTED（台账）/ MODEL_IR IMPLEMENTED（实验层） |

### 2.2 Model 属性逐项对比（裁决表）

| 属性 | BZD | MathModelAgent | LinHoMo（runtime 层） | LinHoMo（MODEL_IR 实验层） |
|---|---|---|---|---|
| assumptions | ✅ 字典`关键假设` | 🟡 文本（prompt 要求） | ✅ artifact（risks 转 assumptions） | ✅ `assumptions[]` |
| variables | ✅ 字典`模型输入/输出` | 🟡 文本 | ❌ | ✅ `variables[]` |
| parameters | ✅ 同上 | 🟡 文本 | ❌ | ✅ `parameters[]` |
| constraints | 🟡 字典`禁忌点` | 🟡 文本 | ❌ | ✅ `constraints[]` |
| objective | 🟡 `原理讲解`内嵌 | 🟡 文本 | ❌ | ✅ `objectives[]` |
| mechanism | ✅ 字典`原理讲解` | 🟡 文本 | ❌ | ✅ `mechanisms[]` |
| candidate alternatives | ✅ ≥2-3 强制 | ❌ 无 | 🟡 shortlist | ✅ 候选集 |
| selection rationale | ✅ `选用理由` | 🟡 弱（LLM 自撰） | 🟡 无（取 arena 第一） | ✅ |
| uncertainty | 🟡 部分 | ❌ | ❌ | ✅（间接） |
| sensitivity | ✅ 字典`检验方法` | 🟡 文本 | ❌（sensitivity_plan 仅在 MODEL_ARTIFACT v1 契约） | 🟡 `validations[]` |
| validation | ✅ 字典`检验方法` | ❌ 无 | ❌ | ✅ `validations[]` |
| failure conditions | ✅ 字典`禁忌点/模型缺陷` | ❌ | ❌ | ✅ `modeling_trace` |
| downstream dependencies | ✅ `cross_question_interface` | ❌ | 🟡 lineage 边 | ✅ `dependencies[]` |

**裁决**：属性覆盖最全的是 **BZD 字典**（静态知识）与 **LinHoMo MODEL_IR**（实验契约）；**MathModelAgent 的 Model 是属性最贫瘠的**（15 项中 9 项缺失或仅文本）。但关键区别：BZD 的属性是"知识库条目"而非"运行实例"；LinHoMo 的 MODEL_IR 属性是 typed 契约但**只在实验层存在**；MathModelAgent 的属性只是"要求 LLM 写的文字"。

### 2.3 是否 typed object？

- **BZD**：否。JSON dict / markdown 表行 / prose 三种形态，无 Model class、无 schema 校验器、无 DAG 节点类型。`query_dictionary.py` 只做字段白名单抽取。
- **MathModelAgent**：否。`schemas/A2A.py` 定义了 `CoordinatorToModeler/ModelerToCoder/CoderToWriter/WriterResponse` 四个 Pydantic 模型，但 workflow 与 agents 全程使用裸 `json.loads` + dict，**A2A schema 无任何 import**（`CONTRACT_ONLY`——"schema 存在 ≠ 能力实现"的教科书案例）。
- **LinHoMo**：分层。runtime 层**无 typed model**（通用 artifact + data dict）；legacy 有 `model_spec.schema.json`（MODEL_SPEC 六段）与 `model_dag.schema.json`；**MODEL_IR（`research/P15/model_representation/model_ir.schema.json`）是三者中唯一 typed、可机检的模型对象**（model_family/mechanisms/equations/dependencies/solvers/experiments/validations/claims/model_graph/modeling_trace），但仅在实验层。

### 2.4 Model 可执行操作对比

| 操作 | BZD | MathModelAgent | LinHoMo |
|---|---|---|---|
| 修改 | 🟡 文本层面 | ❌（只能重新生成） | ✅ `invalidate()` → 失效传播 → 局部重置（IMPLEMENTED） |
| 比较 | 🟡 表格（INSTRUCTIONAL） | ❌ | 🟡 候选评分（实验层）/ legacy 五维评分（INSTRUCTIONAL） |
| 追踪 | ❌ 无 | 🟡 DataRecorder 只记 token/对话 | ✅ lineage + Evidence Graph typed edges + run record（IMPLEMENTED） |
| 验证 | 🟡 prompt 级 | ❌ | 🟡 EvidenceGate 结构校验（非语义） |
| 重放 | ❌ | 🟡 可重跑全 workflow（无 seed 保证） | ✅ `replay.py`（IMPLEMENTED） |
| 复用 | ✅ 字典可重复查询 | ❌ 每任务全量重生成 | 🟡 台账层跨 run 引用 |
| 组合 | 🟡 文本建议 | ❌ | 🟡 `declare_cross_relation`（compares/extends/derived_from） |
| 回滚 | ❌ | ❌ | ✅ `rerun(node_id)` + superseded（IMPLEMENTED） |
| failure attribution | ❌ | ❌（只归因"代码报错"） | 🟡 legacy error_attribution.py / P15 FAILURE_TAXONOMY / V3 引擎 failures（归因闭环 CONTRACT_ONLY） |

### 2.5 Model 与论文文字是否解耦？

- **BZD**：部分解耦。字典是结构化独立资产（✅），但思路表→论文章节无任何绑定；总控台账要求"artifact 改变时标记下游过期"仅是提示词约定（INSTRUCTIONAL）。
- **MathModelAgent**：**完全耦合**。Model ≈ generated explanation text；论文正文 = Writer 对（Modeler 文本 + Coder 结果 + 文献）的再叙述；Model 没有独立于论文文本的运行时存在。V3 稍好（三份报告文件级分离），但模型仍是 markdown 散文。
- **LinHoMo**：**结构性解耦**。`PaperProjection.project(narrative)` 从 claim→evidence 结构生成大纲（模型章节 = model + `assumes` 边收集假设，projection.py:32-41）；死主张（dead arc）禁止投影；`validate.py` 强制论文数值追溯到 `figures/all_results.json`（validated result artifact），禁止论文阶段重估。**但正文文字仍是外部 LLM 产物**——解耦是"结构性"的，不是"语义性"的。

**裁决**：Model 与论文解耦程度：LinHoMo（结构投影 + 数值追溯）> BZD（字典独立但无绑定）> MathModelAgent（完全耦合）。

---

## 3. Model Selection

### 3.1 三者的选择机制定性

| 机制组件 | BZD | MathModelAgent | LinHoMo |
|---|---|---|---|
| model family taxonomy | ✅ 字典五类/20+ 分组（IMPLEMENTED 数据） | 🟡 仅 prompt 文本决策树（INSTRUCTIONAL） | ✅ 方法卡 family + catalog v3 + METHOD-DECISION-TREE |
| candidate generation | ✅ modeling-ideas 强制 ≥2（INSTRUCTIONAL） | ❌ 无 | ✅ MethodArena top-k（IMPLEMENTED）；legacy ≥2 候选（INSTRUCTIONAL） |
| suitability analysis | ✅ fit-assessment 11 维 + 四档（判定 INSTRUCTIONAL） | ❌ 无 | ✅ 卡内 scoring 字段排序（IMPLEMENTED）；legacy 五维评分（INSTRUCTIONAL） |
| decision rules | ✅ "单一致命不匹配即否决"（INSTRUCTIONAL） | 🟡 关键词→模型名映射 | ✅ 取 arena 第一；legacy 加权总分最高（INSTRUCTIONAL 执行） |
| model comparison | 🟡 同任务对比表（INSTRUCTIONAL） | ❌ | 🟡 候选评分（实验层） |

### 3.2 关键裁决：三者都是 heuristic routing，没有 structural model selection

- **BZD**：`cumcm-abcde-modeling-patterns.md` 提供 A–E 题型→推荐主线映射（**letter-based heuristic routing**），但同文件"反机械套题"五条铁律明确禁止"题号决定模型、复制历史模型"——路由是"字母键触发启发式检查清单"，不是模型名映射。**模型选择可信度完全押在 LLM 对 fit-assessment 11 维的主观判断上。**
- **MathModelAgent**：**cookbook 关键词路由**（最纯粹的问题类型→关键词→模型名）：预测→数据量<15→GM(1,1)、纯时序→ARIMA、多因素→回归/RF/XGBoost；评价→AHP/熵权/TOPSIS/DEA；分类→RF/SVM/K-means……（V2 `prompts/modeler.py`，V3 `_references/math_modeling_norms.md`）。系统不对"模型"做结构/语义比较。
- **LinHoMo**：V3 的 `MethodArena` 是三者中**唯一算法化**的选择路径（features 六键 → retriever 评分排序），但**致命边界**：`features` 不自动从题面推导，V3 默认硬编码 `{"problem_types":["evaluation"]}`（handlers.py:75-76）——任何题默认按"评价类"检索，除非外部传入 features。legacy 的 METHOD-DECISION-TREE / CUMCM-HMML 是 INSTRUCTIONAL 检索指南，无机械路由代码。

**统一裁决**：三个系统在"模型选择"上**无一达到 structural model selection**——没有基于题目结构的计算式选择、没有基准比较、没有选择的可计算证据。三者的差异只是"启发式的载体"：BZD 是专家规则文本、MathModelAgent 是关键词决策树、LinHoMo 是特征评分（但特征提取缺失）。**Problem type→keyword→model name 的路由在 BZD（字母信号）与 MathModelAgent（关键词）中真实存在并被文档化；LinHoMo 在 V3 中消除了该路由但用硬编码 features 取代之——同样不是结构选择。**

### 3.3 LinHoMo 特有的治理差异

- `allowed_modeling_structures` vs `core_methods`：benchmark 用允许结构清单而非黄金方法（`MODELING_KNOWLEDGE_GOVERNANCE.md`，P15 `problem_set.yaml` 实测 `allowed_model_families` 字段落地）——"多解模型原则"是三者中唯一显式防"金科玉律"的设计。
- `out_of_catalog` 不自动判错：2024_A 无专卡，retriever top-1 弱匹配，**用实验隔离而非放行**（P15 标记 `out_of_catalog: true`，不进主检验 p 值）——实现了"不自动判错"，同时保持测量纪律。

---

## 4. Model Construction

### 4.1 三者如何产生模型

| 系统 | 构造机制 | 有无结构化构造步骤 | 有无 assumption validation | 有无 constraint checking |
|---|---|---|---|---|
| BZD | LLM 依 modeling-ideas prompt 直接输出 markdown 表格 | ❌ 无（无符号生成/方程模板/求解器绑定/形式化目标约束生成） | 🟡 事后 assumption-checker（INSTRUCTIONAL），构造时无检查 | 🟡 checker prompt 要求"硬约束可验证"（INSTRUCTIONAL） |
| MathModelAgent | Coordinator→Modeler **单次** `llm.chat` 一次输出全部子问题模型文本 | ❌ 无（无交互迭代、无中间草案评审） | ❌ 无机械实现（V3 "假设敏感性预检"为 prompt 要求） | ❌ 无机械实现（V3 "验证约束"为文字要求） |
| LinHoMo | V3：**不构造**（do_model_construction 只把选中卡 risks 转 assumptions）；legacy：Actor→Critic→Improvement 迭代环（INSTRUCTIONAL，默认 1 轮最多 3 轮，产出 model_draft.md + critique.md） | 🟡 legacy 要求从基本定律推导/SymbolRegistry 注册/FormulaChecker 校验（全部 INSTRUCTIONAL，gate 只查 model_draft.md 存在） | 🟡 assumption-validator：必要性打分 ≥6.0 阈值（校验器 IMPLEMENTED，但打分内容由外部 agent 生成，gate 只查 JSON 存在+合法） | 🟡 FormulaChecker（括号/LaTeX 完整性，语法级） |

### 4.2 Model Spec → Artifact 转化路径

- **BZD**：无 Spec→Artifact 概念；模型直接以文字落入论文。
- **MathModelAgent**：Modeler 文本 → user message → Coder（模型文本即 Spec 即产物，无中间表示）。
- **LinHoMo**：legacy `MODEL_SPEC_TEMPLATE.md`（草稿）→ spec-auditor 渲染为 `output/MODEL_SPEC.md`（gate 查文件存在）——**转化是"模板渲染"，无类型化中间表示**；V3 无转化路径（model artifact 与 MODEL_SPEC.md 无程序关联）；P15 的 MODEL IR 是唯一"结构化构造"形态，但只在实验表示层。

**裁决**：三者中 **Model Construction 全部由 LLM 文本输出完成**，没有任何系统具备机械的模型构造器。差异仅在"事后审查"的强度：BZD 有最系统的 checkers、LinHoMo 有最系统的结构校验器（但都是语法/结构级）、MathModelAgent 有最真实的执行反馈（但反馈的是"代码跑通"而非"模型正确"）。

---

## 5. Knowledge → Capability

### 5.1 数学建模知识存在于哪里（三仓库对比）

| 位置 | BZD | MathModelAgent | LinHoMo |
|---|---|---|---|
| 主载体 | model-dictionary.json（5713 条）+ references/*.md（约 40 文件）+ calibrations/*.md（15 个） | V2：prompt 字符串（core/prompts/*.py）；V3：`_references/math_modeling_norms.md`（5.9KB 决策树） | 19 张方法卡 YAML + HMML + METHOD-DECISION-TREE + FAILURE_TAXONOMY + DecisionLog |
| 量级 | 字典 8.68MB / SKILL ~1700 行 | 知识 = 5.9KB 单文件 | 19 卡 × 丰富 schema（mechanism/formulations/solvers/requires/risks/anti_patterns/known_failures/structure_signals） |
| 消费方式 | 字典 → 脚本机械检索（IMPLEMENTED）；references → prompt 指令"完整阅读"（INSTRUCTIONAL） | 静态 prompt 注入（V2）；"如需领域判断，读取 ../_references/…"（INSTRUCTIONAL，LLM 自行决定是否读） | V3 retriever 评分（IMPLEMENTED，但 features 硬编码）；legacy CLI 可选（INSTRUCTIONAL）；P15 实验注入（全卡文本，实验操作非 runtime 能力） |
| RAG | 无 | **无**（README "ChromaDB+Rerank" 为 DOC_CLAIM，settings.RAG_* 无消费者） | 无（知识即结构化文件，无需检索增强） |

### 5.2 Knowledge → Agent → Model 因果链

- **BZD**：prompt 指令要求 + 一个检索脚本。**无任何实验/benchmark/ablation 证明"更多知识→更高建模质量"**。全仓无 tests、无 benchmark、无评估脚本。`learning-protocol.md` 自证："Never describe the Skill as 'trained' statistically unless an actual evaluated dataset and learning method exist"——**蒸馏主张是 DOC_CLAIM**。
- **MathModelAgent**：静态 prompt 文本 → LLM → 模型文本；无检索、无引用机制、无 grounding 校验；**无 benchmark、无评估脚本、无 ablation**（README 后期计划才有 "添加 benchmark"）。
- **LinHoMo**：**唯一有因果实验的系统**。P15-K001 预注册实验（2×2 Knowledge×Case + Sham 负控制，55 runs，主终点 = Model Construction Quality / L2 composite，3 evaluator 独立盲评）。结果：**Δ_K = +2.14，95% CI [+0.00, +6.41]，negative result**。

### 5.3 P15-K001 精确分析（本节必须逐条精确）

#### 5.3.1 Δ_K=+2.14, 95% CI [+0.00,+6.41] → negative result 的含义

CI 下界**恰好 = 0.00**（贴零不严格越过）。预注册决策门是频率学 CI：下界贴 0 意味着**无法排除零效应**；sign-permutation p=1.0（block=3 太少，无法产生显著置换）。**negative 的正确读法 = "未能证明"，不是"证明无"**。点估计为正（+2.14）在功效不足的设计里与 0 不可区分。

#### 5.3.2 Δ_Sham=+3.42 CI 跨 0 → 为什么"更多上下文"假说无法排除

Sham 臂（无关上下文）点估计 **+3.42 > Δ_K 的 +2.14**，CI [-2.56, +12.82] 跨 0（自身也不显著）。含义：**存在一条非知识路径可产生等量甚至更高的质量提升**——"更多上下文/更长的提示包"本身可能改善 LLM 表现（更充分的思考预算、更完整的题面上下文）。既然 Sham 的点估计高于知识臂，观察到的 Δ_K 完全可以被"通用上下文增益"解释，**知识内容的因果贡献无法与"更多上下文"分离**。

#### 5.3.3 为什么 Δ_K>0 但仍是 negative

点估计为正 ≠ 因果效应为正。频率学决策看的是 CI 是否排除零：CI [+0.00,+6.41] 贴零 → 不排除；block=3 使置换检验无分辨力（最小 p=0.25，功效不足以检测 <~6.4 分的真实效应）。**+2.14 与 0 在统计上不可区分**，因此按预注册门禁判 negative，不进 P15.2。

#### 5.3.4 为什么 Sham>K 是重要信号

这是实验设计最有价值的一点：**若不加 Sham 负控制，Δ_K 会被误读为知识效应**。Sham>K 证明存在混杂路径，并直接给出干预含义的分叉：若提升来自"更多上下文"，优化方向是 prompt/上下文工程；若来自"知识卡语义"，优化方向才是知识工程。P15-K001 的结论是：在当前注入方式（1 卡全文、中等剂量）下，**两者无法分开**。

#### 5.3.5 五层区分（必须分开的维度）

| 维度 | 结论 | 证据 |
|---|---|---|
| **Knowledge Ontology**（本体是否合理） | 结构丰富（mechanism/formulations/solvers/requires/risks/anti_patterns/known_failures/structure_signals） | mc-dp.yaml 实测；比 schema 更丰富 |
| **Knowledge Utilization**（是否被消费） | 是，非盲从：注入 33 runs 中 22 使用、21 调整、11 拒绝；**Sham 11/11 被拒绝**（注入不产生服从偏差） | P15-K001-REPORT |
| **Knowledge Causal Effect**（是否因果提升质量） | **未证实**（Δ_K negative） | CI [+0.00,+6.41]，block=3 |
| **Measurement Validity**（测量是否有效） | 主终点有效但有**天花板/粒度问题**：2019_C 全臂 87.18 零变异（评分工具有饱和点）；L2 混合"结构完备+内容正确" | REPORT + ATTRIBUTION |
| **Evaluation Power**（统计功效） | **不足**：block=3，最小 p=0.25，检测不出 <~6.4 分的真实效应 | ATTRIBUTION "统计功效" 节 |

#### 5.3.6 禁止写"知识卡无效"

实验证据明确不支持该结论：CI 上界 +6.41、2019_C 零变异（测量天花板）、2020_B 由单事件驱动（A/E 臂 Q1-only 罕见失败）、block=3 功效不足、注入剂量仅 1 卡、主终点 L2 粒度粗。**正确表述：knowledge causal effect 未被证实，且与 more-context 效应未分离；需更大功效 + 更细终点 + 剂量梯度才能裁决。**

#### 5.3.7 RQ5 measurement failure 与 capability failure 分离

RQ5 方法族命中率 A=0 / B=0.222 / C=0 / D=0.222 / E=0，表面是"LLM 识别方法族能力差"。但盲评样本（`06cb0fb3`）的 MODEL IR：`model_family.primary = "discrete_recurrence"`、`secondary = ["dynamic_programming"]`——**生成侧正确识别了 DP**，只是 primary 填了 schema 枚举示例串；而指标代码（`paired_analysis.py:194`）`ok = r["method_family"] in allowed` 只取 `deterministic.method_family_identified`（= primary），**不看 secondary**。根因是两套受控词表不一致（`model_ir.schema.json` 枚举含 discrete_recurrence vs `problem_set.yaml` 的 allowed_model_families 含 dynamic_programming）+ 指标只比对单串。**结论：RQ5 测的是"词表对齐度"，不是"方法族识别能力"——是 tertiary measurement limitation，与 capability failure 必须分离，且不影响主终点。**

### 5.4 Knowledge→Capability 横向裁决

| 系统 | 知识→能力因果证据 | 分级 |
|---|---|---|
| BZD | 无（蒸馏主张 DOC_CLAIM，learning-protocol 自证未统计训练） | 无证据 |
| MathModelAgent | 无（无 benchmark/ablation） | 无证据 |
| LinHoMo | 有实验但 negative（Δ_K 贴零、Sham 未排除） | **唯一有测量**，效应未证实 |

**贯穿立场**：Model Knowledge ≠ Model Capability。BZD 与 MathModelAgent 把"知识存在"当作"能力存在"；LinHoMo 是唯一用负结果诚实展示"知识注入≠能力提升"的系统——**这个 negative result 本身就是稀缺资产**：它证明该仓库能产出可信的否定结论。

---

## 6. Verification / Evidence / Reproducibility

### 6.1 验证器对比

| 系统 | 验证器 | 性质 | 分级 |
|---|---|---|---|
| BZD | 无代码验证器；8 个章节 checker 全为 prompt 级"核验"（要求页码证据、`无法核验` 标注） | 提示词要求 | INSTRUCTIONAL |
| MathModelAgent | V2：无验证器（唯一反馈 = stderr）；V3：`writing_check.sh` 文本门禁（占位符/泄漏/章节编号/图片存在性/caption，FAIL 硬错误）+ 编译 + PDF 视觉检查 | 文本结构门禁 | 门禁 IMPLEMENTED；数值一致性 WARN 子串检查；视觉 INSTRUCTIONAL |
| LinHoMo | `validate.py` 57 项（仓库结构/论文结构/数值追溯/文本护栏/正确性探针存在性）+ `EvidenceGate` E1–E4（结构性证据边）+ `gate.py` 29 agent 单步门禁 + `hash_chain.verify_chain()` | 存在性+结构+文本模式+数值追溯 | IMPLEMENTED（但均不判数学正确性） |

**关键裁决**：三者的验证器**无一能判定数学模型本身的对错**。差异在"验证的层次"：BZD 验证论文文本的评审规则符合性；MathModelAgent 验证代码执行成功与论文文本卫生；LinHoMo 验证结构完整性与数值可追溯性。**Schema Validity ≠ Mathematical Correctness** 在三个系统都成立，但只有 LinHoMo 通过 P15 盲评实证了这一点（FAIL runs 结构合法、只有人类 evaluator 发现覆盖失败）。

### 6.2 证据生命周期对比

| 系统 | Artifact Registry | Evidence Graph | 状态真源 | 失效传播 | 重放 |
|---|---|---|---|---|---|
| BZD | ❌ 无 | ❌ 无 | ❌ 无（静态 markdown calibrations） | ❌ | ❌ |
| MathModelAgent | 🟡 workdir 文件 + notebook 留痕（NotebookSerializer） | ❌ 无 | 🟡 Redis/WS 消息流（易失） | ❌ | 🟡 可重跑全 workflow（无 seed 保证） |
| LinHoMo | ✅ ArtifactRegistry（ID/版本/lineage/生命周期） | ✅ EvidenceGraph 14 种 typed 关系 + 失效传播 tier + coverage | ✅ 多真源（Event Log→Content Truth→Process Projection→Resume Truth，原子写） | ✅ `invalidate()` → 下游失效 → `rerun()` | ✅ `replay.py` 运行重放/差异归因 |

**Evidence Recording ≠ Evidence of Correctness**：MathModelAgent 的 notebook 留痕是"记录"；LinHoMo 的 Evidence Graph 是"结构化的记录"——两者都记录"发生了什么"，不证明"什么是正确的"。LinHoMo 的额外价值是**失效传播**：当上游 artifact 被 invalidate，下游依赖自动标记，这是三系统中唯一的"证据间因果维护"机制。

### 6.3 可复现性对比

| 系统 | 随机种子 | 确定性层 | 测试覆盖 | CI |
|---|---|---|---|---|
| BZD | 无（只要求论文作者披露种子） | 5 个脚本同输入必同输出（IMPLEMENTED 实测） | **零测试** | 无 |
| MathModelAgent | 无（seed 只存在于 norms.md 文字要求，INSTRUCTIONAL） | 解释器执行本身确定，但 LLM 层无 seed | ≈0（2 个测试文件，e2b 测试需真实 API Key 才跑） | 无（无 .github） |
| LinHoMo | env `code.random_seed 42`（loader 注入，IMPLEMENTED）；P15 实测 seeds [42,43,44] | 36k 行零 LLM 确定性 runtime（原子写/对账/重放） | 9,203 行测试，pytest 774 passed / 11 skipped（基线） | 无 CI（本地命令门禁） |

**裁决**：可复现性 LinHoMo >> MathModelAgent > BZD。但注意：**LinHoMo 的可复现性是"过程的"而非"模型构造质量的"**——重放保证同一状态能重建，不保证外部 LLM 的模型构造能被复现（LLM 层无 seed 控制，P15 生成侧是人工 Claude 会话）。

---

## 7. Engineering Architecture

### 7.1 模块划分与依赖

| 系统 | 架构形态 | 模块 | 依赖关系 | 扩展性 |
|---|---|---|---|---|
| BZD | 无框架的目录约定 | `<skill>/SKILL.md + agents/openai.yaml + references/ + scripts/ + assets/` | 相对路径引用 + `$bzd-xxx` 命名约定；无 import 解析/构建工具 | 新增 = 建目录 + 写 prompt；低耦合但无质量门；**49 个重复文件**（191 blob 中 49 冗余，唯一 blob 仅 142） |
| MathModelAgent | V2：FastAPI 分层；V3：Skill 集合 | V2：routers→flows→workflow→agents→{llm,tools,models,schemas,services}；V3：8 skill + `skills.sh.json` 注册表 | V2：顺序函数调用，非消息总线/事件驱动/图调度；V3：Harness 即运行时 | V2：靠配置扩展，但 workflow 硬编码 4 Agent（新增角色需改 workflow.py）；V3：skill 即插即用（npx skills add） |
| LinHoMo | 五层目录 + V3 DAG + 5 Role + V2 兼容层 | core/（runtime/roles/workflows/validators/schemas/evaluation/tools/skills/knowledge/env/templates/adapters）+ legacy（29 agent）+ research + projects | V3：WorkflowDAG→WaveExecutor→DefaultNodeExecutor→Registry/Graph/State（纯 stdlib）；env/config→loader 注入 | 新增卡 = 加 YAML；新增节点 = do_<node> + DAG 注册 + catalog 登记；新增竞赛 = 新模板目录（11 套） |

### 7.2 依赖方向与分层裁决

- **BZD**：依赖全部是"文本引用"，无编译期约束。工程卫生最弱（零测试、无 CI、无依赖清单、重复文件 26%）。
- **MathModelAgent**：V2 依赖清晰（agents→llm/tools 抽象），工程质量最高的模块是 Code Interpreter 抽象层（base_interpreter + interpreter_factory + local/e2b 双实现）；但存在**系统性死代码**：`schemas/A2A.py`（无 import）、`schemas/response.py: ApprovalMessage`（无发射方）、`settings.RAG_*/HIL_*/TAVILY_*/FALLBACK_*/EVALUATOR_*`（无消费者）——**README 与实现的系统性落差**。
- **LinHoMo**：依赖最严谨（schema→loader→消费方，零第三方运行时依赖），5 Role 重组 29 agent（官方口径：agent 数量不再作为架构质量指标）；**天花板**：认知能力不在 core 内，扩展"智能"只能通过指令/知识/外部 Agent。

---

## 8. Software Philosophy

### 8.1 工程哲学分类裁决

| 系统 | 分类 | 依据 |
|---|---|---|
| **BZD** | **A. Knowledge Engineering**（Expert→Skill→Agent）为主，边缘附着一层 C 式确定性脚本 | 核心资产是专家评审经验蒸馏成的提示词知识（16 道题评阅细则→references/calibrations）；Agent 是宿主 LLM 非仓库组件；5 个确定性脚本是 C 式可复现性的局部实现，但无 registry/验证门禁/重放；无 B 类多 Agent 编排 |
| **MathModelAgent** | **B. Agent Engineering**（Problem→Coordinator→Modeler→Coder→Writer），掺少量 C，几乎不含 A | 第一性对象是 LLM+prompt+工具调用工作流；知识以 prompt/静态 markdown 存在无检索；有 Scientific Runtime 雏形（真解释器/notebook 持久化/文本门禁/编译）但缺验证器/证据图/epistemic state；作者自述"不再做 Harness 层"坐实定位 |
| **LinHoMo** | **C. Scientific Runtime Engineering**（Problem→State→Artifact→Evidence→Verification→Replay），叠加 A 的知识资产，不是 B | Runtime+Guardrails 是零 LLM 的确定性"研究操作系统"（Registry/Graph/State/DAG/失效传播/重放/对账）；知识层（19 卡+HMML+FAILURE_TAXONOMY）是 A 成分；29 agent 无独立执行器/记忆/工具循环，只是指令文件（外部 LLM 消费） |

### 8.2 核心哲学问题裁决

| 问题 | BZD | MathModelAgent | LinHoMo |
|---|---|---|---|
| Agent 当作什么？ | **plugin**（宿主 LLM 的可选技能，yaml 只是展示卡） | **worker**（四段流水线的执行单元，顺序函数调用） | **external executor**（core 记录其 provenance：run_meta.model_provider/model_version/token_cost；P15 manifest generator: claude/claude-manual/console） |
| 模型当作什么？ | **知识库条目 + 论文散文**（无运行时存在） | **text**（Agent 间流转的字符串，无独立语义） | **artifact**（运行时层 = 台账选择记录；MODEL_IR typed 但仅实验层；**不是 executable scientific object**——runtime 不加载/运行/求解模型） |
| 状态当作什么？ | **无状态**（chat history 属于宿主） | **workflow context**（内存态 + Redis 消息流，易失） | **persistent state**（Event Log→Content Truth→Process Projection→Resume Truth，原子写，可重建可对账） |
| 拥有 evidence lifecycle？ | ❌ | 🟡（notebook 记录，无维护） | ✅（registration→typed edges→invalidation→retraction→coverage） |
| 拥有 decision lifecycle？ | 🟡（评审决策有记录模板，无代码消费） | ❌ | ✅（DecisionLog，真源之一） |
| 拥有 failure lifecycle？ | ❌ | 🟡（只归因代码报错） | ⚠️ 部分（发现=外部；记录=TAXONOMY+error_attribution；修正=外部 agent；**自动发现/自动修正闭环缺失**） |

**裁决**：真正拥有 evidence / decision lifecycle 的只有 LinHoMo；failure lifecycle 三者均未闭环（LinHoMo 的"自动发现+自动修正"缺失是最明显的空洞——这正是它与 MathModelAgent 反射循环形成互补的地方）。

---

## 9. Scientific Philosophy

| 维度 | BZD | MathModelAgent | LinHoMo |
|---|---|---|---|
| **可证伪性** | 无可证伪机制——"知识有效"无定义、无测量、无判据（DOC_CLAIM） | 无可证伪机制——README 的 RAG/HIL/Tavily/Fallback 甚至无法区分"已实现/计划中" | **三者唯一**：预注册协议 + 频率学 CI 决策门 + sign-permutation；Δ_K negative 是可证伪的产物 |
| **因果推断** | 无（蒸馏主张无对照） | 无（无 benchmark/ablation） | **唯一有**：2×2 因子 + Sham 负控制 + blocked 配对；虽功效不足，但因果问题被正确提出 |
| **测量效度** | 评分锚点来自经验（DOC_CLAIM 包装成 IMPLEMENTED），无评估者一致性测量 | 无（"论文编译通过"即成功） | 盲评 3 evaluator 独立 + Generator≠Evaluator 隔离 + 泄漏扫描 PASS + 评分标准 v1.0；但 L2 有天花板（2019_C 零变异） |
| **负结果的价值** | 无负结果概念 | 无 | **唯一**：Δ_K negative 被如实报告为"未能证明"，且归因报告区分 measurement limitation 与 capability failure |
| **预注册/冻结** | 无 | 无 | **三者唯一**：DATA FREEZE 165 文件、44 规格文件零漂移、55/55 REGISTERED |

**裁决**：LinHoMo 的 preregistered experiment 与 frozen protocol 是三者中**唯一的正式科学实验**。这不是修辞——它把"知识注入是否提升模型构造质量"从一个不可证伪的宣称变成了一个有 CI、有负控制、有盲评、有归因分析的测量对象。BZD 与 MathModelAgent 的问题不在于"答案错误"，而在于"问题从未被提出"。

---

## 10. Strongest Critique of BZD

不是"缺少 runtime"这种表面问题。深层批判：

**1. 知识如何转化成 capability？无因果证据。**
BZD 把"16 道题评阅细则蒸馏"作为核心卖点，但全仓零测试、零 benchmark、零 ablation。`learning-protocol.md` 自己承认"未统计训练"——**这是 DOC_CLAIM 被当作 IMPLEMENTED 事实使用的模式**。没有任何对照实验证明"用了 BZD Skill 的评审"优于"给了同样上下文的裸 LLM"。

**2. Skill 是否真的比更多 context 更有效？**
P15-K001 的 Sham 结果（+3.42 > Δ_K +2.14）在 BZD 的语境下是一个未被回答的质疑：BZD 的 Skill 价值可能大部分来自"更多上下文/更结构化提示"而非"专家知识的语义内容"。BZD 没有任何机制区分这两者。

**3. 知识表示仍依赖 Agent 自己解释。**
references/calibrations 是自然语言；模型选择（fit-assessment 11 维）与打分（rubric 构建、原子扣分公式 `problem_earned=max(0, 0.90×w−Σdeductions)`）都是**把规则文本喂给 LLM 再信任其执行**。权重和=100 只在 prompt 里要求，无代码断言；"单一致命不匹配即否决"无机械执行。**INSTRUCTIONAL 是 BZD 的默认状态。**

**4. 硬编码经验值被脚本放大的问题（最需警惕的审计模式）。**
`competition_context.py` 中 `national_probability_ceiling = 0.0681`（未上榜学校国奖概率）、`advisor_multiplier 1.2/0.8`、"30%–50%"强校预估、赛区难度分、`is_modeling_strong_school` 标记——这些**硬编码在脚本/CSV 里、看起来确定，但都是 owner 经验值**。脚本的"确定性"会**放大**而非**验证**这些先验：一个无出处的 6.81% 经 `award_position.py` 线性插值后变成"可复算的百分位"，观感上从"猜测"升级为"计算"。**DOC_CLAIM 被包装成 IMPLEMENTED 的输出**——这是本审计中最危险的模式，因为它混淆了"算术正确"与"数值正确"。

**5. 评审一致性无保障。**
rubric 生成、逐条扣分、模型适配判定、章节诊断均为 INSTRUCTIONAL，无种子、无校验器、无多轮一致性检查——同一论文两次评审结果一致性无任何机械保障。评审的"规则化形式主义"（atomic-deduction-scoring）是优点，但它把规则形式化了，没有把**执行**形式化。

**价值裁决**：BZD 作为"评审知识库 + 评审规则文本 + 确定性校准脚本"的组合，在**评审领域**是三者中最深的；但它的知识→能力因果链完全未经受验，且经验数值被脚本外衣包装是系统性风险。

---

## 11. Strongest Critique of MathModelAgent

不是"架构比较简单"。深层批判：

**1. 是否把数学建模真正等价成 LLM workflow completion？**
是。系统对"成功"的定义 = 四段 Agent 顺序跑完 + 论文编译通过 + 文本门禁通过。没有任何环节把"模型是否成立"作为一等公民。数值一致性只是"数字是否出现在论文文本里"的 round(4) 子串搜索（WARN 级）——**Workflow Completion ≠ Scientific Validity** 在此系统中最赤裸。

**2. 模型对象有无独立语义？**
无。Model 是流转于 Agent 之间的字符串；`schemas/A2A.py` 的 typed schema **已写好却未被使用**（全仓库无 import）——这是"CONTRACT_ONLY 即死代码"的最清晰案例。模型没有 typed 表示，就无法被校验、比较、追踪、回滚。

**3. 何时知道自己错了？**
**只有在代码报错/编译失败时**。模型选择错误、假设错误、约束被违反但不崩溃、数值系统性偏差——**系统永远不知道自己错了**。代码解释器反馈的是"代码是否跑通"，不是"模型是否正确"。约束被违反但 scipy 正常返回解，系统无感知。

**4. 是否真正具备 epistemic state？**
无。无模型置信度、无不确定度、无"未验证"标记、无证据链对象。DataRecorder（`utils/data_recorder.py`）只记 token/费用/对话，不记结果真值。

**5. README 与实现的系统性落差（DOC_CLAIM 清单）。**
README "功能特性"列出 RAG（ChromaDB+Rerank）、HIL（6 决策动作）、Web Search（Tavily）、四层容错（Fallback Hand Off / Evaluator Shadow Mode / Feedback Rerun）、litellm 全模型支持、daytona——**全部无代码消费者**（settings 空配置 + 无 import）。A2A schema、ApprovalMessage 同理。**审计结论：以上均为 DOC_CLAIM。** 4.4k stars 的影响力与作者免责声明（"AI 生成仅供参考，目前水平直接参加国赛获奖是不可能的"）形成强烈对照——任何吸收方都必须把它当作"会跑的流水线"而非"已验证的建模引擎"。

**价值裁决**：MathModelAgent 的价值不在其宣称的"全流程自动化"，而在三个具体实现：①Code Interpreter 抽象层（base_interpreter/interpreter_factory/local/e2b，工程质量最高的模块）；②notebook 全量留痕（NotebookSerializer）；③反射循环 + provider 抽象。这些是 execution substrate 的资产，与它的"认知架构"无关。

---

## 12. Strongest Critique of LinHoMo

不是"代码还没做完"。深层批判：

**核心问题：是否已证明 formal scientific runtime 可以提升 Model Construction Quality？**

**没有。** P15-K001（唯一直接测量）给出 Δ_K=+2.14 CI [+0.00,+6.41]：**知识注入路径未证实**；runtime 本身对质量的影响**从未被因果测量**（无"裸 LLM vs 带 harness"对比臂）。因此诚实的定位是：**它是"更好的数学建模研究基础设施"，不是（已被证明的）"更好的数学建模系统"**。作为研究基础设施：证据充分（测量、冻结、盲评、provenance、对账全部 IMPLEMENTED 且经 55-run 实验验证）；作为数学建模系统：证据不足（runtime 不构造/不求解/不验证模型内容；构造质量由外部 LLM 决定；知识因果效应未证实）。

### 六大风险逐条回应

**Risk 1 Formalized nonsense（schema 合法 + graph 完整 + validator PASS 但模型本身错误）**
**回应：防护机制部分存在，但语义空白是结构性的。** 存在的防护：formula_checker（括号/LaTeX 完整性）、symbol_registry（符号一致性）、assumption_validator（必要性评分）、symbolic_verifier/invariant_tracker/cross_model_checker/physics_model（validate.py 引用）——全部是语法/结构/一致性校验。**证据缺口**：V3 runtime 的 experiment 节点产出的 result artifact 是**无数值占位**（claim 字面量 `"{qid} 结论"`），EvidenceGate E1–E4 只查**边存在**——**一个含错误数值的 result artifact 也能 PASS 门禁**。P15 盲评证实：FAIL runs（如 06cb0fb3 只绑定 Q1）在 schema/结构上合法，只有人类 evaluator 按 rubric 逐维评分才发现覆盖失败。**Risk 1 成立且未闭环**——防护网防"形式非法"，不防"内容错误"。

**Risk 2 Over-formalization（变成 research process management system 而非数学建模引擎）**
**回应：部分成立，且项目自己承认。** V3 runtime 36k 行中绝大多数是过程管理（registry/graph/state/dag/invalidation/replay/reconcile/projection），数学构造/求解**不在 runtime 内**。THREE_LAYER_ARCHITECTURE 自述："继续向下挖掘会得到一个'科研操作系统'而不是'数模 Agent'"——作者已自我警觉。P15-K001 的 Δ_K negative 与"过程管理不提升模型质量"一致（但注意：P15 测的是知识注入，**不是 runtime 本身**——runtime 对质量的影响未被因果实验测过）。

**Risk 3 Infrastructure without capability gain（schema/contract/graph/validator 增多但质量未提升）**
**回应：这是 P15-K001 最直接的判决点——但注意实验测的是知识注入，不是基础设施。** Δ_K negative 说明"知识注入"这一条能力路径未显示显著质量提升。但必须公平：①基础设施本身（冻结/盲评/盲评密钥/泄漏扫描）**让"质量测量"变得可信**——没有它，任何 Δ 都是不可信的；②2019_C 全臂 87.18 零变异说明 L2 评分工具有天花板，可能掩盖真实差异；③该实验**没有**对比"无基础设施的裸 LLM"vs"有基础设施"，因此**不能判定基础设施零增益**。结论：尚无证据证明 formal runtime 提升 Model Construction Quality；有证据证明它提升了**测量质量与过程可信度**。

**Risk 4 False scientific confidence（状态/证据/契约完善 → 错误的安全感）**
**回应：真实存在，且已有反例。** 证据 1：2019_C 全臂 87.18 零变异——若解读为"模型质量稳定良好"就是 false confidence，正确解读是**评分饱和**。证据 2：RQ5 的 A=0 命中率若解读为"LLM 识别方法族能力为零"就是 false confidence，正确解读是词表错位。证据 3：EvidenceGate 全绿 + 55/55 REGISTERED 容易给人"实验完整"的安全感，但 **REGISTERED ≠ 模型正确**（FAIL runs 结构合法）。缓解机制存在（STATE_TRUTH 限定状态为"投影可重建"、reconcile 只读对账、归因报告明确写 tertiary limitation），**但使用者的安全感可能越过这些细节**。

**Risk 5 Execution weakness（理论/认知架构强于实际 execution substrate）**
**回应：成立，且是跨仓库对比中最明显的短板。** V3 runtime **不做任何数值计算**（实验节点只建台账）；代码执行、多轮运行、结果验证全部在外部 Agent 的 sandbox 中发生，core 只接收文件产物。对比 MathModelAgent：LinHoMo 的 core **没有 code interpreter、没有 agent 间消息传递、没有工具循环**——29 个 agent 之间**无运行时互操作**（它们只是 SKILL.md 文档，通过 filesystem 交接产物）。"多 Agent 协作"在 LinHoMo = 文件的顺序/条件流转（gate 判定），不是并发智能体协商。**epistemic 架构显著强于 execution substrate**——这是它作为"研究基础设施"合理、作为"数模求解 Agent"不足的根源。

**Risk 6 Ontology weakness（model family/mechanism/method/solver/implementation 未完全分离）**
**回应：成立，RQ5 即实证。** `discrete_recurrence`（model_ir.schema.json 枚举）vs `dynamic_programming`（problem_set.yaml 的 allowed_model_families）——**同一建模思想两种命名**，且 RQ5 指标只比对 primary 单串。MODEL IR 在实验层已把 model_family/mechanisms/equations/solvers/experiments 分列，**但 runtime 层 model artifact 只有 `family` 一个串**；方法卡的 family 是自由字符串（19 卡无统一枚举注册）。结论：实验表示层已接近 6 层分离的 5/6；**runtime 层与受控词表层严重不足**——"表示层领先、生产层滞后"。

**风险排序裁决**：Risk 5（execution weakness）> Risk 1（formalized nonsense）> Risk 2（over-formalization）> Risk 4（false confidence）> Risk 6（ontology）> Risk 3（infra without capability gain，当前证据不足以定罪，但方向需警惕）。

---

## 13. Comparative Scorecard

评级：Weak / Moderate / Strong / Very Strong

| 维度 | BZD | MathModelAgent | LinHoMo | 依据要点 |
|---|---|---|---|---|
| Modeling Knowledge | **Very Strong** | Weak | **Strong** | BZD 5713 条字典 + 15 校准文件（IMPLEMENTED 数据）；LinHoMo 19 卡 + 治理文档；MathModelAgent 5.9KB 单文件 |
| Modeling Theory | Moderate | Weak | **Strong** | LinHoMo 有唯一成文治理哲学（LLM 构造/知识约束/证据裁决）；BZD 有 fit-assessment 11 维；MathModelAgent 无理论 |
| Model Representation | Moderate | Weak | **Strong**（实验层）/ Weak（runtime 层） | BZD 字典结构化但无类型；MathModelAgent 纯字符串；LinHoMo MODEL_IR typed 但仅实验层、runtime 层单串 |
| Model Selection | Moderate | Weak | Moderate | 三者均非 structural selection；BZD 适配判定最深但 INSTRUCTIONAL；MathModelAgent 关键词路由；LinHoMo 算法化检索但 features 硬编码 |
| Model Construction | Weak | Moderate | Weak | 全部 LLM 文本输出；MathModelAgent 有代码反馈回路可修正执行错误；LinHoMo V3 不构造 |
| Verification | Weak | Moderate | **Strong** | LinHoMo 57 项 + EvidenceGate + hash_chain（结构级）；MathModelAgent 文本门禁 + 编译；BZD prompt 级 |
| Evidence | Weak | Moderate | **Very Strong** | LinHoMo EvidenceGraph 14 关系 + 失效传播 + 多真源；MathModelAgent notebook 留痕；BZD 无 |
| Reproducibility | Moderate | Weak-Moderate | **Very Strong** | LinHoMo replay/reconcile/原子写/seed 42；BZD 脚本确定但 LLM 层不确定；MathModelAgent 无 seed |
| Execution | Weak | **Strong** | Weak | MathModelAgent 真解释器（local/e2b IMPLEMENTED）；BZD 无；LinHoMo runtime 零计算 |
| E2E automation | Moderate | **Strong** | Moderate | MathModelAgent V2 全流水线已实现（题→PDF）；BZD 到评审为止（无论文生成）；LinHoMo V2 legacy 可跑 29 步 + V3 台账 |
| Scientific Experimentation | None | None | **Very Strong** | 唯一预注册 + 盲评 + 冻结 + 负控制实验（P15-K001） |
| Software Architecture | Weak-Moderate | Moderate | **Very Strong** | LinHoMo 五层 + V3 DAG + 5 Role + schema 契约；MathModelAgent FastAPI 分层但有死代码；BZD 目录约定 + 49 重复文件 |
| Extensibility | **Strong** | Moderate | **Strong** | BZD 加 Skill 极低耦合；MathModelAgent V3 skill 即插即用但 V2 workflow 硬编码；LinHoMo 加卡/节点/竞赛有登记流程 |
| Engineering maturity | Weak | Moderate | **Very Strong** | LinHoMo 36k 行 + 9.2k 测试行 + 774 passed；MathModelAgent 测试≈0 无 CI；BZD 零测试无 CI |
| Scientific credibility | Weak | Weak | **Strong** | LinHoMo 能产出可信负结论；MathModelAgent README DOC_CLAIM 落差；BZD 蒸馏主张无证据 |

**裁决**：没有赢家通吃。**LinHoMo 在知识资产/验证/证据/可复现/科学实验/工程成熟度上碾压**；**MathModelAgent 在执行/端到端自动化上碾压**；**BZD 在评审知识与经验密度上碾压**。三者恰好互补于"认知架构—执行基质—评审知识"三个象限——这是本报告最重要的结构发现。

---

## 14. What LinHoMo Should Borrow

### 14.1 从 BZD 吸收（进入 modeling knowledge / reviewer policy / model selection policy / benchmark / critic / competition methodology）

| 吸收项 | 进入位置 | 理由 |
|---|---|---|
| `atomic-deduction-scoring.md` + `rubric-construction.md`（90% 评委封顶、原子检查点 1/2/3 扣减、`problem_earned=max(0,0.90×w−Σdeductions)`、格式系数 `(format+10)/20` 确定性映射、低分自底向上复评 35 分帽） | **reviewer policy / judge-critic**（三仓库中最强的 reviewer policy 细节） | 把"评委主观分"拆成可审计、可复算的算术——与 LinHoMo 的 judge-critic role 天然契合 |
| `award_position.py` / `score_percentile.py` / `competition_context.py`（锚点插值 + clamp + 学校/赛区/教师与论文质量分严格分离） | **competition methodology 层**（独立于 runtime core） | 评审公平性边界设计（不回写质量分）值得抄；但作为数据资产挂接，不进入 core 语义 |
| model-dictionary 字段设计（假设/禁忌点/缺陷/检验方法/资料声明） | **modeling knowledge card schema 增补**（LinHoMo 卡已有 risks/known_failures/validation，可对照补齐"禁忌点/检验方法"的措辞规范） | 假设-失败条件-验证三元结构是成熟 schema |
| `learning-protocol.md` 归纳纪律（权重溯源/条件化规则/跨案例≥2 才提升/禁止宣称 statistically trained） | **knowledge operations policy** | 与 LinHoMo governance 同源，可强化"知识运营纪律" |
| 反机械套题护栏（禁止题号决定模型/复制历史数值） | **model selection policy 强化** | 对 cookbook 退化的主动防御 |
| **不应污染 runtime core**：硬编码经验值（6.81%、30–50%、advisor_multiplier 1.2/0.8）——BZD 的"DOC_CLAIM 包装成 IMPLEMENTED"模式正是 LinHoMo 证据纪律要禁止的；若引入校准数据，必须带来源/出处/有效期，且不能从"确定性脚本"获得虚假权威 |

### 14.2 从 MathModelAgent 吸收（进入 execution layer / adapter）

| 吸收项 | 进入位置 | 理由 |
|---|---|---|
| **Code Interpreter 抽象层**（`base_interpreter.py` + `interpreter_factory.py` + local/e2b 双实现，含字体注入、附件上传/产物下载双向同步） | **execution adapter（最高优先级）** | 全仓库工程质量最高的模块，统一 execute_code 契约、可插拔——直接补上 LinHoMo Risk 5 的最短板 |
| `notebook_serializer.py`（每次执行追加 code cell + output，按段落留存输出供下游引用） | **experiment evidence 记录 adapter** | "实验证据留痕"的朴素但实用形态，可挂接 Evidence Graph 的 produces 边 |
| Provider 抽象（`core/llm/providers/` + `StandardResponse` 归一化 + `_validate_and_fix_tool_calls` + `_validate_config`） | **LLM adapter** | 比 litellm 更薄更可控，干净样板 |
| 反射循环（`coder_agent.py` + `get_reflection_prompt` + MAX_CHAT_TURNS/MAX_JSON_RETRIES） | **自愈 adapter** | 异常→反思→重试带上限；可作 external executor 的"自动修正"参考（补 LinHoMo failure lifecycle 的修正环） |
| 17 套 Typst/LaTeX 竞赛模板 | **template 资产** | 转 LaTeX 工作量已完成 |
| `writing_check.sh`（FAIL/WARN 分级、引擎自适应 typ/latex） | **verifier 模式参考** | 可迁移的文本门禁模式 |
| **不应进入 core semantics**：cookbook 模型选择（关键词决策树）、markdown 报告充当 Model、死配置/死 schema（RAG/HIL/Tavily/Fallback/Evaluator）、round(4) 子串"数值一致性"、以及"9 步自动验收"的宣传口径 |

---

## 15. What LinHoMo Must NOT Become

四条红线，逐条明确：

**红线 1：不能变成 research process management system 而非 modeling engine。**
当前仓库 = 研究过程管理基础设施 + 知识资产 + 测量实验；数学建模引擎（模型构造/求解/验证的计算能力）在外部 Agent 里。若继续只加 registry/graph/validator/投影而不加任何计算能力，over-formalization 将从"风险"变成"现实"。**判断标准**：如果新增一行代码永远在"记录/校验/投影"而从不"计算/求解/执行"，就是越过红线。

**红线 2：不能让 schema validity 冒充 mathematical correctness。**
EvidenceGate 全绿 ≠ 模型正确；57 项校验 PASS ≠ 数学成立；REGISTERED ≠ 有效结论。P15 已经证明 FAIL runs 结构完全合法。**判断标准**：任何校验报告必须标注"结构校验/语义校验"边界，禁止把 validate.py 的 PASS 表述为"模型正确性验证通过"。

**红线 3：不能让 infrastructure growth 冒充 capability gain。**
方法卡从 19→N、validator 从 21→更多、schema 增多——这些是**过程资产**，不是**能力证据**。能力证据只能是受控实验的 Δ（如 P15 系列的效应量）。**判断标准**：任何"新增 X 提升了系统"的宣称必须附因果实验或明确标注为推断；P15-K001 的 negative 必须作为后续一切能力宣称的基准参照。

**红线 4：不能丢失 LLM-free Harness 的核心定位。**
核心运行时是零 LLM 的确定性"研究操作系统"——这是它区别于 MathModelAgent（Harness 即 LLM 工作流）的根本。若把 LLM 调用引入 core（如让 LLM 做 gate 判定、做 evidence 登记），会破坏可重放、可对账、可原子写的性质。**判断标准**：core 的确定性必须保持（36k 行零 LLM SDK 依赖是资产不是负债）；LLM 只能在 external executor 层、以 provenance 记录的方式参与。

**附加红线（由 RQ5 教训推出）**：不能让受控词表分叉累积成系统性盲点。`discrete_recurrence` vs `dynamic_programming` 这类分叉必须通过统一枚举注册表（如 `catalog/model_families.yaml`）在下一轮实验前收敛，否则 RQ5 类的"词表对齐度量"会反复污染指标解读。

---

## 16. Next Experimental Priority

### 16.1 哪个方向最有科研价值？

候选：Knowledge effect / Representation effect / Evidence effect / Critic effect / Verification effect / Replay effect / Model ontology effect。

**判断：Representation effect（结构化 Model 表示）最有科研价值**，其次是 Evidence effect（证据要求）。理由：

1. **P15-K001 的直接教训**：Δ_K=+2.14 CI 贴零、Δ_Sham=+3.42 更高——**"更多知识"这条路已被测量且未被证实，且被"更多上下文"假说压制**。再投一个更大功效的"更多知识"实验（K002-K 变体）边际价值低。
2. **Sham>K 的干预含义**：提升可能来自"更完整的提示/思考预算"，而非"知识语义"。而 LinHoMo 真正区别于裸 LLM 的是**结构化表示 + 证据要求**——这两者从未被因果测量过。
3. **机制合理性**：知识注入只改变"提示内容"；representation 改变"输出的结构与可机检性"——后者才能与 runtime 的 EvidenceGate、PaperProjection、数值追溯形成闭环。若 representation 有效，整个 harness 的价值假设被激活；若无效，则 harness 的能力增益承诺被证伪。**无论结果如何，都是决定"LinHoMo 是建模引擎还是工作流系统"的关键裁决实验。**

### 16.2 最干净的下一轮实验设计：P15-K002（Representation × Evidence）

**设计目标**：在完全可控条件下分离"知识内容"、"上下文剂量"、"结构化表示"、"证据要求"四个机制，并以修复后的测量（L3/L4 终点 + 多级族匹配）做裁决。

**Arms（同一 LLM、同一 token budget、同一时间预算、同一工具集、同一 Python env、同一 evaluator、同一 rubric）**：

| Arm | 知识注入 | 表示要求 | 证据要求 | 对照角色 |
|---|---|---|---|---|
| A. Baseline | 无 | 无（自由文本） | 无 | 复现 MathModelAgent/BZD 条件 |
| B. BZD-style knowledge injection | 方法卡全文（同 K001 全卡注入） | 无 | 无 | 知识内容效应（对比 A） |
| C. Unstructured context control | Sham 无关上下文（同 K001） | 无 | 无 | "更多上下文"假说（对比 B） |
| D. Structured Model Artifact | 无 | **必须输出 MODEL_IR v1.1（schema 校验 + 六维本体）** | 无 | **Representation effect（对比 A）** |
| E. Structured + Evidence | 无 | MODEL_IR | **每个 claim 必须引用 experiment/validation 块，且数值来自实际运行结果** | **Evidence effect（对比 D）** |
| F. Critic（可选） | 无 | MODEL_IR | 有 | model-critic 评审环（INSTRUCTIONAL→可测） |

**设计要点（必须满足）**：
- **Blocked 设计**：block ≥ 6（≥6 blocks 才有 2^6=64 置换，最小可达 p≈0.016；8 blocks → 256 置换）。P15-K001 的 block=3 是功效失败的根因，K002 至少翻倍。
- **Same model**：全部 arms 同一 LLM 实例与版本（冻结 provider/model_version）。
- **Fixed token budget / fixed time / fixed tools**：三固定作为实验约束写入 protocol，防"更多上下文"通过 token 差异偷偷进入。
- **Measurement validity 修复**：①终点从 L2 单层改为 L2（结构完备）+ L3（可执行性/可解性）+ L4（对 ground truth 的数值正确性，针对有标准答案的子问题）；②方法族命中改为"primary OR secondary OR mechanism OR solver 任一命中即算族命中"（修复 RQ5 词表错位）；③统一受控词表注册表（`catalog/model_families.yaml`）先行收敛；④evaluator 盲评保持 Generator≠Evaluator 隔离 + 泄漏扫描。
- **Independent blind evaluation**：沿用 P15 3-evaluator 独立评分 + 评分标准版本化。
- **预注册 + 冻结**：沿用 P15-K001 的 DATA FREEZE 与规格零漂移纪律。

**预测与决策门**：
- 若 D（或 E）显著优于 A 且优于 B/C → **Representation effect 成立**，harness 的结构化表示是能力来源，知识注入只是弱代理。
- 若 E 显著优于 D → **Evidence requirement 独立贡献成立**，证据门禁不是摆设。
- 若 B≈C ≈ A → 知识注入在当前剂量下无内容效应，"更多上下文"假说被强化——则停止扩卡，转向表示/证据/执行层。
- 若全部无差异 → harness 的能力增益承诺被证伪，LinHoMo 应重新定位为纯研究基础设施并如实声明。

**统计功效说明**：K001 block=3 最小 p=0.25 检测不出 <~6.4 分效应；K002 block≥6 可将可检测效应下限压到 ~4 分区间（仍需事后功效分析，不预先承诺）。若资金/时间受限，优先保证 D/E 两臂与 block≥6，B/C 可缩小。

---

## 17. Final Strategic Judgment

### 17.1 假设条件

三者面对**完全相同**的 20 道高质量数学建模题：同一个 LLM、相同 token budget、相同工具、相同执行时间、相同 Python environment、相同 evaluator、相同 scoring rubric。

### 17.2 逐项预测（区分"已有证据"与"推断"）

| 问题 | 最可能胜出者 | 证据 vs 推断 |
|---|---|---|
| 谁最可能选对模型？ | **推断：LinHoMo（若 features 正确注入）或 BZD**；MathModelAgent 最弱 | **证据**：三者均无 structural selection（§3）；BZD 有最深的适配判定文本（fit-assessment 11 维）+ 5713 条字典；LinHoMo 有唯一算法化检索但 features 硬编码（handlers.py:75-76 默认 evaluation）；MathModelAgent 是纯关键词路由。**推断**：给定"相同工具"意味着无预先特征提取，BZD 的字典+适配判定深度可能略优；若外部 analyst 正确提取 features，LinHoMo 的 MethodArena 最可复算 |
| 谁最可能构造正确模型？ | **推断：MathModelAgent**（可执行性意义上）；LinHoMo 次之（结构化意义上） | **证据**：三者构造均为 LLM 文本输出（§4）；MathModelAgent 是唯一有真实代码执行反馈回路的（stderr→反思→重试），能修正**执行错误**；LinHoMo 的 MODEL_IR + critic 能提升**结构完备性**但 V3 runtime 不构造。**推断**：对"可运行的正确模型"，代码反馈回路胜出；对"结构正确、可审计的模型"，结构化表示胜出 |
| 谁最可能发现自己的模型错了？ | **推断：MathModelAgent（仅执行层）；无人能发现选择层错误** | **证据**：MathModelAgent 只在代码报错/编译失败时自知（§11）；LinHoMo EvidenceGate 只查结构，P15 FAIL runs 需人类 evaluator 才发现（§12 Risk 1）；BZD checkers 为 prompt 级。**推断**：模型选择错误、假设错误、约束违反不崩溃——三系统全部无感知 |
| 谁最可能修改模型？ | **证据：MathModelAgent** | **证据**：反射循环（MAX_CHAT_TURNS=30）是唯一自动修改路径（IMPLEMENTED）；LinHoMo `invalidate()→rerun()` 只触发重跑不产生新认知；BZD 仅建议性。**推断**：MathModelAgent 自动修正执行错误最可靠，但修改的是代码不是模型语义 |
| 谁最可能产生可复现结果？ | **证据：LinHoMo** | **证据**：replay/reconcile/原子写/seed 42/多真源（§6.3）；MathModelAgent notebook 留痕但无 seed；BZD 脚本确定但 LLM 层不确定。**注意**：LinHoMo 可复现的是**过程**，外部 LLM 的模型构造本身不可复现（P15 生成侧是人工会话） |
| 谁最可能生成高质量论文？ | **推断：BZD（若被用作评审者）／MathModelAgent（若指端到端生成）**；LinHoMo 产生可追溯论文 | **证据**：MathModelAgent 是唯一端到端生成可编译论文的系统（V2 拼接 + V3 章节 + writing_check 门禁 + 编译）；BZD 是唯一有系统评审规则的（但**不写**论文）；LinHoMo PaperProjection 生成大纲 + validate.py 数值追溯 + 外部 writer。**推断**：若"高质量"=可提交可编译 → MathModelAgent；若"高质量"=符合评阅规则 → BZD 规则最有价值（但需 LLM 执行）；若"高质量"=数值可追溯无伪造 → LinHoMo |
| 谁在 blind evaluation 中得到更高 Model Construction Quality？ | **推断：LinHoMo 与 MathModelAgent 接近，LinHoMo 略优（结构化）；BZD 居中偏下** | **证据**：P15-K001 证明 LinHoMo 的 L2 评分在结构完备维度有基线优势且可测量（全臂 ≥87.18 起）；但知识注入因果效应未证实（Δ_K 贴零）——**harness 对构造质量的提升是推断而非证据**。MathModelAgent 的代码反馈可能提升执行正确性但无评分测量。**推断**：在"结构完备+内容正确"的 rubric 下，要求 MODEL_IR 结构化输出的 LinHoMo 最可能得分更高；在"可运行代码正确"的 rubric 下，MathModelAgent 可能更高 |

### 17.3 核心问题裁决

**哪个项目最接近真正的 Mathematical Modeling Computing System？**

**裁决：没有任何一个是完整的"Mathematical Modeling Computing System"；LinHoMo 在架构上最接近，MathModelAgent 在执行基质上最接近，BZD 在知识密度上最接近。** 一个真正的数学建模计算系统需要三者的合体：LinHoMo 的运行时/证据/状态架构（Model 作为 artifact + 可重放 + 可对账）+ MathModelAgent 的 Code Interpreter 执行层（真实计算反馈）+ BZD 的知识密度与评审规则算术（5713 条字典 + 原子扣分）。当前三者各自缺失一块：LinHoMo 缺计算、MathModelAgent 缺模型语义、BZD 缺运行时。

**哪个只是把专家知识包装成 Skill？**

**BZD**（最纯粹）。它的全部能力 = 专家评审经验 → 提示词 → 宿主 LLM 自律执行；唯一机械部分是边缘算术脚本。MathModelAgent V3 也属于 Skill 包装，但 V2 有真实运行时；BZD 没有。

**哪个主要是 LLM workflow automation？**

**MathModelAgent**。Coordinator→Modeler→Coder→Writer 是教科书式的 LLM 文本接力流水线；"成功"定义 = 流水线跑完 + 编译通过。它是三者中最能"跑通"的，也是最没有"模型语义"的。

**LinHoMo 要如何证明自己不是一个越来越复杂的科研工作流系统？**

三条可执行证明路径，按优先级：

1. **执行层补计算（补 Risk 5）**：引入 MathModelAgent 式 Code Interpreter adapter，让 runtime 的 experiment 节点从"建台账"变成"真执行"——当 result artifact 携带真实数值、EvidenceGate 校验的不再是边的存在而是"claim 与 result 数值的对账"时，它就从工作流系统变成了计算系统。
2. **P15-K002 证明 capability gain（补 Risk 3）**：用 Representation × Evidence 实验证明结构化模型表示（而非更多上下文）显著提升 Model Construction Quality。若 Δ_Rep 显著而 Δ_K 不显著，则证明 harness 的价值在"表示与证据"而非"知识堆积"——这是对"越来越复杂的工作流系统"指控的最直接反驳。
3. **Fresh B0 泛化测量（补 Risk 1/4）**：在从未见过的竞赛题（非校准样本）上盲评，报告可复现的构造质量分布，并如实报告 negative/positive——用测量纪律本身证明它追求的是"建模质量"而非"流程美观"。

**最终一句话**：BZD 是最深的"评委"，MathModelAgent 是最快的"流水线"，LinHoMo 是最诚实的"实验室"——而三者合起来才接近用户真正想要的"数学建模计算系统"。LinHoMo 的下一战不在知识库，不在 schema，而在**把计算接回 runtime、把表示变成一等对象、并用受控实验证明这两件事提升了模型构造质量**。

---

*报告完成。所有关键技术判断以三份证据档案的代码级证据为准；证据分级标签（IMPLEMENTED / CONTRACT_ONLY / DOC_CLAIM / INSTRUCTIONAL）贯穿全文；冲突处已裁决而非并列。*
