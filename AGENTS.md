# MathModelSkills — AGENTS

基于 UTG（通用可信生成架构）的数学建模 agent skills 库：四手（Modeler / Programmer / Writer / Reviewer）各司其职，每手内部多 agent 按 UTG L1–L6 串联，最终交付可追溯、可复现、无 AI 痕迹的数学建模论文。

## 定位

MathModelSkills 把"一道赛题 → 一篇论文"的全流程拆分为四个独立可回退的手，每个手再按 UTG 六层防御机制拆分为多个 agent。UTG 的 L1–L6 已从文档机制落地为具体 agent 实体，每层都有唯一承载 agent 与可执行的自检门禁。

- **四手**：Modeler（建模）/ Programmer（编程）/ Writer（撰写）/ Reviewer（评审），四手串联，下游消费上游产物契约。
- **每手内多 agent**：Modeler 8 / Programmer 6 / Writer 7 / Reviewer 8，共 **29 个 agent**，按 stage 顺序串联，每个 agent 对应一个 UTG 层。
- **env 配置层**：根目录 `core/env/config.yaml` + `core/env/loader.py`，五组参数（paper / code / modeling / review / runtime）外加 checkpoint 组统一注入，agent 不再硬编码阈值。
- **UTG 六层防御落地**：L1 形式化规约 / L2 工具调用 / L3 过程验证 / L4 异构验证 / L5 运行时护栏 / L6 事后哈希审计，每层均有 agent 承载与 Self-Check 门禁。
- **跨 runtime 执行协议**：任意通用 agent（WorkBuddy / Claude Code / Trae / opencode / Cursor 等）进入本目录即可执行，不依赖自有 CLI。详见下方「执行协议」。

## 执行协议（所有 agent runtime 通用）

**这是本仓库最重要的章节。** 无论你是什么 agent runtime，都按此执行。

核心原则：**让文件系统记住流程，而不是让你记住流程。** 29 个 agent 共约 4500 行指令，不要试图一次读完再执行——每次只推进一步。

### 每一步的五步循环

```
1. 读状态    python core/tools/state.py <项目> status
             （或读 projects/<项目>/work/STATE.md）
2. 读指令    读它指出的那一个 core/<Hand>/agents/<agent>/SKILL.md
3. 执行      按该 SKILL.md 的 Procedure 做，产物写到它指定的路径
             （SKILL.md 指向 RUNBOOK.md / 知识文件时才额外读，不要预读）
4. 跑门禁    python core/tools/gate.py <项目> <hand> <agent>
5. 推进      PASS → python core/tools/state.py <项目> advance <hand> <agent> --output <产物路径>
             FAIL → 按该 SKILL.md 的 ## Iteration 修正后重跑，最多 3 轮
                    3 轮仍失败 → 按回退规则退回上游，不向下游推进
```

全部 29 步完成后：`python core/tools/gate.py <项目> all` 做全链路终检。

### 首次进入 / 中断恢复

```bash
python core/tools/state.py <项目> init     # 从已有产物反推进度，不需要任何对话记忆
python core/tools/state.py <项目> status   # 看下一步做什么
```

`init` 会扫描 29 个 agent 的主产物，自动算出已完成哪些步骤。因此**换 session、换模型、上下文被压缩，都不影响续跑**。

### 为什么必须这样做

- 你不需要记住 29 个步骤的顺序，只需要每次读一次 `STATE.md`。
- 你的上下文里同时只存在一个 agent 的指令（≤60 行），不会爆上下文。
- 门禁由脚本判定，不是靠你在 Self-Check 的 `[ ]` 里打勾——那些复选框模型可以勾完继续，等于没有门禁。

### 命令速查

| 命令 | 作用 |
|---|---|
| `python core/tools/state.py <项目> init` | 初始化 / 从产物反推进度 |
| `python core/tools/state.py <项目> status` | 显示下一步 |
| `python core/tools/state.py <项目> advance <hand> <agent> --output <路径>` | 登记完成并推进 |
| `python core/tools/state.py <项目> fail <hand> <agent> --reason "..."` | 记录失败 |
| `python core/tools/state.py <项目> reset --to <hand>/<agent>` | 回退到指定步 |
| `python core/tools/new_project.py <项目名> --competition cumcm --problem <文件>` | 新项目脚手架（建目录 + 导入赛题） |
| `python core/tools/retrospect.py <项目>` | 赛后回顾报告（过程数据汇总） |
| `python core/tools/benchmark.py pipeline --competition cumcm` | 开工演练（脚手架→init→doctor，自动清理） |
| `python core/tools/gate.py <项目> <hand> <agent>` | 单步门禁 |
| `python core/tools/gate.py <项目> all` | 全链路门禁 |
| `python core/tools/validate.py` | 项目级 57 项校验 |
| `python core/tools/validate_project.py <项目>` | 单项目级校验 |
| `python core/tools/diagram_gen.py flowchart --nodes "A,B,C" --edges "A->B" -o fig.svg` | 科学图表生成（流程图/DAG/结果图/对比图） |
| `python core/tools/scholar_fetch.py bibtex <关键词>` | 学术文献检索 + BibTeX 获取（5源回退链） |
| `python core/tools/citation_check.py project <项目> [--json]` | 引用可信度扫描（L5 护栏补充） |
| `python core/tools/citation_check.py bib <file> [--json]` | BibTeX 格式校验 |
| `python core/tools/benchmark.py bench list --json` | 列出可用 rubric |
| `python core/tools/benchmark.py bench run --rubric <f>` | 生成得分响应模板 |
| `python core/tools/benchmark.py bench score --rubric <f> --response <f>` | 重算校验响应 |
| `python core/tools/benchmark.py bench report --rubric <f> --response <f>` | 生成可读报告 |
| `python core/tools/bench_mmbench.py list` | 列出 MMBench 111 题 |
| `python core/tools/bench_mmbench.py export --year <Y> --topic <A>` | 导出为 rubric 骨架 |
| `python core/tools/orchestrator.py <项目>` | 一键执行 29 步流水线（含重试/回退） |
| `python core/tools/score_compute.py <项目>` | 自动化 5 维评分卡生成（学术/工程/评委/读者/对抗） |

> 用 `python` 或 `python3` 均可，`core/tools/` 下核心脚本零第三方依赖；`diagram_gen.py` 需 `pip install matplotlib`。

## 使用方式（编排层视角）

1. **准备赛题**：`python core/tools/new_project.py <项目名> --competition cumcm|mcm|diangong|huawei|huashu --problem <赛题文件>`（创建标准目录并导入赛题；也可手工把赛题文件放入 `projects/<项目>/inputs/`）。
2. **初始化状态**：`python core/tools/state.py <项目> init`。
3. **按上述执行协议逐步推进**：Modeler（8 步）→ Programmer（6 步）→ Writer（7 步）→ Reviewer（8 步）。每步都跑门禁。
4. **运行验证**：`python core/tools/validate.py` 验证产物完整性（schema / 哈希链 / 数值一致性 / 护栏）。
5. **回退规则**：任一阶段失败，按各 agent SKILL.md 的 `## Iteration` 在本手内回退修正，不向下游推进。

### 一键执行（可选）

```bash
python core/tools/orchestrator.py <项目>           # 一键执行 29 步（含重试/回退）
python core/tools/score_compute.py <项目>          # 自动生成 5 维评分卡
```

## 项目结构

```
MathModelSkills/
├── core/                         # 核心引擎（技能 + 知识 + 工具 + 配置 + 模板）
│   ├── Modeler/                  # 建模手（8 agent）
│   │   ├── agents/<name>/SKILL.md
│   │   ├── knowledge/            # domain / problem-types（特有知识）
│   │   ├── laws/rules.md         # 建模手铁律 M1–M9
│   │   ├── templates/MODEL_SPEC_TEMPLATE.md
│   │   └── SKILL.md              # 手级编排器（Agent Orchestra）
│   ├── Programmer/               # 编程手（6 agent）
│   ├── Writer/                   # 撰写手（7 agent）
│   ├── Reviewer/                 # 评审手（8 agent：5 评分员 + 缺陷猎手 + 修改规划 + 修改执行）
│   ├── knowledge/                # 共享知识库（四手统一）
│   │   ├── methodology/          # 方法论文档（50 篇 + 选型决策树 + INDEX）
│   │   ├── paper-cases/          # 论文案例
│   │   ├── pitfalls/             # 反模式 / 数值边界
│   │   ├── problems/             # 历史赛题索引（CUMCM 2015–2025 + MCM/ICM 1995–2025 已核实题名）
│   │   ├── data-sources/         # 权威公开数据源目录（外部数据引用规范 + 美赛题型映射）
│   │   ├── review/               # 评分细则与评委洞察（judge-scorer / weakness-hunter 消费）
│   │   └── validation/           # 验证模块（guardrails / hash_chain / stage_gate 等）
│   ├── env/                      # 环境变量配置层（config.yaml + loader.py）
│   ├── schemas/                  # 结构化输出 Schema
│   ├── templates/                # LaTeX 竞赛包（cumcm / mcm / diangong / huawei / huashu）
│   └── tools/                    # 全部工具脚本（state / gate / validate / doctor 等）
├── projects/                     # 项目实例
├── docs/                         # 文档（ARCHITECTURE.md + STATUS.md）
├── tests/                        # unit / integration / e2e 测试
├── AGENTS.md                     # 本文件（agent 活动入口）
├── README.md                     # 顶层说明
└── catalog.yaml                  # agent 元数据索引
```

## 四手编排

| 手 | 职责 | 输入 | 输出 | 下游 |
|---|---|---|---|---|
| Modeler | 问题分析、模型选型、数学建模 | `projects/<项目>/inputs/` 赛题文件 | `output/MODEL_SPEC.md` | Programmer |
| Programmer | 代码实现、测试验证、结果输出 | `MODEL_SPEC.md` | `output/CODE_DELIVERABLES.md` + `code/main.py` + `figures/all_results.json` | Writer |
| Writer | 论文撰写、图表生成、最终校验 | `CODE_DELIVERABLES.md` | `output/PAPER_SPEC.md` + `paper/main.pdf` | （终点） |

数据流：

```
赛题文件 → Modeler → MODEL_SPEC.md → Programmer → CODE_DELIVERABLES.md → Writer → paper/main.pdf
```

## Agent 索引

共 29 个 agent，按手分组。详细契约见 `core/<手>/agents/<name>/SKILL.md`。

### Modeler（8）

| hand | name | utg_layer | stage | 职责 |
|---|---|---|---|---|
| modeler | problem-parser | L1 | 1 | 赛题结构化解析，消除歧义 |
| modeler | type-classifier | L1 | 2 | 题型识别 A/B/C/D/E + 推荐方法方向 |
| modeler | literature-searcher | L2 | 2.5 | 文献检索与证据提取，标注期刊含金量 |
| modeler | method-matcher | L2 | 3 | 方法匹配，从知识库选候选模型 |
| modeler | model-builder | L3 | 4 | 建立数学模型（公式/符号/边界条件） |
| modeler | dag-builder | L3 | 4.5 | 构建模型依赖 DAG + 可视化 |
| modeler | assumption-validator | L4 | 5 | 假设四维评分验证 |
| modeler | spec-auditor | L5+L6 | 6 | MODEL_SPEC 护栏检查 + 哈希审计 |

### Programmer（6）

| hand | name | utg_layer | stage | 职责 |
|---|---|---|---|---|
| programmer | template-selector | L1 | 1 | 根据 MODEL_SPEC 选代码模板 |
| programmer | code-implementer | L2 | 2 | 实现代码，类型制导 |
| programmer | test-runner | L3 | 3 | 单元测试 + 集成测试 |
| programmer | result-verifier | L4 | 4 | 数值验证 + 灵敏度分析 |
| programmer | guardrails-checker | L5 | 5 | 运行时护栏（禁用词/占位符/AI痕迹/权限） |
| programmer | hash-auditor | L6 | 6 | 哈希链 + 错误归因 + 规则迭代 |

### Writer（7）

| hand | name | utg_layer | stage | 职责 |
|---|---|---|---|---|
| writer | structure-planner | L1 | 1 | 论文结构规划 + 字数分配 |
| writer | section-writer | L2 | 2 | 撰写各章节 LaTeX 内容 |
| writer | figure-generator | L2 | 3 | 图表生成与规范命名 |
| writer | reference-curator | L3 | 4 | 参考文献整理 + 引用完整性 |
| writer | consistency-checker | L4 | 5 | 论文-代码数值一致性 |
| writer | guardrails-checker | L5 | 6 | 运行时护栏（禁用词/占位符/AI痕迹） |
| writer | final-validator | L6 | 7 | 最终校验 + 哈希审计 + 渲染 PDF |

### Reviewer（8）

| hand | name | utg_layer | stage | 职责 |
|---|---|---|---|---|
| reviewer | scorer-academic | L4 | 1a | 学术创新性评分 |
| reviewer | scorer-engineering | L4 | 1b | 工程实现质量评分 |
| reviewer | scorer-judge | L4 | 1c | 评委视角评分（竞赛评分标准） |
| reviewer | scorer-reader | L4 | 1d | 读者可读性评分 |
| reviewer | scorer-adversarial | L4 | 1e | 对抗性审查（挑刺/反例） |
| reviewer | weakness-hunter | L4 | 2 | 逐条扫描反模式库挑缺陷 |
| reviewer | revision-planner | L5 | 3 | 把缺陷转成可执行修改清单，支持按子问局部回修 |
| reviewer | revision-executor | L6 | 4 | 按修改清单执行修改，验收通过后产出 execution_report.json |

## env 配置入口

环境变量统一由 `core/env/config.yaml` 提供、`core/env/loader.py` 加载。详细说明见 `core/env/README.md`。

| 配置文件 / 加载器 | 路径 | 作用 |
|---|---|---|
| 配置文件 | `core/env/config.yaml` | 五组可调参数（含默认值与中文注释） |
| 加载器 | `core/env/loader.py` | 零外部依赖，提供 `load_config()` / `get(key)` 接口，缺失时回退默认值 |
| 说明文档 | `core/env/README.md` | 五组参数表、修改示例、缺失回退机制 |

五组参数：

| 参数组 | 关键字段 | 默认值 | 主要消费 agent |
|---|---|---|---|
| `paper` | min_pages / min_words / min_figures / min_tables / min_equations / min_references / max_pages / abstract_min_words / abstract_max_words / chars_per_page / page_fill_ratio / pdf_min_bytes / recent_ref_ratio / figure_min_width / table_max_rows_inline / table_longtable_threshold | 25 / 18000 / 6 / 4 / 15 / 10 / 30 / 400 / 600 / 800 / 0.8 / 102400 / 0.6 / 0.85 / 12 / 15 | Writer：structure-planner / final-validator / section-writer / figure-generator / reference-curator |
| `code` | random_seed / multi_run_count / cv_threshold / solver_timeout_small / solver_timeout_medium / solver_timeout_large / max_fix_rounds / sensitivity_range / sensitivity_steps / min_main_py_bytes / min_deliverables_bytes | 42 / 5 / 0.10 / 300 / 600 / 1200 / 3 / 0.20 / 10 / 500 / 1024 | Programmer：code-implementer / test-runner / result-verifier / hash-auditor |
| `modeling` | min_candidate_models / assumption_score_threshold / ambiguity_min_interpretations / multi_start_check | 2 / 6.0 / 2 / true | Modeler：method-matcher / model-builder / assumption-validator / problem-parser |
| `review` | max_rounds / improvement_max_rounds / pass_score / figure_as_subject_max | 4 / 2 / 6 / 3 | Writer：final-validator / guardrails-checker |
| `runtime` | language / template / strict_mode / traceability_min_ratio / numeric_tolerance_rel / numeric_tolerance_abs | zh / cumcm-zh / true / 0.90 / 0.005 / 0.01 | 所有手共享（`*-validator` / `guardrails-checker` 决定是否退回上游修正） |

读取示例：

```python
from env.loader import get
min_pages = get("paper.min_pages")                 # 25
seed      = get("code.random_seed", default=42)    # 42
threshold = get("modeling.assumption_score_threshold", default=6.0)  # 6.0
template  = get("runtime.template")                # "cumcm-zh"
strict    = get("runtime.strict_mode")             # True
```

## UTG 六层防御

UTG（通用可信生成架构）六层防御已从文档机制落地为具体 agent 实体，每层有唯一承载 agent 与 Self-Check 门禁。

| UTG 层 | 机制 | 承载 agent（按手） | 拦截目标 |
|---|---|---|---|
| L1 | 形式化规约（结构化输出 + 消除歧义） | Modeler：problem-parser / type-classifier；Programmer：template-selector；Writer：structure-planner | 输入语义歧义、字段缺失、模板路径不存在、阈值缺失 |
| L2 | 工具调用与生成（类型制导 / 结构化生成） | Modeler：literature-searcher / method-matcher；Programmer：code-implementer；Writer：section-writer / figure-generator | 方法选择无候选对比、文献检索无证据、语法/类型错误、LaTeX 编译错误、图表命名不规范 |
| L3 | 过程验证（推导链 / 契约 / 引用闭合） | Modeler：dag-builder / model-builder；Programmer：test-runner；Writer：reference-curator | 推导跳步、模型依赖缺失、代码不可运行、契约不齐、引用捏造 |
| L4 | 异构验证（量化评分 / 跨方法对照） | Modeler：assumption-validator；Programmer：result-verifier；Writer：consistency-checker；Reviewer：scorer-*（5 维）/ weakness-hunter | 假设无量化、数值不稳定、论文-代码数值不一致、评审维度缺失 |
| L5 | 运行时护栏（禁用词 / 占位符 / AI 痕迹 / 权限） | Modeler：spec-auditor；Programmer：guardrails-checker；Writer：guardrails-checker | 禁用词、占位符、AI 痕迹、内部路径、权限越界 |
| L6 | 事后哈希审计（篡改检测 + 错误归因） | Modeler：spec-auditor；Programmer：hash-auditor；Writer：final-validator | 产物篡改、规则违反、schema 不符、PDF 渲染失败 |

## 外部 Skill 集成

Agent 可通过 `external_skills` 字段声明所需的外部 skill。格式如下：

```yaml
external_skills:
  - name: skill-name
    type: python  # python | system | api
    required: true  # 是否必需（false 表示可降级）
    fallback: "降级策略描述"
```

运行时检查：
1. 检查 skill 是否已安装（通过 `install` 命令验证）
2. 如果已安装，使用外部 skill
3. 如果未安装且 `required: true`，报错并停止
4. 如果未安装且 `required: false`，使用 `fallback` 降级策略

## 外部 Skill 降级策略

当外部 skill 未安装时，系统按以下优先级降级：

1. **pdf-parser 未安装**:
   - 优先使用 PyPDF2 解析
   - 如果 PyPDF2 也不可用，要求用户提供文本版本的赛题

2. **latex-compiler 未安装**:
   - 根据 env/runtime.compile_pdf 策略决定：
     - `auto`: 仅交付 .tex 源文件
     - `always`: 报错并停止
     - `never`: 仅交付 .tex 源文件（符合预期）

3. **code-executor 未安装**:
   - 仅进行静态分析（语法检查、类型检查）
   - 不实际执行代码
   - 在 CODE_DELIVERABLES.md 中标注"未实际执行"

## MWORKS Syslab 集成（MATLAB/北太天元交付分支的真实执行后端）

本机已安装 MWORKS Syslab 2026b（国产 MATLAB 兼容，M/Julia 双运行时），用于把
`env/code.target_platform` 的 matlab/beitian 交付分支真正跑起来，而不是只产出 `.m` 文件。

- **环境检测**：`python core/tools/check_matlab_env.py --platform syslab`（`check_matlab_env.py` 已支持 syslab）。
- **安装目录**：`SYSLAB_HOME` 已写入 `~/.syslab/syslab-env.ini`（`C:/Program Files/MWORKS/Syslab 2026b`）。
- **Skills**：MWORKS 官方 Syslab skills（`syslab-environment` / `syslab-matlab-to-julia` / `syslab-testing` 等 9 个 + 顶层总宪法）已拷贝到 `.claude/skills/`，agent 按需 `skill_view` 读取，不要一次性全加载。
- **运行时**：
  - M 命令行：`<SYSLAB_HOME>/Tools/TyMLangDist/mlang.bat`（跑 `.m` 代码）
  - Julia：`C:/Users/Public/TongYuan/julia-1.10.10/bin/julia-ty.bat`（跑 `.jl`，绘图统一用 `TyPlot`）
- **约定**：主线仍为 Python（产出 `all_results.json`）；syslab 仅作交付分支的真实执行，优先 `Ty*` 库，M→Julia 迁移优先调用 MCP 的 `map_matlab_functions_to_julia`。

## 不可违反的规则

以下铁律贯穿四手，由各 agent 的 Self-Check 与 Stage Gates 强制执行：

- **最终必有完整可编译的 `paper/main.tex`（+ `references.bib`）**：TEX 源文件是必交付物。PDF 渲染受 `env` `runtime.compile_pdf` 策略控制：`auto`（默认）时若主机存在 LaTeX 工具链（xelatex/latexmk）则 final-validator 必须编译出可打开的 `paper/main.pdf`（HARD）；无工具链时仅交付 main.tex，PDF 检查降级 WARN；`always` 强制编译；`never` 只交付 TEX。
- **所有数值可追溯到 `figures/all_results.json`**：论文中每个数值必须能回溯到 Programmer 手产出的 `figures/all_results.json`，不允许在论文阶段重新估算或换四舍五入口径（铁律 W1 / P2）。
- **无占位符 / AI 痕迹 / 伪造引用**：L5 护栏全绿（无禁用词、无占位符、无 AI 痕迹、无内部路径），参考文献必须真实存在不可捏造（铁律 W5–W8）。
- **随机种子固定为 42**：所有代码必须含 `np.random.seed(42)` 或等效设置，启发式算法须多次运行（≥5 次）报告均值与标准差（铁律 P1 / P6）。
- **不修改 `.gitignore` / `.git/`**：任何 agent 不得修改版本控制元数据与忽略规则。
- **保留用户已有改动**：对用户已存在的产物文件（`projects/<项目>/` 下的代码、论文、图表）做增量更新，不覆盖用户已确认的改动。
- **schema / 哈希链全绿**：所有结构化输出通过对应 `core/schemas/*.schema.json` 校验，哈希链 `verify_chain()==True`，stage_gate L1–L6 全部放行。

## 修改后必做

任何 agent 产出或修改后，必须执行：

```powershell
py core/tools/validate.py
```

验证产物完整性（schema 校验、哈希链、数值一致性、护栏、stage_gate）。`core/tools/validate.py` 全绿后方可宣告本手交付成功；任一项失败按对应 agent 的 `## Iteration` 回退修正后重跑。
