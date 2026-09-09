# P1 Model Construction Runtime — Implementation Plan

> 日期：2026-09-09 · 依据：MODEL_CONSTRUCTION_GAP_AUDIT.md（10 环节证据级审计）
> 原则：**LLM-free**——MODEL_IR/Code 由外部 Agent 产出，core 只登记/校验/执行/保真/验证/谱系；
> 不做新 Agent、不做新顶层架构；每步有测试、有验收、有 commit。
> 目标：打通 `Problem → Model → Code → Execution → Evidence → Validation → Revision` 最小闭环。

---

## 依赖图

```
P1.0 schemas ─┬→ P1.1 MODEL_IR builder ─┬→ P1.2 selection 真实化
              │                          └→ P1.4 exec schema 校验（防伪造）
              └→ P1.3 执行接线（orchestrator 传 adapter + handlers 接 codegen）
                                              │
                              P1.5 Validation L0-L4（engine 挂钩 + VR 进 DAG）
                                              │
                              P1.6 Evidence 修复（implemented_by/claim/gate 数值）
                                              │
                              P1.7 Revision 谱系（revision_of/supersedes + M1→M2）
                                              │
                              P1.8 端到端演示 + 全量自检
```

---

## P1.0 — Schemas 先行（commit: `feat(p1): schemas for model_ir/execution_result/verification_result/claim`）

| 文件 | 动作 |
|---|---|
| `core/schemas/v3/modeling/model_ir.schema.json` | **新增**：从 `research/P15/model_representation/model_ir.schema.json` 迁入（18 required 顶层字段），加 `x-role: external-agent-produced` |
| `core/schemas/v3/run/execution_result.schema.json` | **新增**：status 枚举六态 + execution_id/model_id/code_hash/env_hash/duration_ms/provenance 必填 |
| `core/schemas/v3/run/verification_result.schema.json` | **新增**：VR 三态（passed/failed/invalid）+ check_id/evidence_refs |
| `core/schemas/v3/evidence/claim.schema.json` | **新增**：statement 禁占位（`execution_status` 必填、`provenance` 必填） |
| `core/tools/catalog_check.py` | 同步 schema 清单（如有一致性检查） |
| 测试 `tests/unit/test_p1_schemas.py` | 断言：4 schema JSON 合法；execution_result 缺 status → 校验失败；claim statement 含"结论"占位 → 校验失败 |

验收：pytest 全绿；`catalog_check --check` OK。

---

## P1.1 — MODEL_IR Builder（commit: `feat(p1): MODEL_IR register builder — 登记/校验/落库/边`）

| 文件 | 动作 |
|---|---|
| `core/runtime/modeling/builder.py` | **新增** `ModelIRBuilder`：`register_model_ir(model_ir: dict, question_id, card_id=None) -> model_ir_id`——schema 校验（P1.0）→ `registry.create("model_ir", data=...)` → 写 `model --implements--> model_ir` 边（新增边类型，见 P1.6）→ 返回 id |
| `core/runtime/execution/handlers.py` | `do_model_construction` 改造：model artifact `data` 由 `{card_id,family,shortlist}` 升级为持有 `model_ir_id`（引用 P1.1 builder 产出） |
| `core/runtime/artifacts/ids.py` | 加 `"model_ir"` artifact 类型 |
| `core/runtime/graph/evidence_graph.py` | 注册新边 `"implements": ({"model"}, {"model_ir"})` |
| 测试 `tests/integration/test_model_ir_builder.py` | 断言：合法 MODEL_IR → registry 有 model_ir artifact + implements 边；非法（缺 required 字段）→ 拒绝；question_id 不存在 → 拒绝 |

验收：Model Construction 节点产出可追溯 MODEL_IR（不再是方法卡指针）。

---

## P1.2 — Selection 真实化（commit: `feat(p1): candidate 一等对象 + selects 边 + evidence 选择依据`）

| 文件 | 动作 |
|---|---|
| `core/runtime/modeling/selection.py` | `do_model_selection`：候选持久化——`registry.create("candidate", data={card_id,score,risk,validation_cost})`；`chosen` 不再裸用 `recs[0]`，写入 `alternatives`（全部候选 id）+ `criteria`（真实评估键）+ `evidence_ids`（检索证据）+ `chosen` + `confidence` |
| `core/runtime/execution/handlers.py` | `do_model_selection` 成功后写 `decision --selects--> model` 边（DecisionLog 已登记，补图边） |
| `core/runtime/artifacts/ids.py` | 加 `"candidate"` artifact 类型 |
| 测试 `tests/unit/test_model_selection.py` 扩展 | 断言：候选进 registry；selects 边存在；evidence_ids 非空（有检索证据时）；`chosen` 在 alternatives 内 |

验收：`selects` 边有写入方；"为什么选这个模型"可由 Decision + 边 + 候选 artifact 机械回答。

---

## P1.3 — 执行接线（commit: `fix(p1): orchestrator 传 execution_adapter + handlers 接 codegen 闭环`）

| 文件 | 动作 |
|---|---|
| `core/tools/orchestrator.py` | `--execute` 路径构造 `LocalPythonAdapter` 并传入 `RuntimeSession(execution_adapter=...)`（当前 `orchestrator.py:391-392` 不传） |
| `core/runtime/execution/handlers.py` | `_maybe_execute_experiment`（死代码）修复：plan 无 code 键时从 `shared[qid]["external_code"]` 或 registry code artifact 取；接入 `run_code_pipeline`（codegen.py） |
| `core/runtime/execution/handlers.py` | 无 adapter / 无 code 时不再静默 return：显式 `execution_result.status="not_executed"` 且 DAG 节点标记 `EXEC_SKIPPED`（可观测，不再假装） |
| `core/runtime/execution/handlers.py:452-454` | 执行失败（failed/timeout/invalid）→ 节点返回 **FAIL**（不再是恒 PASS） |
| `core/runtime/modeling/planner.py` | `experiment_plan` 输出加 `code` 键（外部 code 引用或占位声明），供 DAG 消费 |
| 测试 `tests/integration/test_execution_wiring.py` | 断言：orchestrator 默认 run 至少 1 个 execution_result（不再为 0）；失败代码 → 节点 FAIL；无 adapter → not_executed 且可见标记 |

验收：默认 V3 run 真实执行（execution_result 数 > 0）；失败不再被伪装成 PASS。

---

## P1.4 — execution_result 防伪造（commit: `fix(p1): EXEC schema 校验 — status 只能来自真实执行`）

| 文件 | 动作 |
|---|---|
| `core/runtime/artifacts/registry.py` | `create("execution_result")` 时校验 `run/execution_result.schema.json`（P1.0）；`status` 非六态 → 拒绝 |
| `core/runtime/execution/adapters.py` | status 派生保持唯一真源（exit code / timeout / invalid 路径），无任何 handler 可覆盖 |
| 测试 `tests/unit/test_p1_schemas.py` 扩展 | 断言：伪造 status="success" 的 dict → registry 拒绝；真实 adapter 产出 → 通过 |

验收：`execution_status=success` 在系统内只能来自真实执行（exit code 0）。

---

## P1.5 — Validation L0–L4（commit: `feat(p1): validation 分层 + engine 挂钩 + VR 进 DAG 决策`）

| 文件 | 动作 |
|---|---|
| `core/runtime/execution/validation.py` | 加 `VALIDATION_LEVELS` 枚举：L0 schema / L1 execution / L2 fidelity / L3 mathematical / L4 empirical；`run_checks` 支持按 level 分组 |
| `core/runtime/execution/fidelity.py` | fidelity 结果挂 `level="L2"`；输出 `fidelity_report`（F1-F5 明细） |
| `core/runtime/execution/engine.py` | RuntimeSession 构造时接收 validators（当前 `session.py:84-88` 未传）；执行后自动跑 VR；VR 失败 → 节点 FAIL |
| `core/runtime/execution/handlers.py` | `do_experiment` 消费 VR：VR=failed → FAIL 且触发 revision 钩子（P1.7） |
| 测试 `tests/integration/test_validation_levels.py` | 断言：L0/L1/L2 分层可独立运行；VR failed → 节点 FAIL；VR 进入 registry（verification_result artifact） |

验收：验证不再"只记录不决策"——VR 是 DAG 决策输入。

---

## P1.6 — Evidence 修复（commit: `fix(p1): implemented_by 边 + claim 绑定 + gate 数值真实性`）

| 文件 | 动作 |
|---|---|
| `core/runtime/execution/codegen.py` | `register_code` 时写 `model --implemented_by--> code` 边（当前零写入方） |
| `core/runtime/graph/evidence_graph.py` | 修正 `executed_by` 语义：`code --executed_by--> execution_result`（当前为 result→exec，错位）；`execution_result --produces--> result` 边补充 |
| `core/runtime/execution/handlers.py` | `do_evidence_build`：claim `statement` 不再用 `"{qid} 结论"`——必须引用 result/evidence（`evidence_refs` 非空才创建 claim）；占位 → 拒绝创建 |
| `core/runtime/execution/evidence_gate.py` | E1–E8 增补：result.data 有数值（非空）；claim 非占位；execution_result 存在且 status=success/failed（有真实状态） |
| 测试 `tests/integration/test_evidence_integrity.py` | 断言：implemented_by 边在 codegen 后存在；占位 claim 被拒；gate 对空 result 判 FAIL |

验收：Evidence Graph 的 model→code→exec→result→claim 链完整且无占位。

---

## P1.7 — Revision 谱系（commit: `feat(p1): revision_of/supersedes 边 + M1→M2 自动触发`）

| 文件 | 动作 |
|---|---|
| `core/runtime/graph/evidence_graph.py` | 新增关系 `"revision_of": ({"model"}, {"model"})`、`"supersedes": ({"model"}, {"model"})`（含传播档） |
| `core/runtime/execution/handlers.py` | 新增 `do_model_revision`：VR FAIL / execution FAIL → 生成 `revision_request`（诊断 + 建议）→ 外部 Agent 产出 M2 → `registry.create("model")` + `model2 --revision_of--> model1` |
| `core/runtime/execution/engine.py` | DAG 支持 revision 回边（FAIL → 回到 model_construction 节点重跑，max_revisions=1 默认） |
| `core/runtime/execution/evidence_gate.py` | `retract_invalidated` 不再剪断 revision 谱系（保留 revision_of/supersedes 链） |
| 测试 `tests/integration/test_model_revision_loop.py` | 断言：M1 FAIL → M2 自动产生；revision_of 边存在；M2 执行通过 → 图完整可追溯 |

验收：`M1→E1→V1 FAIL→M2→E2→V2 PASS` 最小闭环端到端可跑（测试内注入外部 M2 产物模拟外部 Agent）。

---

## P1.8 — 端到端演示 + 全量自检（commit: `test(p1): end-to-end Model Construction Loop + 全量验证`）

| 动作 |
|---|
| `tests/integration/test_p1_end_to_end.py`：一个最小 run（2019_C 子集）：Problem→MODEL_IR（外部注入）→Decision→Code（外部注入）→Execution→Fidelity→Validation→FAIL→Revision→M2→PASS→Claim 全链断言 |
| 全量自检：`py -3.12 -m pytest tests -q`（≥855/4，新增不回归）；`catalog_check --check` / `--check-terminology`；`validate.py`（57/0） |
| 更新 `docs/STATUS.md` 与 `P15-EXPERIMENT-CONTRACT-v2.md`（P1 链路节点标准） |

验收：全链自检全绿；一个真实最小闭环可复现。

---

## 分批建议（每批一个可运行里程碑）

| 批 | 内容 | 里程碑 |
|---|---|---|
| Batch 1 | P1.0 + P1.1 + P1.2 | Model Construction 前半段闭环（Problem→MODEL_IR→Decision 可追溯） |
| Batch 2 | P1.3 + P1.4 | 默认 V3 run 真实执行 + status 不可伪造 |
| Batch 3 | P1.5 + P1.6 + P1.7 | Validation 决策 + Evidence 完整 + Revision 谱系 |
| Batch 4 | P1.8 | 端到端演示 + 全量验证 + 文档同步 |

> 依赖说明：Batch 间无强依赖（P1.0 是所有前置）；但 P1.6 的边语义修正应先于 P1.3 的 executes 接线做（避免继续写错位边）。
