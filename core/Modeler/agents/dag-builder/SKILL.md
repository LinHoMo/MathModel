---
name: dag-builder
description: "模型依赖 DAG 构建 Agent (Stage 4.5)：在模型建立后、假设验证前，分析子模型间的数据/参数依赖，构建有向无环图，指导 Programmer 并行化实现、Writer 结构规划、Reviewer 级联风险定位。"
utg_layer: L4
stage: 4.5
hand: modeler
inputs:
  - work/model_draft.md
  - work/method_candidates.json
  - work/question_spec.json
outputs:
  - work/model_dag.json
  - work/model_dag.svg
---

# DAG Builder Skill (模型依赖 DAG 构建 Agent)

## Role

Stage 4.5 承载 Agent：在 `model-builder` 完成数学模型建立后、 `assumption-validator` 验证假设前，从模型草稿中提取子模型间的依赖关系，构建有向无环图（DAG），为下游并行化、结构规划、风险定位提供结构化依据。

## Contract

- **输入**：
  - `work/model_draft.md` (model-builder 输出)
  - `work/method_candidates.json` (method-matcher 输出)
  - `work/question_spec.json` (problem-parser 输出)

- **输出**：
  - `work/model_dag.json` (结构化依赖图)
  - `work/model_dag.svg` (Graphviz 渲染的可视化图)

- **中间产物**：`work/dag_analysis.md` (依赖分析说明)

## Procedure

### 1. 解析子模型清单

从 `model_draft.md` 提取每个子问题的建模方案：
- 子问题 ID (Q1, Q2, ...)
- 输入变量/参数
- 输出变量/结果
- 使用的方法/模型族
- 关键假设

### 2. 识别依赖关系

**依赖类型**：
1. **数据依赖**：Qj 的输入数据来自 Qi 的输出结果（如 Q2 优化的目标函数参数来自 Q1 的预测值）
2. **参数依赖**：Qj 的模型参数需由 Qi 估计/校准（如 Q3 仿真的边界条件来自 Q1 的反演结果）
3. **约束耦合**：Qi 和 Qj 共享约束条件，需联合求解
4. **顺序耦合**：Qj 的建模前提假设依赖 Qi 的结论（如 Q2 假设 Q1 的预测误差 < 5%）

**识别规则**：
- 符号表中同一符号在不同子问题出现 → 可能存在依赖
- `model_draft.md` 中显式引用 "上一问结果" / "前序模型输出" → 硬依赖
- 方法族关联（如预测→优化、聚类→评价、机理→仿真） → 经验依赖

### 3. 构建 DAG

**节点**：每个子问题一个节点
```json
{
  "id": "Q1",
  "label": "需求预测",
  "method": "LSTM + 注意力机制",
  "inputs": ["历史销量", "促销日历", "天气"],
  "outputs": ["未来30天预测值", "预测区间"],
  "params": ["窗口长度", "隐层维度", "学习率"],
  "assumptions": ["平稳性", "外生变量已知"],
  "stage_order": 1
}
```

**边**：有向边表示依赖
```json
{
  "source": "Q1",
  "target": "Q2",
  "type": "data",
  "description": "Q2库存优化的需求参数来自Q1预测均值",
  "critical": true,
  "sensitivity": "high"
}
```

**约束**：
- 必须是 DAG（无环检测）
- 拓扑排序给出 `stage_order`（并行组：同层级可并行）
- 标记 `critical=true` 的边为关键路径

### 4. 输出产物

**`work/model_dag.json`**：
```json
{
  "nodes": [...],
  "edges": [...],
  "topological_order": [["Q1"], ["Q2", "Q3"], ["Q4"]],
  "parallel_groups": [["Q2", "Q3"]],
  "critical_path": ["Q1", "Q2", "Q4"],
  "stats": {
    "total_nodes": 4,
    "total_edges": 3,
    "max_parallelism": 2,
    "critical_path_length": 3
  },
  "generated_at": "2026-09-01T11:00:00Z"
}
```

**`work/model_dag.svg`**：Graphviz dot 渲染，节点按 `stage_order` 分层，关键路径加粗红色，边标注类型。

**`work/dag_analysis.md`**：
- 依赖识别依据表（符号/引用/方法族）
- 并行化建议（哪些可同时开工、预计加速比）
- 级联风险点（关键路径上假设失效的影响范围）
- 给 Programmer 的并行实现建议
- 给 Writer 的章节安排建议（按拓扑序）

## Resources

- `core/knowledge/validation/symbol_registry.py` - 符号表复用，识别跨子问题共享符号
- `core/knowledge/validation/process_verifier.py` - 过程验证器，检查依赖完整性
- Graphviz (系统工具) - SVG 渲染
- `core/env/loader.py` - 读取配置

## Self-Check

- [ ] `model_dag.json` 存在且符合 `core/schemas/model_dag.schema.json` (需新建)
- [ ] 所有子问题均在 nodes 中
- [ ] edges 无自环、无重复、类型 ∈ {data, parameter, constraint, sequential}
- [ ] 拓扑排序成功（无环），`topological_order` 覆盖所有节点
- [ ] `parallel_groups` 非空时，组内节点无相互依赖
- [ ] `critical_path` 是从源节点到汇节点的最长路径
- [ ] `model_dag.svg` 存在且可被浏览器打开
- [ ] `dag_analysis.md` 含并行化建议与级联风险点

## Iteration

- 发现环：回退 stage 4 (model-builder) 澄清模型边界、拆分耦合子问题
- 并行度为 1：检查是否可通过解耦（引入中间变量、松弛约束）提升并行性
- 关键路径过长：标记高风险，建议 Writer 增加鲁棒性讨论

## Env Bindings

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `modeling.dag_enable_visualization` | true | 是否生成 SVG |
| `modeling.dag_critical_sensitivity` | high | 关键路径灵敏度阈值 |

## UTG Layer Mapping

| UTG 层 | 机制 | 本 Agent 落地 |
|--------|------|--------------|
| L3.5 | 过程验证 + 依赖结构化 | 依赖识别规约化 + DAG 结构化输出 + 可视化 |

## 注意事项

1. **不创造依赖**：仅从已有模型文本中提取，不凭空添加
2. **最小化关键路径**：优先识别硬依赖，软依赖（经验性）标注低置信度
3. **服务下游**：`parallel_groups` 直接指导 Programmer 的 `template_plan.json` 中的并行任务规划