# Audit C — Execution Chain Authenticity Audit（Agent C 独立只读审计）

- **审计官**: Agent C（独立执行审计官，只读；未修改任何代码/测试/配置）
- **日期**: 2026-09-09
- **仓库**: `C:\Users\Lin\Desktop\Programs\MathModel`
- **审计链**: MODEL_IR → Code Generation → ExecutionPlan → Execution Adapter → subprocess → stdout/stderr → returncode → outputs → duration → hashes → ExecutionResult → Fidelity
- **核心原则**: 如果机器没有产生，就视为不存在。ExecutionResult 只能由 execution substrate 创建。
- **环境**: Windows / PowerShell / `py -3.12`（按 AGENTS.md）

---

## 一、审计范围摘要

逐环节审查了 `core/runtime/execution/` 全部 13 个文件（codegen / composer / dag / session / engine / adapters / fidelity / handlers(1371 行) / wave_executor / replay / validation / yamlio / __init__），以及：
- `core/runtime/artifacts/registry.py`、`artifact.py`、`ids.py`（ExecutionResult 落库门禁）
- `research/P15/experiments/P15-K003/`（k003_formal_runner.py、generate_bundles.py、run_summary.json、formal_results.json、real_execution_results.json、runs/、bundles/、state/registry.json）
- `research/P15/experiments/P15-K003-precheck/k003_runner.py`（正确/错误两种写法的对照）
- `research/P15/measurement_recovery/FIX_LOG.md`、`EXECUTION_PIPELINE_INVESTIGATION.md`（历史修复记录）
- Git 历史：`d44384c`（REAL EXECUTION rebuild）与 `dad33cd`（伪造 generation）两 commit 逐文件 diff

## 二、发现计数

| 严重度 | 数量 |
|---|---|
| HIGH | 4 |
| MEDIUM | 6 |
| LOW | 3 |
| INFO（正面确认） | 3 |
| **合计** | **16** |

## 三、执行链逐环节状态（REAL / GAP / FAKE）

| # | 环节 | 状态 | 结论 |
|---|---|---|---|
| 1 | MODEL_IR → Code Generation | **GAP** | `codegen.py` 明确"core 永久 LLM-free，本模块不生成代码"（L3-7），只做外部代码的登记/执行/校验。composer.py 是 workflow 组合，非代码生成。harness 内不存在 MODEL_IR→code 的机械生成路径；代码由外部 Agent 交付后经 `register_code` 登记。**生成侧真实性依赖外部 Agent，harness 无法机械保证"代码执行了 MODEL_IR 声明的模型"（这正是 fidelity 第二扇门要补的）**。 |
| 2 | ExecutionPlan | REAL | `adapters.py:72-83` 普通 dataclass（model_id/code/inputs/timeout_seconds/workdir/env/adapter/meta）。结构真实，但无校验其"从 MODEL_IR 派生"，调用方可任意构造。 |
| 3 | Execution Adapter → subprocess | **REAL** | `LocalPythonAdapter.execute`（adapters.py:177-261）：写临时 .py → `subprocess.run([python, script], capture_output=True, text=True, timeout=..., cwd=..., env=...)`（L198-202）。**真 subprocess，非模拟**。status 由 returncode 推导（L206），timeout/invalid 分支独立（L234-256）。 |
| 4 | stdout/stderr/returncode 捕获 | **REAL** | `proc.stdout/stderr/returncode` 直接来自 subprocess（L204-206）。outputs 从 stdout 最后一块合法 JSON 解析（L209-223）。 |
| 5 | duration 测量 | **REAL（adapter 内）** | `time.perf_counter()` 前后差值（L186/203/235/247），非硬编码 0。⚠️ 但 K003 runner 落盘文件曾/仍会写 0（见 C-002）。 |
| 6 | code_hash / environment_hash | **REAL（但浅）** | `sha256_text(plan.code)`（L187）；environment_hash 仅 python 版本+platform+executable（L63-69，C-010）。 |
| 7 | ExecutionResult 创建 | **GAP** | `ExecutionResultData` 是公开 dataclass；`registry.create("execution_result", data=任意dict)` **无 schema 门禁**（C-001）。harness 三个创建点（codegen.execute_code / handlers.execute_code / handlers._maybe_execute_experiment）都来自 adapter 结果（真实），异常分支直接构造 status="invalid"（合法）。**但任何持有 registry 的代码路径都可伪造**。 |
| 8 | Fidelity | **REAL** | fidelity.py 基于真实 outputs 机械计算 passed/total（L119-157），非硬编码。⚠️ 但可被构造的 outputs/output_mapping 间接操纵（C-001 连带）；K003 旧版 per-run 报告把 score 与 checks 剥离（C-004）。 |
| 9 | 执行失败传播 | **GAP** | `do_model_execution` 无条件 PASS（handlers.py:525-534）；实验链 `_results_of` 不过滤 `data.status="failed"`（C-007/C-008）。 |
| 10 | K003 实验 | **混合** | 底层执行真实（66/66 success，registry EXEC 全真实字段），但提交的 runner 无法复现、rebuild 脚本未提交、formal_results.json 与 run_summary 冲突（C-002/C-003/C-005）。 |

## 四、Agent 可伪造字段清单（ExecutionResultData → registry.data）

以下字段**全部**可通过 `registry.create("execution_result", data={...})` 由任何持有 registry 的 Agent 直接伪造（registry.py:108-145 只做 Artifact 通用校验，不校验 data 内容）：

| 字段 | 可伪造值示例 | 是否被下游信任 |
|---|---|---|
| `status` | `"success"`（任意字符串，无枚举校验） | ✅ do_model_validation / do_experiment / claim 构建 |
| `outputs` | 任意 dict（可让 fidelity 检查全过） | ✅ fidelity.py / validation.py 直接消费 |
| `stdout` / `stderr` | 任意字符串 | ✅ |
| `returncode` | `0` | ✅ |
| `duration_ms` | `0`（K003 旧版即如此） | ✅ run_summary / 报告 |
| `code_hash` | `""` 或任意 sha256 | ✅ replay 比对（伪造可骗过） |
| `environment_hash` | `""` 或任意 | ✅ |
| `execution_id` | `""`（异常路径也产生空值，无法区分） | ✅ |
| `code` | 任意文本 | ✅ |
| `started_at` / `finished_at` / `provenance` | 任意 | ✅ |

**不能被直接伪造**：`fidelity_score`（由 fidelity.py 从 outputs 计算，不落 EXEC data）。**可间接操纵**：伪造 outputs 满足 F1-F5 检查、或注册时声明宽松 `output_mapping`（output_mapping 只解决命名翻译，不掩盖实体缺失，但可助伪造者对别名）。

> 前置审计 `research/P15/analysis/_audit_B_downstream.md`（L102/L264/L309）已独立指出同一门禁缺失：`registry.create("execution_result", data=...)` 无 schema 门禁、status 可被任意调用方伪造。本审计复现并扩展了该结论。

---

## 五、逐条发现

### C-001 [HIGH] execution_result 落库无 schema 门禁，Agent 可直接构造 ExecutionResult

- **File**: `core/runtime/artifacts/registry.py:108-145`（create/_create_locked）；`core/runtime/artifacts/artifact.py:63-88`（validate）
- **Function-Symbol**: `ArtifactRegistry.create` → `Artifact.validate`
- **Line**: registry.py L133-135（`art.validate()` 只查 ID/type/status 枚举/依赖引用/question 前缀，**不校验 data 内容**）；artifact.py L63-88（`data` 字段完全未进入 validate）
- **Observed**: `registry.create("execution_result", data={"status": "success", "outputs": {...}, "code_hash": "f"*64, "duration_ms": 0, ...})` 可通过全部校验并 `activate=True`。`EXECUTION_RESULT_FIELDS`（adapters.py:40-47）只用于 `to_dict/from_dict` 序列化，registry 不强制。
- **Expected**: execution_result 只能由 execution substrate（LocalPythonAdapter.execute）创建；data 字段集、status 枚举、execution_id 非空、code_hash 与 code 一致应有 schema 门禁。
- **Why it matters**: 这是"ExecutionResult 只能由 substrate 创建"铁律的直接缺口。K003 伪造事件（dad33cd）正是借助这类无门禁落盘路径形成的空壳产物；审计 B 已确认（_audit_B_downstream.md L102）。
- **Evidence**: artifact.py validate 全文无 data 内容检查；registry._create_locked L133-135 仅调 art.validate()。
- **Reproduction**: 内存验证（不落盘）：`Artifact(artifact_id='CODE001', type='code', question='2022_C').validate()` → 报错；但 `data={"status":"success"}` 任意内容均通过。可直接 `reg.create("execution_result", data=伪造dict)` 复现（写操作，只读审计未执行）。
- **Proposed fix**: 为 execution_result 增加 data schema 校验（status ∈ EXEC_STATUS、execution_id 非空、code_hash == sha256(code)、必填字段齐全）；或引入"仅 substrate 可写"的执行结果专用登记 API。
- **Regression risk**: 中——现有测试与旧产物若含空壳 EXEC 会 fail-closed，需迁移。
- **Test required**: `test_execution_result_schema_gate`：伪造 data 必须被拒绝。

### C-002 [HIGH] k003_formal_runner.py 与 run_code_pipeline 返回契约不匹配——已提交 runner 复跑会重新伪造空壳 execution_result

- **File**: `research/P15/experiments/P15-K003/k003_formal_runner.py:720-758`
- **Function-Symbol**: `generate_and_run`
- **Line**: L735-741（execution_result 字段）、L753-755（fidelity 字段）
- **Observed**: `run_code_pipeline`（codegen.py:166-172）只返回 `{code_id, exec_id, exec_status, verification_id, fidelity_status, fidelity_score, fidelity_report}`。runner 却读取 `pipe_result.get("outputs", {})`、`pipe_result.get("duration_ms", 0)`、`pipe_result.get("code_hash", "")`、`pipe_result.get("returncode", 0)`、`pipe_result.get("stdout_tail", "")`、`pipe_result.get("stderr", "")`、`pipe_result.get("environment_hash", "")`、`pipe_result.get("fidelity_checks", [])`、`pipe_result.get("fidelity_passed", 0)`、`pipe_result.get("fidelity_total", 0)`——**这些 key 全部不存在，全部回退到空/0 默认值**。
- **Expected**: 从 registry 读回真实 EXEC（precheck 版 `k003_runner.py:348-367` 就是这么做的——从 registry 读 exec_data、从 fidelity_report 文件读 checks），或 run_code_pipeline 扩展返回契约。
- **Why it matters**: dad33cd 的 66 份伪造空壳（outputs={}/duration=0/code_hash=""）**不是外部 Agent 恶意伪造，而是已提交 runner 的契约 bug 机械产生**。d44384c rebuild 重写了产物文件但**没有修 runner**（该文件不在 rebuild commit 的 diff 中）——当前提交的 runner 一旦复跑，会重新产出伪造空壳。
- **Evidence**: git show dad33cd:.../execution_result.json → `{"outputs": {}, "duration_ms": 0, "code_hash": "", "environment_hash": ""}`；当前 HEAD runner 代码与 dad33cd 逐字一致（git diff 为空）。
- **Reproduction**: 删除一个 run 的 manifest 后重跑 `k003_formal_runner.py full`（写操作，未执行）；或静态对照 codegen.py:166-172 返回字段与 runner L735-741 读取字段。
- **Proposed fix**: 删除 runner 中所有 `pipe_result.get("outputs"/"duration_ms"/"code_hash"/...)`，改为从 registry 读 EXEC 数据（照抄 precheck runner 的正确写法）；或在 codegen.run_code_pipeline 返回中增加 `outputs/duration_ms/code_hash/environment_hash/stdout/stderr/returncode/fidelity_checks/passed/total` 并补单测锁定契约。
- **Regression risk**: 低（纯 research 脚本）。
- **Test required**: `test_k003_runner_contract`：mock run_code_pipeline 返回 7 字段，断言落盘文件不含空壳。

### C-003 [HIGH] K003 REAL EXECUTION rebuild 过程不可从已提交代码重放

- **File**: `research/P15/experiments/P15-K003/`（commit d44384c 的 diff 全集）
- **Observed**: d44384c 重写了 66 个 `runs/<sid>/execution_result.json`、`fidelity_report.json`、新增每个 run 的 `state/registry.json`（EXEC001）与 `state/fidelity/EXEC001.json`、新增 `real_execution_results.json`，但 **diff 中没有任何脚本/工具变更**——写入真实数据的脚本未提交（git status 干净，无未跟踪脚本）。已提交产物与已提交生成代码之间无对应关系。
- **Expected**: 重建过程应由已提交脚本驱动（如 runner 修改 + 数据收集脚本），保证 `git checkout HEAD && 跑脚本 == 已提交产物`。
- **Why it matters**: 审计/复核者无法从仓库证明"66 份真实执行"——只能信任已提交的 JSON 文件本身（自证）。这削弱了 rebuild 的机械可信度。
- **Evidence**: `git show --stat d44384c` 仅含 runs/bundles/key/run_summary/real_execution_results/status 数据文件；`git status --short` 干净。
- **Reproduction**: 尝试用已提交代码重放 rebuild（无脚本可调）。
- **Proposed fix**: 提交 rebuild 脚本（读 registry → 重写 per-run JSON），并在 run_summary 记录脚本 commit hash。
- **Regression risk**: 低。
- **Test required**: `test_k003_rebuild_reproducible`：脚本幂等重放，产物 hash 与已提交一致。

### C-004 [HIGH] K003 伪造链实锤（dad33cd）：execution_result 空壳 + fidelity 报告证据剥离

- **File**: `research/P15/experiments/P15-K003/runs/<sid>/execution_result.json`、`fidelity_report.json` @ dad33cd
- **Observed**: 旧版每 run `execution_result.json` = `{"status":"success","returncode":0,"outputs":{},"stdout_tail":"","stderr":"","duration_ms":0,"code_hash":"","environment_hash":"",...}`；`fidelity_report.json` = `{"fidelity_status":"misaligned","fidelity_score":0.2,"checks":[],"passed":0,"total":0}`。**score=0.2 有值但支撑证据（checks）为空**——分数与证据剥离，文件层面不可验证。
- **Expected**: outputs/duration/hash 为真实 subprocess 值；fidelity 报告含完整 checks/passed/total。
- **Why it matters**: 这正是审计重点怀疑的"Organizer 伪造 66 份 execution_result"的机械根源——不是注册表被写（registry 内 EXEC 实际有真实数据），而是**每 run 交付物文件被契约 bug 写成空壳**，导致外部消费方（盲评 bundle、报告）看到的全是假数据。commit 消息称"hardcoded fidelity 0.2"不精确：0.2 是真实 VR 分数（3/15），但被剥离了 checks 后呈现为无证据的裸分。
- **Evidence**: git show dad33cd 两份文件内容（见上）。
- **Reproduction**: `git show dad33cd:.../runs/09a80448b035/execution_result.json`。
- **Proposed fix**: 同 C-002（修 runner 契约）+ 禁止"分数不带 checks"的报告形态（fidelity 报告必须含 checks 数组）。
- **Regression risk**: 低。
- **Test required**: `test_fidelity_report_checks_not_empty`。

### C-005 [MEDIUM] 同一实验目录存在两份互相冲突的 summary 真源

- **File**: `research/P15/experiments/P15-K003/formal_results.json`（stale）vs `run_summary.json` + `real_execution_results.json` + `runs/*/manifest.json`（rebuild 后）
- **Observed**: formal_results.json 仍是 dad33cd 的分布（aligned 27 / misaligned 39 / unverifiable 0）；rebuild 后 manifest/run_summary/real_execution_results 一致为 aligned 18 / misaligned 26 / unverifiable 22。formal_results.json 未被 rebuild 更新（不在 d44384c diff 中）。
- **Expected**: 单一真源——formal_results.json 应随 rebuild 重算或标记 deprecated。
- **Why it matters**: 消费方取错文件会得到与当前产物矛盾的结论；AGENTS.md 明确"状态单一真源"。
- **Evidence**: 本审计脚本统计：formal_results.json runs 按 fidelity_status → 39 misaligned/27 aligned；real_execution_results.json → 26/18/22；manifests → 26/18/22。
- **Reproduction**: 上面统计命令。
- **Proposed fix**: 重算并提交 formal_results.json（或删除该 stale 文件，保留 run_summary 为唯一摘要）。
- **Regression risk**: 低。
- **Test required**: `test_k003_summary_consistency`：formal_results vs run_summary 分布一致。

### C-006 [MEDIUM] F-arm fidelity 语义与已提交 runner 矛盾（22 unverifiable 不可复现）

- **File**: `research/P15/experiments/P15-K003/k003_formal_runner.py:697-711` vs `run_summary.json`（note：F 臂 fidelity=unverifiable，设计预期）
- **Observed**: rebuild 后 22 个 F-arm run 的 fidelity 为 `unverifiable`（当前 F-arm run 的 fidelity_report 显示 `__no_declarations__`，即 rebuild 以 `model_ir={}` 执行）。但已提交 runner 对 F-arm **仍传 `pdef["model_ir"]`（真实 dict）** → 复跑会得到 misaligned 而非 unverifiable。设计决策（F-arm 无结构化 MODEL_IR → unverifiable）未落入 runner 代码。
- **Expected**: runner 代码与实验设计一致（F-arm 应传空 MODEL_IR 或显式标记 unverifiable）。
- **Why it matters**: 已提交代码无法复现已提交的 fidelity 分布（与 C-003 同源：rebuild 用了未提交的 runner 变体）。
- **Evidence**: 当前 F-arm run fidelity_report.json 含 `"__no_declarations__"`；runner L697 `model_ir = pdef["model_ir"]` 对三臂无差别。
- **Reproduction**: 静态对照。
- **Proposed fix**: runner 中 F-arm 显式传 `model_ir={}`（或加 `unverifiable` 标记），并注释设计理由。
- **Regression risk**: 低。
- **Test required**: `test_k003_f_arm_unverifiable`。

### C-007 [MEDIUM] do_model_execution 无条件 PASS，执行失败不向节点下游传播

- **File**: `core/runtime/execution/handlers.py:525-534`
- **Function-Symbol**: `DefaultNodeExecutor.do_model_execution`
- **Observed**: 遍历全部 (exec_id, result_id) 后**不检查任何 `xr.status`**，恒 `return NodeResult(PASS, f"执行 {n} 个模型（真实 subprocess）")`。即使全部 subprocess 返回码非 0（status=failed/timeout/invalid），节点仍 PASS。`do_model_validation`（L536-561）只在"无任何候选通过且至少一个失败"时 FAIL，部分通过即 PASS。
- **Expected**: 执行节点应反映执行结果（全部失败 → 至少标记/FAIL，或显式把判定责任下放并记录），失败状态应在节点结果与 evidence 中可见。
- **Why it matters**: 审计疑点"handlers.py 约 452-454 行执行失败仍返回 PASS"——当前 452-454 行是 `_active_vr_of`（查边复用，无 PASS），真正的无条件 PASS 在 L525-534。执行失败不会阻断 DAG，下游可基于 failed 执行继续。
- **Evidence**: L525-534 代码；L557-561 条件。
- **Reproduction**: 注入必然失败的 code，跑 C7 节点 → PASS。
- **Proposed fix**: do_model_execution 统计 n_failed/n_success 并在全部失败时返回 FAIL（或至少 reason 注明）；do_model_validation 保持判 FAIL 语义但补充 partial-fail 明细。
- **Regression risk**: 中——现有集成测试可能依赖"执行节点恒 PASS"语义，需同步调整测试。
- **Test required**: `test_execution_node_fails_on_all_failed`。

### C-008 [MEDIUM] 实验链失败不传播：claim 可构建在 data.status="failed" 的结果上

- **File**: `core/runtime/execution/handlers.py:116-119`（_results_of）、`1188-1197`（do_experiment_critique）、`1199-1234`（do_evidence_build）
- **Observed**: `_results_of` 只按生命周期状态过滤（`status not in _TERMINAL`），**不过滤 `data.status`**。`do_experiment_critique` 只检查生命周期终态（invalidated/superseded/deprecated），不检查 `data.status=="failed"`。`do_evidence_build` 直接以 results 建 claim（supports 边），不验证执行是否 success。
- **Expected**: 执行失败（data.status=failed/timeout/invalid）的结果不得支撑 claim；critique 应拒绝 failed 结果。
- **Why it matters**: "执行失败真实传播到下游"的回答为否——失败被记录在 result.data.status，但证据构建与批判环节视而不见，claim 可能建立在失败执行上（false confidence，对应 REPOSITORY_AUDIT R4）。
- **Evidence**: L116-119/L1188-1197/L1199 代码。
- **Reproduction**: 让实验执行失败（result.data.status="failed"）→ do_experiment_critique 仍 PASS（生命周期 active）→ claim 生成。
- **Proposed fix**: `_results_of` 增加 `data.status` 过滤（仅 computed/executed/success）；critique 检查 `data.status`。
- **Regression risk**: 中（同 C-007）。
- **Test required**: `test_failed_execution_does_not_support_claim`。

### C-009 [MEDIUM] EXEC 幂等复用不做真实性校验，可复用伪造/异常产物跳过真实执行

- **File**: `core/runtime/execution/handlers.py:355-365`（_active_exec_of_mir）、391-396（execute_code 复用分支）
- **Observed**: 复用条件仅为 `(question, model_id)` 匹配 + 生命周期非终态；不校验 `execution_id` 非空（异常路径产物 execution_id=""）、不校验 provenance.adapter 为 real subprocess、不校验 code_hash 与 code 一致。若某候选 MIR 已有任何 EXEC（含先前 adapter 异常生成的 invalid 壳、或被 Agent 直接写的伪造 EXEC），**真实执行被跳过**。
- **Expected**: 复用前验证 EXEC 是真实执行产物（execution_id 非空 + adapter=local_python + code_hash 匹配当前 code）。
- **Why it matters**: 幂等设计正确，但信任边界过宽——伪造/异常产物可"冻结"候选状态，阻止重执行。
- **Evidence**: L361-364 条件仅 question/status/model_id；L391-396 直接复用。
- **Reproduction**: 预置一个 data.status="invalid"/execution_id="" 的 EXEC，跑 execute_code → 无 subprocess 调用。
- **Proposed fix**: 复用条件增加 `execution_id 非空 and provenance.adapter 存在 and code_hash == sha256(code)`。
- **Regression risk**: 低-中。
- **Test required**: `test_exec_reuse_rejects_fake_exec`。

### C-010 [MEDIUM] environment_hash 是浅指纹，replay 归因能力有限

- **File**: `core/runtime/execution/adapters.py:63-69`
- **Observed**: environment_manifest 仅 `python 版本 + platform + executable`。不含包版本、随机种子、浮点/外部数据/网络等（adapters.py docstring 自述"未来将演化为 Execution Environment Manifest"）。replay.py:225-233 用它做偏差归因，能力有限。
- **Expected**: 至少含关键依赖版本（numpy/scipy 等）与 seed；K003 实验已固定 seed=42（code 内 set_seed），但 manifest 不记录。
- **Why it matters**: 跨机/跨包版本 replay 差异无法归因；同环境指纹下结果可能不同。
- **Evidence**: L63-69。
- **Proposed fix**: 扩展 manifest 字段（site-packages 关键包版本 + 注入的 seed），向后兼容追加字段。
- **Regression risk**: 低（追加字段改变 hash 值，需重建历史 EXEC 或双版本兼容）。
- **Test required**: `test_environment_manifest_includes_deps`。

### C-011 [LOW] Code Generation 环节在 harness 内不存在（架构性 GAP，非缺陷）

- **File**: `core/runtime/execution/codegen.py:1-15`
- **Observed**: 模块定位"core 永久 LLM-free：本模块不生成代码，只负责登记、执行、校验、归因"。MODEL_IR → code 由外部 Agent 完成，经 `register_code` 进入 harness。`composer.py` 是 workflow 组合（base+stages+competition → DAG），与代码生成无关。
- **Why it matters**: 审计问题 1"从 MODEL_IR 到可执行 Python 代码的生成是否真实"——**harness 内无此环节**；生成真实性只能由外部 Agent 声明 + fidelity 第二扇门机械校验兜底。这是设计决策（THREE_LAYER_ARCHITECTURE v3），但审计链首环节应如实标注 GAP。
- **Evidence**: codegen.py docstring L3-7；composer.py 全文。
- **Proposed fix**: 文档层面将"Code Generation"标注为外部环节；若需 harness 内机械生成，另立 codegen 实现（当前无）。
- **Regression risk**: 无。
- **Test required**: 无（文档/架构层面）。

### C-012 [LOW] adapter 可注入，subprocess 可被绕过（需调用方权限）

- **File**: `core/runtime/execution/codegen.py:110`（`adapter = adapter or LocalPythonAdapter()`）、`handlers.py:404-408`（`self.execution_adapter`）、`session.py:60-62`
- **Observed**: `execute_code`/`RuntimeSession` 接受任意 `ExecutionAdapter`；`handlers.execute_code` 用 `self.execution_adapter`（None 时才 fallback 到 LocalPythonAdapter）。注入返回伪造 ExecutionResultData 的 adapter 可完全绕过 subprocess。无任何校验 adapter 必须是真实后端。
- **Expected**: 执行后端应来自受控工厂（`get_adapter`，adapters.py:264-268），禁止任意注入，或注入时记录 provenance 供审计。
- **Why it matters**: 与 C-001 叠加 = 双通道伪造：直接写 registry 或注入假 adapter。当前信任模型是"调用方有代码权限即可信"，对独立审计不成立。
- **Evidence**: codegen.py:110、handlers.py:405-408、adapters.py:264-268。
- **Proposed fix**: 默认路径强制 `get_adapter("local_python")`；自定义 adapter 必须显式声明且 EXEC provenance 记录 adapter 名。
- **Regression risk**: 低（测试用 fake adapter 需适配）。
- **Test required**: `test_default_adapter_is_local_python`。

### C-013 [LOW] run_code_pipeline 的 question 参数契约：传 problem_id 会抛错

- **File**: `core/runtime/execution/codegen.py:136-172`；`core/runtime/artifacts/artifact.py:80-83`；`registry.py:314-319`
- **Observed**: question 是可选 str，透传 `reg.create(..., question=question)`。`Artifact.validate` 要求 question 以 "Q" 开头（L82-83），`_assert_refs_exist` 要求 question artifact 已存在（L318-319）。传 `"2022_C"` 会抛 `ContractError`（validate 报两条：引用非法 + 非 Q 类型）。**已内存验证**。K003 runner 不传 question（None）→ 无报错。
- **Expected**: 契约即"question 必须是已登记 QID 或 None"；传 problem_id 应报错（当前确实报错，行为符合 fail-closed）。
- **Why it matters**: 回答审计问题 10：传 problem_id 报错，契约清晰；但报错时机在 `register_code`（第一步），若调用方先写 code 再传错 question，会留半成品 code artifact（需回滚或容忍）。
- **Evidence**: 内存验证输出：`["question 引用非法: '2022_C'", "question 必须是 Q 类型 ID: '2022_C'"]`。
- **Proposed fix**: 可选——在 run_code_pipeline 入口前置校验 question 格式，报错更早。
- **Regression risk**: 无。
- **Test required**: `test_run_code_pipeline_question_contract`。

### C-014 [INFO] 正面确认：subprocess / duration / hashes / outputs 捕获真实

- **Evidence**: adapters.py L194-233；顶层 K003 registry EXEC001-EXEC078 全部含真实 execution_id(uuid)/outputs/duration_ms(244 等)/code_hash/code/environment_manifest。运行链真实。

### C-015 [INFO] 正面确认：fidelity 由真实输出机械计算

- **Evidence**: fidelity.py L119-157（check_fidelity：execution 非 success → unverifiable；checks 由 MODEL_IR 声明派生，score=passed/total）；当前 per-run fidelity_report.json 含 15 条真实 checks（3 passed）。replay.py 真实重执行并比对 code_hash/environment_hash/outputs（L214-240）。

### C-016 [INFO] 正面确认：harness 三个 EXEC 创建点均来自 adapter 结果

- **Evidence**: codegen.py L111-126、handlers.py L416-428、handlers.py L1130-1145，全部 `xr = adapter.execute(plan)` 后 `reg.create("execution_result", data=xr.to_dict())`。异常分支（handlers.py L417-421/L1133-1139）直接构造 status="invalid"（合理：框架错误本身是真实状态）。**但**这些点只是"当前实现不伪造"，不是"无法伪造"（C-001）。

---

## 六、审计问题逐条回答

1. **MODEL_IR → 可执行代码生成是否真实？** Harness 内**无生成环节**（C-011）；外部 Agent 交付 code，经 register_code 登记。登记的代码由 LocalPythonAdapter 以独立 subprocess 运行（C-014）——**执行真实**，但"代码是否执行了 MODEL_IR 声明"只能由 fidelity 第二扇门机械回答，生成侧本身无机械保证。
2. **ExecutionPlan 是否含真实执行步骤？** 是（model_id/code/inputs/timeout/workdir/env/adapter），但可从任意处构造，无"从 MODEL_IR 派生"校验。
3. **LocalPythonAdapter 是否真调 subprocess？** **是**（adapters.py L198-202 subprocess.run，非模拟）。
4. **ExecutionResult 创建点？** 3 个 harness 点（均来自 adapter）+ 2 个异常分支（status="invalid"）+ **任意持 registry 代码路径可直接构造（C-001）**。Agent 直接构造路径**存在且无门禁**。
5. **stdout/stderr/returncode 是否真实捕获？** 是（subprocess capture_output 直通）。
6. **duration 是否真实测量？** Adapter 内真实（perf_counter）；但 K003 已提交 runner 落盘文件会写 0（C-002），旧产物确实为 0（C-004）。
7. **code_hash/output_hash 是否真实计算？** 是（sha256_text）；environment_hash 为浅指纹（C-010）。
8. **fidelity 是否基于真实输出？** 是（fidelity.py 机械计算）；旧 K003 每 run 报告剥离 checks 呈现裸分（C-004）；伪造 outputs 可间接操纵（C-001）。
9. **执行失败是否传播？** **否/不完整**：do_model_execution 恒 PASS（C-007）；实验链 claim 可建于 failed 结果（C-008）；EXEC 复用可冻结伪造/异常产物（C-009）。
10. **run_code_pipeline question 契约？** 可选参数，透传 reg.create；非 Q 前缀或未登记的 question → ContractError（C-013，已内存验证）；K003 传 None 无报错。

## 七、K003 重点怀疑独立验证结论

- ✅ **疑点 1（Organizer 伪造 66 份 execution_result）确认**：dad33cd 产物为 `outputs={}/code_hash=""/duration=0/checks=[]`，但根因是**已提交 runner 的契约 bug**（pipe_result.get 不存在 key 回退默认），而非恶意写注册表；registry 内 EXEC 当时即有真实数据。rebuild（d44384c）重跑 66 次真实 subprocess 并重写产物文件（当前数据真实：66/66 success、n_real_outputs=66、n_real_code_hash=66、duration 真实）。
- ⚠️ **但**：runner 未修复（C-002）、rebuild 脚本未提交（C-003）、formal_results.json stale（C-005）、F-arm unverifiable 语义与 runner 矛盾（C-006）——**"REAL EXECUTION rebuild"作为一次性人工修复成立，作为可复现的机械化流程不成立**。
- ❌ **疑点 2（handlers.py 452-454 执行失败仍返回 PASS）不成立（当前行号）**：452-454 是 `_active_vr_of`（复用查询），无 PASS；真正的无条件 PASS 在 do_model_execution L525-534（C-007）。
- ✅ **疑点 3（except:return True / default=success / 硬编码 0.2/0/placeholder）**：核心执行链无 `default="success"`；硬编码 0.2 是误读（真实 VR 分数被剥离证据，C-004）；`placeholder` 出现在 result/claim 的 `not_executed` 占位（FIX_LOG 2a 已治理，合规）；`except: return True` 类模式在 core/runtime 中不存在（grep 验证）。

---

*审计完成。所有证据可复现（只读操作）；未修改任何文件。*
