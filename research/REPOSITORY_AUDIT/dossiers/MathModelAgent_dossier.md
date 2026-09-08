# MathModelAgent 证据级深度技术审计档案

- **仓库**: `jihe520/MathModelAgent`（https://github.com/jihe520/MathModelAgent）
- **审计基准**: `main` 分支，HEAD commit `83d8783187a2d29dda1b046cb667009cc50c8203`（2026-08-17，"docs: 引用 sci-box #107"）
- **审计日期**: 2026-09-08
- **访问方式**: 在线抓取（无本地副本）。证据来源 = GitHub API（元数据/文件树/提交记录）+ raw.githubusercontent.com 全文 + README 原文 + 关键文件逐行精读
- **证据分级标签**: `IMPLEMENTED`（代码中有真实 runtime 路径或测试证据）/ `CONTRACT_ONLY`（有 schema/interface 定义，无 runtime 执行证据）/ `DOC_CLAIM`（文档/注释声称，代码证据不足）/ `INSTRUCTIONAL`（仅 prompt/skill 文本要求，无机械强制执行）

---

## 1. 仓库概览

### 1.1 定位
数学建模竞赛（国赛 CUMCM / 美赛 MCM-ICM / 华数杯 / 华为杯 / 五一杯 / 数维杯等）**全流程自动化多智能体系统**：用户给一道赛题 → 系统自动完成"问题分析 → 建模 → 写代码 → 跑实验 → 写论文 → 排版 → 验收"。仓库同时包含 **两代架构**：

| 代 | 形态 | 状态 |
|---|---|---|
| V1/V2 | 自研 Harness：FastAPI + Redis + WebSocket 后端 + Vue3/Electron 前端 + 4 Agent（Coordinator/Modeler/Coder/Writer） | 保留在 `backend/`+`frontend/`，README 明确"以后不会再做其他部分" |
| V3 | 纯 SKILLS 驱动：Claude Code / Codex 等 Harness + `skills/` 目录的 8 个 skill | README 明示"项目蒸馏成完全由 SKILLS 驱动，不再做 Harness 层"，**当前主线** |

作者原话（README Thinking 节）："两年前，我都是自己实现一套 Agent 框架，现在和以后更多的 Agent 产品直接基于 Harness 如 Codex / Claude Code / Pi + SKILLS 来构建"——这是理解该仓库的关键：**它自己放弃了自研 Harness 路线**。

### 1.2 规模与活跃度（证据）
- GitHub API 元数据：`size=99,677 KB`，`created_at=2025-01-30`，`pushed_at=2026-09-08`，**98 commits**，stars ≈ 4.4k，forks ≈ 369，license = 自定义（"个人免费使用，请勿商业用途"）
- 提交活跃度（`/commits?per_page=10`）：最新代码提交 `83d8783`（2026-08-17）、`13e3995`（2026-08-09）、`11f3862`（2026-07-20，含 "MAX_JSON_RETRIES=3" 修复）；近期提交大量 `Co-authored-by: Claude Opus 5 (1M context)` / `Cursor`——**AI 辅助开发特征明显**
- Releases：15 个，最新 `mathmodel v0.0.15`（README 快照显示 "3 days ago"）
- 文件树（`git/trees/main?recursive=1`，91KB JSON，~1,400 个跟踪路径）：根目录 `.claude/`、`.cursor/`、`backend/`、`docs/`、`frontend/`、`skills/` + `CLAUDE.md`、`README.md`、`README_EN.md`、`docker-compose.yml`；**无 `.github/`（无 CI）、无 tests 目录于根层**

### 1.3 技术栈（证据）
- 后端：Python 3.12+（CLAUDE.md），FastAPI（`backend/app/main.py`），Redis pub/sub + WebSocket（`services/redis_manager.py`、`services/ws_manager.py`），`jupyter_client`（本地解释器），`e2b-code-interpreter`（云端解释器），`nbformat`（notebook 序列化），`requests`（OpenAlex），Pydantic v2
- LLM 接入：自写 provider 抽象（`core/llm/providers/`：OpenAIChatProvider / OpenAIResponsesProvider / AnthropicProvider），**无 litellm 导入**（README 声称 "支持所有模型 litellm" → 见 §11，`DOC_CLAIM`）
- 前端：Vue3 + TypeScript + Vite + shadcn-vue（`frontend/src/`）
- V3：Claude Code / Codex Skills（Markdown SKILL.md + bash 脚本），Typst + LaTeX(xelatex) 双引擎，17 套竞赛模板

---

## 2. 真实 Runtime Pipeline 重建

### 2.1 V2 后端管线（`IMPLEMENTED`，全部有代码路径）

用户输入一道题后（以国赛 C 题为例）的完整执行链：

```
① 前端(Vue3) --HTTP POST /modeling--> modeling_router.create_modeling_task(Problem{task_id, ques_all, comp_template, format_output})
   [HTTP REST / JSON schema（schemas/request.py: Problem）]
② modeling_router --asyncio.create_task--> process_task(task_id, problem)  （asyncio.wait_for 超时 18000s）
   [Python asyncio task / workflow state]
③ process_task --Flows()._process_task(...)--> flows.py: Flows
   [Python function call]
④ Flows --实例化--> workflow.py: MathModelWorkFlow(task_id, ...).execute()
   [Python function call / workflow state]
⑤ execute() 内部（顺序，无并行、无 DAG）：
   a. setup() 建立 work_dir = backend/project/work_dir/<task_id>  ← 之后所有产物落盘于此
      [filesystem artifact]
   b. CoordinatorAgent.run(problem_statement)
      → llm.chat(system=COORDINATOR_PROMPT + FORMAT_QUESTIONS_PROMPT, history=[user: 题目全文])
      → LLM 返回 JSON 字符串 {questions:[{question,title}], ques_count}
      → json.loads 解析（MAX_JSON_RETRIES=3，commit 11f3862）
      [Agent message / JSON string / prompt injection（把整个题目原样塞进 user message）]
   c. ModelerAgent.run(questions)
      → llm.chat(system=MODELER_PROMPT) → JSON {questions_solution: {问题: 模型文本}}
      → json.loads 解析
      [Agent message / JSON string；"模型"在此处 = 一段 markdown/文本]
   d. for 每个子问题:
        CoderAgent.run(subtask_title, solution)
        → llm.chat(tools=[execute_code_tools], tool_choice="auto")（functions.py 定义 JSON schema）
        → LLM 返回 tool_call execute_code(code) → CodeInterpreterFactory.create()（interpreter_factory.py，
          按 settings.CODE_INTERPRETER_TYPE 选 local 或 e2b）
        → LocalCodeInterpreter.execute_code（local_interpreter.py，jupyter_client KernelManager 起 ipykernel 内核）
          或 E2BCodeInterpreter.execute_code（e2b_interpreter.py，AsyncSandbox.run_code，上传 csv/xlsx/字体、下载产物）
        → 返回 (combined_text, error_occurred, error_message)：stdout/stderr/error/traceback + 图片
        → 结果以 tool message 追加进 history；若异常 → get_reflection_prompt（prompts/shared.py）注入反思指令，continue
        → 循环直到 LLM 不再发 tool_call 或 len(history) > settings.MAX_CHAT_TURNS(=30)
        [tool invocation / JSON schema / Agent message / prompt injection（反思 prompt）/ filesystem artifact（notebook.ipynb、图片、结果文件）]
   e. for 每个论文小节（get_sections()，模板来自 config/md_template.toml）:
        WriterAgent.run(section, content)
        → llm.chat(tools=[search_papers_tools]) → 若发 tool_call search_papers → OpenAlexScholar.search_papers
          （openalex_scholar.py，真实 HTTP 调 api.openalex.org，返回标题/摘要/作者/引用格式）
        → 输出该节 markdown/LaTeX 文本（prompt 要求插入图片 markdown、脚注引用）
        [tool invocation / Agent message]
   f. UserOutput.write_paper(...)（models/user_output.py）：把各节文本 + 各子问题解答 + 图片路径拼接
      → 输出 paper.md（或 .tex）到 work_dir
      [filesystem artifact / 字符串拼接——这就是"论文"的生成方式]
   g. cleanup()
⑥ 全程 redis_manager.publish_message → Redis pub/sub 频道 task:<id>:messages → ws_router websocket /task/{task_id} → 前端渲染
   [database state / WebSocket]
```

**各"谁"的答案（V2）**：
- 谁理解题目：`CoordinatorAgent`（prompt 仅要求把题目拆成 questions，**无语义理解层**，原样摘录题面文本）
- 谁拆分子问题：Coordinator 的 JSON `questions` 字段（`prompt injection`，LLM 自行判断；无机械校验子问题数量与依赖）
- 谁判定问题类型：`ModelerAgent`（prompt 内嵌 cookbook 决策树，见 §4）
- 谁生成候选模型：**没有**——Modeler 一次 prompt 直接给最终模型文本
- 谁选择模型：Modeler（cookbook 关键词路由，见 §4）
- 谁构造模型：Modeler（纯文本生成，无结构化对象）
- 谁写代码：`CoderAgent`（LLM 生成 code 字符串，经 tool_call 交给解释器）
- 谁运行实验：`BaseCodeInterpreter` 及其 local/e2b 实现（**真实执行，IMPLEMENTED**）
- 谁验证：**无独立验证器**；唯一反馈 = 代码解释器的 stdout/stderr/error（LLM 自己看）
- 谁发现错误：CoderAgent 反射循环（LLM 自读报错文本 + reflection prompt）
- 谁修改：CoderAgent 自己重试（最多到 MAX_CHAT_TURNS）
- 谁最终评价：**无**（无 evaluator/scorer；README 中 Evaluator 属 roadmap）
- 谁写论文：`WriterAgent`（逐节生成）+ `UserOutput`（字符串拼接）

### 2.2 V3 SKILLS 管线（Harness 驱动）

```
用户: /1start-mathmodel "完成这个数学建模任务"（claude --dangerously-skip-permissions / codex --yolo）
① 1start-mathmodel/SKILL.md：AskUserQuestion 问偏好（竞赛/语言/引擎）→ 创建 plan.md + todo.md → Agent 工具依次触发下游 skill
   [HIL=Harness 原生 AskUserQuestion / filesystem artifact / harness Agent tool]
② 2analysis-modeling/SKILL.md：读题面+附件+（按需读 _references/math_modeling_norms.md）→ 产出 reports/ANALYSIS_MODELING_REPORT.md
   （子问题拆解、假设敏感性预检、变量、目标函数、约束、求解算法、代码任务清单）
   [INSTRUCTIONAL / filesystem artifact]
③ 3coding-visual/SKILL.md：按 plan.md 建 code/ + figures/，逐子问题实现、运行、验证约束、出图 → reports/RESULTS_REPORT.md + figures/*.pdf
   [INSTRUCTIONAL（"必须验证约束""先保证可行解"均为文本要求）/ filesystem artifact]
④ 4drawio/SKILL.md：技术路线/流程图 → DRAWIO_REPORT.md（可选）
   [INSTRUCTIONAL]
⑤ 5writing/SKILL.md：AskUserQuestion 选排版引擎（LaTeX 默认）→ 复制 17 套模板之一到 paper/ → 按引擎写章节
   → paper/main.typ 或 main.tex（章节 include 结构）
   [INSTRUCTIONAL / filesystem artifact]
⑥ 6verity/SKILL.md：9 步验收 —— 文本质量门禁(scripts/writing_check.sh，唯一机械化步骤) → 章节数量/标题顺序 → 图表引用 →
   占位符/泄露 → 数值一致性 → 参考文献 → 编译(typst/xelatex) → PDF 视觉检查(pdftoppm 逐页，要求"模型有视觉能力") →
   reports/VERIFY_REPORT.md (PASS/FAIL)
   [bash script = IMPLEMENTED 的机械检查；视觉检查 = INSTRUCTIONAL]
```

### 2.3 重点机制裁决

| 机制 | 裁决 | 证据 |
|---|---|---|
| Coordinator 调度 | `IMPLEMENTED`（V2 顺序调度） | `core/workflow.py: MathModelWorkFlow.execute()` |
| Modeler→Coder 交接 | `IMPLEMENTED`（文本接力） | workflow.py：`json.loads(...)["questions_solution"]` 逐题传入 |
| Code Interpreter 真执行 | `IMPLEMENTED` | `tools/local_interpreter.py`（jupyter_client）、`tools/e2b_interpreter.py`（AsyncSandbox）、`tools/interpreter_factory.py` |
| RAG 检索 | **无**（`DOC_CLAIM`） | 全树无 chroma/langchain/retrieval 模块；`settings.RAG_*` 无消费者 |
| HIL 人机协作 | **V2 无**（`CONTRACT_ONLY`）；V3 = Harness 原生 AskUserQuestion | `schemas/response.py: ApprovalMessage`（confirm/edit/regenerate/ask/skip/abort）定义但全仓库无发射方、无审批端点（已核 `routers/` 全部 4 个文件） |
| Web research | `IMPLEMENTED`（仅 OpenAlex 学术检索，writer 专用）；Tavily = `DOC_CLAIM` | `tools/openalex_scholar.py: OpenAlexScholar.search_papers`；README"Web Search: Tavily"无代码 |
| Fallback | V2 仅 `IMPLEMENTED` 一层（LLM 重试+退避）；"Fallback Hand Off / Evaluator Shadow Mode / Feedback Rerun" = `DOC_CLAIM` | `core/llm/llm.py: LLM.chat()` 重试循环；`FALLBACK_*`/`EVALUATOR_*` 配置无消费者 |
| LLM routing | `IMPLEMENTED`（**静态**每 Agent 一模型 + api_type 选 provider；非动态路由） | `core/llm/llm_factory.py: LLMFactory.get_all_llms()`；`llm.py: _create_provider()` |
| 子问题类型判定/模型选择 | `INSTRUCTIONAL` | `prompts/modeler.py` 决策树；V3 同见 `_references/math_modeling_norms.md` |

---

## 3. "Model" 到底是什么

### 3.1 定义
**V2**：系统把 "Model" 定义为 `questions_solution: dict[str, str]` 中**一个子问题对应的字符串值**——即 Modeler 单次 prompt 输出的文本（含模型名、假设、公式草稿的 markdown）。它经 workflow 作为 user message 原样传给 Coder，Coder 据此写代码，Writer 再据 Coder 结果写论文。

**V3**：Model = `reports/ANALYSIS_MODELING_REPORT.md` 中的 markdown 小节（"问题一模型"等），结构由 prompt 规定（符号/假设/目标函数/约束/求解方法/输入输出/校验方法），仍为**文本制品**。

**不是**：typed object、Model Spec/JSON schema、DAG 节点、evidence-backed object。`schemas/A2A.py` 定义了 `CoordinatorToModeler/ModelerToCoder/CoderToWriter/WriterResponse` 四个 Pydantic 模型，但 workflow 与 agents 全程使用裸 `json.loads` + dict，**A2A schema 无任何 import**（`CONTRACT_ONLY`）。

### 3.2 Model 属性逐项检查（V2 与 V3 相同结论）

| 属性 | 有/无 | 形式 | 机械强制？ |
|---|---|---|---|
| assumptions | 有（文本） | prompt 要求写假设 | 无 |
| variables | 有（文本） | prompt 要求符号说明 | 无 |
| parameters | 有（文本） | 要求"参数来源三选一"（writer prompt） | 无 |
| constraints | 有（文本） | 建模报告/论文章节要求 | 无 |
| objective | 有（文本） | 要求目标函数 | 无 |
| mechanism | 有（文本） | 公式/推导为 LLM 文本 | 无 |
| candidate alternatives | **无** | 不生成候选集；仅 writer prompt 要求写"与备选方案对比"（可编造） | 无 |
| selection rationale | 弱（文本） | 要求写"为什么选这个模型" | 无（LLM 自行撰写） |
| uncertainty | **无** | 无置信区间/不确定性传播对象 | — |
| sensitivity | 文本 | 论文章节要求 | 无 |
| validation | **无** | 无模型级验证器 | — |
| failure conditions | **无** | 无 | — |
| downstream dependencies | **无** | 无 | — |

### 3.3 Model 生命周期操作

| 操作 | 支持？ | 说明 |
|---|---|---|
| 修改 | 否 | 只能让 LLM 重新生成文本 |
| 比较 | 否 | 无模型对比/评分 |
| 追踪 | 弱 | DataRecorder 记录对话历史/Token（`utils/data_recorder.py`），但无模型级溯源 |
| 验证 | 否 | 无模型验证器 |
| 重放 | 弱 | 可重跑整个 workflow，但无确定性保证（无固定 seed） |
| 复用 | 否 | 每任务全量重生成 |
| 组合 | 否 | 无 |
| 回滚 | 否 | 无版本/快照 |
| failure attribution | 否 | 错误只归因到"代码报错"，模型选择错误不可归因 |

### 3.4 与论文的解耦
**Model ≈ generated explanation text**，完全耦合。论文正文 = Writer 对（Modeler 文本 + Coder 结果 + OpenAlex 文献）的再叙述；Model 没有独立于论文文本的运行时存在。V3 稍好：模型写在 `ANALYSIS_MODELING_REPORT.md`、结果在 `RESULTS_REPORT.md`、论文在 `paper/`，三者是**文件级分离**，但模型本身仍是 markdown 散文，无 schema 校验其"可执行性/一致性"。

---

## 4. Model Selection 机制

- **model family taxonomy**：有，但**只存在于 prompt 文本**（V2 `prompts/modeler.py`；V3 `_references/math_modeling_norms.md`）。V3 版是完整的手写决策树（五大题型：优化/预测/评价/分类聚类/机理动力学；每类下有方法选型表）。
- **candidate generation**：无（单次输出最终模型，无候选集）。
- **suitability analysis**：无（无评分/排序/对比计算）。
- **decision rules**：**cookbook 关键词路由**。V2 modeler prompt 明文示例：
  - 预测 → 数据量<15→GM(1,1)；纯时序→ARIMA/指数平滑/Prophet；多因素→线性回归/岭回归/RF/XGBoost；非线性→LSTM/GRU
  - 评价 → AHP（主观）/熵权法（客观）/TOPSIS/DEA/灰色关联/PCA+TOPSIS
  - 分类 → RF/SVM/K-means；优化 → LP/IP/NLP/GA/NSGA-II；统计 → Pearson/ANOVA/SHAP；文本 → VADER/LDA；仿真 → 蒙特卡洛/元胞自动机
- **结论**：属于 **heuristic routing / model-name classification**，**不是** structural model selection。系统不对"模型"做结构/语义比较；"选对模型"完全依赖 LLM 对 prompt 决策树的遵循（`INSTRUCTIONAL`）。`_references/math_modeling_norms.md` 自述定位为"规范知识库，不指定必须用 X"（该文件对"题型防错"的约束也全部是文字建议）。

---

## 5. Model Construction 机制

- **产生方式**：V2 = `CoordinatorAgent → ModelerAgent` 单次 `llm.chat`（`prompts/modeler.py` 系统提示 + questions JSON），一次输出全部子问题模型文本。**无交互迭代、无中间草案评审**。
- **assumption validation**：无机械实现。V3 `2analysis-modeling` 要求写"假设敏感性预检"（模糊表述≥2 种解释 + 快速验算 + 最终采用解释）——纯 prompt 要求（`INSTRUCTIONAL`）。
- **constraint checking**：无机械实现。V3 `3coding-visual` 要求"验证约束""先保证可行解，再优化目标值"；`math_modeling_norms.md` 列了 scipy 约束符号、整数取整、数据泄露等常见错——全部为文字防错清单（`INSTRUCTIONAL`）。
- **Code Interpreter 是否真正执行模型代码并反馈结果**：**是（`IMPLEMENTED`）**。这是本仓库最强的工程点：
  - `tools/base_interpreter.py: BaseCodeInterpreter`（execute_code / add_section / section_output / get_created_images / 文件同步抽象）
  - `tools/local_interpreter.py: LocalCodeInterpreter`（jupyter_client 内核，真实执行，捕获 stdout/stderr/error，超时）
  - `tools/e2b_interpreter.py: E2BCodeInterpreter`（E2B 沙箱，初始化注入中文字体，上传附件/字体，执行后下载全部分散文件，base64 结果经 Redis/WS 推前端）
  - `tools/notebook_serializer.py: NotebookSerializer`（每次执行追加 code cell + output，产出可再编辑的 notebook.ipynb；`segmentation_output_content` 按段落留存输出供 Writer 引用）
  - 反馈回路：stdout/stderr/error → tool message → LLM 反思重试（`coder_agent.py` + `prompts/shared.py: get_reflection_prompt`）
- **局限**：解释器反馈的是"代码是否跑通"，**不是"模型是否正确"**；数值合理性问题（如约束被违反但代码不报错）完全无感知。

---

## 6. Knowledge 的地位

- **数学建模知识存在哪里**：
  - V2：**prompt 字符串**（`core/prompts/*.py`，编译进系统提示），静态、无检索、无版本化知识库。
  - V3：`skills/_references/math_modeling_norms.md`（5.9KB，18 个小节：题型识别、选型速查、评价/预测/优化/机理/图论/统计分型指南、论文规范、MCM 专项），由 2/3/4/5/6 号 skill 通过"如需领域判断，读取 ../_references/…"引用——**`INSTRUCTIONAL`**（LLM 自行决定是否读取；无机械注入）。
  - 另有 `skills/typst-author/`（Typst 语法知识，5writing 按需调用）与 `skills/mathmodel-figure-templates/`（绘图模板）。
- **RAG**：**不存在**。README "📚 RAG 知识库: ChromaDB + Rerank" 与 settings 的 `RAG_ENABLED/RAG_DB_PATH/RAG_TOP_K/RAG_EMBEDDING_MODEL/RAG_RERANKER_MODEL` 均为空壳（无检索代码、无 embedding 代码、无注入点）→ `DOC_CLAIM`。
- **Knowledge → Agent → Model 因果链**：V2 = 静态 prompt 文本 → LLM → 模型文本；V3 = 静态 markdown 规范（可选读取）→ LLM → 建模报告。**无检索、无引用机制、无 grounding 校验**。
- **有无实验/benchmark/ablation 证明知识注入的 causal effect**：**无**。README 后期计划里才有 "添加 benchmark"；仓库无 benchmark 目录、无评估脚本、无 ablation。

---

## 7. Verification / Evidence / Reproducibility

- **验证器**：
  - V2：**无**模型/结果验证器。唯一"发现错误"机制 = CoderAgent 反射循环（LLM 读 stderr 后自行修复）。
  - V3：`skills/6verity/` 是唯一的验证环节，其中 **`scripts/writing_check.sh`（5.3KB，`IMPLEMENTED`）** 提供机械文本门禁：占位符（PLACEHOLDER/TODO/待补充…）、内部工作流文件名泄漏（RESULTS_REPORT/CLAUDE.md/figures/*.json…）、include 缺失/重复、章节编号顺序、一级标题格式（Typst `= ` 空格、LaTeX `\section`）、图片文件存在性、caption 存在性、重复标题、参考文献存在——这些是 **FAIL（硬错误）**。
  - 数值一致性 = **WARN 弱检查**：把 RESULTS_REPORT 的指标名（rmse/mae/…/权重/误差）与论文做子串匹配；把 `all_results.json` 前 100 个绝对值≥1 的数字 round(4) 后取前 30 个看是否出现在论文文本中——**字符串包含检查，非数值对账**（`INSTRUCTIONAL` 层面的"一致性"由 LLM 自查）。
  - 编译：`typst compile` / `xelatex` 双遍（`IMPLEMENTED`，编译器可用才跑）。
  - PDF 视觉检查：pdftoppm/mutool/magick 逐页导出后由"模型视觉能力"看——**条件性 `INSTRUCTIONAL`**，无视觉能力时仅记录未执行。
- **模型何时知道自己错了**：**只有在代码报错/编译失败时**（stderr/compile error）。模型选择错误、假设错误、数值系统性偏差、约束违反而不崩溃——**系统永远不知道自己错了**。V3 的 VERIFY_REPORT 只覆盖"论文文本/编译/版式"硬错误，明确"不重新建模、不重新跑大规模实验"。
- **epistemic state（认知状态）**：**无**。无模型置信度、无不确定度、无"未验证"标记、无证据链对象。DataRecorder（`utils/data_recorder.py`）只记 token/费用/对话，不记结果真值。
- **可复现性**：随机种子仅存在于 `_references/math_modeling_norms.md` 的文字要求（"随机算法要固定随机种子，并用多次运行或稳定性指标说明"）——`INSTRUCTIONAL`，代码无 seed 固定。V3 `3coding-visual` 要求 `RESULTS_REPORT.md` 含"可复现运行方式"——同为文本要求。
- **测试覆盖**：`backend/app/tests/` 仅 2 个文件：`test_e2b.py`（1 个用例 `TestE2BCodeInterpreter.test_execute_code`，无 `E2B_API_KEY` 即 skip，需真实云沙箱的集成烟测）、`test_common_utils.py`（538B，fetch 失败但体量微小）；其余为 `mock/res.json`（19.7KB 假数据）、`res.md`、`get_config_template.py`（helper）。**无 CI（无 .github）**。结论：测试覆盖 ≈ 0，且非确定性（依赖外部 API Key）。

---

## 8. Software Architecture

### 8.1 V2 模块划分与依赖（`IMPLEMENTED`）

```
routers/ (modeling, ws, common, files)          ← FastAPI 入口
   └─▶ core/flows.py: Flows._process_task
         └─▶ core/workflow.py: MathModelWorkFlow.execute
               ├─▶ core/agents/agent.py: Agent（基类：history/轮次/记忆压缩）
               │    ├─ coordinator_agent.py  ──▶ core/prompts/coordinator.py
               │    ├─ modeler_agent.py      ──▶ core/prompts/modeler.py
               │    ├─ coder_agent.py        ──▶ core/prompts/coder.py + shared.py + core/functions.py(execute_code schema)
               │    └─ writer_agent.py       ──▶ core/prompts/writer.py + shared.py + core/functions.py(search_papers schema)
               ├─▶ core/llm/llm.py: LLM ──▶ core/llm/llm_factory.py ──▶ core/llm/providers/{base,openai_chat,openai_responses,anthropic}.py
               ├─▶ tools/ interpreter_factory ──▶ base_interpreter ──▶ local_interpreter | e2b_interpreter
               │      + notebook_serializer + openalex_scholar + matplotlib_setup
               ├─▶ models/user_output.py: UserOutput（论文拼接）
               └─▶ schemas/{request,response,enums,A2A(死),tool_result}
services/redis_manager + ws_manager（消息广播，供 llm.send_message 与解释器推流）
config/setting.py + model_config.toml + md_template.toml（节模板/prompt inject）
utils/{common_utils,data_recorder,cli,track,RichPrinter,log_util}
```

- **multi-agent workflow 实现方式**：**顺序函数调用**，非消息总线、非事件驱动、非图调度。Agent 间无对象传递，只有 LLM 对话 + JSON 字符串 + 文件系统。Agent 基类 `agent.py`（12.2KB）承担 history 管理/轮次控制/记忆压缩（CLAUDE.md 明文），四 Agent 均为其子类。
- **扩展性**：靠配置（每 Agent 独立 model/api_key/base_url；md_template.toml 可增删论文小节）与 provider/解释器两处抽象；但 workflow 硬编码 4 Agent 顺序，新增角色需改 `workflow.py`。

### 8.2 V3 SKILLS 架构
- 8 个 skill：`1start-mathmodel`（入口）、`2analysis-modeling`、`3coding-visual`、`4drawio`、`5writing`、`6verity`、`doctor`、`typst-author` + 内部依赖 `_references`（`skills/skills.sh.json` 注册表）。
- 实现方式：SKILL.md（frontmatter：name/description/**allowed-tools** + 工作流步骤），由 Claude Code/Codex 加载执行；阶段产物 = 工作区文件（reports/*.md、code/、figures/、paper/）。**无运行时，无调度代码**——Harness 即运行时。
- 扩展性：**skill 即插即用**（`npx skills add jihe520/MathModelAgent --all`），可组合（单独跑分析/只写论文），模板与知识库可自由扩展；姊妹项目 `jihe520/sci-box`（scibox-figure/scibox-diagram）已拆分。

---

## 9. 工程哲学分类

**B. Agent Engineering（主），掺少量 C 的成分，几乎不含 A。**

判断依据：
- 第一性对象是 **LLM + prompt + 工具调用** 的工作流（Agent Engineering 的核心特征）；知识以 prompt/静态 markdown 存在，无检索/无因果验证 → 不是 Knowledge Engineering。
- 有 Scientific Runtime 的**雏形**（真实代码解释器、notebook 持久化、workdir 制品、文本门禁脚本、Typst 编译），但**缺验证器/证据图/epistemic state** → 不是完整的 Scientific Runtime Engineering。
- 作者自述（README Thinking）明确"不再做 Harness 层"，把执行语义全部外包给 Claude Code/Codex——进一步坐实"Agent Engineering 以 Harness 为运行时"的定位。

---

## 10. 关键文件路径索引

| 判断 | 路径（GitHub 相对路径，main 分支） | 类/函数 |
|---|---|---|
| 后端入口 | `backend/app/main.py` | `app = FastAPI(...)`、lifespan |
| 任务入口/超时 | `backend/app/routers/modeling_router.py` | `create_modeling_task`、`process_task`、`asyncio.wait_for(..., 18000)` |
| 流程基类 | `backend/app/core/flows.py` | `Flows._process_task` |
| 主工作流（顺序调度） | `backend/app/core/workflow.py` | `MathModelWorkFlow.execute` |
| Agent 基类 | `backend/app/core/agents/agent.py` | `Agent`（history/轮次/记忆压缩） |
| Coordinator | `backend/app/core/agents/coordinator_agent.py` | `CoordinatorAgent.run`、`extract_questions` |
| Modeler | `backend/app/core/agents/modeler_agent.py` | `ModelerAgent.run` |
| Coder（反射循环） | `backend/app/core/agents/coder_agent.py` | `CoderAgent.run`（tool_call + reflection + MAX_CHAT_TURNS） |
| Writer | `backend/app/core/agents/writer_agent.py` | `WriterAgent.run`（search_papers + 逐节写作） |
| 工具 JSON schema | `backend/app/core/functions.py` | `execute_code_tools`、`search_papers_tools` |
| LLM 封装/重试/工具修复 | `backend/app/core/llm/llm.py` | `LLM.chat`、`_validate_and_fix_tool_calls`、`_create_provider` |
| 每 Agent 模型配置 | `backend/app/core/llm/llm_factory.py` | `LLMFactory.get_all_llms` |
| Provider 抽象 | `backend/app/core/llm/providers/{base,openai_chat,openai_responses,anthropic}.py` | `BaseProvider.call` |
| 模型选择 cookbook（V2） | `backend/app/core/prompts/modeler.py` | `MODELER_PROMPT`（决策树） |
| 题目拆分 prompt（V2） | `backend/app/core/prompts/coordinator.py` | `COORDINATOR_PROMPT`、`FORMAT_QUESTIONS_PROMPT` |
| 写作 prompt（含备选对比/图片强制） | `backend/app/core/prompts/writer.py` | `get_writer_prompt` |
| 反思 prompt | `backend/app/core/prompts/shared.py` | `get_reflection_prompt`、`get_completion_check_prompt` |
| 解释器抽象 | `backend/app/tools/base_interpreter.py` | `BaseCodeInterpreter.execute_code` |
| 本地解释器（真实执行） | `backend/app/tools/local_interpreter.py` | `LocalCodeInterpreter`（jupyter_client KernelManager） |
| 云端解释器 | `backend/app/tools/e2b_interpreter.py` | `E2BCodeInterpreter`（AsyncSandbox、字体注入、文件双向同步） |
| 解释器工厂 | `backend/app/tools/interpreter_factory.py` | `create()`（按 CODE_INTERPRETER_TYPE 选 local/e2b） |
| notebook 持久化 | `backend/app/tools/notebook_serializer.py` | `NotebookSerializer`（`segmentation_output_content`） |
| 学术检索（唯一 web research） | `backend/app/tools/openalex_scholar.py` | `OpenAlexScholar.search_papers` |
| 论文拼接 | `backend/app/models/user_output.py` | `UserOutput.write_paper` |
| 死 schema：A2A | `backend/app/schemas/A2A.py` | `CoordinatorToModeler/ModelerToCoder/CoderToWriter`（无 import） |
| 死 schema：HIL 审批 | `backend/app/schemas/response.py` | `ApprovalMessage`（6 选项，无发射方） |
| 死配置：RAG/HIL/Tavily/Fallback/Evaluator | `backend/app/config/setting.py` | `SEARCH_ENABLED/TAVILY_API_KEY`、`RAG_*`、`HIL_*`、`FALLBACK_*`、`EVALUATOR_*`（无消费者） |
| 消息推送 | `backend/app/services/redis_manager.py` + `routers/ws_router.py` | `publish_message`、`websocket_endpoint` |
| 记录（token/费用/对话） | `backend/app/utils/data_recorder.py` | `DataRecorder` |
| 测试 | `backend/app/tests/test_e2b.py`、`test_common_utils.py` | `TestE2BCodeInterpreter.test_execute_code`（API Key 门控） |
| V3 入口 skill | `skills/1start-mathmodel/SKILL.md` | AskUserQuestion + plan.md/todo.md + Agent 串联 |
| V3 建模阶段 | `skills/2analysis-modeling/SKILL.md` | ANALYSIS_MODELING_REPORT.md 结构 |
| V3 编码阶段 | `skills/3coding-visual/SKILL.md` | code/ + figures/ + RESULTS_REPORT.md |
| V3 写作阶段 | `skills/5writing/SKILL.md` | 模板族/引擎选择/章节结构 |
| V3 验收阶段 | `skills/6verity/SKILL.md` | 9 步验收 |
| **V3 唯一机械门禁** | `skills/6verity/scripts/writing_check.sh` | 占位符/泄漏/include/图片/caption FAIL；数值为 WARN 子串检查 |
| V3 知识库（决策树） | `skills/_references/math_modeling_norms.md` | 题型识别/选型速查/防错清单 |
| 环境检查 | `skills/doctor/SKILL.md` | typst/xelatex/python 依赖检测 |
| Skill 注册表 | `skills/skills.sh.json` | 6 工作流 + 2 工具 + 1 内部依赖 |
| README 声明与 roadmap 矛盾 | `README.md` | "功能特性" vs "后期计划" vs "新功能配置" |
| 仓库规则/结构说明 | `CLAUDE.md` | 后端/前端命令、目录结构、Boundaries |

---

## 11. 优势与风险（证据级）

### 11.1 最值得 LinHoMo 吸收为 execution layer / adapter 的部分

1. **Code Interpreter 抽象层（`tools/base_interpreter.py` + `interpreter_factory.py` + local/e2b 双实现）**——`IMPLEMENTED`。这是全仓库工程质量最高的模块：统一 `execute_code` 契约、local（jupyter_client）与云端（E2B）可插拔、字体注入解决中文绘图、附件上传/产物下载双向同步。**可直接作为 execution adapter 的参考实现**。
2. **notebook 全量留痕（`notebook_serializer.py`）**——每次执行追加 code cell + output，产物可再编辑、可复查，按段落留存输出供下游引用（`segmentation_output_content`）。这是"实验证据留痕"的朴素但实用的形态。
3. **Provider 抽象（`core/llm/providers/`，OpenAI Chat / OpenAI Responses / Anthropic + StandardResponse 归一化）**——比 litellm 更薄、更可控；配合 `LLM._validate_and_fix_tool_calls`（修复残缺 tool_calls）与 `_validate_config`（启动前配置校验，commit 11f3862 引入），是 LLM routing 的干净样板。
4. **反射循环模式（`coder_agent.py` + `get_reflection_prompt`）**——异常 → 反思指令 → 重试，带轮次上限（MAX_CHAT_TURNS）与 JSON 解析重试上限（MAX_JSON_RETRIES=3）。可作为 adapter 的"自愈"参考。
5. **V3 阶段边界（`2analysis→3coding→4drawio→5writing→6verity`，各阶段独立产物文件）**——`ANALYSIS_MODELING_REPORT.md`（模型设计）/`RESULTS_REPORT.md`（结果证据）/`figures/*.pdf`（图表资产）/`paper/`（论文）**文件级解耦**，这是向"模型与论文分离"迈出的正确一步（虽然模型仍是 markdown）。
6. **机械文本门禁（`6verity/scripts/writing_check.sh`）**——占位符/内部泄漏/章节编号/图片存在性/caption 检查是**可迁移的 verifier 模式**（FAIL/WARN 分级、引擎自适应 typ/latex）。
7. **17 套 Typst/LaTeX 竞赛模板 + 决策树知识库**——作为内容资产值得整体借鉴（模板转 LaTeX 的工作量大且已完成）。
8. **OpenAlex 检索封装（`openalex_scholar.py`）**——引用格式生成 + Redis 推送，可作为文献 adapter 起点。

### 11.2 不应该进入 core semantics 的部分

- **cookbook 模型选择**（prompt 决策树）：把"问题类型→关键词→模型名"写死在 prompt 里，是 model-name classification，不是 model selection；若 LinHoMo 要 structural selection，应把 taxonomy/候选/评分做成数据与算法，而不是提示词。
- **markdown 报告充当 Model**：ANALYSIS_MODELING_REPORT.md 不能作为模型语义载体——无法执行、无法校验、无法比较。
- **死配置/死 schema**：`settings.RAG_*/HIL_*/TAVILY_*/FALLBACK_*/EVALUATOR_*`、`schemas/A2A.py`、`schemas/response.py: ApprovalMessage`——设计先行但无 runtime，**勿被 README 误导为已实现能力**。
- **writing_check.sh 的"数值一致性"**：round(4) 后子串搜索是 WARN 级启发式，**不能当作数值验证**；核心语义必须用真值对账。
- **"9 步自动验收"的宣传口径**：其中多数步骤是 LLM 自查（`INSTRUCTIONAL`），机械强制的只有文本门禁 + 编译。

### 11.3 最大风险（本仓库的底层问题）

1. **把数学建模等价成 LLM workflow completion**：系统对"成功"的定义 = 四段 Agent 顺序跑完 + 论文编译通过 + 文本门禁通过。没有任何环节把"模型是否成立"作为一等公民。
2. **Model 无独立语义**：模型是流转于 Agent 之间的字符串，不是 typed object；`A2A.py` 的 typed schema 已写好却未被使用（`CONTRACT_ONLY`）。
3. **何时知道自己错了**：只有代码崩溃/编译失败时。模型选错、假设错误、约束被违反但不报错、数值系统性偏差——系统无感知。数值一致性只是"数字是否出现在论文文本里"的子串检查。
4. **不具备 epistemic state**：无置信度、无不确定性、无"未验证"状态、无证据图；DataRecorder 只记 token 费用。
5. **README 与实现的系统性落差**：RAG（ChromaDB+Rerank）、HIL（6 决策动作）、Web Search（Tavily）、四层容错（Fallback Hand Off / Evaluator Shadow Mode / Feedback Rerun）、litellm、daytona——全部在"后期计划"里，但"功能特性/新功能配置"又提前列出，且 README 引用的"升级说明"文档在 `docs/md/` 中不存在。**审计结论：以上均为 `DOC_CLAIM`**。
6. **作者免责声明**（README 原文）："AI 生成仅供参考，目前水平直接参加国赛获奖是不可能的"——与 4.4k stars 的影响力形成对照，提醒任何吸收方不要把该系统当作已验证的建模引擎，而只是"会跑的流水线"。

---

## 12. 一句话工程哲学描述

**该项目的本质是"把数学建模竞赛论文生成当作一条顺序执行的 LLM 文本接力流水线（Coordinator→Modeler→Coder→Writer→Verifier）"，第一性优化目标是"端到端跑通从赛题到可提交 PDF 的 Agent 工作流"；它用真实代码解释器作为唯一的机械反馈回路，而 Model 自始至终只是流转在 Agent 之间的文本，从未成为一个有独立语义、可验证、有认知状态的运行时对象。**
