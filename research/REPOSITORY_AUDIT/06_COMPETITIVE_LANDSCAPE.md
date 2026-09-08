# 06 — Competitive Landscape：数学建模 Agent / Harness / Benchmark 竞争性架构研究

> **审计角色**：Competitive Landscape & External Source Provenance 研究员
> **审计日期**：2026-09-08
> **研究范围**：公开可检索的数学建模 Agent、Skill、Harness、Benchmark、算法库及科学工作流 Agent
> **方法论**：general_search 多轮中英文检索 → web.fetch 深度阅读 → 结构化交叉比对 → marketing claim 标记

---

## 1. 竞争性项目研究

以下选取 **10 个**真正有内容、可检索到架构细节的公开项目，按与数学建模竞赛的相关度排序。所有 Star 数与更新时间为检索时（2026-09-08）可获得的公开信息；无法确认的标记为 `N/A`。

### 1.1 MathModelAgent

| 字段 | 内容 |
|---|---|
| **项目名称** | MathModelAgent |
| **URL** | https://github.com/jihe520/MathModelAgent |
| **项目类型** | Agent（多智能体自动化系统） |
| **Star 数** | N/A（个人项目，检索时未显示明确 star 计数） |
| **最后更新** | 2025-02（掘金技术博客发布时间） |
| **架构概述** | 三智能体协作框架：建模手（问题拆解+模型选择）、代码手（编程+自动纠错）、论文手（LaTeX 格式编排+格式自检）。支持本地代码解释器与 E2B 云端双模式。不同 Agent 可配置不同 LLM（GPT-4 / Claude / 本地模型）。输出 LaTeX 格式论文，集成可视化图表与文献引用。 |

**关键宣称**："将原本需要3天的建模过程压缩至1小时""直接输出符合学术规范的完整论文"。
**验证状态**：**marketing claim** — 无公开 benchmark 结果、无获奖论文实证、无可复现的端到端评测数据。三 Agent 分工为常见模式，无证据表明其建模质量优于单 Agent + 强 prompt。

---

### 1.2 Math Modeling Skill（XiaoMaColtAI）

| 字段 | 内容 |
|---|---|
| **项目名称** | Math Modeling Skill |
| **URL** | https://github.com/XiaoMaColtAI/math-modeling-skill |
| **项目类型** | Skill（Agent 技能包，兼容 Claude Code / OpenClaw 等 Skills 平台） |
| **Star 数** | N/A |
| **最后更新** | 2026-03（掘金发布时间） |
| **架构概述** | 三阶段工作流（建模分析→代码实现→论文撰写），三角色模式（建模手/编程手/论文手）。内置 7 大类 60+ 算法资源库（优化15/预测11/评价11/图论6/统计9/综合6/机器学习3）。集成 4 个子 Skill：pdf 处理、xlsx 处理（强制 Excel 公式而非硬编码）、docx 生成、paper_search（OpenAlex API）。包含优秀论文库（CUMCM 国赛 + 2017 MCM/ICM O 奖）和论文模板。内置"去 AI 味写作指南"。 |

**关键宣称**："支持数学建模竞赛全流程自动化""帮助选手高效完成从问题分析到论文产出"。
**验证状态**：**partial / marketing claim** — 算法资源库和子 Skill 有实际代码结构，但"全流程自动化"无端到端评测。60+ 算法为文档级说明，非可执行求解器集成。优秀论文库为参考资料，非 gold standard。

---

### 1.3 Datawhale intro-mathmodel

| 字段 | 内容 |
|---|---|
| **项目名称** | intro-mathmodel（数学建模导论） |
| **URL** | https://github.com/datawhalechina/intro-mathmodel |
| **项目类型** | Established Resource（开源教程/教学材料） |
| **Star 数** | N/A（Datawhale 系列项目通常 1k+） |
| **最后更新** | 持续维护（2025 仍在用于组队学习） |
| **架构概述** | 基于《数学建模导论——基于Python语言》整理的开源教程，覆盖常用数学模型（线性/非线性规划、微分方程、预测、评价、聚类等）的 Python 实现。配套在线学习网站。非 Agent 系统，是知识资源库。 |

**定位**：Level 3 已建立建模资源。可作为 knowledge base / method card 的素材来源，但本身不提供自动化能力。

---

### 1.4 ASI-Bench

| 字段 | 内容 |
|---|---|
| **项目名称** | ASI-Bench: At the Dawn of Artificial Superintelligence |
| **URL** | https://github.com/apexin-ai/ASI-Bench |
| **项目类型** | Benchmark（自主科研能力基准） |
| **Star 数** | N/A（2026-08 新发布） |
| **最后更新** | 2026-08（arXiv:2608.17271） |
| **架构概述** | 清华/哈佛等机构联合提出。覆盖 11 大学科的 60 项项目级科研任务。每项任务是完整微型科研项目：问题理解→方法选择→代码实现→实验运行→错误排查→结果迭代。任务来源于 1300+ 学术文献。评估 Agent 端到端科研能力，而非知识问答。 |

**与本仓库关系**：最接近"数学建模全流程自动化"的通用 benchmark 范式。其项目级任务设计（多环节、需代码实跑、需结果迭代）可直接借鉴为 MMBench 的任务结构参考。但其学科覆盖广而非数学建模专项，评估维度不同。

---

### 1.5 IDA-Bench

| 字段 | 内容 |
|---|---|
| **项目名称** | IDA-Bench（Iterative Data Analysis Benchmark） |
| **URL** | https://github.com/lhydave/IDA-Bench |
| **项目类型** | Benchmark（迭代式数据分析基准） |
| **Star 数** | N/A |
| **最后更新** | 2025-06（arXiv:2505.18223） |
| **架构概述** | 北大/伯克利联合提出。模拟真实世界中"边想边改"的分析场景：多轮、不断演进的指令。测试 Agent 在动态需求下的任务成功率。最强 Agent 成功率仅 40%。核心洞察：静态单轮 benchmark 高估了 Agent 的实际分析能力。 |

**与本仓库关系**：其"迭代式需求变更"范式验证了本仓库 V3 DAG + reconcile + 门禁的设计合理性——真实建模过程不是线性流水线，而是需要状态对账和回退修正。

---

### 1.6 AgentSociety（清华 FIB Lab）

| 字段 | 内容 |
|---|---|
| **项目名称** | AgentSociety |
| **URL** | https://github.com/tsinghua-fib-lab/agentsociety |
| **项目类型** | Multi-Agent Framework + Benchmark |
| **Star 数** | N/A |
| **最后更新** | 2025-07（Urban Cup 2025 智能体挑战赛使用） |
| **架构概述** | 清华 FIB 实验室开源的多智能体社会模拟框架。包含 agentsociety-benchmark 子包。从传统 ABM（Agent-Based Modeling）向 LLM 驱动的自主认知智能体演进。支持大规模异质 Agent 个体交互、自下而上涌现宏观现象。 |

**与本仓库关系**：其 benchmark 子包设计可参考，但核心方向是社会模拟而非数学建模竞赛。多 Agent 交互模式可作为"多模型辩论/模型选择"的参考架构。

---

### 1.7 OmniaBench

| 字段 | 内容 |
|---|---|
| **项目名称** | OmniaBench |
| **URL** | https://github.com/scuuy/OmniaBench |
| **项目类型** | Benchmark（通用 Agent 能力基准） |
| **Star 数** | N/A |
| **最后更新** | 2026-07（arXiv:2607.14989） |
| **架构概述** | 通用 Agent 基准测试，代码/数据集/评估工具全开源（Apache 2.0）。HuggingFace 数据集开放。覆盖多维度 Agent 能力评估。 |

**与本仓库关系**：通用基准，非数学建模专项。可作为"Agent 基础能力"的外部参照，但不覆盖建模深度。

---

### 1.8 SPSSPRO

| 字段 | 内容 |
|---|---|
| **项目名称** | SPSSPRO |
| **URL** | https://www.spsspro.com（CUMCM 官方赞助单位） |
| **项目类型** | Commercial Platform（在线数据分析/数学建模平台） |
| **Star 数** | N/A（商业产品，非开源） |
| **最后更新** | 持续运营（2026 年 CUMCM 赞助商） |
| **架构概述** | 在线数据分析平台，提供拖拽式统计分析、机器学习、可视化。CUMCM 官方赞助单位之一。面向非编程背景用户，降低建模工具门槛。非 Agent 系统，是工具平台。 |

**与本仓库关系**：代表"工具民主化"路线——降低使用门槛但不提升建模深度。其算法菜单化模式与本仓库"方法卡 + 自动匹配"有表面相似，但本仓库强调可追溯的建模决策而非黑箱工具调用。

---

### 1.9 MATH / MATH500 / GSM8K 系列基准

| 字段 | 内容 |
|---|---|
| **项目名称** | MATH Dataset / MATH500 / GSM8K |
| **URL** | https://github.com/hendrycks/math（MATH）；MATH500 为 MATH 子集 |
| **项目类型** | Benchmark（数学推理基准） |
| **Star 数** | MATH: 1.5k+（估算） |
| **最后更新** | MATH (2021)；MATH500 (2023)；持续被引用 |
| **架构概述** | MATH：7500 道竞赛级数学题，分 7 大领域（代数/数论/组合/概率/几何/中级代数/初等代数），5 级难度。MATH500：500 道代表性子集，用于快速评测。GSM8K：8500 道小学数学应用题。这些是 LLM 数学推理能力的事实标准基准。 |

**关键局限**：这些基准测试的是**纯数学解题**（有标准答案、单步/多步推理），而非**数学建模**（开放问题、需假设、需数据、需论文、无唯一标准答案）。2025 USAMO 测试显示所有大模型得分 <5%，证明即使在纯数学领域 LLM 仍远未成熟。

**与本仓库关系**：可作为"基础数学推理能力"的下游评估维度，但完全不能替代建模专项 benchmark。本仓库的 MMBench 必须覆盖建模全流程（题面理解→假设→建模→实跑→验证→论文），这是 MATH 系列不涉及的。

---

### 1.10 MathDebugger（北京大学 DCAI）

| 字段 | 内容 |
|---|---|
| **项目名称** | MathDebugger |
| **URL** | EMNLP 2026 论文（检索时未找到独立 GitHub 仓库） |
| **项目类型** | Benchmark（数学合成数据质检基准） |
| **Star 数** | N/A |
| **最后更新** | 2026-09（EMNLP 2026 接收） |
| **架构概述** | 北大 DCAI 团队提出。4000 道题目 + 2000 条带标注答案 + 7 类细粒度错误类型。评测 14 个主流 LLM 和 3 个 Process Reward Model。核心问题：合成数学数据中存在大量隐性错误，需要专门的质检机制。 |

**与本仓库关系**：其"细粒度错误类型分类"方法可借鉴为本仓库 validator 的错误分类体系。其核心发现——合成数据不可信——直接支持本仓库"所有数值必须可追溯到已验证 Result Artifact"的铁律。

---

## 2. 结构比较矩阵

以下对 10 个项目在 13 个维度上进行结构化比较。符号说明：✅ 有明确实现/证据；◐ 部分实现或仅宣称；❌ 无此能力；N/A 不适用。

| 维度 | MathModelAgent | Math Modeling Skill | Datawhale intro | ASI-Bench | IDA-Bench | AgentSociety | OmniaBench | SPSSPRO | MATH/MATH500 | MathDebugger |
|---|---|---|---|---|---|---|---|---|---|---|
| **Architecture** | 多Agent(3) Pipeline | Skill+3角色 Pipeline | 教程(无Agent) | 项目级任务 Benchmark | 迭代式 Benchmark | 多Agent 社会模拟 | 通用Agent Benchmark | 工具平台 | 数据集 Benchmark | 数据集 Benchmark |
| **Problem ingestion** | ◐ 文本输入 | ✅ PDF+xlsx子Skill | N/A | ✅ 文献级任务 | ✅ 多轮指令 | ◐ 场景配置 | ◐ 通用输入 | ✅ 数据上传 | ❌ 纯题目文本 | ❌ 题目文本 |
| **Skill system** | ❌ 无 | ✅ 标准化Skill+4子Skill | N/A | ❌ 无 | ❌ 无 | ◐ 框架级 | ❌ 无 | ❌ 无 | N/A | N/A |
| **Model construction** | ◐ 建模手选择 | ◐ 60+算法文档(非执行) | ✅ 方法讲解 | ✅ 要求方法选择 | ✅ 分析过程 | ◐ 个体行为规则 | ◐ 通用 | ✅ 菜单化算法 | ❌ 不涉及 | ❌ 不涉及 |
| **Data analysis (EDA)** | ◐ 代码手处理 | ✅ xlsx子Skill | ✅ Python示例 | ✅ 实验运行 | ✅ 数据分析 | ◐ 模拟数据 | ◐ 通用 | ✅ 拖拽式分析 | ❌ 不涉及 | ❌ 不涉及 |
| **Solver integration** | ◐ 本地/E2B执行 | ◐ 代码生成非集成求解器 | ✅ Python库调用 | ✅ 代码实现+运行 | ✅ 代码执行 | ❌ 无求解器 | ◐ 工具调用 | ✅ 内置求解器 | N/A | N/A |
| **Validation** | ◐ 论文手格式自检 | ◐ 去AI味自查清单 | ❌ 无 | ✅ 结果评估 | ✅ 成功率评估 | ◐ 涌现度量 | ✅ 多维度评估 | ❌ 无自动化验证 | ✅ 标准答案 | ✅ 7类错误标注 |
| **Evidence chain** | ❌ 无 | ❌ 无 | N/A | ◐ 文献溯源 | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 | N/A | N/A |
| **Paper generation** | ✅ LaTeX输出 | ✅ docx生成 | ❌ 无 | ❌ 无(科研报告非论文) | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 | N/A | N/A |
| **Benchmark** | ❌ 无 | ❌ 无 | ❌ 无 | ✅ 60任务11学科 | ✅ 迭代分析任务 | ✅ benchmark子包 | ✅ 通用Agent | ❌ 无 | ✅ 7500/500题 | ✅ 4000题 |
| **Evaluation** | ❌ 自宣称 | ❌ 自宣称 | N/A | ✅ 端到端科研能力 | ✅ 多轮成功率 | ◐ 社会模拟指标 | ✅ 多维度 | ❌ 用户自评 | ✅ 准确率 | ✅ 错误检测率 |
| **Reproducibility** | ◐ 需API密钥 | ✅ 开源可安装 | ✅ 完全开源 | ✅ 开源 | ✅ 开源 | ✅ 开源 | ✅ 开源(Apache2) | ❌ 商业闭源 | ✅ 公开数据集 | ◐ 论文级 |
| **Failure handling** | ◐ 代码手纠错 | ◐ 自查清单 | N/A | ✅ 错误排查环节 | ✅ 迭代修正 | ❌ 无 | ◐ 通用 | ❌ 无 | N/A | ✅ 错误诊断 |

---

## 3. 常见问题分析

### 3.1 Multi-agent ≠ better modeling

**观察**：MathModelAgent（3 Agent）、Math Modeling Skill（3 角色）、AgentSociety（大规模多 Agent）均采用多 Agent 架构。但多 Agent 仅意味着**任务分工**，不意味着**建模质量提升**。

**证据**：
- IDA-Bench 显示最强 Agent 在迭代式数据分析中成功率仅 40%——多 Agent 并未解决核心分析能力不足的问题。
- ASI-Bench 的 60 项科研任务中，现有 Agent 系统表现普遍不佳，多 Agent 编排的 overhead 可能反而引入协调错误。
- 数学建模的核心瓶颈是**模型选择合理性**和**结果可验证性**，而非"有多少个 Agent 在干活"。

**结论**：Agent 数量不是架构质量指标。本仓库 V3 已重组为 5 Role 驱动的 DAG 节点，Agent 数量不再作为架构质量指标——这一决策与外部证据一致。

### 3.2 More prompts ≠ better reasoning

**观察**：多个项目通过精心设计的 prompt 模板（建模手说明、编程手说明、论文手说明）来引导 Agent 行为。Math Modeling Skill 甚至包含"去 AI 味写作指南"和七大类 AI 痕迹识别。

**证据**：
- USAMO 2025 测试：所有大模型得分 <5%，即使有复杂推理 prompt。
- MATH-P-Hard 数据集：所有模型准确率普遍降低 10%-25%，prompt 工程无法弥补深层推理能力缺陷。
- Prompt 的边际收益递减：当问题需要真正的数学洞察（而非模式匹配）时，prompt 长度与质量无正相关。

**结论**：Prompt 是必要的脚手架，但不是推理能力的来源。本仓库将 prompt 固化为 role yaml + skill 指令，同时通过 validator 门禁确保输出质量不依赖 prompt 的"精妙"。

### 3.3 More algorithms ≠ better model selection

**观察**：Math Modeling Skill 宣称 60+ 算法资源库，SPSSPRO 提供菜单化算法选择，Datawhale 教程覆盖常用模型。但"算法库大"不等于"模型选择对"。

**证据**：
- 数学建模的核心挑战是**在特定问题约束下选择合理模型并论证其适用性**，而非"知道最多算法"。
- CUMCM 评阅标准明确为"假设的合理性、建模的创造性、结果的正确性"——评的是**选择和论证**，不是算法数量。
- 60+ 算法文档为静态说明，不包含"什么问题该用什么算法、为什么"的决策逻辑。

**结论**：算法库是资源，不是决策系统。本仓库的 method-matcher + assumption-validator + spec-auditor 链路正是为了解决"选择合理性"问题，而非堆砌算法。

### 3.4 Longer paper ≠ better solution

**观察**：Math Modeling Skill 宣称输出"≥15000 字"论文，MathModelAgent 宣称"完整论文"。社区经验（赛氪 2016）甚至建议"不到10页也要凑到20页"。

**证据**：
- **官方规范**（2020 修订稿）：正文"尽量控制在20页以内"，不是越长越好。
- CUMCM 评阅标准四项中无"论文长度"。评委评阅时间有限（每篇至少3位评委独立评阅，实际评阅时间原则不少于2天但分摊到每篇极短），过长论文反而降低评阅体验。
- 数维杯 2026 规则：AIGC 生成比例超过 30% 视为雷同——长论文如果是 AI 填充，反而增加违规风险。

**结论**：论文长度是软目标（本仓库 env 配置 min_pages 17 也是软目标），核心是内容密度和论证质量。本仓库的"所有数值可追溯到已验证 Result Artifact"铁律直接对抗"凑字数"倾向。

### 3.5 More references ≠ stronger evidence

**观察**：论文生成类项目通常集成文献搜索（Math Modeling Skill 的 paper_search 子 Skill 使用 OpenAlex API）。但引用数量不等于证据强度。

**证据**：
- CUMCM 参赛规则：引用他人成果必须按规定方式标注，"不得大篇幅照抄，否则视为学术不端"。
- 获奖论文的参考文献通常 10-20 篇，且每篇都与建模决策直接相关。堆砌不相关文献是减分项。
- MathDebugger 的核心发现：合成数据中存在大量隐性错误——自动检索的文献如果未经验证，可能引入错误引用。

**结论**：本仓库 reference-curator + consistency-checker + L5 护栏（无伪造引用）确保参考文献的真实性和相关性，而非数量。

### 3.6 Higher self-score ≠ actual capability

**观察**：
- MathModelAgent 宣称"3天→1小时""获奖级论文"——**无 benchmark evidence**。
- Math Modeling Skill 宣称"全流程自动化"——**无端到端评测**。
- 部分多 Agent 框架宣称"专业任务完成准确率 85%+"（基于领域测试集）——测试集未公开，不可复现。

**证据**：
- 这些项目均未在 CUMCM 实际竞赛中提交并获奖，无外部验证。
- 无公开的 ablation study（多 Agent vs 单 Agent、有/无 skill 系统的对比）。
- ASI-Bench、IDA-Bench 等独立基准显示现有 Agent 系统在复杂任务上表现远低于自宣称水平。

**标记**：所有"85+ score / award-winning / fully automatic"但无独立 benchmark evidence 的宣称，一律标记为 **marketing claim**。

---

## 4. 我们的定位

### 4.1 我们应该吸收什么

| 来源 | 可吸收要素 | 吸收方式 |
|---|---|---|
| Math Modeling Skill | 60+ 算法资源库的分类体系（优化/预测/评价/图论/统计/综合/ML） | 作为 knowledge base 方法卡的分类参考，补充到 `core/knowledge/` |
| Math Modeling Skill | xlsx 子 Skill 的"使用 Excel 公式而非硬编码值"规范 | 吸收到 programmer 的数据输出规范中 |
| Math Modeling Skill | "去 AI 味"七大类痕迹识别清单 | 补充到 writer 的 L5 护栏检查项 |
| ASI-Bench | 项目级任务设计（多环节、需代码实跑、需结果迭代） | 借鉴为 MMBench 任务结构的参考范式 |
| IDA-Bench | 迭代式需求变更 + 多轮成功率评估 | 验证 V3 DAG + reconcile 设计的合理性，可作为 failure handling 评估维度 |
| MathDebugger | 7 类细粒度错误类型分类 | 借鉴为 validator 错误分类体系 |
| Datawhale intro-mathmodel | Python 实现的常用模型代码 | 作为 method card 的代码参考素材 |
| AgentSociety | 多 Agent 辩论/模型选择模式 | 可作为 model-builder 候选模型对比的参考架构 |

### 4.2 我们不应该复制什么

| 不复制 | 原因 |
|---|---|
| "3天→1小时"的速度宣称 | 数学建模质量与时间正相关，过度压缩时间意味着跳过验证和迭代 |
| 60+ 算法的静态文档堆砌 | 算法库大不等于选择对，核心是决策逻辑而非资源数量 |
| "≥15000字"的论文长度目标 | 官方规范为"尽量20页以内"，长论文不代表好方案 |
| 三 Agent 固定流水线（建模→编程→论文） | 真实建模是迭代式的（IDA-Bench 验证），固定线性流水线无法处理回退和修正 |
| 自评分/自宣称准确率 | 无独立 benchmark 的自评分无意义，本仓库用 57 项 validator + 外部 MMBench |
| 商业平台的菜单化算法调用 | 黑箱工具调用无法追溯建模决策，与 evidence graph 理念冲突 |
| 纯数学解题基准（MATH/GSM8K）作为建模能力评估 | 这些基准不覆盖建模全流程，不能替代建模专项 benchmark |

### 4.3 我们的独特优势

| 优势 | 外部项目对比 |
|---|---|
| **Harness 架构**（Artifact Registry + Evidence Graph + Research State + Workflow DAG + 验证门禁） | 所有外部项目均为"Agent + Prompt"模式，无状态真源、无证据图、无运行时对账。MathModelAgent 和 Math Modeling Skill 都是无状态流水线。 |
| **Capability measurement**（57 项 validate.py + catalog_check + 758 pytest + score_compute 五维评分卡） | 外部项目无系统化能力度量。ASI-Bench/IDA-Bench 是外部基准，但不针对建模专项。本仓库有内部门禁 + 外部 benchmark 双重度量。 |
| **Evidence Graph**（所有数值可追溯到已验证 Result Artifact） | 无任何外部项目有证据链机制。Math Modeling Skill 的 paper_search 仅检索文献，不建立 claim→evidence 映射。 |
| **Replay**（replay.py 运行重放 + 差异归因） | 无外部项目支持运行重放。多 Agent 系统的失败通常无法定位到具体环节。 |
| **Deterministic**（随机种子固定 42 + 多种子 ≥5 次 + 均值标准差 + hash_chain） | 外部项目无确定性保证。MathModelAgent 支持本地/E2B 双模式但无种子控制。SPSSPRO 为商业黑箱。 |
| **V3 DAG + reconcile**（状态可对账、运行可重放） | IDA-Bench 从外部验证了迭代式需求的重要性，但无项目实现 DAG + reconcile 闭环。 |
| **Schema + 哈希链全绿** | 无外部项目有结构化输出 schema 校验和哈希链完整性验证。 |

### 4.4 我们缺什么

| 缺失 | 严重程度 | 补救方向 |
|---|---|---|
| **建模专项 benchmark（MMBench）的公开语料** | 高 | 需系统收集 CUMCM 历年题面+附件+获奖论文，构建可复现的 benchmark 语料库（在仓库外 MMBENCH_ROOT） |
| **方法卡的代码级实现** | 中 | Datawhale intro-mathmodel 有 Python 实现可参考，需将方法卡从文档级升级为可执行模板级 |
| **EDA 自动化深度** | 中 | Math Modeling Skill 的 xlsx 子 Skill 有数据处理规范，本仓库 EDA 能力需深化为自动化数据质量检查 + 特征工程建议 |
| **多模型对比/辩论机制** | 低 | AgentSociety 的多 Agent 交互可参考，用于 model-builder 的候选模型对比（当前 min_candidate_models=2） |
| **官方论文格式规范的自动化校验** | 中 | 需将 CUMCM 2020 论文格式规范（摘要页/正文≤20页/附录源代码）编码为 writer 的格式校验项 |
| **AI 工具使用合规性检查** | 高 | 2026 年 CUMCM 首次试行 AI 工具使用规定，需在论文中体现 AI 使用说明。本仓库需增加 AI 使用披露的自动化生成和合规检查 |

---

## 5. 反向验证：为什么坚持 Harness / Capability Measurement 路线

外部项目的"大而全"倾向从反面验证了本仓库路线的正确性：

### 5.1 "大而全"的结构性缺陷

| 倾向 | 结构性缺陷 | 本仓库的对策 |
|---|---|---|
| 多 Agent 堆砌 | 协调 overhead + 责任模糊 + 失败不可定位 | V3 5 Role DAG + state.py reconcile + replay.py 差异归因 |
| 算法库膨胀 | 选择困难 + 静态文档非执行 + 无决策逻辑 | method-matcher + assumption-validator + spec-auditor 决策链路 |
| 论文长度导向 | 内容稀释 + AIGC 检测风险 + 评阅疲劳 | 数值追溯铁律 + L5 护栏 + min_pages 为软目标 |
| 自宣称准确率 | 无独立验证 + 不可复现 + marketing 驱动 | 57 项 validator + 外部 MMBench + pytest 基线 |
| 无状态流水线 | 中断不可续跑 + 上下文丢失 + 结果不可对账 | Artifact Registry + Research State + 事件溯源 |
| 黑箱工具调用 | 决策不可追溯 + 错误不可归因 + 合规风险 | Evidence Graph + hash_chain + 所有数值溯源 |

### 5.2 外部基准的佐证

- **IDA-Bench**（最强 Agent 迭代分析成功率 40%）：证明线性流水线不够，需要 DAG + 回退 + 对账——本仓库 V3 的核心设计。
- **ASI-Bench**（60 项科研任务端到端评估）：证明项目级任务需要多环节闭环——本仓库从题面到论文的全链路覆盖。
- **MathDebugger**（合成数据 7 类隐性错误）：证明自动生成内容必须有质检机制——本仓库的 validator + L1-L6 门禁。
- **USAMO 2025**（所有大模型 <5%）：证明基础推理能力仍不足，Harness 的验证和回退机制比"相信模型一次做对"更可靠。
- **MATH-P-Hard**（所有模型准确率降 10-25%）：证明 prompt 工程有天花板，需要系统化的能力度量而非 prompt 调优。

### 5.3 结论

外部项目普遍停留在 **"Agent + Prompt + 算法库 + 论文模板"** 的组合层面，缺乏：
1. **状态真源**（谁在什么状态、产出了什么、是否验证过）
2. **证据链**（论文中的每个数字从哪里来、是否可复现）
3. **能力度量**（系统到底能做什么、不能做什么，有量化基线）
4. **失败可定位**（出错了是哪一环、为什么、怎么修）

本仓库的 Harness / Capability Measurement 路线正是针对这四个结构性缺陷。外部项目的"大而全"反而证明了"小而硬"（状态硬、证据硬、度量硬、验证硬）的稀缺性和必要性。

---

## 附录 A：检索方法与覆盖说明

- **检索时间**：2026-09-08
- **检索工具**：general_search（中英文多轮）+ web.fetch（深度阅读）
- **检索关键词**：CUMCM 2026 论文格式规范、全国大学生数学建模竞赛 评阅标准、CUMCM agent github、math modeling agent LLM、数学建模 多智能体、CUMCM benchmark、mathematical modeling benchmark LLM、MCM agent automated、ASI-Bench、MathModelAgent、Math Modeling Skill 等
- **覆盖局限**：
  - GitHub Star 数因搜索接口限制，部分项目未获取精确数值，标记为 N/A
  - 部分项目（如 MathDebugger）检索时未找到独立 GitHub 仓库，仅基于论文信息
  - 商业产品（SPSSPRO）的内部架构不可知，仅基于公开信息
  - 未检索到 CUMCM 2026 版论文格式规范（最新可检索的官方规范为 2020 修订稿），2026 年是否有更新需在官网确认
