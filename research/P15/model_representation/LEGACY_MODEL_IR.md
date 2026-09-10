# MODEL_IR 历史产物 Legacy 边界（P1-4 唯一真源收敛）

> 契约真源：`core/schemas/v3/model/model_ir.schema.json`（Draft 2020-12，18 required
> 顶层字段 + code_mapping 可选）。runtime 结构校验：`core/runtime/modeling/model_ir.py`
> `validate_model_ir()`（零依赖）。`research/P15/model_representation/model_ir.schema.json`
> 已删除（2026-09-10，P1-4）——全仓仅一份 schema。

## 不回溯（legacy 冻结）

以下实验产物的 model_ir.json 按当时契约生成，**标记 legacy 不回溯**（不重算、不迁移）：

| 产物集 | 数量 | 说明 |
|---|---|---|
| P15-K001 runs | 55 | 已 CLOSED，冻结基线 |
| P15-K002 runs + precheck | 108 + 12 | 已 CLOSED，冻结基线 |
| P15-K003 bundles + runs + precheck | 66 + 66 + 12 | 已 CLOSED，冻结基线 |
| p1-vs001 m0/m1/m2 | 3 | 演示闭环基线（7/7 验收已冻结） |

这些产物的差异（词表/嵌套结构/占位 hash）属内容级差异，机械迁移会改动实验数据，
违反"FROZEN 后不回溯"纪律。

## 新产物义务

- 新 MODEL_IR 必须通过 `core/schemas/v3/model/model_ir.schema.json`（jsonschema 全量
  校验，`Draft202012Validator`）与 `validate_model_ir()`（结构校验）。
- 迁移旧格式（仅补 code_mapping）用 `model_ir.migrate_legacy_format()`。
- 契约细节见 `MODEL_IR_SPEC.md`（v1.1）。
