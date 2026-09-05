# Runtime Contracts — P7 契约冻结（v1.0，2026-09-05）

> **本文件是 V3 Runtime 的语义契约真源。** 任何 handlers / gate / critic / tool
> 的行为与本文件冲突时，以本文件 + `core/runtime/contracts.py`（代码真源）为准。
> 修改契约必须同时改：本文档、`contracts.py`、`lifecycle.py`、对应测试。

范围约束（P7 任务书）：**NO new agents / NO new top-level directories /
NO architecture rewrite / NO paper-quality work / NO new workflow features。**

---

## 1. 事实来源层级（Source of Truth）

```text
Artifact Registry + Evidence Graph + Research State   ← 唯一事实来源
        ↑ 派生
Node 执行器内存上下文（shared）                        ← 仅加速缓存，可随时丢弃
        ↑ 输入
Agent / LLM / Handler / Tool                          ← 永远不是事实来源
```

**不变量 S1**：任何 handler 在崩溃/重启后必须能仅凭 Registry + Graph + State
重建其继续执行所需的全部上下文。handler 禁止把"只存在于内存"的信息当作可复用
事实（P7 修复的 E8 死循环、resume 断链均源于违反本条）。

**不变量 S2**：Agent/LLM 的陈述（"模型 A 比模型 B 好"）不得直接进入论文——
必须先落为 Artifact + Evidence 关系，经 Evidence Gate 判活后才可投影。

---

## 2. Artifact Lifecycle Contract

权威状态机：`core/runtime/artifacts/lifecycle.py`（fail-closed，未列出转换一律拒绝）。
语义谓词代码真源：`core/runtime/contracts.py`。

| 状态         | 可复用 | 可进证据图     | 可支撑 Claim | 可进论文投影 | 审计保留 |
|--------------|--------|----------------|--------------|--------------|----------|
| draft        | 否     | 边可挂（E6 弱）| 否           | 否           | 是       |
| active       | **是** | 是             | 是           | 是           | 是       |
| validated    | **是** | 是             | 是           | 是           | 是       |
| published    | **是** | 是             | 是           | 是           | 是       |
| blocked      | 否     | 是             | 否           | 否           | 是       |
| superseded   | 否     | 否（剪边）     | 否           | 否           | 是       |
| invalidated  | 否     | 否（剪边）     | 否           | 否           | 是       |
| deprecated   | 否     | 否（剪边）     | 否           | 否           | 是       |

**不变量 L1（Terminal Immutability）**：终态产物不可转出（状态机强制）。
**不变量 L2（Non-Reusable）**：handler 复用判断一律使用 `contracts.is_reusable()`，
禁止手写 status 元组或 `if exists: reuse`。
**不变量 L3（Audit Retention）**：终态产物保留在 Registry 及其 lifecycle_history；
剪边（`retract_invalidated`）只删关系，不删产物。
**不变量 L4（Supersession ≠ Invalidation）**：
* `superseded` = 被主动重跑的新谱系替代（旧链并非"错"，仅过时）；
* `invalidated` = 证据失效传播判定死亡（数据勘误、上游失效）。
* 两者都不可复活、不可复用、不可进入论文；区别在触发源与审计含义。

---

## 3. Evidence Lifecycle Contract

* 失效传播（`EvidenceGraph.invalidate`）只标记不删除；传播完成后由
  `retract_invalidated()` 剪除触及终态产物的死边（幂等，剪边不撤标记）。
* Evidence Gate（E1–E8）清点口径：
  * E1/E2（无主张/无支撑）只统计**非终态** claim；
  * E3（链含死产物）闭包排查走**全部** claim——死 claim 的死链正是要抓的；
  * E4/E5 清点只统计**非终态** experiment/result（终态实验的 produces 边已被剪除）。
* 叙事/投影口径（N 系列）：
  * `ResearchDirector` 保留死弧供审计（`arc.status == "dead"` ↔ claim 终态）；
  * `PaperProjection` 排除死弧；`pending_placement` 不含死弧；
  * N2 只在死主张**仍被投影**时 FAIL（剔除失败），N5 在结果章节为空时 FAIL。

---

## 4. NodeResult Contract

```python
executor(node_id, ctx) -> NodeResult
NodeResult.outputs 允许键（contracts.NODE_RESULT_OUTPUT_KEYS）:
    artifacts: list   # 产出说明（默认 handlers 直接写 Registry；LLM 节点用）
    evidence:  list   # [{from, relation, to}]，ID 必须已注册
    metrics:   dict
    context:   dict   # 只读约定
```

校验函数：`contracts.validate_node_result_outputs()`（多余键/类型错 = 违约）。
PASS 结果先过 validator（engine `validators` 挂钩），否决走统一 retry→反馈环；
节点最终 PASS 后 `on_success` 挂钩把 evidence 登记进图。

---

## 5. 执行语义四分（P7 冻结）

| 语义       | 触发源               | 入口                              | 旧谱系归宿     |
|------------|----------------------|-----------------------------------|----------------|
| **Resume** | 进程崩溃/重启        | `session.resume()`                | 不产生新谱系   |
| **Retry**  | 节点执行失败（自动） | 引擎内 `max_retries` → on_fail    | 不产生新谱系   |
| **Rerun**  | 研究者主动要求       | `session.rerun(node_id)`          | 整链 **superseded**，全新 Artifact |
| **Recompute** | 上游证据失效      | `session.invalidate(artifact_id)` | 受影响分支 **invalidated**，重建新链 |

---

## 6. 并发契约（Concurrent Wave Safety）

* Registry / EvidenceGraph / DecisionLog 内部持 `RLock`：
  ID 分配、关系追加、决策登记在并行波次下互斥，ID 零重复、边零重复。
* WaveExecutor 并行边界：**executor 调用并行，引擎落账串行**（`apply_result`）。
  节点执行器内部对 Registry/Graph 的并发写入由上述锁保护。
* 引擎状态（completed/retries/blocked/waiting）只允许在串行落账点变更。

---

## 7. 验收映射（P7 任务书 A–K → 测试）

| 项 | 验收标准 | 测试（tests/integration/test_p7_integrity.py） |
|----|----------|------------------------------------------------|
| A | Fresh Run 15/15 | `TestAFreshRun` |
| B | 并行执行 + 依赖序保持 + ID 零重复 | `TestBWaveExecution` |
| C | 任意检查点崩溃 | `TestCrashResume::test_crash_at_wave_and_resume_consistent` |
| D | Resume 无重复完成/无丢产物/无丢证据/状态不倒退 | 同上（快照逐项比对） |
| E | Retry 正确收敛 | `TestERetry` |
| F | Rerun 显式新谱系 | `TestFRerun` |
| G | Invalidation 下游 claim 不可用 | `TestGInvalidation` |
| H | 局部重建只跑受影响分支 | `TestHPartialRebuild` |
| I | Supersession 审计保留且不可复活 | `TestISupersession` |
| J | 只有活跃证据进入论文投影 | `TestJPaperProjection` |
| K | 同输入确定性重放 | `TestKReplay` |

回归底线：`pytest tests` 全绿 + `validate.py` 57/57 + `catalog_check` 一致。
