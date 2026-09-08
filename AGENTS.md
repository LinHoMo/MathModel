# MathModel Harness — AGENTS

面向数学模型构建、验证与模型—论文传输的**可信 Harness**。核心是 V3 认知工作流
运行时（Artifact Registry + Evidence Graph + Research State + Workflow DAG +
验证门禁）；V2 四手 29 agent 流水线保留为**兼容层**（`core/legacy/hands/`）。

> **Source of truth = Artifact Registry + Evidence Graph + Research State。
> Agent / LLM 只是 Executor。**
> 状态真源：`docs/STATUS.md`（机器实测数字 + commit hash，唯一口径）。
> 硬化计划：`docs/architecture/HARDENING_PROGRAM.md`（P0–P6，架构已冻结）。

## 五层目录

| 层 | 位置 | 说明 |
|---|---|---|
| product | `core/` | 引擎本体：runtime / roles / workflows / validators / schemas / evaluation / tools / skills / knowledge / env / templates / adapters |
| legacy | `core/legacy/hands/` | V2 兼容层（Modeler / Programmer / Writer / Reviewer），只读兼容不新增 |
| benchmark | `core/tools/evaluation/` | 评分链 / benchmark / 八项能力指标（语料在仓库外 `MMBENCH_ROOT`） |
| research | `research/` | 研究实验（P13-3D 系列、bench 运行）与其实验专属脚本 |
| instance | `projects/` | 用户运行实例（仅 `new_project.py` 创建） |

## 执行协议（所有 agent runtime 通用）

**每次只推进一步。** 29 个 agent 共约 4500 行指令，不要一次读完再执行。

### V3 模式（默认）

```
1. 读状态    python core/tools/state.py <项目> status
             （V3 workspace：projects/<项目>/state/status.json 是流程状态投影）
2. 看计划    python core/tools/orchestrator.py <项目>          # DAG 干跑 / 波次计划
3. 执行      python core/tools/orchestrator.py <项目> --execute  # RuntimeSession 跑认知管线
             或按 orchestrator 输出的节点，读对应 core/roles/*.yaml 与 core/skills/ 指令执行
4. 对账      python core/tools/state.py <项目> reconcile       # 状态与 Registry/Graph 对账
5. 门禁      python core/tools/validate.py                     # 57 项项目级校验
```

### V2 兼容模式（legacy 五步循环，路径已迁）

```
1. 读状态    python core/tools/state.py <项目> status
2. 读指令    读它指出的那一个 core/legacy/hands/<Hand>/agents/<agent>/SKILL.md
3. 执行      按该 SKILL.md 的 Procedure 做，产物写到它指定的路径
4. 跑门禁    python core/tools/gate.py <项目> <hand> <agent>
5. 推进      PASS → python core/tools/state.py <项目> advance <hand> <agent> --output <产物路径>
             FAIL → 按该 SKILL.md 的 ## Iteration 修正后重跑，最多 3 轮
```

`init` 会扫描 29 个 agent 的主产物自动反推进度；换 session、换模型、上下文被压缩都不影响续跑。

### 为什么必须这样做

- 你不需要记住 29 个步骤的顺序，只需要每次读一次状态。
- 门禁由脚本判定（`gate.py` / `validate.py` / `catalog_check.py`），不是靠 Self-Check
  里的 `[ ]` 打勾。
- 状态可对账（`state.py reconcile`）、运行可重放（`replay.py`）——出错可以定位到人/机
  那一环，而不是从对话里猜。

### 命令速查

| 命令 | 作用 |
|---|---|
| `python core/tools/state.py <项目> init` | 初始化 / 从产物反推进度 |
| `python core/tools/state.py <项目> status` | 显示下一步 |
| `python core/tools/state.py <项目> reconcile` | 状态 ↔ Registry/Graph 对账 |
| `python core/tools/state.py <项目> advance <hand> <agent> --output <路径>` | 登记完成并推进 |
| `python core/tools/orchestrator.py <项目>` | 默认 V3 DAG 干跑（波次并行计划） |
| `python core/tools/orchestrator.py <项目> --execute` | V3 实际执行（RuntimeSession） |
| `python core/tools/orchestrator.py <项目> --legacy` | V2 legacy：一键执行 29 步流水线 |
| `python core/tools/gate.py <项目> <hand> <agent>` | 单步门禁 |
| `python core/tools/validate.py` | 项目级 57 项校验 |
| `python core/tools/catalog_check.py --check` | catalog v5 双视图三方一致性 |
| `python core/tools/replay.py <项目> [<run_id> [diff <run_id>]]` | 运行重放 / 差异归因 |
| `python core/tools/knowledge.py recommend --types <题型>` | V3 方法卡检索 |
| `python core/tools/score_compute.py <项目>` | 自动化 5 维评分卡 |
| `python core/tools/new_project.py <项目名> --competition cumcm --problem <文件>` | 新项目脚手架 |
| `python core/tools/diagram_gen.py flowchart --nodes "A,B" --edges "A->B" -o fig.svg` | 科学图表生成（需 matplotlib） |
| `python core/tools/scholar_fetch.py bibtex <关键词>` | 学术文献检索 + BibTeX |

> Windows 本机：默认 `py`（3.14/3.13）安装损坏，统一用 `py -3.12 ...`。
> 其余机器 `python` / `python3` 均可。

## Agent 索引

legacy 兼容层四手共 29 个 agent，**结构单一真源是 `catalog.yaml`**（hands 节路径 +
UTG 层映射；`catalog_check.py --check` 强制三方一致），指令文件位于
`core/legacy/hands/<Hand>/agents/<name>/SKILL.md`。

| 手 | agents | 数量 |
|---|---|---|
| modeler | problem-parser, type-classifier, literature-searcher, method-matcher, model-builder, dag-builder, assumption-validator, spec-auditor | 8 |
| programmer | template-selector, code-implementer, test-runner, result-verifier, guardrails-checker, hash-auditor | 6 |
| writer | structure-planner, section-writer, figure-generator, reference-curator, consistency-checker, guardrails-checker, final-validator | 7 |
| reviewer | scorer-academic, scorer-engineering, scorer-judge, scorer-reader, scorer-adversarial, weakness-hunter, revision-planner, revision-executor | 8 |

> V3 视图下 agent 已重组为 5 Role（analyst / modeler / experimenter / critic / writer）
> 驱动的 DAG 节点（见 `catalog/v3.yaml`）；上表仅描述 legacy 兼容层，**agent 数量
> 不再作为架构质量指标**。

## env 配置入口

所有阈值集中在 `core/env/config.yaml`，由零依赖的 `core/env/loader.py` 注入：

| 参数组 | 关键字段 | 主要消费方 |
|---|---|---|
| `paper` | min_pages 17 / min_words 13000 / min_figures 6 / min_tables 4 / min_equations 15 / min_references 10 | Writer |
| `code` | random_seed 42 / multi_run_count 5 / cv_threshold 0.10 / max_fix_rounds 3 / sensitivity_range 0.20 | Programmer |
| `modeling` | min_candidate_models 2 / assumption_score_threshold 6.0 / ambiguity_min_interpretations 2 | Modeler |
| `review` | max_rounds 4 / pass_score 6 / figure_as_subject_max 3 | Writer / Reviewer |
| `runtime` | language zh / template cumcm-zh / strict_mode true / traceability_min_ratio 0.90 | 所有手共享 |

```python
from env.loader import get
min_pages = get("paper.min_pages")          # 17（软目标；国赛官方硬上限 20 页）
threshold = get("modeling.assumption_score_threshold", default=6.0)
```

## 不可违反的规则

以下铁律贯穿全部模式，由 L1–L6 门禁与 `validate.py` 强制执行：

- **最终必有完整可编译的 `paper/main.tex`（+ `references.bib`）**：TEX 是必交付物；PDF
  渲染受 `env` `runtime.compile_pdf` 策略控制（`auto`/`always`/`never`）。
- **所有数值可追溯到已验证的 Result Artifact**：论文数值必须解析到 `validated` 状态的
  Artifact（legacy 载体为 `figures/all_results.json`），不允许论文阶段重新估算。
- **无占位符 / AI 痕迹 / 伪造引用**：L5 护栏全绿，参考文献必须真实存在。
- **随机种子固定为 42**：多种子运行 ≥5 次，报告均值与标准差。
- **不修改 `.gitignore` / `.git/`**：任何 agent 不得修改版本控制元数据与忽略规则。
- **保留用户已有改动**：对用户已确认的产物做增量更新，不覆盖。
- **schema / 哈希链全绿**：结构化输出通过对应 schema 校验，`hash_chain.verify_chain()==True`。
- **状态单一真源**：status.json 是流程状态投影（由事件重建），禁止多份状态文件并存；
  改动后必须 `state.py reconcile` 通过。

### 方向锁定：Modeling Knowledge 定位（2026-09-08 冻结）

方法卡 = Constraint / Prior / Validation（约束/先验/验证），不是答案库。
- LLM = Model Generator（自由建模，不是方法卡执行器）
- Modeling Knowledge = Constraint / Prior（提供 requirements/risks/validation，不指定"必须用 X"）
- Evidence = Adjudication（实验证据决定模型是否成立）

治理原则：
- Knowledge coverage must constrain evaluation, not constrain creativity
- Research-layer calibration ≠ Agent capability intervention
- 多解模型原则：benchmark 用 allowed_model_families，不用 core_methods/gold method
- Tier 0-3 核心覆盖：不追求全方法覆盖

详见：docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md

## 修改后必做

```powershell
py -3.12 core/tools/validate.py                         # 57 项校验（全绿方可宣告交付）
py -3.12 core/tools/catalog_check.py --check            # 双视图一致
py -3.12 -m pytest tests -q                             # 758 passed / 11 skipped（基线）
```

任一项失败按对应 `## Iteration` 回退修正后重跑，不向下游推进。

## 其他运行环境

- **MWORKS Syslab**：MATLAB/北太天元交付分支的真实执行后端（`check_matlab_env.py --platform syslab`），
  主线仍为 Python。
- **Docker**：仓库提供 `Dockerfile` / `docker-compose.yml`。