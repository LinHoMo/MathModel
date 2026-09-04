# 项目状态

> 本文件由对齐流程维护；数字由 `core/tools/metrics.py` 自动注入。

## V3.1 迁移（2026-09-04 完成）

| 阶段 | 状态 | Commit |
|---|---|---|
| 审计轮 1-3（基线 + V3.1 架构 + 迁移映射） | ✅ 完成 | `1140e96` |
| V3-P0 Artifact Layer（Stable ID / Contract / Lifecycle / Registry） | ✅ 完成 | `a97991e` |
| V3-P1 State + Evidence Graph + Workflow DAG + Legacy 双向转换 | ✅ 完成 | `e5c3049` |
| V3-P2 Knowledge 层（16 方法卡 / 10 失败记忆 / 6 模式 / Decision Log） | ✅ 完成 | `3087cb0` |
| V3-P3 Modeling 层（5 Roles / MethodArena / Evidence Gate E1-E8） | ✅ 完成 | `4df9cc7` |
| V3-P4 Writing 层（ResearchDirector / Projection / 四态 Judge）+ catalog v5 | ✅ 完成 | `4487cd8` |
| V3-P5 收尾（目录重构 / orchestrator 默认 V3 / 回归测试 / 最终审计） | ✅ 完成 | 本次提交 |

测试：**542 passed / 10 skipped / 1 pre-existing fail**（V2 基线 382 → 净增 +160）。
详见 `docs/architecture/V3_FINAL_AUDIT.md` 与 `V3_IMPLEMENTATION_REPORT.md`。

## 阶段完成度（V2 改进计划，早于 V3 迁移）

| 阶段 | 状态 | Commit |
|---|---|---|
| P0 诚信基线（gate 接入 + manifest + metrics + aggregate） | ✅ 完成 | `5967940` |
| P1 国赛复盘基准（rubric 22 年 + bench 4 命令 + MMBench + 时序回顾） | ✅ 完成 | `d147bda` |
| P2 引用可信（citation_check + citation schema） | ✅ 完成 | `9b3c77a` |
| P3 交付物与图表（figure template + 配色常量 + diagram_gen） | ⚠️ 部分（在 v1/v2 阶段已完成图表模板、配色、diagram_gen.py） | — |
| P4 知识与方法层（HMML 注册 + lazy loading + MCM 2026 规则） | ⏳ 待补 | — |
| P5 定位重写（数字一致性 + README 命令对齐） | 🔄 进行中 | — |

## 当前数字（由 metrics.py 自动注入）

运行 `python core/tools/metrics.py --write` 获取最新数字，或查看 docs/METRICS.md。

## 风险与待办

- **V3 下一步**：WaveExecutor 实装（orchestrator V3 从干跑转实际执行）；修复 test_delivery_gates AI 披露 1 个 pre-existing fail；metrics.py 历史基线死引用清理
- P4 HMML 注册需在 methodology/INDEX.md 中加 HMML 条目（当前 methodology 共 53 篇）
- P5 ARCHITECTURE 与 STATUS 文档需要与 AGENTS.md 统一措辞（避免"评委评分"与"bench 复盘"概念混淆）
- P3 diagram_gen.py 已被增强，但 SVG 渲染需要 matplotlib（可选依赖）
