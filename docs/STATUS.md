# MathModelSkills 状态快照

> 生成日期：2026-08-31（2026-09-01 更新：四手由 23 agent 扩展至 29 agent）
> 本文件记录项目当前的可运行状态，供后续会话快速接续。执行协议见 `../AGENTS.md`。

## 一分钟速览

四手 29 个 agent 的数学建模技能库，技术选型 **LaTeX**（单一主线，竞赛差异用 template pack 表达）。
目标是**任意通用 agent**（WorkBuddy / Claude Code / Trae / opencode / Cursor / Gemini / Copilot）
进入目录即可执行，不依赖自有 CLI。

核心机制：**让文件系统记住流程，而不是让模型记住流程**——
进度写进 `projects/<项目>/work/state.json`，agent 每次只需读一次就知道下一步。

## 目录分层

| 层 | 目录 | 说明 |
|---|---|---|
| 引擎 | `core/` | 四手 + 共享知识库 + 验证模块 + env + schemas + tools |
| 入口 | 根目录 | AGENTS.md + runtime 转发文件 + catalog.yaml + 安装脚本 |
| 实例 | `projects/<项目>/` | 赛题运行时产物（inputs / work / output / code / figures / paper） |
| 基础设施 | `docs/` + `tests/` + `.github/` | 文档 + 测试 + CI |

---

## 当前验证结果（全绿）

| 检查 | 命令 | 结果 |
|---|---|---|
| 项目级校验 | `python core/tools/validate.py` | **56 通过 / 0 失败 / 1 警告** |
| 测试套件 | `python -m pytest tests -q` | **217 passed / 0 failed** |
| 全链路门禁 | `python core/tools/gate.py cumcm2024a all` | **57 通过 / 0 硬失败 / 0 软失败** |
| 环境预检 | `python core/tools/doctor.py --project cumcm2024a --competition cumcm` | 就绪 27 / 警告 1 |
| 数字冻结 | `python core/tools/freeze_numbers.py cumcm2024a check` | 追溯率 **94.9%**（阈值取 env `runtime.traceability_min_ratio`=90%，与 validate 同口径） |
| 执行进度 | `python core/tools/state.py cumcm2024a status` | **23/29**（新增 6 agent 尚未在该实例补跑） |
| 评审判定 | `python core/tools/score_artifact.py cumcm2024a` | 均分 7.04，**verdict=refine** |

**已知警告（不阻塞，均有合理解释）**：

1. **文献年份**：近 3 年文献 7% < 60%。
   2024 年赛题的引用是当时的真实文献，无法引用后世文献。属 WARN 级，不阻塞。
   （检测基准已修正为赛题年份；同时新增「未来文献」检测防造假。）
2. **原始数据只读**：`projects/cumcm2024a/inputs/problem.md` 可写。
   建议设为只读后重新建立基线。

---

## 架构

### 四手 29 agent

| 手 | Agent 数 | 职责 | 产物契约 |
|---|---|---|---|
| Modeler | 8 | 问题分析、模型选型、数学建模 | `output/MODEL_SPEC.md` |
| Programmer | 6 | 代码实现、测试验证、结果输出 | `output/CODE_DELIVERABLES.md` |
| Writer | 7 | 论文撰写、图表、文献、校验 | `output/PAPER_SPEC.md` + `paper/main.pdf` |
| **Reviewer** | 8 | **评审**：打分（5 维）/ 挑缺陷 / 出修改清单 / 执行修改 | `work/revision_plan.json` |

Reviewer 的评审独立于撰写手自检，且**评分由脚本重算**（`core/tools/score_artifact.py`），避免模型给自己打高分。

### 两个硬规则（评审判定）

1. **最低分不被均分掩盖**：加权均分用于排序，但任一关键维度低于 `review.pass_score` 必须单独处理。
   当前样例均分 7.04 达标，但「创新与亮点」5.0 < 6.0，仍判 `refine`。
2. **权重夹紧在 [0.7, 1.5]**：避免题型偏好被过度放大。

### 门禁分级

- **HARD**：失败即阻塞交付
- **WARN**：文献年份 / 表格行数 / 段落句式 / 摘要字数 —— 只记警告

### 两处口径说明（易踩坑）

1. **论文字数**：按「跳过导言区 → 去注释 → 去数学环境 → 去 LaTeX 命令 → 统计中文字符 + 正文英文单词」计算。
   直接统计 LaTeX 源码会把 `\theta`、`\begin`、`\cite` 等命令计入，实测虚高约 2000 字。
2. **文献年份**：近 3 年以**赛题年份**为基准，不是当前年份；同时检测「未来文献」（引用造假信号，判 HARD）。

---

## 工具脚本（`core/tools/`，零第三方依赖）

| 脚本 | 用途 | 典型命令 |
|---|---|---|
| `state.py` | 执行状态唯一事实源（29 步） | `init` / `status` / `sync` / `advance` / `fail` / `reset` / `qfail` / `qfix` / `qstatus` |
| `gate.py` | 门禁判定 | `gate.py <项目> <hand> <agent>` / `<hand>` / `all` |
| `gatelib.py` | 门禁公共库（含内容级校验） | 供 gate.py 调用 |
| `score_artifact.py` | 评审判定，脚本重算 verdict + 题型差异化权重 | `score_artifact.py <项目> [--round N] [--type A\|C\|MCM...]` |
| `weight_profiles.py` | 题型差异化评审权重（A-E/MCM/ICM × 5 评分员，clamp+归一化） | `weight_profiles.py [题型]` |
| `freeze_numbers.py` | 数字冻结，论文数字单一真源 | `freeze` / `check` / `show` |
| `repro_checklist.py` | 复现清单：种子/依赖版本/SHA-256/唯一复现命令，generate/verify/show（写 output/reproducibility.json） | `repro_checklist.py <项目> generate\|verify\|show` |
| `render_ai_usage.py` | AI 使用台账与披露生成器 | `add` / `show` / `render --competition cumcm\|mcm` |
| `retrospect.py` | 赛后回顾（Growth 阶段）：汇总失败/返修/评审数据生成回顾报告 | `retrospect.py <项目>` |
| `reflection_bank.py` | 反思银行：跨项目经验沉淀与检索（scan/search/grounding/stats/export-pitfalls） | `reflection_bank.py scan\|search <关键词>\|grounding\|stats\|export-pitfalls` |
| `cloud_sandbox.py` | 云执行沙箱（可选）：E2B/Daytona/本地三后端 + 降级 | `cloud_sandbox.py run\|status\|config` |
| `check_matlab_env.py` | MATLAB/北太天元环境检测（决定是否产出交付分支） | `check_matlab_env.py [--summary] [--platform matlab\|beitian]` |
| `new_project.py` | 新项目脚手架：创建标准目录 + 导入赛题（多元化赛事开工） | `new_project.py <项目名> --competition cumcm --problem <文件>` |
| `benchmark.py` | 引擎演练（开工全链路冒烟，自动清理）+ 题库健康检查 | `benchmark.py pipeline --competition cumcm` / `library` |
| `doctor.py` | 环境预检（开工前暴露问题） | `doctor.py --project <项目> --competition cumcm` |
| `validate.py` | 项目级校验（57 项） | `validate.py` |
| `validate_project.py` | 单项目校验 | `validate_project.py <项目>` |

## 入口文件（跨 runtime）

`AGENTS.md` 是唯一权威入口。以下文件全部转发到它：

`CLAUDE.md` / `.cursorrules` / `.trae/rules/project_rules.md` / `.windsurfrules` /
`.clinerules` / `GEMINI.md` / `.github/copilot-instructions.md`

WorkBuddy / opencode / Codex 原生读取 `AGENTS.md`，无需转发。

全局安装（可选，非必需）：`./install.sh --target claude` 或 `.\\install.ps1 -Target claude`
支持 `--dry-run` / `--force`（带时间戳备份）。

## 能力分层

`runtime.profile`：`standard`（完整 29 步 + 全门禁）| `lite`（弱模型，放宽软性门禁）

## 竞赛包

`core/templates/latex/{cumcm,mcm,diangong,huawei,huashu}/`，各含 `config.yaml` + `rules.md` + `antipatterns.md`。
引擎分配沿用验证过的做法：CUMCM / 电工杯 / 华为杯用 **XeLaTeX**，MCM/ICM 用 **pdfLaTeX**。
MCM 包的 `rules.md` 另含 Summary Sheet（摘要页）专项规范：六段结构清单、一页口径、数字与正文同源。

## 知识库

- `core/knowledge/methodology/` **50 篇** + `INDEX.md` + 方法选型决策树（MD + JSON，method-matcher 已接入）
- `core/knowledge/paper-cases/` 论文案例拆解 **117 篇**（A/B/C/D/E 题 + 2025 江苏案例卡 + reference）
- `core/knowledge/pitfalls/` 反模式 + 数值边界 bug 库
- `core/knowledge/problems/` 赛题索引（CUMCM 2015–2025 共 36 条 + MCM/ICM 1995–2025 已核实题名 119 条）
- `core/knowledge/data-sources/` 权威公开数据源目录（外部数据引用规范）
- `core/knowledge/review/` 赛区评分细则与评委洞察（judge-scorer / weakness-hunter / structure-planner 已接入）
- `core/knowledge/validation/` 20 个验证模块
- 共享层（`core/knowledge/`）+ 私有层（`core/<Hand>/knowledge/`）

## 内容层

| 项 | 现状 | 优先级 |
|---|---|---|
| methodology 补篇 | **50 篇达成** + `INDEX.md` + 方法选型决策树（MD + JSON，method-matcher 已接入） | 已完成 |
| 赛题库 `core/knowledge/problems/` | CUMCM 2015–2025 索引（36 条；2018/2019 与库内案例卡交叉印证，2015–2017 据公开汇总资料整理）+ MCM/ICM 1995–2025 官方题面页核实题名（119 条，来源已标注；2015 缺 E/F、2014 缺 D–F、2001 缺 ICM C、2003–2013 每年仅列 A–C 三题、1998 及更早当年无 ICM）；1994 及更早官方页不可达待恢复 | 低 |
| 数据源目录 `core/knowledge/data-sources/` | 权威公开数据源分领域目录（宏观/环境/能源/金融/交通/健康/通用数据集/体育/开放网络/国际治理）+ 美赛题型→数据源映射表 | 低 |
| 高阶图表库 `core/Writer/knowledge/reference/advanced-figures.md` | 技术路线图/龙卷风/Taylor/雨云/桑基/标注热力图（零依赖配方），figure-generator 已接入 | 中 |
| D/E 题案例 | D-topic 7 篇 + E-topic 8 篇 | 中 |
| 失败案例库 `core/knowledge/_negative/` | README + 7 个负样本案例 | 中 |

---

## 接续指南

新会话开始时，先跑：

```bash
python core/tools/validate.py                    # 应 56/0/1
python core/tools/doctor.py --competition cumcm
python core/tools/state.py cumcm2024a status     # 应 29/29（当前实例 23/29，新增 6 agent 待补跑）
```

然后读 `AGENTS.md` 的「执行协议」章节了解五步循环。
任何改动后重跑上述三条，确保没有回退。