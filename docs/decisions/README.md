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

## 规则

- 新决策：复制 `ADR-TEMPLATE.md`，编号顺延（ADR-0006…），填入 6 字段。
- 状态：`Accepted` / `Proposed` / `Deprecated`。被推翻的 ADR 标 `Deprecated` 并注明替代。
- 证据：ADR 的 Decision/Consequences 必须能追溯到现有文档或机器实测，禁止编造。
