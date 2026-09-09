# P1-VS-001 — Executable Model Construction Loop（Vertical Slice First）完成报告

- 日期：2026-09-09
- 选题：**2024_A（板凳龙闹元宵）Q1** — 正向运动学仿真
- 代码实现路径：本仓库 HEAD 链（C1/C5 来自历史提交，C6–C10 本次新增）
- 闭环：`M1 → RUN1 → VALIDATION FAIL → REVISION → M2 → RUN2 → VALIDATION PASS`

---

## 1. 7 条验收证据（逐条）

| # | 验收 | 证据 | 状态 |
|---|---|---|---|
| 1 | Problem 稳定 Artifact ID | `P001`（type=problem, status=active），见 `research/P15/vs001_run/project/state/registry.json` | ✅ |
| 2 | M1 是真实 MODEL_IR（三层） | `MIR001` data.model_id=`M2024A-Q1-v1`，`ModelIR.layers()` = L1_semantic(4) / L2_mathematical(5) / L3_computational(3)；E001 constitutive ∈ L2，S001 simulation ∈ L3 | ✅ |
| 3 | Code 由 M1 生成并实际执行 | `CODE001`（含固定 ABI `def solve(inputs)` + code_hash）→ `EXEC001` 经 `LocalPythonAdapter` 真 subprocess（`input.json → run_model.py → output.json`）；边 `MIR001 -implemented_by-> CODE001 -executed_by-> EXEC001` | ✅ |
| 4 | ExecutionResult 含真实数值 | `EXEC001.data.outputs`：`pair_distances["0"][1]=1.925`（实测体板间距）、`head_speeds["60"]=0.9994`、224 把手×6 时刻；`status=success` 来自真实 returncode=0；`R001.data.value` 同源 | ✅ |
| 5 | Validation 基于真实数值判 FAIL | `VR001`：`mathematical_valid=False`，`constraint_violation_max=0.275`（声明 1.65 vs 实测 1.925），`status=failed`；checks 含 `C002_body_spacing passed=False`。FAIL 独立于 evidence_gate（纯数值判定） | ✅ |
| 6 | M2 revision lineage，不覆盖 M1 | `MIR002`（model_id=M2024A-Q1-v2）为新 artifact；边 `MIR002 -revision_of-> MIR001` + `MIR001 -supersedes-> MIR002`；MIR001 数据/状态保持不变 | ✅ |
| 7 | Replay 复现 RUN1/RUN2 | `replay_execution()` 重放 EXEC001/EXEC002：`ok=True`、`outputs_match=True`、`deviation=[]`（数值逐位一致） | ✅ |

### 1.1 闭环关键数值（来自真实执行，非占位）

| 阶段 | 实测体板间距 d₁ (m) | 声明 C002 (m) | constraint_violation_max | 龙头速度@60s (m/s) | 判定 |
|---|---|---|---|---|---|
| M1 RUN1 (EXEC001) | 1.925 | 1.65 | **0.275** | 0.9994 | `VR001 failed` |
| M2 RUN2 (EXEC002) | 1.650 | 1.65 | **0.000** | 0.9994 | `VR002 passed` |

M1 故意错误（数学/数值层面，非语法）：C002 约束系数与 PARM006 参数把体板孔心距写成
`L_body − d_offset = 1.925`（正确应为 `L_body − 2·d_offset = 1.65`）；M2 修正后数值验证全绿。

### 1.2 证据图谱边（project/state/evidence_graph.json，17 条）

```
P001  ←based_on- D001
M001  ←instantiates- MIR001 / MIR002
CODE001 ←implemented_by- MIR001      CODE002 ←implemented_by- MIR002
EXEC001 ←executed_by- CODE001        EXEC002 ←executed_by- CODE002
R001   ←produces- EXEC001            R002   ←produces- EXEC002
VR001  ←verified_by- EXEC001         VR002  ←verified_by- EXEC002
MIR002 -revision_of-> MIR001         MIR001 -supersedes-> MIR002
（另有 model_selection/assumption 等常规边）
```

---

## 2. 实现修改清单（按 commit）

### 历史已有（本任务未改动）
| commit | 内容 |
|---|---|
| `1534fa5` | C1：MODEL_IR 升入 core（schema 迁移 `core/schemas/v3/model/model_ir.schema.json`、`core/runtime/modeling/model_ir.py`、ids `MIR`、`tests/runtime/test_model_ir.py`） |
| `5f6c554` | C5 集成：MODEL_IR contract 统一到 core single source（schema vocabulary-complete；handlers `construct_model_ir`/`instantiates` 边、`external_model_irs` 注入入口；evidence_graph 关系扩展；`tests/runtime/test_model_ir.py` 黄金样本） |

### 本次新增（均为 `feat(p1-vs001): ...`，不 push）
| commit | 改动文件 | 内容 |
|---|---|---|
| `42de1cc` | `core/runtime/execution/handlers.py` | C6 `generate_code`（外部代码注入 → ABI 校验 → code Artifact + code_hash + `implemented_by` 边）+ C7 `execute_code`（input.json 落盘 → LocalPythonAdapter 真 subprocess → execution_result + result，status 只来自退出码，`executed_by`/`produces` 边）+ C8 `validate_execution`（数值验证 → VR 四字段 + `verified_by` 边）+ `do_code_generation`/`do_model_execution`/`do_model_validation` DAG 节点；do_experiment 幂等分支防御 |
| `bec1948` | `core/runtime/graph/evidence_graph.py` | C7：`produces` 关系 from 集合扩为 `{experiment, execution_result}`（EXEC→R 正向边） |
| `90410f9` | `core/runtime/execution/validation.py` | C8：`run_numeric_validation()`（constraint_violation_max / objective_sanity / variable_domain_violation / robustness；execution 非 success → invalid 铁律） |
| `4434dcf` | `catalog/v3.yaml`、`core/workflows/stages/modeling.yaml`、`core/workflows/stages/experiment.yaml`、`tests/unit/test_workflow_compose.py`、`tests/integration/test_red_team.py` | C6-C8 DAG 集成：modeling 尾链 `assumption_check → code_generation → model_execution → model_validation`，experiment_design 依赖改接 model_validation；测试同步（compose 尾链断言、red_team CUTS 插入新节点） |
| `4b80dc0` | `core/runtime/execution/replay.py`、`core/runtime/execution/handlers.py` | C10：replay 重建固定 ABI 环境（workdir + input.json 落盘）；generate_code 幂等分支补 implemented_by 边 |
| `7fabbba` | `tests/integration/test_p1_vs001_e2e.py` + `research/P15/vs001_run/`（fixtures/driver/demo/落盘产物） | C10：2024_A 垂直切片 e2e（8 tests，7 条验收逐条断言）+ 演示运行产物 |

> 已跳过（非验收必需，任务允许裁剪）：C2（Candidate 持久化）、C3（Decision+selects 边）、C9（evidence_gate 数值真实性——本实现以独立数值验证替代，不依赖 evidence_gate）。

---

## 3. Replay 复现说明

```powershell
cd C:\Users\Lin\Desktop\Programs\MathModel
py -3.12 research/P15/vs001_run/run_vs001_demo.py      # 重跑完整闭环（覆盖 project/ + 两份报告）
py -3.12 -m pytest tests/integration/test_p1_vs001_e2e.py -q   # 8 passed（含 replay 断言）
```

独立重放（仅凭落盘 registry，不重跑闭环）：

```powershell
py -3.12 -c "import sys; sys.path.insert(0,'core'); sys.path.insert(0,'research/P15/vs001_run');
from vs001_driver import replay_report
print(replay_report('research/P15/vs001_run/project','EXEC001')['ok'])
print(replay_report('research/P15/vs001_run/project','EXEC002')['outputs_match'])"
# → True / True（零偏差）
```

`replay_report.json`（已提交）：RUN1/RUN2 均 `ok=True, outputs_match=True, deviation=[]`，
即凭 `EXEC.data.code + inputs` 重建 subprocess 得到与原始逐位一致的输出。

---

## 4. 设计要点与约束落实

- **LLM-free**：M1/M2 MODEL_IR（JSON）与 C1/C2（Python 代码字符串）由外部 Model Constructor
  在 `research/P15/vs001_run/vs001_fixtures.py` 手写；core runtime 只登记/校验/执行/保真/
  验证/谱系/replay。
- **status 真实性**：`EXEC.status` 只来自 `LocalPythonAdapter` 的真实 `returncode`（成功=0），
  无任何硬编码状态；M1 的 FAIL 来自真实数值（约束违反 0.275），非伪造。
- **M2 不覆盖 M1**：`MIR002` 为新 artifact，`revision_of`/`supersedes` 双向边，MIR001 原样保留。
- **禁改冻结物**：K002 frozen_specs / rubric、`research/P15/benchmark/problem_cards/2024_A/`
  冻结题面、`.gitignore`/`.git` 均未触碰。
- **DAG 一致性**：`catalog_check.py --check` 通过（v3 双视图三方一致）。
- **故意失败设计**：M1 错误是约束系数（C002）+ 参数值（PARM006 ell_body=1.925）层面的
  数学/数值错误，非语法错误（语法错误会在 L0 ABI 校验或子进程 traceback 处暴露，不算
  "基于真实数值判 FAIL"）。

---

## 5. 全量验证数字（本报告提交时）

| 检查 | 结果 |
|---|---|
| `py -3.12 -m pytest tests -q` | **890 passed, 4 skipped**（94.5s） |
| `py -3.12 core/tools/catalog_check.py --check` | **OK**（v3 双视图与 roles/DAG/validators 三方一致） |
| `py -3.12 core/tools/validate.py` | **57 通过, 0 失败, 0 警告** |
| `py -3.12 -m pytest tests/integration/test_p1_vs001_e2e.py -q` | **8 passed** |

基线对照：任务开始时 HEAD=5f6c554 未跑全量；上一外部提交 53037c2 记录 882/4/57-0；
本实现全量 890/4/57-0（新增 8 个 e2e 用例，无回归）。
