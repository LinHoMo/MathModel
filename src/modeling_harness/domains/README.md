# domains/ — Canonical Domain Model（契约层，冻结）

## 定位 / Positioning
`domains/` 是**概念唯一真源**（Canonical Domain Model）：注册 12 类规范实体的
canonical schema 归属、v3 subtype 与合法投影名（详见
`docs/architecture/CANONICAL_DOMAIN.md`）。

**纯定义层**：零行为、零第三方依赖；`runtime` / `validators` / 文档均可安全 import。

## 状态 / Status（v1.0 冻结）
- **冻结不接入**：当前全仓零 import（无消费者）。这是"契约先于消费者"的设计，
  不是缺陷。
- **接入条件**：当某个 profile / domain / validator 需要 canonical entity 校验
  （如"该 artifact 的 schema 归属是否合法""该字段是否发明了近义词"）时，从此处
  import `CANONICAL_ENTITIES` / `canonical_name` / `entity_schema` 作为唯一真源。
- **红线**：任何新 schema / 字段 / 文件不得发明本模块之外的近义词；已有 V2 schema
  全部视为 legacy 投影。

## 决策 / Decision
- ADR-0006（结构顶层归位）将 `runtime/domain` 上提为顶层 `domains/`。
- T-CONF-006 裁定：**标注预定义，冻结不接入**（2026-09-10，用户裁定）。
