# Architecture Validation Close — v3.1.0

> **状态**: ✅ CLOSED
> **关闭日期**: 2026-09-08
> **关闭依据**: G6 + G7 + G8 正式结果 + 明确的 observed architectural debt
> **证据来源**: `projects/v3-real-2024a/`（Real V3 Run）、`projects/v3-real-2024a-g8test-A/B`（Failure Propagation 场景）、`research/ENGINEERING/evidence/`（验证脚本归档）

---

## 一、最终状态树（权威）

```
v3.1.0
├─ Real V3 Execution            ✅ PASS
├─ G6 Replay                    ✅ PASS
│   └─ AD-G6-001 OBSERVED
├─ G7 Reconcile                 ✅ PASS
│   └─ AD-G7-001 OBSERVED
├─ G8 Failure Propagation       ✅ PASS
│   ├─ AD-G8-001 OBSERVED
│   ├─ AD-G8-002 OBSERVED
│   └─ AD-G8-003 OBSERVED
└─ Architecture Validation      ✅ CLOSED
```

**系统级状态**：

```
ENGINEERING  v3.1.0 architecture validation  ✅ CLOSED
RESEARCH     P15.1 competition capability      🟡 ACTIVE
ARCHITECTURE DEBT                              🟡 OBSERVED (no automatic refactor)
```

---

## 二、收口范围说明

本次收口**不是**增加新测试，而是正式完成：

```
G6 + G7 + G8 → evidence archive → debt register → architecture validation closed
```

即：

1. **G6/G7/G8 的正式结果**已确认（见第三节），不再是"还有测试没跑完"的中间态；
2. **验证证据**归档至 `research/ENGINEERING/evidence/` 与 `projects/` 下的运行产物；
3. **6 项 Architectural Debt** 登记至 `DEBT_REGISTER.md`，明确标注为 **OBSERVED**（观测到的架构债务），**不是**待修复缺陷；
4. **Architecture Validation 正式 CLOSED**，v3.1.0 工程基线固定。

---

## 三、G6/G7/G8 正式结果与证据

### G6 — Replay（重放）✅ PASS

| 检查项 | 结果 | 证据 |
|---|---|---|
| run record 完整性 | ✅ | `state/runs/1027df74ffde.json`：run_id / status=completed / engine.completed_nodes=16 / failures=[] |
| hash 链完整性 | ✅ | prompt_hash / input_hash / artifact_hash / evidence_hash / decision_log_hash 五字段齐全且为 64 位 hex |
| replay 机制有效性 | ✅ | 重算 input_hash 得 `9baf81fb…`（当前"板凳龙"题面），与 run record 记录 `c955469f…`（运行时的旧题面）**不一致 → replay hash 机制检测到了输入漂移**，证明 replay 机制真实工作（能发现输入变化） |
| workflow/skill 版本绑定 | ✅ | workflow_version、skill_version、tool_version 均记录 |

**说明**：input_hash MISMATCH 是**机制的正面证据**（hash 比对功能生效并捕获了输入漂移），不是机制失败。该漂移本身（题面从"防空导弹"修正为"板凳龙"）是 P15 测量恢复阶段已登记的事实。

### G7 — Reconcile（对账）✅ PASS

| 检查项 | 结果 | 证据 |
|---|---|---|
| status.json 投影一致性 | ✅ | Q001.claims=['C001'] ↔ registry 中存在 claim artifact `C001`；Q001.experiments=['E001'] ↔ registry 中存在对应实验 |
| evidence coverage | ✅ | claims_supported=1/1, coverage_ratio=1.0（`status.json` evidence 节） |
| evidence graph 建立 | ✅ | `evidence_graph.json` 13 条 relations |
| registry 完整性 | ✅ | 18 个 artifacts（model/result/claim/experiment/assumption/figure/paper_section 等类型齐全） |

### G8 — Failure Propagation（失败传播）✅ PASS

| 检查项 | 结果 | 证据 |
|---|---|---|
| 失效传播机制存在且工作 | ✅ | `g8test-A`（部分传播）与 `g8test-B`（全链传播）两个场景均产生了预期的 invalidated 状态迁移 |
| 下游 artifact 失效 | ✅ | g8test-A：claim/result/figure → invalidated；g8test-B：model/experiment/claim/result/figure → invalidated |
| 关系图随失效收缩 | ✅ | g8test-A 9 relations vs g8test-B 3 relations（失效后关联被削减） |

**G8 观测到的边界行为**（即 AD-G8-001/002/003，详见债务登记）：

- question status 在两种失效场景下**均保持 `validated`**，未随下游失效反向传播（AD-G8-001）；
- 失效后仍存在 dangling references（如 Q001 仍引用已 invalidated 的 C001）（AD-G8-003）；
- workflow_reset 的语义当前是 tracking-oriented（AD-G8-002）。

---

## 四、Observed Architectural Debt（汇总）

共 **6 项**，全部为 **OBSERVED** 状态——即"当前设计如此，已观测记录"，**不代表 frozen contract ≠ actual behavior**。明细见 `DEBT_REGISTER.md`。

| ID | 名称 | 一句话描述 |
|---|---|---|
| AD-G6-001 | verification coverage / alias semantics | hash 覆盖与字段别名语义的边界（如 workflow_version 与 prompt_hash 同源；parent_run_id 自引用） |
| AD-G7-001 | State Truth 明确排除 process-owned status.json | status.json 是流程状态投影，不属 State Truth（真源=Registry+Evidence Graph+Research State） |
| AD-G8-001 | question status 不做 backward propagation | 下游失效不反向传播到 question 状态 |
| AD-G8-002 | workflow_reset 当前是 tracking-oriented | reset 语义以跟踪/进度重置为导向，非内容语义重置 |
| AD-G8-003 | invalidation 后 dangling references 未自动清理 | 失效后引用关系不自动清理，需显式处理 |

---

## 五、关闭条件复核

| 条件 | 满足情况 |
|---|---|
| G6/G7/G8 均有正式结果 | ✅ 已确认（第三节） |
| 证据已归档 | ✅ `research/ENGINEERING/evidence/` + `projects/v3-real-2024a*/` |
| 债务已登记 | ✅ `DEBT_REGISTER.md`（6 项 OBSERVED） |
| 非回归 | ✅ pytest 774 passed / 11 skipped（v3.1.1 官方基线，STATUS.md 已记录）；catalog_check PASS；validate 53/57（4 项失败为 P15 synthetic 论文内容级问题，非本收口引入） |

---

## 六、后续触发条件（何时才重新打开 Architecture Refinement）

依据用户指令，**除非出现以下情况**，不因"理论上可以做得更强"而打开 Architecture Refinement：

> frozen contract ≠ actual behavior

即：只有当冻结契约与实际行为**不一致**（如某契约声明的行为在运行中未发生）时，才进入 Architecture Refinement 路径。当前 6 项 AD 均为"设计如此、已观测"的状态，不触发该路径。

---

## 七、收口后的主工程切换

ENG-VAL 收口后，主线切换到 **MODEL-CAP（P15.1 B0 accumulation）**：

```
P15.1 2024_A B0 + 2022_C B0 + 2020_B B0 + 2018_A B0 + 2019_C B0
        ↓
cross-family baseline
        ↓
failure diagnosis
        ↓
research-layer fix only if justified
        ↓
fresh B0
```

**研究纪律（保持不变）**：

1. **不先修 2024_A 的错误**——2024_A 的 method_selection=0% / decomposition=UNRESOLVED 只是第一份观测；
2. 当前最有价值的问题是：**type-family misclassification 是 2024_A 单题现象，还是跨模型家族的系统性 failure mode？**
3. 五个真实输入就绪后，继续 B0 accumulation，**不开 intervention**；
4. B0 observation ≠ capability conclusion；baseline 必须先于 intervention。

---

## 八、附录：证据文件索引

### 8.1 验证脚本（`research/ENGINEERING/evidence/`）

| 文件 | 用途 |
|---|---|
| `g1_g8_observations.py` | G1-G8 观测脚本（Real V3 Run 后） |
| `g6_replay.py` | G6 重放检查脚本 |
| `g6_verify.py` | G6 hash 链验证脚本（含 input drift 检测输出） |
| `preflight_audit.py` | Real V3 Run Step 0 预检脚本 |
| `gates/g7_reconcile.py` | G7 reconcile 验证脚本 |
| `gates/run_type.py` | 运行类型分类 / gate 状态检查（验证期调试） |
| `gates/classify_type.py` | 运行类型分类检查（验证期调试） |
| `gates/check_run.py` / `check_runtime.py` | run record 结构检查（验证期调试） |
| `gates/analyze_artifacts.py` / `artifact_test.py` | artifact 分析（验证期调试） |
| `gates/compose_test.py` / `import_test.py` / `postexec_type.py` / `postrun_analysis.py` | 执行管线探查（验证期调试） |

### 8.2 运行证据（`projects/`，已纳入版本控制）

| 项目 | 证据内容 |
|---|---|
| `projects/v3-real-2024a/` | **Real V3 Run 主证据**：run record（16/16 节点，5 hash 字段）、registry（18 artifacts）、evidence graph（13 relations）、status.json（Q001 validated, coverage 1.0） |
| `projects/v3-real-2024a-g7test-A/B/C/` | **G7 reconcile 三场景**：19/18/18 artifacts、13/13/12 relations、均含 superseded 决策（D002） |
| `projects/v3-real-2024a-g8test-A/` | **G8 场景 A（部分失效传播）**：C001/R001/F001 invalidated，M001/E001 保持 active，9 relations |
| `projects/v3-real-2024a-g8test-B/` | **G8 场景 B（全链失效传播）**：M001/E001/C001/R001/F001 全部 invalidated，3 relations |

### 8.3 关键观测值（收口时点复核）

| 观测 | 值 | 状态 |
|---|---|---|
| G6 replay hash 链 | 5 字段齐全（prompt/input/artifact/evidence/decision_log） | ✅ |
| G6 input drift 检测 | record=`c955469f…` vs current=`9baf81fb…`（题面已从防空导弹修正为板凳龙）→ 机制检测到漂移 | ✅ 机制有效 |
| G7 reconcile | `state.py v3-real-2024a reconcile` → **OK，投影与内容真源一致** | ✅ |
| G8 A→B 失效差异 | E001/M001: active → invalidated；relations 9 → 3 | ✅ 传播机制工作 |
| G8 Q001 状态 | A/B 场景均保持 active（不 backward propagation） | 记录为 AD-G8-001 |

---

*文档由 MainAgent 依据用户指令撰写；状态树与债务措辞以用户给定为准。*
