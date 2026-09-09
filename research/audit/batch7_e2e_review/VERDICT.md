# Batch 7 独立复审 VERDICT — Model Construction Loop

- 复审对象：MathModel 仓库 `core/runtime` 可执行建模闭环（P1-VS-001 垂直切片）
- 复审日期：2026-09-09
- 复审方式：**独立、只读**；不参考既往 audit 结论，仅从最终仓库代码与运行实测取证
- Python：`py -3.12`；仓库根：`C:\Users\Lin\Desktop\Programs\MathModel`

---

## E2E VERDICT: MODEL CONSTRUCTION LOOP = **REAL**

闭环 M1 → RUN1 → VALIDATION FAIL → REVISION → M2 → RUN2 → VALIDATION PASS + Replay
经源码逐行追踪与独立运行复现，判定为**真实**：

- 执行由真实 `subprocess` 驱动，status 来自真实退出码；
- FAIL 由真实数值（M1 体板间距 1.925 vs 参考 1.65，违反 0.275 > 容差 1e-6）机械算出；
- supersede 保留 M1 数据、状态机正确，M2 作为新 artifact 注册；
- diagnosis / comparison 全部基于 VR 机械字段，零 LLM；
- Replay 真实重跑并对 outputs 做精确字典比对。

未发现 P0（fake execution / 占位冒充 / 测试假绿）。发现 2 项 P2（图边语义、死代码），不影响真实性结论。

---

## 1. 证据链（逐项：路径 / 函数 / 行号 / 关键代码 / 结论）

### a. M1 的 model_validation 为何 FAIL —— 真实数值判 FAIL，非占位/硬编码

| 项 | 位置 |
|---|---|
| 测试断言 | `tests/integration/test_p1_vs001_e2e.py:125-141`（test_05）：`status=="failed"`、`mathematical_valid is False`、`constraint_violation_max≈0.275`、`C002_body_spacing` 未通过 |
| M1 故意错误来源 | `research/P15/vs001_run/vs001_fixtures.py:183-202`（`_constraints_m1`）、`:231-235`（M1 `ell_body=1.925`，孔心距只减一次 `d_offset`） |
| 验证规格 | `vs001_fixtures.py:423-433` `VALIDATION_SPEC`：`C002_body_spacing` `reference=1.65, tolerance=1e-6, pair_index="1+"` |
| 数值计算 | `core/runtime/execution/validation.py:289-310` `run_numeric_validation` |
| FAIL 判定 | `validation.py:303` `ok = viol <= tol`；`:351` `mathematical_valid = (constraint_violation_max <= constraint_tolerance and domain_ok)`；`:359` `status = "passed" if (mathematical_valid and empirical_valid) else "failed"` |
| 节点 FAIL | `core/runtime/execution/handlers.py:762-775` `do_model_validation`：单候选 `n_fail>0 and n_pass==0` → `NodeResult(FAIL)` |
| driver 断言 | `research/P15/vs001_run/vs001_driver.py:88-90` 断言 `model_validation` 节点必为 `fail` |

**关键计算摘录**（validation.py:295-304）：
```python
for t, ds in pair_distances.items():
    for i, d in enumerate(ds):
        if pi == "1+" and i < 1: continue
        ...
        viol = max(viol, abs(float(d) - ref))
ok = viol <= tol
```

**数值证据（独立运行实测，见第 2 节）**：
- M1 执行输出体板间距实测 `1.924999999999999`（=1.925），参考 `1.65`，
  `viol = |1.925 − 1.65| = 0.275`，容差 `1e-6`，`0.275 > 1e-6` → check FAIL。
- `constraint_violation_max = 0.275`，`mathematical_valid = False`，VR `status = failed`。

> 结论：FAIL 由 subprocess 真实输出经容差比较得出，阈值 1e-6、实际违反 0.275 均为实数。
> M1 错误是数学/系数层面（ell_body 1.925），不是语法错误，也不是硬编码 `FAIL`。

---

### b. ExecutionResult.status 只来自真实 subprocess

| 项 | 位置 |
|---|---|
| subprocess 调用 | `core/runtime/execution/adapters.py:198-202` `LocalPythonAdapter.execute` → `subprocess.run([self.python, str(script)], ...)` |
| status 唯一来源 | `adapters.py:206` `status = "success" if proc.returncode == 0 else "failed"` |
| 超时 | `adapters.py:234-245` `TimeoutExpired` → `status="timeout"` |
| 框架异常 | `adapters.py:246-256` 其它异常 → `status="invalid"` |
| provenance | `adapters.py:231` `provenance={"adapter": self.name, "python": self.python}` |
| handler 存储 | `core/runtime/execution/handlers.py:615` `xr = adapter.execute(xplan)`；`:621-627` 原样 `xr.to_dict()` 注册，**不改写 status** |
| handler 异常分支 | `handlers.py:616-620` 仅在 adapter 自身抛错时构造 `status="invalid"`（失败，非伪造 success） |
| 节点层只读 status | `handlers.py:737-748` `do_model_execution` 读 `xdata["status"]` 决定节点 PASS/FAIL，从不回填执行结果 status |

**关键摘录**（adapters.py:198-206）：
```python
proc = subprocess.run([self.python, str(script)], capture_output=True, ...)
...
status = "success" if proc.returncode == 0 else "failed"
```

> 结论：`status` 字段由 `subprocess` 真实返回码派生，handler 无任何路径把失败伪造成 success。
> 测试 `test_03` 同时断言 `returncode==0`、`"local_python" in provenance`（test:97-99）。

---

### c. registry.supersede 后 M1 状态与数据

| 项 | 位置 |
|---|---|
| 调用点 | `vs001_driver.py:153` `reg.supersede(mir1_id, reason=..., replacement=mir2, by=...)` |
| supersede 实现 | `core/runtime/artifacts/registry.py:346-357` |
| 数据保留 | 同函数仅 `art = self.get(artifact_id)` 后改状态/失效标记，**无删除 data** |
| 状态 → superseded | `registry.py:352` `art.transition("superseded", ...)` |
| invalidated_by | `registry.py:353-355` `art.invalidation = {"status":"superseded", ..., "invalidated_by": replacement, ...}` |
| transition 不清 data | `core/runtime/artifacts/artifact.py:156-166`：仅 `lifecycle_history.append` + `self.status = target`，从不触碰 `self.data` |
| M2 作为新版本注册 | engine 在 `handlers.py:240-247` `registry.create("model_ir", ...)` 新建 MIR002（非覆盖 MIR001） |

**关键摘录**（registry.py:351-355）：
```python
art = self.get(artifact_id)
art.transition("superseded", by=by, reason=reason)
if replacement:
    art.invalidation = {"status": "superseded", "reason": reason,
                        "invalidated_by": replacement, "at": utcnow()}
```

> 结论：(i) M1 数据保留（`Artifact.transition` 不删 data；测试 test_06:155-156 断言
> `get(mir1).data == m1_snapshot`）；(ii) M1 `status=="superseded"` 且
> `invalidation.invalidated_by==MIR002`（test:157-158）；(iii) MIR002 作为独立新 artifact 注册，
> 谱系边 `MIR002 -revision_of-> MIR001`（test:161）。

---

### d. diagnosis artifact 基于机械归因，非 LLM/硬编码结论

| 项 | 位置 |
|---|---|
| 入口 | `core/runtime/modeling/diagnosis.py:74-103` `diagnose_failure` |
| 前置护栏 | `:80-82` 仅当 VR `status=="failed"` 才诊断，否则 raise |
| 机械归因 | `:36-71` `_classify_failure`：遍历 `data["checks"]` 取 `not passed` 项（`:48-64`），按 `kind` 分类；`:65-70` 读 `constraint_violation_max > 1e-9` |
| root_cause 拼装 | `:86-93` 仅由 `execution_valid` / `constraint_violation_max` / `mathematical_valid` 三个机械字段拼接 |
| 注册与边 | `vs001_driver.py:145-151` 建 `diagnosis` artifact + `(MIR1, diagnosed_by, DIAG)` 边 |

**关键摘录**（diagnosis.py:65-70）：
```python
cvm = data.get("constraint_violation_max")
if isinstance(cvm, (int, float)) and cvm > 1e-9:
    components.append("constraint_violation")
    fixes.append(f"约束违反最大值 {cvm:.6g}：校对约束参考值/系数 ...")
```

> 结论：诊断完全由 failed checks / execution status / constraint_violation_max 机械推导，
> 模块 docstring（:2-8）与代码均无 LLM 调用；建议文本只引用具体 check 名与数值，不编造新数值。

---

### e. comparison 的 accept 决策基于 VR 机械证据

| 项 | 位置 |
|---|---|
| 入口 | `core/runtime/modeling/comparison.py:66-115` `compare_models` |
| 反查 VR | `:31-50` `_resolve_vr_for_model`：沿 `model_ir→implemented_by→code→executed_by→execution→verified_by→VR` 谱系解析 |
| 机械指标提取 | `:53-63` `_metrics`：`valid = status=="passed"`、`checks_passed`、`constraint_violation_max`、`robustness` |
| accept/reject | `:89-106`：`m2.valid and not m1.valid → accept`；`m1.valid and not m2.valid → reject`；均有效则按 `checks_passed` 计数比较；均无效 → reject |
| 落决策 artifact | `vs001_driver.py:157-177`：`revision_acceptance` decision，`chosen=better_model`，`(dec, selects, M2)` 边 |

**关键摘录**（comparison.py:89-91）：
```python
if m2.get("valid") and not m1.get("valid"):
    better, rec = mir2_id, "accept"
    reason = f"{mir2_id} 通过验证（M1 failed）"
```

> 结论：accept 决策纯由 VR 的 `passed/failed` 布尔与通过检查数、约束违反量、robustness
> 等机械字段比较得出，无主观判断。证据缺失时显式返回 `INCONCLUSIVE/pending`（`:70-78`），不硬判。

---

### f. Replay 真实重跑并比对 outputs

| 项 | 位置 |
|---|---|
| 实现 | `core/runtime/execution/replay.py:167-257` `replay_execution`（`core/tools/replay.py` 仅为 CLI 壳） |
| 取原 code/inputs | `:188` `code = ... data.get("code")`；`:202` `inputs = ... data.get("inputs")` |
| 重建执行环境 | `:210-211` 写 `input.json`（对齐 fixture 的 `__main__` 读 input.json 契约） |
| **真实重跑** | `:199-205` 建 `ExecutionPlan`；`:214` `rep = adapter.execute(plan)`（LocalPythonAdapter 真 subprocess） |
| status 比对 | `:221-224` |
| code_hash 比对 | `:225-228` |
| environment_hash 比对 | `:229-235` |
| **outputs 精确比对** | `:236-241` `if rep.outputs != orig_out: deviation.append(...)`；`:249-251` `outputs_match = 双 success 且 rep.outputs == recorded` |

**关键摘录**（replay.py:214, 238-241）：
```python
rep = adapter.execute(plan)
...
if rep.outputs != orig_out:
    deviation.append({"dim": "outputs", ...,
                      "why": "输出不一致（非确定性/随机种子/浮点/外部数据）"})
```

> 结论：Replay 用 artifact 中存储的 code 与 inputs 通过同一 adapter **真实重新执行**，
> 并对 status / code_hash / environment_hash / outputs 做逐项偏差比对（outputs 为整字典相等）。
> 不是回放日志。独立运行实测 RUN1/RUN2 `ok=true, outputs_match=true`。

---

## 2. Demo 独立复现结果

- **命令**：`py -3.12 research/P15/vs001_run/run_vs001_demo.py`
- **退出码**：0
- **输出摘要**：

| 指标 | M1 (EXEC001) | M2 (EXEC002) |
|---|---|---|
| exit_code | 0 | 0 |
| status | success | success |
| 体板间距实测 | **1.924999999999999** | **1.6499999999999997** |
| head_speed@60 | 0.99937 | 0.99937 |
| VR verdict | **failed** | **passed** |
| mathematical_valid | false | true |
| empirical_valid | — | true |
| constraint_violation_max | **0.275** | 0.0 |
| robustness | — | 1.0 |
| Replay run | ok=true / outputs_match=true | ok=true / outputs_match=true |

**复现结论**：独立复现 M1 FAIL（1.925 vs 1.65，违反 0.275）→ REVISION → M2 PASS（1.65，违反 0.0）闭环成功；
谱系边完整（instantiates / implemented_by / executed_by / produces / verified_by / revision_of / diagnosed_by / supersedes / selects）。

---

## 3. 测试运行确认

- **命令**：`py -3.12 -m pytest tests/integration/test_p1_vs001_e2e.py -q`
- **实测结果**：`8 passed in 3.65s`（本轮独立执行，退出码 0）
- 与用户提供的基线（8 passed in 7.52s）一致；耗时差异仅来自机器负载/缓存。

---

## 4. 发现的问题

### P0（fake execution / 占位冒充 / 测试假绿）
**无。** 执行确为 subprocess 真跑，数值来自真实 stdout 解析，FAIL/PASS 由容差比较机械决定。

### P1（真实性存疑）
**无。** 六项证据链均有代码行号与数值支撑，未发现"看似真实实则写死"的路径。

### P2（代码质量 / 语义瑕疵，不影响真实性）

1. **【P2-1】`supersedes` 边方向自相矛盾，且被测试固化**
   - `core/runtime/execution/handlers.py:253` 在登记修订 M2 时写：
     `self.graph.add_relation(rev_of, "supersedes", art.artifact_id)`
     即 `(MIR001, supersedes, MIR002)`——读作"旧模型取代新模型"，方向语义相反。
   - 正确方向由 `vs001_driver.py:155` 后补：`(MIR002, supersedes, MIR001)`。
   - 最终 evidence_graph 同时存在两条反向 `supersedes` 边；且
     `tests/integration/test_p1_vs001_e2e.py:234` 显式断言了反向边 `("MIR001","supersedes","MIR002")`，
     把瑕疵固化为期望。
   - 影响：不影响权威状态机（`registry.supersede` 正确把 MIR001 置 `superseded`、
     `invalidated_by=MIR002`），也不影响数值真实性；但作为审计谱系图，语义自相矛盾，
     下游按方向遍历"谁取代了谁"会得到相反结论。建议统一为"新→旧"单一方向。

2. **【P2-2】`run_numeric_validation` 内有不可达的重复分支**
   - `core/runtime/execution/validation.py:246-261` 与 `:263-283` 是两段几乎相同的
     `if spec.get("checks"):` 处理；第一段命中即 `return`，第二段永不执行。
   - 影响：纯死代码/重复，VS-001 走的是其后的 2024_A 硬编码数值分支，不影响本闭环正确性。

> 备注（非问题）：M1/M2 的求解器代码本体相同，差异在 MODEL_IR 的 `ell_body`
> 参数（1.925→1.65）与 provenance 注释（fixtures.py:374-377），这是 fixture
> 设计意图（修订发生在建模层而非代码层），code_hash 因注释不同而不同，符合 fixture 声明，不构成造假。

---

## 5. 复审者声明

本复审为**独立只读验证**：
- 未修改任何源代码、测试或配置；未执行任何 git 命令；
- 仅新增本报告文件 `research/audit/batch7_e2e_review/VERDICT.md` 及其目录；
- 全部结论均附文件路径、函数名、行号与关键代码摘录，并以独立运行 demo 与 pytest 的实测输出佐证；
- 未为"好看"降低严重度：真实性证据充分故判 REAL，同时如实记录 P2-1/P2-2。
