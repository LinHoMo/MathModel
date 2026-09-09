# MathModel 仓库治理审计 — Agent H（audit_h）

> 审计类型：**只读治理审计**（docs / terminology / schema / catalog / archival /
> git history / 生成产物可复现性 / source of truth）。
> 审计基线：HEAD `d44384c`（2026-09-09 16:44），工作区除 `research/P15/analysis/raw_k003/`
> 与 `research/audit/` 外无未提交改动。
> 审计时间：2026-09-09（审计期间观察到 K003 Organizer 后台进程在写实验产物）。
> 核心原则：**Source of truth = Artifact Registry + Evidence Graph + Research State。
> 文档声称的数字必须与磁盘实据一致。**

## 一、审计范围摘要

本审计覆盖八个维度，实际执行的命令与核查点：

| 维度 | 核查内容 | 执行方式 |
|---|---|---|
| Source of Truth | STATUS.md 声称数字逐条复测（pytest / validate.py / catalog_check / 冻结脚本） | 命令实测 + git show 对照 |
| Terminology | MODEL_IR / ExecutionResult / Evidence / Validation / Revision 术语一致性、V2 残留 | `catalog_check.py --check-terminology` + docs 检索 |
| Schema 治理 | core/schemas/ 引用与校验、registry.create 门禁、schema 漂移 | 源码阅读 + grep |
| Catalog 一致性 | catalog.yaml ↔ catalog/v3.yaml ↔ 代码三方一致 | `catalog_check.py --check` + 节点计数 |
| Git History | 可疑 commit、.gitignore 历史、大文件/生成产物入库、commit message | git log / ls-tree / status |
| 可复现性 | K001/K002/K003 冻结哈希、实验产物环境信息、魔法数字/硬编码路径 | 冻结脚本 + 文件检查 |
| Documentation | README / AGENTS / HANDOFF / architecture 与代码一致性 | 文件阅读对照 |
| Archival | 历史数据归档、孤儿文件 | 目录清单 + 引用核对 |

## 二、发现计数

| 严重度 | 数量 | Finding ID |
|---|---|---|
| Critical | 0 | — |
| High | 2 | H-001, H-002 |
| Medium | 5 | H-003, H-004, H-005, H-006, H-007 |
| Low | 3 | H-008, H-009, H-010 |
| Info | 1 | H-011 |
| **合计** | **11** | |

另：H-012 为核验通过项（terminology 零残留、catalog 三方一致、冻结哈希零漂移），
不作为缺陷，仅记录证据。

## 三、STATUS.md 数字验证矩阵（声称值 vs 实测值）

审计基线 HEAD = `d44384c`。STATUS.md 声称"所有数字来自机器命令实测并绑定
commit hash"。

| STATUS.md 声称 | 实测输出（本次审计） | 一致？ |
|---|---|---|
| 测试 `911 passed / 4 skipped / 0 failed` | `py -3.12 -m pytest tests -q` → **911 passed, 4 skipped**（68.72s） | ✅ |
| 项目级校验 `57 通过 / 0 失败 / 0 警告` | `py -3.12 core/tools/validate.py` → **56 通过 / 1 失败 / 0 警告**（L6 PDF大小：`tests\fixtures\sample_paper_project\paper\main.pdf` 8230B < 102400B） | ❌ |
| catalog 三方一致 `OK` | `catalog_check.py --check` → **OK** | ✅ |
| 术语零残留 `OK`（production 零残留） | `catalog_check.py --check-terminology` → **OK** | ✅ |
| K001 冻结 `PASS（44 文件）` | `k001_freeze.py --check` → **PASS，44 文件**，root a9fe3043… | ✅ |
| K002 冻结 `PASS（40 文件）` | `k002_freeze.py --check` → **PASS，40 文件**，root bb9d5b5c… | ✅ |
| K003 冻结 `PASS（36 文件）`，root `94b14d4f` | `k003_freeze.py --check` → **PASS，36 文件**，root `94b14d4ffc04…`（前缀一致） | ✅ |
| K003 阶段锚点 `46c6a4f` | git log 存在 `46c6a4f feat(p15-k003): FROZEN — five gates all PASS…` | ✅ |
| K002 冻结文件数 `40`（STATUS.md 行 40） | 实测 40；**README.md 行 106 仍写"38 文件"** | ⚠️ 见 H-006 |

## 四、Catalog 一致性结果

- `py -3.12 core/tools/catalog_check.py --check` → **OK**（v3 双视图与 roles/DAG/
  validators 三方一致，legacy 29 agent 视图完整）。
- `--check-terminology` → **OK**（production 区旧术语零残留）。
- **但存在注释级不一致**：catalog.yaml 头注释与 catalog/v3.yaml 头注释声称
  "15 节点 DAG + 5 角色 + 6 validator"，实际 v3.yaml 列出 **20 节点 + 7 validator**
  （workflow stage yaml 汇总：problem-analysis 2 + modeling 8 + experiment 3 +
  evidence 3 + paper 4 = 20）。catalog_check 不校验注释数字 → 见 H-005。

## 五、冻结哈希状态

| 冻结 | 状态 | 文件数 | frozen_root_sha256 |
|---|---|---|---|
| K001 | ✅ PASS，无漂移 | 44 | a9fe304373757f651d4015f852d241ee749c803f6c25faf0d076ed23bc70933e |
| K002 | ✅ PASS，无漂移 | 40 | bb9d5b5c5b5feeb0425f63a0e904c24650d8c8e8ae780ced2aedbcf125de6ada |
| K003 | ✅ PASS，无漂移 | 36 | 94b14d4ffc04ddb0144a4cfdfd0d4f194bf3989ac875602287523e9b0921e52c |

无哈希漂移。注意：K003 预注册冻结文件与"正式 66 runs"运行产物是两回事；
运行产物（bundles / runs / formal_results.json）**不参与**冻结校验（见 H-002、H-007）。

---

## 六、发现明细

### H-001 — High — Source of Truth：STATUS.md 声称的 validate.py "57/0/0" 与 HEAD 实测不符

- **File**：`docs/STATUS.md`（行 49）；`core/tools/validate.py`
- **Function-Symbol**：`check_pdf_size`（L6 PDF 大小检查）
- **Line**：STATUS.md:49（声称表）；validate.py 校验项 `[L6] PDF大小`
- **Observed behavior**：`py -3.12 core/tools/validate.py` 输出
  `验证完成: 56 通过, 1 失败, 0 警告`，失败项 `[L6] PDF大小:
  tests\fixtures\sample_paper_project\paper\main.pdf: 8230B < 102400B`（退出码 1）。
  该 fixture PDF **未入库且未被 .gitignore 忽略**（`git check-ignore` 返回
  NOT-IGNORED；`git ls-files` 仅有 main.tex），是本地生成物。
- **Expected behavior**：STATUS.md 声称"57 通过 / 0 失败 / 0 警告（机器实测）"；
  且作为"唯一口径"，该数字应在当前 HEAD 可复现。实际 HEAD 上 validate.py 必失败
  （fixture PDF 不存在于干净检出，或存在但 <102400B），**声称值与磁盘实据不符**，
  且干净检出根本无法复现"57/0/0"。
- **Why it matters**：STATUS.md 自封"状态数字唯一出处 + 绑定 commit hash"，是治理
  铁律的锚点；一条声称数字无法在当前 HEAD 复现，破坏整个 Source-of-Truth 契约，
  会让下游（AGENTS.md 交付门禁、README 宣称的"57 项校验"）引用失效。
- **Evidence**：本次 validate.py 实测输出；`git ls-files tests/fixtures/.../paper/`
  仅 main.tex；`git check-ignore` 返回 NOT-IGNORED；`git status` 未列出该 PDF
  （实际为 untracked，见下 Reproduction）。
- **Reproduction**：`py -3.12 core/tools/validate.py`（HEAD d44384c，无本地手工
  放大 fixture PDF 的前提下）→ 56/1/0。
- **Proposed fix**：二选一：(a) 在仓库内提交一个 ≥102400B 的 fixture PDF（或让
  PDF 检查跳过 fixture 目录/只在活跃项目实例上运行）；(b) 若确认为本地环境差异，
  将 STATUS.md 数字改注"受本地 fixture 生成影响"并给出可复现命令。修复后重跑
  validate.py 至 57/0/0 再更新 STATUS.md。
- **Regression risk**：低（只影响 fixture 检查口径）。
- **Test required**：`validate.py` 退出码 0；STATUS.md 数字与实测一致。

### H-002 — High — 可复现性/完整性：K003 formal_results.json 在审计期间被后台进程原地改写，出现与 run_summary.json 冲突的瞬时状态

- **File**：`research/P15/experiments/P15-K003/formal_results.json`（对比
  `run_summary.json`）
- **Function-Symbol**：`run_code_pipeline` / Organizer 后台生成链路（commit
  d44384c 所描述的重建管线）
- **Line**：—（数据文件）
- **Observed behavior**：审计期间三次读取同一路径：
  1) 首次读取：`fidelity_status` 分布 `{misaligned: 39, aligned: 27, unverifiable: 0}`，
     与 run_summary.json 的 `{misaligned: 26, aligned: 18, unverifiable: 22}` **冲突**；
     且 `files` 字段仅为文件名列表（无 outputs/code_hash）。
  2) 文件 mtime 显示 18:55:16 被重写（run_summary.json 为 16:43:54）。
  3) 复读 + `git show HEAD:…formal_results.json`：分布变为
     `{misaligned: 26, unverifiable: 22, aligned: 18}`，与 run_summary 一致，
     工作区与 HEAD 一致（git status 干净）。
- **Expected behavior**：实验结果产物在"FROZEN/生成中"阶段应可写，但**已提交到
  git 的产物文件不应在审计窗口内被原地改写并出现与配套 summary 冲突的瞬时
  状态**；任何写回应原子化、先校验一致性、再落盘/提交。
- **Why it matters**：K003 是当前主实验（66 runs，五 Gate 后 FROZEN）；消费
  formal_results.json 的下游（配对分析、P15-K003-REPORT）若在冲突窗口运行会产出
  与 run_summary 矛盾的数字（27/39/0 vs 18/26/22）。这与 K002 的 E02 残留事件
  同类——实验数据的"确定性复现"承诺被后台可变产物破坏。当前无任何门禁在提交时
  校验 formal_results ↔ run_summary 的一致性。
- **Evidence**：三次读取输出 + mtime（18:55 vs 16:43）+ `git show HEAD` 对照 +
  `git status`（终态干净）。HEAD 提交 d44384c 的 message 声称 "run_summary
  recomputed" 但未提及 formal_results.json 需重建——重建发生在提交之后。
- **Reproduction**：连续读取
  `research/P15/experiments/P15-K003/formal_results.json` 的 `fidelity_status`
  分布（在 Organizer 后台运行期间可能观察到 27/39/0 瞬时态）。
- **Proposed fix**：(a) 生成器写 formal_results.json 前先做 run_summary 交叉校验，
  不一致则 fail-closed；(b) 产物落盘原子化（临时文件 + rename）；(c) 提交门禁
  （pre-commit 或 catalog/validate 扩展）校验 K003 产物一致性；
  (d) STATUS.md 明确"正式实验产物在最终报告定稿前不被冻结承诺"。
- **Regression risk**：低。
- **Test required**：新增一致性测试：formal_results 与 run_summary 的
  by_arm / by_fidelity / exec_success 全等，否则抛错。

### H-003 — Medium — Schema 治理：registry.create 无 payload schema 门禁；"真 jsonschema" 仅存在于 P15 独立脚本且含硬编码路径

- **File**：`core/runtime/artifacts/registry.py`（create/_create_locked）；
  `core/tools/gatelib.py`（_validate）；`research/P15/model_representation/validate_example.py`
- **Function-Symbol**：`ArtifactRegistry.create` / `_create_locked`；
  `gatelib._validate`；`validate_example.py` 顶层
- **Line**：registry.py:108-145；gatelib.py:240-270；validate_example.py:5-7
- **Observed behavior**：`create()` 只调用 `art.validate()`（Artifact 结构/引用契约），
  不加载 `core/schemas/v3/artifact/artifact.schema.json` 校验 payload；
  gatelib 的 `_validate` 是自研子集（仅 type/required/properties/minItems/items），
  非完整 JSON Schema；K002 声称的 "register 真 jsonschema" 只在
  `research/P15/model_representation/validate_example.py` 中通过
  `Draft202012Validator` 实现，且 `SCHEMA_PATH` 为**硬编码绝对路径**
  `C:\Users\Lin\Desktop\Programs\MathModel\...`。
- **Expected behavior**：核心契约（artifact.schema.json / model_ir.schema.json 等）
  应在 runtime 登记路径被强制校验；schema 校验代码应使用仓库相对路径。
- **Why it matters**：无 payload schema 门禁 = registry 可登记不符合 canonical
  schema 的 artifact，违反 "schema 单一真源 + 契约校验" 治理；硬编码绝对路径使
  校验脚本在任何其他机器/工作目录不可复现。
- **Evidence**：registry.py 源码（create 无 jsonschema 引用）；gatelib.py
  docstring "不引入 jsonschema 依赖"；validate_example.py SCHEMA_PATH 硬编码。
- **Reproduction**：阅读源码；`py -3.12 -c "from core.runtime.artifacts.registry
  import ArtifactRegistry; import inspect; print('jsonschema' in
  inspect.getsource(ArtifactRegistry.create))"` → False。
- **Proposed fix**：(a) 为 registry.create 增加可选的 schema 校验钩子
  （canonical entity → v3 schema 映射已在 `core/runtime/domain/__init__.py`）；
  (b) 将 P15 的 jsonschema 校验收敛到 core（如 core/runtime/schema.py）；
  (c) validate_example.py 改用 `Path(__file__)` 相对路径。
- **Regression risk**：中（若强制校验现有写入路径可能暴露历史脏数据）。
- **Test required**：单测——向 registry.create 注入违反 artifact.schema.json 的
  payload 应被拒绝。

### H-004 — Medium — 死代码/术语残留：core/validators/modules/ 下 21 个模块全部未被任何代码导入执行

- **File**：`core/validators/modules/*.py`（21 个模块）；`core/tools/validate.py`
  （check_* 系列）；`core/tools/gatelib.py`
- **Function-Symbol**：`validate.py:check_symbol_registry` 等 21 个 check_*
- **Line**：validate.py:687-887（仅 `py_path.exists()` 存在性检查）
- **Observed behavior**：全仓 grep `validators\.modules\.` / `from core.validators.modules import`
  在 core 与 tests 中 **0 命中**；validate.py 对这 21 个模块只做 `exists()` 检查
  （"文件在不在"≠"功能通不通"）；实际护栏逻辑在 gatelib.py 自包含实现；
  catalog.yaml 的 resources 引用这些路径，营造"被使用"假象。
- **Expected behavior**：模块要么被真实接线（import + 调用），要么标记 deprecated
  并移出 catalog resources，避免"声称有门禁、实际未执行"。
- **Why it matters**：与治理铁律"门禁由脚本判定，不是文件存在即通过"直接冲突；
  这些模块是 L1–L6 六层防御叙述的载体，但从未运行——安全假象。
- **Evidence**：grep 0 命中；validate.py 源码（`return False, "...不存在"` 模式）。
- **Reproduction**：`rg "validators\.modules" core tests` → 无导入语句。
- **Proposed fix**：审计后二选一：(a) 将 21 个模块并入 gate 链（gatelib 或
  runtime validator 实际调用）；(b) 移入 `core/legacy/` 并更新 catalog resources
  与 validate.py 检查口径（改为检查 gate 链实际接线）。
- **Regression risk**：中（若直接删除需确认无动态 import，如 importlib）。
- **Test required**：import 扫描测试：断言生产代码无指向 modules/ 的悬空引用，
  或断言每个模块至少被一个 gate 消费。

### H-005 — Medium — 文档一致性：README 与 catalog 注释声称 "15 节点 / 6 validator"，实际为 20 节点 / 7 validator

- **File**：`README.md`（行 18）；`catalog.yaml`（行 4 注释）；`catalog/v3.yaml`
  （行 24、94 注释）；`core/workflows/stages/*.yaml`
- **Function-Symbol**：—（元数据注释）
- **Line**：README.md:18；catalog.yaml:4；catalog/v3.yaml:24,94
- **Observed behavior**：catalog/v3.yaml 实际列出 20 个 node、7 个 validator；
  workflow stage yaml 节点合计 2+8+3+3+4=20；但三处注释与 README 均写
  "15 节点（+ 5 角色 + 6 validator）"。`catalog_check.py --check` 不校验注释数字，
  故全绿。
- **Expected behavior**：注释/README 中的架构数字与 registry 实列一致。
- **Why it matters**：README 是外部读者对架构的第一认知；节点数差异（15→20，含
  P1-M3 新增 model_selection_decision 等）未被同步，属文档与代码漂移。
- **Evidence**：v3.yaml 计数（20/7）；stage yaml 逐文件节点计数。
- **Reproduction**：`py -3.12 -c "import yaml; d=yaml.safe_load(open('catalog/v3.yaml',
  encoding='utf-8')); print(len(d['v3']['nodes']), len(d['v3']['validators']))"` → 20 7。
- **Proposed fix**：更新 README.md:18 与两处 catalog 注释为"20 节点 + 7 validator"
  （或改为不加数字的动态表述）。
- **Regression risk**：无。
- **Test required**：catalog_check 增加注释数字与 registry 计数一致性断言（可选）。

### H-006 — Medium — Source of Truth/多状态文件并存：README 研究表与 HANDOFF.md 与 STATUS.md 数字冲突

- **File**：`README.md`（行 106、128）；`HANDOFF.md`（行 4-11）；`docs/STATUS.md`
- **Function-Symbol**：—（状态文档）
- **Line**：README.md:106（K002 "38 文件"、"正式实验在 P1 闭环之后执行"）、
  128（"项目级 57 项校验"）；HANDOFF.md:4-11（"当前活跃任务：P15-K002 正式实验
  执行"，882 passed / 4 skipped，v3.1.1/9199f03）
- **Observed behavior**：
  - README 研究表：K002 仍标 `🔒 FROZEN（38 文件哈希锁定）`，未提 K003；
    STATUS.md 与实测：K002 已 **CLOSED**、**40 文件**、K003 已 FROZEN。
  - README 行 128 宣称"项目级 57 项校验"，与 H-001 的实测 56/1/0 冲突。
  - HANDOFF.md 宣称当前任务为 K002 正式实验、882/4；STATUS.md 为 911/4、
    K002 CLOSED、K003 66 runs 生成中。
- **Expected behavior**：按"状态单一真源"铁律，仅 STATUS.md 承载当前数字；
  README/HANDOFF 应同步或标注 archive，不得承载互相冲突的活跃数字。
- **Why it matters**：STATUS.md 自身即记载"双真源问题档案"（228/574/751/774/855
  多套旧数字并存作废），但当前 README + HANDOFF 又在制造新的第二/第三真源，
  违反治理初衷。
- **Evidence**：三文件逐行对照；实测 911/4、K002 freeze 40 文件。
- **Reproduction**：对比 README.md:106 vs STATUS.md:41；HANDOFF.md:9 vs STATUS.md:48。
- **Proposed fix**：(a) README 研究表同步为 K002 CLOSED（40 文件）+ K003 FROZEN；
  (b) HANDOFF.md 更新或改名为 `HANDOFF_ARCHIVE_20260908.md` 并加"仅存档"头；
  (c) 在 STATUS.md 增补"其他文档若含状态数字以本文件为准，自动视为 stale"声明
  （已有，但需执行）。
- **Regression risk**：无。
- **Test required**：文档 lint：全仓 *.md 中与 STATUS.md 冲突的数字列表告警。

### H-007 — Medium — Git 卫生：生成产物/运行状态/大二进制误入库

- **File**：`.gitignore`（未覆盖）；git 追踪文件（`git ls-tree -r -l HEAD`）
- **Function-Symbol**：—
- **Line**：—
- **Observed behavior**：git 中追踪的 >512KB 文件包括：
  - `core/legacy/hands/Writer/knowledge/templates/mathmodel/zh/cumcm/simsun.ttc`（18.0MB）
    + `simkai.ttf`（11.8MB）——二进制字体；
  - `research/P15/experiments/P15-K003/state/registry.json`（1.77MB）、
    `research/P15/m3_run|vs001_run|m4_run/project/state/registry.json`（各 ~1.4MB）、
    `P15-K003-precheck/state/registry.json`（555KB）——实验运行状态文件；
  - `research/REPOSITORY_AUDIT/src/.../model-dictionary.json`（8.67MB）——外部仓库
    快照；
  - `projects/` 下 232 个文件（p151-*、rcs1-2024a、v3-real-* 运行实例）。
  K003 实验目录共追踪 1056 文件（bundles 352 个）。
- **Expected behavior**：运行实例的 `state/registry.json`、生成 bundles 属派生产物，
  按"生成产物应被 ignore 或在特定目录"原则应排除或使用 hash 摘要入库；
  字体应作为 release asset/LFS 管理。当前 .gitignore 仅忽略 `work/_*`、`*.log`、
  `_checkpoints/`、`projects/testproj*`、`projects/regtest*`，未覆盖上述路径。
- **Why it matters**：仓库体积膨胀（>40MB 二进制 + 数 MB 状态 JSON），clone/审计
  变慢；运行状态入库使"产物可复现性"与"源码版本控制"边界模糊（状态文件本应由
  `state.py reconcile` 重建而非入库）。
- **Evidence**：`git ls-tree -r -l HEAD` 输出；`git ls-files projects | measure` = 232；
  `git ls-files research/P15/experiments/P15-K003 | measure` = 1056。
- **Reproduction**：`git ls-tree -r -l HEAD | ... > 524288`。
- **Proposed fix**：分类处理：(a) 实验 registry/状态加入 .gitignore（保留 hashes/
  summary 入库）；(b) 字体移入 release asset 或 `assets/`（git LFS）；(c)
  REPOSITORY_AUDIT 外部快照保留 provenance 文件 + 压缩归档；(d) 对已有历史可
  用 `git filter-repo`（需用户决策，只读审计不做）。
- **Regression risk**：中（涉及历史提交改写需谨慎；仅对新增路径做 ignore 则低）。
- **Test required**：仓库体积/派生产物清单 CI 检查。

### H-008 — Low — Git 卫生：.gitignore 重复条目

- **File**：`.gitignore`
- **Function-Symbol**：—
- **Line**：57、61（`projects/regtest*` 出现两次）
- **Observed behavior**：`projects/regtest*` 在 .gitignore 第 57 行与第 61 行重复。
- **Expected behavior**：单一条目。
- **Why it matters**：低；反映 .gitignore 维护未走统一 diff 流程（最近一次
  `1eee789` 追加 `.workbuddy/` 时连带重复了上一行）。
- **Evidence**：文件读取。
- **Proposed fix**：删除第 61 行重复条目。
- **Regression risk**：无。
- **Test required**：无（视觉检查）。

### H-009 — Low — Documentation：AGENTS.md 测试基线数字陈旧

- **File**：`AGENTS.md`
- **Function-Symbol**：—（"修改后必做"）
- **Line**：157（`py -3.12 -m pytest tests -q  # 758 passed / 11 skipped（基线）`）
- **Observed behavior**：声称基线 758 passed / 11 skipped；实测 911 passed / 4 skipped。
- **Expected behavior**：AGENTS.md 的"修改后必做"基线应指向 STATUS.md 当前口径，
  或注明"以 STATUS.md 实测为准"。
- **Why it matters**：交付门禁的对照基准错误会让提交者误判回归。
- **Evidence**：AGENTS.md:157 + pytest 实测。
- **Proposed fix**：更新为 911/4，或改为"数字以 docs/STATUS.md 为准"。
- **Regression risk**：无。
- **Test required**：无。

### H-010 — Low — 可复现性：P15 校验脚本硬编码绝对路径 + 遗留 superseded schema 副本

- **File**：`research/P15/model_representation/validate_example.py`；
  `research/P15/model_representation/model_ir.schema.json`
- **Function-Symbol**：`SCHEMA_PATH`（模块级）
- **Line**：validate_example.py:7
- **Observed behavior**：`SCHEMA_PATH = r"C:\Users\Lin\Desktop\Programs\MathModel\
  research\P15\model_representation\model_ir.schema.json"`——机器专属绝对路径；
  P15 副本 schema 与 core 版已分叉（P15 版含 `x_superseded_by: core/schemas/v3/
  model/model_ir.schema.json` 标记，属 2026-09-09 治理迁移），但文件仍留在原地，
  且模板/校验脚本仍可能引用。
- **Expected behavior**：脚本应使用仓库相对路径；superseded 副本应移入 archive 或
  删除（保留迁移记录即可）。
- **Why it matters**：硬编码路径在任何其他环境（CI/他人机器）不可复现；双 schema
  副本长期存在是漂移隐患（目前靠 x_superseded 标记缓解）。
- **Evidence**：文件读取；JSON diff（core vs P15 版不等，P15 版带 superseded 标记）。
- **Reproduction**：从其他工作目录运行 validate_example.py 会 FileNotFoundError。
- **Proposed fix**：(a) 改为 `Path(__file__).resolve().parent / ...`；(b) 将 P15 副本
  移入 `research/P15/archives/` 并更新引用。
- **Regression risk**：低。
- **Test required**：从任意 cwd 运行脚本通过。

### H-011 — Info — Archival/可复现性：K003 盲评原始数据（raw_k003/）未入库；REPOSITORY_AUDIT 内嵌外部仓库快照

- **File**：`research/P15/analysis/raw_k003/`（untracked）；`research/REPOSITORY_AUDIT/src/`
- **Function-Symbol**：—
- **Line**：—
- **Observed behavior**：`git status` 显示 `research/P15/analysis/raw_k003/`（含
  scores/、compute_kappa.py、EVALUATOR_INSTRUCTIONS.md）**未追踪**；
  REPOSITORY_AUDIT/src/ 内含另一仓库（BZD skills）的完整副本（数百文件，含
  8.67MB model-dictionary.json），以审计证据形式归档。
- **Expected behavior**：K003 盲评分数是正式结论的核心证据，应随实验定稿入库
  （带哈希/审计记录，避免重演 K002 E02 残留污染）；外部快照应压缩归档并保留
  来源与抓取日期 provenance。
- **Why it matters**：盲评原始分数缺失 = K003 正式报告不可从 git 复现；
  外部快照未压缩 = 仓库膨胀且来源不可追溯（若 provenance 未写清）。
- **Evidence**：git status untracked 输出；REPOSITORY_AUDIT 目录清单。
- **Reproduction**：`git ls-files research/P15/analysis/raw_k003` → 空。
- **Proposed fix**：K003 盲评收尾时按 K002 流程提交 raw scores + 分配/校准审计
  记录；REPOSITORY_AUDIT 外部快照加压缩包 + SOURCE_PROVENANCE 索引。
- **Regression risk**：低。
- **Test required**：实验定稿检查：raw_k003 内容全部入库且 hash 可校验。

### H-012 — 核验通过项（非缺陷，记录证据）

- **Terminology**：`catalog_check.py --check-terminology` → OK（production 零残留）；
  `core/runtime/domain/__init__.py` 的 CANONICAL_ENTITIES 同义词回收表与 docs 术语
  （MODEL_IR / ExecutionResult / Evidence / Validation / Revision）一致；docs/
  architecture 检索未见 V2 术语混入 V3 主体。
- **Catalog 三方一致性**：`catalog_check.py --check` → OK。
- **冻结哈希**：K001/K002/K003 全部 PASS、零漂移，root sha 与 STATUS.md 前缀一致。
- **pytest 声称**：911/4 与 STATUS.md 一致。
- **Git 历史健康度**：`git log --oneline -30` 未见 "fake/placeholder/hardcode"
  性质提交（`d44384c` 的 message 描述的是**已修复**的 fabrication 事件，属如实
  披露）；commit message 采用 conventional 风格（feat/fix/docs/chore + 范围）。
  `.gitignore` 共 5 次提交，最近一次 `1eee789` 追加 `.workbuddy/`（合理）。

---

## 七、结论摘要

1. **冻结与测试基础设施可信**：911/4、catalog 三方一致、三组冻结哈希全部实测
   PASS——STATUS.md 的"硬"数字（可脚本复测项）大体准确。
2. **两个 High 需优先处理**：H-001（validate.py 声称 57/0/0 与 HEAD 实测 56/1/0
   不符，且 fixture PDF 未入库导致不可复现）；H-002（K003 formal_results.json 在
   审计期间被后台进程原地改写并出现与 run_summary 冲突的瞬时态，提交后无一致性
   门禁）。
3. **治理结构性问题**：README/HANDOFF 与 STATUS.md 的多状态文件并存（H-006）
   正是 STATUS.md 自身宣称要消灭的"双真源"复发；21 个 validator 模块死代码
   （H-004）与 registry.create 无 schema 门禁（H-003）表明"声明能力"与"实测行为"
   之间存在系统性落差。
4. **建议优先级**：H-001/H-002（阻断）→ H-006/H-004/H-003（治理修复）→
   H-005/H-007/H-010（文档与仓库卫生）→ H-008/H-009/H-011（收尾）。

---

*审计官：Agent H（独立仓库治理审计）｜ 审计基线 commit：`d44384c` ｜
审计日期：2026-09-09 ｜ 方法：命令实测 + git 对账 + 源码阅读，全程只读（仅写入
本 FINDINGS.md）。*
