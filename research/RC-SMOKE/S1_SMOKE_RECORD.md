# S1 Smoke Record — 2024A / 16 波真实认知执行

- 日期：2026-09-07 · 项目：`projects/rcs1-2024a`（真实 CUMCM 2024A 题面）
- 执行方式：`orchestrator.py rcs1-2024a --execute`（RuntimeSession，全程本地，无外部 provider 调用）
- 判定对象：**链路完整性**（State Truth / Replay / RunRecord / Provider boundary / Artifact-Evidence chain），非论文分数

## 1. 执行摘要

RuntimeSession 一次通过全部波次：完成 16/16 节点、0 阻塞、0 失败；registry 登记 **16 artifacts**（1 problem / 1 question / 2 decision / 1 model / 2 assumption / 1 experiment / 1 result / 1 figure / 1 claim / 5 paper_sections）；evidence graph 12 relations（P001→Q001→M001→A001/A002→E001 validated_by→…，链路连贯）。

## 2. 五链验证

| 链 | 验证方式 | 结果 |
|---|---|---|
| State Truth | `state.py reconcile` | **PASS**——投影与内容真源一致（exit 0） |
| Replay | `replay.py projects/rcs1-2024a` | **PASS**——run `22a4bf4ad576` 确定性口径全匹配（input/workflow/skill/tool/artifact/evidence/decision_log hash）+ 对账一致 |
| RunRecord | `state/runs/22a4bf4ad576.json` | **存在且 verify 全字段匹配** |
| Provider boundary | 执行日志 | 全程本地；adapters/openai.yaml 未启用（未走外部 runtime），边界无违反 |
| Artifact/Evidence chain | registry.json / evidence_graph.json | 内联单源设计（`artifacts/` 空目录为正常形态，非缺陷）；关系图连贯；claim 1/1 |

## 3. 缺陷分级清单（治理矩阵：A/B/C）

| 级 | 缺陷 | 处置 |
|---|---|---|
| **A×1** | `core/tools/runtime/replay.py:55`——verify 失败路径裸取 `rep["reconcile"]`，RunRecord 存在但调用方传参不当时 CLI 以 KeyError 崩溃（replay 区域） | **已按 bug-fix-only 修复**（`.get` 兜底）：原调用优雅 FAIL 不崩溃、正确路径仍 OK、catalog_check OK、**pytest 781 passed / 11 skipped 基线不变** |
| B×1 | CLI 契约不一致：`state.py` 收项目名（解析到 `projects/`），`replay.py` 收字面路径；且路径不存在时报"非 v3 项目"（误导性诊断） | 记录；建议未来小 PR 归一化参数语义与报错文案 |
| B×2 | 双视图展示缺口：`state.py status` 只显示 V2 视角 0/29，V3 完成态需 reconcile/v3 视图才能看到 | 记录；建议 status 增加 v3 进度行 |
| B×3 | 内容深度：2024A 模型仅 2 假设 / 1 实验 / 1 结果（真实题面的碰撞仿真等更重建模未展开） | 模型质量问题，归 skill/workflow 层改进；不判 RC、不改架构 |
| C×1 | `validate.py` 56/57：[L6] 论文结构缺 .tex | 预期——smoke 止步于"论文投影就绪"，Writer 渲染未执行；非缺陷 |
| C×2 | 执行日志"波次 20 · 完成 16/16"口径含混（20 为含重试/子波次的处理计数） | 记录；文案澄清建议 |

## 4. 判定

> **RC-S1 smoke：PASS。** 五条链在真实题面 + 真实认知负载下全部成立；A 类缺陷 1 项已按冻结治理（bug-fix-only）修复闭环；无未闭环 A 类，RC 无需重开。B/C 类共 6 项全部留层处理。

## 5. 后续

- B×1/B×2：CLI 归一化与状态展示改进（未来小 PR，不阻塞）。
- B×3：内容深度由 skill/工作流层迭代（不阻塞）。
- S2：等用户提供科研建模问题。
- RC 线至此：S1 PASS / S3 PASS / S2 BLOCKED——**RC 线全部可判定项收口**。
