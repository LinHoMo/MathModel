# MathModelSkills

基于 UTG（通用可信生成架构）的数学建模技能库。四手分工、29 个 agent 串联，把一道赛题变成一篇可追溯、可复现、无 AI 痕迹的 LaTeX 论文。

**当前版本**：2.0.0 ｜ **技术选型**：LaTeX（单一主线，竞赛差异用 template pack 表达）

---

## 它解决什么问题

数学建模论文的失败，很少是因为"缺少一个更聪明的回答"。更常见的是：

- 模型换了，摘要没更新；第二问重新求解后，第三问还在引用旧结果
- 论文里的数字没有任何脚本真正产出
- 关键假设只存在于聊天记录里，上下文一断就没了
- 提交前才发现页数、匿名或 AI 使用披露不符合要求

本项目的应对方式不是写一个更大的 Prompt，而是**把这些隐含依赖显式化**：四手之间用契约文件传递，每个 agent 的产物落在固定路径，每道门禁由脚本判定。

---

## 架构

```
赛题文件 → Modeler → MODEL_SPEC.md → Programmer → CODE_DELIVERABLES.md → Writer → paper/main.pdf
```

| 手 | 职责 | Agent 数 | 输出契约 |
|---|---|---|---|
| Modeler | 问题分析、模型选型、数学建模 | 8 | `MODEL_SPEC.md` |
| Programmer | 代码实现、测试验证、结果输出 | 6 | `CODE_DELIVERABLES.md` + `figures/all_results.json` |
| Writer | 论文撰写、图表生成、最终校验 | 7 | `PAPER_SPEC.md` + `paper/main.pdf` |
| Reviewer | 评审：打分、挑缺陷、出修改清单、执行修改 | 8 | `work/revision_plan.json` |

### UTG 六层防御

| 层 | 机制 | Modeler | Programmer | Writer | Reviewer |
|---|---|---|---|---|---|
| L1 | 形式化规约 | problem-parser / type-classifier | template-selector | structure-planner | — |
| L2 | 工具调用与生成 | literature-searcher / method-matcher | code-implementer | section-writer / figure-generator | — |
| L3 | 过程验证 | model-builder / dag-builder | test-runner | reference-curator | — |
| L4 | 异构验证 | assumption-validator | result-verifier | consistency-checker | scorer-*（5 维）/ weakness-hunter |
| L5 | 运行时护栏 | spec-auditor | guardrails-checker | guardrails-checker | revision-planner |
| L6 | 事后哈希审计 | spec-auditor | hash-auditor | final-validator | revision-executor |

铁律共 35 条（M1–M9 / P1–P12 / W1–W14），分布在各 agent 的 Self-Check 中执行。

### env 配置层

所有阈值集中在 `core/env/config.yaml`，由零依赖的 `core/env/loader.py` 注入，agent 不硬编码：

| 组 | 关键参数 |
|---|---|
| `paper` | min_pages 17 / min_words 13000 / min_figures 6 / min_tables 4 / min_equations 15 / min_references 10 |
| `code` | random_seed 42 / multi_run_count 5 / cv_threshold 0.10 / max_fix_rounds 3 / sensitivity_range 0.20 |
| `modeling` | min_candidate_models 2 / assumption_score_threshold 6.0 / ambiguity_min_interpretations 2 |
| `review` | max_rounds 4 / pass_score 6 / figure_as_subject_max 3 |
| `runtime` | language zh / template cumcm-zh / strict_mode true / traceability_min_ratio 0.90 |
| `checkpoint` | enabled false / path / save_interval |

```python
from env.loader import get
min_pages = get("paper.min_pages")          # 17（软目标；国赛官方硬上限 20 页）
threshold = get("modeling.assumption_score_threshold", default=6.0)
```

---

## 快速开始

```bash
# 1. 把赛题放入项目目录
mkdir -p projects/my-problem/inputs
#   将 PDF / Word / TXT 赛题放进 inputs/

# 2. 按 catalog.yaml 的 stage 顺序执行三个 bundle
#    Modeler  bundle → output/MODEL_SPEC.md
#    Programmer bundle → output/CODE_DELIVERABLES.md
#    Writer   bundle → output/PAPER_SPEC.md + paper/main.pdf

# 3. 验证产物完整性
python core/tools/validate.py              # 项目级：57 项检查
python core/tools/validate_project.py projects/my-problem   # 单项目级
```

每个 agent 的详细契约见 `core/<Hand>/agents/<name>/SKILL.md`，手级编排见 `core/<Hand>/SKILL.md`。

---

## 目录结构

```
MathModelSkills/
├── core/                            # 引擎（唯一可复用资产）
│   ├── Modeler/ Programmer/ Writer/ Reviewer/   # 四手
│   │   ├── SKILL.md                 # 手级编排器
│   │   ├── agents/<name>/SKILL.md   # 29 个 UTG agent
│   │   ├── knowledge/               # 手私有知识库
│   │   ├── laws/rules.md            # 铁律
│   │   └── templates/               # 契约模板
│   ├── knowledge/                   # 共享知识库
│   │   ├── methodology/             # 50 个方法论文档 + 选型决策树 + INDEX
│   │   ├── paper-cases/             # 论文案例拆解（117 篇获奖论文）
│   │   ├── problems/                # 赛题索引（CUMCM 2015–2025 + MCM/ICM）
│   │   ├── data-sources/            # 权威公开数据源目录
│   │   ├── review/                  # 评分细则与评委洞察
│   │   ├── pitfalls/ _negative/     # 反模式与失败案例库
│   │   └── validation/              # 20 个验证模块
│   ├── env/                         # 配置层（config.yaml + loader.py）
│   ├── schemas/                     # 结构化输出 Schema
│   └── tools/                       # 工具脚本（state / gate / validate 等）
├── projects/                        # 项目实例
│   └── （参考样例归档于 archives/cumcm2024a；库模式 projects/ 为空，无活跃实例）
├── docs/                            # 架构与状态文档
├── tests/                           # unit / integration / e2e
├── AGENTS.md                        # 唯一权威入口
├── catalog.yaml                     # agent 元数据索引
└── install.sh / install.ps1         # 全局安装脚本（可选）
```

---

## 当前状态（2026-09-04）

库模式（`projects/` 为空，仅含引擎与配置）下的真实复跑结果：

| 项 | 结果 | 生成命令 |
|---|---|---|
| 库模式全链路检查 | **57 通过 / 0 失败 / 0 警告** | `python core/tools/validate.py` |
| 单元测试 | **228 passed / 16 failed** | `python -m pytest tests -q`（需先安装 pytest） |
| 单项目门禁 | 按活跃实例判定（HARD 门禁） | `python core/tools/gate.py <项目> all` |
| 单项目校验 | 按活跃实例判定 | `python core/tools/validate_project.py --project <项目>` |

说明：
- `pytest` 的 16 个失败均为**既有 / 环境性**问题，非本次重构引入：`test_state.py` ×2（`state.py` 既有 `AttributeError`）、`test_aggregate_scores.py` ×5（评分聚合既有断言）、`e2e`/`integration` ×8（依赖活跃项目实例，库模式无实例，参考样例归档于 `archives/cumcm2024a`）。本次重构修复了其中因旧基线失效的 `test_env.py::test_get_paper_min_pages`（已对齐 17 / 13000）。
- `gate.py` / `validate_project.py` 为**单项目级**检查，须在活跃项目实例上运行；归档参考样例 `archives/cumcm2024a` 为部分样例（5 页 / 6116 字），不保证全绿。
- 参数已对齐 2025 国赛官方基线：正文硬上限 20 页、软目标 17 页、字数软下限 13000；唯一真源见 `core/env/schema.yaml` 与 `core/env/profiles/cumcm-2025.yaml`。

### 门禁分级

- **HARD**：失败即阻塞交付
- **WARN**：文献年份 / 表格行数 / 段落句式 / 摘要字数——只记警告，不阻塞

### 两处口径说明（易踩坑）

1. **论文字数**：按"跳过导言区 → 去注释 → 去数学环境 → 去 LaTeX 命令 → 统计中文字符 + 正文英文单词"计算。直接统计 LaTeX 源码会把 `\theta`、`\begin`、`\cite` 等命令计入，实测虚高约 2000 字，足以让不达标的论文"险过"门禁。
2. **文献年份**：近 3 年以**赛题年份**为基准（从 `projects/<项目名>` 推断），不是当前年份。同时检测"未来文献"（年份晚于赛题年份），命中即判 HARD——这是引用造假的信号。

---

## 项目定位

- **不做自有品牌 CLI**。目标是任意通用 agent（WorkBuddy / Claude Code / Trae / opencode / Cursor 等）进入本目录即可执行，通过「入口统一 + 状态外置 + 门禁脚本化」实现，而非写一个 orchestrator 接管推理。
- **引擎与实例分离**：`core/` 是唯一可复用引擎，`projects/<项目>/` 是引擎在校验下跑出来的实例；改引擎不动实例，换实例不伤引擎。
- **赛道瓶颈不在流程编排**，而在内容质量与合规安全。
- **最高优先级缺口是 AI 使用披露**（CUMCM 需支撑材料、MCM 需 AI use report），属合规范畴而非体验问题。

## 设计原则

1. **角色独立**：四手各有知识库与铁律，通过契约文件协作
2. **契约协作**：`MODEL_SPEC.md` / `CODE_DELIVERABLES.md` / `PAPER_SPEC.md` 是唯一接口
3. **可追溯**：所有数值可追溯到 `figures/all_results.json`
4. **可验证**：阈值集中在 env，判定交给脚本，不靠人工自觉
5. **可回退**：每手内部支持迭代修正，不向下游推进未通过的产物

## 许可与边界

本仓库是协作与质量控制工具，不是自动获奖系统。AI 生成的公式、代码、事实和引用必须人工复核；竞赛规则（页数、匿名、AI 使用披露）变化频繁，提交前须以当届官方通知为准。

---

## 命令速查（P0–P2 补充）

### 引用检查

```
python core/tools/citation_check.py project <项目路径> [--json]
python core/tools/citation_check.py bib <references.bib> [--json]
```

### 国赛复盘基准

```
python core/tools/benchmark.py bench list [--json]
python core/tools/benchmark.py bench run --rubric <path>
python core/tools/benchmark.py bench score --rubric <f> --response <f> [--json]
python core/tools/benchmark.py bench report --rubric <f> --response <f>
python core/tools/bench_mmbench.py list [--json]
python core/tools/bench_mmbench.py export --year <Y> --topic <A> [--out <dir>]
python core/tools/bench_mmbench.py path
```
