# Architecture Debt Register — v3.1.0

> **状态**: 🟡 OBSERVED（观测到的架构债务，非待修复缺陷）
> **登记日期**: 2026-09-08
> **登记背景**: Architecture Validation Close（G6+G7+G8 收口）
> **配套文档**: `research/ENGINEERING/ARCHITECTURE_VALIDATION_CLOSE.md`

---

## 登记原则

以下 6 项均为 **Observed Architectural Debt**，含义是：

- ✅ 当前设计**如此**，已在实际运行中被观测并记录；
- ⚠️ **不是** "待修复缺陷"——不因"理论上可以做得更强"而打开 Architecture Refinement；
- 🚫 仅当出现 **frozen contract ≠ actual behavior**（冻结契约与实际行为不一致）时，才进入 Architecture Refinement 路径。

---

## Debt 清单

| ID | 名称 | 观测描述 | 观测证据 | 状态 |
|---|---|---|---|---|
| AD-G6-001 | verification coverage / alias semantics | G6 重放验证的 hash 覆盖范围与字段别名语义存在边界：run record 中 `workflow_version` 与 `prompt_hash` 为同源值（alias），`parent_run_id` 为自引用；hash 链验证覆盖顶层字段，未逐 artifact 全覆盖 | `projects/v3-real-2024a/state/runs/1027df74ffde.json`：workflow_version == prompt_hash == 5e65f282…；parent_run_id == run_id | OBSERVED |
| AD-G7-001 | State Truth 明确排除 process-owned status.json | State Truth 的定义为 Artifact Registry + Evidence Graph + Research State；`status.json` 是流程状态投影（由事件重建），明确**不属于** State Truth。对账时以投影一致性为校验目标，而非以 status.json 为真源 | `status.json` schema_version=3 注释与 `core/tools/state.py reconcile` 语义 | OBSERVED |
| AD-G8-001 | question status 不做 backward propagation | 下游 artifact 失效（invalidation）**不反向传播**到 question 状态：g8test-A/B 中 Q001 在 claim/result/figure 均已 invalidated 的情况下仍保持 `validated` | `projects/v3-real-2024a-g8test-A/state/status.json`：Q001 status=validated；同目录 registry 中 C001/R001/F001 = invalidated | OBSERVED |
| AD-G8-002 | workflow_reset 当前是 tracking-oriented | `workflow_reset` 的语义以**跟踪/进度重置**为导向（重置 completed/current/retries 等流程跟踪字段），而非内容语义重置（不重建 artifact 状态） | `engine_progress.json` / `status.json` workflow 节结构与 reset 行为 | OBSERVED |
| AD-G8-003 | invalidation 后 dangling references 未自动清理 | 失效传播后，引用已失效 artifact 的 dangling references 不被自动清理（如 Q001.claims 仍引用已 invalidated 的 C001），需显式处理 | g8test-A/B：`status.json` Q001.claims=['C001'] 而 registry C001=invalidated | OBSERVED |

---

## 当前处置

**不处置。** 上述债务维持 OBSERVED 状态，不触发 Architecture Refinement，理由：

1. 6 项均未出现 **frozen contract ≠ actual behavior**；
2. 当前为 P15.1 B0 accumulation 阶段，主工程注意力应放在 MODEL-CAP，而非架构打磨；
3. 若后续 P15 测量暴露某项债务确实造成**契约违背**（如 replay 无法复现、reconcile 误报、失效传播导致测量污染），再单独评估该单项。

---

## 触发重新评估的条件（预登记）

| 触发事件 | 可能涉及债务 |
|---|---|
| 出现 frozen contract ≠ actual behavior 的实测案例 | 视具体契约而定 |
| P15 测量中发现 hash 别名导致 replay 复现失败 | AD-G6-001 |
| reconcile 发现 status.json 投影与真源冲突 | AD-G7-001 |
| 测量中 question 状态与下游失效不一致导致误判 | AD-G8-001 / AD-G8-003 |
| workflow reset 行为导致跨轮次污染 | AD-G8-002 |

---

*登记人：MainAgent；债务措辞依据用户指令（OBSERVED，非待修复缺陷）。*
