# AGENT AUTHORITY MODEL — Agent 权限模型与"The Agent Is Not The State"执行审计

> **基于 5 路独立审计的代码证据**。核心原则：Agent Claim ≠ System Fact。只有机械状态（filesystem / artifact / hash / git / freeze manifest / validator / execution_result）能推进状态机。

---

## 1. AGENT AUTHORITY MATRIX（最终）

| Artifact / State | Owner | Agent 可写? | 机械 Harness 可写? | 当前合规? |
|---|---|---|---|---|
| Problem interpretation | Agent | ✅ | — | ✅ |
| Candidate models | Agent | ✅ | — | ✅（但 TEST-ONLY） |
| MODEL_IR | Agent | ✅（通过 external_* 注入） | — | ✅ |
| Code | Agent | ✅（通过 external_code 注入） | — | ✅ |
| ExecutionPlan | Agent/Runtime | ✅ | ✅ | ✅ |
| **ExecutionResult** | **Harness（机械 subprocess）** | ❌ **禁止** | ✅ | ⚠️ **违规**：registry.create 无来源鉴别，伪造可通过 |
| **Fidelity** | **Harness** | ❌ **禁止** | ✅ | ✅（但未接入主路径） |
| Evidence（边） | Runtime | ❌（add_relation 开放 API 无身份绑定） | ✅ | ⚠️ 设计缺口 |
| **Validation PASS** | **Validator** | ❌ **禁止** | ✅ | ❌ **违规**：critic SKILL.md 指令 Agent 调 mark_validated |
| PASS/FAIL（节点） | Validator / Engine | ❌ | ✅ | ✅ |
| Revision Proposal | Agent | ✅ | — | ✅（但 revision 不在主 DAG） |
| Revision lineage（supersede/revision_of） | Runtime | ❌ | ✅ | ⚠️ vs001 由 runner 手工 add_relation |
| Final State（validated/published） | Runtime | ❌ | ✅ | ⚠️ 机械路径下模型永停 draft（validators 未接线） |

---

## 2. 违反权限模型的路径（全部清单，含 file:line）

### 2.1 【高】Agent 直接写 Validation PASS

| 位置 | 违反内容 | 证据 |
|---|---|---|
| `core/skills/critics/model-critic/SKILL.md:63` | Agent 指令执行 `mark_validated("model-critic", report)` | Agent 写 validation PASS |
| `core/skills/critics/experiment-critic/SKILL.md:52` | Agent 指令执行 `mark_validated` + 打 sensitivity/baseline tags | Agent 写 validation PASS |
| `core/runtime/artifacts/registry.py:257` / `artifact.py:168` | `mark_validated` 无调用方白名单、无"验证器已实际运行"证明要求 | 放大上述两条；任何持有 registry 引用的代码可调用 |

**后果**：这是当前唯一能让模型获得 validated 状态的路径（机械路径下 validators 未接线，模型永停 draft）。Authority Matrix 中"Validation | Validator"所有权被 Agent 侵占。

**修复**：
1. `mark_validated` 增加门禁：validator 白名单 + 必须携带"验证器运行记录"（run id/hash）
2. 改写两条 critic SKILL.md：删除直接 `mark_validated` 指令，改为"提交 review report，由 runtime 登记"
3. 引擎 validators 钩子接线（见 2.2），使机械验证路径成为唯一通道

### 2.2 【高】引擎 validator 钩子空接

| 位置 | 违反内容 | 证据 |
|---|---|---|
| `core/runtime/execution/session.py:96-100` | 构造 WorkflowEngine 时不传 validators | `self.engine = self.waves.engine` 覆盖，waves 内建 engine `validators=None` |
| `core/runtime/execution/wave_executor.py:28-31` | 内建 engine `state=None, validators=None` | 实测 `engine.validators = {}` |
| `core/runtime/execution/engine.py:181-190` | `_run_validator` 钩子存在但永不触发 | validators 表恒空 = 功能性 dead |
| `catalog/v3.yaml` | 声明 6 个 validator（model-critic/assumption-checker/experiment-critic/evidence-gate/research-quality/judge-critic） | 声明与实际执行脱节 |
| `core/runtime/state/model.py:282-285` | `models.selected` 只认 validated/published | 机械路径下恒为空 |

**后果**：声明的验证义务无人执行。critic 节点退化为 artifact 存在性检查（`handlers.py:1474-1492`）。

**修复**：session.py 构造 engine 时传入 validators；至少为 model-critic / assumption-checker 提供机械实现或显式 UNKNOWN。

### 2.3 【高】ExecutionResult 无来源鉴别（K003 事故可复现）

| 位置 | 违反内容 | 证据 |
|---|---|---|
| `core/runtime/artifacts/registry.py:108-145` | `registry.create("execution_result", data=任意dict)` 无 schema 门禁、无来源鉴别 | 只做通用 Artifact 校验 |
| `core/runtime/artifacts/artifact.py:110-152` | EXEC 校验只挡空壳（空 outputs / 空 hash / 假 status / rc≠0） | 挡不住"编造 outputs + 编造 hash + 编造 stdout"的完整伪造 |
| `artifact.py:137` | `code_hash` 仅要求 `len >= 16` | 弱校验 |
| `artifact.py:145-147` | code↔hash 一致性在无 code 字段时跳过 | 可绕过 |

**实测复现**：`registry.create("execution_result", data={status:"success", outputs:{x:1.0}, code_hash:"f"*16, returncode:0})`（无 code 字段）→ **通过门禁**（FORGED SUCCESS ACCEPTED）。

**K003 事故现场**：`research/P15/experiments/P15-K003-precheck/state/registry.json` EXEC001-3，`created_by=external_agent`，结构完整伪造。

**修复**：EXEC 必须携带 adapter 签发的 execution_id/不可伪造字段；门禁强制 code 同源 + sha256 全 64 位 + code↔model_ir 一致性。

### 2.4 【中】零执行 = PASS / 零验证 = PASS

| 位置 | 违反内容 | 证据 |
|---|---|---|
| `handlers.py:753` | `do_model_execution` 执行 0 个模型也返回 PASS | "未执行 = PASS" |
| `handlers.py:776-781` | `do_model_validation` 无 spec 时 validate_execution 返回 [] → 0/0 PASS | "未验证 = PASS"；实测 0 VR 全绿 |
| `handlers.py:777` | 有 FAIL 候选但 n_pass>0 时 PASS | 只拦"n_fail>0 且 n_pass==0" |
| `evidence_gate.py:208-215` | E9 只查 `EXEC.status=="success" and outputs 非空`，不检查 VR 存在 | "有执行无验证"的 claim 可通过 gate |

**修复**：
- model_execution 无代码 → blocked（非 PASS）
- model_validation 无 spec → blocked（非 PASS）
- E9 增加 VR 存在性要求
- n_fail>0 时即使 n_pass>0 也应标记 partial_fail

### 2.5 【中】K003 残余直写路径

| 位置 | 违反内容 | 证据 |
|---|---|---|
| `research/P15/experiments/P15-K003/k003_formal_runner.py:829` | 当 `write_run_execution` 自身抛异常时，Runner 直接 `(run_dir / "execution_result.json").write_text(...)` 写 error 壳 | 绕过 execution_writer 唯一写入路径 |
| `tests/unit/test_k003_governance.py` | 结构测试仅 grep `write_json(run_dir / "execution_result.json"` 形式 | 漏掉 `.write_text(` 变体，产生虚假安全感 |

**修复**：删除 fallback，改为失败时写独立 error log，不触碰 execution_result.json；结构测试覆盖 `.write_text(` 变体。

### 2.6 【中】add_relation 开放 API 无身份绑定

| 位置 | 违反内容 | 证据 |
|---|---|---|
| `core/runtime/graph/evidence_graph.py:163-196` | `add_relation()` 是开放 API，无关系类型/写入者门禁 | 任何拿到 graph 引用的代码可写 supports 边 |
| `handlers.py:1579-1587` | claim 的 supports 边要求 exec_ref（FIX-4.1） | 这是正确的约束，但仅在 claim 合成路径强制执行 |

**修复**：add_relation 增加写入者上下文（created_by），关键关系（supports/verified_by/executed_by）要求携带机械来源证明。

### 2.7 【低-中】V2 兼容层路径损坏

| 位置 | 违反内容 | 证据 |
|---|---|---|
| `core/tools/orchestrator.py:58-59` | `_skill_path()` 解析为 `core/Modeler/agents/...`（实测不存在） | 正确路径是 `core/legacy/hands/Modeler/agents/...` |
| `core/tools/state.py:377` | 状态提示同样输出旧路径 | — |

**后果**：`--legacy` 模式当前必然失败。AGENTS.md 声称的"V2 兼容层已迁移"与消费方代码不一致。

**修复**：修正路径为 `core/legacy/hands/<Hand>/agents/...`，或直接废弃 `--legacy`。

---

## 3. "The Agent Is Not The State" 执行情况

### 3.1 合规的部分（做得好的）

| 机制 | 位置 | 判定 |
|---|---|---|
| status.json 由 artifact 重建 | `core/runtime/state/reconcile.py:49-145` | ✅ 用 registry+graph 重新派生"理想投影"与落盘 status.json 逐项 diff——本仓库最硬的"Agent Is Not The State"证据 |
| state.py init 从产物反推 | `core/tools/state.py:303-328` | ✅ sync_from_artifacts |
| state.py advance 耦合 gate | `core/tools/state.py:400-456` | ⚠️ 半合规：advance 由 Agent 触发，但 gate.py fail-closed（HARD/ERROR 拒推） |
| ExecutionResult 由 subprocess 写入 | `adapters.py:198-206` | ✅ status 由 returncode 推导 |
| K003 execution_writer 唯一写入者 | `execution_writer.py:2-9,74-84` | ✅ FIX-4.2/4.3 已收敛（残余 2.5） |
| 字符串状态断言 | `core/runtime` 内 14 处 | ✅ 全部为机械数据读取，无 Agent 声称类 |

### 3.2 违规的部分（需修复）

| 位置 | Agent 声称内容 | 系统事实兜底? | 判定 |
|---|---|---|---|
| `core/skills/critics/*/SKILL.md:63/52` | Agent 报告 model 通过批判并 mark_validated | ❌ 无（机械路径不接线） | ❌ Agent claim = 状态 |
| `core/tools/state.py advance` | Agent 声明某步完成 | ✅ gate.py fail-closed | ⚠️ 半合规 |

### 3.3 K003 事故的制度化

K003 曾发生 Organizer 声称 execution 完成但 execution_result 伪造/硬编码的事故。当前状态：

| 修复项 | 状态 | 证据 |
|---|---|---|
| 唯一写入者收敛 | ✅ | `execution_writer.py:2-9` 明确"唯一写入者" |
| 数值来自真实 subprocess | ✅ | `run_summary.json` 66/66，note: "status 仅来自 returncode" |
| 结构测试 | ✅ | `tests/unit/test_k003_governance.py` |
| 残余直写路径 | ⚠️ | `k003_formal_runner.py:829` fallback（见 2.5） |
| registry 层来源鉴别 | ❌ | 仍可伪造（见 2.3） |

**事故教训制度化**：
1. ExecutionResult 的写入权必须结构性地只属于 ExecutionAdapter，不能靠"唯一写入者"的文档声明
2. 结构测试必须覆盖所有写入形式（write_json / write_text / json.dump / 直接赋值）
3. registry.create 必须对 EXEC 类型做来源鉴别，不能只做通用 Artifact 校验

---

## 4. 状态机真源审计

| 模块 | 真源 | 判定 |
|---|---|---|
| `core/runtime/state/model.py:refresh_from`（:301-310） | registry + graph（models.selected 按 status 过滤；question 晋级由 supports 边驱动） | ✅ artifact 真源 |
| `core/runtime/state/reconcile.py:49-145` | 用 registry+graph 重新派生"理想投影"与落盘 status.json 逐项 diff | ✅ 强实现 |
| `core/tools/state.py` | init 从产物反推；advance 耦合 gate | ✅ 基本 artifact 真源 |
| `projects/*/state/status.json` | 投影结构（claims_supported 来自 graph coverage） | ✅ |

**结论**：状态机真源整体成立。唯一"Agent 声称 = 状态"残留是 critic 技能的 mark_validated 路径（2.1）。

---

## 5. 修复优先级

| 优先级 | 修复项 | 文件 | 验收标准 |
|---|---|---|---|
| **P0** | mark_validated 门禁 + critic SKILL 改写 | `registry.py:257` + `artifact.py:168` + 2 个 SKILL.md | Agent 无法直接调用 mark_validated；只能提交 review report |
| **P0** | Engine validators 挂载 | `session.py:96-100` + `wave_executor.py:28-31` | 实测 engine.validators 非空；catalog 声明的 gate 真实执行 |
| **P0** | EXEC 来源鉴别 | `artifact.py:110-152` + `registry.py:108-145` | 伪造 EXEC（无 code 字段 + 16 字符 hash）被门禁拒绝 |
| **P0** | 零执行/零验证 ≠ PASS | `handlers.py:753,776-781` + `evidence_gate.py:208-215` | 无代码 → blocked；无 spec → blocked；E9 要求 VR |
| **P1** | K003 残余直写删除 | `k003_formal_runner.py:829` + 测试 | 无 .write_text(execution_result.json)；结构测试覆盖 |
| **P1** | add_relation 写入者上下文 | `evidence_graph.py:163-196` | 关键关系要求 created_by + 机械来源证明 |
| **P2** | V2 路径修正或废弃 | `orchestrator.py:58-59` + `state.py:377` | --legacy 可用或明确移除 |
| **P2** | Revision lineage 机械化 | `handlers.py` + `catalog/v3.yaml` | revision_of/supersedes 边由 runtime 生成，非 runner 手工 |

---

## 6. 不变量（写死）

1. **Agent Claim ≠ System Fact**：任何 Agent 输出的"完成/通过/成功"必须经过机械验证才能成为系统状态
2. **ExecutionResult 仅由 subprocess 基底写入**：结构性限制，不靠文档声明
3. **Validation PASS 仅由 Validator 写入**：Agent 提交 review report，由 runtime 登记 validated 状态
4. **零执行 ≠ PASS，零验证 ≠ PASS**："没做"和"做了且通过"必须区分
5. **Evidence 边必须带 exec_ref**：claim 的 supports 边必须指向真实 ExecutionResult
6. **状态仅由 filesystem/artifact/hash/validator 推进**：Organizer 报告、Agent 进度、文字声称都不是状态
7. **FROZEN 后不改冻结项**：改 = new revision，旧版作废

---

*本模型基于 5 路独立审计的代码证据。所有违反路径附 file:line，可直接定位修复。*
