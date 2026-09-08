# 数学模型构造任务（P15-K001）

> 本文件是本次模型构造运行的**唯一输入**。请严格按第 3 节的输出契约产出结果，不要自行检索外部资料。

- submission_id：`{{SUBMISSION_ID}}`
- problem_id：`{{PROBLEM_ID}}`
- random_seed：`{{SEED}}`

## 1. 题面

{{PROBLEM_STATEMENT}}

## 2. 参考资料

<!-- BEGIN REFERENCE — 各臂唯一差异区，之外的内容必须逐字节一致 -->
本轮**不提供**任何参考资料。请仅依据题面进行建模。
<!-- END REFERENCE -->

## 3. 输出契约

产出一份符合 **MODEL IR v1.0** 的 JSON，写入 `runs/{{SUBMISSION_ID}}/model_ir.json`。

必需顶层字段：

```
ir_version, model_id, model_family, problem_binding, assumptions, variables,
parameters, objectives, constraints, mechanisms, equations, dependencies,
solvers, experiments, validations, claims, model_graph, modeling_trace
```

各条目最小字段：

| 条目 | 必需字段 |
|---|---|
| assumption | `assumption_id, text, source, confidence, sub_question_binding` |
| variable | `variable_id, name, symbol, definition, unit, type, sub_question_binding` |
| parameter | `parameter_id, name, symbol, definition, unit, value, source, sub_question_binding` |
| objective | `objective_id, type, expression, variables_refs, sub_question_binding, clarity_score` |
| constraint | `constraint_id, type, expression, variables_refs, source, sub_question_binding` |
| mechanism | `mechanism_id, name, description, type, governing_principle, variables_refs, sub_question_binding` |
| equation | `equation_id, latex, type, variables_refs, derivation_trace, sub_question_binding` |
| validation | `validation_id, type, method, results, pass_fail, sub_question_binding` |
| claim | `claim_id, text, type, evidence_refs, sub_question_binding`（`status` ∈ `supported` / `refuted` / `unresolved`） |
| model_graph | `graph_version, nodes, edges` |
| modeling_trace | `trace_version, generated_at, agent_identity, input_sha256` |

`problem_binding.problem_sha256` 必须填 `{{PROBLEM_SHA256}}`。

质量要求（直接影响评分；但**不要**为了凑分写空话，缺失就写"待求解"）：

1. **符号自洽**：方程中出现的每个符号都必须能在 `variables` 或 `parameters` 中找到；索引口径须前后一致。
2. **机理**：写明"为何是这个机理"、它与题目物理/现实机制的一致性；若考虑过其他候选机理，写明对比与选择依据。
3. **约束**：覆盖题面全部硬性条件，注意方向（≤ 还是 ≥）。
4. **方程**：控制方程 + 初始条件 + 边界条件。
5. **验证**：`validations` 至少含 1 个对照基线 + 1 个灵敏度分析。
6. **主张**：每条 `claim` 必须指向 `evidence_refs`。

## 4. 参考资料使用记录

若第 2 节提供了参考资料，**必须**在 `runs/{{SUBMISSION_ID}}/manifest.json` 的 `knowledge_trace` 字段记录：

- `retrieved`：参考资料条目标识列表
- `considered`：实际认真考虑过的条目
- `used`：最终采纳的条目
- `adapted`：做了改造后使用的条目
- `rejected`：`[{card_id, reason}]` —— 明确拒绝的条目及理由

**如果参考资料与本题机理不符，你应该拒绝它并说明理由；不要为了迎合参考资料而强行套用。**

若第 2 节未提供参考资料，请将上述字段留为空白数组。

## 5. 禁止事项

- 不检索题面之外的外部资料或网络。
- 不输出与本任务设置相关的任何元信息标注。
- 不伪造数值结果；无法计算的部分标为"待求解"，不要编造。
