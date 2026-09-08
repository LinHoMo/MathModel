# P0-E Executable Model Runtime — 完成记录（2026-09-09）

> **战略裁决**（用户 2026-09-09）：P0-E 不是"又一个功能"，而是 LinHoMo 从
> **架构设计项目**跨入**可被科学实验检验的 modeling runtime** 的分水岭。
> 优先级：P0-E1/E2/E3 🔴 > P0-E4/E5 🟠 > K002 正式 prereg 🟡 > ontology 扩展/新 Skill/新 Agent/Paper intelligence 🟢（全部暂缓）。
> **原则**：STOP BUILDING ABSTRACT INFRA → MAKE MODEL EXECUTE → PRODUCE REAL RESULT → BUILD REAL EVIDENCE → BLINDLY EVALUATE → SHOW REPRESENTATION IMPROVES MODEL CONSTRUCTION。

## 1. 最小闭环（已打通）

```text
MODEL_IR ──→ ExecutionPlan ──→ Code Generation* ──→ Code Interpreter ──→ ExecutionResult ──→ Evidence ──→ EvidenceGate
```

- `*` Code Generation 由外部 Agent / 未来 code generator 提供（本轮闭环：外部提供 code → adapter 真实执行）。
- 本轮打通：**ExecutionAdapter（真实执行）+ ExecutionResult 一等 artifact + do_experiment 集成 + executed_by 证据绑定**。

## 2. 交付物

| 模块 | 位置 | 说明 |
|---|---|---|
| ExecutionAdapter 抽象 + LocalPython | `core/runtime/execution/adapters.py` | subprocess 执行 Python，零依赖；可替换 E2B/Docker/Syslab |
| execution_result 一等 artifact | `core/runtime/artifacts/ids.py`（EXEC 前缀） | 与 E/R/F/C 同级的一等对象 |
| executed_by 关系 | `core/runtime/graph/evidence_graph.py` | result → execution_result（Evidence←Execution 强绑定） |
| session 透传 | `core/runtime/execution/session.py` | `execution_adapter` 参数 |
| do_experiment 集成 | `core/runtime/execution/handlers.py` | adapter+code → 真实执行 → result.status 翻写 + EXEC artifact + executed_by 边 |
| 测试 | `tests/unit/test_execution_adapter.py` + `tests/integration/test_execution_runtime.py` | 12 + 4 用例 |

## 3. ExecutionResult 一等 artifact 契约（用户指定字段全集）

```json
{
  "execution_id": "EXEC001",
  "model_id": "M001",
  "status": "not_executed|running|success|failed|timeout|invalid",
  "inputs": {},
  "outputs": {},
  "stdout": "",
  "stderr": "",
  "returncode": 0,
  "duration_ms": 1234,
  "code_hash": "sha256",
  "environment_hash": "sha256",
  "started_at": "ISO8601",
  "finished_at": "ISO8601",
  "provenance": {"adapter": "local_python", "python": "..."}
}
```

**铁律**：`status` 只能来自真实执行状态，**绝不默认 success**（无 adapter/无 code → result 保持 `not_executed`）。

## 4. 状态语义（唯一合法来源）

| 状态 | 触发 |
|---|---|
| not_executed | 未提供 adapter 或无可执行 code（外部 executor 回填路径） |
| running | 执行中（本轮 subprocess 同步执行未暴露；保留给异步后端） |
| success | subprocess returncode==0 |
| failed | returncode≠0（stderr 含错误） |
| timeout | 超过 timeout_seconds |
| invalid | 空代码 / framework error / adapter 异常 |

## 5. Evidence 哲学（用户裁决）

> **Evidence 不是 Agent 写出来的，是 execution substrate 产生的。**

`Claim → requires Evidence → Execution → ExecutionResult → Evidence → supported/unsupported`
——执行产物成为 claim 支撑的**唯一机械来源**；这同时给 BZD 式 reviewer knowledge 一个可靠 substrate（Knowledge → Modeling Policy → Model → Execution → Evidence → Reviewer）。

## 6. 验证

| 项 | 结果 |
|---|---|
| `tests/unit/test_execution_adapter.py` | 12 passed（success/failed/timeout/invalid 四态 + 字段契约 + 类型注册） |
| `tests/integration/test_execution_runtime.py` | 4 passed（无 adapter→not_executed；有 adapter 无 code→not_executed；有 code→success + executed_by 边；failed 代码→failed） |
| `tests/unit/test_evidence_graph.py` | 更新为 15 关系类型，passed |
| 全量 pytest | 待确认（预期 774+16） |

## 7. 后续（P0-E 余项，按用户优先级）

- **P0-E4 Replay/provenance**：`replay.py` 支持按 code_hash/environment_hash 重放（数据已就绪，工具待扩展）。
- **P0-E5 K002 dry-run**：用 adapter 产物走一遍 K002 预检（五 Gate 的 G4 验证 execution 终点）。
- **Code Generation**：MODEL_IR → 可运行代码的自动生成（外部 Agent 或规则模板，下一大步）。
- **K002 冻结顺序**：P0-E runtime validation → K002 dry-run → 题目区分度检查 → 五 Gate → PREREGISTERED → FROZEN。
