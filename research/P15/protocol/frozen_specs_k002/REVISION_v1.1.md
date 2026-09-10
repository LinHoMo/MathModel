# P15-K002 冻结基线 revision v1.1

- 时间：2026-09-10T03:16:38Z
- 原因：P1-4 MODEL_IR 契约分层重构：core schema 唯一真源收敛（research/P15/model_representation/model_ir.schema.json 已删除）；数组元素 required=旧core∩0.8 公共核心；模板承诺字段标 x-template-promise（register 层强制）；词表 enum 移入模板承诺层；sub_question_binding 统一 string|array；model_graph/modeling_trace 宽松承载。K002 已 CLOSED，无新数据。
- 处置：REVISION 记录 + hashes.json 重冻结（frozen_at/root 更新）
- 约束：实验已 CLOSED，无新数据；结论不变；历史产物不回溯。
