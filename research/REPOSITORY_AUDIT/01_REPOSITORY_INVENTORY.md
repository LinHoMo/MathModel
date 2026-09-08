# 01 — Repository Inventory（仓库清单）

> 审计日期：2026-09-08 | 审计基线 commit：`af1bbd5`（P15.1: record 2024A B0 alignment baseline）
> 审计范围：全仓库文件级深度审计（只读，未修改任何仓库文件）
> 统计口径：git tracked = 1866 files；磁盘非缓存文件 = 2213 files（含 .opencode/node_modules 等未跟踪内容）

---

## 1. 仓库概览

| 项 | 值 |
|---|---|
| 当前分支 | `main`（领先 origin/main 3 commits） |
| 标签 | `v3.1.0`, `v3.1.0-rc1`, `p15.0-benchmark-freeze` |
| 最近提交 | `af1bbd5` P15.1: record 2024A B0 alignment baseline |
| git tracked 文件数 | 1866 |
| 磁盘总文件数（排除 .git/.opencode/node_modules/.pytest_cache） | 2213 |
| 未跟踪目录 | `.trae/`, `.zcode/` |
| Python 版本 | `py -3.12`（本机 py 3.14/3.13 损坏） |

### 1.1 顶层目录文件数

| 目录 | 文件数 | Owner Layer |
|---|---|---|
| `core/` | 1103 | Runtime |
| `research/` | 701 | Research / Benchmark |
| `.claude/` | 101 | Tool-config（syslab skills） |
| `tests/` | 189 | Test / Fixture |
| `docs/` | 57 | Documentation |
| `.opencode/` | 3671（3667 in node_modules，仅 1 file tracked） | Tool-config / Generated |
| `projects/` | 25 | Instance |
| `core/legacy/` | 283 | Legacy（V2 兼容层） |
| `core/knowledge/` | 404 | Runtime Knowledge |
| `archives/` | 10 | Historical |
| `catalog/` | 3 | Runtime Schema |
| `adapters/` | 1 | Generated（auto-gen） |
| `examples/` | 1 | Fixture |
| `.github/` | 1 | Tool-config |
| `node_modules/` | 1（.package-lock.json，gitignored） | Generated |
| `.trae/` | 1（untracked） | Tool-config |
| `.workbuddy/` | 1（untracked, gitignored） | Tool-config |
| `.zcode/` | 1（untracked） | Tool-config |
| `.pytest_cache/` | 5（gitignored） | Generated |

---

## 2. 顶层目录逐项审计

### 2.1 `core/` — Runtime Source of Truth

| 属性 | 值 |
|---|---|
| **Purpose** | 引擎本体：runtime / roles / workflows / validators / schemas / evaluation / tools / skills / knowledge / env / templates / adapters |
| **Owner layer** | Runtime |
| **被 import** | 是 — 全仓库核心消费方 |
| **被 test** | 是 — tests/unit, tests/integration, tests/e2e 全覆盖 |
| **被 CLI 使用** | 是 — core/tools/*.py 为 CLI 入口（37 个 shim 转发到子目录实现） |
| **被 workflow 引用** | 是 — core/workflows/ 定义 DAG，core/runtime/execution/ 消费 |
| **被 documentation 引用** | 是 — docs/ARCHITECTURE.md, docs/STATUS.md, AGENTS.md |
| **被 CI / validation 使用** | 是 — validate.py 57 项校验, catalog_check.py, pytest 781 passed |
| **最后使用证据** | `b004cd1` 2026-09-08 v3.1.0 RC收口 |
| **是否应继续存在** | ✅ 是 — 运行时真源 |

**子目录结构：**

| 子目录 | 文件数 | 说明 |
|---|---|---|
| `core/env/` | 15 | 配置集中地（config.yaml + loader.py + 9 竞赛 profile） |
| `core/evaluation/` | 6 | V3 评估 import 面（scoring/），实际实现驻留 core/tools/evaluation/ |
| `core/knowledge/` | 404 | 方法卡/论文案例/bench 语料/负面案例（详见 §2.2） |
| `core/legacy/` | 283 | V2 四手 29 agent 兼容层（详见 §2.3） |
| `core/roles/` | 5 | V3 五角色 YAML（analyst/modeler/experimenter/critic/writer） |
| `core/runtime/` | 108 | 认知工作流运行时（artifacts/decisions/domain/execution/graph/knowledge/legacy/modeling/state/synthesis/writing/adapters） |
| `core/schemas/` | 26 | JSON Schema（model_spec, paper_spec, code_deliverables 等 15 份） |
| `core/skills/` | 4 | V3 critic skills（experiment/judge/model/narrative-critic） |
| `core/templates/` | 39 | LaTeX 竞赛模板（9 赛事）+ matplotlib 图表模板（6 种） |
| `core/tools/` | 170 | CLI 工具层：37 个根级 shim（~900B each）+ 7 个子目录实现 |
| `core/validators/` | 35 | V3 校验器（evidence_gate / modules 21 项 / quality 4 项） |
| `core/workflows/` | 8 | DAG 定义（base + 2 competition + 5 stages） |

**核心发现：**
- `core/tools/*.py`（37 个文件，每个 ~900B）全部为兼容 shim，通过 `runpy`/`exec` 转发到 `core/tools/<subdir>/<name>.py`。这是 P4 目录重构的产物，保证 AGENTS.md 协议命令路径不变。
- `core/tools/run_p13_3d.py`（511B）指向 `core/tools/evaluation/run_p13_3d.py`，但**目标文件不存在** — 破损 shim（见 DEBT-002）。
- `core/evaluation/` 和 `core/validators/` 为 V3 前向兼容包，实际逻辑仍在 `core/tools/` 侧。

---

### 2.2 `core/knowledge/` — Runtime Knowledge Layer

| 属性 | 值 |
|---|---|
| **Purpose** | 方法卡、论文案例、bench 语料、负面案例、竞赛情报 — V3 知识检索真源 |
| **Owner layer** | Runtime |
| **被 import** | 是 — `core/tools/knowledge/knowledge.py`, `core/runtime/knowledge/` |
| **被 test** | 是 — tests/unit/test_method_cards.py, test_knowledge 相关 |
| **被 CLI 使用** | 是 — `python core/tools/knowledge.py recommend --types <题型>` |
| **最后使用证据** | `b004cd1` 2026-09-08 |
| **是否应继续存在** | ✅ 是 |

**子目录分布：**

| 子目录 | 文件数 | 分类 | 说明 |
|---|---|---|---|
| `bench/` | 136 | Benchmark 语料 | cumcm(22) + e2e(114)：10 道历年真题 + p13_3d 的 ARM 三臂 artifact + blind 评分 |
| `paper-cases/` | 117 | Knowledge | 获奖论文范式蒸馏 |
| `methodology/` | 54 | Knowledge | 方法论卡片 |
| `validation/` | 21 | Knowledge | 验证方法卡 |
| `methods/` | 16 | Knowledge | 具体算法方法卡 |
| `playbooks/` | 13 | Knowledge | 操作手册 |
| `cookbooks/` | 8 | Knowledge | 食谱式教程 |
| `failures/` | 10 | Knowledge | 失败案例库 |
| `_negative/` | 8 | Knowledge | 7 个反模式案例 + README（小样本硬套神经网络、启发式宣称全局最优等） |
| `problems/` | 5 | Knowledge | 问题分类 |
| `patterns/` | 6 | Knowledge | 模式卡 |
| `pitfalls/` | 4 | Knowledge | 陷阱卡 |
| `competition/` | 2 | Knowledge | 竞赛情报 |
| `review/` | 2 | Knowledge | 评审标准 |
| `empirical/` | 1 | Knowledge | 实证数据 |
| `data-sources/` | 1 | Knowledge | 数据源索引 |

**核心发现：**
- `core/knowledge/bench/e2e/artifacts/` 含 114 个文件，覆盖 2019_C 到 2025_B 共 10 道真题 + p13_3d 三题。每道题含 ARM_B0/B1/MMA.json（三臂论文 artifact）和 blind/ 目录下的 X/Y/Z.json（盲评矩阵）+ scores_r5.json。这些是 P13 系列实验的固化语料，**不是垃圾**。
- 同名文件（如 ARM_B0.json x10）是按题目分目录的正常结构，非重复实现。
- `_negative/` 目录的 7 个反模式案例是有价值的训练数据。
- 未发现死知识或明显重复知识。

---

### 2.3 `core/legacy/` — V2 兼容层

| 属性 | 值 |
|---|---|
| **Purpose** | V2 四手 29 agent 流水线，只读兼容不新增 |
| **Owner layer** | Legacy |
| **被 import** | 是 — `core/runtime/legacy/` 桥接层, `core/tools/validation/gate.py` |
| **被 test** | 是 — tests/unit/test_legacy_convert.py, tests/regression/test_v2_capability_regression.py |
| **被 CLI 使用** | 是 — `python core/tools/orchestrator.py <项目> --legacy` |
| **被 documentation 引用** | 是 — AGENTS.md V2 兼容模式, docs/architecture/COMPATIBILITY_POLICY.md |
| **被 CI / validation 使用** | 是 — catalog_check.py 三方一致性, validate.py legacy 冒烟 |
| **最后使用证据** | `5a6b051` 2026-09-07 hardening(P4): Legacy Isolation |
| **是否应继续存在** | ✅ 是 — 架构冻结，长期兼容政策保障 |

**四手分布：**

| 手 | agents 数 | 文件数 | Agent 列表 |
|---|---|---|---|
| Modeler | 8 | 77 | problem-parser, type-classifier, literature-searcher, method-matcher, model-builder, dag-builder, assumption-validator, spec-auditor |
| Programmer | 6 | 72 | template-selector, code-implementer, test-runner, result-verifier, guardrails-checker, hash-auditor |
| Writer | 7 | 108 | structure-planner, section-writer, figure-generator, reference-curator, consistency-checker, guardrails-checker, final-validator |
| Reviewer | 8 | 25 | scorer-academic, scorer-engineering, scorer-judge, scorer-reader, scorer-adversarial, weakness-hunter, revision-planner, revision-executor |

**每个 agent 含 3 个文件：** `SKILL.md`（指令主体）+ `openai.yaml`（agent manifest）+ `evals.json`（评估配置）。

**附加资产：** 每手含 `knowledge/`（代码模板/论文模板）和 `templates/`（SPEC 模板）目录。

**核心发现：**
- 283 文件全部为 V2 资产，P4 已完成隔离迁移到 `core/legacy/hands/`。
- `catalog.yaml`（根目录 17KB）为 legacy 结构单一真源，`catalog_check.py --check` 强制三方一致。
- Reviewer 手仅 25 文件（8 agents × 3 = 24 + 1），比其他手少 — 因为 Reviewer 没有独立 knowledge/templates 目录。
- 未发现 legacy 层有新增修改，只读兼容状态确认。

---

### 2.4 `adapters/` — Generated Adapter Config

| 属性 | 值 |
|---|---|
| **Purpose** | OpenAI Agents SDK 兼容配置（自动生成） |
| **Owner layer** | Generated |
| **被 import** | 间接 — `core/runtime/adapters/__init__.py` 桥接层, `core/tools/runtime/gen_runtime_manifest.py` 生成方 |
| **被 test** | 是 — tests/unit/test_openai_manifest.py |
| **被 CLI 使用** | 是 — gen_runtime_manifest.py 生成 |
| **被 documentation 引用** | 是 — research/RC-SMOKE/S3_PROVIDER_AUDIT.md |
| **最后使用证据** | `b004cd1` 2026-09-08 |
| **是否应继续存在** | ⚠️ 可自动重新生成，但当前为 provider boundary 审计证据 |

**唯一文件：** `adapters/openai.yaml`（8748B）

**核心发现：**
- 文件头明确标注：`*** 本文件由 core/tools/gen_runtime_manifest.py 自动生成 ***`，`*** 请勿手工编辑 —— 以 catalog.yaml 为单一真源 ***`
- 生成时间：2026-09-07T14:00:22+00:00Z
- **内容过时：** 描述仍为 "4 手 29 agent"（V2 术语），`instructions_file` 指向 `core/AGENTS.md`（实际在根目录 `AGENTS.md`）。生成器未随 V3 迁移更新模板。
- RC-S3 provider boundary 审计 PASS 依赖此文件作为声明证据。

---

### 2.5 `archives/` — Historical Archive

| 属性 | 值 |
|---|---|
| **Purpose** | 历史项目归档区 |
| **Owner layer** | Historical |
| **被 import** | 间接 — `core/tools/evaluation/metrics.py` 引用历史基线, `core/tools/validation/validate.py` 排除出实时校验 |
| **被 test** | 否 |
| **被 CLI 使用** | 否（validate.py 显式排除） |
| **被 documentation 引用** | 是 — archives/README.md 自述 |
| **最后使用证据** | `0ce897f` 2026-09-05 refactor(structure): 评审收尾 — 归档样例 |
| **是否应继续存在** | ✅ 是 — 历史基线参考 |

**内容：** `archives/cumcm2024anew/`（10 文件）— 早期脚手架样例的部分归档，含 inputs/problem + state/ + work/（含 handoff.md, state.json, STATE.md, time_budget.yaml）。

**核心发现：**
- README 明确："原幽灵脚手架样例已迁移至 tests/fixtures/scaffolds/（V3 P5 清理）"，"validate.py 将其排除出实时校验，metrics.py 引用历史基线"。
- `work/state.json`（4879B）与 `work/STATE.md`（1673B）并存，与 `state/status.json`（1563B）形成三份状态文件 — 历史遗留的双真源痕迹。
- 归档不完整（无 code/、figures/、paper/），为部分样例。

---

### 2.6 `catalog/` — Runtime Schema Registry

| 属性 | 值 |
|---|---|
| **Purpose** | V3 视图注册表 + 外部 Skill 注册表 + 协议工具表 |
| **Owner layer** | Runtime |
| **被 import** | 是 — load_catalog() 合并到主视图 |
| **被 test** | 是 — catalog_check.py 三方一致性 |
| **被 CLI 使用** | 是 — gen_runtime_manifest.py, orchestrator.py |
| **被 documentation 引用** | 是 — AGENTS.md |
| **最后使用证据** | `5a6b051` 2026-09-07 hardening(P4) |
| **是否应继续存在** | ✅ 是 |

**文件：**
- `catalog/v3.yaml`（3579B）— V3 五角色 + 15 DAG 节点 + 7 validator 注册表
- `catalog/external_skills.yaml`（1761B）— 4 个外部 skill（pdf-parser, latex-compiler, code-executor, syslab）
- `catalog/protocol_tools.yaml`（6186B）— 协议工具表

**核心发现：**
- 根目录 `catalog.yaml`（17167B）为 legacy hands 节真源，`catalog/` 下三个文件为从 catalog.yaml 拆出的 V3/外部/协议视图。
- `catalog_check.py --check` 强制三方一致（catalog.yaml + catalog/v3.yaml + 实际目录结构）。

---

### 2.7 `docs/` — Documentation

| 属性 | 值 |
|---|---|
| **Purpose** | 架构文档、研究报告、决策记录、集成指南 |
| **Owner layer** | Documentation |
| **被 import** | 否（纯文档） |
| **被 test** | 否 |
| **被 CLI 使用** | 否 |
| **被 workflow 引用** | 间接 — STATUS.md 为状态真源 |
| **最后使用证据** | `b004cd1` 2026-09-08 |
| **是否应继续存在** | ✅ 是（部分文档需标记过时） |

**子目录：**
- `docs/architecture/`（48 文件）— 架构冻结文档、P13 系列报告、硬化计划、V3 审计报告、diagrams/（6 个 HTML/JSON 架构图）
- `docs/decisions/`（1 文件）— 2026-09-04-refactor-plan-v2.md（38KB 深度体检与标准化方案）
- `docs/integration/`（1 文件）— harness-compat.md（跨 Harness 行为约定）

**根级文档：**
| 文件 | 大小 | 状态 |
|---|---|---|
| STATUS.md | 6073B | ✅ 状态真源，机器实测数字绑定 commit |
| ARCHITECTURE.md | 14740B | ✅ 架构总览 |
| IMPROVEMENT_PLAN.md | 21812B | ⚠️ V2 时代文档，STATUS.md 明确"仅存档不再维护" |
| TEAM_GUIDE.md | 6917B | ⚠️ 引用 V2 四手结构（Modeler 6 agent 等），未更新 V3 五角色 |
| BENCHMARK.md | 4755B | ✅ 基准说明 |
| CHECKLIST.md | 5153B | ✅ 检查清单 |
| METRICS.md | 2205B | ✅ 机器生成（metrics.py --write），禁止手改 |

**核心发现：**
- `docs/architecture/` 下 48 文件为 P0-P15 各阶段研究报告与架构文档，是研究证据的重要组成部分，**不是垃圾**。
- `docs/architecture/diagrams/` 含 6 个架构图（HTML+JSON），为可视化资产。
- `docs/decisions/2026-09-04-refactor-plan-v2.md` 为已完成的重构计划诊断文档。
- `docs/integration/harness-compat.md` 引用 V2 "四手"契约（MODEL_SPEC.md → CODE_DELIVERABLES.md → PAPER_SPEC.md），未更新 V3 DAG 节点。

---

### 2.8 `examples/` — Fixture

| 属性 | 值 |
|---|---|
| **Purpose** | 题面文件样例 |
| **Owner layer** | Fixture |
| **被 import** | 否 |
| **被 test** | 间接 — new_project.py 可引用 |
| **被 CLI 使用** | 是 — `new_project.py --problem <文件>` |
| **最后使用证据** | `3ceaaf3` 2026-09-04 fixup(P4): 恢复 examples 题面文件 |
| **是否应继续存在** | ✅ 是 |

**唯一文件：** `examples/problems/cumcm2024A.txt`（2397B）— 与 `projects/p151-2024a/inputs/cumcm2024A.txt` 和 `archives/cumcm2024anew/inputs/problem_cumcm2024A.txt` 内容相同（同一份题面的三处副本）。

---

### 2.9 `projects/` — User Run Instances

| 属性 | 值 |
|---|---|
| **Purpose** | 用户运行实例（仅 new_project.py 创建） |
| **Owner layer** | Instance |
| **被 import** | 是 — state.py, orchestrator.py, validate_project.py |
| **被 test** | 是 — tests/e2e, tests/integration |
| **被 CLI 使用** | 是 — 所有 core/tools 命令的操作目标 |
| **最后使用证据** | `af1bbd5` 2026-09-08 P15.1 |
| **是否应继续存在** | ✅ 是 |

**两个实例：**
- `projects/p151-2024a/`（13 文件）— P15.1 2024A B0 alignment baseline 项目
- `projects/rcs1-2024a/`（12 文件）— RC-S1 smoke 测试项目（16 波真实认知执行）

两个实例结构相同：inputs/ + state/（含 registry.json ~32KB, evidence_graph.json, decision_log.json, status.json, runs/）+ work/（handoff.md, state.json, STATE.md, time_budget.yaml）。

**核心发现：**
- 两个实例的 state/registry.json 大小完全相同（31981B），decision_log.json 相同（1671B），evidence_graph.json 相同（1733B）— rcs1 可能是 p151 的克隆或并行运行。
- 每个实例 work/ 下有 state.json + STATE.md 双状态文件，与 state/status.json 并存 — 历史遗留模式。

---

### 2.10 `research/` — Research / Experiment Artifact

| 属性 | 值 |
|---|---|
| **Purpose** | 研究实验（P13-3D 系列、P14、P15、RC-SMOKE）与 bench 运行残留 |
| **Owner layer** | Research / Benchmark |
| **被 import** | 部分 — test_non_regression_contract.py 引用 bench-m4-2000c 基线 |
| **被 test** | 是 — tests/e2e/test_research_runs.py, regression 基线 |
| **被 CLI 使用** | 部分 — P13/P14 脚本消费各自目录 |
| **最后使用证据** | `af1bbd5` 2026-09-08 P15.1 |
| **是否应继续存在** | ✅ 是 — 研究证据 ≠ 垃圾 |

**子目录分布：**

| 目录 | 文件数 | 阶段 | 状态 |
|---|---|---|---|
| `P13-3D/` | 106 | P13-3D 首轮 | ✅ 关闭（Negative but informative） |
| `P13-3D-R2/` | 130 | P13-3D R2 复现 | ✅ 冻结（仅 output + state） |
| `P13-3D-R3/` | 207 | P13-3D R3 真实 Writer 对照 | ✅ 关闭（R3_2_FINAL_REPORT.md） |
| `P14/` | 134 | P14 研究能力 pilot | ✅ PASS（21/21 replay match） |
| `P15/` | 14 | P15 CUMCM Benchmark 冻结 | 🟡 进行中（P15.1 baseline） |
| `RC-SMOKE/` | 4 | RC 冒烟测试 | ✅ S1/S3 PASS |
| `bench-m4-2000c/` | 24 | M4 方法 2000C 基准 | ⚠️ 历史残留（P4 迁移） |
| `bench-m4-2000c-p131-b/` | 14 | 变体基准 | ⚠️ 历史残留（无外部引用） |
| `bench-m4-2000c-p131-c/` | 14 | 变体基准 | ⚠️ 历史残留（无外部引用） |
| `bench-m4-2000c-p132-a/` | 13 | 变体基准 | ⚠️ 历史残留（无外部引用） |
| `bench-m4-2000c-p132-b/` | 14 | 变体基准 | ⚠️ 历史残留（无外部引用） |
| `bench-m4-2000c-p132-c/` | 14 | 变体基准 | ⚠️ 历史残留（无外部引用） |
| `bench-p132-2023c/` | 13 | 2023C 基准 | ⚠️ 历史残留（无外部引用） |

**核心发现：**
- P13-3D 系列（R1/R2/R3 共 443 文件）为已关闭实验的完整证据链（prompts + output + real_evaluation + golden_set + real_papers），**必须保留**。
- P14（134 文件）含 runs/P14-20260907-01/（124 文件）+ scripts/（4 文件）+ schemas/ + state/，为 pilot PASS 的完整证据。
- P15（14 文件）为进行中的 benchmark 冻结，含 CUMCM-Bench-v2.json（39.5KB）+ manifests + catalog + scripts。
- bench-m4-2000c* 系列（7 目录共 106 文件）为 P4 迁移时从 projects/ 移出的早期基准运行。仅 `bench-m4-2000c` 被 regression test 引用作为基线，其余 6 个变体目录无任何外部代码引用（Grep 确认仅自引用）。
- `P13-3D/inputs/` 为空目录（0 文件）。
- `P13-3D-R3/prompts/_tmp_*.txt`（12 文件）为临时 prompt 导出，无任何脚本引用（Grep 确认零引用）。

---

### 2.11 `tests/` — Test / Fixture / Reproducibility

| 属性 | 值 |
|---|---|
| **Purpose** | 单元/集成/端到端/回归测试 + fixtures |
| **Owner layer** | Test / Fixture |
| **被 import** | 是 — pytest 收集 |
| **被 test** | N/A（本身即测试） |
| **被 CLI 使用** | 是 — `py -3.12 -m pytest tests -q` |
| **被 CI / validation 使用** | 是 — 781 passed / 11 skipped 基线 |
| **最后使用证据** | `2ea318c` 2026-09-07 hardening(P5): Regression Gate |
| **是否应继续存在** | ✅ 是 |

**子目录：**

| 目录 | 测试文件数 | 说明 |
|---|---|---|
| `tests/unit/` | 50 | 单元测试（state, artifacts, evidence_graph, dag_engine, validators 等） |
| `tests/integration/` | 16 | 集成测试（cross_question, paper_intelligence, research_quality, red_team 等） |
| `tests/e2e/` | 2 | 端到端（pipeline, research_runs） |
| `tests/regression/` | 2 | 回归（non_regression_contract, v2_capability_regression） |
| `tests/compat/` | 1 | 多运行时兼容测试（V2 时代） |
| `tests/fixtures/` | 8 | 测试夹具（sample_problem, projects/, scaffolds/） |
| `tests/tests/` | 1 | ⚠️ 嵌套错误目录（fixtures/sample_problem.txt 18B 副本） |

**根级文件：**
- `tests/test_tex_to_docx_quick.py`（4207B）— ⚠️ 独立脚本，非 pytest 格式（无 `def test_`、无 pytest import、使用裸 assert + print），不会被 pytest 收集。
- `tests/conftest.py`（685B）— pytest 配置

**核心发现：**
- `tests/tests/fixtures/sample_problem.txt`（18B，内容"测试赛题内容"）与 `tests/fixtures/sample_problem.txt`（54B，内容"回归测试赛题：某物理系统的数学建模。"）为路径错误导致的嵌套重复目录。
- `tests/compat/test_runtime_compat.py`（11619B）为 V2 多运行时（Claude Code/Codex CLI/opencode/Cursor）兼容测试，引用 V2 状态文件规范。
- `__pycache__/` 目录未被 git 跟踪（.gitignore 生效），仅存在于磁盘。

---

### 2.12 工具配置目录

#### `.claude/`（101 files，tracked）

| 属性 | 值 |
|---|---|
| **Purpose** | Claude Code 本地 skills — 10 个 MWORKS Syslab 相关 skill |
| **Owner layer** | Tool-config |
| **被 import** | 间接 — catalog/external_skills.yaml 声明 syslab skill |
| **被 test** | 否 |
| **最后使用证据** | 随仓库提交 |
| **是否应继续存在** | ✅ 是 — MATLAB/北太天元交付分支的 skill 资产 |

含 syslab, syslab-app-designer, syslab-code-style, syslab-digital-filter-design, syslab-environment, syslab-julia-to-cpp, syslab-matlab-to-julia, syslab-mds-docs, syslab-performance-optimization, syslab-testing 共 10 个 skill。

#### `.github/`（1 file，tracked）

- `.github/copilot-instructions.md`（311B）— 与 `.clinerules`, `.cursorrules`, `.windsurfrules` 内容完全相同（指向 AGENTS.md 的指针文件）。

#### `.opencode/`（3671 files，仅 1 tracked）

| 属性 | 值 |
|---|---|
| **Purpose** | opencode 工具本地缓存 |
| **Owner layer** | Tool-config / Generated |
| **tracked 文件** | `.opencode/.gitignore`（63B） |
| **未跟踪** | `.opencode/node_modules/`（3667 files）+ package.json + package-lock.json |
| **是否应继续存在** | ⚠️ node_modules 可删除重建，.gitignore 应保留 |

#### `.trae/`（1 file，untracked）

- `.trae/documents/harness-consolidation-plan.md`（19904B）— Trae 编辑器生成的整合计划文档。

#### `.workbuddy/`（1 file，untracked, gitignored）

- `.workbuddy/memory/2026-09-07.md`（1344B）— WorkBuddy IDE 本地内存。

#### `.zcode/`（1 file，untracked）

- `.zcode/plans/plan-sess_2d77314d-*.md`（3310B）— Z 编辑器会话计划。

#### `node_modules/`（1 file，gitignored）

- `node_modules/.package-lock.json`（110B）— npm 内部锁文件残留。

---

### 2.13 根目录文件

| 文件 | 大小 | 分类 | 说明 |
|---|---|---|---|
| `AGENTS.md` | 8685B | A — Runtime | 执行协议真源（V3 认知工作流 + V2 兼容） |
| `catalog.yaml` | 17167B | A — Runtime | legacy hands 结构真源 |
| `README.md` | 9705B | A — Documentation | 公开门面（V3） |
| `CHANGELOG.md` | 4469B | A — Documentation | 版本变更记录 |
| `pyproject.toml` | 892B | A — Runtime | Python 项目配置 |
| `Dockerfile` | 1387B | A — Runtime | Docker 构建 |
| `docker-compose.yml` | 301B | A — Runtime | Docker Compose |
| `install.ps1` | 3993B | A — Runtime | Windows 安装脚本 |
| `install.sh` | 3974B | A — Runtime | Unix 安装脚本 |
| `.gitignore` | 874B | A — Runtime | 忽略规则 |
| `.dockerignore` | 245B | A — Runtime | Docker 忽略 |
| `.clinerules` | 311B | D — Tool-config | 与 .cursorrules/.windsurfrules/.github/copilot-instructions.md 四重复 |
| `.cursorrules` | 311B | D — Tool-config | 同上 |
| `.windsurfrules` | 311B | D — Tool-config | 同上 |
| `CLAUDE.md` | 384B | D — Tool-config | 与 GEMINI.md 二重复 |
| `GEMINI.md` | 384B | D — Tool-config | 同上 |
| `package.json` | 495B | D — Stale | V2 描述，无实际依赖，test 脚本为占位符 |
| `package-lock.json` | 205B | D — Generated | npm 锁文件（gitignored 规则存在但文件仍 tracked?） |

**注意：** `package-lock.json`（205B）在 git tracked 列表中，但 .gitignore 有 `package-lock.json` 规则。可能是在添加规则前已提交，需 `git rm --cached` 清理。

---

## 3. 重要文件分类（A/B/C/D 四分类）

### A — Runtime Source of Truth（运行时真源）

| 路径 | 说明 |
|---|---|
| `core/runtime/` | 认知工作流运行时（108 文件） |
| `core/tools/` | CLI 工具层（37 shim + 子目录实现，170 文件） |
| `core/validators/` | V3 校验器（evidence/modules/quality，35 文件） |
| `core/schemas/` | JSON Schema（15 份） |
| `core/workflows/` | DAG 定义（8 文件） |
| `core/roles/` | 五角色 YAML（5 文件） |
| `core/skills/` | critic skills（4 文件） |
| `core/env/` | 配置集中地（15 文件） |
| `core/knowledge/` | 知识层（404 文件，含 bench 语料） |
| `core/templates/` | LaTeX + matplotlib 模板（39 文件） |
| `catalog/` | V3 注册表（3 文件） |
| `catalog.yaml` | legacy 结构真源 |
| `AGENTS.md` | 执行协议 |
| `docs/STATUS.md` | 状态数字唯一出处 |
| `pyproject.toml` | Python 项目配置 |

### B — Research / Experiment Artifact（研究实验证据）

| 路径 | 说明 |
|---|---|
| `research/P13-3D/` | P13-3D 首轮实验（106 文件，含 fidelity 评估 + scripts） |
| `research/P13-3D-R2/` | R2 复现实验（130 文件，冻结 output） |
| `research/P13-3D-R3/` | R3 真实 Writer 对照（207 文件，含 prompts/golden_set/real_evaluation/real_papers） |
| `research/P14/` | P14 pilot（134 文件，21 实验全证据 + hash manifest） |
| `research/P15/` | P15 benchmark 冻结（14 文件，CUMCM-Bench-v2 + manifests） |
| `research/RC-SMOKE/` | RC 冒烟记录（4 文件，S1/S3 PASS 证据） |
| `docs/architecture/P13_*.md` | P13 系列研究报告 |
| `docs/architecture/RESEARCH_QUALITY_*.md` | 研究质量契约与报告 |
| `core/knowledge/bench/e2e/` | P13 实验固化语料（114 文件，10 真题三臂 artifact + 盲评矩阵） |

### C — Test / Fixture / Reproducibility Artifact（测试与可复现资产）

| 路径 | 说明 |
|---|---|
| `tests/unit/` | 50 个单元测试 |
| `tests/integration/` | 16 个集成测试 |
| `tests/e2e/` | 2 个端到端测试 |
| `tests/regression/` | 2 个回归测试（含五轴 non-regression 契约） |
| `tests/fixtures/` | 测试夹具（sample_problem, projects/, scaffolds/） |
| `tests/conftest.py` | pytest 配置 |
| `examples/problems/cumcm2024A.txt` | 题面 fixture |
| `research/bench-m4-2000c/` | regression 基线（e2e_metrics.json 被 test_non_regression_contract.py 消费） |
| `projects/rcs1-2024a/` | RC-S1 smoke 可复现实例 |
| `projects/p151-2024a/` | P15.1 baseline 可复现实例 |

### D — Historical / Deprecated / Candidate for Removal（历史/废弃/待评估）

| 路径 | 说明 | 建议动作 |
|---|---|---|
| `research/P13-3D-R3/prompts/_tmp_*.txt`（12 文件） | 临时 prompt 导出，零引用 | DELETE（见 DEBT-001） |
| `core/tools/run_p13_3d.py` | 破损 shim，目标文件不存在 | DELETE 或 FIX（见 DEBT-002） |
| `tests/tests/` | 嵌套错误目录 | DELETE（见 DEBT-003） |
| `docs/IMPROVEMENT_PLAN.md` | V2 时代文档，STATUS.md 明确不再维护 | ARCHIVE（见 DEBT-004） |
| `package.json` | V2 描述，无实际依赖 | DOCUMENT 或 DELETE（见 DEBT-005） |
| `docs/TEAM_GUIDE.md` | 引用 V2 四手结构 | UPDATE 或 ARCHIVE（见 DEBT-006） |
| `research/P13-3D/inputs/` | 空目录 | DELETE（见 DEBT-007） |
| `research/bench-m4-2000c/work/mc_scorecard_v2.json` | v2 重复评分卡 | DELETE（见 DEBT-008） |
| `.opencode/node_modules/` | 可重建依赖 | DELETE（本地清理，见 DEBT-009） |
| `node_modules/` | gitignored 残留 | DELETE（本地清理，见 DEBT-010） |
| `adapters/openai.yaml` | 自动生成，内容含 V2 术语 | REGENERATE（见 DEBT-011） |
| `research/bench-m4-2000c-p131-b/c`（2 目录） | 变体基准，无外部引用 | ARCHIVE（见 DEBT-012） |
| `research/bench-m4-2000c-p132-a/b/c`（3 目录） | 变体基准，无外部引用 | ARCHIVE（见 DEBT-012） |
| `research/bench-p132-2023c/` | 变体基准，无外部引用 | ARCHIVE（见 DEBT-012） |
| `.trae/`, `.zcode/` | 未跟踪编辑器元数据 | 加入 .gitignore（见 DEBT-013） |
| `.clinerules` + `.cursorrules` + `.windsurfrules` + `.github/copilot-instructions.md` | 四重复 311B 指针 | MERGE（见 DEBT-014） |
| `CLAUDE.md` + `GEMINI.md` | 二重复 384B 指针 | MERGE（见 DEBT-015） |
| `tests/test_tex_to_docx_quick.py` | 非 pytest 独立脚本 | CONVERT 或 MOVE（见 DEBT-016） |
| `docs/decisions/2026-09-04-refactor-plan-v2.md` | 已完成重构计划 | ARCHIVE（见 DEBT-017） |
| `archives/cumcm2024anew/work/state.json` + `STATE.md` | 与 state/status.json 三状态并存 | DOCUMENT（见 DEBT-020） |
| `docs/integration/harness-compat.md` | 引用 V2 四手契约 | UPDATE（见 DEBT-021） |

---

## 4. 重复实现检测

### 4.1 同名/近同名文件

| 模式 | 实例 | 性质 |
|---|---|---|
| `sample_problem.txt` | `tests/fixtures/`（54B）vs `tests/tests/fixtures/`（18B） | ❌ 路径错误导致的嵌套重复，内容不同 |
| `cumcm2024A.txt` / `problem_cumcm2024A.txt` | `examples/` + `projects/p151-2024a/inputs/` + `archives/cumcm2024anew/inputs/` | ✅ 同一份题面的三处合法副本（fixture / instance / archive） |
| `mc_scorecard.json` + `mc_scorecard_v2.json` | `research/bench-m4-2000c/work/` | ⚠️ v2 后缀重复，需确认是否 superseded |
| `state.json` + `STATE.md` + `status.json` | `archives/cumcm2024anew/work/` + `projects/*/work/` | ⚠️ 历史双真源模式，V3 已收口到 state/status.json |
| `ARM_B0.json` x10, `ARM_B1.json` x10, `ARM_MMA.json` x10 | `core/knowledge/bench/e2e/artifacts/<year>_<letter>/` | ✅ 按题目分目录的正常结构 |
| `X.json` x12, `Y.json` x12, `Z.json` x12 | `core/knowledge/bench/e2e/artifacts/<year>_<letter>/blind/` | ✅ 盲评矩阵按题目分目录 |
| `INDEX.md` x4 | methodology/, paper-cases/, playbooks/, problems/ | ✅ 每目录标准索引 |
| `README.md` x3 | paper-cases/, problems/, _negative/ | ✅ 每目录标准说明 |

### 4.2 逻辑重复

| 重复对 | 说明 |
|---|---|
| `core/tools/*.py`（37 shim）vs `core/tools/<subdir>/*.py`（实现） | 兼容 shim 模式，非真正重复，P4 重构产物 |
| `core/evaluation/scoring/` vs `core/tools/evaluation/` | V3 前向兼容包 vs 实际实现，评分逻辑仅一份在 tools/ |
| `core/validators/` vs `core/tools/validation/` | 两套校验器并存：validators/ 为 V3 模块化实现（evidence_gate, modules 21 项, quality），tools/validation/ 为 CLI 入口（gate.py 38KB, validate.py 76KB）。存在功能重叠风险。 |
| `core/legacy/hands/*/knowledge/` vs `core/knowledge/` | V2 知识模板 vs V3 知识层，内容不重叠（legacy 为代码/论文模板，V3 为方法卡/论文案例） |
| `core/legacy/hands/*/templates/` vs `core/templates/` | V2 SPEC 模板（MODEL_SPEC_TEMPLATE.md 等）vs V3 LaTeX/matplotlib 模板，不重叠 |

---

## 5. 临时文件 / Migration 残留检测

Grep 模式 `_old|_new|_v2|_v3|_final|_bak|backup|_tmp|_temp|_draft` 结果（排除 .git/.opencode/node_modules/.pytest_cache）：

### 5.1 真正的临时文件

| 文件 | 大小 | 说明 |
|---|---|---|
| `research/P13-3D-R3/prompts/_tmp_B0_W0_system.txt` | 908B | 临时 prompt 导出 |
| `research/P13-3D-R3/prompts/_tmp_B0_W0_user.txt` | 2565B | 同上 |
| `research/P13-3D-R3/prompts/_tmp_B0_W1_system.txt` | 1109B | 同上 |
| `research/P13-3D-R3/prompts/_tmp_B0_W1_user.txt` | 7613B | 同上 |
| `research/P13-3D-R3/prompts/_tmp_B1_F_W0_system.txt` | 908B | 同上 |
| `research/P13-3D-R3/prompts/_tmp_B1_F_W0_user.txt` | 5235B | 同上 |
| `research/P13-3D-R3/prompts/_tmp_B1_F_W1_system.txt` | 1109B | 同上 |
| `research/P13-3D-R3/prompts/_tmp_B1_F_W1_user.txt` | 15071B | 同上 |
| `research/P13-3D-R3/prompts/_tmp_MMA_W0_system.txt` | 908B | 同上 |
| `research/P13-3D-R3/prompts/_tmp_MMA_W0_user.txt` | 2584B | 同上 |
| `research/P13-3D-R3/prompts/_tmp_MMA_W1_system.txt` | 1109B | 同上 |
| `research/P13-3D-R3/prompts/_tmp_MMA_W1_user.txt` | 8208B | 同上 |

**以上 12 个文件 Grep 全仓库零引用**，确认为实验过程中的临时导出残留。

### 5.2 含 v2/v3/final 但非临时的文件

| 文件 | 说明 | 非临时原因 |
|---|---|---|
| `research/bench-m4-2000c/work/mc_scorecard_v2.json` | 评分卡 v2 | 可能为 superseded 版本，需确认 |
| `research/P13-3D/output/fidelity/*_v2.json`（10 文件） | fidelity 评估 v2 | P13-3D 实验的版本化评估输出，有研究价值 |
| `research/P13-3D/scripts/run_fidelity_gate_v2.py` | fidelity gate v2 脚本 | 实验脚本 |
| `research/P13-3D-R3/real_evaluation/R3_2_FINAL_REPORT.md` | 最终报告 | "FINAL" 为报告命名，非临时 |
| `research/P14/scripts/p14_finalize_hashes.py` | hash 终结脚本 | P14 实验流程的一部分 |
| `docs/architecture/V3_FINAL_AUDIT.md` | V3 最终审计 | 正式文档 |
| `tests/regression/test_v2_capability_regression.py` | V2 能力回归测试 | 正式测试 |
| `tests/unit/test_state_v3.py` | V3 状态测试 | 正式测试 |
| `docs/decisions/2026-09-04-refactor-plan-v2.md` | 重构计划 v2 | 正式决策文档 |
| `core/legacy/hands/*/templates/*_TEMPLATE.md` | 模板文件 | "TEMPLATE" 为命名惯例 |

### 5.3 空目录

| 路径 | 说明 |
|---|---|
| `research/P13-3D/inputs/` | 0 文件，实验输入未使用或已迁移 |
| `research/P13-3D-R3/.workbuddy/` | 0 文件，编辑器残留 |

---

## 6. 关键统计汇总

| 指标 | 值 |
|---|---|
| Runtime 源码（core/ 排除 legacy） | ~820 文件 |
| V2 Legacy 兼容层 | 283 文件（25.7% of core/） |
| 研究实验证据（research/ 排除 bench-m4 残留） | ~595 文件 |
| bench-m4 历史残留（7 目录） | 106 文件 |
| 测试代码（tests/ 排除 pycache） | ~80 .py 文件 |
| 测试 fixtures | 9 文件 |
| 文档（docs/） | 57 文件 |
| 自动生成文件 | adapters/openai.yaml, docs/METRICS.md |
| 破损 shim | 1（run_p13_3d.py） |
| 确认零引用临时文件 | 12（P13-3D-R3 _tmp_*.txt） |
| 嵌套错误目录 | 1（tests/tests/） |
| 四重复工具配置 | 4 文件（.clinerules/.cursorrules/.windsurfrules/.github/copilot-instructions.md） |
| 二重复工具配置 | 2 文件（CLAUDE.md/GEMINI.md） |
| 未跟踪编辑器目录 | 2（.trae/, .zcode/） |
| gitignored 但磁盘存在 | node_modules/, .pytest_cache/, .workbuddy/ |

---

*报告生成时间：2026-09-08 | 审计员：Repository Inventory & Debt Ledger Auditor | 下一份：02_DEBT_LEDGER.md*
