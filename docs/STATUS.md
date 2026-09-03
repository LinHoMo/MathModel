# 项目状态

> 本文件由对齐流程维护；数字由 `core/tools/metrics.py` 自动注入。

## 阶段完成度

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

- P4 HMML 注册需在 methodology/INDEX.md 中加 HMML 条目（当前 methodology 共 53 篇）
- P5 ARCHITECTURE 与 STATUS 文档需要与 AGENTS.md 统一措辞（避免"评委评分"与"bench 复盘"概念混淆）
- P3 diagram_gen.py 已被增强，但 SVG 渲染需要 matplotlib（可选依赖）
