# MathModel 架构审计报告 — Agent A（整体架构 / 依赖方向 / 模块边界 / 数据流 / core-runtime 分层）

- 审计时间：2026-09-09
- 审计员：Agent A（独立架构审计官，只读）
- 仓库：`C:\Users\Lin\Desktop\Programs\MathModel`（HEAD = `d44384c`）
- 审计模式：只读。仅使用 Read/Grep/Glob/ast 静态解析/只读 Python 脚本，未修改任何仓库文件。

---

## 审计范围摘要

对以下范围做了**静态代码证据审计**（全部结论附磁盘证据，不采用"代码看起来合理"判断）：

1. **import 依赖图**：用 AST 解析器对 `core/`（排除 `__pycache__`）全部 250+ Python 文件构建模块级依赖图（90 条内部边），并用 Tarjan SCC 做环检测；同时检测核心链对 legacy 层的 import。
2. **orchestrator.py**：全文阅读，核对 `--legacy` / 默认干跑 / `--execute` 三条路径实际调用栈。
3. **四个核心组件**：`core/runtime/artifacts/registry.py`、`core/runtime/graph/evidence_graph.py`、`core/runtime/state/model.py`、`core/runtime/execution/{dag,composer,engine,wave_executor,session,handlers}.py` 逐一核对实现与互相接线。
4. **契约与 schema**：对 `core/runtime/contracts.py` 全部符号做全仓引用扫描；对 `core/schemas/` 27 个 schema 做消费方扫描（jsonschema / gatelib mini-validator / validate.py）。
5. **死代码**：模块级引用计数 + tests/ 引用核对。
6. **Git 历史**：最近 30 条 commit（含 `d44384c` "REAL EXECUTION rebuild — generator fabricated execution_result"）。

## 发现计数（按 severity）

| Severity | 数量 | 含义 |
|---|---|---|
| P0（科学诚信） | 0 | 未发现当前生产链直接造假证据（历史造假事件在 research 层，已修复重建） |
| P1（loop 断裂） | 2 | A-001, A-002 |
| P2（validation/revision 弱点） | 2 | A-003, A-004 |
| P3（架构/可维护性） | 6 | A-005, A-006, A-007, A-008, A-009, A-010 |
| P4（文档/外观） | 3 | A-011, A-012, A-013 |
| **合计** | **13** | |

## 核心架构结论（5 条）

1. **V3 runtime 是真实的、可执行的分层实现，不是空壳。** `RuntimeSession` 把四个核心组件（ArtifactRegistry / EvidenceGraph / ProjectState / WorkflowDAG）真实接线：`session.run() → WaveExecutor → WorkflowEngine → DefaultNodeExecutor(handlers) → LocalPythonAdapter 真 subprocess → run_numeric_validation 真数值校验`。`orchestrator --execute` 走的就是这条 production path（证据见 B-3/B-4）。
2. **模块级 import 图无环（无多模块 SCC），V3 与 V2 legacy 边界干净。** 核心链对 `core/legacy/hands/`（V2 29-agent 层）**零 import**；唯一 legacy 触点 `core/tools/state.py → runtime.legacy.convert` 是 V3 内部的 V2→V3 适配器，只依赖 Registry/Graph/State。
3. **但"契约冻结"与"schema 校验"两大治理机制是装饰性的：未接线。** `contracts.py` 全部谓词在 core/ 中零调用（0 个 import 点），终态元组反而在 ≥10 个文件中内联；27 个 schema 中 v3 schema 无任何数据校验消费方（pyproject 连 jsonschema 依赖都没有）。这正是该模块 docstring 声称要消灭的"口径分裂"。
4. **V2 legacy 编排路径已断裂（P1）。** `orchestrator.py --legacy` 的 `_skill_path()` 仍指向迁移前路径 `core/<Hand>/agents/<agent>/SKILL.md`（实际在 `core/legacy/hands/<Hand>/...`），**每一步**都会以 "SKILL.md 不存在" 失败；`state.py status` 打印的下一步 SKILL 路径同样过期。catalog.yaml（单一真源）路径正确，说明是调用方硬编码绕过真源。
5. **存在两条并行执行管线与一个孤岛子系统。** 生产链 = handlers 内联执行（adapters + validation）；`codegen.py + fidelity.py` 是另一条完整管线（register→execute→fidelity→run_code_pipeline），仅测试/CLI 可达，不在 runtime 生产链上；`writing/{paragraphs,expression,patterns,fact_check,redundancy}` 是只被 tests 引用的写作质量孤岛。多管线并存是"REAL EXECUTION rebuild"造假事件的结构性土壤。

---

## Finding 明细

### A-001 [P1] orchestrator.py `--legacy` 模式的 SKILL 路径全部失效，29 步流水线一步都跑不起来

- **File**: `core/tools/orchestrator.py`
- **Function/Symbol**: `_skill_path`（L58-59）/ `_execute_step`（L141-143）/ `main`（L525-527）
- **Line**: 58-59, 141-143
- **Observed behavior**: `_skill_path` 构造 `ROOT / "core" / hand.capitalize() / "agents" / agent / "SKILL.md"`，即 `core/Modeler/agents/problem-parser/SKILL.md`。该目录在迁移后已不存在（实际路径 `core/legacy/hands/Modeler/agents/problem-parser/`）。`_execute_step` 先判 `skill_path.exists()`，对 29 个 agent 全部返回 `(False, "SKILL.md 不存在: ...")`；`_retry_step` 重试 3 次后仍失败，`_run_pipeline` 因消息不含 "block"/"refine" 直接 `return 1`。因此 `python core/tools/orchestrator.py <项目> --legacy` 在第一步即失败退出。
- **Expected behavior**: `--legacy`（AGENTS.md 文档化为 "V2 legacy：一键执行 29 步流水线"）应能读取 `core/legacy/hands/<Hand>/agents/<agent>/SKILL.md` 并推进流水线。
- **Why it matters**: AGENTS.md 命令速查表把 `orchestrator.py <项目> --legacy` 列为 V2 兼容模式的一键入口，当前完全不可用；同时 `_skill_path` 绕过了 catalog.yaml 这一"结构单一真源"（catalog 已指向正确路径），是路径硬编码与真源脱节的直接证据。
- **Evidence**（只读验证输出）：
  ```
  py -3.12 -c "import orchestrator as O; p=O._skill_path('modeler','problem-parser')..."
  skill path: C:\Users\Lin\Desktop\Programs\MathModel\core\Modeler\agents\problem-parser\SKILL.md
  exists: False
  core/Modeler exists: False
  actual legacy dir exists: True
  ```
  对照 `catalog.yaml` L13-16：`hands: - name: modeler  path: core/legacy/hands/Modeler`。
- **Reproduction**: `py -3.12 core/tools/orchestrator.py --legacy <任一项目>`（无需真实执行：静态路径检查已证 exists=False；如需端到端，首次调用即输出 "SKILL.md 不存在"）。
- **Proposed fix**: `_skill_path` 改为读 `catalog.yaml` 的 `hands[].agents[].path`，或直接指向 `core/legacy/hands/<Hand>/agents/<agent>/SKILL.md`；在 `catalog_check.py --check` 中增加"orchestrator/state 的 SKILL 路径与 catalog 一致"断言。
- **Regression risk**: 低。仅修复路径解析；不影响 V3 默认路径。若同时改动 PIPELINE 定义需与 catalog 保持三方一致（catalog_check 已强制）。
- **Test required**: 单测：对 catalog 中全部 29 个 agent 断言 `_skill_path` 存在；e2e：`--legacy --dry-run` 能打印 29 步而非在第一步失败。

### A-002 [P1] `state.py status` 打印的下一步 SKILL 路径过期，V2 续跑指引失效

- **File**: `core/tools/state.py`
- **Function/Symbol**: `cmd_status`（L361）
- **Line**: 377
- **Observed behavior**: `cmd_status` 打印 `读: {hand.capitalize()}/agents/{agent}/SKILL.md`（如 `Modeler/agents/problem-parser/SKILL.md`），相对仓库根也不存在（真实路径 `core/legacy/hands/Modeler/agents/...`）。`state.py init` 反推/续跑流程指引 Agent 去读不存在的文件。
- **Expected behavior**: 打印的 SKILL 路径应真实存在（`core/legacy/hands/...`），或改为引用 catalog.yaml。
- **Why it matters**: AGENTS.md V2 兼容模式第 2 步"读指令：读它指出的那一个 core/legacy/hands/.../SKILL.md"——CLI 指引与文档/真源三方不一致，续跑协议在实际环境中无法按提示执行。
- **Evidence**: `core/tools/state.py` L377：`print(f"  读:   {str(cur.get('hand','')).capitalize()}/agents/{cur.get('agent')}/SKILL.md")`；对照 A-001 的目录存在性验证。
- **Reproduction**: 任一含 `work/state.json` 的项目运行 `py -3.12 core/tools/state.py <项目> status`，观察 "读:" 行路径不存在。
- **Proposed fix**: 与 A-001 同源修复：从 catalog.yaml 派生 SKILL 路径。
- **Regression risk**: 低。
- **Test required**: 与 A-001 合并断言。

### A-003 [P2] `contracts.py` 契约冻结层零接线：谓词从未被生产代码调用，终态元组在 ≥10 处内联

- **File**: `core/runtime/contracts.py`（全文件）；违反方含 `core/runtime/execution/handlers.py` L31、`core/runtime/artifacts/lifecycle.py` L24、`core/runtime/graph/evidence_graph.py` L283/304/431、`core/runtime/artifacts/artifact.py` L124/139、`core/runtime/state/dependencies.py` L52、`core/runtime/writing/fact_check.py` L20、`core/runtime/writing/director.py` L83-84、`core/runtime/writing/findings.py` L183、`core/runtime/writing/narrative_ir.py` L24、`core/runtime/writing/paragraphs.py` L326/342
- **Function/Symbol**: `is_reusable`/`is_terminal`/`can_support_claim`/`can_enter_paper`/`validate_node_result_outputs`/`ContractViolation`/`requires_reuse_check`
- **Line**: 39-122（定义处）
- **Observed behavior**: 全仓扫描 `from runtime.contracts|from .contracts|runtime.contracts|contracts import` = **0 匹配**（core/ 无任何文件 import contracts.py）。`validate_node_result_outputs` 仅在自身定义与 `tests/integration/test_p7_integrity.py` 中出现，生产链（engine.apply_result / handlers / session）从不调用；`ContractViolation` 从无人 raise；`requires_reuse_check` 是 no-op 装饰器（docstring 自认"文档用，无行为"）。与此同时 `("invalidated", "superseded", "deprecated")` 元组在 10+ 个文件中内联重复（handlers L31 的 `_TERMINAL` 即一例）。
- **Expected behavior**: contracts.py docstring 声明"handlers / gate / critic / tools 一律 import 这里的谓词，禁止各自内联元组（P6 修的 E1/E2/E3/E4/N2 口径分裂即由此而来）"——即谓词应被生产代码引用，终态判断应收敛到单一真源。
- **Why it matters**: 契约冻结层是 P7 验收项（test_p7_integrity 的 A–K 清单）声称的语义不变量单一真源；实际只是"可导入的常量表"，生产代码各写各的元组。一旦某处漏掉 `deprecated` 或新增终态，口径将静默分裂——正是该模块声称已修复的缺陷形态。NodeResult.outputs 多余键/缺字段也无任何运行时拦截。
- **Evidence**：
  - `core/runtime/contracts.py` L59-61：`def requires_reuse_check(fn): """装饰器：标注该 handler/函数已按契约做终态复用检查（文档用，无行为）。""" return fn`
  - grep 全仓 `contracts import`：0 命中；grep `_TERMINAL|"invalidated", "superseded"`：46 命中（10+ 文件）。
  - `test_p7_integrity.py` L20-23 import contracts 谓词并直接单测谓词本身——**不**断言生产代码调用它们。
- **Reproduction**: `Select-String -Path core\**\*.py -Pattern 'from runtime.contracts' -Recurse` → 0 命中。
- **Proposed fix**: (1) handlers/evidence_graph/lifecycle/artifact/dependencies/writing 全部改为 import `contracts.is_terminal/is_reusable/can_enter_paper`；(2) engine.apply_result/_post_execute 中调用 `validate_node_result_outputs(result.outputs)`，违约即 FAIL（fail-closed）；(3) 删除 no-op 装饰器或实现真实行为；(4) 在 test_p7_integrity 增加"生产链调用谓词"的接线断言（import 图级）。
- **Regression risk**: 中。若某个内联元组与契约语义存在差异（如 lifecycle 允许 `blocked` 状态而 contracts 的 ACTIVE_STATUSES 不含 blocked），收敛后会暴露既有行为漂移，需逐一核对状态表（lifecycle.py L28-32 与 contracts L23-24 已见不一致：`blocked` 不在 ACTIVE_STATUSES，但 lifecycle 允许 blocked↔active）。
- **Test required**: 接线测试（断言 handlers/evidence_graph 不出现内联终态字面量）；NodeResult 违约注入测试（多余键→FAIL）。

### A-004 [P2] v3 schema 全部无数据校验消费方，schema 层是装饰性的

- **File**: `core/schemas/v3/**`（27 个 schema 文件）；`core/tools/validate.py` L675-684；`core/tools/gatelib.py` L237-285；`pyproject.toml`
- **Function/Symbol**: `check_question_spec_schema`、`gatelib.check_schema/_validate`
- **Line**: validate.py 675-684；gatelib.py 237-285
- **Observed behavior**: (1) `validate.py` 的 L1.1 只检查 `question_spec.schema.json` **文件存在且 JSON 可解析**，不对任何数据做校验；(2) gatelib `check_schema` 是极简子集校验器（仅 `required`/`type`/`minItems`，无 enum/additionalProperties/$ref），且 gate.py GATES 中只对 V2 产物（question_spec、literature_evidence、model_dag）启用；(3) v3 schema（registry/graph/status/run_record/dag/decision）在 core/ 中除 `$id` 自引用与 `domain/__init__.py` 元数据外**零引用**；(4) pyproject.toml **无任何 runtime dependencies**（无 jsonschema/pydantic）；(5) `model_ir.py` 自述"不引 jsonschema"，仅手工对齐顶层 required。
- **Expected behavior**: schema 文件描述（如 model_ir.schema.json 自述"本重建使 jsonschema 校验成为真实可执行的门槛"）应反映真实校验接线：registry/status/graph/run_record 落盘前应经对应 schema 校验。
- **Why it matters**: 结构与文档宣称的"结构化输出通过对应 schema 校验"（AGENTS 铁律）不符；v3 状态文件（registry.json/status.json/evidence_graph.json/run_record.json）无任何机器门槛，格式漂移只能靠代码内部约定兜底。这是"看起来有校验、实际没有"的典型治理空洞。
- **Evidence**：
  - `validate.py` L677-684：`schema_path = ...; if not schema_path.exists(): return False,...; json.loads(schema_path.read_text(...)); return True, "question_spec.schema.json有效"`（只解析 schema 本身，无 data 校验）。
  - `gatelib.py` L240-241：`不引入 jsonschema 依赖，只实现本项目 schema 实际用到的关键字`；`_validate` 仅 required/type/minItems。
  - grep `registry\.schema|status\.schema|run_record\.schema|dag\.schema|graph\.schema`：命中均只在 schema 自身 `$id`、`domain/__init__.py` 描述、docstring/注释，无校验调用。
  - `pyproject.toml` L5-11：`[project] ... requires-python=">=3.8"`，无 dependencies 段。
- **Reproduction**: grep `core/schemas/v3` 中任意 schema 文件名在 core/ 源码中的引用，除注释/`$id` 外 0 校验调用。
- **Proposed fix**: (1) 为 registry/status/graph/run_record/dag 落盘点（session.checkpoint、registry.save、graph.save、state.save、runs.emit_run_record）接入真实 schema 校验（引入 jsonschema 或完整实现 gatelib 子集）；(2) validate.py 57 项中加入"V3 状态文件符合 v3 schema"校验；(3) 移除或重写 schema 文件内"真实可执行的门槛"等不实描述。
- **Regression risk**: 中。现有落盘数据若与 schema 存在漂移，接入后会批量 FAIL，需先修数据/修 schema 二选一（这正是该修复的价值）。
- **Test required**: 对每个 v3 schema 的 fixture 数据做通过/违例两侧测试；对 session.run 产物断言 schema 合规。

### A-005 [P3] `codegen.py + fidelity.py` 是生产链外的平行执行管线（测试/CLI 可达）

- **File**: `core/runtime/execution/codegen.py`（190 行）、`core/runtime/execution/fidelity.py`（227 行）
- **Function/Symbol**: `run_code_pipeline`、`verify_fidelity`、`check_fidelity`
- **Line**: codegen.py L136-172；fidelity.py L160-215
- **Observed behavior**: 模块级 import 扫描显示 codegen.py/fidelity.py 在 core/ 中**零引用方**；生产执行链（handlers.execute_code L376-441）自研 `LocalPythonAdapter + ExecutionPlan + run_numeric_validation`，不调用 codegen/fidelity。codegen 的 `run_code_pipeline`（register→execute→verify_fidelity 三合一）只被自身 `__main__` 与 `tests/integration/test_execution_codegen.py` 使用。fidelity（K002 声称的 model_fidelity 测量）不在 RuntimeSession 链路上。
- **Expected behavior**: 同一执行+保真语义应只有一条生产实现；fidelity 作为"第二扇门"应挂在 model_validation 节点（如 handlers.validate_execution 内），或 codegen 应被 handlers 复用。
- **Why it matters**: 两条管线各自实现"执行→验证"语义，容易漂移（一条被修复另一条遗漏）；且 git 历史 `d44384c`（"generator fabricated execution_result ... fidelity 18/26/22"）表明 fidelity 测量曾长期在 production path 之外由 research 层脚本代跑——孤儿管线是这类事故的结构性土壤。
- **Evidence**：
  - dead_scan 输出：`UNREFERENCED: core/runtime/execution/codegen.py`；fidelity 的唯一 core 引用方 = codegen.py。
  - `handlers.py` L404-408：`from runtime.execution.adapters import ExecutionPlan...; adapter = self.execution_adapter; if adapter is None: ... LocalPythonAdapter()`（生产路径不用 codegen）。
  - grep `run_code_pipeline`：仅 codegen.py 自身（L136 定义、L190 main 调用）与 tests。
- **Reproduction**: `Select-String -Path core\runtime\**\*.py -Pattern 'codegen|verify_fidelity'` 除 codegen/fidelity 自身外 0 命中。
- **Proposed fix**: 二选一：(a) handlers 复用 `run_code_pipeline`（消除重复执行语义）；或 (b) 明确声明 codegen 为 research 层工具并移出 core/runtime（避免被当作 runtime 能力）。至少将 `verify_fidelity` 接入 model_validation 节点。
- **Regression risk**: 中。若改 (a) 会影响真实执行产物路径与幂等键，需跑全量 integration（P1-VS-001 C6/C7/C8、test_execution_codegen）。
- **Test required**: 双管线一致性测试（同一 model_ir+code 经 handlers 与 codegen 得到等价 VR 判定）。

### A-006 [P3] 写作质量子系统（paragraphs/expression/patterns/fact_check/redundancy）是只被 tests 引用的孤岛

- **File**: `core/runtime/writing/{paragraphs,expression,patterns,fact_check,redundancy}.py`
- **Function/Symbol**: `PaperFactChecker`、`redundancy.detect`、`question_dependencies`、`ExpressionContext/...`
- **Line**: 各文件入口（paragraphs.py L21/L24 为孤岛内引用）
- **Observed behavior**: core/ 内对上述 5 模块的引用链为 `paragraphs → {expression, patterns}`，而 `paragraphs`/`fact_check`/`redundancy` 在 core/ 中零引用方；唯一消费方是 `tests/integration/test_writing_redteam.py`、`test_controlled_expression.py`、`test_paper_redteam.py`、`test_question_dependency.py`。生产叙事质量链路（handlers→judge_critic→narrative_critic）不使用这些受控表达/冗余检测/事实核查能力。
- **Expected behavior**: 若这些是论文阶段质量门禁，应在 Writer/判审链路（judge_critic 或 paper 投影后）接线；若仅作参考实现，应移出 runtime 或标注非生产。
- **Why it matters**: 质量能力"存在但不在执行链上"——论文事实核查（fact_check）与冗余检测在真实交付路径上没有生效；同时 5 个模块形成维护负担与"测试绿但生产没用"的假象。
- **Evidence**：
  - dead_scan：`UNREFERENCED: core/runtime/writing/{fact_check,paragraphs,redundancy}.py`；expression/patterns 仅被 paragraphs 引用。
  - `handlers.py` L42 import `runtime.writing.judge_critic`（生产）；`judge_critic.py` L66/87 import `narrative_critic`（生产）——不含上述孤岛模块。
- **Reproduction**: dead_scan 脚本输出；或 grep `from runtime.writing.fact_check` 在 core/ 中 0 命中（仅 tests）。
- **Proposed fix**: 在 `PaperProjection`/`JudgeCritic` 后接入 `PaperFactChecker`+`redundancy.detect` 作为论文质量 gate，或显式将孤岛模块降级为 `research/` 工具并移除 runtime 入口。
- **Regression risk**: 中（若接线）。低（若仅移动/标注）。
- **Test required**: 接线后对 test_paper_redteam 的场景跑端到端断言。

### A-007 [P3] `runtime/knowledge/intelligence.py`（CompetitionIntelligence）在 core/ 中零引用，仅测试可达

- **File**: `core/runtime/knowledge/intelligence.py`
- **Function/Symbol**: `CompetitionIntelligence`
- **Line**: 全文件
- **Observed behavior**: core/ 无任何模块 import `knowledge.intelligence`；唯一消费方 `tests/unit/test_competition_intelligence.py` L17。生产检索链（handlers→retriever/packs/candidates）不使用它。
- **Expected behavior**: 若为 P8 Competition Intelligence 的生产能力，应在 handlers 选型/候选竞技场中调用；否则标注为测试工具。
- **Why it matters**: 同名能力在代码与文档/测试中存在，但生产链不可达，容易让审计/新开发者误判该能力已生效。
- **Evidence**: dead_scan：`UNREFERENCED: core/runtime/knowledge/intelligence.py`；grep tests 命中 test_competition_intelligence。
- **Reproduction**: dead_scan 输出。
- **Proposed fix**: 明确三选一：接入 handlers、移入 research/、删除；至少加模块 docstring 标注"未接入生产链"。
- **Regression risk**: 低。
- **Test required**: 若接入，跑 test_competition_intelligence + P8 相关 e2e。

### A-008 [P3] execution ↔ knowledge 子包存在双向耦合（handlers→packs 与 packs→yamlio）

- **File**: `core/runtime/execution/handlers.py`（L93）、`core/runtime/knowledge/packs.py`（L88）
- **Function/Symbol**: `DefaultNodeExecutor.__init__` 内 `from runtime.knowledge.packs import load_competition_packs`；`packs.py` 顶部 `from runtime.execution.yamlio import ...`
- **Line**: handlers.py 93；packs.py 88
- **Observed behavior**: execution 依赖 knowledge（handlers→packs/retriever），knowledge 依赖 execution（packs→execution.yamlio）。Tarjan SCC 未检测到环（因为 handlers→packs 被推迟到函数体内、yamlio 不再回引 execution），但子包层面是双向依赖。
- **Expected behavior**: 依赖方向应单向（如 execution → knowledge；YAML 解析工具应放共享层而非 execution 子包）。
- **Why it matters**: 双向依赖使 knowledge 无法独立加载/测试，也为未来在 yamlio 中加入 execution 引用时形成真环埋雷。
- **Evidence**: import_graph2 输出：`knowledge -> execution`（packs.py L88 → execution/yamlio.py）；`execution -> knowledge`（handlers.py L93 → knowledge/packs.py）。
- **Reproduction**: 运行 import_graph2.py 查看子包依赖段。
- **Proposed fix**: 将 `yamlio` 移到共享层（如 `core/runtime/yaml_util.py` 或 `core/env`），knowledge 不再反向依赖 execution。
- **Regression risk**: 低（纯搬移，注意 import 面）。
- **Test required**: 全量 pytest + import 图断言（knowledge 不得 import execution）。

### A-009 [P3] "状态单一真源"铁律与双状态文件并存冲突（work/state.json vs state/status.json）

- **File**: `core/tools/state.py`（L107-110 state_path → work/state.json）、`core/runtime/state/model.py`（L64-67 → state/status.json）、AGENTS.md
- **Function/Symbol**: `state_path` / `ProjectState.__init__`
- **Line**: state.py 107-110；state/model.py 64-67
- **Observed behavior**: V2 CLI 状态机以 `projects/<p>/work/state.json` 为真源（29 步线性），V3 ProjectState 以 `projects/<p>/state/status.json` 为真源（Registry/Graph 派生）。二者并存且各自可写：V2 `advance/fail/reset` 只写 work/state.json，V3 session.run/checkpoint 只写 state/status.json。AGENTS.md 铁律写"状态单一真源：status.json 是流程状态投影（由事件重建），禁止多份状态文件并存"。
- **Expected behavior**: 单一真源或明确的双轨设计文档；`state.py status` 应明确标识读取的是哪一份。
- **Why it matters**: 铁律与实现冲突：同一项目存在两份可写状态文件，`state.py reconcile` 只能事后对账（且 V2→V3 映射是 hand 级粗粒度聚合，见 convert.py docstring），无法保证"投影由事件重建"的实时性。跨会话/跨模型续跑时可能对同一进度产生两份不一致视图。
- **Evidence**：
  - `state.py` L107-110：`def state_path(project): return project_dir(project) / "work" / "state.json"`
  - `state/model.py` L64-67：`self.path = Path(path); ... if self.path.exists(): self.load()`（由 session 以 `state/status.json` 调用）
  - `convert.py` L126-131：映射规则注明"粗粒度但保守"。
  - projects/ 下实存 V2 项目（p151-*）与 V3 项目（v3-real-2024a*）并存。
- **Reproduction**: 对任一 V3 运行项目同时查看 `work/state.json`（若存在）与 `state/status.json` 的进度口径。
- **Proposed fix**: 短期：在 `state.py status`/AGENTS.md 中明确"V2 线性态仅 legacy 兼容，V3 真源为 status.json"；中期：V2 CLI 的 advance/fail 在写 work/state.json 时同步触发 convert 更新 status.json，或逐步退役 V2 命令。
- **Regression risk**: 中（涉及 V2 兼容行为，需保持 V2 工具链 zero-change 消费承诺）。
- **Test required**: 双状态一致性测试（advance 后 reconcile OK）。

### A-010 [P3] RuntimeSession 未接线 engine validator 钩子（session docstring 声称的 P6-⑤ 不生效）

- **File**: `core/runtime/execution/session.py`（L84-88）、`core/runtime/execution/wave_executor.py`（L28-33）
- **Function/Symbol**: `RuntimeSession.__init__` / `WaveExecutor.__init__`
- **Line**: session.py 84-88；wave_executor.py 30-31
- **Observed behavior**: `RuntimeSession` 构造 `WorkflowEngine(dag, executor_impl, state=..., on_success=...)` 时**不传 validators**；随后 `WaveExecutor` 内部又新建 `WorkflowEngine(dag, executor, state=state, validators=None)`（L30-31），并用 `self.engine = self.waves.engine` 覆盖——最终引擎 `self.validators = {}`。引擎的 `_run_validator`（engine.py L169-179）存在但永无注册项。节点 PASS 前不经过任何 engine 级 validator（校验实际由 handlers 节点内部自证，如 do_evidence_gate）。
- **Expected behavior**: session docstring L13"⑤ Validator Hook engine validators 挂钩（PASS 先过 validator）"应真实接线——例如把 evidence_gate / model-critic 等注册进 engine.validators。
- **Why it matters**: "PASS 先过 validator 再 completed"的引擎级 fail-closed 语义在生产会话中为空；所有校验依赖 handler 自己"诚实调用"，削弱了引擎作为裁判的架构定位。
- **Evidence**: session.py L84-88（构造参数）；wave_executor.py L30-31（validators=None）；engine.py L172-174（`fn = self.validators.get(...); if fn is None: return ""`）。
- **Reproduction**: 对 RuntimeSession 运行后断言 `session.engine.validators == {}`。
- **Proposed fix**: 在 session 构造 engine/wave 时传入 `validators={node.type: 对应 gate}`（如 evidence_gate、model_ir schema 校验、critic），并保留节点内自证作为兜底。
- **Regression risk**: 中——接线后某些原"自证通过"的节点可能被 validator 拦截，需逐节点对账。
- **Test required**: 注入一个总是 FAIL 的 validator，断言节点不 completed 且走 retry。

### A-011 [P4] `core/tools/runtime/` 只剩陈旧 __pycache__，orchestrator 仍插入该路径到 sys.path

- **File**: `core/tools/orchestrator.py`（L32）、`core/tools/runtime/`
- **Function/Symbol**: `main` 的 sys.path.insert
- **Line**: 32
- **Observed behavior**: `core/tools/runtime/` 目录下**无任何 .py 源文件**，只有 `__pycache__/` 内 4 个 .pyc（cloud_sandbox/gen_runtime_manifest/orchestrator/state 的 cpython-312 编译物）；orchestrator L32 仍 `sys.path.insert(0, str(ROOT / "core" / "tools" / "runtime"))`。路径插入无实际效果（无源可导入）。
- **Expected behavior**: 无源目录不应被插入 sys.path；陈旧 .pyc 应清理或还原对应源。
- **Why it matters**: 说明 `core/tools/*.py` 曾以副本形式存在于 runtime/ 下（布局迁移残留），易误导开发者在错误位置改文件。
- **Evidence**: `Get-ChildItem -Recurse core\tools\runtime` 输出仅 4 个 .pyc；orchestrator.py L32。
- **Reproduction**: 列出 `core/tools/runtime/` 目录。
- **Proposed fix**: 删除 sys.path.insert(L32) 与空壳目录（属清理，不属功能改动）。
- **Regression risk**: 极低。
- **Test required**: 无（或 orchestrator import 冒烟）。

### A-012 [P4] `requires_reuse_check` 是无行为装饰器，属"看起来有门禁"的装饰性代码

- **File**: `core/runtime/contracts.py`
- **Function/Symbol**: `requires_reuse_check`
- **Line**: 59-61
- **Observed behavior**: 装饰器直接 `return fn`，docstring 自述"文档用，无行为"；且全仓无任何函数使用该装饰器（0 命中）。
- **Expected behavior**: 要么实现真实行为（如标记/审计复用检查结果），要么删除。
- **Why it matters**: 属于 A-003 契约空洞的具体表现之一；保留无行为装饰器会让"复用检查已做"的假象。
- **Evidence**: contracts.py L59-61；grep `requires_reuse_check` 仅定义处。
- **Reproduction**: grep。
- **Proposed fix**: 删除，或改为在 handler 复用路径上实际记录 `reuse_checked=True` 的审计字段。
- **Regression risk**: 低。
- **Test required**: 无/随 A-003。

### A-013 [P4] `ProjectState.refresh_from` 在"派生视图"函数内带副作用修改 question 状态

- **File**: `core/runtime/state/model.py`
- **Function/Symbol**: `refresh_from`
- **Line**: 302-310
- **Observed behavior**: `refresh_from` 被文档定位为"从 Registry + EvidenceGraph 派生聚合视图（State 是派生层的落点）"，但 L302-310 在派生过程中直接写 `q["status"] = "validated"`（experimenting→validated 自动晋级），即读操作带写副作用。
- **Expected behavior**: 派生函数应纯读并返回聚合；状态迁移应由显式动作（引擎/失效传播）触发。
- **Why it matters**: 同一函数既"投影"又"推进"，导致 checkpoint()（session 每次落盘都调 refresh_from）会隐式推进问题状态，使"状态由事件重建"的可重放性/可归因性变弱。
- **Evidence**: state/model.py L302-310。
- **Reproduction**: 构造 experimenting 状态 + 已支撑 claim，调用 refresh_from 观察状态被改写。
- **Proposed fix**: 将自动晋级移出 refresh_from，改为引擎节点完成时的显式 `set_question_status`；或至少让 refresh_from 返回"建议迁移"由调用方决定。
- **Regression risk**: 中——现有多处依赖该隐式晋级（如 session.run 后 Q 状态直接 validated），需同步调整测试期望。
- **Test required**: 断言 refresh_from 不改变输入状态；显式晋级路径单测。

---

## 附：8 个必答问题的直接结论

| # | 问题 | 结论（证据） |
|---|---|---|
| 1 | core/runtime import 依赖方向？有无循环依赖？ | 无模块级环（Tarjan SCC 无 >1 节点分量，90 条边）；存在 execution↔knowledge 子包双向耦合（A-008）。双命名导入约定（相对 `from .x` + sys.path 后 `runtime.x`）跨文件混合（handlers L29 vs L37）。 |
| 2 | V3/V2 边界清晰？核心链是否意外依赖 legacy？ | 边界干净：核心链对 `core/legacy/hands/` 零 import；唯一触点 `state.py→runtime.legacy.convert` 是 V3 内部适配器。但 V2 编排路径路径硬编码已断裂（A-001/A-002）。 |
| 3 | 四个核心组件真实存在且互相连接？ | 真实存在且由 RuntimeSession 接线（B-3/B-4），非空壳；含持久化（state/{registry,evidence_graph,status,engine_progress}.json）与 reconcile 对账。 |
| 4 | orchestrator --execute 真执行还是干跑？ | 默认/`--v3`/`--dry-run` 是干跑（DAG 组合+角色校验+本地波次列举，不调引擎）；`--execute` 真执行（RuntimeSession.run→WaveExecutor→engine→handlers→真 subprocess+数值校验）。 |
| 5 | state.py 状态机与 artifact 生命周期一致？ | 双状态机并存：V2 work/state.json（过程线性）与 V3 status.json（Registry/Graph 派生）桥接但粗粒度（A-009）；artifact 生命周期由 lifecycle.py 强制执行，与 V3 状态机通过 reconcile 对账。 |
| 6 | contracts.py 契约是否被遵守？ | 未被遵守——零接线，终态元组 ≥10 处内联，validate_node_result_outputs/ContractViolation 生产零调用（A-003/A-012）。 |
| 7 | schemas 是否被实际校验？ | v3 schema 零数据校验消费方；validate.py L1.1 只验 schema 文件本身；gatelib mini-validator 仅覆盖 3 个 V2 产物（A-004）。 |
| 8 | 死代码路径？ | 有：codegen+fidelity（A-005）、writing 孤岛 5 模块（A-006）、intelligence（A-007）、contracts 谓词（A-003）、core/tools/runtime 空壳（A-011）。 |

## 附：审计方法（可复现）

- 只读脚本（位于审计工作区 scratch/，未写入仓库）：`import_graph2.py`（90 边依赖图）、`cycle_detect.py`（Tarjan SCC + legacy import 扫描）、`dead_scan.py`（模块引用计数）。
- 命令：`py -3.12 <script>`；PowerShell `;` 连接；未对仓库做任何写操作。
