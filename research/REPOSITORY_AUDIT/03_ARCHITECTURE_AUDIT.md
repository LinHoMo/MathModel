# 03 — Architecture Audit（架构深度审计）

> 审计日期：2026-09-08
> 审计范围：MathModel 仓库全量架构（v3.1.0 冻结后状态）
> 审计员：Architecture & Test System Auditor
> 方法：只读观察（Phase A OBSERVE）+ Grep 依赖链 + pytest 收集 + 目录指纹
> 约束：本次审计不修改任何仓库文件（本报告除外）

---

## 0. 执行摘要

| 维度 | 结论 | 严重度 |
|---|---|---|
| 仓库定位 | 正在从"Harness"向"大而全的数模 Agent 项目"漂移，核心证据是 `core/knowledge/bench/`（136 文件）与 `core/tools/evaluation/`（8 文件）承载了本应属于 research/ 的基准与评测逻辑 | 中 |
| Research → Core 依赖 | **无直接 import 污染**（`from research` / `import research` 在 core/ 中 0 命中），但存在 3 类间接污染：research 专用工具 shim 混入 core/tools/、MMBench 外部仓库路径硬编码、benchmark 数据驻留 runtime knowledge | 中 |
| Projects/ | 2 个项目状态文件**完全相同**（仅时间戳差异），均为 init 阶段无论文无模型——本质是重复 smoke fixture，不是真实用户运行实例 | 高 |
| 测试体系 | 792 tests（559 unit / 205 integration / 15 regression / 13 e2e），但 ~72 个为纯 fixture-existence（`os.path.exists`），`tests/tests/` 嵌套异常，Security / Failure Recovery / Real Problem Execution 能力覆盖不足 | 中 |
| Core 子系统 | `core/evaluation/` 是空壳（6 文件全为 `__init__.py`），`core/runtime/domain/` 与 `adapters/` 仅含 `__init__.py`，38 个 root-level shim 中 2 个目标缺失（broken） | 中 |
| 冻结架构 | Artifact Registry / Evidence Graph / Research State / Workflow DAG / L1-L6 门禁 / status.json / hash chain 均在位且可测试；Provider boundary 声明存在但 `core/runtime/adapters/` 为空包 | 低 |

**核心判断**：仓库的 V3 运行时内核（runtime + validators + schemas）是干净、稳定、可测试的。污染主要发生在 **knowledge 层与 tools 层的边界模糊**——benchmark 数据、评测脚本、research 专用工具没有彻底从 core/ 剥离到 research/。projects/ 被 fixture 占用，tests/ 存在结构异常与能力盲区。

---

## 1. 目录复杂度审计

### 1.1 核心问题回答

> **«这个仓库是不是正在从 Harness 演变成一个"大而全的数学建模 Agent 项目"？»**

**是，存在明显漂移，但内核尚未被侵蚀。** 证据如下：

- `core/knowledge/` 404 文件中，**136 个（33.7%）属于 `bench/` 子目录**——这是 benchmark 数据（CUMCM rubric 22 份 + e2e 基准案例 114 份），按三层 Profile 应属于 research/ 而非 runtime knowledge。
- `core/tools/evaluation/` 8 个文件承载了完整的评分链（`score_compute.py` / `aggregate_scores.py` / `e2e_metrics.py` / `benchmark.py` / `bench_mmbench.py`），而 `core/evaluation/` 包本身只有 `__init__.py`——评测逻辑的"物理位置"与"逻辑归属"分裂。
- `research/` 已膨胀至 701 文件 / 15 个子目录，其中 P13-3D 系列（443 文件）、P14（134 文件）是完整的研究实验线，包含独立的 `schemas/` / `scripts/` / `state/`——research 正在形成自己的"迷你 runtime"。
- `docs/architecture/` 45+ 文件中，P13/P14 研究报告（`P13_3C_REPORT.md` / `P13_3D_REPORT.md` / `P13_3D_R2_PREREG.md` 等 12 份）与架构契约文档（`V3.1_ARCHITECTURE.md` / `RUNTIME_CONTRACTS.md` / `STATE_TRUTH.md`）混放——架构文档目录正在被研究产出物占用。

### 1.2 三层 Profile 职责对照

| 目录 | 当前实际职责 | 应有职责（Profile） | 判定 |
|---|---|---|---|
| `core/runtime/` | Artifact Registry / Evidence Graph / State / Workflow DAG / Execution / Writing / Modeling / Knowledge runtime / Decisions / Synthesis / Legacy 适配 | **Runtime**：execution, state, workflow, tools, skills loading, verification, provider boundary, artifact/evidence mechanics | ✅ 基本合规；`writing/`（24 文件）与 `modeling/`（8 文件）偏向 Agent Brain，但作为 runtime 可插拔层可接受 |
| `core/validators/` | L1-L6 验证模块（21 modules）+ evidence gate + quality evaluators | **Runtime**：verification / guardrails | ✅ 合规 |
| `core/schemas/` | 16 个 V2 schema + v3/ 子树 12 个 schema | **Runtime**：contracts | ✅ 合规 |
| `core/workflows/` | base.yaml + competition/（cumcm, mcm）+ stages/（5 阶段） | **Runtime + Competition Profile**：workflow DAG 定义 | ✅ 合规；competition/ 是 Competition Profile 的正确位置 |
| `core/roles/` | 5 个 Role yaml（analyst/modeler/experimenter/critic/writer） | **Runtime**：capability composition | ✅ 合规 |
| `core/skills/` | 仅 critics/ 子目录（4 个 SKILL.md） | **Runtime**：capability skills | ⚠️ 不完整——V3 skill 加载机制仅有 critic skill，其余能力仍依赖 legacy/hands/ 的 29 agent SKILL.md |
| `core/knowledge/` | 404 文件：methodology(54) / paper-cases(117) / **bench(136)** / playbooks(13) / methods(16) / failures(10) / patterns(6) / validation(21) / 其他 | **Runtime**：决策知识（method cards / failures / patterns）；**Benchmark 不应在此** | ❌ `bench/`（136 文件）越界——CUMCM rubric + e2e 基准案例属于 benchmark/research，不是 runtime 决策知识 |
| `core/evaluation/` | 6 文件，全为 `__init__.py`（含 pycache） | **Research Profile**：scoring / benchmark / regression | ❌ 空壳——真实评测逻辑在 `core/tools/evaluation/`，包迁移未完成 |
| `core/tools/` | 170 文件：38 个 root-level shim + 6 子目录（runtime/validation/evaluation/knowledge/devtools/rendering） | **Runtime**：CLI 入口 / 工具脚本 | ⚠️ `evaluation/` 子目录（8 文件）承载了本属 research 的 benchmark 与评分逻辑；`run_p13_3d.py` 是 research 专用工具混入 |
| `core/legacy/` | 283 文件：四手 29 agent（Modeler 77 / Programmer 72 / Writer 108 / Reviewer 25） | **Legacy 兼容层**：只读，不新增 | ✅ 合规（确认只读） |
| `core/env/` | config.yaml + loader.py + schema.yaml + profiles/（9 个竞赛 profile） | **Runtime + Competition Profile**：配置注入 | ✅ 合规 |
| `core/templates/` | latex 模板 + figures 模板（39 文件） | **Competition Profile**：论文模板 | ✅ 合规 |
| `research/` | 701 文件：P13-3D 系列 / P14 / P15 / bench-* 系列 / RC-SMOKE / REPOSITORY_AUDIT | **Research Profile**：research modeling, experiment design, evidence, claim adjudication, reproducibility | ✅ 位置正确；但内部已形成独立 schemas/scripts/state，需警惕"research 内 runtime 化" |
| `projects/` | 25 文件：p151-2024a / rcs1-2024a / README.md | **Runtime 实例**：用户运行实例 | ❌ 当前 2 个项目均为 smoke fixture（详见 §3） |
| `tests/` | 189 文件：unit(126) / integration(36) / e2e(6) / regression(4) / compat(2) / fixtures(8) / tests(1) | **Runtime**：测试套件 | ⚠️ `tests/tests/` 嵌套异常；能力覆盖有盲区（详见 §4） |
| `examples/` | 1 文件：problems/cumcm2024A.txt | **Competition Profile**：示例赛题 | ⚠️ 过于单薄，且与 projects/ 中输入文件重复 |
| `docs/` | 57 文件：architecture/(45+) / decisions/ / integration/ + 根级文档 | **全部 Profile**：架构与状态文档 | ⚠️ architecture/ 被 P13/P14 研究报告占用（12 份），架构契约与研究产出混放 |
| `catalog/` | 3 文件：v3.yaml / external_skills.yaml / protocol_tools.yaml | **Runtime**：双视图注册表 | ✅ 合规 |
| `adapters/` | 1 文件：openai.yaml | **Runtime**：provider 适配 | ⚠️ 仅一个 provider，且与 `core/runtime/adapters/`（空包）职责重叠 |
| `archives/` | 10 文件：cumcm2024anew（历史样例）+ README | **归档**：只读历史样例 | ✅ 合规 |

### 1.3 职责重叠与越界汇总

| 重叠/越界 | 涉及目录 | 证据 | 建议方向 |
|---|---|---|---|
| Benchmark 数据驻留 runtime knowledge | `core/knowledge/bench/` ↔ `research/` | 136 文件：cumcm rubric 22 + e2e 案例 114 | 迁移至 `research/benchmark/` 或仓库外 `MMBENCH_ROOT`；runtime 仅保留 method cards / failures / patterns |
| 评测逻辑物理位置分裂 | `core/evaluation/`（空壳）↔ `core/tools/evaluation/`（8 文件） | `core/evaluation/__init__.py` 自述"P4 阶段评分实现仍留在 core/tools/"；`core/evaluation/benchmark/__init__.py` 是 lazy loader | 完成迁移或正式宣布 core/tools/evaluation/ 为永久位置，删除空壳包 |
| Research 专用工具混入 core/tools | `core/tools/run_p13_3d.py` | 文件名为 P13 研究实验专用，且目标 `core/tools/evaluation/run_p13_3d.py` 不存在（broken shim） | 删除或迁移至 `research/P13-3D/scripts/` |
| MMBench 外部仓库路径硬编码 | `core/tools/evaluation/benchmark.py` + `bench_mmbench.py` | `_DEFAULT_MMBENCH = ROOT.parent / "_mm_analysis" / "LLM-MM-Agent" / "MMBench"` | 这是 benchmark 专用外部依赖，应随 benchmark 逻辑一起迁出 core/ |
| Provider 适配职责分裂 | `adapters/openai.yaml` ↔ `core/runtime/adapters/`（空包） | 根目录 adapters/ 有 openai.yaml；core/runtime/adapters/ 仅 `__init__.py` | 统一到一处；若 core/runtime/adapters/ 是设计位置，则将 openai.yaml 迁入 |
| 架构文档被研究报告占用 | `docs/architecture/P13_*.md`（12 份） | P13_3C_REPORT / P13_3D_REPORT / P13_3D_R2_PREREG 等是研究实验产出，不是架构契约 | 迁移至 `research/P13-3D/docs/` 或 `docs/research/`；architecture/ 只保留契约文档 |
| 示例赛题与项目输入重复 | `examples/problems/cumcm2024A.txt` ↔ `projects/p151-2024a/inputs/cumcm2024A.txt` | 同一文件两处存在 | examples/ 保留为模板源，projects/ 中的是运行时拷贝——可接受，但应在 README 说明 |

---

## 2. Research 污染 Runtime 检查（最重要）

### 2.1 直接 Import 污染：**零命中**

```
Grep: core/ 中 `from research` 或 `import research`
结果：0 matches
```

core/ 中没有任何 Python 文件直接 import research 包。这是好消息——**运行时内核没有被研究代码直接侵入**。

### 2.2 间接污染：3 类问题

#### 类别 A：Research 专用工具混入 core/tools/

| 文件 | 证据 | 判定 |
|---|---|---|
| `core/tools/run_p13_3d.py` | 文件名直接包含研究实验编号 P13-3D；内容为 shim，指向 `core/tools/evaluation/run_p13_3d.py` | **Broken + 越界**：目标文件不存在（`Test-Path` 返回 False），且 P13-3D 是 research/ 中的实验线，不应有 core/tools/ 入口 |

验证：
```powershell
PS> Test-Path core/tools/evaluation/run_p13_3d.py
False
```

#### 类别 B：MMBench 外部仓库路径硬编码

| 文件 | 行号 | 硬编码内容 |
|---|---|---|
| `core/tools/evaluation/benchmark.py` | 352-353 | `_DEFAULT_MMBENCH = ROOT.parent / "_mm_analysis" / "LLM-MM-Agent" / "MMBench"` |
| `core/tools/evaluation/bench_mmbench.py` | 33-34 | 同上 |

这是 benchmark 专用的外部仓库依赖，硬编码了仓库外的相对路径 `../_mm_analysis/LLM-MM-Agent/MMBench`。虽然有 `MMBENCH_ROOT` 环境变量覆盖，但默认路径假设了特定的本地目录布局——这属于 **benchmark-specific exception entering core**。

#### 类别 C：Benchmark 数据驻留 runtime knowledge

`core/knowledge/bench/` 136 文件：
- `bench/cumcm/`：22 份 CUMCM 评分细则 rubric（`rubric_2021a.json` … `rubric_2025d.json`）
- `bench/e2e/`：114 文件，包含：
  - 12 份 `mc_YYYYx.json`（modeler candidate 基准案例，2019-2025）
  - `gt_2023C.json`（golden truth）
  - `case_2000C_global.json` / `case_2023C_global.json`（全局基准案例）
  - `question_profiles.json`（含 "从 MMBench 未触碰题中按 regime 配额挑选" 等 benchmark 运行逻辑）
  - `mma_modeler_prompt.md`（benchmark 专用 prompt）

这些文件的内容性质是 **benchmark 数据集与运行配置**，不是 runtime 决策知识（method cards / failures / patterns）。按三层 Profile，benchmark 原则上属于 research/。

### 2.3 P13/P14/P15 引用在 core/ 中的分布

Grep `P13|P14|P15|p13|p14|p15` 在 core/ 中命中 25 个文件，逐一分析：

| 文件 | 引用性质 | 是否污染 |
|---|---|---|
| `core/runtime/execution/handlers.py` L53-58 | P13-1 已批准例外（`features_for()` 函数），注释引用 `P13_1_REPORT.md` | ❌ 不污染——THREE_LAYER_ARCHITECTURE.md §3 已登记批准 |
| `core/runtime/knowledge/retriever.py` L8-10, L187-188 | P13-2 已批准例外（类型命中权重 +3→+6），注释引用 `P13_2_REPORT.md` | ❌ 不污染——已登记批准 |
| `core/tools/validation/validate.py` L90-91 | 注释说明"研究实验（P13-3D 系列 / bench 运行）自 Hardening P4 起迁至 research/" | ❌ 不污染——是迁移说明，不是硬编码路径 |
| `core/tools/run_p13_3d.py` | 文件名即 P13，broken shim | ✅ **污染**——research 专用工具 |
| `core/tools/evaluation/e2e_metrics.py` | P13.0 基准指标定义，注释引用 `CAPABILITY_ROADMAP_P13_P17.md` | ⚠️ 边界——e2e 指标是 capability baseline 工具，逻辑上属 research 评测，但已被 runtime 消费（`orchestrator.py` 生态） |
| `core/tools/evaluation/benchmark.py` | MMBench 路径 + benchmark 运行逻辑 | ✅ **污染**——benchmark 专用 |
| `core/knowledge/bench/e2e/*.json`（17 文件） | 基准案例数据，部分 note 字段含 "P13-3C 预注册 rubric" | ✅ **污染**——benchmark 数据 |
| `core/knowledge/pitfalls/model_construction_checklist.md` | 文档中提及 P13 | ❌ 不污染——知识文档引用 |
| `core/schemas/model_artifact.schema.json` / `model_paper_map.schema.json` | schema 中可能含 P 系列引用 | ❌ 不污染——需确认是数据字段还是硬编码 |

### 2.4 core/evaluation/ 的 6 个文件分析

`core/evaluation/` 递归文件列表：
```
core/evaluation/__init__.py
core/evaluation/benchmark/__init__.py
core/evaluation/benchmark/__pycache__/__init__.cpython-312.pyc
core/evaluation/scoring/__init__.py
core/evaluation/scoring/__pycache__/__init__.cpython-312.pyc
core/evaluation/__pycache__/__init__.cpython-312.pyc
```

**实际 Python 源文件仅 3 个，全为 `__init__.py`。** 其中：
- `core/evaluation/__init__.py` 自述："P4 阶段评分实现仍留在 core/tools（零依赖脚本，state/gate/编排器消费），本包提供稳定的 V3 import 面 `evaluation.scoring`；P5 目录重构时实现迁入本包，core/tools/ 退化为 CLI 转发，本 import 面保持不变。"
- `core/evaluation/benchmark/__init__.py` 是 lazy loader，从 `core/tools/` 动态加载 `benchmark` 和 `bench_mmbench` 模块。

**判定**：这是一个**未完成的迁移**。P4 计划将评测逻辑迁入 `core/evaluation/`，但实际代码仍在 `core/tools/evaluation/`。`core/evaluation/` 作为空壳包存在，造成了"逻辑归属"与"物理位置"的分裂。这本身不是 research→core 污染，但它是 **core 内部职责不清** 的表现。

### 2.5 目标方向验证

> **目标：core ↑ stable contracts；research ↓ consume core。而不是 core → research。**

当前状态：
- ✅ research/ 中的实验（P13-3D / P14 / P15）通过 `sys.path.insert(0, _CORE)` 消费 core/runtime（见 `e2e_metrics.py` L32-40 的模式，research 脚本同理）——方向正确。
- ✅ core/ 无直接 import research——方向正确。
- ⚠️ 但 core/tools/evaluation/ 中的 benchmark 与评分逻辑本质上是 research 工具，被 core/ 的编排器生态消费——这是"core 消费 research 工具"的灰色地带。
- ❌ `core/knowledge/bench/` 的 benchmark 数据是 research 资产驻留 core。

**结论**：依赖方向基本正确（research consumes core），但**资产归属**有 3 处越界（run_p13_3d shim、MMBench 硬编码、bench/ 数据）。

---

## 3. Projects 垃圾场检查

### 3.1 逐项目分析

#### 项目 1：`projects/p151-2024a/`

| 检查项 | 结果 |
|---|---|
| 子目录 | artifacts/ code/ deliverables/ figures/ inputs/ output/ paper/ state/ work/ _scratch/ |
| 输入文件 | `inputs/cumcm2024A.txt` + `inputs/external/` |
| state/status.json | schema_version 3，problem status = **pending**，Q001 status = validated（models 为空，experiments=[E001]，claims=[C001]），models.status = pending（candidates=[M001], selected=[]），paper.status = pending（sections_written=0），run.phase = **init** |
| state/registry.json | 31981 字节（较大，含预注册 artifact） |
| paper/ | **空**（无 main.tex，无 PDF） |
| code/ | 存在（未深入检查内容） |
| 时间戳 | 2026-09-08 08:35（全部子目录同一时间戳——脚手架创建时间） |

**判定**：**Smoke test fixture / Golden fixture（初始化态）**。状态停留在 init 阶段，问题未解析（pending），无论文，无选中模型。registry.json 较大说明有预注册的 artifact 结构。全部子目录时间戳一致说明是 `new_project.py` 脚手架创建后未实际运行。

#### 项目 2：`projects/rcs1-2024a/`

| 检查项 | 结果 |
|---|---|
| 子目录 | 与 p151 完全相同（artifacts/ code/ deliverables/ figures/ inputs/ output/ paper/ state/ work/ _scratch/） |
| 输入文件 | `inputs/problem_cumcm2024A.txt` + `inputs/external/`（**同一道题，文件名不同**） |
| state/status.json | 与 p151 **内容完全相同**（仅 `last_updated` / `started_at` / `updated_at` 时间戳差 1 小时 7 分钟） |
| state/registry.json | 31981 字节——**与 p151 完全相同大小** |
| state/evidence_graph.json | 1733 字节——**与 p151 完全相同大小** |
| state/decision_log.json | 1671 字节——**与 p151 完全相同大小** |
| state/quality_report.json | 1883 字节——**与 p151 完全相同大小** |
| state/engine_progress.json | 528 字节——**与 p151 完全相同大小** |
| paper/ | **空** |

**判定**：**Smoke test fixture（p151 的副本）**。7 个 state 文件大小完全一致，status.json 内容完全一致（仅时间戳不同），输入是同一道 CUMCM 2024A 题。这是 RC-SMOKE（Release Candidate Smoke Test）的运行实例，从 `research/RC-SMOKE/` 的 RUNBOOK 可以印证其用途。

### 3.2 关键发现：状态文件完全相同

```
p151-2024a/state/:
  registry.json        31981 bytes
  evidence_graph.json   1733 bytes
  decision_log.json     1671 bytes
  quality_report.json   1883 bytes
  engine_progress.json   528 bytes
  status.json           1423 bytes

rcs1-2024a/state/:
  registry.json        31981 bytes  ← 相同
  evidence_graph.json   1733 bytes  ← 相同
  decision_log.json     1671 bytes  ← 相同
  quality_report.json   1883 bytes  ← 相同
  engine_progress.json   528 bytes  ← 相同
  status.json           1423 bytes  ← 相同（内容仅时间戳差异）
```

这不是巧合——两个项目是**同一份 fixture 的拷贝**。

### 3.3 分类与处置建议

| 项目 | 当前分类 | 应分类 | 处置建议 |
|---|---|---|---|
| `p151-2024a/` | Active runtime fixture? | **Smoke test fixture / Golden fixture（init 态）** | 保留为 golden fixture，但应移至 `tests/fixtures/projects/` 或明确标注为 fixture；不应占用 projects/ 的"用户运行实例"语义 |
| `rcs1-2024a/` | Active runtime fixture? | **Smoke test fixture（RC smoke 运行副本）** | 与 p151 重复度 100%（state 文件完全相同），建议删除或归档至 `archives/`；RC smoke 记录已在 `research/RC-SMOKE/` 保留 |

### 3.4 «"projects/" 应该是什么，而不应该是什么»

**应该是**：
- 用户通过 `new_project.py` 创建的**真实运行实例**
- 每个项目有独立的 problem input、独立的 state 演进、独立的 paper 产出
- 项目状态从 init → problem_parsed → modeling → experimenting → evidence → paper → completed 真实推进
- 是引擎在校验下跑出来的结果，不是脚手架的静态拷贝

**不应该是**：
- ❌ Smoke test fixture 的存放地（应在 `tests/fixtures/`）
- ❌ 研究实验的运行实例（应在 `research/`）
- ❌ 同一 fixture 的多份拷贝
- ❌ 永远停留在 init 阶段、无论文产出的"僵尸项目"

**当前问题**：projects/ 中 2 个项目 100% 是 fixture，0 个是真实用户运行实例。这意味着 `validate.py` 的"活跃实例判定"和论文交付门禁实际上没有真实项目可校验——**校验逻辑在空转**。

---

## 4. 测试体系全面审计

### 4.1 测试收集统计

```
py -3.12 -m pytest tests -q --co
→ 792 tests collected in 1.07s
```

按目录分布：

| 目录 | 测试数 | 占比 |
|---|---|---|
| `tests/unit/` | 559 | 70.6% |
| `tests/integration/` | 205 | 25.9% |
| `tests/regression/` | 15 | 1.9% |
| `tests/e2e/` | 13 | 1.6% |
| `tests/compat/` | 0（文件存在但未被收集？） | 0% |
| `tests/` 根级 | 0（`test_tex_to_docx_quick.py` 未被收集？） | 0% |

> 注：STATUS.md 报告 781 passed / 11 skipped = 792 total，与收集数吻合。compat/ 的 `test_runtime_compat.py`（11619 字节）和根级 `test_tex_to_docx_quick.py` 可能被 skip 或未匹配收集模式。

Top 15 测试文件（按测试数）：

| 文件 | 测试数 | 性质 |
|---|---|---|
| `unit/test_artifacts.py` | 37 | Runtime contract（Artifact Registry） |
| `unit/test_evidence_graph.py` | 29 | Runtime contract（Evidence Graph） |
| `unit/test_dag_engine.py` | 24 | Runtime contract（Workflow DAG） |
| `unit/test_state_v3.py` | 24 | Runtime contract（State） |
| `unit/test_method_cards.py` | 23 | Knowledge runtime |
| `unit/test_decision_log.py` | 23 | Runtime contract（Decisions） |
| `integration/test_red_team.py` | 23 | Integration（红队） |
| `integration/test_research_quality.py` | 22 | Integration（质量评估） |
| `unit/test_agents_structure.py` | 19 | **Fixture existence**（legacy 29 agent 结构） |
| `unit/test_openai_manifest.py` | 18 | Provider boundary |
| `unit/test_workflow_compose.py` | 18 | Runtime contract（Workflow compose） |
| `unit/test_competition_intelligence.py` | 17 | Competition profile |
| `integration/test_controlled_expression.py` | 17 | Integration（表达契约） |
| `integration/test_p7_integrity.py` | 17 | Integration（P7 完整性） |
| `integration/test_cross_question_relations.py` | 16 | Integration（跨问题关系） |

### 4.2 测试分类审计

#### A. 真正验证 Runtime Contract 的测试（高价值）

| 能力 | 测试文件 | 测试数 | 判定 |
|---|---|---|---|
| Artifact Registry | `unit/test_artifacts.py` | 37 | ✅ 真正验证 ID / lifecycle / registry 契约 |
| Evidence Graph | `unit/test_evidence_graph.py` | 29 | ✅ 真正验证 14 relation / invalidation / coverage |
| Workflow DAG | `unit/test_dag_engine.py` + `test_workflow_compose.py` + `test_wave_executor.py` | 24+18+9=51 | ✅ 真正验证 DAG 引擎 / 波次调度 / 组合 |
| State | `unit/test_state_v3.py` + `test_state.py` + `test_reconcile.py` | 24+11+9=44 | ✅ 真正验证 state model / reconcile 对账 |
| Decisions | `unit/test_decision_log.py` | 23 | ✅ 真正验证 decision log / invalidation |
| Evidence Gate | `unit/test_evidence_gate.py` | 13 | ✅ 真正验证 evidence gate 准入 |
| Legacy 转换 | `unit/test_legacy_convert.py` | 10 | ✅ 真正验证 V2↔V3 适配器 |
| Runtime Session | `integration/test_runtime_session.py` + `test_state_registry_sync.py` | 9+4=13 | ✅ 真正验证 RuntimeSession 胶水层 |
| Replay / Provenance | `unit/test_run_provenance.py` | 7 | ✅ 真正验证 run record / replay |
| Crash consistency | `unit/test_crash_consistency.py` | 2 | ⚠️ 部分覆盖（仅 2 个测试） |

#### B. Fixture Existence 测试（低价值，仅验证文件存在）

| 测试文件 | 测试数 | 模式 |
|---|---|---|
| `unit/test_modeler.py` | 13 | `assert os.path.exists("core/legacy/hands/Modeler/SKILL.md")` 等 |
| `unit/test_programmer.py` | 14 | 同上（Programmer 手） |
| `unit/test_writer.py` | 15 | 同上（Writer 手） |
| `unit/test_gateway_agents.py` | 11 | 同上（Reviewer 手 + gateway） |
| `unit/test_agents_structure.py` | 19 | 29 agent 名称/数量/UTG 层映射断言 |
| **小计** | **72** | 占全部测试的 9.1% |

这些测试的价值是**防止 legacy 目录被意外删除**，但它们不验证任何 runtime contract。在 V3 架构下，legacy 是只读兼容层，这些测试可以合并为一个 `test_legacy_integrity.py`，减少 72→~10。

#### C. 重复测试

| 重复点 | 涉及文件 | 说明 |
|---|---|---|
| Legacy 四手结构 | test_modeler / test_programmer / test_writer / test_gateway_agents / test_agents_structure | 5 个文件都在验证 legacy 四手的目录结构，高度重叠 |
| State 测试 | test_state.py（11）+ test_state_v3.py（24）+ test_reconcile.py（9） | 三者边界模糊，test_state.py 可能是 V2 遗留，test_state_v3.py 是 V3 新版 |
| Benchmark 测试 | unit/test_benchmark.py（8）+ integration/test_e2e_metrics.py（4） | 都涉及 benchmark/e2e 指标，可能有重叠 |

#### D. Implementation Detail 测试

| 测试文件 | 关注点 | 判定 |
|---|---|---|
| `unit/test_env.py` | env loader 配置注入 | ⚠️ 部分是 implementation detail（loader 内部逻辑），部分是 contract（配置阈值） |
| `unit/test_weight_profiles.py` | 竞赛 profile 权重 | ⚠️ 验证 profile 数据正确性，偏 implementation detail |
| `unit/test_features_for.py` | handlers.features_for() | ⚠️ 验证 P13-1 例外的具体实现，3 个测试偏少 |
| `unit/test_openai_manifest.py` | gen_runtime_manifest | ⚠️ 18 个测试，验证 manifest 生成逻辑，偏 implementation detail 但有 provider boundary 价值 |

#### E. 已无价值的测试

| 测试 | 原因 |
|---|---|
| `tests/tests/fixtures/sample_problem.txt` | 不是测试，是嵌套目录中的 fixture 文件；`tests/tests/` 目录本身是异常结构 |
| `unit/test_modeler.py` 等中的 `test_templates_directory_exists` | 与 test_agents_structure.py 完全重复 |

### 4.3 Test Coverage by Capability 矩阵

| 能力 | 覆盖状态 | 具体测试文件 | 缺口说明 |
|---|---|---|---|
| **Architecture** | ✅ 有测试 | `test_agents_structure.py`(19), `test_roles.py`(11), `test_workflow_compose.py`(18) | 架构结构测试充分，但偏 legacy 结构 |
| **State** | ✅ 有测试 | `test_state_v3.py`(24), `test_state.py`(11), `test_reconcile.py`(9), `test_crash_consistency.py`(2) | 覆盖充分；crash consistency 仅 2 测试偏薄 |
| **Workflow** | ✅ 有测试 | `test_dag_engine.py`(24), `test_wave_executor.py`(9), `test_workflow_compose.py`(18), `integration/test_workflow_execution.py`(6) | 覆盖充分 |
| **Provider boundary** | ⚠️ 部分覆盖 | `test_openai_manifest.py`(18), `test_cloud_sandbox.py`(8) | 仅覆盖 openai manifest 与 cloud sandbox；provider 插拔、多 provider 切换、provider failure 无测试 |
| **Replay** | ⚠️ 部分覆盖 | `test_run_provenance.py`(7) | 仅 7 个测试；replay verify/diff、并发契约（P3）无专门测试 |
| **Determinism** | ⚠️ 部分覆盖 | `test_artifacts.py` 中 ID 分配测试, `test_state_v3.py` | 随机种子固定（42）无专门测试；多 run 均值/标准差无测试 |
| **Artifact integrity** | ✅ 有测试 | `test_artifacts.py`(37), `test_legacy_convert.py`(10) | 覆盖充分（ID / lifecycle / registry / 版本） |
| **Evidence integrity** | ✅ 有测试 | `test_evidence_graph.py`(29), `test_evidence_gate.py`(13), `integration/test_cross_question_relations.py`(16) | 覆盖充分 |
| **Schema** | ✅ 有测试 | `test_validate_project.py`(13), `test_delivery_gates.py`(8) | schema 校验通过 validate_project 间接覆盖；无专门的 schema 单元测试 |
| **Security** | ❌ **完全无测试** | 无 | 权限守卫（permission_guard）、信任域（trust_domain）、增量校验（incremental_checker）、路径遍历防护、注入防护均无测试 |
| **Failure recovery** | ⚠️ 部分覆盖 | `test_crash_consistency.py`(2), `test_reconcile.py`(9) | 仅 2 个 crash 测试；resume（断点续跑）、invalidation→rerun、节点 retry/on_fail 反馈环无专门测试 |
| **Real problem execution** | ⚠️ 部分覆盖 | `e2e/test_pipeline.py`(9), `e2e/test_research_runs.py`(4) | 仅 13 个 e2e 测试；真实赛题端到端 DAG 运行（V3 全面验证标准）无充分测试 |
| **Mathematical modeling capability** | ⚠️ 部分覆盖 | `test_method_cards.py`(23), `test_model_selection.py`(15), `test_competition_intelligence.py`(17) | 验证方法卡检索与选型，但不验证实际建模正确性（模型求解、数值结果） |
| **Hash chain** | ⚠️ 部分覆盖 | 间接通过 `validate.py` 57 项校验 | 无专门的 hash_chain 单元测试 |
| **Competition profile** | ✅ 有测试 | `test_competition_intelligence.py`(17), `test_weight_profiles.py`(7) | 覆盖 cumcm/mcm profile |
| **Legacy compatibility** | ✅ 有测试 | `test_legacy_convert.py`(10), `compat/test_runtime_compat.py` | 覆盖 V2↔V3 转换 |

**能力覆盖统计**：
- ✅ 充分覆盖：8 项（Architecture, State, Workflow, Artifact integrity, Evidence integrity, Schema, Competition profile, Legacy compatibility）
- ⚠️ 部分覆盖：8 项（Provider boundary, Replay, Determinism, Failure recovery, Real problem execution, Mathematical modeling, Hash chain, Replay）
- ❌ 完全无测试：1 项（**Security**）

### 4.4 测试结构异常

| 异常 | 证据 | 影响 |
|---|---|---|
| `tests/tests/` 嵌套目录 | `tests/tests/fixtures/sample_problem.txt`——tests/ 下又有一个 tests/ 目录，仅含 1 个 fixture 文件 | 目录结构混乱，可能是历史迁移遗留；pytest 收集时可能产生歧义 |
| `tests/compat/` 测试未被收集 | `test_runtime_compat.py`（11619 字节）存在但 792 收集数中无 compat/ 目录的测试 | 可能被 skip 或不匹配 `test_*.py` 模式；需确认 |
| `tests/` 根级测试未被收集 | `test_tex_to_docx_quick.py`（4207 字节）存在但不在收集列表中 | 同上 |
| conftest.py 强制 cwd | `os.chdir(ROOT)`——所有测试依赖相对路径（`os.path.exists("core/legacy/...")`） | 换目录运行全挂；fixture-existence 测试尤其依赖此 |

---

## 5. Core 子系统健康度

### 5.1 子系统总览

| 子系统 | 文件数 | 职责 | 活跃度 | 死代码 | V3 定位符合度 |
|---|---|---|---|---|---|
| `core/env/` | 15 | 配置注入（config.yaml + loader.py + schema.yaml + 9 竞赛 profile） | 高 | 无 | ✅ |
| `core/evaluation/` | 6（3 个 py 源文件） | 评分/基准/回归（**空壳包**） | 低 | **全为空壳** | ❌ 迁移未完成 |
| `core/knowledge/` | 404 | 决策知识 + benchmark 数据 | 高 | bench/ 越界 | ⚠️ 33.7% 文件越界 |
| `core/legacy/` | 283 | V2 四手 29 agent 兼容层 | 冻结（只读） | 无（按设计保留） | ✅ |
| `core/roles/` | 5 | 5 Role 能力组合声明 | 高 | 无 | ✅ |
| `core/runtime/` | 108 | V3 运行时（artifacts/state/graph/execution/writing/modeling/...） | 高 | domain/ + adapters/ 为空包 | ✅（2 个空包） |
| `core/schemas/` | 26 | 16 V2 schema + 12 V3 schema | 高 | 无 | ✅ |
| `core/skills/` | 4 | V3 capability skills（仅 critics/） | 中 | 无（但不完整） | ⚠️ 仅 4 个 critic skill |
| `core/templates/` | 39 | LaTeX 论文模板 + figures 模板 | 中 | 无 | ✅ |
| `core/tools/` | 170 | CLI 工具（38 shim + 6 子目录） | 高 | 2 个 broken shim | ⚠️ evaluation/ 越界 |
| `core/validators/` | 35 | L1-L6 验证模块（21 modules + evidence gate + quality） | 高 | 无 | ✅ |
| `core/workflows/` | 8 | base.yaml + competition/ + stages/ | 高 | 无 | ✅ |

### 5.2 重点子系统深度分析

#### core/skills/（4 文件）——是否正常？

```
core/skills/
└── critics/
    ├── experiment-critic/SKILL.md
    ├── judge-critic/SKILL.md
    ├── model-critic/SKILL.md
    └── narrative-critic/SKILL.md
```

**判定**：**结构上符合 V3 设计，但能力上不完整。**

V3.1_ARCHITECTURE.md §1.7 定义："Skill = 单一可执行能力单元（prompt + procedure + self-check + 工具绑定）"。当前 `core/skills/` 仅有 4 个 critic skill，而 catalog/v3.yaml 定义了 15 个 DAG 节点，每个节点应引用 capability（skill 组合）。

**V3 的 skill 加载机制**：
- `catalog/v3.yaml` 的 nodes 节中，validator 类型节点引用 `core/skills/critics/<name>/SKILL.md`（model-critic / experiment-critic）
- 其余节点（problem_analysis / model_selection / experiment_design 等）的 skill 定义**不在 core/skills/ 中**——它们仍依赖 `core/legacy/hands/<Hand>/agents/<name>/SKILL.md`
- `core/runtime/roles.py` 负责 Role→capability 映射，但 capability 的实际指令文件在 legacy/

**结论**：V3 的 skill 层是**半迁移状态**——critic skill 已迁入 core/skills/，其余 11 个节点的 skill 仍在 legacy/hands/。这不是 bug（V3.1_ARCHITECTURE.md §1.18 明确 legacy 双模式运行），但意味着 `core/skills/` 的 4 文件是**预期内的不完整**，而非异常。

#### core/roles/（5 文件）——5 Role 定义

```
core/roles/
├── analyst.yaml      (324 bytes)
├── critic.yaml       (468 bytes)
├── experimenter.yaml (413 bytes)
├── modeler.yaml      (339 bytes)
└── writer.yaml       (453 bytes)
```

**判定**：✅ 完全符合 V3 设计。5 个 Role 与 catalog/v3.yaml 的 roles 节一一对应。文件体积小（300-500 字节），因为 Role 只是 capability 组合的声明模板，实际指令在 skill/agent 层。

#### core/knowledge/（404 文件）——是否应该属于 runtime？

**分层分析**：

| 子目录 | 文件数 | 性质 | 是否应属 runtime |
|---|---|---|---|
| `methodology/` | 54 | 方法论文档 + METHOD-DECISION-TREE + INDEX | ✅ 决策知识 |
| `paper-cases/` | 117 | 论文案例拆解 + METHOD-MAPPING + INNOVATION-TAGS | ✅ 决策知识（案例参考） |
| `methods/cards/` | 16 | 机器可读方法卡片（good_for/requires/risks/validation） | ✅ **核心**决策知识 |
| `playbooks/` | 13 | 端到端例题（国赛 9 + 美赛 3） | ⚠️ 边界——是教学案例还是 runtime 知识？ |
| `validation/` | 21 | 验证模块文档/配置 | ✅ runtime 验证知识 |
| `failures/` | 10 | Failure Memory（failure_id / root_cause / fix） | ✅ **核心**决策知识 |
| `patterns/` | 6 | Innovation Patterns | ✅ **核心**决策知识 |
| `cookbooks/` | 8 | 算法手册 | ✅ 决策知识 |
| `_negative/` | 8 | 反例库 | ✅ 决策知识 |
| `problems/` | 5 | 历年赛题库索引 | ⚠️ 边界——赛题数据属 competition profile |
| `review/` | 2 | 评审视角洞察 | ✅ 决策知识 |
| `empirical/` | 1 | 获奖论文实测分位锚定 | ⚠️ 边界——empirical data 属 benchmark |
| `data-sources/` | 1 | 数据源清单 | ✅ 决策知识 |
| `pitfalls/` | 4 | 反模式库 | ✅ 决策知识 |
| `competition/` | 2 | 竞赛知识 | ✅ Competition Profile |
| **`bench/`** | **136** | **CUMCM rubric + e2e 基准案例** | ❌ **Benchmark 数据，不应属 runtime** |

**结论**：`core/knowledge/` 的 **84.6%（342/404）文件是合理的 runtime 决策知识**，但 **15.4%（62 文件，若算 e2e 全部则 136）是 benchmark 数据**。`bench/` 子目录是最大的越界块。

**V3 知识层的设计定位**（V3.1_ARCHITECTURE.md §1.5）：
> "Knowledge = 帮助 Agent 做更好选择的决策知识，不是让 Agent 读更多文档的文档库。三层结构：Method Cards / Failure Memory / Innovation Patterns。"

按此定义，`bench/`（rubric + e2e 案例）不是"决策知识"，而是"评测数据"——它帮助的是**评测者**打分，不是帮助 Agent 做选择。因此 `bench/` 应迁出 `core/knowledge/`。

#### core/legacy/（283 文件）——V2 兼容层确认只读

```
core/legacy/hands/
├── Modeler/    (77 files: 8 agents + knowledge + laws + templates)
├── Programmer/ (72 files: 6 agents + knowledge + laws + templates)
├── Writer/     (108 files: 7 agents + knowledge + laws + templates + writing)
└── Reviewer/   (25 files: 8 agents + knowledge + laws)
```

**判定**：✅ 符合 V3 兼容层定位。Hardening P4 已将四手降级至 `core/legacy/hands/`，AGENTS.md 明确"只读兼容不新增"。文件分布合理（Writer 最大因为写作知识多，Reviewer 最小因为 scorer 已降级为 validator/critic）。

**潜在风险**：legacy/hands/ 中仍有 282 个非 pycache 文件，其中大量是 SKILL.md 指令文档。这些指令是 V2 时代的"Agent Brain"，在 V3 架构下仍被编排器消费（orchestrator --legacy 模式）。只要 legacy 模式不下线，这些文件就必须保留。下线标准见 V3.1_ARCHITECTURE.md §1.18："真实项目端到端 DAG 运行 + regression 套件全绿"。

#### core/runtime/（108 文件）——子系统健康

| 子目录 | 文件数 | 职责 | 健康度 |
|---|---|---|---|
| `artifacts/` | 10（5 py） | ID / artifact / lifecycle / registry | ✅ 核心，测试充分（37 tests） |
| `state/` | 12（6 py） | 多维状态模型 / dependencies / relations / reconcile / runs | ✅ 核心，测试充分（44 tests） |
| `graph/` | 4（2 py） | Evidence Graph + invalidation | ✅ 核心，测试充分（29 tests） |
| `execution/` | 18（9 py） | DAG 引擎 / WaveExecutor / composer / handlers / session / replay | ✅ 核心，测试充分（51+ tests） |
| `writing/` | 24（12 py） | director / expression / fact_check / findings / judge_critic / narrative_critic / narrative_ir / paragraphs / patterns / projection / redundancy | ⚠️ 最大子系统——writing 层逻辑丰富，但与 `core/skills/critics/` 的 critic skill 有职责重叠（judge_critic / narrative_critic 同时存在于 runtime/writing/ 和 skills/critics/） |
| `modeling/` | 8（4 py） | candidates / planner / selection | ✅ 建模运行时 |
| `knowledge/` | 10（5 py） | cards / intelligence / packs / retriever | ✅ 知识检索运行时 |
| `decisions/` | 4（2 py） | decision log | ✅ 测试充分（23 tests） |
| `synthesis/` | 4（2 py） | cross-question context | ✅ P12 跨问题合成 |
| `legacy/` | 4（2 py） | V2 适配器（convert.py） | ✅ 测试充分（10 tests） |
| `domain/` | 1（仅 `__init__.py`） | **空包** | ❌ 无实现 |
| `adapters/` | 1（仅 `__init__.py`） | **空包** | ❌ 无实现——provider boundary 声明存在但代码为空 |
| `contracts.py` | 1 | runtime 契约定义 | ✅ |
| `roles.py` | 1 | Role 加载器 | ✅ |

**关键发现**：
1. `core/runtime/writing/`（24 文件）是最大的 runtime 子系统，包含了 narrative_critic 和 judge_critic 的 Python 实现。而 `core/skills/critics/` 也有 narrative-critic/SKILL.md 和 judge-critic/SKILL.md。**critic 的"Python 实现"与"SKILL.md 指令"分处两处**——这是设计（catalog/v3.yaml 中 narrative-critic 和 judge-critic 的 kind=runtime，path 指向 `core/runtime/writing/`；model-critic 和 experiment-critic 的 kind=skill，path 指向 `core/skills/critics/`），但容易造成混淆。
2. `core/runtime/domain/` 和 `adapters/` 是空包——**provider boundary 的代码实现缺失**。V3.1_ARCHITECTURE.md §2 的目录规划中有 `core/runtime/adapters/`（"runtime manifest 生成 / cloud sandbox / harness compat"），但实际只有 `__init__.py`。gen_runtime_manifest.py 和 cloud_sandbox.py 在 `core/tools/runtime/` 中，不在 `core/runtime/adapters/`。

#### core/tools/（170 文件）——Shim 与子目录

**Root-level shim（38 个）**：全部是兼容转发，指向 `core/tools/<子目录>/<同名文件>`。模式统一：
```python
_TARGET = Path(__file__).resolve().parent / "<subdir>" / "<name>.py"
# runpy.run_path 或 exec 转发
```

**Broken shim（2 个）**：
| Shim | 目标 | 状态 |
|---|---|---|
| `core/tools/fidelity_gate.py` | `core/tools/evaluation/fidelity_gate.py` | ❌ 目标不存在 |
| `core/tools/run_p13_3d.py` | `core/tools/evaluation/run_p13_3d.py` | ❌ 目标不存在 |

**6 个子目录**：
| 子目录 | 文件数 | 职责 | 越界 |
|---|---|---|---|
| `runtime/` | 5 | orchestrator / state / replay / gen_runtime_manifest / cloud_sandbox | ✅ |
| `validation/` | 8 | validate / validate_project / gate / gatelib / citation_check / writing_check / freeze_numbers / repro_checklist | ✅ |
| `evaluation/` | 8 | score_compute / aggregate_scores / e2e_metrics / benchmark / bench_mmbench / metrics / score_artifact / weight_profiles | ⚠️ benchmark + 评分逻辑属 research 评测 |
| `knowledge/` | 6 | knowledge / catalog_check / distill_empirical / reflection_bank / retrospect / scholar_fetch | ✅ |
| `devtools/` | 4 | new_project / doctor / env_doctor / check_matlab_env | ✅ |
| `rendering/` | 5 | diagram_gen / tex_to_docx / docx_post_processor / text_cleanup / render_ai_usage | ✅ |
| `friendly/` | 1（仅 `__init__.py`） | 空包 | ❌ |

---

## 6. 绝对不能动的核心架构（v3.1.0 冻结）

以下是 v3.1.0 已冻结的核心架构组件，本次审计**绝对不修改**，仅记录其在位状态与健康度：

### 6.1 冻结组件清单

| # | 组件 | 位置 | 在位状态 | 测试覆盖 | 冻结依据 |
|---|---|---|---|---|---|
| 1 | **Artifact Registry** | `core/runtime/artifacts/registry.py` + `artifact.py` + `ids.py` + `lifecycle.py` | ✅ 在位（10 文件，5 py 源） | 37 tests（test_artifacts.py） | V3.1_ARCHITECTURE.md §1.1, §1.10, §1.11；Hardening P0 |
| 2 | **Evidence Graph** | `core/runtime/graph/evidence_graph.py` | ✅ 在位（4 文件，2 py 源） | 29 tests（test_evidence_graph.py）+ 13（evidence_gate） | V3.1_ARCHITECTURE.md §1.3, §1.12；Hardening P0 |
| 3 | **Research State** | `core/runtime/state/model.py` + `dependencies.py` + `relations.py` + `reconcile.py` + `runs.py`；持久化 `projects/<p>/state/status.json` | ✅ 在位（12 文件，6 py 源） | 24（state_v3）+ 11（state）+ 9（reconcile） | V3.1_ARCHITECTURE.md §1.2；Hardening P2 State Truth |
| 4 | **Workflow DAG** | `core/runtime/execution/dag.py` + `engine.py` + `wave_executor.py` + `composer.py` + `yamlio.py`；定义 `core/workflows/` | ✅ 在位（18 文件，9 py 源） | 24（dag_engine）+ 9（wave_executor）+ 18（workflow_compose）+ 6（integration workflow_execution） | V3.1_ARCHITECTURE.md §1.4, §1.14, §1.15；Hardening P0 |
| 5 | **验证门禁（L1-L6）** | `core/validators/modules/`（21 模块）+ `core/validators/evidence/` + `core/validators/quality/`；CLI `core/tools/validation/gate.py` + `validate.py` | ✅ 在位（35 文件） | 间接通过 validate.py 57 项校验 + test_validate_project(13) + test_delivery_gates(8) | docs/ARCHITECTURE.md 六层防御体系；Hardening P0 |
| 6 | **State 单一真源（status.json）** | `projects/<p>/state/status.json`（schema_version 3）；由 `state.py reconcile` 对账 | ✅ 在位 | test_reconcile(9) + test_crash_consistency(2) + integration test_state_registry_sync(4) | Hardening P2 State Truth；docs/architecture/STATE_TRUTH.md |
| 7 | **Hash chain** | `core/validators/modules/hash_chain.py` | ✅ 在位 | 间接通过 validate.py L6 校验；无专门单元测试 | docs/ARCHITECTURE.md L6；AGENTS.md 铁律 |
| 8 | **Provider boundary** | `core/runtime/adapters/`（**空包**）+ `adapters/openai.yaml` + `core/tools/runtime/gen_runtime_manifest.py` + `cloud_sandbox.py` | ⚠️ 声明在位，实现不完整 | test_openai_manifest(18) + test_cloud_sandbox(8) | V3.1_ARCHITECTURE.md §2 目录规划；RC-SMOKE S3 Provider Audit |

### 6.2 冻结组件的健康度备注

- **Artifact Registry / Evidence Graph / State / Workflow DAG**：四大支柱均在位且测试充分（合计 150+ 专门测试），是仓库最健康的部分。
- **验证门禁 L1-L6**：21 个 modules 在位，但 hash_chain 无专门单元测试（仅间接覆盖），Security 相关模块（permission_guard / trust_domain / incremental_checker）完全无测试。
- **State 单一真源**：status.json 契约稳定，但 projects/ 中无真实运行实例（2 个均为 init 态 fixture），**真源在空转**——没有真实数据验证 reconcile 的端到端正确性。
- **Provider boundary**：是冻结组件中**最薄弱**的一环——`core/runtime/adapters/` 是空包，provider 逻辑散落在 `core/tools/runtime/` 和根目录 `adapters/`。RC-SMOKE S3 已做 Provider Audit（`research/RC-SMOKE/S3_PROVIDER_AUDIT.md`），但代码层的 provider 抽象尚未落地。

---

## 7. 风险汇总与优先级

| # | 风险 | 严重度 | 证据位置 | 建议处置（不属本次审计执行范围） |
|---|---|---|---|---|
| R1 | projects/ 被 fixture 占用，无真实运行实例，validate 空转 | **高** | §3.2 状态文件完全相同；§3.4 | 将 p151/rcs1 移至 tests/fixtures/ 或 archives/；用 new_project.py 创建真实项目并跑通 DAG |
| R2 | core/knowledge/bench/（136 文件）benchmark 数据越界 | 中 | §1.2, §2.2-C | 迁移至 research/benchmark/ 或仓库外；runtime 仅保留 method cards/failures/patterns |
| R3 | 2 个 broken shim（fidelity_gate, run_p13_3d） | 中 | §5.2, §2.2-A | 删除 run_p13_3d.py（research 专用）；确认 fidelity_gate 是否需要实现或删除 |
| R4 | MMBench 外部仓库路径硬编码在 core/ | 中 | §2.2-B | 随 benchmark 逻辑一起迁出 core/；或仅保留环境变量接口，删除默认硬编码 |
| R5 | Security 能力完全无测试 | 中 | §4.3 矩阵 | 为 permission_guard / trust_domain / incremental_checker 编写单元测试 |
| R6 | tests/tests/ 嵌套目录异常 | 低 | §4.4 | 将 sample_problem.txt 移至 tests/fixtures/，删除 tests/tests/ |
| R7 | core/evaluation/ 空壳包，迁移未完成 | 低 | §2.4, §5.1 | 完成迁移或正式宣布 core/tools/evaluation/ 为永久位置，删除空壳 |
| R8 | core/runtime/domain/ + adapters/ 空包 | 低 | §5.2 | 实现 provider adapters 或删除空包；将 gen_runtime_manifest/cloud_sandbox 归入 adapters |
| R9 | ~72 个 fixture-existence 测试可合并 | 低 | §4.2-B | 合并 test_modeler/programmer/writer/gateway_agents 为一个 test_legacy_integrity.py |
| R10 | docs/architecture/ 被 P13/P14 研究报告占用（12 份） | 低 | §1.3 | 迁移至 research/ 对应实验目录下的 docs/ |

---

## 8. 审计结论

### 8.1 总体判定

MathModel 仓库的 **V3 运行时内核是健康、稳定、可测试的**。Artifact Registry、Evidence Graph、Research State、Workflow DAG 四大支柱均有充分的测试覆盖（150+ 专门测试），research→core 无直接 import 污染，依赖方向正确（research consumes core）。

**污染集中在三个边界**：
1. **knowledge 层边界**：`core/knowledge/bench/`（136 文件）的 benchmark 数据没有彻底剥离
2. **tools 层边界**：`core/tools/evaluation/` 的 benchmark/评分逻辑与 research 专用 shim 混入
3. **projects 层边界**：projects/ 被 smoke fixture 占用，无真实运行实例

### 8.2 对核心问题的最终回答

> **«这个仓库是不是正在从 Harness 演变成一个"大而全的数学建模 Agent 项目"？»**

**是，但漂移是可控的、局部的。** 内核（runtime + validators + schemas）没有被侵蚀，漂移发生在 knowledge/tools/projects 三个外围层。仓库的"大而全"倾向主要体现在：
- research/ 已膨胀至 701 文件且内部形成迷你 runtime（独立 schemas/scripts/state）
- docs/architecture/ 被研究报告占用
- core/knowledge/ 承载了 benchmark 数据

但这些都是**资产归属问题**，不是**架构污染问题**。core/runtime/ 的 108 个文件是干净的、专注的、可测试的。只要完成 benchmark 数据剥离、fixture 归位、空包清理，仓库就能回到"精干 Harness"的定位。

### 8.3 对冻结架构的确认

v3.1.0 冻结的 8 大核心组件全部在位，其中 7 个健康，1 个（Provider boundary）实现不完整但不影响核心流程。本次审计未修改任何冻结组件。

---

## 附录 A：审计命令记录

```powershell
# 目录结构
ls core; ls core/runtime; ls core/tools; ls core/evaluation; ...

# 文件计数
foreach ($d in Get-ChildItem core -Directory) { (Get-ChildItem $d.FullName -Recurse -File | Measure-Object).Count }

# Research → Core 依赖
Grep pattern="from research|import research" path=core/  → 0 matches
Grep pattern="P13|P14|P15" path=core/  → 25 files

# Broken shim 扫描
Test-Path core/tools/evaluation/fidelity_gate.py  → False
Test-Path core/tools/evaluation/run_p13_3d.py  → False

# 测试收集
py -3.12 -m pytest tests -q --co  → 792 tests collected

# 项目状态对比
Get-ChildItem projects/p151-2024a/state -File  → 6 files, sizes match rcs1 exactly
```

## 附录 B：关键文件路径索引

| 组件 | 路径 |
|---|---|
| V3.1 架构真源 | `docs/architecture/V3.1_ARCHITECTURE.md` |
| 三层架构治理 | `docs/architecture/THREE_LAYER_ARCHITECTURE.md` |
| 状态真源 | `docs/STATUS.md` |
| 硬化计划 | `docs/architecture/HARDENING_PROGRAM.md` |
| Catalog 双视图 | `catalog.yaml`（根）+ `catalog/v3.yaml` |
| Artifact Registry | `core/runtime/artifacts/registry.py` |
| Evidence Graph | `core/runtime/graph/evidence_graph.py` |
| State Model | `core/runtime/state/model.py` |
| Workflow Engine | `core/runtime/execution/engine.py` |
| Wave Executor | `core/runtime/execution/wave_executor.py` |
| Runtime Session | `core/runtime/execution/session.py` |
| Validators | `core/validators/modules/`（21 模块） |
| Evidence Gate | `core/validators/evidence/evidence_gate.py` |
| Hash Chain | `core/validators/modules/hash_chain.py` |
| Knowledge Retriever | `core/runtime/knowledge/retriever.py` |
| Legacy 适配器 | `core/runtime/legacy/convert.py` |
| V3 Schemas | `core/schemas/v3/`（12 schema） |
| Workflow 定义 | `core/workflows/base.yaml` + `competition/` + `stages/` |
| 5 Role 定义 | `core/roles/*.yaml` |
| V3 Skills | `core/skills/critics/`（4 critic） |
| 项目状态真源 | `projects/<p>/state/status.json` |
| 测试套件 | `tests/`（792 tests） |
| 研究实验 | `research/`（701 files） |

---

*报告结束。本次审计为只读观察，未修改任何仓库文件（本报告除外）。*
