# 结构与命名迁移方案

> **文档定位**：依据新三分定位（Model Construction=What / Model Representation=How / Harness=How do we know），对 MathModel 仓库的文件夹结构与命名进行逐项审视，产出迁移方案。
>
> **铁律**：本文件只写方案，不执行任何目录移动/改名/删除。不动 research 历史证据、不动 .git/.gitignore、不改 v3.1.x core 架构、不擅自删未跟踪本地工具目录。
>
> **生成时间**：2026-09-08 | **评估范围**：全仓库顶层目录 + core/ 全部子目录 + 关键配置文件
>
> **架构约束**：AGENTS.md 已定义五层目录（product=core/ / legacy=core/legacy/hands/ / benchmark=core/tools/evaluation/ / research/ / instance=projects/），架构已冻结，本方案优先在此框架内落位，不推翻重排。

---

## 0. 执行摘要

### 新定位一句话

MathModel 是一个面向数学建模的 **LLM-free、可复现、可审计的建模能力实验基础设施**。外部 Agent 负责认知与模型构造（What），Harness 负责冻结问题、记录建模过程、建立模型与证据的可追溯关系、验证执行真实性并进行能力测量（How do we know）；Model Representation 是连接二者的标准化表达层（How）。

### 核心结论

| 维度 | 结论 |
|---|---|
| 根目录名 | **KEEP "MathModel"** — 代码零依赖、中性、改名只有外部成本无收益 |
| 五层框架 | 完全复用，不推翻；Model Representation 嵌入 product 层的 core/schemas/ + research/P15 孵化 |
| 最高优先级清理 | package.json + package-lock.json（V2 残留占位，无消费方） |
| 最大结构债务 | core/tools/ 松散文件与子目录双版本并行（35 loose + 37 subdir，subdir 版零导入、V2 时代 docstring） |
| 需用户决定 | core/tools 双版本处置、AI 工具配置去重策略、docs/ 历史文档归档范围 |

### 事实勘误（相对于用户初步勘察）

| 用户初步结论 | 核实结果 |
|---|---|
| archives/ 目录为空 | **错误** — archives/ 有 10 个跟踪文件（cumcm2024anew 快照 + README.md） |
| tests/tests/ 嵌套已删 | **错误** — tests/tests/fixtures/sample_problem.txt 仍被跟踪 |
| .clinerules/.cursorrules/.windsurfrules/CLAUDE.md/GEMINI.md/AGENTS.md 疑似未跟踪 | **错误** — 全部 6 个文件均被 git 跟踪 |
| research/P15/model_representation/ 正在写 MODEL_IR_SPEC | **该目录当前为空** — 无任何文件，MODEL_IR_SPEC 尚未落盘 |
| core/tests/adapters 内 0 处绝对路径 | **正确** — git grep 确认 core/tests/adapters 无 "Programs/MathModel" |

---

## 1. 概念到目录的映射

### 1.1 三分定位与五层结构的对应

```
┌─────────────────────────────────────────────────────────────────┐
│                    Model Construction = What                     │
│         （外部 Agent 的认知与建模能力，Harness 不拥有此层）        │
│         Harness 侧支撑：core/runtime/modeling/、core/roles/      │
│         core/knowledge/methods/、core/schemas/model_*.json       │
├─────────────────────────────────────────────────────────────────┤
│                  Model Representation = How                      │
│         数学模型的结构化表达：IR / Graph / Card / Trace / Diff   │
│         ┌─ 稳定 schema：core/schemas/（product 层）              │
│         └─ 孵化期规范：research/P15/model_representation/        │
├─────────────────────────────────────────────────────────────────┤
│                     Harness = How do we know                     │
│         可信度底座：执行、验证、测量、复现、溯源                   │
│         core/runtime/、core/tools/、core/validators/             │
│         core/tools/evaluation/、core/env/、core/schemas/         │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 逐映射表

| 新定位层 | 现有目录 | 角色 | 动作 |
|---|---|---|---|
| **Harness 执行层** | `core/runtime/` | RuntimeSession、Artifact Registry、Evidence Graph、Workflow DAG 执行 | KEEP — 已是 Harness 核心 |
| **Harness 编排层** | `core/tools/`（松散文件） | state.py / orchestrator.py / gate.py / validate.py / replay.py 等 CLI 入口 | KEEP — AGENTS.md 命令速查全部指向松散路径 |
| **Harness 测量层** | `core/tools/evaluation/` | benchmark.py / metrics.py / score_compute.py / e2e_metrics.py | KEEP — 对应五层中的 benchmark 层 |
| **Harness 验证层** | `core/validators/` | evidence/、modules/、quality/ 三门验证模块 | KEEP |
| **Harness 配置层** | `core/env/` | config.yaml 阈值集中注入 | KEEP |
| **Harness 角色定义** | `core/roles/` | 5 Role YAML（analyst/modeler/experimenter/critic/writer） | KEEP |
| **Harness 工作流** | `core/workflows/` | base.yaml + competition/ + stages/ | KEEP |
| **Model Representation（稳定）** | `core/schemas/` | 16 个 schema JSON + v3/ 子目录（artifact/decision/evidence/knowledge/run/state/workflow） | KEEP + 扩展 — Model IR/Graph/Card/Trace/Diff 稳定后迁入 |
| **Model Representation（孵化）** | `research/P15/model_representation/` | MODEL_IR_SPEC.md + model_ir.schema.json（待创建） | KEEP — 研究期规范与实例 |
| **Model Construction 支撑** | `core/knowledge/` | methods/、methodology/、patterns/、pitfalls/、playbooks/ 等 16 子目录 | KEEP — 方法卡检索支撑 Agent 建模 |
| **Model Construction 支撑** | `core/runtime/modeling/` | 建模领域逻辑 | KEEP |
| **Legacy 兼容** | `core/legacy/hands/` | V2 四手 29 agent（Modeler/Programmer/Writer/Reviewer） | KEEP（只读兼容，不新增） |
| **Legacy 兼容** | `core/evaluation/` | 空壳（仅 3 个 __init__.py，零导入） | **候选 DELETE** — 见 §3 |
| **Instance 层** | `projects/` | 用户运行实例（p151-2024a 等 3 个项目） | KEEP |
| **Research 层** | `research/` | P13-3D 系列、P14、P15、bench-m4*、RC-SMOKE | KEEP + 内部整理（见 §3） |
| **模板层** | `core/templates/` | latex/ + figures/ | KEEP |
| **技能层** | `core/skills/` | critics/（4 个 critic skill） | KEEP — 注意与 legacy hands 的 skills 区分 |

### 1.3 映射原则

1. **不新增顶层目录**：Model Representation 不独立成顶层，嵌入 core/schemas/（稳定）+ research/（孵化），符合五层冻结框架。
2. **Harness 是底座不是全部**：core/ 下所有目录本质都是 Harness 组件；Model Construction 是外部 Agent 的能力，Harness 只提供支撑（knowledge、schemas、roles）。
3. **Representation 是横切层**：schema 同时服务于 Harness（验证 artifact 格式）和 Construction（Agent 输出契约），放在 product 层 core/schemas/ 是正确位置。

---

## 2. Model Representation 的家

### 2.1 现状

- `core/schemas/`：16 个顶层 schema JSON（model_artifact、model_dag、model_spec、question_spec、paper_spec、score_card 等）+ `v3/` 子目录（artifact/、decision/、evidence/、knowledge/、run/、state/、workflow 七个分类）。
- `research/P15/model_representation/`：**当前为空目录**，MODEL_IR_SPEC.md 与 model_ir.schema.json 尚未落盘。
- `research/P15/schemas/`：有 `p15_capability_tags.schema.json`（P15 实验专用）。

### 2.2 推荐落位

| 产物 | 孵化期位置 | 稳定后位置 | 说明 |
|---|---|---|---|
| Model IR 规范文档 | `research/P15/model_representation/MODEL_IR_SPEC.md` | `docs/architecture/MODEL_IR_SPEC.md` | 规范文档随稳定迁入 docs |
| Model IR schema | `research/P15/model_representation/model_ir.schema.json` | `core/schemas/model_ir.schema.json` | 与现有 model_*.schema.json 并列 |
| Model Graph schema | `research/P15/model_representation/model_graph.schema.json` | `core/schemas/v3/evidence/` 或 `core/schemas/model_graph.schema.json` | 与 Evidence Graph 关系需明确：Model Graph 是语义结构，Evidence Graph 是溯源结构，二者不同 |
| Model Card schema | `research/P15/model_representation/model_card.schema.json` | `core/schemas/model_card.schema.json` | 模型元数据卡 |
| Model Trace schema | `research/P15/model_representation/model_trace.schema.json` | `core/schemas/v3/run/` 或 `core/schemas/model_trace.schema.json` | 建模过程轨迹，与 run/ 分类相关 |
| Model Diff 规范 | `research/P15/model_representation/MODEL_DIFF_SPEC.md` | `docs/architecture/MODEL_DIFF_SPEC.md` | 模型版本差异规范 |
| 实例与验证用例 | `research/P15/model_representation/examples/` | `tests/fixtures/model_representation/` | 稳定后转为测试夹具 |

### 2.3 从 research 迁移到 product 层的条件

schema 或规范从 `research/P15/model_representation/` 迁移到 `core/schemas/` / `docs/architecture/` 须**同时满足**以下条件：

1. **稳定性验证**：schema 经过 ≥3 个真实模型实例的 round-trip 验证（序列化→反序列化→语义等价），无 breaking change 连续 ≥2 周。
2. **消费方存在**：至少一个 core/ 模块（evaluator、validator、runtime）实际 import 并使用该 schema 进行校验或序列化；或至少一个 research 实验的产出物以该 schema 为契约。
3. **确定性校验实现**：存在对应的 deterministic check 实现（Python 函数或 pytest 用例），能在 CI 中验证 schema 本身的合法性（meta-schema 校验）。
4. **向后兼容策略**：明确 version 字段与 deprecation 策略；若与现有 core/schemas/ 中的 schema 有重叠，须给出合并或共存的明确理由。
5. **文档完备**：规范文档包含字段语义、示例、边界条件、与现有 schema 的关系图。

### 2.4 与现有 core/schemas/ 的关系

**复用优先，新增最小化**：

- `model_spec.schema.json`（现有）：已覆盖模型规格的基本结构。Model IR 应是其超集或重构，而非平行体系。迁移时须明确：Model IR 是替代 model_spec 还是与之共存（IR 为机器内部表示，spec 为 Agent 输出契约）。
- `model_dag.schema.json`（现有）：建模 DAG 结构。Model Graph 若表达的是模型内部的数学依赖图（变量→方程→约束），则与 DAG（流程节点）不同，可共存；若表达相同则合并。
- `model_artifact.schema.json`（现有）：产物登记结构。Model Card 是模型元数据，与 artifact registry 的关系需明确（Card 是 Artifact 的一种类型，还是独立实体）。
- `v3/evidence/`（现有）：Evidence Graph schema。Model Trace 是建模过程轨迹，Evidence Graph 是证据溯源图，Trace 可作为 Evidence Graph 的输入源之一。

**建议**：在 MODEL_IR_SPEC 中专门设一节 "与现有 schema 的映射与差异"，逐字段说明复用/扩展/新增，避免双轨制。

---

## 3. 逐项命名审视表

> 动作定义：KEEP（保留）/ RENAME（改名）/ MOVE（移动）/ MERGE（合并）/ DELETE（删除）/ DOCUMENT（仅文档化）

### 3.1 顶层目录

| 当前名 | 建议动作 | 建议名 | 理由 | 被引用证据 | 风险 | 验证方式 |
|---|---|---|---|---|---|---|
| `core/` | KEEP | — | product 层，Harness 引擎本体，架构冻结 | AGENTS.md 五层定义；所有运行时代码 | 无 | — |
| `adapters/` | **MOVE+MERGE** | 内容并入 `core/runtime/adapters/` | 根目录仅 1 个文件 openai.yaml（自动生成），与 core/runtime/adapters/（空壳 __init__.py）功能重叠；生成器 gen_runtime_manifest.py 输出路径应改为 core/runtime/adapters/ | `git ls-files adapters/` = 仅 openai.yaml；gen_runtime_manifest.py 引用；tests/unit/test_openai_manifest.py 引用 | 中 — 生成器输出路径和测试路径需同步改 | grep "adapters/openai" 全仓；改后跑 test_openai_manifest.py |
| `catalog/` | KEEP | — | v3.yaml + external_skills.yaml + protocol_tools.yaml，与根 catalog.yaml 构成双视图 | catalog_check.py 三方一致性校验 | 低 — 已有 catalog_check 强制一致 | `py -3.12 core/tools/catalog_check.py --check` |
| `catalog.yaml` | KEEP | — | legacy 29 agent 主视图（hands 节），catalog/v3.yaml 是 V3 视图拆分；双真源由 catalog_check.py 管控 | AGENTS.md "结构单一真源是 catalog.yaml"；catalog_check.py | 低 | 同上 |
| `docs/` | KEEP + 内部整理 | — | 文档层；含 architecture/（38 文件）、decisions/（1 文件）、integration/（1 文件）+ 7 个顶层 .md | 多处引用 docs/STATUS.md 为状态真源 | 中 — 部分文档可能 stale，见 §3.3 | 逐文档核实最后更新时间与引用方 |
| `examples/` | KEEP | — | 题面 fixture（仅 cumcm2024A.txt），作为 new_project.py 的输入样例合理 | new_project.py 可能引用；examples/problems/ 是标准 fixture 位置 | 低 | grep "examples/problems" 全仓 |
| `projects/` | KEEP | — | instance 层，用户运行实例 | AGENTS.md 五层定义；state.py 操作 projects/<项目>/ | 无 | — |
| `research/` | KEEP + 内部整理 | — | research 层，P13/P14/P15 实验 + bench 运行 + REPOSITORY_AUDIT | AGENTS.md 五层定义 | 低 — 内部命名可优化，见 §3.6 | — |
| `tests/` | KEEP + 修复嵌套 | — | 测试层；unit(46)/integration(16)/e2e(2)/regression(2)/compat(1)/fixtures/ + 残留 tests/tests/ 嵌套 | pyproject.toml testpaths=["tests"]；pytest 基线 758 passed | 中 — tests/tests/ 嵌套需清理 | 删除嵌套后跑 pytest 确认无引用 |
| `archives/` | KEEP | — | **非空** — 含 cumcm2024anew 快照（10 跟踪文件：state/registry/evidence_graph/status + work/ 产物） | `git ls-files archives/` 返回 10 文件 | 低 — 历史归档，不动 | — |

### 3.2 core/ 十二子目录逐一审视

| 当前名 | 建议动作 | 理由 | 被引用证据 | 风险 | 验证方式 |
|---|---|---|---|---|---|
| `core/env/` | KEEP | 阈值集中配置（config.yaml + loader.py），零依赖注入，所有手共享 | AGENTS.md env 配置入口表；`from env.loader import get` | 无 | — |
| `core/evaluation/` | **DELETE（候选）** | 空壳 — 仅 3 个 __init__.py（benchmark/、scoring/、顶层），零导入方，零实际代码；功能已由 core/tools/evaluation/ 承担 | `git grep "core.evaluation"` 无匹配；目录内无 .py 业务代码 | 低 — 但需确认无动态 import（如 importlib） | `git grep -r "evaluation" -- core/ tests/` 排除 core/tools/evaluation/ 后确认；删除后跑 pytest |
| `core/knowledge/` | KEEP | 方法卡知识库（16 子目录：methods/methodology/patterns/pitfalls/playbooks/bench/competition 等），knowledge.py recommend 消费 | `core/tools/knowledge.py`；AGENTS.md 命令速查 | 无 | — |
| `core/legacy/` | KEEP | V2 兼容层入口（hands/ + README.md），只读不新增 | AGENTS.md legacy 定义；catalog.yaml hands 节路径 | 无 | — |
| `core/roles/` | KEEP | 5 Role YAML（analyst/critic/experimenter/modeler/writer），V3 DAG 角色定义 | catalog/v3.yaml roles 节；orchestrator.py 消费 | 无 | — |
| `core/runtime/` | KEEP | Harness 执行核心（12 子目录：artifacts/graph/state/execution/modeling/domain/decisions/synthesis/writing/knowledge/legacy/adapters + contracts.py/roles.py） | orchestrator.py RuntimeSession；state.py；AGENTS.md V3 模式 | 无 | — |
| `core/schemas/` | KEEP + 扩展 | Model Representation 稳定层的家；16 顶层 schema + v3/ 七分类 | gate.py/validators 消费；catalog.yaml 引用 | 低 — 扩展不影响现有 | schema 校验测试 |
| `core/skills/` | KEEP | V3 critic skills（4 个：experiment/judge/model/narrative critic） | catalog/v3.yaml；runtime 消费 | 低 — 注意与 legacy hands/agents/*/SKILL.md 区分，命名不冲突 | — |
| `core/templates/` | KEEP | LaTeX 模板 + figures 模板 | Writer 手消费；tex_to_docx.py | 无 | — |
| `core/tools/` | **DOCUMENT + 待用户决定** | **双版本并行**：35 个松散 .py（V3  canonical，AGENTS.md 引用）+ 6 子目录含 37 个 .py（V2 时代平行实现，零导入方，docstring 写"29 步""四手"）。松散版是真源，子目录版疑似未完成的重构残留 | AGENTS.md 命令速查全部指向松散路径；`git grep "core.tools.runtime."` 无匹配；子目录 orchestrator.py docstring = "一键跑完 29 步" | **高** — 子目录版 29 个文件被跟踪，若删除需确认无脚本直接调用子目录路径；属 Tier 3 core 架构调整，须用户拍板 | `git grep "core/tools/runtime/\|core/tools/validation/"` 全仓（含 docs、scripts、CI）；确认无直接调用后再评估 |
| `core/validators/` | KEEP | 三门验证（evidence/modules/quality），L1-L6 门禁执行方 | gate.py 消费；AGENTS.md 铁律 "schema/哈希链全绿" | 无 | — |
| `core/workflows/` | KEEP | V3 工作流定义（base.yaml + competition/ + stages/） | catalog/v3.yaml workflows_dir；orchestrator.py 消费 | 无 | — |

### 3.3 docs/ 内部审视

| 当前名 | 建议动作 | 理由 |
|---|---|---|
| `docs/STATUS.md` | KEEP | 状态真源（机器实测数字 + commit hash），AGENTS.md 明确指定 |
| `docs/ARCHITECTURE.md` | **REVIEW** | 含 UTG/29 agent 引用，需确认是历史描述还是当前架构声明；若与 V3.1 矛盾则更新或标注 "historical" |
| `docs/IMPROVEMENT_PLAN.md` | **REVIEW** | 含 UTG 引用，可能是 V2 时代改进计划，需确认是否已执行完毕或已过时 |
| `docs/BENCHMARK.md` | KEEP | benchmark 说明 |
| `docs/CHECKLIST.md` | KEEP | 检查清单 |
| `docs/METRICS.md` | KEEP | 指标定义 |
| `docs/TEAM_GUIDE.md` | **REVIEW** | 团队指南，可能含 V2 分工描述 |
| `docs/architecture/`（38 文件） | KEEP + 标注 | 含 P11/P13/R3/V3 系列报告，多数是历史实验报告（合理保留）；HARDENING_PROGRAM.md 是当前硬化计划（活跃）；THREE_LAYER_ARCHITECTURE.md 需确认是否与新三分定位一致 |
| `docs/decisions/2026-09-04-refactor-plan-v2.md` | KEEP | 决策记录（ADR 模式），保留 |
| `docs/integration/harness-compat.md` | KEEP | 集成兼容文档 |

**建议**：对 docs/ 中含 "UTG"/"29 agent"/"四手" 且非历史实验报告的文件，逐个标注 `> 状态：historical（V2 时代）` 或更新为 V3 表述。此动作属 DOCUMENT 级，低风险。

### 3.4 tests/ 内部审视

| 当前名 | 建议动作 | 理由 | 验证 |
|---|---|---|---|
| `tests/unit/`（46 文件） | KEEP | 单元测试主力 | — |
| `tests/integration/`（16 文件） | KEEP | 集成测试 | — |
| `tests/e2e/`（2 文件） | KEEP | 端到端测试 | — |
| `tests/regression/`（2 文件） | KEEP | 回归测试 | — |
| `tests/compat/`（1 文件） | KEEP | 兼容性测试 | — |
| `tests/fixtures/` | KEEP | 测试夹具 | — |
| `tests/tests/` | **DELETE** | 残留嵌套，仅含 fixtures/sample_problem.txt（1 跟踪文件）；用户曾认为已删但实际未删；需确认该 fixture 无测试引用 | `git grep "tests/tests" -- tests/`；若 sample_problem.txt 被引用则先移至 tests/fixtures/ 再删 |
| `tests/conftest.py` | KEEP | pytest 配置 | — |
| `tests/test_tex_to_docx_quick.py` | **MOVE** | 松散测试文件，应归入 tests/unit/ 或 tests/integration/ | 确认 import 路径后移动 |
| `tests/__pycache__/` | 不跟踪 | 本地缓存，.gitignore 应已覆盖 | `git ls-files tests/__pycache__/` 应为空 |

### 3.5 adapters/ 详细分析

```
根 adapters/          core/runtime/adapters/
└── openai.yaml       ├── __init__.py（空壳）
（自动生成，101 行）   └── __pycache__/
```

- `adapters/openai.yaml` 由 `core/tools/runtime/gen_runtime_manifest.py` 自动生成（文件头注释明确标注），从 catalog.yaml 派生。
- 被 `tests/unit/test_openai_manifest.py` 和 `tests/regression/test_v2_capability_regression.py` 引用。
- `core/runtime/adapters/__init__.py` 是空壳，无实际代码。
- **问题**：生成器输出到根 adapters/，但 core/runtime/adapters/ 是更合理的位置（runtime 层的适配器）。且 openai.yaml 中 `instructions_file: "core/AGENTS.md"` 指向不存在的文件（实际是根 `AGENTS.md`）——这是生成器的 bug。
- **建议**：MOVE openai.yaml → `core/runtime/adapters/openai.yaml`，修复 gen_runtime_manifest.py 输出路径和 instructions_file 路径，更新测试引用。属 Tier 1（无行为变化的结构整理），但因涉及生成器代码修改，需谨慎验证。

### 3.6 research/ 内部组织

| 目录 | 跟踪文件数 | 性质 | 建议 |
|---|---|---|---|
| `P13-3D/` | 104 | P13 实验第一轮 | KEEP（历史证据） |
| `P13-3D-R2/` | 130 | P13 第二轮 | KEEP（历史证据） |
| `P13-3D-R3/` | 207 | P13 第三轮 | KEEP（历史证据） |
| `P14/` | 91 | P14 预注册实验（runs/schemas/scripts/state + PILOT_REPORT） | KEEP（活跃/历史） |
| `P15/` | 14 | P15 当前活跃（benchmark/capability/catalog/measurement_recovery/model_representation/reports/schemas/scripts + PRE_REGISTRATION） | KEEP（**当前主攻方向**，含 Model Representation 孵化） |
| `bench-m4-2000c/` | 23 | M4 基准运行 | KEEP（benchmark 证据） |
| `bench-m4-2000c-p131-b/` | 14 | P13-1 变体 B | KEEP |
| `bench-m4-2000c-p131-c/` | 14 | P13-1 变体 C | KEEP |
| `bench-m4-2000c-p132-a/` | 13 | P13-2 变体 A | KEEP |
| `bench-m4-2000c-p132-b/` | 14 | P13-2 变体 B | KEEP |
| `bench-m4-2000c-p132-c/` | 14 | P13-2 变体 C | KEEP |
| `bench-p132-2023c/` | 13 | P13-2 2023C 题 | KEEP |
| `RC-SMOKE/` | 4 | Release Candidate 冒烟测试 | KEEP |
| `REPOSITORY_AUDIT/` | ~15 | 仓库审计系列文档（含本文件） | KEEP |

**命名观察**：
- `bench-m4-2000c-p131-b` 这类命名混合了基准名（m4-2000c）和实验编号（p131-b），可读性差但已被历史报告引用，**不建议改名**（改名会破坏历史证据的路径引用）。
- P13-3D 系列用 R2/R3 后缀表示轮次，P14/P15 无后缀，命名风格不统一但可接受（不同实验系列有不同惯例）。
- **建议**：research/ 下新增 `README.md` 说明各目录的性质（活跃/历史/基准），便于新贡献者理解。属 DOCUMENT 级。

### 3.7 关键文件

| 当前名 | 建议动作 | 理由 | 验证 |
|---|---|---|---|
| `pyproject.toml` | **REWRITE description** | name="mathmodel-skills"、description="Mathematical Modeling Skills - Role-based Architecture" 是 V2 时代表述；应更新为新定位描述（如 "LLM-free reproducible auditable mathematical modeling capability harness"）；name 是否改需用户决定 | 改后 `pip install -e .` 验证 |
| `Dockerfile` | KEEP | Python 3.11 + TeX Live，注释中 "mathmodel-skills" 标签可同步更新 | docker build 验证 |
| `docker-compose.yml` | KEEP | 容器编排 | — |
| `README.md` | **REVIEW** | 需确认是否与新定位一致；若仍描述 V2 "四手 29 agent" 则更新 | — |
| `.gitignore` | KEEP（不动） | 已有 node_modules/ 规则；铁律禁止修改 | — |

---

## 4. AI 工具配置治理

### 4.1 跟踪状态核实（git ls-files 实测）

| 配置 | 跟踪状态 | 跟踪文件数 | 内容性质 |
|---|---|---|---|
| `.claude/` | **被跟踪** | 101 | skills/ 下 10 个 syslab 相关 skill（syslab-app-designer、syslab-code-style、syslab-digital-filter-design、syslab-environment、syslab-julia-to-cpp、syslab-matlab-to-julia、syslab-mds-docs、syslab-performance-optimization、syslab-testing 等） |
| `.opencode/` | **被跟踪** | 1 | plans/V3_ARCHITECTURE_PLAN.md |
| `.trae/` | 未跟踪 | 0 | 本地缓存（用户勘察：23 处绝对路径，可再生） |
| `.workbuddy/` | 未跟踪 | 0 | 本地工具目录 |
| `.zcode/` | 未跟踪 | 0 | 本地工具目录 |
| `.clinerules` | **被跟踪** | 1 | 指向 AGENTS.md，提及 V2 "projects/<项目>/work/STATE.md" |
| `.cursorrules` | **被跟踪** | 1 | 与 .clinerules 内容完全相同 |
| `.windsurfrules` | **被跟踪** | 1 | 与 .clinerules 内容完全相同 |
| `CLAUDE.md` | **被跟踪** | 1 | 指向 AGENTS.md，V3 表述（"Scientific/Mathematical Modeling Harness"） |
| `GEMINI.md` | **被跟踪** | 1 | 与 CLAUDE.md 内容完全相同 |
| `AGENTS.md` | **被跟踪** | 1 | **唯一真源**，五层目录 + V3/V2 执行协议 |

### 4.2 重复分析

**规则文件三组完全重复**：

1. `.clinerules` ≡ `.cursorrules` ≡ `.windsurfrules`（三者逐字相同，V2 表述）
2. `CLAUDE.md` ≡ `GEMINI.md`（二者逐字相同，V3 表述）
3. 两组之间的差异：clinerules 组提及 "projects/<项目>/work/STATE.md"（V2 路径），CLAUDE.md 组提及 "Scientific/Mathematical Modeling Harness" + "docs/STATUS.md"（V3 表述）

**.claude/skills/ 与 core/skills/ 的关系**：
- `.claude/skills/` 是 Claude Code 工具的 skill 格式（10 个 syslab 相关），与 `core/skills/`（4 个 critic skill）**内容不重叠**，但命名空间相似可能造成混淆。
- `.claude/skills/` 被跟踪 101 文件，体积较大，需确认是否应继续跟踪（syslab skills 是 MWORKS 交付分支相关，可能属于特定环境配置而非仓库核心资产）。

### 4.3 治理建议

| 配置 | 建议动作 | 理由 | 风险 |
|---|---|---|---|
| `AGENTS.md` | KEEP — **唯一真源** | 所有其他规则文件均应指向此文件 | 无 |
| `CLAUDE.md` | KEEP | Claude Code 入口，内容已正确指向 AGENTS.md（V3 表述） | 无 |
| `GEMINI.md` | **MERGE → 删除** | 与 CLAUDE.md 完全相同；Gemini 工具若支持读取 CLAUDE.md 则无需独立文件；若 Gemini 强制要求 GEMINI.md 则保留但内容改为 `@AGENTS.md` 单行 | 低 — 需确认 Gemini 是否强制要求 GEMINI.md |
| `.clinerules` | **UPDATE** | 内容为 V2 表述（"projects/<项目>/work/STATE.md"），应更新为与 CLAUDE.md 一致的 V3 表述，或改为 `@AGENTS.md` 单行 | 低 |
| `.cursorrules` | **MERGE → 删除或更新** | 与 .clinerules 完全相同；Cursor 若支持 .clinerules 或 AGENTS.md 则删除；否则更新为 V3 表述 | 低 — 需确认 Cursor 规则文件优先级 |
| `.windsurfrules` | **MERGE → 删除或更新** | 与 .clinerules 完全相同；同上 | 低 |
| `.claude/` | **REVIEW 跟踪范围** | 101 个跟踪文件中 10 个是 syslab skills；若 syslab 是可选环境（MWORKS 交付分支），可考虑移至 docs/ 或加 .gitignore；但当前被跟踪且可能被 Claude Code 运行时依赖，**不建议轻动** | 中 — 需确认 Claude Code 是否依赖 .claude/skills/ |
| `.opencode/` | KEEP | 仅 1 个架构计划文档，跟踪合理 | 无 |
| `.trae/` / `.workbuddy/` / `.zcode/` | **不跟踪，不删除** | 用户本地工具目录，铁律禁止擅自删；建议在 .gitignore 中确认已覆盖（若未覆盖则添加，但铁律禁止改 .gitignore——需用户决定） | 无 |

**核心原则**：AGENTS.md 是唯一真源，所有 AI 工具配置文件应尽量简化为 `@AGENTS.md` 指针，避免多份规则文档内容漂移。当前 clinerules 组的 V2 表述与 AGENTS.md 的 V3 协议已存在不一致（STATE.md 路径），属于内容漂移。

---

## 5. node 残留处置

### 5.1 现状核实

| 文件 | 跟踪状态 | 内容 | 消费方 |
|---|---|---|---|
| `package.json` | **被跟踪** | name="mathmodel"，version="1.0.0"，description（乱码，原文为"基于 UTG…四手分工、29 agent 串联、把赛题变成无 AI 痕迹 LaTeX 论文"），main="index.js"（**index.js 不存在**），scripts.test="echo Error: no test specified && exit 1"（占位），无 dependencies | **无** — 全仓无 JS/TS 代码，无 Node 工具链依赖 |
| `package-lock.json` | **被跟踪** | 与 package.json 对应（无 dependencies 时应为空或最小锁文件） | **无** |
| `node_modules/` | **未跟踪**（0 文件） | 本地安装产物，.gitignore 第 13-14 行已有 `node_modules/` 规则 | 本地杂物 |

### 5.2 判定

- **package.json 是 V2 时代残留占位**：description 与新定位（LLM-free Harness + Model Construction）直接冲突；main 指向不存在的 index.js；scripts 是 npm init 默认占位；无任何 dependencies。
- **全仓无 JavaScript/TypeScript 源代码**：`git ls-files "*.js" "*.ts"` 应仅返回 package.json 相关（若有）。无 Node 工具链消费方。
- **满足删除规则**：provably-unused（无消费方）+ superseded（V2 时代产物，已被 Python 工具链替代）+ generated-and-reproducible（若未来需要可随时 `npm init` 重建）。

### 5.3 处置建议

| 文件 | 建议动作 | 理由 | 验证 |
|---|---|---|---|
| `package.json` | **DELETE（Tier 0）** | 无消费方、描述与新定位冲突、main 指向不存在文件、全仓无 JS 代码 | 删除前 `git grep -r "package.json" -- .github/ docs/ scripts/` 确认无 CI/文档引用；删除后 pytest 不受影响 |
| `package-lock.json` | **DELETE（Tier 0）** | 与 package.json 共生，无 dependencies 时无实际价值 | 同上 |
| `node_modules/` | **不替用户删** | 未跟踪的本地目录，用户可自行 `rm -rf node_modules`；方案中说明即可 | — |

**替代方案（若用户希望保留）**：REWRITE package.json 为新定位描述，移除 main/index.js 引用，scripts 留空或加 `"private": true`。但鉴于全仓无 JS 代码，保留一个空壳 package.json 的价值极低，**推荐 DELETE**。

---

## 6. 根文件夹改名评估

### 6.1 "MathModel" 是否需要改？

**独立判断：不需要改，推荐 KEEP。**

理由：

1. **代码零依赖**：`git grep "Programs.MathModel" -- core/ tests/ adapters/` 确认运行时代码 0 处绝对路径。全部相对路径，改名不破坏代码。
2. **名称中性且足够宽**："MathModel" 不窄化到 "Harness" 或 "Forge" 或 "Lab"，能同时涵盖 Construction（建模）、Representation（模型表达）、Harness（实验基础设施）三个层面。"MathModel" = "数学模型"，本身就是 What + How 的统称，Harness 是其实现方式。
3. **改名收益极小**：当前名称无歧义、无负面含义、不与其他项目冲突（用户自有仓库）。
4. **改名成本明确**：见 §6.3。
5. **历史证据绑定**：research/ 中有 22 处绝对路径 "Programs\MathModel"（历史证据快照，禁止回改），改名后这些历史路径与实际路径不一致，增加认知负担。

### 6.2 候选名分析（若用户仍想改）

| 候选名 | 优点 | 缺点 | 适配度 |
|---|---|---|---|
| `MathModelHarness` | 明确 Harness 定位 | 过长；窄化到 Harness 而弱化 Construction/Representation；"Harness" 对非技术受众不直观 | 中 |
| `ModelForge` | 简洁、有"锻造/构建"意象，暗示 Construction | "Forge" 偏代码构建，弱化数学建模的学术性；与已有 "Model Forge" 项目可能重名 | 中低 |
| `ModelLab` | 简洁、"实验室"意象贴合实验基础设施 | 过于通用（无数个 ModelLab）；不突出数学领域 | 低 |
| `ModelKit` | "工具包"意象，贴合 Harness 工具属性 | "Kit" 暗示轻量，与项目的厚重架构（57 项校验、29 agent 兼容）不匹配 | 低 |
| `MathModelLab` | 保留 MathModel 品牌 + Lab 实验属性 | 较长；Lab 后缀增量信息有限 | 中 |
| `ModelWorks` | "工厂/作品"意象，贴合 AI 软件工厂愿景 | 与 MWORKS（北太天元）品牌可能混淆；不突出数学 | 低 |

**若必须改，首选 `MathModelHarness`**（最准确描述当前定位），但仍不推荐。

### 6.3 改名影响清单

| 影响项 | 具体内容 | 修复方式 |
|---|---|---|
| IDE 工作区 | VS Code/Cursor/Trae 等打开的工作区路径失效 | 重新打开文件夹 |
| 终端会话 | 当前终端 cwd 失效 | 重新 cd |
| venv 绝对路径 | 虚拟环境中的 shebang、pyvenv.cfg 含绝对路径 | 重建 venv（`python -m venv .venv`） |
| 远程仓库 | GitHub/GitLab 仓库名（若与本地同名） | 远程仓库改名 + `git remote set-url origin <new-url>` |
| 绝对路径引用 | research/ 中 22 处历史证据快照（禁止回改） | 不修复，接受历史路径与实际不一致 |
| .trae 缓存 | 23 处绝对路径（可再生缓存） | 重新生成缓存 |
| 用户快捷方式 | 桌面快捷方式、启动脚本、别名 | 用户自行更新 |
| 已打开文件 | IDE 中打开的文件标签失效 | 重新打开 |
| Docker 构建 | Dockerfile 中 WORKDIR/COPY 路径（若用绝对路径） | 检查 Dockerfile，通常用相对路径不受影响 |
| CI/CD | GitHub Actions 中的 checkout 路径（通常不依赖根目录名） | 检查 workflows |

### 6.4 推荐操作步骤（若用户决定改）

```
1. 远程仓库改名（GitHub Settings → Rename）
2. git remote set-url origin <new-url>
3. 关闭所有 IDE/终端会话
4. 文件系统重命名：MathModel → <新名>
5. 重新打开 IDE，确认工作区
6. 删除旧 venv，重建：py -3.12 -m venv .venv；.venv\Scripts\Activate；pip install -e .
7. 验证：py -3.12 core/tools/validate.py；py -3.12 -m pytest tests -q
8. 更新用户快捷方式/别名
```

### 6.5 回滚方式

```
1. 远程仓库改回原名
2. git remote set-url origin <old-url>
3. 文件系统重命名回 MathModel
4. 重建 venv
5. 验证
```

### 6.6 最终推荐

> **KEEP "MathModel"**。名称中性、代码零依赖、改名只有外部成本无实质收益。若未来项目范围显著扩展（如从数学建模泛化到通用科学建模），再考虑改名；当前阶段应将精力放在核心架构而非品牌上。

---

## 7. 执行优先级与批次

### Tier 0 — 安全删除（证据充分，零行为变化）

| 项 | 动作 | 前置验证 | 验证要求 |
|---|---|---|---|
| `package.json` | DELETE | `git grep -r "package.json" -- .github/ docs/ scripts/` 无引用；全仓无 .js/.ts 源码 | 删除后 `py -3.12 -m pytest tests -q` 全绿 |
| `package-lock.json` | DELETE | 与 package.json 共生 | 同上 |

### Tier 1 — 无行为变化的结构整理

| 项 | 动作 | 前置验证 | 验证要求 |
|---|---|---|---|
| `tests/tests/` | DELETE（先确认 sample_problem.txt 无引用） | `git grep "tests/tests" -- tests/ core/` 无匹配；若有引用则先 `git mv tests/tests/fixtures/sample_problem.txt tests/fixtures/` | 删除后 pytest 全绿 |
| `tests/test_tex_to_docx_quick.py` | MOVE → `tests/unit/` | 确认 import 路径不依赖顶层位置 | 移动后 pytest 该文件通过 |
| `.clinerules` / `.cursorrules` / `.windsurfrules` | UPDATE 为 V3 表述或 `@AGENTS.md` 单行 | 确认各工具仍能正常读取 | 人工验证各 AI 工具启动 |
| `GEMINI.md` | 若与 CLAUDE.md 完全重复且 Gemini 支持 CLAUDE.md，则 DELETE | 确认 Gemini 工具行为 | — |
| `adapters/openai.yaml` | MOVE → `core/runtime/adapters/openai.yaml` + 修复生成器 | 修复 gen_runtime_manifest.py 输出路径 + instructions_file 路径（core/AGENTS.md → AGENTS.md）；更新 test_openai_manifest.py | `py -3.12 core/tools/runtime/gen_runtime_manifest.py` 重新生成；pytest test_openai_manifest.py 通过 |
| `pyproject.toml` description | REWRITE 为新定位 | — | `pip install -e .` 成功 |

### Tier 2 — research-layer 调整

| 项 | 动作 | 前置验证 | 验证要求 |
|---|---|---|---|
| `research/README.md` | CREATE — 说明各子目录性质（活跃/历史/基准） | — | — |
| `research/P15/model_representation/` | 开始写入 MODEL_IR_SPEC.md + model_ir.schema.json（用户已有计划） | — | 按 §2.3 迁移条件评估 |
| docs/ 中 stale 文档 | 标注 `> 状态：historical` 或更新 | 逐文档核实 | — |

### Tier 3 — core 架构调整（**禁止，除非满足条件**）

| 项 | 动作 | 条件 |
|---|---|---|
| `core/evaluation/` | DELETE（空壳） | 确认无动态 import；`git grep -r "importlib.*evaluation\|__import__.*evaluation"` 无匹配；删除后 pytest 全绿 |
| `core/tools/` 子目录双版本 | DELETE 子目录版（core/tools/runtime/、validation/、knowledge/、rendering/、devtools/、friendly/ 中的 .py） | **需用户拍板**；确认全仓（含 docs、CI、scripts）无直接调用子目录路径；确认子目录版与松散版无功能差异；属 v3.1.x core 架构，铁律要求 "真实 failure mode + minimal patch + non-regression" |
| `core/tools/` 松散文件整理 | 按功能分组到子目录（如 runtime/、validation/） | **需用户拍板**；AGENTS.md 命令速查全部引用松散路径，改动需同步更新 AGENTS.md；属高风险架构调整 |

**Tier 3 铁律重申**：若某内部调整必须动 core 架构才能实现，STOP 报回用户，不擅自做。当前 core/tools 双版本问题需用户决定处置策略。

### 每批通用验证要求

```powershell
# 每批完成后必须全部通过
py -3.12 core/tools/validate.py                      # 57 项项目级校验
py -3.12 core/tools/catalog_check.py --check         # 双视图三方一致
py -3.12 -m pytest tests -q                           # 758 passed / 11 skipped 基线
# Tier 1 涉及 import 路径变更时额外执行
git grep -r "<旧路径>" -- core/ tests/ docs/          # 确认无残留引用
```

---

## 附录 A：事实核实记录

| # | 核实项 | 命令 | 结果 |
|---|---|---|---|
| 1 | 规则文件跟踪状态 | `git ls-files \| Select-String "^\.(clinerules\|cursorrules\|windsurfrules)$\|^CLAUDE\.md$\|^GEMINI\.md$\|^AGENTS\.md$"` | 全部 6 个被跟踪 |
| 2 | package-lock.json 跟踪 | `git ls-files \| Select-String "package-lock"` | 被跟踪 |
| 3 | .claude 跟踪文件数 | `(git ls-files .claude \| Measure-Object -Line).Lines` | 101 |
| 4 | archives/ 跟踪内容 | `git ls-files archives/` | 10 文件（cumcm2024anew 快照 + README） |
| 5 | 运行时代码绝对路径 | `git grep -l "Programs.MathModel" -- core/ tests/ adapters/` | 0 匹配 |
| 6 | tests/tests/ 嵌套 | `git ls-files tests/tests/` | tests/tests/fixtures/sample_problem.txt 仍在 |
| 7 | core/evaluation/ 导入方 | `git grep -l "core.evaluation" -- core/ tests/` | 0 匹配 |
| 8 | core/tools 子目录版导入方 | `git grep -l "core.tools.runtime.\|core.tools.validation." -- core/ tests/` | 0 匹配 |
| 9 | index.js 存在性 | `Test-Path index.js` | False |
| 10 | node_modules 跟踪 | `(git ls-files node_modules/ \| Measure-Object -Line).Lines` | 0 |
| 11 | core/AGENTS.md 存在性 | `Test-Path core/AGENTS.md` | False（openai.yaml 中引用是 bug） |
| 12 | research/P15/model_representation/ 内容 | `Get-ChildItem research/P15/model_representation/ -Recurse` | 空目录 |

## 附录 B：需要用户决定的事项清单

| # | 事项 | 选项 | 影响 |
|---|---|---|---|
| 1 | **core/tools 双版本处置** | (a) 删除子目录版（29 跟踪文件）；(b) 保留但标注 deprecated；(c) 用子目录版替代松散版（需改 AGENTS.md） | Tier 3 高风险，需用户拍板 |
| 2 | **AI 工具配置去重** | (a) 删除 GEMINI.md + 更新 clinerules 组为 V3；(b) 全部保留仅更新内容；(c) 所有非 AGENTS.md 规则文件改为 `@AGENTS.md` 单行 | 低风险，但影响各 AI 工具启动行为 |
| 3 | **.claude/ 跟踪范围** | (a) 继续跟踪 101 文件；(b) syslab skills 移至 docs/ 或取消跟踪 | 中风险，需确认 Claude Code 运行时依赖 |
| 4 | **根目录改名** | KEEP "MathModel"（推荐）/ RENAME | 外部成本高，收益低 |
| 5 | **pyproject.toml name** | 保持 "mathmodel-skills" / 改为 "mathmodel-harness" 或其他 | 影响 pip 包名，低风险 |
| 6 | **docs/ stale 文档处理** | 标注 historical / 更新 / 归档至 archives/ | 低风险，但工作量大 |
| 7 | **adapters/ 合并** | MOVE openai.yaml 至 core/runtime/adapters/ / 保留根 adapters/ | Tier 1，需改生成器代码 |
| 8 | **core/evaluation/ 删除** | DELETE 空壳 / 保留 | Tier 3，需确认无动态 import |

---

> **文档结束**。本方案仅为迁移建议，所有执行动作须用户确认后按 Tier 分批进行，每批完成后通过 validate.py + catalog_check.py + pytest 三道门禁。
