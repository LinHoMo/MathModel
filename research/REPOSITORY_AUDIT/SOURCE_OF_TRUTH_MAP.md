# Source of Truth Map — MathModel Repository

> 生成日期：2026-09-08 | 基线 commit：`af1bbd5`（Tier 0 删除后）
> 目的：识别仓库中所有"单一真源"（Single Source of Truth），标记重复/冲突/多真源问题，提出收敛方案。

---

## 1. 真源清单

### 1.1 运行时真源（Runtime Source of Truth）

| 真源 | 路径 | 类型 | 消费方 | 状态 |
|---|---|---|---|---|
| **执行协议** | `AGENTS.md`（根目录） | Markdown | 所有 agent / human | ✅ 唯一 |
| **状态数字** | `docs/STATUS.md` | Markdown | 人类 / 审计 | ✅ 唯一（机器实测数字 + commit hash） |
| **架构总览** | `docs/ARCHITECTURE.md` | Markdown | 人类 / 新 agent | ✅ 唯一 |
| **V3 角色定义** | `core/roles/`（5 个 YAML） | YAML | orchestrator / runtime | ✅ 唯一 |
| **V3 DAG 定义** | `core/workflows/`（8 个文件） | YAML/Python | orchestrator | ✅ 唯一 |
| **运行时执行引擎** | `core/runtime/execution/` | Python | orchestrator | ✅ 唯一 |
| **Artifact Registry** | `projects/<项目>/state/registry.json` | JSON | runtime / validators | ✅ 唯一（每项目） |
| **Evidence Graph** | `projects/<项目>/state/evidence_graph.json` | JSON | runtime / validators | ✅ 唯一（每项目） |
| **流程状态** | `projects/<项目>/state/status.json` | JSON | state.py / orchestrator | ✅ 唯一（V3 已收口） |
| **Decision Log** | `projects/<项目>/state/decision_log.json` | JSON | runtime / audit | ✅ 唯一 |
| **Run Manifest** | `projects/<项目>/state/runs/` | JSON | measurement / replay | ✅ 唯一 |
| **配置** | `core/env/config.yaml` + `core/env/loader.py` | YAML/Python | 所有 runtime | ✅ 唯一 |
| **JSON Schema** | `core/schemas/`（26 个） | JSON Schema | validators / runtime | ✅ 唯一 |
| **Hash Chain** | `core/runtime/` 内 hash_chain 模块 | Python | validators / replay | ✅ 唯一 |
| **Provider Boundary** | `core/runtime/adapters/` + `adapters/openai.yaml` | Python/YAML | runtime / gen_manifest | ⚠️ 生成文件含 V2 术语（DEBT-011） |

### 1.2 目录结构真源

| 真源 | 路径 | 类型 | 消费方 | 状态 |
|---|---|---|---|---|
| **Legacy 结构** | `catalog.yaml`（根目录，17KB） | YAML | catalog_check / gen_manifest | ✅ 唯一（legacy hands 节） |
| **V3 视图** | `catalog/v3.yaml` | YAML | orchestrator / catalog_check | ✅ 唯一 |
| **外部 Skill 注册** | `catalog/external_skills.yaml` | YAML | runtime / gen_manifest | ✅ 唯一 |
| **协议工具表** | `catalog/protocol_tools.yaml` | YAML | runtime | ✅ 唯一 |

### 1.3 知识真源

| 真源 | 路径 | 类型 | 消费方 | 状态 |
|---|---|---|---|---|
| **方法卡** | `core/knowledge/methods/` + `methodology/` | Markdown | knowledge.py / agent | ✅ 唯一 |
| **论文案例** | `core/knowledge/paper-cases/` | Markdown | knowledge.py / agent | ✅ 唯一 |
| **验证方法卡** | `core/knowledge/validation/` | Markdown | knowledge.py | ✅ 唯一 |
| **Playbook** | `core/knowledge/playbooks/` | Markdown | agent / benchmark | ✅ 唯一 |
| **失败案例** | `core/knowledge/failures/` + `_negative/` | Markdown | agent / training | ✅ 唯一 |
| **Benchmark 语料** | `core/knowledge/bench/`（136 文件） | JSON | evaluation / benchmark | ⚠️ **越界**：benchmark 数据应在 research/，不应在 runtime knowledge（见 §2.1） |

### 1.4 Benchmark 真源

| 真源 | 路径 | 类型 | 消费方 | 状态 |
|---|---|---|---|---|
| **CUMCM Benchmark** | `research/P15/benchmark/CUMCM-Bench-v2.json` | JSON | benchmark.py / evaluation | ⚠️ **P0**：2024_A 题面与实际输入不一致（防空导弹 ≠ 板凳龙） |
| **能力标签** | `research/P15/catalog/by_capability.json` | JSON | measurement / reporting | ⚠️ 基于 invalid B0 数据 |
| **失败模式分类** | `research/P15/catalog/by_failure_mode.json` | JSON | measurement / reporting | ⚠️ 有 overlap 和遗漏（上一轮审计确认） |
| **模型家族分类** | `research/P15/catalog/by_family.json` | JSON | measurement / reporting | ✅ |
| **能力标签 Schema** | `research/P15/schemas/p15_capability_tags.schema.json` | JSON Schema | validators | ✅ |
| **Baseline Snapshot** | `research/P15/benchmark/manifests/baseline_snapshot.json` | JSON | measurement / regression | ⚠️ 基于 invalid B0 |
| **Content Hashes** | `research/P15/benchmark/manifests/content_hashes.json` | JSON | authenticity check | ⚠️ 2024_A hash 与 run manifest 不一致 |
| **Run Manifest** | `research/P15/benchmark/manifests/p151-2024a-run.json` | JSON | measurement / replay | ⚠️ **P0**：latency=0.06s, provider=null, 空壳 artifact |

### 1.5 题面真源（P0 问题区）

| 真源 | 路径 | 类型 | 消费方 | 状态 |
|---|---|---|---|---|
| **2024_A 题面（当前）** | `examples/problems/cumcm2024A.txt` | Text | new_project.py / pipeline | 🔴 **P0**：内容是"防空导弹"，非 gold standard 中的"板凳龙" |
| **2024_A 题面（项目副本）** | `projects/p151-2024a/inputs/cumcm2024A.txt` | Text | pipeline | 🔴 同上（hash 匹配，证明 pipeline 收到错误题面） |
| **2024_A 题面（归档副本）** | `archives/cumcm2024anew/inputs/problem_cumcm2024A.txt` | Text | archive | 🔴 同上（三处副本都是错误题面） |
| **2022_C / 2020_B / 2018_A / 2019_C** | CUMCM-Bench-v2.json 中 input_file=null | — | benchmark | 🔴 **BLOCKED**：无题面文件 |

### 1.6 评估器真源

| 真源 | 路径 | 类型 | 消费方 | 状态 |
|---|---|---|---|---|
| **E2E Metrics** | `core/tools/evaluation/e2e_metrics.py` | Python | benchmark / measurement | 🔴 **P0**：无 non-emptiness check，method_selection 字符串匹配，model_correctness 依赖外部输入 |
| **Artifact Scoring** | `core/tools/evaluation/score_artifact.py` | Python | measurement | ⚠️ 对空 payload 处理不当 |
| **Benchmark Runner** | `core/tools/evaluation/benchmark.py` | Python | benchmark | ⚠️ 可能有 solution-method leakage |
| **Metrics** | `core/tools/evaluation/metrics.py` | Python | measurement | ✅ |
| **Score Compute** | `core/tools/evaluation/score_compute.py` | Python | measurement | ✅ |
| **V3 Validators** | `core/validators/`（35 个文件） | Python | validate.py / gate | ✅ 模块化实现 |
| **Validation CLI** | `core/tools/validation/`（gate.py, validate.py） | Python | CLI | ✅ CLI 入口 |
| **V3 前向兼容包** | `core/evaluation/`（6 文件，仅 `__init__`） | Python | import 兼容 | ⚠️ 空壳，实际逻辑在 tools/evaluation/ |

### 1.7 研究证据真源

| 真源 | 路径 | 类型 | 状态 |
|---|---|---|---|
| **P13-3D 实验** | `research/P13-3D/`（106 文件） | 实验证据 | ✅ 关闭（negative but informative） |
| **P13-3D-R2** | `research/P13-3D-R2/`（130 文件） | 复现实验 | ✅ 冻结 |
| **P13-3D-R3** | `research/P13-3D-R3/`（207 文件） | 对照实验 | ✅ 关闭（已删 12 个 _tmp_*.txt） |
| **P14 Pilot** | `research/P14/`（134 文件） | 验证链 | ✅ PASS（21/21 replay match） |
| **RC-SMOKE** | `research/RC-SMOKE/`（4 文件） | 冒烟测试 | ✅ S1/S3 PASS |
| **P15 Benchmark** | `research/P15/`（14+ 文件） | 进行中 | 🟡 measurement invalid（待恢复） |

---

## 2. 多真源 / 冲突问题

### 2.1 Benchmark 语料越界（中严重度）

**问题**：`core/knowledge/bench/`（136 文件，含 10 道真题三臂 artifact + 盲评矩阵）驻留在 runtime knowledge 层。

**冲突**：
- 架构原则：Benchmark 属 research/，不属 runtime knowledge
- 实际：bench 语料在 core/knowledge/ 下，被 knowledge.py 加载
- 风险：research 实验数据反向污染 runtime

**收敛方案**：MOVE → `research/benchmarks/corpus/`，core/knowledge/ 保留检索接口（Tier 1）。

### 2.2 题面三处副本（中严重度）

**问题**：2024_A 题面存在于三处：
1. `examples/problems/cumcm2024A.txt`（fixture）
2. `projects/p151-2024a/inputs/cumcm2024A.txt`（项目副本）
3. `archives/cumcm2024anew/inputs/problem_cumcm2024A.txt`（归档副本）

**冲突**：三处内容相同（都是错误的"防空导弹"），但没有 single source of truth。修改一处不会自动同步其他处。

**收敛方案**：
- 真源：`research/P15/benchmark/problem_cards/2024_A/problem_statement.txt`（待 Input Authenticity Recovery 找到真实题面后建立）
- examples/ 和 projects/ 为派生副本（由 new_project.py 从真源复制）
- archives/ 为历史归档（不更新）

### 2.3 评估器双入口（低严重度）

**问题**：`core/validators/`（35 文件，V3 模块化实现）和 `core/tools/validation/`（CLI 入口，gate.py 38KB + validate.py 76KB）并存。

**冲突**：功能重叠风险——validators/ 是实现层，tools/validation/ 是 CLI 层，但边界不明确。

**收敛方案**：DOCUMENT——明确 validators/ = 实现层，tools/validation/ = CLI 入口（调用 validators/）。不合并，保持分层。

### 2.4 状态文件三真源（历史遗留，已部分收敛）

**问题**：`archives/cumcm2024anew/work/` 下存在 `state.json` + `STATE.md` + `state/status.json` 三份状态文件。

**冲突**：V2 时代的双真源模式（state.json + STATE.md）与 V3 的 status.json 并存。

**收敛方案**：V3 已收口到 `state/status.json` 为唯一真源。archives/ 下的历史文件保留为归档，不更新。projects/ 下的 work/state.json + STATE.md 为 V2 兼容残留，标记为 DEBT（不删除，因为可能被 legacy 模式引用）。

### 2.5 能力分类多真源（中严重度）

**问题**：能力定义存在于多处：
1. `research/P15/catalog/by_capability.json`（P15 能力标签）
2. `research/REPOSITORY_AUDIT/04_MODELING_CAPABILITY_AUDIT.md`（上一轮 C0–C15）
3. `research/P15/capability/CAPABILITY_MAP.md`（本轮重建，待子代理产出）
4. `core/knowledge/methodology/`（方法卡中的能力描述）

**冲突**：C0–C15 vs 11 项能力 vs 方法卡中的隐式能力定义，不一致。

**收敛方案**：以 `research/P15/capability/CAPABILITY_MAP.md` 为能力定义真源（本轮重建）。P15 catalog 为 measurement 数据（引用能力定义）。上一轮审计为历史参考。方法卡为知识资产（不定义能力，只描述方法）。

### 2.6 论文规范冲突（已确认）

**问题**：任务简报中提到"30 pages"，但上一轮审计确认官方规范为"正文尽量控制在 20 页以内"（2020 修订稿）。

**冲突**：30页 vs 20页。

**收敛方案**：以官方来源为准（20页）。等待 Input Authenticity Recovery 子代理获取官方规范的 URL 和发布日期，记录在 `research/P15/measurement_recovery/INPUT_AUTHENTICITY_PROTOCOL.md`。

---

## 3. 真源健康度总览

| 类别 | 真源数 | 健康 | 有问题 | P0 |
|---|---|---|---|---|
| 运行时 | 16 | 14 | 2 | 0 |
| 目录结构 | 4 | 4 | 0 | 0 |
| 知识 | 7 | 6 | 1 | 0 |
| Benchmark | 9 | 2 | 4 | 3 |
| 题面 | 5 | 0 | 0 | 5 |
| 评估器 | 9 | 5 | 3 | 1 |
| 研究证据 | 6 | 6 | 0 | 0 |
| **合计** | **56** | **37 (66%)** | **10 (18%)** | **9 (16%)** |

**结论**：运行时和研究证据真源健康（66% 全绿）。Benchmark、题面、评估器三个测量相关真源是 P0 重灾区（9 个 P0 全部集中在测量层）。这与上一轮审计结论一致：**内核健康，测量仪器失真**。

---

## 4. 收敛优先级

| 优先级 | 动作 | 真源 | 预期效果 |
|---|---|---|---|
| **P0** | 找到真实 2024_A 板凳龙题面，建立题面真源 | `research/P15/benchmark/problem_cards/2024_A/problem_statement.txt` | 输入真实性恢复 |
| **P0** | 修复 orchestrator 真实执行，建立 execution 真源 | run manifest 中 provider/latency/artifact 非空 | 执行真实性恢复 |
| **P0** | 实现 artifact non-emptiness gate | `research/P15/measurement_recovery/execution_gate.py` | artifact 完整性恢复 |
| **P0** | 修复 e2e_metrics.py（non-emptiness + method_selection） | `core/tools/evaluation/e2e_metrics.py` | 评估器有效性恢复 |
| **P1** | Benchmark 语料迁出 core | `research/benchmarks/corpus/` | 消除 research→runtime 越界 |
| **P1** | 能力定义真源收敛 | `research/P15/capability/CAPABILITY_MAP.md` | 消除能力定义多真源 |
| **P1** | 题面副本收敛（真源→派生副本） | examples/ + projects/ 从真源复制 | 消除题面三处副本 |
| **P2** | 评估器双入口文档化 | validators/ = 实现, tools/validation/ = CLI | 消除功能重叠歧义 |
| **P2** | 论文规范官方来源确认 | INPUT_AUTHENTICITY_PROTOCOL.md | 消除 20页/30页 冲突 |

---

*报告生成时间：2026-09-08 | 基于 FILE_INVENTORY.json（1808 文件）和上一轮审计结论 | 下一步：等待 4 个子代理完成测量恢复工作*
