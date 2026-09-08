# 数学模型构造任务（P15-K001）

> 本文件是本次模型构造运行的**唯一输入**。请严格按第 3 节的输出契约产出结果，不要自行检索外部资料。

- submission_id：`deda4e16-1b3d-4d5c-a9a1-fa6f81f76d1c`
- problem_id：`2019_C`
- random_seed：`44`

## 1. 题面

2019 年高教社杯全国大学生数学建模竞赛题目
（请先阅读"全国大学生数学建模竞赛论文格式规范"）

C 题 机场的出租车问题

大多数乘客下飞机后要去市区（或周边）的目的地，出租车是主要的交通工具之一。国内多数机场都是将送客（出发）与接客（到达）通道分开的。送客到机场的出租车司机都将会面临两个选择：
(A) 前往到达区排队等待载客返回市区。出租车必须到指定的"蓄车池"排队等候，依"先来后到"排队进场载客，等待时间长短取决于排队出租车和乘客的数量多少，需要付出一定的时间成本。
(B) 直接放空返回市区拉客。出租车司机会付出空载费用和可能损失潜在的载客收益。

在某时间段抵达的航班数量和"蓄车池"里已有的车辆数是司机可观测到的确定信息。通常司机的决策与其个人的经验判断有关，比如在某个季节与某时间段抵达航班的多少和可能乘客数量的多寡等。如果乘客在下飞机后想"打车"，就要到指定的"乘车区"排队，按先后顺序乘车。机场出租车管理人员负责"分批定量"放行出租车进入"乘车区"，同时安排一定数量的乘客上车。在实际中，还有很多影响出租车司机决策的确定和不确定因素，其关联关系各异，影响效果也不尽相同。

请你们团队结合实际情况，建立数学模型研究下列问题：

(1) 分析研究与出租车司机决策相关因素的影响机理，综合考虑机场乘客数量的变化规律和出租车司机的收益，建立出租车司机选择决策模型，并给出司机的选择策略。

(2) 收集国内某一机场及其所在城市出租车的相关数据，给出该机场出租车司机的选择方案，并分析模型的合理性和对相关因素的依赖性。

(3) 在某些时候，经常会出现出租车排队载客和乘客排队乘车的情况。某机场"乘车区"现有两条并行车道，管理部门应如何设置"上车点"，并合理安排出租车和乘客，在保证车辆和乘客安全的条件下，使得总的乘车效率最高。

(4) 机场的出租车载客收益与载客的行驶里程有关，乘客的目的地有远有近，出租车司机不能选择乘客和拒载，但允许出租车多次往返载客。管理部门拟对某些短途载客再次返回的出租车给予一定的"优先权"，使得这些出租车的收益尽量均衡，试给出一个可行的"优先"安排方案。

## 2. 参考资料

<!-- BEGIN REFERENCE — 各臂唯一差异区，之外的内容必须逐字节一致 -->
本轮**不提供**任何参考资料。请仅依据题面进行建模。
<!-- END REFERENCE -->

## 3. 输出契约

产出一份符合 **MODEL IR v1.0** 的 JSON，写入 `runs/deda4e16-1b3d-4d5c-a9a1-fa6f81f76d1c/model_ir.json`。

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

`problem_binding.problem_sha256` 必须填 `4fc950a9a22510431b26b0406c4e354dec0c18c75f97c4fe8087d439795e5ad2`。

质量要求（直接影响评分；但**不要**为了凑分写空话，缺失就写"待求解"）：

1. **符号自洽**：方程中出现的每个符号都必须能在 `variables` 或 `parameters` 中找到；索引口径须前后一致。
2. **机理**：写明"为何是这个机理"、它与题目物理/现实机制的一致性；若考虑过其他候选机理，写明对比与选择依据。
3. **约束**：覆盖题面全部硬性条件，注意方向（≤ 还是 ≥）。
4. **方程**：控制方程 + 初始条件 + 边界条件。
5. **验证**：`validations` 至少含 1 个对照基线 + 1 个灵敏度分析。
6. **主张**：每条 `claim` 必须指向 `evidence_refs`。

## 4. 参考资料使用记录

若第 2 节提供了参考资料，**必须**在 `runs/deda4e16-1b3d-4d5c-a9a1-fa6f81f76d1c/manifest.json` 的 `knowledge_trace` 字段记录：

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
