# BZD 证据档案 — bzd-math-modeling-skills 深度技术审计

- **仓库**: `BZDmathclub/bzd-math-modeling-skills`
- **审计日期**: 2026-09-08
- **访问方式**: GitHub API（目录树）+ raw.githubusercontent.com（全量文本抓取 164/164）+ 本机执行验证
- **审计范围**: 全部 191 个 blob（文本 164 个全量下载精读；二进制资产仅核验存在性）
- **证据分级**: IMPLEMENTED（有 runtime 路径/测试证据） / CONTRACT_ONLY（有 schema/interface 无 runtime） / DOC_CLAIM（文档声称） / INSTRUCTIONAL（仅 prompt 要求，无机械执行）

---

## 1. 仓库概览

### 1.1 元数据（来源：GitHub API `repos/BZDmathclub/bzd-math-modeling-skills`）

| 字段 | 值 |
|---|---|
| 创建时间 | 2026-08-13T14:05:58Z |
| 最后推送 | 2026-09-07T07:07:14Z（审计前一天） |
| Stars / Forks / Open Issues | 221 / 9 / 1 |
| 默认分支 | `main` |
| GitHub 语言统计 | HTML（因大型 HTML 模板占主导） |
| 仓库 size | 8293 KB |
| description | "数学建模竞赛论文智能评审 Skill，支持 Codex 与 Claude Code，使用近五年国赛评阅细则…较为完备的复刻完整的评审流程" |

### 1.2 规模

- 目录树（git trees API，`truncated: false`）：**272 项 = 191 blob + 81 tree**，总字节 **15,326,404 B（≈15.3 MB）**
- 文本子集（下载到本地）：**164 个文本文件 ≈ 9.9 MB**
  - Markdown（SKILL 与 references）≈ **12,510 行**
  - Python ≈ **781 行**（5 个唯一脚本，3 个重复副本）
  - `model-dictionary.json` **8.68 MB / 5,713 条记录**（结构见 §3）
  - HTML 模板 3 个（report-template 7.5KB、AIGC 审计报告 37KB、自查指南 25.6KB）
  - CSV 3 个（school_awards 129KB、region_public、region_difficulty）
- 二进制资产（未下载仅核验存在）：XLSX 2 个（154KB + 29KB）、DOCX/PDF 若干、官方评阅细则 zip 424KB

### 1.3 目录结构（证据：tree_main.json）

```
bzd-math-modeling-skills/
├── README.md (14.6KB) / CHANGELOG.md (372B) / .gitignore
├── integrations/claude-code/bzd-review-paper/CLAUDE.md
├── skills/
│   ├── 总控类/bzd-modeling-workflow/          # SKILL.md + end-to-end-workflow.md
│   ├── 生成类/
│   │   ├── bzd-problem-translator/            # SKILL + agents/openai.yaml + 4 references
│   │   ├── bzd-modeling-ideas/                # SKILL + openai.yaml + 3 references
│   │   ├── bzd-problem-restatement/           # SKILL + openai.yaml + 2 references
│   │   └── bzd-ai-usage-disclosure/           # SKILL + openai.yaml + 4 references
│   ├── 综合评审与自我定位类/
│   │   ├── bzd-review-paper/                  # SKILL(111行) + openai.yaml + 14 references + 15 calibrations + 3 scripts + report-template.html + 3 CSV
│   │   └── bzd-cumcm-school-awards/           # SKILL + openai.yaml + query_school.py + 154KB XLSX
│   └── 论文自查类/                             # 9 个专项 checker（见 §2.7）
└── 数模资料/                                   # 模板/评阅参考/板块说明（DOCX/PDF）
```

### 1.4 Commit 活跃度（证据：commits API，前 30 条）

- 仓库年龄约 **3.5 周**（2026-08-13 建仓，2026-08-27 起密集开发，2026-09-07 最后提交）
- 提交风格为 conventional commits（`feat:` / `fix:` / `docs:` / `refactor:` / `merge:`）
- 关键提交（2026-09-07）：`feat: 新增全流程总控skill，各skill补充CUMCM题型专用参考`；2026-09-03：AIGC auditor v2.2 修复"权重二次相乘错误"并收严判分标准——说明**评分公式层存在真实迭代**
- 活跃度评级：**高**（近两周几乎每日提交，单人/双账号：BZDmathclub + BZD数模社）

---

## 2. 真实 Runtime Pipeline 重建

### 2.0 总体判定：**不存在统一 runtime**

该仓库是**纯 Skill 集合**：没有可执行入口、没有 orchestrator 代码、没有状态机、没有 schema 校验器、没有测试。所有"流程"都表达为 **SKILL.md 中的提示词指令**，由宿主（Codex / Claude Code / ChatGPT）在对话中把 SKILL.md 内容注入上下文后由 LLM 执行。**唯一的真 runtime 是 5 个 Python 脚本**（§2.8），它们承担位次计算、竞争校准、字典查询、学校查询四个边缘函数；核心的"理解/建模/评审"全部是 INSTRUCTIONAL。

消费方式（证据：README.md 安装节 + 调用示例）：
- Codex：把 Skill 文件夹复制到 `%USERPROFILE%\.codex\skills\`，用 `$bzd-problem-translator ...` 触发
- Claude Code：复制到 `.claude/skills/`；`integrations/claude-code/bzd-review-paper/CLAUDE.md` 指示先读 `@SKILL.md` 再评审
- `agents/openai.yaml`（18 个，含重复）仅提供 `interface.display_name / short_description / default_prompt`，是 **Codex/OpenAI 界面的可选展示元数据**（bzd-paper-format-checker 的 SKILL.md 明说"仅为 Codex/OpenAI 界面提供可选展示信息，其他平台可忽略"）——即 yaml 不是运行时配置，只是展示卡。

### 2.1 完整执行链（用户输入一道题 → 最终产物）

按 `skills/总控类/bzd-modeling-workflow/SKILL.md` 与 `references/end-to-end-workflow.md` 的声张流程，逐环节标注真实机制：

| # | 环节 | 负责 Skill | 机制 | 证据分级 |
|---|---|---|---|---|
| 1 | 理解题目 | bzd-problem-translator | Agent message + prompt injection；要求逐句建 ledger（B01/Q2-04 稳定 ID）、Mermaid 跨问流程图、完整性核验 | INSTRUCTIONAL（产物为 .md 文件，由 LLM 生成） |
| 2 | 拆分子问题 | translator 内部 | 句子单元切分规则（`sentence-interpretation-rules.md`） | INSTRUCTIONAL |
| 3 | 判定问题类型 | translator + modeling-ideas | A–E 题型信号表（`cumcm-abcde-translation-signals.md` / `cumcm-abcde-modeling-patterns.md`）：题号 → 题型 → 稳定主干 | INSTRUCTIONAL（启发式 letter routing，见 §4） |
| 4 | 生成候选模型 | bzd-modeling-ideas | 要求每问 ≥2 个"真正不同"候选、比较表、推荐+理由+备选 | INSTRUCTIONAL（表格由 LLM 填） |
| 5 | 选择模型 | bzd-model-dictionary | **混合**：`scripts/query_dictionary.py`（真脚本查 5713 条 JSON）+ SKILL 提示词做 11 维适配判定（`fit-assessment.md`） | 查询 IMPLEMENTED；判定 INSTRUCTIONAL |
| 6 | 构造模型 | **仓库外** | workflow 明示"pass to the user's modeling agent, Codex, Claude Code or other authorized solver"——仓库不构造模型 | N/A（显式外包） |
| 7 | 写代码/运行实验 | **仓库外** | 无任何运行代码的能力；`bzd-reference-appendix-checker` 仅在"条件具备且用户授权"时运行程序并记录命令/环境/结果 | N/A |
| 8 | 验证 | 各 checker | 全部为 prompt 级"核验"：要求引用证据、标 `无法核验`；**没有任何机械验证器** | INSTRUCTIONAL |
| 9 | 发现错误/修改 | 8 个章节 checker（abstract/restatement/analysis/assumption/symbol/solution/reference/ai-usage） | 每个 checker 是独立 SKILL.md，输出分级问题清单 | INSTRUCTIONAL |
| 10 | 最终评价 | bzd-review-paper | **混合**：rubric 构建/打分是 prompt；位次/竞争校准是确定性脚本（§2.8）；HTML 模板填充 | 打分 INSTRUCTIONAL；位次脚本 IMPLEMENTED |
| 11 | 写论文 | **不存在** | 仓库只提供写作模板（`数模资料/`），无论文生成 Skill；restatement 只写第一章 | N/A |

**箭头类型总结**：整条链的箭头 = prompt injection（SKILL.md 注入上下文）+ Agent message（宿主 LLM 自我执行）+ filesystem artifact（.md 报告产物）。**不存在** workflow state、JSON schema 校验、DAG、事件日志或任何可对账的状态。

### 2.2 总控 Skill 是"prompt 版 orchestrator"

`skills/总控类/bzd-modeling-workflow/SKILL.md`（2026-09-07 新增）要求 LLM 扮演 workflow controller：识别竞赛阶段 → 路由到对应 Skill → 维护一张**工作台账表**（Stage/Required material/Skill/Status/Output/Blocking issue/Next action）。关键自证句（第 47 行）：*"The controller does not claim that code ran or results were verified unless execution evidence exists."*——这证明控制器自身无执行证据能力，只是让 LLM 别吹牛。**证据分级：INSTRUCTIONAL。**

---

## 3. "Model" 到底是什么

### 3.1 三种并存的 Model 载体

1. **字典记录（结构化 JSON）**：`skills/论文自查类/bzd-model-dictionary/assets/model-dictionary.json`，5,713 条，每条 15 字段：`序号/模型大类/具体分组/模型名称/模型类别/适用场景/数据要求/原理讲解/模型输入/模型输出/关键假设/禁忌点/模型缺陷/检验方法/资料使用声明`。这是仓库中**唯一结构化、可查询、可复用**的 Model 表示。实测 `query_dictionary.py --model "层次分析法"` 返回 9 条匹配，字段完整。**IMPLEMENTED（数据 + 查询脚本）。**
2. **Markdown 表格（LLM 输出）**：modeling-ideas 的"可用模型及选型比较"表（模型本质/实现步骤/数据假设/优缺点/验证/接口）+ `推荐模型/选用理由/备选模型`。**INSTRUCTIONAL。**
3. **论文正文散文**：最终 Model 以文字落入论文，与结构化表示**完全解耦**——没有任何绑定/追踪机制证明论文里的模型与字典记录或思路表是同一条目。

### 3.2 Model 属性逐项核对（按审计要求 15 项）

| 属性 | 有/无 | 载体 | 证据 |
|---|---|---|---|
| assumptions | ✅ 有 | 字典`关键假设`字段；assumption-checker 逐条审 | 字典样例（IDW 条目）；`assumption-review-rules.md` |
| variables | ✅ 有 | 字典`模型输入/输出`；modeling-ideas"全文统一建模口径"表 | 字典；strategy-output-standard.md |
| parameters | ✅ 有 | 同上 | 同上 |
| constraints | 🟡 部分 | 字典`禁忌点`；modeling-ideas 要求"硬约束可验证" | 字典样例；strategy-output-standard.md §coherence |
| objective | 🟡 部分 | `原理讲解`内嵌；fit-assessment"任务对齐"维度 | fit-assessment.md |
| mechanism | ✅ 有 | 字典`原理讲解`字段 | 字典样例 |
| candidate alternatives | ✅ 有 | modeling-ideas 强制 ≥2-3 个；model-dictionary 强制推荐 2-4 替代 | modeling-ideas SKILL §4.x.3；model-dictionary SKILL 第7步 |
| selection rationale | ✅ 有 | `选用理由`/`fit-assessment` 四档判定 | 两份 SKILL |
| uncertainty | 🟡 部分 | fit-assessment metric routing 提到不确定性；字典仅个别条目 | fit-assessment.md |
| sensitivity | ✅ 有 | 字典`检验方法`；model-solution-checker 灵敏度专项 | 字典样例（IDW: 对幂指数 p 敏感性分析） |
| validation | ✅ 有 | 字典`检验方法`字段；fit-assessment 验证维度 | 字典样例 |
| failure conditions | ✅ 有 | 字典`禁忌点/模型缺陷`；modeling-ideas 表格"失败风险"列 | 字典样例；modeling-ideas SKILL |
| downstream dependencies | ✅ 有 | `cross_question_interface` 标签；modeling-ideas 接口表 | cumcm-abcde-modeling-patterns.md §结构化标签 |

### 3.3 Model 是否为 typed object？

**否。** Model 在系统中分别是：JSON dict（字典）、markdown 表行（思路输出）、prose（论文）。**没有 Model class、没有 schema 校验器、没有 DAG 节点类型。** `query_dictionary.py` 只做了字段白名单抽取（`fields = [...]`），不构成类型系统。

### 3.4 Model 可执行操作

| 操作 | 有/无 | 证据 |
|---|---|---|
| 修改 | 🟡 仅文本层面 | checker 建议修改（INSTRUCTIONAL） |
| 比较 | ✅ | modeling-ideas 同任务对比表（INSTRUCTIONAL）；字典检索可并列多条 |
| 追踪 | ❌ 无 | 无 artifact registry / 无 ID 链 |
| 验证 | 🟡 仅 prompt 级 | checkers 要求证据，无机械执行 |
| 重放 | ❌ 无 | 无运行记录 |
| 复用 | ✅ | 字典可重复查询（IMPLEMENTED） |
| 组合 | 🟡 文本建议 | modeling-ideas"推荐全文组合" |
| 回滚 | ❌ 无 | 无版本化 |
| failure attribution | ❌ 无 | 无错误追踪 |

### 3.5 Model 与论文文字解耦

**部分解耦。** 字典是结构化独立资产（✅），但思路表→论文章节之间无任何绑定；`总控类` 台账要求"artifact 改变时标记下游过期"仅是提示词约定。**结论：CONTRACT_ONLY / INSTRUCTIONAL。**

---

## 4. Model Selection 机制

- **Model family taxonomy**：✅ 有。字典五类：预测分类(2250)/评价(1183)/优化模型(1087)/数据预处理(674)/其他(519)，细分为 20+ 具体分组（时间序列扩展 588、元启发式 585、多准则决策 421、综合评价 410…）。**IMPLEMENTED（数据在 JSON 中）。**
- **Candidate generation**：✅ 有（modeling-ideas 强制多候选），INSTRUCTIONAL。
- **Suitability analysis**：✅ 有（fit-assessment 11 维度 + 四档判定规则），判定本身 INSTRUCTIONAL。
- **Decision rules**：✅ 有形式化规则文本（`合适/有条件合适/不合适/证据不足，待人工复核` + "单一致命不匹配即否决"），INSTRUCTIONAL。
- **Model comparison**：✅ 有（同任务同指标对比表），INSTRUCTIONAL。
- **Cookbook routing**：🟡 **部分存在但被明确反制**。`cumcm-abcde-modeling-patterns.md` 提供 A–E 题型→"推荐整体主线/基线优先/必要升级/核心验证"映射（如 A→工程对象→状态方程→数值仿真→参数优化→工程验算），`cumcm-abcde-translation-signals.md` 提供题号→信号表。**这是 letter-based heuristic routing**；但同一文件第 4 节"反机械套题"五条铁律明确禁止"题号决定模型、复制历史模型"。翻译 SKILL 也说"历史规律不指定模型"。所以路由是"**字母键触发启发式检查清单**"，不是模型名映射。
- **结论**：属于 **heuristic routing / model-name classification 之上的"专家规则提示"**，不是 structural model selection——没有基于题目结构的计算式选择、没有基准比较、没有选择的可计算证据。模型选择的可信度完全押在 LLM 对 fit-assessment 维度的主观判断上。

---

## 5. Model Construction 机制

- **模型如何产生**：全部由 LLM 依据 prompt 直接输出文本（modeling-ideas 表格）。**没有**结构化构造步骤（无符号生成、无方程模板、无求解器绑定、无形式化目标/约束生成）。
- **Assumption validation**：仅在事后由 `bzd-model-assumption-checker` 做审查（INSTRUCTIONAL），构造时无检查。
- **Constraint checking**：仅 checker prompt 要求"硬约束可验证"（INSTRUCTIONAL）。
- **结论**：构造 = **LLM 自由生成 + 事后 prompt 审查**。仓库明确不构造可执行模型（§2.1 第 6 行）。

---

## 6. Knowledge 的地位

### 6.1 知识存放位置（全部五类）

| 位置 | 内容 | 量级 | 消费方式 |
|---|---|---|---|
| SKILL.md（12 个唯一） | 过程性指令 | ~1,700 行 | 宿主注入上下文（INSTRUCTIONAL） |
| references/*.md | 题型模式/评阅规则/评分锚点 | ~40 个文件 | SKILL 指示"完整阅读后再执行"（INSTRUCTIONAL） |
| model-dictionary.json | 模型知识（假设/禁忌/缺陷/检验） | 5,713 条 | `query_dictionary.py` 机械检索（IMPLEMENTED） |
| calibrations/*.md | 15 道题评阅细则的规范化和权重重构 | 15 个文件 | SKILL 指示"最接近时使用"（INSTRUCTIONAL） |
| data/*.csv + XLSX | 学校/赛区/教师获奖数据 | 1127 校 + 31 赛区 | `competition_context.py` / `query_school.py` 机械读取（IMPLEMENTED） |

### 6.2 Knowledge → Agent → Model 因果链

- 实现方式：**prompt 指令要求**（"Read completely before generating the report"）+ 一个检索脚本。无 RAG、无向量库、无重排、无检索增强的自动注入。
- **无任何实验/benchmark/ablation/evaluation 证明"更多知识→更高建模质量"**。搜索全仓库：无 tests、无 benchmark、无评估脚本。`learning-protocol.md` 第 6 节自证：*"Never describe the Skill as 'trained' statistically unless an actual evaluated dataset and learning method exist; call this structured rule induction and calibration."* —— **DOC_CLAIM（蒸馏主张），无因果证据。**
- 唯一可量化的"知识→输出"链路是字典/CSV → 脚本 → JSON 输出（IMPLEMENTED），但那是检索/查表，不是建模质量提升。

---

## 7. Verification / Evidence / Reproducibility

- **验证器**：无代码验证器。`gate`/`validate` 类工具不存在（对比：MathModel harness 有 57 项校验）。所有"验证"是 prompt 级要求（checkers 输出分级问题、要求页码证据、无法核验时标 `无法核验` 而非判错）。**INSTRUCTIONAL。**
- **证据生命周期**：无 artifact registry、无 evidence graph、无状态。calibrations 是静态 markdown；`calibration-record-template.md` 定义了记录格式（CONTRACT_ONLY），`learning-protocol.md` 描述了归纳协议（INSTRUCTIONAL），但**没有代码消费这些记录**。
- **可复现性**：
  - 确定性层（IMPLEMENTED，已实测）：`award_position.py`（固定锚点线性插值）、`competition_context.py`（固定 CSV + clamp 公式）、`score_percentile.py`（midrank）、`query_dictionary.py`、`query_school.py` —— 同输入必同输出。
  - 非确定性层：LLM 打分/判题/rubric 生成，**无种子控制、无多轮一致性检查**。
- **随机种子**：仓库自身不使用种子；仅 `model-solution-checker` 要求论文作者披露随机种子（作为审查对象）。
- **测试覆盖**：**零测试**。目录树检索 `test/spec/pytest` 无任何命中；无 CI 配置；无 requirements/pyproject（唯一外部依赖 `openpyxl` 仅 query_school.py 使用）。
- **脚本实测记录**（本审计执行）：
  - `award_position.py --score 68.5 --contest-type cumcm` → percentile 92.8、省一区间（✅）
  - `competition_context.py --score 68.5 --region 江苏 --school 苏州大学 --advisor 张三 --division 本科组` → 命中苏州大学真实记录（五年国奖 10、高频教师严继高、赛区难度 64.41→国奖 delta −7.2）（✅）
  - `score_percentile.py --score 68.5 --distribution <81 点 CSV>` → midrank 72.84（✅）
  - `query_dictionary.py --model "层次分析法"` → 9 匹配，含 AHP/ANP 完整字段（✅）
  - `query_school.py --school 苏州大学 --region 江苏` → 2021-2025 年度/汇总/2026 预测/高频教师（✅，需 openpyxl）

---

## 8. Software Architecture

- **无框架**。架构 = 目录约定：`<skill>/SKILL.md + agents/openai.yaml + references/ + scripts/ + assets/`。
- **依赖关系**：SKILL.md 用相对路径引用 references（`[references/xxx.md](references/xxx.md)`）；跨 Skill 调用靠 `$bzd-xxx` 命名约定（总控 SKILL 以名称引用兄弟 Skill）——**无 import 解析、无符号链接、无构建工具**。
- **扩展性**：新增能力 = 新建目录 + 写 prompt。低耦合，但无质量门。
- **重复与维护风险**（blob-hash 实测）：**49 个文件是完全重复副本（49 组两两同 hash），唯一 blob 仅 142 个**——
  - `bzd-review-paper` 整包在 `综合评审与自我定位类/` 与 `论文自查类/` 各一份（42 文件同 hash，含 3 个 .py 与 15 个 calibrations）
  - `bzd-ai-usage-disclosure`（6 文件）、`bzd-problem-restatement`（4 文件）各两份
  - `bzd-reference-appendix-checker` 在自身目录下嵌套一份完整副本（5 文件）
  - 即 191 blob 中 49 个是冗余；修改需多副本同步，CHANGELOG 中"保留原 BZD-review-paper 兼容目录"解释了成因（迁移遗留）。
- **版本管理**：无 schema 版本、无 artifact 版本；CHANGELOG 仅 1 条 v1.0.0 记录。

---

## 9. 工程哲学分类

**判定：A（Knowledge Engineering: Expert→Skill→Agent）为主，边缘附着一层 C 式确定性脚本；不属 B（无 coordinator agent 之外的 agent 编排），不属 C（无 state/artifact/evidence runtime）。**

判断依据：
1. 核心资产是**专家评审经验蒸馏成的提示词知识**（16 道题评阅细则 → references/calibrations），Agent 是宿主 LLM，不是仓库组件——完全符合 A 的 Expert→Skill→Agent 单向链。
2. 唯一的"系统"行为是 5 个确定性脚本对**位次/竞争校准/字典/学校查询**四个边缘函数做算术——这是 C 式可复现性的局部实现，但无 artifact registry、无验证门禁、无重放。
3. 没有任何 B 类证据：不存在多 Agent 协作的运行时，总控 Skill 只是让一个 LLM 自我路由。

---

## 10. 关键文件路径索引

所有路径相对于 `https://github.com/BZDmathclub/bzd-math-modeling-skills/tree/main/`，raw 前缀 `https://raw.githubusercontent.com/BZDmathclub/bzd-math-modeling-skills/main/`。

| 判断 | 路径 | 分级 |
|---|---|---|
| 入口/定位/安装 | `README.md` | — |
| 版本记录 | `CHANGELOG.md` | — |
| 总控（prompt orchestrator） | `skills/总控类/bzd-modeling-workflow/SKILL.md` | INSTRUCTIONAL |
| 端到端流程路由表 | `skills/总控类/bzd-modeling-workflow/references/end-to-end-workflow.md` | INSTRUCTIONAL |
| 题意翻译 | `skills/生成类/bzd-problem-translator/SKILL.md` + `references/{sentence-interpretation-rules,historical-review-signals,cumcm-abcde-translation-signals,md-output-standard}.md` | INSTRUCTIONAL |
| 建模思路/选型 | `skills/生成类/bzd-modeling-ideas/SKILL.md` + `references/{integrated-modeling-patterns,cumcm-abcde-modeling-patterns,strategy-output-standard}.md` | INSTRUCTIONAL |
| 模型字典（结构化 Model 知识） | `skills/论文自查类/bzd-model-dictionary/assets/model-dictionary.json`（5713 条） | IMPLEMENTED |
| 字典查询脚本 | `skills/论文自查类/bzd-model-dictionary/scripts/query_dictionary.py` | IMPLEMENTED |
| 适配判定规范 | `skills/论文自查类/bzd-model-dictionary/references/fit-assessment.md` | INSTRUCTIONAL |
| 评审主 SKILL（rubric/打分/位次） | `skills/综合评审与自我定位类/bzd-review-paper/SKILL.md` | 打分 INSTRUCTIONAL / 脚本 IMPLEMENTED |
| 原子扣分公式 | `references/atomic-deduction-scoring.md`（`problem_earned=max(0, 0.90×w−Σdeductions)`） | INSTRUCTIONAL（公式文本，由 LLM 执行） |
| rubric 构建/质量门 | `references/rubric-construction.md` | INSTRUCTIONAL |
| 通用评分锚点 | `references/rubric.md` | INSTRUCTIONAL |
| 位次估算脚本（锚点插值） | `scripts/award_position.py` | IMPLEMENTED |
| 经验分布百分位脚本 | `scripts/score_percentile.py` | IMPLEMENTED |
| 竞争校准脚本（赛区/学校/教师） | `scripts/competition_context.py` + `references/data/*.csv` + `references/competition-context-adjustment.md` | 脚本 IMPLEMENTED / 数值 DOC_CLAIM |
| 低分保底机制 | `references/low-score-safeguard.md` | INSTRUCTIONAL |
| 评阅学习协议 | `references/learning-protocol.md` | INSTRUCTIONAL |
| 15 道题校准记录（示例） | `references/calibrations/cumcm-2025-a-smoke-screen.md` 等 15 个 | CONTRACT_ONLY（记录格式已建，无代码消费） |
| HTML 报告模板 | `assets/report-template.html` | IMPLEMENTED（模板存在，填充由 LLM） |
| AIGC 痕迹审计（两层 9 维） | `skills/论文自查类/bzd-paper-aigc-auditor/SKILL.md` + `references/{audit-framework,layer1-enhanced-detection,nature-detector-integration,patterns-zh,models-zh}.md` + `templates/*.html` | INSTRUCTIONAL |
| 格式审计（15 分制原子清单） | `skills/论文自查类/bzd-paper-format-checker/SKILL.md` + `references/{format-review-rules,paper-section-self-check-table}.md` + `assets/*.xlsx` | INSTRUCTIONAL |
| 章节自查（8 个 checker） | `skills/论文自查类/{bzd-abstract-checker,bzd-model-assumption-checker,bzd-model-solution-checker,bzd-problem-analysis-checker,bzd-problem-restatement,bzd-symbol-notation-checker,bzd-reference-appendix-checker,bzd-ai-usage-disclosure}/SKILL.md` | INSTRUCTIONAL |
| 学校奖项查询 | `skills/综合评审与自我定位类/bzd-cumcm-school-awards/scripts/query_school.py` + `assets/高教社杯国赛学校综合统计与2026预测.xlsx` | IMPLEMENTED |
| Agent 展示配置（非 runtime） | 各 `agents/openai.yaml`（18 个） | CONTRACT_ONLY |
| Claude Code 集成 | `integrations/claude-code/bzd-review-paper/CLAUDE.md` | INSTRUCTIONAL |
| 写作模板/备赛资料 | `数模资料/`（模板、板块说明 PDF/DOCX、官方评阅细则 zip） | 资产存在 |

---

## 11. 优势与风险（证据级）

### 11.1 最值得吸收的东西

1. **评审打分的规则化形式主义**（`atomic-deduction-scoring.md` + `rubric-construction.md`）：90% 评委封顶、原子检查点 1/2/3 分扣减、扣分无上限、`problem_earned` 公式保底为零、格式质量系数 `(format+10)/20` 的确定性映射、低分自底向上复评（35 分帽）——**把"评委主观分"拆成了可审计、可复算的算术**。这是三仓库对比中最强的 reviewer policy 细节。
2. **确定性位次/校准脚本**（award_position / competition_context / score_percentile）：锚点插值与 clamp 公式与文档完全一致，已实测可执行；竞争校准把"学校/赛区/教师"与"论文质量分"严格分离（不回写质量分）——**评审公平性边界的设计值得抄**。
3. **模型字典的字段设计**（5713 条 × 假设/禁忌点/缺陷/检验方法/资料声明）：假设-失败条件-验证三元结构是"模型知识卡"的成熟 schema，且用只读脚本查询 + 版权保护指令（禁止输出全文）。
4. **评阅校准语料方法**（`learning-protocol.md` + `calibration-record-template.md`）："权重溯源/条件化规则/跨案例≥2 才提升"的归纳纪律，以及"禁止宣称 statistically trained"的诚实条款。
5. **反机械套题护栏**：modeling-ideas/translator 多处明文禁止"题号决定模型""复制历史数值"——对 cookbook 退化的主动防御。

### 11.2 最大风险

1. **知识→能力无因果证据**：全仓零测试、零 benchmark、零 ablation。"基于 16 道题蒸馏"是 DOC_CLAIM；`learning-protocol.md` 自己承认未统计训练。无法证明 Skill > 更多 context。
2. **核心能力全部依赖 LLM 自律**：rubric 生成、逐条扣分、模型适配判定、章节诊断——均为 INSTRUCTIONAL，无机械强制执行；同一论文两次评审结果一致性无任何保障（无种子、无校验器）。
3. **校准数值来源不透明**：`6.81%`（未上榜学校国奖概率）、`30%–50%`（强校预估）、2025 锚点表、赛区难度分、`is_modeling_strong_school` 标记——这些**硬编码在脚本/CSV 里、看起来确定，但都是 owner 经验值**；脚本的"确定性"会放大而非验证这些先验。`competition_context.py` 中 `national_probability_ceiling = 0.0681`、`advisor_multiplier 1.2/0.8` 均为无出处常数。**DOC_CLAIM 被包装成 IMPLEMENTED 的输出**——这是审计上最需警惕的模式。
4. **知识表示仍靠 Agent 自行解释**：references 是自然语言，模型选择/打分是把自然语言规则喂给 LLM 再信任其执行；没有形式化约束（如权重和=100 只在 prompt 里要求，无代码断言）。
5. **工程卫生**：49 个重复文件、无测试、无 CI、无依赖清单、`openai.yaml` 无 schema 校验——长期维护风险高。

---

## 12. 一句话工程哲学描述

**BZD 的本质是"评委经验提示词工程"：把 16 道国赛题的评阅细则蒸馏成高度规则化的评审 prompt + 边缘确定性脚本，第一性优化目标是让没有评审经验的参赛者获得"可复算、可审计、可定位"的论文质量与位次估计——但其核心打分与建模能力仍完全押注于 LLM 对提示词的自律执行，而非任何机械验证。**

---

*附录：审计方法说明。目录树来自 `git/trees/main?recursive=1`（truncated:false，272 项）；164 个文本文件经 raw.githubusercontent.com 全量下载并精读；5 个 Python 脚本在本机实际运行验证（Python 3.12，openpyxl 3.1.5）；重复文件经 blob sha 聚类确认；commit 与 repo 元数据来自 GitHub REST API（2026-09-08 抓取）。二进制资产（PDF/DOCX/XLSX/ZIP）未下载，仅通过目录树核验存在与大小。*
