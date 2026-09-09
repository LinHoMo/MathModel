# P1-VS-001 — Executable Model Construction Loop 实验报告

- 仓库：`C:\Users\Lin\Desktop\Programs\MathModel`
- 实验日期：2026-09-09
- 目标：第一次让 LinHoMo 真正完成「模型构造—运行—验证—失败—修正—再运行」闭环
- 核心哲学：Agent / LLM 只是 Executor（外部 Model Constructor），core 只做登记/执行/校验/谱系，LLM-free

---

## 一、闭环总览

```
Problem (P002: 2019_C 机场出租车)
  │ motivates
  ▼
Question (Q002: M/M/c 排队模型)
  │ solved_by
  ▼
Model M1 (M002) + MODEL_IR v1 (MIR002)  ← 外部 Model Constructor 产出
  │ implemented_by
  ▼
Code C1 (CODE002)
  │ derived_from (EXEC ← CODE)
  ▼
Execution R1 (EXEC002)  status=success  真实数值: rho=1.5, Wq=-0.09, Lq=-5.4
  │ verified_by
  ▼
Validation V1 (VR002)  status=FAILED  (4/5 checks failed)
  │
  ▼
RevisionRequest (D001)
  │
  ▼
Model M2 (M003) + MODEL_IR v2 (MIR003)  ← 外部 Model Constructor 修正
  │ revision_of / supersedes → MIR002
  │ implemented_by
  ▼
Code C2 (CODE003)
  │
  ▼
Execution R2 (EXEC003)  status=success  真实数值: rho=0.75, Wq=0.032, Lq=1.93
  │ verified_by
  ▼
Validation V2 (VR003)  status=PASSED  (6/6 checks passed)
```

**M1 → RUN1 → VALIDATION FAIL → REVISION → M2 → RUN2 → VALIDATION PASS** 完整跑通。

---

## 二、M0 — Executable Model Contract（手写 LP 验证最小契约）

| 项 | 值 |
|---|---|
| Problem | P001（工厂两产品生产计划 LP） |
| MODEL_IR | MIR001（三层：semantic/mathematical/computational） |
| Model | M001 |
| Code | CODE001（纯 Python 顶点枚举法，`def solve(inputs=None)->dict`） |
| Execution | EXEC001，status=success |
| Validation | VR001，status=passed（6/6 checks） |
| 真实数值 | objective=160.0, x_A=20.0, x_B=20.0, constraint_violation_max=0.0 |

M0 验证了 runtime 最小契约：Problem → MODEL_IR → Code → Execution → Validation 全链路可用，所有数值来自真实 subprocess 执行。

---

## 三、M1 — One Real Problem（2019_C Q1，v1 故意缺陷）

### 3.1 问题选择

2019_C 机场出租车 Q1：建立 M/M/c 排队模型分析平均等待时间与队列长度。
选择理由：可数值执行（解析公式）、可构造 FAIL（参数错误导致不稳定）、模型不复杂。

### 3.2 MODEL_IR v1（三层结构）

- **L1 Semantic**：entities=[passenger, taxi, queue, airport]；variables=[avg_waiting_time, avg_queue_length, server_utilization, probability_wait]；parameters=[arrival_rate=60, num_servers=2, service_rate=20]
- **L2 Mathematical**：objective=compute(Wq,Lq,rho,Pw)；constraints=[stability: lambda/(c*mu)<1, utilization_range, nonneg_wait]
- **L3 Computational**：solver.family=queueing_theory, backend=pure_python_math, method=mmc_analytical；execution.language=python, abi=def solve(inputs=None)->dict

**故意缺陷**：service_rate(mu)=20 过小 → rho = 60/(2*20) = 1.5 ≥ 1，系统不稳定。

### 3.3 执行结果（EXEC002，真实数值）

| 字段 | 值 |
|---|---|
| status | success（Python 没崩，但模型错了） |
| avg_waiting_time | -0.09（负值，物理无意义） |
| avg_queue_length | -5.4（负值） |
| server_utilization | 1.5（>1，违反稳定条件） |
| probability_wait | 1.8（>1，概率超范围） |
| constraint_violation_max | 5.4 |
| solver_status | unstable |

### 3.4 Validation（VR002，基于真实数值判 FAIL）

| Check | 结果 | 依据 |
|---|---|---|
| wait_time_exists | PASS | 字段存在（=-0.09） |
| wait_time_nonnegative | **FAIL** | avg_waiting_time=-0.09 < 0 |
| utilization_le_1 | **FAIL** | server_utilization=1.5 > 1.0 |
| queue_length_nonnegative | **FAIL** | avg_queue_length=-5.4 < 0 |
| stability_constraint | **FAIL** | constraint_violation_max=5.4 > 1e-6 |

**VR002 status = failed**（4/5 checks failed）。这不是文本判断，是基于执行输出的真实数值检查。

---

## 四、M2 — Model Revision（v1 FAIL → v2 PASS）

### 4.1 RevisionRequest（D001）

```json
{
  "revision_of": "MIR002",
  "trigger": "validation_failed",
  "failed_checks": ["wait_time_nonnegative", "utilization_le_1",
                    "queue_length_nonnegative", "stability_constraint"],
  "diagnosis": "M1 v1 的服务率参数错误（mu 过小），导致系统不稳定 (rho >= 1)，排队论公式产生负值或无穷大等待时间。",
  "corrective_action": "修正服务率 mu 为正确值，确保 rho = lambda/(c*mu) < 1，重新计算 M/M/c 排队指标。"
}
```

### 4.2 MODEL_IR v2（修正版，MIR003）

与 v1 结构完全相同，唯一修正：**service_rate = 40**（mu=40 → rho = 60/(2*40) = 0.75 < 1）。

### 4.3 Revision Lineage（谱系边）

| 边 | 方向 |
|---|---|
| revision_of | MIR003 → MIR002 |
| supersedes | MIR003 → MIR002 |
| registry supersede | MIR002 status=superseded, invalidated_by=MIR003 |
| registry supersede | M002 status=superseded, invalidated_by=M003 |

**禁止 overwrite model**：MIR002 保留为 superseded 终态，MIR003 是新 artifact，谱系可审计。

### 4.4 执行结果（EXEC003，真实数值）

| 字段 | 值 |
|---|---|
| status | success |
| avg_waiting_time | 0.03214286（小时 ≈ 1.93 分钟） |
| avg_queue_length | 1.92857143 |
| server_utilization | 0.75 |
| probability_wait | 0.64285714 |
| constraint_violation_max | 0.0 |
| solver_status | optimal |

### 4.5 Validation（VR003，PASS）

| Check | 结果 |
|---|---|
| wait_time_exists | PASS |
| wait_time_nonnegative | PASS（0.032 ≥ 0） |
| utilization_le_1 | PASS（0.75 ≤ 1.0） |
| queue_length_nonnegative | PASS（1.93 ≥ 0） |
| stability_constraint | PASS（0.0 ≤ 1e-6） |
| wait_time_finite | PASS（0.032 ≤ 1e6） |

**VR003 status = passed**（6/6 checks passed）。

---

## 五、Replay 验证

对 RUN1 (EXEC002) 和 RUN2 (EXEC003) 分别执行 `replay_execution()`：

| Execution | recorded_status | replayed_status | outputs_match | ok |
|---|---|---|---|---|
| EXEC002 (RUN1) | success | success | True | True |
| EXEC003 (RUN2) | success | success | True | True |

- 同 code 同 env → outputs 完全一致（确定性执行）
- code_hash / environment_hash 无偏差
- Replay 报告：`replay_report.json`

---

## 六、7 条验收逐条核对

| # | 验收标准 | 状态 | 证据 |
|---|---|---|---|
| 1 | Problem 有稳定 Artifact ID | **PASS** | P002 注册于 registry.json，可 checkpoint 恢复；P001 (M0) 同理 |
| 2 | M1 是真实 MODEL_IR（三层结构） | **PASS** | MIR002 含 semantic(entities/variables/parameters) + mathematical(objective/constraints) + computational(solver/execution)，非 model_family 标签 |
| 3 | Code 由 M1 生成并实际执行 | **PASS** | CODE002 由外部 Model Constructor 产出，M002 -implemented_by-> CODE002，EXEC002 为真实 subprocess 执行（status=success, returncode=0, 真实 outputs） |
| 4 | ExecutionResult 含真实数值输出 | **PASS** | EXEC002.outputs = {avg_waiting_time:-0.09, avg_queue_length:-5.4, server_utilization:1.5, constraint_violation_max:5.4, solver_status:unstable, ...}；含 checks + diagnostics |
| 5 | Validation 能基于真实数值判 FAIL | **PASS** | VR002 status=failed，4 项检查基于 EXEC002 的真实数值失败（非文本判断） |
| 6 | M2 与 M1 存在 revision lineage | **PASS** | MIR003 -revision_of-> MIR002，MIR003 -supersedes-> MIR002；MIR002/M002 status=superseded, invalidated_by=MIR003/M003；未 overwrite |
| 7 | Replay 能从 M1 重现 RUN1/RUN2 | **PASS** | EXEC002 和 EXEC003  replay 均 ok=True, outputs_match=True，偏差报告见 replay_report.json |

**7/7 全部 PASS。**

---

## 七、最小修改清单

### Core 改动（2 处，均有对应测试）

| # | 文件 | 改动 | 原因 | 测试 |
|---|---|---|---|---|
| 1 | `core/runtime/artifacts/ids.py` | 新增 `model_ir` 类型（前缀 MIR），正则加入 MIR | MODEL_IR 需要作为一等 artifact 注册进 Registry，Gap Audit 环节6 指出 runtime 零集成 | `tests/unit/test_p1_vs001_core.py::TestModelIRType`（7 tests） |
| 2 | `core/runtime/graph/evidence_graph.py` | 新增 `revision_of` 和 `supersedes` 两种 relation（model/model_ir → model/model_ir，弱边，不传播），加入 WEAK_RELATIONS 和 _PROPAGATION | Gap Audit 环节10/11 指出无 revision_of/supersedes 边，修订谱系不可审计 | `tests/unit/test_p1_vs001_core.py::TestRevisionRelations`（13 tests） |

### 测试更新（1 处）

| # | 文件 | 改动 | 原因 |
|---|---|---|---|
| 3 | `tests/unit/test_evidence_graph.py` | `test_all_16_relation_types_defined` → `test_all_relation_types_defined`，断言 16→18，新增 revision_of/supersedes 类型断言 | 新增 2 种 relation 类型后的必要更新 |

### 实验产物（非 core，research/P15/experiments/p1-vs001/）

| 文件 | 说明 |
|---|---|
| `p1_vs001_runner.py` | 闭环驱动脚本（M0/M1/M2/Replay），使用 core 现有原语，不修改 core |
| `m0/model_ir.json` + `m0/run_model.py` | M0 手写 LP 三层 MODEL_IR + 自包含代码 |
| `m1/model_ir_v1.json` + `m1/run_model_v1.py` | M1 v1 缺陷版（外部 Model Constructor 产出） |
| `m2/model_ir_v2.json` + `m2/run_model_v2.py` | M2 v2 修正版（外部 Model Constructor 产出） |
| `project/state/registry.json` | 完整 Artifact Registry（20 artifacts） |
| `project/state/evidence_graph.json` | 完整 Evidence Graph（16 relations，graph_version=17） |
| `m0/result.json`, `m1/result.json`, `m2/result.json` | 各阶段结果摘要 |
| `replay_report.json` | Replay 偏差报告 |
| `_inspect.py` | 谱系检查辅助脚本 |

### 明确未做的事（遵守最小修改原则）

- ❌ 未新增 Agent / Skill / 知识库 / 论文模块 / 前端
- ❌ 未在 core 加任何 LLM 调用（MODEL_IR/Code 由外部子代理产出）
- ❌ 未修改 orchestrator.py / session.py / handlers.py / planner.py
- ❌ 未修改 evaluator / 测试阈值 / 题面
- ❌ 未修改 core/legacy/ 下任何文件
- ❌ 未修改 .gitignore / .git
- ❌ 未修改 V3 DAG / catalog.yaml

---

## 八、Evidence Graph 完整谱系（16 条边）

```
P001 -motivates-> Q001
Q001 -solved_by-> M001
M001 -implemented_by-> CODE001
EXEC001 -derived_from-> CODE001
EXEC001 -verified_by-> VR001

P002 -motivates-> Q002
Q002 -solved_by-> M002
M002 -implemented_by-> CODE002
EXEC002 -derived_from-> CODE002
EXEC002 -verified_by-> VR002

Q002 -solved_by-> M003
MIR003 -revision_of-> MIR002
MIR003 -supersedes-> MIR002
M003 -implemented_by-> CODE003
EXEC003 -derived_from-> CODE003
EXEC003 -verified_by-> VR003
```

---

## 九、遗留缺口（后续 Milestone）

1. **M3 Candidate Arena**：当前只有单一模型 v1→v2，未实现多候选竞争（Model A/B/C → Evidence → Selection）
2. **M4 Knowledge-guided Construction**：未接入 BZD knowledge 引导候选生成
3. **orchestrator --execute 集成**：闭环由独立 runner 驱动，未接入 V3 DAG 主路径（orchestrator 仍不传 adapter）
4. **execution_result schema 门禁**：registry.create("execution_result") 仍无 JSON Schema 校验
5. **L3/L4 Validation**：当前 Validation 仅 L0（字段存在）+ L1（数值范围），未实现约束残差/敏感性分析
6. **自动 Revision**：RevisionRequest 由 runner 构造，未实现 LLM 自动修正（当前设计是外部 Model Constructor 接手）
7. **K002**：Runtime 成熟后才可作为 capability experiment，当前不具备测量条件

---

## 十、结论

P1-VS-001 第一次让 LinHoMo 完成了真实的「模型构造—运行—验证—失败—修正—再运行」闭环。

- M1 (MIR002, mu=20, rho=1.5) → 真实执行 → 真实数值 → Validation **FAIL**（4 项数值检查失败）
- RevisionRequest → M2 (MIR003, mu=40, rho=0.75) → 真实执行 → 真实数值 → Validation **PASS**（6/6）
- revision_of / supersedes 谱系边写入 Evidence Graph，MIR002 保留为 superseded 终态
- Replay 从 EXEC002/EXEC003 重现 RUN1/RUN2，outputs 完全一致

这证明了 Artifact Registry + Evidence Graph + Runtime Contract + Replay 这套架构**第一次被一个真实数学模型踩起来了**。项目性质从「建模基础设施」变为「可执行模型运行时」。
