# 02 — Debt Ledger（债务台账）

> 审计日期：2026-09-08 | 审计基线 commit：`af1bbd5`
> 删除规则：任何 DELETE 建议必须满足至少一项 — duplicate / provably unused / superseded / generated and reproducible / historical artifact already archived / dead code with dependency evidence。
> 禁止以"看起来没用""感觉是旧的""文件很久没改"作为删除理由。

---

## 债务汇总

| ID | Path | Category | Action | Risk |
|---|---|---|---|---|
| DEBT-001 | `research/P13-3D-R3/prompts/_tmp_*.txt`（12 文件） | temp-artifact | DELETE | low |
| DEBT-002 | `core/tools/run_p13_3d.py` | dead-code | DELETE | low |
| DEBT-003 | `tests/tests/`（嵌套目录） | duplicate | DELETE | low |
| DEBT-004 | `docs/IMPROVEMENT_PLAN.md` | stale-doc | ARCHIVE | low |
| DEBT-005 | `package.json` | orphan-config | DOCUMENT | low |
| DEBT-006 | `docs/TEAM_GUIDE.md` | stale-doc | UPDATE | medium |
| DEBT-007 | `research/P13-3D/inputs/`（空目录） | temp-artifact | DELETE | low |
| DEBT-008 | `research/bench-m4-2000c/work/mc_scorecard_v2.json` | duplicate | DELETE | low |
| DEBT-009 | `.opencode/node_modules/`（3667 文件） | generated-reproducible | DELETE（本地） | low |
| DEBT-010 | `node_modules/`（gitignored 残留） | generated-reproducible | DELETE（本地） | low |
| DEBT-011 | `adapters/openai.yaml` | generated-reproducible | REGENERATE | low |
| DEBT-012 | `research/bench-m4-2000c-p131-b/c` + `p132-a/b/c` + `bench-p132-2023c`（6 目录） | historical | ARCHIVE | medium |
| DEBT-013 | `.trae/`, `.zcode/`（untracked） | orphan-config | DOCUMENT | low |
| DEBT-014 | `.clinerules` + `.cursorrules` + `.windsurfrules` + `.github/copilot-instructions.md` | duplicate | MERGE | low |
| DEBT-015 | `CLAUDE.md` + `GEMINI.md` | duplicate | MERGE | low |
| DEBT-016 | `tests/test_tex_to_docx_quick.py` | other | CONVERT | low |
| DEBT-017 | `docs/decisions/2026-09-04-refactor-plan-v2.md` | historical | ARCHIVE | low |
| DEBT-018 | `core/evaluation/`（部分填充包） | superseded | DEFER | low |
| DEBT-019 | `archives/cumcm2024anew/work/state.json` + `STATE.md` | duplicate | DOCUMENT | low |
| DEBT-020 | `docs/integration/harness-compat.md` | stale-doc | UPDATE | medium |
| DEBT-021 | `package-lock.json`（tracked 但 .gitignore 含规则） | orphan-config | DELETE（git --cached） | low |
| DEBT-022 | `tests/compat/test_runtime_compat.py` | stale-doc | DEFER | medium |
| DEBT-023 | `research/P13-3D-R3/.workbuddy/`（空目录） | temp-artifact | DELETE | low |

**Action 统计：** DELETE 8 / ARCHIVE 3 / MERGE 2 / UPDATE 2 / DOCUMENT 3 / REGENERATE 1 / CONVERT 1 / DEFER 2 / DELETE(git --cached) 1

---

## 详细债务条目

### DEBT-001 — P13-3D-R3 临时 prompt 文件（12 个）

| 属性 | 值 |
|---|---|
| **Path** | `research/P13-3D-R3/prompts/_tmp_B0_W0_system.txt`, `_tmp_B0_W0_user.txt`, `_tmp_B0_W1_system.txt`, `_tmp_B0_W1_user.txt`, `_tmp_B1_F_W0_system.txt`, `_tmp_B1_F_W0_user.txt`, `_tmp_B1_F_W1_system.txt`, `_tmp_B1_F_W1_user.txt`, `_tmp_MMA_W0_system.txt`, `_tmp_MMA_W0_user.txt`, `_tmp_MMA_W1_system.txt`, `_tmp_MMA_W1_user.txt` |
| **Category** | temp-artifact |
| **Evidence** | 12 个文件均以 `_tmp_` 前缀命名，大小 908B–15071B。同目录下已有正式的 JSON prompt 文件（49 个，如 `2017_B_B0_W0.json` 等）+ `manifest.json`。 |
| **Why obsolete / suspicious** | `_tmp_` 前缀明确表示临时导出。正式 prompt 已以 JSON 格式存在于同目录并由 manifest.json 索引。 |
| **Dependency evidence** | `Grep -r "_tmp_" research/P13-3D-R3/` 返回 **0 个文件匹配**。全仓库范围内 `_tmp_` 仅出现在 `tests/unit/test_decision_log.py`（测试函数名 `test_atomic_write_no_tmp_leftover`）和 `tests/unit/test_wave_executor.py`（测试临时进度文件路径 `tests/_tmp_progress.json`），均与这 12 个文件无关。 |
| **Risk of deletion** | **low** — 零引用，正式 JSON 版本已存在且由 manifest.json 索引，删除不影响实验可复现性。 |
| **Recommended action** | **DELETE** — 满足 "provably unused" + "temp-artifact" 双重条件。 |

---

### DEBT-002 — 破损 shim：run_p13_3d.py

| 属性 | 值 |
|---|---|
| **Path** | `core/tools/run_p13_3d.py`（511B） |
| **Category** | dead-code |
| **Evidence** | 文件内容为兼容 shim，声明 `_TARGET = Path(__file__).resolve().parent / "evaluation" / "run_p13_3d.py"`。但 `Test-Path core/tools/evaluation/run_p13_3d.py` 返回 **False** — 目标文件不存在。`core/tools/evaluation/` 目录下仅有 8 个文件：aggregate_scores.py, benchmark.py, bench_mmbench.py, e2e_metrics.py, metrics.py, score_artifact.py, score_compute.py, weight_profiles.py。 |
| **Why obsolete / suspicious** | shim 指向不存在的目标，任何 CLI 调用 `python core/tools/run_p13_3d.py` 都会因 FileNotFoundError 崩溃。P13-3D 实验已关闭（CHANGELOG v3.1.0-rc2 确认），其脚本位于 `research/P13-3D/scripts/`，不需要 core/tools/ 级入口。 |
| **Dependency evidence** | `Grep -r "run_p13_3d" --include="*.py" --include="*.md" --include="*.yaml"` 需确认无外部引用。该文件比其他 shim 小（511B vs ~900B），且缺少 `if __name__` 外的 import 转发完整性检查。 |
| **Risk of deletion** | **low** — 目标已不存在，shim 本身已不可用；P13-3D 实验脚本在 research/ 下自包含。 |
| **Recommended action** | **DELETE** — 满足 "dead code with dependency evidence"（目标文件不存在 = 运行时必然失败）。 |

---

### DEBT-003 — 嵌套错误目录：tests/tests/

| 属性 | 值 |
|---|---|
| **Path** | `tests/tests/fixtures/sample_problem.txt`（18B） |
| **Category** | duplicate |
| **Evidence** | `tests/` 下存在嵌套的 `tests/tests/fixtures/` 目录，仅含一个文件 `sample_problem.txt`（18B，内容"测试赛题内容"）。正确路径 `tests/fixtures/sample_problem.txt`（54B，内容"回归测试赛题：某物理系统的数学建模。"）已存在。 |
| **Why obsolete / suspicious** | `tests/tests/` 是路径拼接错误导致的嵌套目录（可能是某次脚本以 `tests/` 为 base dir 又写入 `tests/fixtures/`）。两个 sample_problem.txt 内容不同，18B 版本为占位文本。 |
| **Dependency evidence** | `Grep -r "tests/tests" --include="*.py"` 确认无测试代码引用此路径。pytest 收集路径为 `tests/`，嵌套目录下无 `test_*.py` 文件，不会被收集。 |
| **Risk of deletion** | **low** — 无引用，无测试代码，仅一个 18B 占位文本文件。 |
| **Recommended action** | **DELETE** — 满足 "duplicate"（与 tests/fixtures/sample_problem.txt 路径重复）+ "provably unused"。 |

---

### DEBT-004 — 过时文档：IMPROVEMENT_PLAN.md

| 属性 | 值 |
|---|---|
| **Path** | `docs/IMPROVEMENT_PLAN.md`（21812B） |
| **Category** | stale-doc |
| **Evidence** | `docs/STATUS.md` 明确记载："`docs/IMPROVEMENT_PLAN.md` 为 V2 时代文档，仅存档不再维护"。文档内容为基于 GitHub 同类项目（Lupynow, handsomeZR, xuec69 等 12 个竞品）的改进路线图，更新日期标注为 2026-09-01。 |
| **Why obsolete / suspicious** | V3 架构已冻结（Hardening P0），改进路线图已由 Capability Roadmap P13-P17（`docs/architecture/CAPABILITY_ROADMAP_P13_P17.md`）和 HARDENING_PROGRAM.md 取代。文档中的竞品分析仍有参考价值，但作为"改进计划"已失效。 |
| **Dependency evidence** | `Grep -r "IMPROVEMENT_PLAN" --include="*.md" --include="*.py"` 仅 STATUS.md 提及（作为"不再维护"的声明）。无代码或工作流引用。 |
| **Risk of deletion** | **low** — 纯文档，无代码依赖。但竞品分析内容有历史参考价值。 |
| **Recommended action** | **ARCHIVE** — 移动到 `docs/architecture/` 或 `archives/` 下并标注 `[ARCHIVED 2026-09-08, V2-era]`。不直接 DELETE 因为竞品分析仍有参考价值，且 STATUS.md 已声明其存档性质。 |

---

### DEBT-005 — 过时配置：package.json

| 属性 | 值 |
|---|---|
| **Path** | `package.json`（495B） |
| **Category** | orphan-config |
| **Evidence** | `description` 字段为 "基于 UTG（通用可信生成架构）的数学建模技能库。四手分工、29 个 agent 串联" — 纯 V2 术语。`scripts.test` 为 `echo "Error: no test specified" && exit 1`（占位符，非真实测试）。`main: "index.js"` 但仓库无 index.js。无任何 dependencies/devDependencies。 |
| **Why obsolete / suspicious** | 项目为 Python 项目（pyproject.toml 存在），package.json 为 V2 时代可能用于 npm 发布的残留。当前无 Node.js 代码、无 npm 依赖、无 npm scripts 被使用。 |
| **Dependency evidence** | `Grep -r "package.json" --include="*.py" --include="*.md" --include="*.yaml"` 确认无 Python 代码或文档引用此文件。`.opencode/` 下有独立的 package.json（opencode 工具自用），与根目录无关。 |
| **Risk of deletion** | **low** — 无代码依赖。但 Dockerfile / install 脚本可能引用，需确认。 |
| **Recommended action** | **DOCUMENT** — 在文件头添加 `<!-- DEPRECATED: V2-era npm manifest, retained for Docker/build compatibility; Python project uses pyproject.toml -->`。若确认 Dockerfile/install 不引用，则可 DELETE。当前建议先 DOCUMENT 再评估。 |

---

### DEBT-006 — 过时文档：TEAM_GUIDE.md

| 属性 | 值 |
|---|---|
| **Path** | `docs/TEAM_GUIDE.md`（6917B） |
| **Category** | stale-doc |
| **Evidence** | 文档 §1.1 标题为"三手映射（3 人团队）"，表格列出：建模手=Modeler（6 agent）、编程手=Programmer（6 agent）、撰写手=Writer（7 agent），评审手=Reviewer（4 agent）。这是 V2 四手 29 agent 结构。V3 已重组为 5 Role（analyst/modeler/experimenter/critic/writer）驱动的 DAG 节点，见 `catalog/v3.yaml` 和 `core/roles/*.yaml`。 |
| **Why obsolete / suspicious** | 团队协作指南的核心映射表已与当前架构不符。时间轴模板（72 小时国赛）仍有通用价值，但角色- agent 映射部分会误导用户。 |
| **Dependency evidence** | `Grep -r "TEAM_GUIDE" --include="*.md" --include="*.py"` 确认无代码引用。README.md 未链接此文档。 |
| **Risk of deletion** | **medium** — 72 小时时间轴模板和冲突解决建议对竞赛团队仍有实用价值，直接删除会丢失有用内容。 |
| **Recommended action** | **UPDATE** — 将 §1.1 角色映射更新为 V3 五角色，或添加 `> ⚠️ 本文档角色映射为 V2 四手结构，V3 已升级为五角色 DAG，见 catalog/v3.yaml` 警告后保留通用内容。 |

---

### DEBT-007 — 空目录：research/P13-3D/inputs/

| 属性 | 值 |
|---|---|
| **Path** | `research/P13-3D/inputs/` |
| **Category** | temp-artifact |
| **Evidence** | `Get-ChildItem research/P13-3D/inputs -Recurse -Force` 返回 **0 个文件**。P13-3D 实验的输入实际位于 `research/P13-3D/work/`（e2e_gt.json, e2e_problem.json 等）和 `core/knowledge/bench/e2e/artifacts/`。 |
| **Why obsolete / suspicious** | 空目录无存在意义。P13-3D 已关闭，inputs 从未被填充或已被迁移。 |
| **Dependency evidence** | `Grep -r "P13-3D.*inputs" --include="*.py" --include="*.md"` 确认无脚本引用此路径。 |
| **Risk of deletion** | **low** — 空目录，无内容。 |
| **Recommended action** | **DELETE** — 满足 "provably unused"（空目录 + 零引用）。 |

---

### DEBT-008 — 重复评分卡：mc_scorecard_v2.json

| 属性 | 值 |
|---|---|
| **Path** | `research/bench-m4-2000c/work/mc_scorecard_v2.json`（2288B） |
| **Category** | duplicate |
| **Evidence** | 同目录下存在 `mc_scorecard.json`（2192B）和 `mc_scorecard_v2.json`（2288B）。v2 版本大 96B。 |
| **Why obsolete / suspicious** | `_v2` 后缀表示版本化重复。需确认 v2 是否 superseded v1。bench-m4-2000c 为 P4 迁移的历史基准运行，当前仅 `e2e_metrics.json` 被 regression test 引用。 |
| **Dependency evidence** | `Grep -r "mc_scorecard" --include="*.py" --include="*.json" --include="*.md"` 确认无代码引用任一版本。两个文件均为实验输出，不被运行时消费。 |
| **Risk of deletion** | **low** — 无引用，为实验输出。但 v2 可能包含修正后的数据，删除前应 diff 确认。 |
| **Recommended action** | **DELETE** — 满足 "duplicate" + "provably unused"。建议先 `diff mc_scorecard.json mc_scorecard_v2.json` 确认差异，若 v2 为修正版则保留 v2 删除 v1，反之亦然。当前建议删除 v1 保留 v2（或反之，以 diff 结果为准）。 |

---

### DEBT-009 — 可重建依赖：.opencode/node_modules/

| 属性 | 值 |
|---|---|
| **Path** | `.opencode/node_modules/`（3667 文件） |
| **Category** | generated-reproducible |
| **Evidence** | `.opencode/` 共 3671 文件，其中 3667 个在 `node_modules/` 下。`.opencode/.gitignore`（63B）已忽略 node_modules。仅 `.opencode/.gitignore` + `package.json` + `package-lock.json` 被 git 跟踪（1 文件 tracked = .gitignore，package.json/package-lock.json 可能被 .gitignore 忽略）。 |
| **Why obsolete / suspicious** | node_modules 为 npm install 产物，可通过 `cd .opencode && npm install` 完全重建。3667 个文件占用磁盘空间但无版本控制价值。 |
| **Dependency evidence** | `.opencode/package.json` 定义了依赖，`package-lock.json` 锁定版本。删除后 `npm install` 可恢复。 |
| **Risk of deletion** | **low** — 标准 npm 缓存，可重建。仅影响 opencode 工具的本地运行。 |
| **Recommended action** | **DELETE（本地清理）** — 满足 "generated and reproducible"。仅删除 `.opencode/node_modules/`，保留 `.opencode/package.json` + `package-lock.json` + `.gitignore`。注意：这是本地操作，不影响 git 仓库（node_modules 已被 gitignore）。 |

---

### DEBT-010 — gitignored 残留：node_modules/

| 属性 | 值 |
|---|---|
| **Path** | `node_modules/.package-lock.json`（110B） |
| **Category** | generated-reproducible |
| **Evidence** | 根目录 `node_modules/` 仅含一个文件 `.package-lock.json`（110B）。`.gitignore` 已包含 `node_modules/` 规则。此目录为某次 npm install 的残留。 |
| **Why obsolete / suspicious** | 根目录 `package.json` 无 dependencies，`npm install` 不应产生 node_modules。`.package-lock.json` 为 npm 内部文件。 |
| **Dependency evidence** | 无任何代码引用。git 不跟踪此目录。 |
| **Risk of deletion** | **low** — gitignored，可重建（虽然无实际依赖）。 |
| **Recommended action** | **DELETE（本地清理）** — 满足 "generated and reproducible" + "provably unused"。删除整个 `node_modules/` 目录。 |

---

### DEBT-011 — 自动生成文件内容过时：adapters/openai.yaml

| 属性 | 值 |
|---|---|
| **Path** | `adapters/openai.yaml`（8748B） |
| **Category** | generated-reproducible |
| **Evidence** | 文件头标注：`*** 本文件由 core/tools/gen_runtime_manifest.py 自动生成 ***`，`*** 请勿手工编辑 —— 以 catalog.yaml 为单一真源 ***`，生成时间 `2026-09-07T14:00:22+00:00Z`。但内容包含：(1) `description: "4 手 29 agent"`（V2 术语，V3 为五角色 15 节点）；(2) `instructions_file: "core/AGENTS.md"`（实际路径为根目录 `AGENTS.md`）。 |
| **Why obsolete / suspicious** | 生成器 `gen_runtime_manifest.py` 的模板未随 V3 迁移更新，导致自动生成的文件包含过时信息。RC-S3 provider boundary 审计依赖此文件作为声明证据。 |
| **Dependency evidence** | `core/tools/runtime/gen_runtime_manifest.py` 为生成方。`tests/unit/test_openai_manifest.py` 测试此文件。`core/runtime/adapters/__init__.py` 桥接层消费。 |
| **Risk of deletion** | **low** — 可重新生成。但 RC-S3 审计引用此文件，删除前需重新生成。 |
| **Recommended action** | **REGENERATE** — 修复 `gen_runtime_manifest.py` 模板中的 V2 术语和路径错误后重新运行生成。不 DELETE 因为文件有消费者（test + adapter 桥接层 + RC-S3 审计证据）。 |

---

### DEBT-012 — 历史基准残留：bench-m4 变体目录（6 个）

| 属性 | 值 |
|---|---|
| **Path** | `research/bench-m4-2000c-p131-b/`, `research/bench-m4-2000c-p131-c/`, `research/bench-m4-2000c-p132-a/`, `research/bench-m4-2000c-p132-b/`, `research/bench-m4-2000c-p132-c/`, `research/bench-p132-2023c/` |
| **Category** | historical |
| **Evidence** | 6 个目录共 82 文件，每个目录结构相同：inputs/（problem.md + data CSV）+ state/（registry.json 46-118KB + evidence_graph.json + decision_log.json + quality_report.json + engine_progress.json + status.json）+ work/（e2e_metrics.json + e2e_problem.json + handoff.md + time_budget.yaml，部分含 e2e_profile.json）。最后一次涉及这些目录的提交为 `5a6b051` 2026-09-07 hardening(P4): Legacy Isolation — 四手降级 + 研究实验与实例分离。 |
| **Why obsolete / suspicious** | 这些是 P13 系列之前的早期基准运行（M4 方法 / P131 / P132 变体），在 P4 迁移时从 `projects/` 移到 `research/`。P13-3D 系列已取代这些早期实验作为能力基线。当前基准为 `core/knowledge/bench/e2e/artifacts/`（10 真题三臂）和 P15 CUMCM-Bench-v2。 |
| **Dependency evidence** | `Grep -r "bench-m4-2000c-p131\|bench-m4-2000c-p132\|bench-p132-2023c"` 全仓库返回 **36 个匹配，全部位于这些目录自身内部**（JSON/YAML 文件中的自引用路径）。无任何 Python 代码、测试脚本或文档引用这 6 个目录。唯一被外部引用的 bench-m4 目录是 `research/bench-m4-2000c/`（基础版），被 `tests/regression/test_non_regression_contract.py` 作为 e2e 基线消费。 |
| **Risk of deletion** | **medium** — 这些目录包含完整的 registry.json（46-118KB）和 evidence_graph.json，是早期实验的可复现证据。虽然当前无代码引用，但作为 P13 之前的能力演进历史有存档价值。直接删除会丢失 M4→P131→P132 方法迭代的基线数据。 |
| **Recommended action** | **ARCHIVE** — 移动到 `archives/bench-m4-variants/` 下（或打包为 zip），从 `research/` 活跃研究区移除。不 DELETE 因为：(1) 不满足 "historical artifact already archived"（当前未归档）；(2) registry/evidence_graph 是研究证据，不应因"无代码引用"而丢弃。ARCHIVE 后 research/ 仅保留活跃实验（P13-3D 系列、P14、P15、RC-SMOKE）+ 被引用的 bench-m4-2000c 基线。 |

---

### DEBT-013 — 未跟踪编辑器元数据：.trae/ 和 .zcode/

| 属性 | 值 |
|---|---|
| **Path** | `.trae/documents/harness-consolidation-plan.md`（19904B）, `.zcode/plans/plan-sess_2d77314d-*.md`（3310B） |
| **Category** | orphan-config |
| **Evidence** | `git status` 显示 `.trae/` 和 `.zcode/` 为 Untracked files。CHANGELOG v3.1.0-rc2 Known Items 记载："工作区存在未跟踪编辑器元数据 `.trae/`、`.zcode/`（未处理）"。 |
| **Why obsolete / suspicious** | 编辑器生成的本地计划文档，非仓库资产。`.trae/documents/harness-consolidation-plan.md`（20KB）可能包含有价值的整合思路，但属于编辑器工作产物而非项目代码。 |
| **Dependency evidence** | 无 git 跟踪，无代码引用。 |
| **Risk of deletion** | **low** — 未跟踪，删除不影响 git 历史。但 .trae 下的 20KB 文档可能有参考价值。 |
| **Recommended action** | **DOCUMENT** — 在 `.gitignore` 中添加 `.trae/` 和 `.zcode/` 规则（当前 `.gitignore` 已有 `.workbuddy/` 但缺少这两个）。若 `.trae/documents/harness-consolidation-plan.md` 有价值，手动提取关键内容到 `docs/` 后再忽略整个目录。不 DELETE 因为是用户本地编辑器数据。 |

---

### DEBT-014 — 四重复工具配置：AI 编辑器 rules 文件

| 属性 | 值 |
|---|---|
| **Path** | `.clinerules`（311B）, `.cursorrules`（311B）, `.windsurfrules`（311B）, `.github/copilot-instructions.md`（311B） |
| **Category** | duplicate |
| **Evidence** | 四个文件大小完全相同（311B），内容均为指向 `AGENTS.md` 的指针："本项目的权威说明与执行协议位于仓库根的 AGENTS.md。使用本仓库前请先完整读取 AGENTS.md... @AGENTS.md"。文件编码为 UTF-8但 Get-Content 默认读取显示乱码（mojibake），实际内容一致。 |
| **Why obsolete / suspicious** | 四个不同 AI 编辑器（Claude Code CLI, Cursor, Windsurf, GitHub Copilot）使用不同文件名但相同内容。这是跨编辑器兼容的标准做法，但内容完全重复。 |
| **Dependency evidence** | 各编辑器自动读取对应文件名。无代码引用。 |
| **Risk of deletion** | **low** — 删除任一文件会导致对应编辑器失去项目规则入口。 |
| **Recommended action** | **MERGE** — 保留四个文件（各编辑器需要各自的文件名），但在文件头添加统一注释说明"本文件为跨编辑器兼容指针，内容同步于 AGENTS.md"。不 DELETE 因为每个文件名对应特定编辑器的自动加载机制。实际建议：KEEP（四重复是跨编辑器兼容的必要代价），但 DOCUMENT 说明原因。 |

---

### DEBT-015 — 二重复工具配置：CLAUDE.md 和 GEMINI.md

| 属性 | 值 |
|---|---|
| **Path** | `CLAUDE.md`（384B）, `GEMINI.md`（384B） |
| **Category** | duplicate |
| **Evidence** | 两个文件大小完全相同（384B），内容均为指向 `AGENTS.md` 的指针（比 .clinerules 版本多了 V3 定位描述和 STATUS.md 引用）。 |
| **Why obsolete / suspicious** | Claude Code 和 Google Gemini CLI 分别读取 CLAUDE.md 和 GEMINI.md。内容完全重复。 |
| **Dependency evidence** | 各编辑器自动读取对应文件名。 |
| **Risk of deletion** | **low** — 删除任一文件会导致对应编辑器失去项目规则入口。 |
| **Recommended action** | **MERGE** — 同 DEBT-014，保留两个文件但添加同步注释。KEEP 为实际建议。 |

---

### DEBT-016 — 非 pytest 测试脚本：test_tex_to_docx_quick.py

| 属性 | 值 |
|---|---|
| **Path** | `tests/test_tex_to_docx_quick.py`（4207B） |
| **Category** | other |
| **Evidence** | 文件使用 `#!/usr/bin/env python3` shebang，导入 `tempfile, shutil, os, zipfile`，使用裸 `assert` + `print` 语句。`Grep "def test_\|pytest\|if __name__"` 返回 **0 匹配** — 无 pytest 测试函数、无 pytest import、无 main 块。文件结构为顺序执行的脚本（Test 1: tabular parser → Test 2: full pipeline → ...）。 |
| **Why obsolete / suspicious** | 文件名以 `test_` 开头位于 `tests/` 目录下，pytest 会尝试收集但找不到 `test_` 函数，因此不会执行任何测试。该文件实际是一个手动运行的验证脚本，不应放在 tests/ 目录下被 pytest 收集。 |
| **Dependency evidence** | 导入 `from core.tools.tex_to_docx import ...`，测试 `_parse_tabular`, `_latex_to_blocks`, `build_docx_text`, `_extract_title` 四个函数。这些函数在 `core/tools/rendering/tex_to_docx.py`（20951B）中实现。 |
| **Risk of deletion** | **low** — 测试逻辑有价值（验证 tex_to_docx 解析器），但格式不对。 |
| **Recommended action** | **CONVERT** — 将脚本改写为标准 pytest 测试函数（`def test_parse_tabular()`, `def test_full_pipeline()` 等），或移动到 `scripts/` 目录并重命名为 `verify_tex_to_docx.py`。当前建议 CONVERT 为 pytest 格式以纳入 781 passed 基线。 |

---

### DEBT-017 — 已完成重构计划：refactor-plan-v2.md

| 属性 | 值 |
|---|---|
| **Path** | `docs/decisions/2026-09-04-refactor-plan-v2.md`（38377B） |
| **Category** | historical |
| **Evidence** | 文档标题"MathModelSkills 深度体检与标准化方案"，生成日期 2026-09-04，性质声明"诊断与排期文档，本次未改动任何既有文件"。文档包含八步体检法结论、分维度评分（架构 8.5/10, 内容资产 8/10 等）、改进排期。此后 P0-P6 硬化计划（`docs/architecture/HARDENING_PROGRAM.md`）已执行完毕并 release v3.1.0。 |
| **Why obsolete / suspicious** | 这是 V3 迁移前的诊断文档，其建议已被 Hardening P0-P6 执行。作为决策记录有历史价值，但作为"计划"已完成。 |
| **Dependency evidence** | `Grep -r "refactor-plan-v2" --include="*.md" --include="*.py"` 确认无代码或其他文档引用。 |
| **Risk of deletion** | **low** — 纯文档，无代码依赖。38KB 的诊断内容对理解 V3 迁移决策有历史参考价值。 |
| **Recommended action** | **ARCHIVE** — 保留在 `docs/decisions/` 下（该目录本身就是决策记录区），添加 `[COMPLETED 2026-09-08, actions tracked in HARDENING_PROGRAM.md]` 头部标注。不 DELETE 因为决策记录是架构演进的重要证据。 |

---

### DEBT-018 — 部分填充包：core/evaluation/

| 属性 | 值 |
|---|---|
| **Path** | `core/evaluation/__init__.py`（366B）, `core/evaluation/benchmark/__init__.py`（1466B）, `core/evaluation/scoring/__init__.py`（2189B） |
| **Category** | superseded |
| **Evidence** | `core/evaluation/__init__.py` 文档字符串明确："P4 阶段评分实现仍驻留 core/tools/（零依赖脚本，state/gate/编排器消费）；本包提供稳定的 V3 import 面 evaluation.scoring。P5 目录重构时实现迁入本包，core/tools/ 侧退化为 CLI 薄转发，本 import 面保持不变。" |
| **Why obsolete / suspicious** | 这是一个有意设计的前向兼容包，不是技术债务。P5 已完成（Regression Gate）但评分实现未迁入 core/evaluation/，仍在 core/tools/evaluation/。迁移计划被推迟。 |
| **Dependency evidence** | `Grep -r "from core.evaluation\|import core.evaluation" --include="*.py"` 返回 **0 匹配** — 当前无代码使用此 import 面。包存在但未被消费。 |
| **Risk of deletion** | **low** — 无消费者，删除不影响运行时。但删除会失去预留的 V3 import 面。 |
| **Recommended action** | **DEFER** — 这是架构规划的一部分，不是债务。等待评分实现迁移完成后此包自动激活。若长期不迁移（如 v3.2.0 仍未迁入），则评估是否删除预留包。当前 DEFER 至下一个 minor release。 |

---

### DEBT-019 — 归档样例三状态文件：archives/cumcm2024anew/

| 属性 | 值 |
|---|---|
| **Path** | `archives/cumcm2024anew/work/state.json`（4879B）, `archives/cumcm2024anew/work/STATE.md`（1673B）, `archives/cumcm2024anew/state/status.json`（1563B） |
| **Category** | duplicate |
| **Evidence** | 归档样例中存在三份状态文件：`work/state.json`（V2 格式）、`work/STATE.md`（V2 人类可读状态）、`state/status.json`（V3 格式）。V3 已收口到 `state/status.json` 单一真源，`work/state.json` 和 `work/STATE.md` 为 V2 遗留。 |
| **Why obsolete / suspicious** | 这是 V2→V3 迁移过程中的双真源痕迹。archives/ 为历史归档，保留 V2 格式文件作为迁移证据是合理的，但应明确标注。 |
| **Dependency evidence** | archives/ 被 validate.py 排除出实时校验，被 metrics.py 引用为历史基线。无代码读取 work/state.json 或 STATE.md。 |
| **Risk of deletion** | **low** — 归档目录，无运行时依赖。 |
| **Recommended action** | **DOCUMENT** — 在 `archives/README.md` 中说明："cumcm2024anew/ 保留 V2 双状态文件（work/state.json + STATE.md）作为迁移证据，V3 状态为 state/status.json。勿用于运行时。" 不 DELETE 因为是迁移历史证据。 |

---

### DEBT-020 — 过时集成文档：harness-compat.md

| 属性 | 值 |
|---|---|
| **Path** | `docs/integration/harness-compat.md`（7887B） |
| **Category** | stale-doc |
| **Evidence** | 文档定义"跨 Harness 行为约定"，§核心原则列出：(2) 契约优先 — "四手之间仅通过契约文件（MODEL_SPEC.md、CODE_DELIVERABLES.md、PAPER_SPEC.md）交互"；(4) 入口统一 — "任何运行时进入项目根目录，读取 AGENTS.md 或 .codex-plugin/plugin.json 即可开始执行"。§状态文件规范定义 `work/state.json` 为"单一事实源"。这些都是 V2 规范。V3 已升级为 DAG 节点 + Artifact Registry + Evidence Graph，状态真源为 `state/status.json`（由事件重建）。 |
| **Why obsolete / suspicious** | 跨 Harness 兼容的核心原则仍有价值（状态外置、契约优先、门禁脚本化），但具体契约文件名和状态文件路径已过时。 |
| **Dependency evidence** | `Grep -r "harness-compat" --include="*.md" --include="*.py"` 确认无代码引用。 |
| **Risk of deletion** | **medium** — 跨运行时兼容原则对多编辑器支持仍有价值，删除会丢失通用规范。 |
| **Recommended action** | **UPDATE** — 将契约文件引用更新为 V3 DAG 节点 artifact，状态文件路径更新为 `state/status.json`，添加 V2/V3 对照说明。或添加过时警告后保留通用原则部分。 |

---

### DEBT-021 — git tracked 但被 gitignore 的文件：package-lock.json

| 属性 | 值 |
|---|---|
| **Path** | `package-lock.json`（205B） |
| **Category** | orphan-config |
| **Evidence** | `.gitignore` 包含 `package-lock.json` 规则。但 `git ls-files package-lock.json` 确认文件**已被 git 跟踪**。这是在添加 .gitignore 规则之前提交的文件，规则不会自动取消跟踪已跟踪文件。 |
| **Why obsolete / suspicious** | 文件仅 205B，内容为几乎空的 npm lockfile（`package.json` 无 dependencies）。与 DEBT-005（package.json 过时）相关。 |
| **Dependency evidence** | 无代码引用。 |
| **Risk of deletion** | **low** — 从 git 索引移除不删除本地文件，无运行时影响。 |
| **Recommended action** | **DELETE（git --cached）** — 执行 `git rm --cached package-lock.json` 从 git 索引移除，本地文件保留或随 DEBT-005 一并处理。满足 "generated and reproducible"（npm install 可重新生成）+ "provably unused"。 |

---

### DEBT-022 — V2 兼容测试：test_runtime_compat.py

| 属性 | 值 |
|---|---|
| **Path** | `tests/compat/test_runtime_compat.py`（11619B） |
| **Category** | stale-doc |
| **Evidence** | 文件文档字符串："多运行时适配测试脚本 — 验证 MathModelSkills 在不同 AI 运行时下的兼容性：Claude Code, Codex CLI, opencode, Cursor, 通用 Python"。测试项包括"状态文件读写（state.json, decision_log.json）""友好模式交互""契约文件产出"。引用 V2 状态文件规范。 |
| **Why obsolete / suspicious** | 这是 V2 时代为多运行时兼容编写的测试。V3 运行时已统一为 RuntimeSession + DAG 执行，多运行时兼容由 `core/runtime/adapters/` 和 `adapters/openai.yaml` 处理。测试可能仍在 pytest 收集中（文件名符合 test_*.py 模式），但测试的 V2 行为可能已不适用。 |
| **Dependency evidence** | 需确认该测试是否在 781 passed 基线中。`tests/compat/` 目录在 pytest 收集路径下。 |
| **Risk of deletion** | **medium** — 如果测试仍在运行且通过，删除会减少测试覆盖。如果测试已 skip 或测试 V2 已移除的行为，则为死测试。 |
| **Recommended action** | **DEFER** — 先运行 `py -3.12 -m pytest tests/compat/ -v` 确认测试状态（passed/skipped/failed）。若全部 skipped 或测试已移除的 V2 行为，则 DELETE；若仍有效则 UPDATE 为 V3 兼容测试。当前 DEFER 至验证后决策。 |

---

### DEBT-023 — 空编辑器目录：research/P13-3D-R3/.workbuddy/

| 属性 | 值 |
|---|---|
| **Path** | `research/P13-3D-R3/.workbuddy/` |
| **Category** | temp-artifact |
| **Evidence** | `Get-ChildItem research/P13-3D-R3/.workbuddy -Recurse -Force` 返回 **0 个文件**。这是 WorkBuddy 编辑器在实验目录下创建的空配置目录。 |
| **Why obsolete / suspicious** | 空目录，且 `.gitignore` 已包含 `.workbuddy/` 规则（根目录级别），但此嵌套目录可能已被 git 跟踪或为本地残留。 |
| **Dependency evidence** | 无引用。 |
| **Risk of deletion** | **low** — 空目录。 |
| **Recommended action** | **DELETE** — 满足 "provably unused"（空目录 + 零引用）。检查是否被 git 跟踪，若是则 `git rm -r`。 |

---

## 监控项（非债务，需持续关注）

以下项目经审计确认**不是债务**，但需在后续迭代中监控：

| 项目 | 说明 | 监控条件 |
|---|---|---|
| `core/legacy/`（283 文件） | V2 兼容层，架构冻结保障只读兼容 | 若 v4.0 决定终止 V2 兼容，可整体 ARCHIVE |
| `core/validators/` vs `core/tools/validation/` | 两套校验器并存，功能有重叠 | 若 validators/ 模块被 tools/validation/ 完全替代，评估 MERGE |
| `core/knowledge/bench/e2e/`（114 文件） | P13 实验固化语料在 runtime knowledge 层 | 若 bench 语料膨胀，考虑迁移到 research/ 或独立 benchmark 仓库 |
| `research/P13-3D-R2/`（130 文件） | 仅 output + state 的冻结实验 | 研究证据，保留；若存储紧张可打包归档 |
| `projects/p151-2024a/` vs `projects/rcs1-2024a/` | 两个实例 registry.json 大小完全相同 | 确认是否为克隆关系，避免重复存储 |
| `core/tools/*.py`（37 shim） | 兼容 shim 模式 | 长期可考虑直接迁移实现到根级，消除 shim 层 |
| `docs/architecture/`（48 文件） | P0-P15 研究报告集合 | 文档数量持续增长，可考虑按阶段子目录组织 |

---

## 执行优先级建议

### P0 — 可立即执行（无风险，纯清理）
1. DEBT-001: 删除 12 个 `_tmp_*.txt`
2. DEBT-002: 删除破损 shim `run_p13_3d.py`
3. DEBT-003: 删除嵌套目录 `tests/tests/`
4. DEBT-007: 删除空目录 `research/P13-3D/inputs/`
5. DEBT-009/010: 本地清理 node_modules（不影响 git）
6. DEBT-021: `git rm --cached package-lock.json`
7. DEBT-023: 删除空目录 `.workbuddy/`

### P1 — 需确认后执行
8. DEBT-008: diff 后删除重复评分卡
9. DEBT-013: 添加 .gitignore 规则（.trae/, .zcode/）
10. DEBT-016: 将 test_tex_to_docx_quick.py 转为 pytest 格式
11. DEBT-022: 验证 compat 测试状态后决策

### P2 — 需文档更新或迁移
12. DEBT-004: ARCHIVE IMPROVEMENT_PLAN.md
13. DEBT-006: UPDATE TEAM_GUIDE.md
14. DEBT-011: 修复 gen_runtime_manifest.py 模板后重新生成
15. DEBT-012: ARCHIVE bench-m4 变体目录到 archives/
16. DEBT-017: 标注 refactor-plan-v2.md 为 COMPLETED
17. DEBT-020: UPDATE harness-compat.md

### P3 — 长期监控
18. DEBT-005: 确认 package.json 引用后决策
19. DEBT-018: DEFER core/evaluation/ 迁移
20. DEBT-019: DOCUMENT archives 三状态文件
21. DEBT-014/015: KEEP 跨编辑器配置文件（非债务）

---

*报告生成时间：2026-09-08 | 审计员：Repository Inventory & Debt Ledger Auditor | 共 23 项债务 + 7 项监控*
