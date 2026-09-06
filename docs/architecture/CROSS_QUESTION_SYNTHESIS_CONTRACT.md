# Cross-Question Synthesis Contract — P12-3-lite（冻结）

> 状态：**已冻结**（2026-09-06）。本契约同时是 P12 全阶段的收口文件：
> P12-1 / P12-2 / P12-3-lite 交付即终点，后续扩展见文末「不做清单」与门禁。
> `core/runtime/state/dependencies.py` 头部注释引用的即本文件。

## 1. 定位

P12-3-lite 不是新的科研实体体系（Synthesis IR 被否决），而是**给 Agent 的
统一跨问题上下文**：一个派生式的只读汇总层，把 Registry / EvidenceGraph /
State / P12-1 依赖 / P12-2 关系压缩成一个可供四手执行会话直接消费的上下文块。
它只是 Agent 的上下文压缩/汇总结果。

## 2. 最小语义闭包（边界即契约）

```text
Input:   Registry / EvidenceGraph / State / P12-1 dependencies / P12-2 relations
Output:  CrossQuestionContext（派生对象）
Properties:
  derived-only（每次从 State 重算）      deterministic（零 LLM、零随机）
  no persistence（不落盘、不写 State）    no artifact registration（不进 Registry）
  no invalidation propagation            no new ontology（不新增 artifact/关系类型）
  no LLM
```

实现不追求行数，只对上述闭包负责：`core/runtime/synthesis/context.py`。

## 3. API

```python
ctx = session.cross_question_context(question_ids=None)   # 缺省 = 全部 question
# 等价：build_cross_question_context(registry, graph, state, question_ids)

ctx.per_question      # {qid: {status, claims, findings[稳定键引用]}}
ctx.dependencies      # 两端在问题集内的 P12-1 records
ctx.cross_relations   # 两端在问题集内的 P12-2 records（CQR）
ctx.conclusions       # 准入组合（supported / qualified）
ctx.hypotheses        # 未准入组合（引用必须保持假设态）
ctx.state_version     # {graph_version, dependency_records, cross_question_relations}
ctx.as_dict()         # 程序化导出
ctx.to_context_block()  # markdown 上下文块（Agent 消费入口）
```

finding 引用使用稳定键 `{type}:{'+'.join(supported_by)}`；`finding_id` 含
FindingGraph batch 序号，不跨重建稳定，仅作展示不作引用。

## 4. 准入门与定级（P12-0 §3 裁决的落地）

准入三条件（全部满足才得 conclusion，否则降级 hypothesis）：

1. **显式依赖声明**：P12-1 records 中存在连接两问题的依赖，且类型参与
   synthesis（参与矩阵冻结：evidential / comparative / extension）；
2. **状态可入组**：组件 finding status ∈ {PASS, WEAK}，FAIL/UNKNOWN 永不入组合；
3. **证据独立**：两侧成员的支撑 result 集合不相交（P9 EQ-independence
   跨问题扩展：同源不得因数量升级）。

定级（离散瓶颈规则，**不实现连续加权**）：

| 条件 | 级别 |
|---|---|
| 全部成员 PASS | supported |
| 存在 WEAK（瓶颈 = 最弱） | qualified |
| 任一准入条件未过 | hypothesis |
| 无任何准入组合 | 上下文块标注 `synthesis: absent` |

provenance 最小集（audit §Q12）：`question_refs / finding_refs（含
result/experiment 反查链）/ claim_refs / dependency_refs / relations /
decision_rule / state_version / limitations`。

## 5. 不做清单（与 P12 一起冻结）

- 不新增跨问题关系类型：`compares / extends / derived_from` 三类型即终点
  （P12-2 现状冻结）；不做 relation lifecycle / relation revalidation 系统
  （上游失效 → `requires_revalidation` 可逆记账已覆盖全部需求）；
- **P12-7 取消**（跨问题失效重派生 / state_version 对账）——陈旧性由
  state_version 展示 + 重派生即更新替代；
- **P12-8 取消**（comparative metrics 跨问题数值源）——依赖真实实验执行，
  属 P15 实验智能的能力问题，不是契约问题；
- **P12-9 取消**（literature ingestion 通道）——`literature_refs` 插座保留原样；
- **P12-10 取消**（projection re-projection）——projection 保持现状；
  synthesis 缺位时上下文块标注 `synthesis: absent`，不硬失败（P12-0 §4 建议）；
- 不做连续置信度加权；不做 synthesis 落盘；不做 synthesis 级 artifact 类型。

## 6. 扩展规则

出现真实需求时，任何扩展必须先过三层治理门禁
（见 `docs/architecture/THREE_LAYER_ARCHITECTURE.md` 三问门禁）：
Q1 提升解题能力？Q2 提升可靠性？——两者皆否（仅内部语义更严谨）则不做。

## 7. 相关文件

- 设计裁决：`docs/architecture/CROSS_QUESTION_SYNTHESIS_AUDIT.md`（P12-0 只读审计）
- 实现：`core/runtime/synthesis/context.py`；会话入口 `core/runtime/execution/session.py`
- 上游契约：`core/runtime/state/dependencies.py`（P12-1）、`core/runtime/state/relations.py`（P12-2）
- 测试：`tests/integration/test_cross_question_context.py`（14 项边界性质）
