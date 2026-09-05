# MathModelSkills 改进计划

基于对 GitHub 同类优秀项目的深度分析，制定本项目的持续改进路线图。

---

## 竞品分析总结

| 项目 | 核心亮点 | 可借鉴点 |
|------|---------|---------|
| **Lupynow/math-modeling-skills** | 8本 Cookbook、29个代码模板、12个 Playbook、Stage 1.5 文献检索、Paper Bridge | 算法手册化、端到端例题、文献支撑建模选择 |
| **handsomeZR/mathmodel-skill** | 10阶段+4反馈层、Harness-agnostic、Friendly Mode、91篇论文蒸馏 empirical.json、Per-Qi加权、题型Dim权重、Codex-native | 跨运行时状态共享、问答式交互、实测分位锚定、差异化降级 |
| **xuec699/math-modeling-skills** | 双模式、6维选题评估、模型依赖DAG、5人评审团、学术诚信门控、Word OMML公式、三线表自动 | 可视化依赖、多视角评审、反幻觉、Word生产线 |
| **liuziyang/mathmodel-pro** | Word生产线、6阶段量化验收、9篇获奖论文范式、经典题算法速查 | Pandoc+MathType管线、血泪教训、视觉检查清单 |
| **MaYucong/MCM_skills** | 决策日志、时间预算、L2回溯、Fresh-eyes、反思银行、记忆架构、工具接地验证 | 过程可追溯、元认知、长程记忆 |
| **Jaxon/MathModelHub** | 团队协作指南、5天时间轴、算法参考手册、历年C题论文库 | 团队工程化、实战手册 |
| **usail-hkust/MM-Agent** | HMML 98方法节点层级库、Actor-Critic 方法选择、MLE-Solver 自动代码迭代、Next.js+FastAPI Web UI、E2B 沙箱 | 层级化方法检索、沙箱执行、Web 交互界面 |
| **jihe520/MathModelAgent** | 9步自动验收、17套 Typst 布局、E2B/Daytona 云解释器、Tavily 网络搜索、ChromaDB RAG、Docker 部署、人机交互6决策动作、科学图表配套仓库 | 多格式排版、云执行、RAG 知识库、容器化部署 |
| **XiaoMaColtAI/math-modeling-skill** | 981★、三阶段（建模/编程/论文）+ 阶段内只读质检 Subagent、Python+MATLAB 双语言、出版级可视化（色觉友好 + SVG/300DPI）、OpenAlex+AnySearch 双引擎文献、复现清单（种子/SHA-256/依赖版本/唯一复现命令）、默认 Word 论文、DeepSeek Harness 插件、覆盖 APMCM/MathorCup/认证杯/数维杯 | 双语言实现、复现清单、双引擎文献、多竞赛覆盖、出版级可视化 |
| **zhnnky329/MathModeling-skills** | Claude Code/Codex Skills、Python + MATLAB/北太天元代码分支、分阶段建模流程 | MATLAB/北太天元国产替代分支 |
| **N-allpass/modex-mh-agent** | AI 全自动数学建模智能体、国赛/美赛/华为杯全覆盖、一夜跑完（架构展示） | 全自动一站式（定位差异，不作主方向） |

> 2026-09-01 更新：新增 MM-Agent、MathModelAgent 两个竞品分析；并补充 XiaoMaColtAI / zhnnky329 / N-allpass 三个竞品（Python+MATLAB 双语言、复现清单、双引擎文献、多竞赛覆盖、国产 MATLAB 替代分支）。

---

## 核心差距矩阵

| 能力维度 | 现状 | 目标 | 优先级 |
|---------|------|------|--------|
| **文献检索支撑** | 无 | ~~P0~~ ✅ 已完成（literature-searcher agent + schema + env 配置 + state.py 集成，Stage 1.5 硬上限5次/5-8篇，期刊含金量标注） |
| **算法手册** | 方法论文档50+，但非Cookbook形态 | ~~P0~~ ✅ 已完成（8大类 Cookbook：优化/ML/评价/机理/统计/网络/聚类/博弈） |
| **端到端例题** | 无 | ~~P0~~ ✅ 已完成（12 Playbook：国赛9+美赛3，含拆题→代码全流程） |
| **实测分位锚定** | 无 | ~~P1~~ ✅ 已完成（empirical.json：117篇蒸馏，overall + A/B/C/D/E 分题型 p25/p50/p75 + 代码指标 + 质量基准 + 方法频率） |
| **友好交互模式** | 无 | Friendly Mode：全程编号选项+兜底"让我决定" | ~~P1~~ ✅ 已完成（friendly/__init__.py） |
| **跨运行时状态** | state.py 单项目 | decision_log.json 跨 Claude/Codex/Cursor 互通 | ~~P1~~ ✅ 已完成（schema + friendly 集成） |
| **模型依赖DAG** | 无 | 子模型依赖可视化有向无环图 | ~~P1~~ ✅ 已完成（dag-builder + model_dag.schema + diagram_gen.py） |
| **多视角评审** | 4 agent 单视角 | 5人评审团（学术/工程/评委/读者/对抗） | ~~P2~~ ✅ 已完成（5 scorer agents） |
| **学术诚信门控** | 护栏检查 | 7类阻断式检查（抄袭/造假/引用缺失/未来文献/数据篡改/AI比例/匿名违规） | ~~P2~~ ✅ 已完成（integrity_gate.py） |
| **Word/OMML生产线** | tex_to_docx.py 基础版 | Pandoc+三线表(1.5/0.5pt)+居中编号公式+MathType+视觉检查 | ~~P2~~ ✅ 已完成（结构化降级版：三线表+编号公式+标题样式+styles.xml） |
| **决策日志/时间预算** | 无 | decision_log.json + time_budget.yaml + handoff.md | ~~P2~~ ✅ 已完成（schema + friendly + new_project 脚手架） |
| **反思银行/记忆** | retrospect.py 赛后 | 持久化反思银行 + 记忆架构 + 工具接地验证 | ~~P3~~ ✅ 已完成（reflection_bank.py：scan/search/grounding/stats/export-pitfalls 五命令 + _bank/reflections.json 聚合索引，+4 测试） |
| **题型差异化权重** | 固定权重 | A优化/C数据/MCM沟通/F政策 动态权重 clamp[0.7,1.5] | ~~P3~~ ✅ 已完成（weight_profiles.py + config.yaml + 已接入 score_artifact.py：题型自动解析 + 5 评分员映射 + 旧 8 维回退兼容，+7 测试） |
| **Codex/插件原生** | 无 | .codex-plugin/plugin.json + adapters/openai.yaml | ~~P3~~ ✅ 已完成（plugin.json 更新：29 agent + 10 竞赛枚举 + catalog.yaml 注册新工具） |
| **团队协作指南** | 无 | 角色分工、时间轴、工具配置、冲突解决 | ~~P3~~ ✅ 已完成（docs/TEAM_GUIDE.md：三手映射 + 72h/96h 时间轴 + 协作模式 + 冲突解决 + 反模式） |
| **Docker 部署** | 无 | Dockerfile + docker-compose.yml 一键启动 | ~~P1~~ ✅ 已完成 |
| **华数杯竞赛支持** | 4 竞赛（cumcm/mcm/diangong/huawei） | 新增 huashu 竞赛模板 | ~~P1~~ ✅ 已完成 |
| **科学图表工具** | 无独立工具 | diagram_gen.py 支持流程图/DAG/结果图/对比图 | ~~P1~~ ✅ 已完成 |
| **云执行沙箱** | 无 | E2B/Daytona 云端代码执行（可选） | ~~P3~~ ✅ 已完成（cloud_sandbox.py：E2B/Daytona/本地三后端 + API Key 检测 + 超时控制 + 本地降级，+8 测试） |
| **扩展 Typst 模板** | 2 套（cumcm/mcm） | 覆盖全部 5 竞赛的 Typst 布局 | ~~P2~~ ✅ 已完成（5套：cumcm/mcm/diangong/huawei/huashu） |
| **铁律补全** | M1-M7/P1-P9/W1-W10 | 补全 M8-M9/P10-P12/W11-W14 | ~~P0~~ ✅ 已完成 |
| **Paper Bridge 契约** | 无 | `paper-bridge.md`：MODEL_SPEC→论文章节映射 + 数值占位符协议 + 诚实讨论模板 | ~~P0~~ ✅ 已完成 |
| **MATLAB/北太天元代码分支** | 仅 Python | 双语言代码模板 + `check_matlab_env` 依赖检查 + 国产替代分支 | ~~P2~~ ✅ 已完成（check_matlab_env.py + 6 模板 .m：GA/PSO/SA/DE/IP/多元回归） |
| **复现清单** | freeze_numbers 数字冻结 | 依赖版本 + SHA-256 + 唯一复现命令的 `复现清单.json` | ~~P1~~ ✅ 已完成（reproducibility.schema.json + repro_checklist.py：import 扫描依赖 + 一等方过滤 + generate/verify/show 漂移校验 + 6 测试） |
| **双引擎文献检索** | scholar_fetch 5 源回退 | 增加 OpenAlex（DOI/题名交叉核验） | ~~P1~~ ✅ 已完成（scholar_fetch.py cross_verify() + cross-verify CLI：OpenAlex DOI/题名交叉核验双通道） |
| **多竞赛覆盖扩展** | 5 竞赛（cumcm/mcm/diangong/huawei/huashu） | 增加 APMCM / MathorCup / 认证杯 / 数维杯 | ~~P2~~ ✅ 已完成（9 竞赛：+apmcm/mathorcup/renzhengbei/shuweibei 模板包 + new_project.py 支持） |
| **出版级/色觉友好可视化** | advanced-figures.md（零依赖配方） | 色觉友好编码 + SVG/300DPI 双导出 + 成图自检闭环 | ~~P2~~ ✅ 已完成（advanced-figures.md 新增：Okabe-Ito 调色板 + cividis colormap + 颜色/形状双编码 + SVG/PDF/PNG 三格式导出 + 单图/批量自检闭环 + 色盲模拟） |
| **投稿前检查清单** | 无 | docs/CHECKLIST.md 覆盖 L1-L6 + 5 竞赛特定检查 | ~~P2~~ ✅ 已完成 |
| **AGENTS.md 同步** | 23 agent 文档 | 同步至 29 agent（Modeler 8 + Reviewer 8） | ~~P1~~ ✅ 已完成 |
| **新 agent 运行时配置补齐** | 19 agent 有 evals/openai，10 个新 agent 缺失 | 10 个新 agent 的 `evals.json` + `openai.yaml` + 测试覆盖扩至 29 agent | ~~P1~~ ✅ 已完成 |

---

## 分阶段实施路线图

### Phase 1: 核心能力补全（P0，1-2周）

#### 1.1 增加 Stage 1.5：文献检索 Agent
- **位置**：`core/Modeler/agents/literature-searcher/` (新增，插在 type-classifier 与 method-matcher 之间)
- **职责**：拆题后先搜文献，提取方法证据，标注期刊含金量（SCI Q1-Q4 + 中文核心），可跳过
- **产物**：`work/literature_evidence.json`
- **门禁**：检索次数≤5，文献数 5-8，每篇有 DOI/年份/期刊分级

#### 1.2 构建 8 大 Cookbook
- **目录**：`core/knowledge/cookbooks/`
- **8 个文件**：
  - `cookbook-optimization.md` (GA/PSO/SA/LP/DP/整数规划/多目标/鲁棒优化)
  - `cookbook-ml.md` (XGBoost/RF/SVM/NN/集成/深度学习/特征工程)
  - `cookbook-evaluation.md` (TOPSIS/AHP/熵权/模糊/灰色/DEA/综合评价)
  - `cookbook-mechanistic.md` (热传导/ODE/PDE/几何光学/流体/结构力学)
  - `cookbook-statistical.md` (假设检验/ANOVA/蒙特卡洛/贝叶斯/生存分析)
  - `cookbook-network.md` (网络流/最短路/中心性/社区发现/图神经网络)
  - `cookbook-clustering.md` (层次/K-Means/DBSCAN/GMM/谱聚类/密度峰值)
  - `cookbook-game-theory.md` (Nash/演化/Stackelberg/机制设计/拍卖/合作博弈)
- **格式**：每模型含「适用场景/核心公式/代码模板指引/参数敏感性/常见坑/文献支撑」

#### 1.3 建设 12 个 Playbook
- **目录**：`core/knowledge/playbooks/`
- **国赛 9 个**：A/B/C/D/E 五题型覆盖 + 经典组合（如 2024A 优化、2023C 数据、2022B 实验、2021D 运筹、2020E 跨学科 + 4 个历年高分案例）
- **美赛 3 个**：A 连续/机理、B 离散/图论、C 大数据/预测
- **每个 Playbook 含**：问题拆解 JSON、类型判定、候选模型对比表、模型建立全推导、代码完整实现、结果验证报告、论文结构规划、关键图表、完整 LaTeX 源码

#### 1.4 Paper Bridge 规则
- **文件**：`core/Modeler/knowledge/paper-bridge.md`
- **内容**：MODEL_SPEC → 论文章节映射表、数值占位符协议、假设/符号/边界条件在论文中的呈现规范、模型评价诚实讨论模板

---

### Phase 2: 体验与工程化（P1，2-3周）

#### 2.1 Friendly Mode（全程问答式）
- **机制**：所有关键决策点（选题/选模型/verdict/refine）以编号选项呈现
- **实现**：各 agent SKILL.md 顶层约束 `interaction_mode: friendly`
- **兜底**：每个问题提供 "让我决定 (推荐 X)" 选项
- **状态文件**：`work/decision_log.json` 记录每轮 {question, options, choice, rationale, timestamp}

#### 2.2 Harness-Agnostic 与 Codex-Native
- **新增**：
  - `.codex-plugin/plugin.json` (Codex 插件清单)
  - `adapters/openai.yaml` (OpenAI Agents SDK 兼容)
  - `skills/mathmodeling/` (Codex skill shim)
- **协议**：`docs/integration/harness-compat.md` 定义跨运行时行为约定
- **状态互通**：`decision_log.json` 跨 Claude Code / Codex CLI / opencode / Cursor 共享

#### 2.3 实测分位锚定
- **数据源**：教育部展廊 2023-2025 (32篇) + GitHub zhanwen/MathModel (58篇) + Jackyleo/cumcm-2025 等，共 91+ 篇
- **产出**：`core/knowledge/empirical/cumcm-empirical.json`
- **11 维指标**：正文字数/页数/图表数/表格数/公式数/参考文献数/摘要字数/灵敏度分析深度/创新标签数/模型复杂度/代码行数
- **分位**：p25/p50/p75 直接注入 L1 Critic prompt 的 evidence 字段

#### 2.4 模型依赖 DAG
- **新增 Agent**：`core/Modeler/agents/dag-builder/` (Stage 4.5，model-builder 后)
- **输入**：`work/model_draft.md` + `work/method_candidates.json`
- **输出**：`work/model_dag.json` (nodes: 子模型, edges: 数据/参数依赖) + `work/model_dag.svg` (Graphviz 渲染)
- **用途**：指导 Programmer 并行化、Writer 结构规划、Reviewer 定位级联风险

---

### Phase 3: 质量与合规硬化（P2，2-3周）

#### 3.1 5 人评审团
- **扩展 Reviewer 手**：`judge-scorer` → 5 个独立 scorer agent
  - `scorer-academic` (学术严谨性：推导/假设/验证)
  - `scorer-engineering` (工程落地：代码/复现/性能/鲁棒性)
  - `scorer-judge` (评委视角：创新/完整性/规范/亮点)
  - `scorer-reader` (可读性：结构/语言/图表/叙事)
  - `scorer-adversarial` (对抗视角：找漏洞/反例/边界/造假风险)
- **聚合**：加权平均 + 最低分否决制（任一关键维度 <6 即 block）
- **输出**：`work/score_card_multi.json` + `work/panel_consensus.md`

#### 3.2 学术诚信门控
- **新增**：`core/validators/modules/integrity_gate.py`
- **7 类阻断检查**：
  1. 文本相似度（Turnitin式 n-gram，阈值 15%）
  2. 数据造假特征（Benford/分布异常/过度拟合）
  3. 引用闭合性（所有 \citep{} 在 bib 中、年份≤赛题年份、无未来文献）
  4. AI 写作比例（检测 8 类痕迹，占比 >30% 阻断）
  5. 匿名违规（作者/学校/导师/致谢/文件属性）
  6. 数值唯一事实源（所有数字可追溯 all_results.json）
  7. 占位符/禁用词/内部路径残留

#### 3.3 Word/OMML 生产线升级
- **增强 `tex_to_docx.py`**：
  - Pandoc + 自定义 Lua filter 处理三线表 (1.5pt/0.5pt)
  - 数学公式 → OMML (可编辑 Word 公式，非图片)
  - 图片统一导出 SVG/EMF 矢量
  - 页码/页眉/页脚/目录自动生成
  - 视觉检查清单：字体/行距/边距/编号/交叉引用/参考文献格式

#### 3.4 决策日志 + 时间预算 + 交接协议
- **decision_log.json**：已有雏形，扩展字段 {stage, agent, decision_type, options, choice, confidence, time_spent, alternatives_considered}
- **time_budget.yaml**：每 stage 预算分钟数，实时剩余，超支预警
- **handoff.md**：四手交接清单（输入契约/输出契约/验收项/风险提示/回滚点）

---

### Phase 4: 进阶智能化（P3，持续迭代）

#### 4.1 反思银行 + 记忆架构
- **反思银行**：`core/knowledge/_negative/reflection_bank.json`
  - 结构：{problem_pattern, failure_mode, root_cause, fix_strategy, prevention_rule, confidence, usage_count}
  - 来源：retrospect.py 赛后汇总 + 评审缺陷 + 实战复盘
- **记忆架构**：长期记忆（模式库）+ 工作记忆（当前项目决策链）+ 情景记忆（相似题检索）
- **工具接地验证**：每次工具调用前后校验副作用，防止幻觉工具调用

#### 4.2 题型差异化权重
- **配置**：`core/env/dim_weights.yaml`
- **权重矩阵**：
  | 竞赛/题型 | 模型权重 | 统计/灵敏度 | 代码/复现 | 表达/沟通 | 创新/政策 |
  |----------|---------|------------|----------|----------|----------|
  | CUMCM-A  | 1.3     | 0.8        | 1.0      | 0.9      | 1.0      |
  | CUMCM-B  | 0.9     | 1.2        | 1.1      | 0.8      | 1.0      |
  | CUMCM-C  | 0.8     | 1.5        | 1.2      | 0.9      | 1.0      |
  | MCM-A/B  | 1.2     | 1.0        | 1.1      | 1.3      | 1.0      |
  | MCM-F    | 0.9     | 1.1        | 0.9      | 1.2      | 1.4      |
- **Clamp**：[0.7, 1.5] 防过激
- **消费**：`score_artifact.py` 在加权聚合时应用

#### 4.3 Per-Qi 差异化降级
- **Verdict 扩展**：`pass_with_review` / `refine_partial` (已有雏形，需深化)
- **逻辑**：单 Qi 弱不再被全 stage 平均掩盖
- **执行**：revision-planner 输出 `target_questions: [Q2]`，revision-executor 仅修改受影响章节
- **效率**：节省 ~60% 修改时间

---

## 技术债务清理（并行进行）

| 债务项 | 现状 | 目标 |
|--------|------|------|
| **Modeler laws M8/M9 缺失** | 只有 M1-M7 | 补充 M8: 模型复杂度匹配问题规模 / M9: 结果可解释性优于黑盒精度 |
| **Programmer laws P10-P12 缺失** | 只有 P1-P9 | 补充 P10: 计算资源感知 / P11: 结果可视化自动化 / P12: 代码模块化可复用 |
| **Writer laws W11-W14 缺失** | 只有 W1-W10 | 补充 W11: 创新点显性化 / W12: 局限性诚实讨论 / W13: 复现包完整性 / W14: 评审视角预判 |
| **env 参数文档化** | README 简述 | `core/env/README.md` 完整参数表 + 修改示例 + 回退机制 |
| **测试覆盖** | 190 passed | 增加集成测试：全链路跑通、边界条件、异常注入、并发安全 |

---

## 目录结构变更预览

```
MathModelSkills/
├── core/
│   ├── Modeler/
│   │   ├── agents/
│   │   │   ├── literature-searcher/      # NEW (Stage 1.5)
│   │   │   ├── dag-builder/              # NEW (Stage 4.5)
│   │   │   └── ...existing 6 agents...
│   │   ├── knowledge/
│   │   │   ├── cookbooks/                # NEW (8 files)
│   │   │   ├── playbooks/                # NEW (12 dirs)
│   │   │   ├── paper-bridge.md           # NEW
│   │   │   └── ...existing...
│   │   └── ...
│   ├── Reviewer/
│   │   ├── agents/
│   │   │   ├── scorer-academic/          # NEW
│   │   │   ├── scorer-engineering/       # NEW
│   │   │   ├── scorer-judge/             # NEW
│   │   │   ├── scorer-reader/            # NEW
│   │   │   ├── scorer-adversarial/       # NEW
│   │   │   └── ...existing 4 agents...
│   │   └── ...
│   ├── knowledge/
│   │   ├── empirical/                    # NEW
│   │   │   └── cumcm-empirical.json
│   │   ├── cookbooks/                    # NEW (共享层也可复用)
│   │   ├── _negative/
│   │   │   └── reflection_bank.json      # NEW
│   │   └── ...
│   ├── env/
│   │   ├── config.yaml                   # 扩展
│   │   ├── dim_weights.yaml              # NEW
│   │   └── time_budget.yaml              # NEW
│   └── ...
├── .codex-plugin/
│   └── plugin.json                       # NEW
├── agents/
│   └── openai.yaml                       # NEW
├── skills/
│   └── mathmodeling/                     # NEW (Codex skill shim)
├── references/
│   └── harness_compat.md                 # NEW
└── docs/
    ├── TEAM_WORKFLOW.md                  # NEW
    ├── FRIENDLY_MODE_GUIDE.md            # NEW
    └── IMPROVEMENT_PLAN.md               # 本文件
```

---

## 成功指标

| 指标 | 当前 | 目标 (Phase 4 后) |
|------|------|------------------|
| 验证通过率 | 56/57 | 57/57 (0 警告) |
| 端到端跑通样例 | 1 (cumcm2024a) | 12 (Playbook 全覆盖) |
| 文献支撑率 | 0% | 100% (method-matcher 每候选必引文献) |
| 友好模式覆盖 | 0% | 100% 关键决策点 |
| 跨运行时状态互通 | 单项目 | 全哈ness 共享 decision_log |
| 评审视角数 | 1 (脚本重算) | 5 (多视角面板) |
| 学术诚信拦截 | 基础护栏 | 7 类阻断式门控 |
| Word 交付质量 | 基础转换 | 竞赛级视觉检查全绿 |
| 实测分位锚定 | 无 | 91 篇 p25/p50/p75 注入 L1 |

---

## 风险与对策

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| Cookbook/Playbook 维护成本高 | 中 | 高 | 建立自动化测试：每 Playbook 必跑通代码+编译 PDF+通过验证 |
| 实测分位数据版权 | 低 | 中 | 仅蒸馏统计量 (p25/p50/p75)，不存全文；来源标注公开渠道 |
| Friendly Mode 过度约束专家用户 | 低 | 低 | 提供 `expert_mode` 标志跳过问答，直接读 decision_log |
| 5人评审团 token 消耗大 | 中 | 中 | 并行调用 + 缓存同类问题评审结果 + 增量评审 |
| Codex 插件维护跟不上上游 | 低 | 低 | 仅维护 shim 层，核心逻辑在 core/ 复用 |

---

## 立即行动项 (本周)

1. **创建 Stage 1.5 literature-searcher agent 目录结构 + SKILL.md 骨架**
2. **建立 `core/knowledge/cookbooks/` 目录，迁移现有 methodology 文档为 Cookbook 格式**
3. **设计 `work/decision_log.json` schema 并更新 `core/tools/state.py` 支持**
4. **编写 `core/knowledge/empirical/` 采集脚本，启动 91 篇论文蒸馏流水线**
5. **补充 Modeler/Programmer/Writer 缺失铁律 (M8/M9, P10-P12, W11-W14)**
6. **创建 `.codex-plugin/plugin.json` 和 `adapters/openai.yaml` 最小可用版本**

---

## 维护原则

1. **引擎与实例分离**：`core/` 只放可复用引擎，`projects/` 存实例产物
2. **契约优先**：任何新增 agent 必须定义输入/输出 Schema 和 Stage Gate
3. **门禁脚本化**：Self-Check 复选框 → 可执行 Python 断言 (`gate.py` / `gatelib.py`)
4. **配置外置化**：阈值全部在 `core/env/config.yaml`，代码零硬编码
5. **可追溯性**：每个数值/决策/修改都有哈希链锚定
6. **向后兼容**：新增能力不破坏现有 29 agent 流程，通过 `runtime.strict_mode` 控制

---

*文档版本：1.0 | 创建时间：2026-09-01 | 维护者：MathModelSkills 核心团队*