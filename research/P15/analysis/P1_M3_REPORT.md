# P1-M3 — Candidate Competition（候选竞技场 + Evidence-based Selection）完成报告

- 日期：2026-09-09
- 选题：**2024_A（板凳龙闹元宵）Q1** — 正向运动学仿真（复用 VS-001 的 M1/M2 双候选）
- 前置：P1-VS-001（可执行模型闭环，本报告为直接下一块）
- 闭环：候选 A(M1, 约束系数错误) + 候选 B(M2, 修正) → 各自执行/验证 → VR 机械选型 → **chosen=MIR002**

---

## 1. 7 条验收证据（逐条）

| # | 验收 | 证据 | 状态 |
|---|---|---|---|
| ① | ≥2 候选真 subprocess 执行 + 数值验证 | `MIR001/MIR002` → `CODE001/CODE002` → `EXEC001/EXEC002`（returncode=0, status=success, 真实 outputs）→ `VR001/VR002`；独立链边齐全，互不覆盖 | ✅ |
| ② | decision 含 alternatives/criteria/evidence_ids/chosen，criteria 机械可算，chosen 与证据排序一致 | `D002`：alternatives=[MIR001(cv=0.275), MIR002(cv=0.0)]、criteria=5 项机械指标、evidence_ids=[VR001,VR002]、chosen=MIR002、confidence=0.95；ranked=[MIR002, MIR001]（约束违反最小者当选） | ✅ |
| ③ | decision -selects-> model 边，理由可溯源到 EXEC/VR 数值 | 边 `D002 -selects-> M001`（首次真正写入）；reasoning=`chosen=MIR002 because VR002.mathematical_valid=True; MIR001(VR001.constraint_violation_max=0.275) worse than VR002.constraint_violation_max=0.0)` | ✅ |
| ④ | 新增测试 + 全量 pytest 不回归（≥890）、catalog OK、validate 57/0 | pytest **897 passed / 4 skipped**（较 VS-001 890 基线 +7，零回归）；catalog_check OK；validate 57-0 | ✅ |
| ⑤ | LLM-free：候选 MODEL_IR/Code 外部注入 | `research/P15/m3_run/m3_fixtures.py` 手写 CANDIDATES（复用 VS-001 M1/M2 + C1/C2）；core 只登记/校验/执行/验证/选型/谱系；`provenance.adapter=local_python` | ✅ |
| ⑥ | 禁越界 | 仅改 core runtime（handlers/roles）+ 工作流 DAG + 测试同步 + M3 fixtures/driver/demo；未新增 Agent/Skill/知识库/论文模块/schema；K002/frozen_specs/preregistration 全部未触碰 | ✅ |
| ⑦ | 按序 commit（feat(p1-m3):）+ 报告，不 push | 见 §3 commit 列表；本报告 + `research/P15/m3_run/` 落盘 | ✅ |

### 1.1 闭环关键数值（真实执行）

| 候选 | MIR | EXEC | 实测体板间距 (m) | 声明 C002 (m) | cv_max | VR 判定 | 排序 |
|---|---|---|---|---|---|---|---|
| A（M1 故意错误） | MIR001 | EXEC001 (rc=0) | 1.925 | 1.65 | **0.275** | VR001 failed (math_valid=False) | 2nd |
| B（M2 修正） | MIR002 | EXEC002 (rc=0) | 1.650 | 1.65 | **0.000** | VR002 passed | **1st → chosen** |

龙头速度@60s 两者一致 0.9994（objective_sane=True）；VR001 的 FAIL 纯来自约束违反
（variable_domain_violation=0，execution_valid=True），非伪造。

### 1.2 证据图谱边（m3_run/project/state/evidence_graph.json）

```
P001  ←based_on- D001(literature)
M001  ←instantiates- MIR001 / MIR002
CODE001 ←implemented_by- MIR001      CODE002 ←implemented_by- MIR002
EXEC001 ←executed_by- CODE001        EXEC002 ←executed_by- CODE002
R001   ←produces- EXEC001            R002   ←produces- EXEC002
VR001  ←verified_by- EXEC001         VR002  ←verified_by- EXEC002
D002   -selects-> M001               （D002.evidence_ids=[VR001,VR002]）
```

---

## 2. 实现修改清单（按 commit）

| commit | 改动文件 | 内容 |
|---|---|---|
| `ee11065` | `core/runtime/execution/handlers.py` | M3-1 多候选链：`_external_candidates`/`construct_candidate_mirs`/`_register_mir` 重构（单候选与多候选统一）；`generate_code→list` + `_register_code`（候选按 model_id 匹配 code）；`execute_code→list`（逐 code 执行 + EXEC 幂等复用）；`validate_execution→list`（逐 EXEC 验证 + VR 幂等复用）；`do_model_validation` 判定改为"无存活候选才 FAIL"（VS-001 单候选语义保持）；M3-2：`do_model_selection` 候选模式（容器 M001，消除 recs[0] 假选型）、新增 `do_model_selection_decision`（VR 机械排序 + decision 全字段 + `selects` 边 + DecisionLog 审计镜像） |
| `28cf548` | `core/workflows/stages/modeling.yaml`、`experiment.yaml`、`catalog/v3.yaml`、`core/roles/modeler.yaml` | DAG：modeling 尾链 `model_validation → model_selection_decision`，experiment_design 依赖改接；v3 节点 +1（20）；modeler executes +1 |
| `939bf73` | `tests/unit/test_workflow_compose.py`、`tests/integration/test_red_team.py`、`tests/unit/test_openai_manifest.py`、`tests/integration/test_workflow_execution.py` | DAG 同步：compose 尾链断言、red_team CUTS/resume 步进 +1 节点、v3.nodes 19→20；回滚断言改为循环不变量（max_steps 截断奇偶与 DAG 节点数相关） |
| `018f906` | `tests/integration/test_p1_m3_competition.py`（新增）、`research/P15/m3_run/`（m3_fixtures/m3_driver/run_m3_demo + project 落盘） | 7 条验收逐条断言（7 tests）+ 2024_A 双候选演示落盘 |
| `1218e3a` | `research/P15/analysis/P1_M3_REPORT.md` | 本报告 |

> 偏差记录：任务书"重写 do_model_selection"按 DAG 语义落地为两段——
> (a) `do_model_selection` 候选模式只登记容器 model（不假装选型，消除 recs[0] 硬编码）；
> (b) 新增 `model_selection_decision` 节点（紧随 model_validation）执行 evidence-based 选型，
> 因为 VR 证据在 DAG 中只存在于 model_validation 之后。无证据时如实 `UNSELECTED`
> （item 4）在 (b) 中实现。`selects` 边目标为模型容器 M001（relation type 注册为 decision→model）。

---

## 3. Replay 复现说明

```powershell
cd C:\Users\Lin\Desktop\Programs\MathModel
py -3.12 research/P15/m3_run/run_m3_demo.py                 # 重跑双候选闭环（自清理 project/）
py -3.12 -m pytest tests/integration/test_p1_m3_competition.py -q   # 7 passed（含 replay 断言）
```

独立重放（仅凭落盘 registry，不重跑闭环）：

```powershell
py -3.12 -c "import sys; sys.path.insert(0,'core'); sys.path.insert(0,'research/P15/m3_run');
from m3_driver import replay_report
print(replay_report('research/P15/m3_run/project','EXEC001')['outputs_match'])
print(replay_report('research/P15/m3_run/project','EXEC002')['ok'])"
# → True / True（零偏差，deviation=[]）
```

`project/replay_report.json`：EXEC001/EXEC002 均 `ok=True, outputs_match=True, deviation=[]`。

---

## 4. 全量验证数字（本报告提交时）

| 检查 | 结果 |
|---|---|
| `py -3.12 -m pytest tests -q` | **897 passed, 4 skipped**（较 VS-001 890 基线 +7，零回归） |
| `py -3.12 core/tools/catalog_check.py --check` | **OK**（v3 双视图与 roles/DAG/validators 三方一致） |
| `py -3.12 core/tools/validate.py` | **57 通过, 0 失败, 0 警告** |
| `py -3.12 -m pytest tests/integration/test_p1_m3_competition.py -q` | **7 passed** |
| 演示 | `research/P15/m3_run/project/`（registry/graph/status/replay_report/demo_summary） |

## 5. 设计要点与约束落实

- **消除 recs[0] 硬编码**：候选模式 `do_model_selection` 不再调 `arena.select`（不取
  shortlist[0]），容器 model 的 `selection_status=pending_evidence`；真正选型在
  `model_selection_decision` 按机械 criteria 完成；无 VR 证据 → `UNSELECTED` +
  confidence=0 + `no execution evidence available`（e2e test_05 断言）。
- **LLM-free**：候选 MODEL_IR（JSON）+ Code（Python 字符串）由外部 Model Constructor
  手写；`SELECTION_CRITERIA`/`_rank_candidates`/`_decision_confidence` 全为确定性
  机械逻辑，无 LLM 打分。
- **status 真实性**：EXEC.status 只来自 LocalPythonAdapter 真实 returncode（禁硬编码）；
  M3 中两个 EXEC returncode=0 → success，FAIL 判定发生在 VR 数值层。
- **幂等/可重入**：多候选 + 修订场景下 EXEC/VR 按 `executed_by`/`verified_by` 边幂等复用，
  VS-001 e2e（8 passed）不受影响。
- **禁改冻结物**：K002 frozen_specs/rubric、problem_cards/ 冻结题面、.gitignore/.git
  未触碰；`research/P15/experiments/P15-K002/` 等外部 dirty 文件未 add。
