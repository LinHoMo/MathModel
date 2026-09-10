# MathModel — Agent Development Protocol / Agent 开发协议

> 本文件是 Agent 在本仓库工作的**唯一权威协议**。任何 Agent（Doubao / GPT / Claude Code /
> 人工）进入本仓库，必须先完整阅读本文件，再按 §1 必读顺序读完其余文档，方可开始实现。
> 定位：可信 Harness（V3 认知工作流运行时）。输入赛题 → 产出 MODEL_IR（JSON）+ 模型描述文档（MD/Mermaid）。
> core 内 LLM-free；不含论文生成；不向后兼容 V2。

---

## 核心定位 / Core Positioning

**中文 / ZH**

**问题输入 → 数学建模产出（MD/Mermaid 文本）**：产出物为 MODEL_IR（JSON）+
模型描述文档（MD/Mermaid）。**Source of truth = Artifact Registry + Evidence Graph。**
core 内 LLM-free（Agent / LLM 只是 Executor）；不包含论文生成（LaTeX/PDF）；
不向后兼容 V2。

**English / EN**

**Problem input → math-modeling output (MD/Mermaid text)**: deliverables are
MODEL_IR (JSON) + a model description document (MD/Mermaid).
**Source of truth = Artifact Registry + Evidence Graph.**
core is LLM-free (Agents/LLMs are only Executors); no paper generation (LaTeX/PDF);
no backward compatibility with V2.

---

## 目录结构 / Directory Structure

**中文 / ZH**

| 目录/文件 | 说明 |
|---|---|
| `core/` | 引擎本体（LLM-free）：runtime / roles / workflows / validators / schemas / tools / skills / knowledge / env |
| `core/tools/` | CLI 工具：validate.py / catalog_check.py / new_project.py / doctor.py 等 |
| `core/workflows/` | DAG 模板（stages/）+ WorkflowComposer |
| `core/roles/` | 4 角色：analyst / modeler / experimenter / critic |
| `core/validators/` | 门禁：evidence-gate / research-quality / model-critic / assumption-checker |
| `catalog/` | 元数据双视图单一真源（catalog.yaml / v3.yaml / protocol_tools.yaml） |
| `docs/` | 文档区（入口见 docs/README.md） |
| `docs/decisions/` | 架构决策记录（ADR） |
| `prompts/` | Agent 角色提示词与任务卡模板 |
| `research/` | 研究实验（ENGINEERING / P15） |
| `tests/` | 分层测试（unit / integration / e2e / regression） |
| `projects/` | 用户运行实例（仅 `new_project.py` 创建） |
| `TASKS.md` | 任务看板 |

**English / EN**

| Path | Description |
|---|---|
| `core/` | Engine (LLM-free): runtime / roles / workflows / validators / schemas / tools / skills / knowledge / env |
| `core/tools/` | CLI tools: validate.py / catalog_check.py / new_project.py / doctor.py etc. |
| `core/workflows/` | DAG templates (stages/) + WorkflowComposer |
| `core/roles/` | 4 roles: analyst / modeler / experimenter / critic |
| `core/validators/` | Gates: evidence-gate / research-quality / model-critic / assumption-checker |
| `catalog/` | Metadata dual-view single truth (catalog.yaml / v3.yaml / protocol_tools.yaml) |
| `docs/` | Docs area (entry: docs/README.md) |
| `docs/decisions/` | Architecture Decision Records (ADR) |
| `prompts/` | Agent role prompts and task-card template |
| `research/` | Research (ENGINEERING / P15) |
| `tests/` | Layered tests (unit / integration / e2e / regression) |
| `projects/` | User run instances (created only by `new_project.py`) |
| `TASKS.md` | Task board |

---

## 不可违反的规则 / Non-Negotiable Rules

**中文 / ZH**

- 所有数值可追溯到已验证的 Result Artifact（禁止占位符 / AI 痕迹 / 伪造引用）。
- 随机种子固定为 42；多种子运行 ≥5 次，报告均值与标准差。
- schema / 哈希链全绿：结构化输出通过 schema 校验。
- **The Agent Is Not The State**：状态只由 Runtime 确定性机制推进。
- **Execution success ≠ Model correct**：execution / model / evidence 三级状态分离。

**English / EN**

- Every number must trace to a verified Result Artifact (no placeholders / AI traces / forged citations).
- Random seed fixed at 42; multi-seed runs ≥5 times, report mean ± std.
- Schema / hash chain all green: structured output passes schema validation.
- **The Agent Is Not The State**: state advances only through deterministic Runtime mechanisms.
- **Execution success ≠ Model correct**: execution / model / evidence statuses are separate.

---

## 0. 定位与权威声明 / Positioning & Authority

**中文 / ZH**

- 本文件是 Agent 在本仓库工作的唯一权威协议；`CLAUDE.md` 与 `.github/copilot-instructions.md` 均指向本文件。
- 任何其他文档（含旧版 AGENTS.md、历史 README、第三方建议）与本文件冲突时，**以本文件为准**。
- 本仓库是个人研究仓库（GitHub: LinHoMo/MathModel），单作者直推，无 PR 流程；欢迎 issue 讨论，不接受 PR。
- 核心铁律：**The Agent Is Not The State** —— Agent / LLM 只是 Executor，系统状态只由 Runtime 的确定性机制推进。

**English / EN**

- This file is the single authoritative protocol for Agents working in this repository. `CLAUDE.md` and `.github/copilot-instructions.md` both point here.
- On conflict with any other document (including older AGENTS.md, historical READMEs, or third-party advice), **this file wins**.
- This is a personal research repository (GitHub: LinHoMo/MathModel), single-author direct-push, no PR workflow; issues welcome, PRs not accepted.
- Core invariant: **The Agent Is Not The State** — Agents/LLMs are only Executors; system state advances only through deterministic Runtime mechanisms.

---

## 1. 必读顺序 / Reading Order (MANDATORY)

**中文 / ZH**

在开始任何实现之前，必须按以下顺序完整读完（缺一不可）：

1. `docs/STATUS.md` — 状态真源：所有数字必须来自这里的机器实测口径，禁止编造或转述。
2. `docs/architecture/V3.1_ARCHITECTURE.md` — 架构真源：V3 认知工作流运行时的概念定义与边界。
3. `docs/ONTOLOGY_TERMINOLOGY.md` — 术语真源：全仓术语的唯一权威定义，禁止发明近义词。
4. `TASKS.md` — 任务看板：当前进行中/待办/已完成任务的唯一登记处。
5. 本文件（AGENTS.md）— 工作协议：角色、工作流、禁止事项、验收标准。

未按顺序读完，**不得开始任何实现**。读完后仍不确定的项，按 §10 处理（停下问，不要猜）。扩展阅读见 `docs/README.md` 文档索引。

**English / EN**

Before starting any implementation, you MUST read all of the following in order (none may be skipped):

1. `docs/STATUS.md` — State truth: every number must follow the machine-measured convention recorded here; never fabricate or relay unverified numbers.
2. `docs/architecture/V3.1_ARCHITECTURE.md` — Architecture truth: concepts and boundaries of the V3 cognitive-workflow runtime.
3. `docs/ONTOLOGY_TERMINOLOGY.md` — Terminology truth: single authoritative vocabulary; do not invent near-synonyms.
4. `TASKS.md` — Task board: the single registry of in-progress / todo / done tasks.
5. This file (AGENTS.md) — Working protocol: roles, workflow, prohibitions, acceptance criteria.

Do NOT start any implementation before reading all of the above in order. If anything remains uncertain, follow §10 (stop and ask; do not guess). For further reading, see the `docs/README.md` documentation index.

---

## 2. 角色定义 / Roles

**中文 / ZH**

| 角色 | 职责边界 | 禁止 |
|---|---|---|
| **Planner** | 只读：读任务描述/STATUS/架构文档，输出实现计划、风险、验收标准 | 不改代码、不新增依赖、不越界 |
| **Implementer** | 只改任务卡指定文件；产出代码 diff 与验证命令输出 | 越界修改、伪造产物、改测试语义 |
| **Tester** | 只写/跑测试；按验收命令验证；报告失败原因 | 改业务代码、为通过而改测试语义 |
| **Reviewer** | 只读 diff：审查越界、伪造、数字来源、依赖声明 | 不改代码、不修产物 |

一个 Agent 可身兼多角，但**每个角色的边界必须遵守**；兼任时须在汇报中说明当前以何角色行事。

**English / EN**

| Role | Boundary | Forbidden |
|---|---|---|
| **Planner** | Read-only: read task description / STATUS / architecture docs; produce plan, risks, acceptance criteria | Editing code, adding deps, out-of-scope actions |
| **Implementer** | Touch only files named in the task card; produce code diff and verification output | Out-of-scope edits, forging artifacts, tampering with test semantics |
| **Tester** | Only write/run tests; verify via acceptance commands; report failures | Editing business code, changing test semantics to pass |
| **Reviewer** | Read-only diff review: check scope, forgery, number provenance, dependency claims | Editing code or artifacts |

One Agent may take multiple roles, but **each role's boundary must be respected**; when acting in multiple roles, state the active role in your report.

---

## 3. 任务卡模板 / Task Card Template

**中文 / ZH**

任务卡是任务的最小单元，六要素缺一不可（模板见 `prompts/task-template.md`）：

```markdown
# Task [ID] / 任务 [ID]
- Goal / 目标：做什么
- Context (must-read) / 上下文（必读）：要读哪些文档/文件
- Acceptance / 验收：可验证的完成标准
- Prohibitions / 禁止：本任务的禁止事项
- Verify commands / 验证命令：验收要跑的命令
- Rollback / 回滚：失败时如何回退
```

**English / EN**

A task card is the smallest unit of work; all six elements are mandatory (template at `prompts/task-template.md`):

```markdown
# Task [ID] / 任务 [ID]
- Goal / 目标：what to do
- Context (must-read) / 上下文（必读）：which docs/files to read
- Acceptance / 验收：verifiable completion criteria
- Prohibitions / 禁止：what is forbidden for this task
- Verify commands / 验证命令：commands to run for acceptance
- Rollback / 回滚：how to roll back on failure
```

---

## 4. 工作流 / Workflow (MANDATORY)

**中文 / ZH**

**计划 → 确认 → 实现 → 验证 → 审查 → 提交**（Plan → Confirm → Implement → Verify → Review → Commit）。每步推进一次，禁止跳步。

1. **计划 / Plan**：读任务卡与必读文档，输出计划（改动文件清单、风险、验收标准）。若计划依赖的事实未取得，先补证据。
2. **确认 / Confirm**：计划与用户/组织者确认。有歧义且影响结论时，一次问清；不影响则自行选择并注明。
3. **实现 / Implement**：只改任务卡指定文件，单任务单意图；不得顺手改未点名文件。
4. **验证 / Verify**：跑任务卡验证命令；diff 自审（是否越界、是否伪造、数字是否有来源）。
5. **审查 / Review**：以 Reviewer 视角重读自己的 diff，寻找反证；发现问题先修产物再重跑验证。
6. **提交 / Commit**：conventional commits，单 commit 单意图；提交信息清晰说明「做了什么 + 为什么」；提交后更新 `TASKS.md` 对应任务状态。

**English / EN**

**Plan → Confirm → Implement → Verify → Review → Commit**. Advance one step at a time; no skipping.

1. **Plan**: Read the task card and mandatory docs; produce a plan (file list, risks, acceptance criteria). If the plan depends on facts you do not have, gather evidence first.
2. **Confirm**: Confirm the plan with the user/organizer. If ambiguity changes the conclusion, ask once; otherwise decide and note it.
3. **Implement**: Touch only files named in the task card; one intent per task; do not edit unnamed files along the way.
4. **Verify**: Run the task's verify commands; self-review the diff (scope, forgery, number provenance).
5. **Review**: Re-read your own diff from a Reviewer's perspective; actively look for counter-evidence; fix the artifact first, then re-verify.
6. **Commit**: Conventional commits, one intent per commit; message states clearly what and why; after committing, update the corresponding task status in `TASKS.md`.

---

## 5. 禁止事项 / Prohibitions (NON-NEGOTIABLE)

**中文 / ZH**

- 禁止新增 core 运行时第三方依赖（零依赖是定位红利）/ No new runtime third-party deps (zero-dep is a positioning advantage).
- 禁止修改 `core/schemas/v3/` 下的 canonical schema / No edits to canonical schemas under `core/schemas/v3/`.
- 禁止修改 `core/runtime/` 下的业务逻辑代码（文档/配置/基线任务除外）/ No edits to business logic under `core/runtime/` (except doc/config/baseline tasks).
- 禁止伪造 ExecutionResult 或任何验证产物 / No forged ExecutionResult or any verification artifact.
- 禁止修改测试语义来通过测试 / No test-semantics tampering to pass tests.
- 禁止越界修改任务卡未指定文件 / No out-of-scope edits beyond the task card.
- 禁止回填 STATUS.md 数字；数字必须来自机器实测 / No manual backfill of STATUS numbers; numbers must come from machine runs.
- 禁止以本地环境判断依赖；以 CI 为准 / Never judge dependencies from the local environment; use CI.
- 修改本文件前，必须先读 `validate.py` 中对 AGENTS.md 的章节校验规则（当前要求含「核心定位 / 目录结构 / 不可违反的规则」三章），确保不破坏机器校验 / Before editing this file, first read the AGENTS.md section-check rules in `validate.py` (currently requiring the three sections 核心定位 / 目录结构 / 不可违反的规则) to ensure machine checks stay green.

**English / EN**

- No new runtime third-party dependencies (zero-dep is the positioning advantage).
- No edits to canonical schemas under `core/schemas/v3/`.
- No edits to business logic under `core/runtime/` (except documentation/config/baseline tasks).
- No forged ExecutionResult or any other verification artifact.
- No test-semantics tampering to make tests pass.
- No out-of-scope edits beyond what the task card specifies.
- No manual backfill of STATUS.md numbers; numbers must come from machine-measured runs.
- Never judge dependencies from the local environment; trust CI.

---

## 6. 环境与依赖 / Environment & Dependencies

### 6.1 运行时 / Runtime

**中文 / ZH**

- core **零第三方运行时依赖**（定位红利，不可破坏）：core 的 import 只能来自标准库与 core 自身。
- Python：`>= 3.8`（声明），实测 `3.12`。
- 本机（Windows）必须用 `py -3.12`——默认 `py` 指向 3.14/3.13 且安装损坏。

**English / EN**

- core has **zero third-party runtime dependencies** (positioning advantage, must not be broken): imports in core may only come from the standard library and core itself.
- Python: `>= 3.8` (declared), `3.12` (verified).
- On this Windows machine always use `py -3.12` — the default `py` points to a broken 3.14/3.13 install.

### 6.2 测试环境 / Test Environment

**中文 / ZH**

- 测试环境依赖（CI 已验证，见 `.github/workflows/ci.yml`）：`pytest`、`pyyaml`、`jsonschema`、`ripgrep`（rg）、`ruff`。
- 这些是**测试环境**依赖，不是运行时依赖；core 运行时仍为零依赖。
- 本地缺依赖时**以 CI 为准**，不以本地残留为准。

**English / EN**

- Test-environment dependencies (verified in CI, see `.github/workflows/ci.yml`): `pytest`, `pyyaml`, `jsonschema`, `ripgrep` (rg), `ruff`.
- These are **test-environment** deps, not runtime deps; core runtime stays zero-dep.
- When local packages are missing, **trust CI**, not whatever happens to be installed locally.

### 6.3 判断依赖的方法 / How to Judge Dependencies

**中文 / ZH**

1. 跑 `py -3.12 -m pytest tests -q`；失败时看 import 错误，按缺失模块名判断。
2. 不要假设「本地能跑 CI 就能跑」——本地可能残留了 CI 没有的包，反之亦然。
3. 需要新增测试依赖时，必须同步修改 `.github/workflows/ci.yml` 并在汇报中单列说明。

**English / EN**

1. Run `py -3.12 -m pytest tests -q`; on failure read the import error and judge from the missing module name.
2. Never assume "runs locally so it runs in CI" — local envs may have leftovers CI lacks, and vice versa.
3. Adding a test dependency requires updating `.github/workflows/ci.yml` in the same commit and calling it out in the report.

---

## 7. 验收标准 / Acceptance Criteria

**中文 / ZH**

任何改动（文档、配置、代码、研究）完成后，必须通过**四件套**：

```powershell
py -3.12 core/tools/validate.py                     # 项目级校验（基线见 docs/STATUS.md）
py -3.12 core/tools/catalog_check.py --check        # catalog 双视图三方一致
py -3.12 core/tools/catalog_check.py --check-terminology  # 术语零残留
py -3.12 -m pytest tests -q                         # 基线测试（数字以 docs/STATUS.md 实测为准）
```

- 手动检查清单：diff 自审（无越界文件、无伪造数字、无占位符）、关键数字可追溯到输入/实测。
- 回滚步骤：每个任务独立 commit；失败时 `git revert` 到上一个绿色 commit（四件套全过的提交）。
- 推送后必须确认 GitHub Actions CI 全绿；本地四件套通过**不等于** CI 通过。

**English / EN**

After any change (docs, config, code, research), the **four-gate** must pass:

```powershell
py -3.12 core/tools/validate.py                     # project-level checks (baseline: docs/STATUS.md)
py -3.12 core/tools/catalog_check.py --check        # catalog dual-view consistency
py -3.12 core/tools/catalog_check.py --check-terminology  # zero stale terminology
py -3.12 -m pytest tests -q                         # baseline tests (numbers per docs/STATUS.md)
```

- Manual checklist: self-review the diff (no out-of-scope files, no forged numbers, no placeholders); key numbers traceable to input or measured runs.
- Rollback: each task is an independent commit; on failure `git revert` to the last green commit (a commit where all four gates passed).
- After pushing, confirm the GitHub Actions CI is all green; local four-gate passing does **not** equal CI passing.

### 7.1 文档更新纪律 / Doc Update Discipline

**中文 / ZH**

改动代码后必须同步更新：`STATUS.md`（数字变化时）、`CHANGELOG.md`（版本相关时）、`TASKS.md`（任务状态）。

**English / EN**

After changing code, keep the following in sync: `STATUS.md` (when numbers change), `CHANGELOG.md` (when version-relevant), `TASKS.md` (task status).

---

## 8. Commit 规范 / Commit Convention

**中文 / ZH**

- 使用 conventional commits：`feat` / `fix` / `refactor` / `chore` / `test` / `docs`。
- **单 commit 单意图**：一个提交只做一件事，禁止把无关改动混进同一提交。
- 提交信息中英不限，但必须清晰：`<type>(<scope>): <summary>`，如 `docs(p0): fix stale V2 references`。
- 每个任务独立 commit，便于失败时定点 revert。

**English / EN**

- Use conventional commits: `feat` / `fix` / `refactor` / `chore` / `test` / `docs`.
- **One intent per commit**: one commit does one thing; never mix unrelated changes.
- Message may be Chinese or English but must be clear: `<type>(<scope>): <summary>`, e.g. `docs(p0): fix stale V2 references`.
- Each task gets its own commit so failures can be reverted precisely.

---

## 9. 同类事实修正 / Same-Class Fact Corrections

**中文 / ZH**

允许（任务过程中发现的同类事实错误，可随任务一并修正，但必须单列汇报）：

- 已删除项的残留引用（如 LaTeX / paper_section / 已删 schema 的引用）。
- 数字不一致（如校验项数 58→45，以实测为准）。
- 断裂链接、失效路径、过时命令说明。

要求：

- 必须在汇报中单列「范围外修正清单」，每条附**文件路径 + 证据**（实测输出 / grep 结果 / 文件存在性）。
- 禁止借「事实修正」之名改架构、改 schema、改业务逻辑、改测试语义。

**English / EN**

Allowed (same-class fact errors found during a task may be fixed alongside it, but MUST be reported separately):

- Stale references to deleted items (e.g. LaTeX / paper_section / deleted schemas).
- Number inconsistencies (e.g. check count 58→45, always from measurement).
- Broken links, dead paths, outdated command docs.

Requirements:

- The report MUST include a separate "Out-of-Scope Corrections" list, each entry with **file path + evidence** (measured output / grep result / file existence).
- Forbidden to use "fact correction" as cover for changing architecture, schemas, business logic, or test semantics.

---

## 10. 遇到不确定时 / When Uncertain

**中文 / ZH**

- 停下，写「待人工确认」，**不要编造**。
- 列清楚：问题、可选方案、影响、建议。
- 继续执行会改变结论或造成不可逆影响的事项，必须先确认再动手；可逆的小事可自行决定并注明。
- 所有「待人工确认」项必须登记到 `TASKS.md`（T-CONF-xxx），关闭时在汇报中说明裁定。

**English / EN**

- Stop and write "pending human confirmation"; **never fabricate**.
- List clearly: the question, options, impact, and a recommendation.
- If proceeding would change the conclusion or cause irreversible effects, confirm first; reversible minor matters may be decided and noted.
- Every pending item must be registered in `TASKS.md` (T-CONF-xxx) and its resolution reported when closed.
