# ROADMAP — LinHoMo V3 最终实施路线图

> **基于 5 路独立审计 + 战略裁决**。原则：先接线后扩能，先修信任边界后加新功能，先做 P0 再谈 P1+。
> 所有任务必须能落到代码、实验或治理动作。

---

## P0：生产闭环接通 + 信任边界修复（最高优先级，2-3 周）

> **目标**：让默认 `orchestrator --execute` 能跑通完整的 MODEL_IR→Code→Execution→Validation 链路，并修复所有信任边界漏洞。这是"有引擎没钥匙"和"可信 Harness 不可信"两个致命问题的修复。

### P0-1：orchestrator 注入通道

> ✅ **DONE 2026-09-10**（commit `d04feb1`）：`--constructor-dir` 从 `<project>/constructor/` 加载外部 Constructor 产物（MIR+code+specs），默认 `--execute` 20/20 节点跑通、EXEC rc=0、VR 如实传播；验收 `test_orchestrator_injection.py` 5/5；全量 1026/4。


| 项 | 内容 |
|---|---|
| **目标** | orchestrator 支持从项目目录加载外部 Constructor 产物（MODEL_IR + code + validation_specs），使默认 `--execute` 能跑通完整链路 |
| **为什么做** | 当前生产路径仅完成 3/20 节点，model_construction 必然 BLOCKED（orchestrator.py:322-326 从不注入 external_*）。所有下游原语无法在生产中发挥作用 |
| **不做的风险** | LinHoMo 的"闭环能力"只存在于测试和独立脚本中，永远无法成为可运行的产品 |
| **具体文件** | `core/tools/orchestrator.py`（_execute_v3:391, RuntimeSession 构造:322-326）、`core/runtime/execution/session.py`（__init__:47-100） |
| **具体函数** | `orchestrator._execute_v3()` 增加 `external_model_irs` / `external_code` / `validation_specs` 加载逻辑（从 `<project>/constructor/` 目录读取）；`RuntimeSession.__init__()` 接受并传递这些参数 |
| **测试** | `tests/integration/test_orchestrator_injection.py`：给定 `<project>/constructor/model_ir.json` + `code.py` + `specs.json`，`orchestrator --execute` 跑通 ≥15/20 节点，EXEC/VR/claim 均真实 |
| **验收标准** | 临时项目 + 注入 fixtures → `orchestrator --execute` → ≥15/20 节点 completed，EXEC 真实 subprocess（rc=0），VR 真实（pass 或 fail 如实传播），Evidence Graph 有完整谱系边 |
| **是否改变 API** | 是：orchestrator CLI 增加 `--constructor-dir` 参数；RuntimeSession 构造函数增加可选参数 |
| **是否影响旧实验** | 否：不传 `--constructor-dir` 时行为不变（仍 3/20 节点，如实 BLOCKED） |
| **是否需要迁移** | 否 |
| **预计依赖** | 无（纯接线） |

### P0-2：Engine validators 挂载

> ✅ **DONE 2026-09-10**（commit `fcee52e` + `ec39c83`）：`core/runtime/execution/validators.py`（evidence_consistency_validator）挂载到 WorkflowEngine 与 WaveExecutor；PASS 节点声明的 artifacts/evidence 必须真实存在于 registry；验收 5/5。


| 项 | 内容 |
|---|---|
| **目标** | session 构造 engine 时传入 validators，使 catalog/v3.yaml 声明的 6 个 gate 真实执行 |
| **为什么做** | 当前 engine.validators={}（实测），6 个声明 validator 全部不执行，critic 节点退化为存在性检查。"Validation 是核心竞争力"的承诺被破坏 |
| **不做的风险** | 验证层永远是空转，"没验证=通过"持续存在 |
| **具体文件** | `core/runtime/execution/session.py:96-100`、`core/runtime/execution/wave_executor.py:28-31`、`core/runtime/execution/engine.py:68,181-190` |
| **具体函数** | `WaveExecutor.__init__()` 接受 validators 参数并传递给 WorkflowEngine；`RuntimeSession.__init__()` 从 catalog/v3.yaml 加载 validator 绑定并传入 |
| **测试** | `tests/unit/test_engine_validators.py`：实测 engine.validators 非空；validator 被调用时节点状态受影响 |
| **验收标准** | 实测 `session.engine.validators` 非空；catalog 声明的 model-critic/assumption-checker 至少有一个机械实现或显式 UNKNOWN 状态 |
| **是否改变 API** | 是：WaveExecutor 构造函数增加 validators 参数 |
| **是否影响旧实验** | 否：validators 为空时行为不变 |
| **是否需要迁移** | 否 |
| **预计依赖** | 无 |

### P0-3：ExecutionResult 来源鉴别

> ✅ **DONE 2026-09-10**（commit f8f21f1）：`execution_auth.py` 进程级 HMAC （issue_token/verify_token，常数时间比较）；adapter 签发 `execution_token`；`registry.create` 对 success EXEC 强制来源鉴别（无 token / HMAC 不匹配拒绝），历史/测试桩显式 `legacy_unverified=true` 豁免（不回溯）；读取路径不校验，尊重已存在事实。验收 `test_execution_authenticity.py` 5/5（真实通过/伪造拒绝/坏 token 拒绝/legacy 豁免/正反例）；全量 1026/4；validate 58/0；catalog/terminology OK；三 freeze 全 PASS。


| 项 | 内容 |
|---|---|
| **目标** | EXEC 必须携带 adapter 签发的不可伪造字段，registry.create("execution_result") 拒绝无来源鉴别或来源不匹配的 EXEC |
| **为什么做** | 当前伪造 EXEC 可通过门禁（实测 FORGED SUCCESS ACCEPTED），K003 事故形态可复现。这是"可信 Harness"的核心承诺被破坏 |
| **不做的风险** | 任何持有 registry 引用的 Agent 可伪造执行结果，Evidence Graph 被污染且无法对账 |
| **具体文件** | `core/runtime/artifacts/artifact.py:110-152`、`core/runtime/artifacts/registry.py:108-145`、`core/runtime/execution/adapters.py:87-130` |
| **具体函数** | `ExecutionResultData` 增加 `execution_token` 字段（adapter 签发，含 code_hash + timestamp + adapter_id 的 HMAC）；`artifact.py` EXEC 校验增加 token 验证；`registry.create` 对 EXEC 类型强制 token 校验 |
| **测试** | `tests/unit/test_execution_authenticity.py`：① 真实 adapter 产出的 EXEC 通过校验；② 伪造 EXEC（无 token / token 不匹配）被拒绝；③ 无 code 字段 + 16 字符 hash 的伪造被拒绝 |
| **验收标准** | 伪造 EXEC 100% 被门禁拒绝；真实 adapter 产出的 EXEC 100% 通过；K003-precheck 的 external_agent EXEC 形态被拒绝 |
| **是否改变 API** | 是：ExecutionResultData 增加 execution_token 字段；registry.create 对 EXEC 类型增加校验 |
| **是否影响旧实验** | 是：历史 EXEC 产物无 token，需要迁移（见下）或标记为 legacy_unverified |
| **是否需要迁移** | 是：历史 EXEC 产物标记为 `legacy_unverified`，不追溯重算；新产生的 EXEC 必须带 token |
| **预计依赖** | 无（标准库 hmac） |

### P0-4：零执行/零验证 ≠ PASS

| 项 | 内容 |
|---|---|
| **目标** | model_execution 无代码 → blocked（非 PASS）；model_validation 无 spec → blocked（非 PASS）；E9 要求 VR 存在 |
| **为什么做** | 当前"没做"和"做了且通过"不区分（handlers.py:753, 776-781 实测 0 VR 全绿）。这是语义级假成功 |
| **不做的风险** | 全管线可在零执行零验证下交付，"可信 Harness"名存实亡 |
| **具体文件** | `core/runtime/execution/handlers.py:753,776-781`、`core/validators/evidence/evidence_gate.py:208-215` |
| **具体函数** | `do_model_execution()`：无 code 时返回 NodeResult(status="blocked", reason="no_code")；`do_model_validation()`：无 spec 时返回 blocked；`evidence_gate E9`：增加 VR 存在性检查 |
| **测试** | `tests/integration/test_zero_exec_validation.py`：① 无代码 → model_execution blocked；② 无 spec → model_validation blocked；③ 有 EXEC 无 VR → evidence_gate FAIL |
| **验收标准** | 注入 MIR+code 但无 spec → model_validation blocked，全管线不 completed；注入 MIR+code+spec → 正常执行验证 |
| **是否改变 API** | 否（handler 内部语义变更） |
| **是否影响旧实验** | 是：依赖"0/0=PASS"的测试/实验需要更新（预期少量测试失败，需修正测试预期而非放宽门禁） |
| **是否需要迁移** | 否 |
| **预计依赖** | P0-1（注入通道） |

### P0-5：mark_validated 门禁 + critic SKILL 改写

| 项 | 内容 |
|---|---|
| **目标** | Agent 无法直接调用 mark_validated；只能提交 review report，由 runtime 登记 validated 状态 |
| **为什么做** | critic SKILL.md（model-critic:63, experiment-critic:52）指令 Agent 调 mark_validated，registry 无调用方门禁。这是 Authority Matrix 核心违规——Validation PASS 的所有权被 Agent 侵占 |
| **不做的风险** | Agent 可自封 validation PASS，The Agent Is Not The State 原则被破坏 |
| **具体文件** | `core/runtime/artifacts/registry.py:257`、`core/runtime/artifacts/artifact.py:168`、`core/skills/critics/model-critic/SKILL.md:63`、`core/skills/critics/experiment-critic/SKILL.md:52` |
| **具体函数** | `registry.mark_validated()` 增加调用方白名单（仅 validator 模块可调用）+ 必须携带验证器运行记录（run_id/hash）；改写两条 SKILL.md：删除直接 mark_validated 指令，改为"提交 review report 到 `<project>/reviews/`，由 runtime 登记" |
| **测试** | `tests/unit/test_mark_validated_gate.py`：① 非白名单调用方调 mark_validated → 抛 PermissionError；② 白名单调用方 + 有效运行记录 → 通过；③ critic SKILL.md 不含 mark_validated 字符串 |
| **验收标准** | grep 全仓 `mark_validated(` 仅出现在 registry 定义 + validator 调用 + 测试；critic SKILL.md 无此字符串 |
| **是否改变 API** | 是：mark_validated 增加 caller 参数 + run_record 参数 |
| **是否影响旧实验** | 否（V2 legacy 路径不受影响） |
| **是否需要迁移** | 否 |
| **预计依赖** | P0-2（validators 挂载后，白名单才有真实调用方） |

### P0-6：K003 残余直写路径删除

> ✅ **DONE 2026-09-10**（commit `46d9f49`）：`k003_formal_runner.py` 直写 execution_result.json fallback 删除，改独立 error log；结构测试覆盖 `.write_text(`变体；grep 全仓 execution_result.json 写入点仅 execution_writer。


| 项 | 内容 |
|---|---|
| **目标** | 删除 k003_formal_runner.py:829 的 fallback 直写 execution_result.json；结构测试覆盖 .write_text( 变体 |
| **为什么做** | 当前 write_run_execution 抛异常时，Runner 直接 .write_text() 写 error 壳，绕过唯一写入路径。结构测试 grep 形式漏检 |
| **不做的风险** | "唯一写入者"声明被 fallback 打破，K003 事故的残余入口 |
| **具体文件** | `research/P15/experiments/P15-K003/k003_formal_runner.py:829`、`tests/unit/test_k003_governance.py` |
| **具体函数** | 删除 `(run_dir / "execution_result.json").write_text(...)` fallback；改为写独立 `<run_dir>/error.log`；测试增加 `.write_text(` 形式的 grep 检查 |
| **测试** | `test_k003_governance.py` 增加：grep 所有 `.write_text(` 和 `json.dump(` 形式，确认无 execution_result.json 直写 |
| **验收标准** | grep 全仓 `execution_result.json` 的写入点仅 execution_writer.py:84；结构测试覆盖所有写入形式 |
| **是否改变 API** | 否 |
| **是否影响旧实验** | 否（K003 已冻结，不回溯） |
| **是否需要迁移** | 否 |
| **预计依赖** | 无 |

---

## P1：核心闭环补全 + Constructor Protocol（3-4 周）

### P1-1：Fidelity 门接入主路径

> ✅ **DONE 2026-09-10**（commit `2e6662a` + `f0a4bba` + `80741df`）：`do_model_execution` 对成功 EXEC 跑 `_fidelity_of`（misaligned→FAIL），`verify_fidelity` 生产 DAG 内 `register_vr=False`（防 C8 幂等复用跳过真实数值验证），容器/向量输出 F5 如实 skipped；验收 `test_fidelity_integration.py` 5/5。


| 项 | 内容 |
|---|---|
| **目标** | code_generation 后自动跑 fidelity check，misaligned → FAIL |
| **为什么做** | 当前 fidelity.py 仅被 run_code_pipeline（独立入口）和 CLI 调用，V3 DAG 零调用。Model→Code 保真无机器检查 |
| **不做的风险** | 代码与模型声明不一致无法被机械检测（K003 fidelity misaligned 59% 但不阻断流程） |
| **具体文件** | `catalog/v3.yaml`（增加 fidelity_check 节点）、`core/runtime/execution/handlers.py`（增加 do_fidelity_check handler）、`core/runtime/execution/fidelity.py` |
| **具体函数** | `do_fidelity_check()`：读 MODEL_IR + code，调 `check_fidelity()`，misaligned → NodeResult FAIL，aligned → PASS |
| **测试** | `tests/integration/test_fidelity_gate.py`：① aligned code → PASS；② misaligned code → FAIL；③ fidelity 结果写入 Evidence Graph |
| **验收标准** | 注入 misaligned code → fidelity_check FAIL → 下游 blocked；aligned → 正常继续 |
| **是否改变 API** | 是：DAG 增加节点 |
| **是否影响旧实验** | 否 |
| **是否需要迁移** | 否 |
| **预计依赖** | P0-1（注入通道） |

### P1-2：Revision Loop 接入主 DAG

> ✅ **DONE 2026-09-10**（commit `311a863` + `123f287` + `d358171` + 本轮）：`do_model_validation` FAIL 时 `_diagnose_and_draft`（沿 `verified_by` 边机械诊断 → diagnosis artifact + diagnosed_by 边；`build_revision_draft` 生成 M2 草案入 shared 供外部 Constructor 消费；modeling_trace object 契约对齐）。**自动修订闭环（本轮）**：`_auto_revision` 节点内闭环——外部 Constructor 注入 `revision_bundles[qid]`（M2 MIR+code）后，同一 `model_validation` 节点执行内完成 M2 注册（`revision_of` 边由 runtime 生成）→ M1 收口（supersede + `supersedes` 边由 runtime 生成）→ M2 重跑 EXEC/R/VR → PASS；无修订注入 → FAIL 如实（`revision_blocked`，等待外部）；M2 重跑失败 → FAIL 如实（`revision_failed`）。**实现说明**：采用节点内闭环而非 DAG 增 3 节点——引擎 `on_fail` 回退语义专用于"重做前置"（rollback 后失败节点仍 ready 会触发自旋保护），不适用于 revision 推进链；验收语义不变（vs001 场景经 V3 主 DAG 自动完成、谱系边由 runtime 生成）。独立 API `do_model_revision()` / `do_model_re_execute()` 保留。验收测试 `tests/integration/test_auto_revision_loop.py` 3/3。


| 项 | 内容 |
|---|---|
| **目标** | model_validation FAIL → diagnose_failure → revision_draft → new_model_version → re-execution，形成自动 M1→M2 闭环 |
| **为什么做** | 当前 revision.py + diagnosis.py 仅被 tests + vs001_driver.py 调用，V3 主 DAG 无此节点。model_validation FAIL→重试耗尽→blocked，无自动诊断/修订。"Revision-capable"定位的承诺被破坏 |
| **不做的风险** | LinHoMo 只能"检测失败"不能"从失败中恢复"，L5 层永远是空白 |
| **具体文件** | `catalog/v3.yaml`（增加 diagnosis / revision / re_execute 节点）、`core/runtime/execution/handlers.py`（增加对应 handler）、`core/runtime/modeling/diagnosis.py`、`core/runtime/modeling/revision.py` |
| **具体函数** | `do_diagnosis()`：调 `diagnose_failure(VR, EXEC, MODEL_IR)` → diagnosis artifact + diagnosed_by 边；`do_revision()`：调 `build_revision_draft(diagnosis, old_MIR)` → revision proposal（Agent 可介入）→ new MIR artifact + revision_of/supersedes 边；`do_re_execute()`：用新 MIR 重跑 code/execution/validation |
| **测试** | `tests/integration/test_revision_loop.py`：注入 M1（故意错误）→ validation FAIL → diagnosis → revision → M2 → validation PASS；revision_of/supersedes 边由 runtime 生成 |
| **验收标准** | vs001 场景（ρ=1.5→FAIL→ρ=0.75→PASS）可通过 V3 主 DAG 自动完成（不再需要独立 runner）；revision 边由 runtime 生成而非手工 add_relation |
| **是否改变 API** | 是：DAG 增加 3 个节点 |
| **是否影响旧实验** | 否 |
| **是否需要迁移** | 否 |
| **预计依赖** | P0-1, P0-4, P1-1 |

### P1-3：Constructor Protocol 层

> ✅ **DONE 2026-09-10**（commit `b52cf7b` + `5e78137`）：`core/runtime/constructors/{protocol,registry}.py`——ConstructionBundle + ConstructorAdapter ABC + capability C0-C5 + ConstructorRegistry；验收 5/5。


| 项 | 内容 |
|---|---|
| **目标** | 建立 `core/runtime/constructors/`，实现 ConstructorAdapter ABC + ConstructionBundle + BaseConstructorAdapter + LocalAgentAdapter |
| **为什么做** | 外部 Agent（MathModelAgent/Pi/OpenAI/Claude）需要统一接入通道；当前 orchestrator 注入通道（P0-1）是手动文件加载，不是协议级集成 |
| **不做的风险** | 每个外部 Agent 都需要定制集成代码，无法做到"Constructor 可替换" |
| **具体文件** | 新建 `core/runtime/constructors/{__init__,protocol,adapter,registry}.py` + `adapters/{__init__,local,openai,claude}.py` |
| **具体函数** | `ConstructorAdapter.construct(problem, context) -> ConstructionBundle`；`BaseConstructorAdapter._parse_text_to_mir(raw_output)`；`ConstructorRegistry.register/get/health_check`；`LocalAgentAdapter.construct()`（LLM + 方法卡检索 + ModelIRBuilder） |
| **测试** | `tests/unit/test_constructor_protocol.py`：① ConstructionBundle schema 校验；② 解析失败 fail-closed 降级 C0；③ bundle 内 execution_result 字段被丢弃；④ LocalAgentAdapter 端到端 construct → Runtime 复跑 → VR |
| **验收标准** | LocalAgentAdapter 输出的 ConstructionBundle 能被 Runtime 消费并跑通完整链路；bundle 内的 execution_result/fidelity/validation 字段被 Runtime 忽略并重新执行 |
| **是否改变 API** | 是：新增模块 |
| **是否影响旧实验** | 否 |
| **是否需要迁移** | 否 |
| **预计依赖** | P0-1（注入通道是 Protocol 的底层实现） |

### P1-4：MODEL_IR 契约漂移修复

> ✅ **DONE 2026-09-10**（本轮 commit）：core schema = 0.8 校准版 + 契约分层
> （数组元素 required=旧core∩0.8 公共核心；模板承诺字段标 x-template-promise、
> register 层强制；词表 enum 入模板承诺层；sub_question_binding 统一
> string|array；model_graph/modeling_trace 宽松承载）；research 副本已删
> （唯一真源）；`migrate_legacy_format()` + `LEGACY_MODEL_IR.md`；
> K001/K002/K003 冻结基线 revision v1.1 重冻；验收 6/6 + contract_gate 5/5
> + skeleton 3/3；全量 1067/4、validate 58/0、三 freeze PASS。

| 项 | 内容 |
|---|---|
| **目标** | model_ir schema 收敛到唯一真源（core/schemas/v3）；research 侧改为引用；统一 runtime 与 research 的 MODEL_IR 格式 |
| **为什么做** | 当前 246/246 份 research model_ir.json 同时违反 runtime schema 与 research 自身 schema（0% 合规）；schema 双副本漂移（core 含 modeling_trace，research 不含）。"MODEL_IR 是核心契约"的承诺被破坏 |
| **不做的风险** | schema 永远是空转门槛，没有任何产物通过过当前 schema |
| **具体文件** | `core/schemas/v3/model/model_ir.schema.json`（唯一真源）、`research/P15/model_representation/model_ir.schema.json`（改为引用 core 或删除）、`core/runtime/modeling/model_ir.py` |
| **具体函数** | 统一 schema 字段；提供 `model_ir.migrate_legacy_format(legacy_dict) -> current_dict` 迁移函数；research 产物批量迁移或标记为 legacy |
| **测试** | `tests/unit/test_model_ir_schema.py`：① 当前 schema 校验通过 vs001 的 MIR；② 迁移函数能将旧格式转为新格式；③ research 侧无独立 schema |
| **验收标准** | 全仓只有一份 model_ir.schema.json（core/schemas/v3）；vs001 + K003 正式产物的 MIR 能通过 schema 校验（或明确标记为 legacy 不回溯） |
| **是否改变 API** | 是：schema 字段可能调整 |
| **是否影响旧实验** | 是：K003 已冻结，不回溯；新实验必须用新 schema |
| **是否需要迁移** | 是：research 产物标记 legacy，不重算；新产物用新格式 |
| **预计依赖** | 无 |

### P1-5：死代码清理（第一批）

> ✅ **DONE 2026-09-10**（commit `6466490` + `95a5cb3`）：删除确认的死模块/死循环/`_maybe_execute_experiment` 等；删除后全量 pytest + validate 全绿。


| 项 | 内容 |
|---|---|
| **目标** | 删除确认的死代码：core/validators/modules/ 20 个模块、core/runtime/domain/、core/runtime/adapters/（非 execution/adapters.py）、core/tools/ 6 个空壳子目录、_maybe_execute_experiment、bench_mmbench.py 空壳 |
| **为什么做** | 死代码误导"验证层厚度"，增加维护负担，违反"infra 不冒充 capability" |
| **不做的风险** | 新贡献者误以为 20 个 validator 模块在工作；测试覆盖率虚高 |
| **具体文件** | 见 MODEL_CONSTRUCTION_GAP.md §4 DEAD 判定 |
| **具体函数** | 纯删除 |
| **测试** | 删除后 `py -3.12 -m pytest tests -q` 全绿；`py -3.12 core/tools/validate.py` 全绿 |
| **验收标准** | 上述模块/目录不存在；import 测试无 ImportError；测试全绿 |
| **是否改变 API** | 是（删除模块） |
| **是否影响旧实验** | 否（死代码无调用方） |
| **是否需要迁移** | 否 |
| **预计依赖** | 无 |

---

## P2：能力深化 + 外部集成（4-6 周）

### P2-1：L6 数值正确性机械判定层

| 项 | 内容 |
|---|---|
| **目标** | 把 8 题 gt.json 机械化为可执行数值断言，接入 arena VR 管线；修复 fidelity 同题同分退化 |
| **为什么做** | "最终数学正确性"这一无争议的建模能力终点从未被机械测量。这是 Constructor-independent benchmark 的前置依赖 |
| **不做的风险** | 永远无法证明 LinHoMo 提升了建模质量（只能证明提升了文本质量） |
| **具体文件** | `core/runtime/execution/validation.py`（增加 L6 判定函数）、`research/P15/benchmark/arena/`（接入 L6）、`core/runtime/execution/fidelity.py`（退化修复） |
| **具体函数** | `validate_against_gt(execution_result, gt_assertions) -> L6Result`；fidelity 从"查声明符号可观测"升级为"校验约束/残差/目标值" |
| **测试** | `tests/unit/test_l6_validation.py`：① 正确数值 → PASS；② 错误数值 → FAIL；③ 无 GT 断言 → unverifiable（不编造分数） |
| **验收标准** | 8/8 题有可执行 GT 断言；fidelity 对同题不同构造有区分度；L6 判定接入 arena 报告 |
| **是否改变 API** | 是：validation.py 增加 L6 判定 |
| **状态** | ✅ 已完成（2026-09-10）：`validate_against_gt` 落地（feasibility/objective_sane/output_nonnegative/output_range，无断言 unverifiable、无法判定 skipped 不误伤）；8/8 题 `gt.json#l6_assertions` v1.0（数学必然 + 题面客观边界，非答案数值）；fidelity 升级 F6 约束数值满足（带显式 check 断言时判定、无断言不误判）+ F7 目标值有限；arena 接入 L6（output_nonnegative 由 MODEL_IR 声明派生 paths，全池 44 候选 8/8 题零误伤全 passed，报告加 l6 列与选型排序）；`tests/unit/test_l6_validation.py` 12 用例；2019_C 收益差/2018_A 温度键异构等误伤在实现期即修复 |
| **是否影响旧实验** | 否 |
| **是否需要迁移** | 否 |
| **预计依赖** | P1-1（fidelity 接入） |

### P2-2：MathModelAgent Adapter

| 项 | 内容 |
|---|---|
| **目标** | 实现 MathModelAgentAdapter（经其 API/CLI，External Solver/Worker 通道）；导入 17 套论文模板 + 12 套图表模板 |
| **为什么做** | MMA 是唯一可比的端到端基线，也是 Constructor-independent benchmark 的 C2 臂 |
| **不做的风险** | benchmark 只有自研 Constructor，无法证明 Runtime 增益的普适性 |
| **具体文件** | `core/runtime/constructors/adapters/mathmodel_agent.py`、`core/templates/papers/`（导入模板）、`core/templates/figures/`（导入图表模板） |
| **具体函数** | `MathModelAgentAdapter.construct()`：经 API 发送 problem → 解析返回的 questions_solution → BaseConstructorAdapter._parse_text_to_mir() → ConstructionBundle |
| **测试** | `tests/integration/test_mma_adapter.py`：① MMA API 可用时端到端 construct；② 输出格式异构时 fail-closed 降级；③ Runtime 复跑 MMA 的代码并验证 |
| **验收标准** | MMA 输出的 ConstructionBundle 能被 Runtime 消费；模板资产导入且不复制 MMA 代码 |
| **是否改变 API** | 是：新增适配器 |
| **是否影响旧实验** | 否 |
| **是否需要迁移** | 否 |
| **预计依赖** | P1-3（Constructor Protocol） |
| **状态** | ✅ 已完成（2026-09-10）：`core/runtime/constructors/adapters/` 落地——`MathModelAgentAdapter`（MMA 产物目录加载，真实可用；CLI/API 通道未配置时 construct() 抛 ConstructorNotConfigured，禁止伪造）、`PiAdapter`（同目录加载模式）、`ReferenceConstructor`（内置最小参考 Constructor，benchmark baseline/regression/demo）；`tests/unit/test_constructor_adapters.py` 7 用例（未配置如实报错 / 目录加载 / capability 推断 / registry + apply_bundle 集成）。边界：MMA/Pi 均为 Worker/External Solver/Baseline，不触碰 Runtime 信任核心。论文/图表模板导入列 P3-4 目录重组一并处理 |

### P2-3：Model Selection 证据驱动化

| 项 | 内容 |
|---|---|
| **目标** | selection 不再恒取 recs[0]；evidence（VR 数值、fidelity、execution success）参与排序 |
| **为什么做** | 当前 evidence 只是"有/无"门禁，有 evidence 仍 chosen=recs[0]（selection.py:80）。"基于 evidence 选型"名不副实 |
| **不做的风险** | Candidate Arena 的多候选比较无意义（选型永远是检索 top-1） |
| **具体文件** | `core/runtime/modeling/selection.py:66-108`、`core/runtime/modeling/comparison.py` |
| **具体函数** | `MethodArena.select()`：evidence 非空时，用 comparison.py 的多指标排序（E4 指标）替代 recs[0]；evidence 为空时 UNSELECTED（保持当前门禁） |
| **测试** | `tests/unit/test_evidence_selection.py`：① 有 evidence 时选型基于 evidence 排序而非 recs[0]；② 无 evidence 时 UNSELECTED；③ selects 边真实写入 |
| **验收标准** | 构造两个候选，evidence 得分不同 → 选中 evidence 得分高的（非 recs[0]） |
| **是否改变 API** | 否（内部逻辑变更） |
| **是否影响旧实验** | 否 |
| **是否需要迁移** | 否 |
| **预计依赖** | P1-1（fidelity）、P2-1（L6） |

### P2-4：V2 兼容层路径修复或废弃

| 项 | 内容 |
|---|---|
| **目标** | 修正 orchestrator.py:58-59 的 _skill_path 为 core/legacy/hands/，或直接废弃 --legacy |
| **为什么做** | 当前 --legacy 模式必然失败（路径不存在），AGENTS.md 声称的"V2 兼容层已迁移"与代码不一致 |
| **不做的风险** | 用户/文档声称的兼容层实际不可用 |
| **具体文件** | `core/tools/orchestrator.py:58-59`、`core/tools/state.py:377` |
| **具体函数** | 修正路径或删除 --legacy 分支 |
| **测试** | `--legacy` 可用或明确报错"已废弃" |
| **验收标准** | --legacy 行为与文档一致 |
| **是否改变 API** | 是 |
| **是否影响旧实验** | 否 |
| **是否需要迁移** | 否 |
| **预计依赖** | 无 |
| **状态** | ✅ 已完成（2026-09-10）：`_skill_path` 修正为 `core/legacy/hands/<Hand>/agents/<agent>/SKILL.md`（orchestrator.py:58-59）、state.py:377 提示路径同步修正；四手 29 agent SKILL 路径全部可解析；`tests/unit/test_legacy_paths.py` 2 用例（路径指向 + 四手全解析） |

---

## P3：长期能力 + 实验验证（6+ 周）

### P3-1：Constructor × Runtime 2×2 析因 benchmark

| 项 | 内容 |
|---|---|
| **目标** | 执行第一个 Constructor-independent benchmark：C1（裸 Doubao）×C2（MathModelAgent）×R0/R1，6 题 × 5 rep = 120 runs，L6 为主终点 |
| **为什么做** | 这是唯一能回答"LinHoMo Runtime 带来多少建模增益"的实验 |
| **不做的风险** | 永远无法证明产品价值，所有架构决策都是假设 |
| **具体文件** | `research/P15/benchmark/constructor_independent/`（新建）、预注册协议 |
| **具体函数** | benchmark runner：2×2 析因执行 + block 配对 + bootstrap CI + 析因分解 |
| **测试** | 预注册五 Gate（G1 映射 / G2 κ / G3 词表 / G4 exec / G5 功效） |
| **验收标准** | 120 runs 完成；L6 主终点的 Runtime 主效应 Δ 有 95% CI；positive 或 negative 均如实归档 |
| **是否改变 API** | 否（实验层） |
| **是否影响旧实验** | 否 |
| **是否需要迁移** | 否 |
| **预计依赖** | P0 全部 + P1-3 + P2-1 + P2-2 |

### P3-2：L5 Revision 端到端度量实验

| 项 | 内容 |
|---|---|
| **目标** | 把 vs001 的 M1→FAIL→M2 从单题扩展到 6 题 × 多 rep，量化"验证义务→修正→最终正确"的因果增益 |
| **为什么做** | 承接 K002 SV−F(VAL)=+4.81 的未决假设；L5 是 LinHoMo 的核心增量层 |
| **不做的风险** | "Revision-capable"只有 vs001 n=1 的证据，无法系统证明 |
| **具体文件** | `research/P15/experiments/P15-K004/`（预注册） |
| **具体函数** | 实验 runner：故意引入可检测错误 → 测量修正概率/轮数/L6 提升 |
| **测试** | 预注册五 Gate |
| **验收标准** | 修正后 L6 提升量的 95% CI；有 revision vs 无 revision 的配对差分 |
| **是否改变 API** | 否 |
| **是否影响旧实验** | 否 |
| **是否需要迁移** | 否 |
| **预计依赖** | P1-2（Revision 接入主 DAG）、P2-1（L6 判定） |
| **状态** | ✅ 已完成（2026-09-10）：**P15-K004** 预注册 + runner（`research/P15/scripts/k004_runner.py`）+ 18 单元全量执行。Δ_L6=+1.0000 CI[+1.0000,+1.0000] H1 SUPPORTED；M1 失败真实性 18/18、M2 通过 18/18、Replay 18/18、修正轮数均值 1.0。报告 `research/P15/experiments/P15-K004/K004_REPORT.md`。范围如实披露：单题模板（2019_C M/M/c），测 Revision 执行/验证层；Revision 提议层（Agent 发现新错误）列 K004 v2 |

### P3-3b：Paper Projection 真实化（E2E 打通） ✅ 已完成（559930e/f1eeefc）

| 项 | 内容 |
|---|---|
| **目标** | paper 链从死代码变为真实闭环：Projection 统一消费 ScientificNarrative IR（6 节规范大纲），handlers 三节点（research_direction/paper_projection/paper_sections）全部走 IR |
| **为什么做** | 旧 PaperProjection 消费已废弃的 Narrative(.questions/.arcs)，paper 链从未真正跑通（占位符式假闭环） |
| **修复内容** | ① PaperProjection 重写：SECTION_ORDER 6 节（discussion 并入结论）、models→{model,question,assumptions}（assumes 边机械派生）、dead claim 排除并记 dead_claims_excluded（registry 终态+死证据传递闭包）、灵敏度章节 evidence=tags 含 sensitivity/baseline 的 active result、figures 经 supports 证据链 visualized_by 机械派生；② narrative_critic/judge_critic N1/UNKNOWN 判定兼容新旧协议（getattr arcs/sections）；③ do_research_direction 产 IR 入 shared[narrative]/narrative_ir |
| **测试** | test_writing_layer（6 节顺序/models 假设/灵敏度/死 claim 排除/pending placement）、test_judge_critic、test_narrative_critic、test_p7_integrity、test_red_team 全部升级 IR 契约；e2e_metrics writing denominator 12（DAG 实际节点）；full_run 全节点通过 |
| **验收标准** | 全量回归全绿；Projection 不再接触 .questions/.arcs；无任何旧 Narrative 注入路径 |
| **是否改变 API** | 是（project 消费 IR；旧 Narrative 仅 director 测试保留） |
| **是否影响旧实验** | 否（K001-K004 冻结基线不触碰） |

### P3-3：Pi Adapter + 沙箱边界

| 项 | 内容 |
|---|---|
| **目标** | 实现 PiAdapter（子进程/stdio 桥接）；参考其 session checkpoint/recovery 设计改进 RuntimeSession |
| **为什么做** | Pi 是通用 worker/执行基座，可作为 Constructor-independent benchmark 的 C3 臂 |
| **不做的风险** | benchmark 只有 2 个 Constructor，普适性不足 |
| **具体文件** | `core/runtime/constructors/adapters/pi.py` |
| **具体函数** | `PiAdapter.construct()`：子进程启动 pi CLI → 解析文件系统变更 → ConstructionBundle |
| **测试** | `tests/integration/test_pi_adapter.py` |
| **验收标准** | Pi 输出能被 Runtime 消费；沙箱边界方案落地 |
| **是否改变 API** | 是 |
| **是否影响旧实验** | 否 |
| **是否需要迁移** | 否 |
| **预计依赖** | P1-3 |

### P3-4：BZD 知识导入 + 目录结构重组

| 项 | 内容 |
|---|---|
| **目标** | BZD rubric/校准/自查清单导入为 knowledge 资产；按 ARCHITECTURE_FINAL.md 的推荐目录重组仓库结构 |
| **为什么做** | BZD 评审知识是 Evaluation 层的重要资产；当前目录结构有 Agent-centric residue / V2 residue / 死代码 |
| **不做的风险** | 目录混乱持续，新贡献者难以理解架构 |
| **具体文件** | `core/runtime/knowledge/packs/bzd_review.yaml`、目录重组 |
| **具体函数** | 知识导入脚本 + 目录迁移脚本 |
| **测试** | 迁移后全量测试通过；import 路径更新 |
| **验收标准** | BZD 知识可被 retriever 消费；目录结构符合 ARCHITECTURE_FINAL.md §4；所有经验常数打 provenance=empirical 标签 |
| **是否改变 API** | 是（目录重组改变 import 路径） |
| **是否影响旧实验** | 是（import 路径变更，需同步更新） |
| **是否需要迁移** | 是（大规模目录迁移，需分阶段） |
| **预计依赖** | P1-5（死代码清理后再重组） |

---

## 依赖关系图

```
P0-1 注入通道 ──┬── P0-4 零执行/验证≠PASS
                ├── P1-1 Fidelity 接入 ── P1-2 Revision 接入
                ├── P1-3 Constructor Protocol ── P2-2 MMA Adapter ── P3-1 2×2 benchmark
                └── P2-3 Selection 证据化
P0-2 validators 挂载 ── P0-5 mark_validated 门禁
P0-3 EXEC 来源鉴别（独立）
P0-6 K003 残余直写（独立）
P1-4 MODEL_IR 契约修复（独立）
P1-5 死代码清理（独立）── P3-4 目录重组
P2-1 L6 判定 ── P3-1 2×2 benchmark ── P3-2 L5 实验
P2-4 V2 路径修复（独立）
P3-3 Pi Adapter ── P3-1（C3 臂扩展）
```

---

## 验收总标准

所有 P0 完成后必须满足：
1. `orchestrator --execute --constructor-dir <dir>` 跑通 ≥15/20 节点，EXEC/VR/claim 均真实
2. 伪造 EXEC 100% 被拒绝
3. 零执行/零验证 → blocked（非 PASS）
4. engine.validators 非空，声明的 gate 真实执行
5. Agent 无法直接调 mark_validated
6. `py -3.12 -m pytest tests -q` 全绿
7. `py -3.12 core/tools/validate.py` 全绿
8. `py -3.12 core/tools/catalog_check.py --check` OK
9. K001/K002/K003 freeze --check 全部 PASS
10. git diff 仅包含本路线图声明的变更

---

*本路线图基于 5 路独立审计的代码证据。每项任务可独立验收，不依赖"看起来先进"的复杂度。*
