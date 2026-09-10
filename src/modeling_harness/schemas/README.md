# src/modeling_harness/schemas — Schema 目录说明

> **`src/modeling_harness/schemas/v3/` 是唯一 canonical schema**（不可修改，见 AGENTS.md §5）。
> 本目录其余内容均为历史/衍生，不做运行时真源。

## 目录结构

| 路径 | 状态 | 说明 |
|---|---|---|
| `v3/` | **canonical（唯一真源）** | V3 认知工作流运行时的 schema：artifact / evidence / decision / model(MODEL_IR) / run / state / workflow / knowledge |
| `legacy/` | 归档（只读） | 9 个 V2 时代 schema，随 v3.2.2 起无代码路径引用，保留为历史证据（迁移 ≠ 删除） |

## 规则

- 修改 `v3/` 下任何 schema = 违反 AGENTS.md §5 禁令，必须先走 ADR。
- `legacy/` 为历史证据，不提供兼容路径（ADR-0005：V3 不向后兼容 V2）。
- 新增 schema 一律进 `v3/` 对应子域；归档旧 schema 进 `legacy/` 并更新本 README 与 `docs/architecture/CANONICAL_DOMAIN.md` 的归属登记。
