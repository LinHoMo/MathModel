# Decision Records / 决策记录（ADR）

> 本目录登记架构级决策（Architecture Decision Records）。任何影响
> 架构边界、真源归属、依赖策略、兼容性策略的决策，必须先写 ADR 再执行。
> 模板见 `ADR-TEMPLATE.md`。

## 索引

| ADR | 标题 | 状态 |
|---|---|---|
| [ADR-0001](ADR-0001-architecture-freeze.md) | 架构冻结（V3.1） | Accepted |
| [ADR-0002](ADR-0002-llm-free-core.md) | core LLM-free（Agent 只是 Executor） | Accepted |
| [ADR-0003](ADR-0003-artifact-registry-as-truth.md) | Artifact Registry 作为真源 | Accepted |
| [ADR-0004](ADR-0004-no-third-party-deps.md) | 运行时零依赖（区分测试依赖） | Accepted |
| [ADR-0005](ADR-0005-v3-no-backward-compat.md) | V3 不向后兼容 V2 | Accepted |
| [ADR-0006](ADR-0006-structure-top-level-placement.md) | 顶层结构归位（domains / adapters / retired） | Accepted |
| [ADR-0007](ADR-0007-profiles-package.md) | profiles 包 | Accepted |
| [ADR-0008](ADR-0008-problem-understanding-layer.md) | 问题理解层归属与 runtime 修改授权 | Accepted |
| [ADR-0009](ADR-0009-integration-inside-existing-nodes.md) | 机制在既有节点内集成而非新增 DAG 节点 | Accepted |
| [ADR-0010](ADR-0010-model-families-revision-r1.md) | model_families 词表修订 r1（CUMCM 2026 结构对齐） | Accepted |
| [ADR-0011](ADR-0011-knowledge-card-gate.md) | 知识卡双层门禁与 source_type 枚举增补 | Accepted |
| [ADR-0012](ADR-0012-efficiency-metric-denominator.md) | 效率统计口径以题面定义为准、跨实现比较前必须归一 | Accepted |
| [ADR-0013](ADR-0013-objective-over-validation-in-model-selection.md) | 模型选择必须比目标函数值，基线对照链必须闭环 | Accepted |

## 规则

- 新决策：复制 `ADR-TEMPLATE.md`，编号顺延（ADR-0006…），填入 6 字段。
- 状态：`Accepted` / `Proposed` / `Deprecated`。被推翻的 ADR 标 `Deprecated` 并注明替代。
- 证据：ADR 的 Decision/Consequences 必须能追溯到现有文档或机器实测，禁止编造。
