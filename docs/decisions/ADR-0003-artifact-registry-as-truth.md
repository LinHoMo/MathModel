# ADR-0003: Artifact Registry as Truth / Artifact Registry 作为真源

- Status / 状态：Accepted
- Date / 日期：2026-09-10
- Context / 上下文：系统需要回答「当前状态是什么、产出过什么、彼此什么关系」。历史多套状态/产物并存导致语义漂移（双真源问题档案见 STATUS.md）。
- Decision / 决策：**Source of truth = Artifact Registry + Evidence Graph**。Artifact 是内容真源（稳定 ID + 生命周期 + payload 路径），Evidence Graph 是关系真源（typed edges + 失效传播 + Revision lineage）；`status.json` 是派生视图，只能由 `refresh_from(registry, graph)` 重建，禁止手工/Agent 直接写入。状态只设一个权威来源。
- Consequences / 后果：状态可对账（reconcile）、可重放（replay）、可审计；投影（Evidence / Experiment / Paper / Evaluation）只能从 Registry / Graph / 事件重建，禁止反向手写；Agent 文字输出不是系统状态。
- Evidence / 证据：`docs/architecture/V3.1_ARCHITECTURE.md`（§1.1 Artifact、§1.2 State、§1.3 Evidence、§1.11 Stable ID）；`docs/architecture/STATE_TRUTH.md`（状态单一真源决策表，reconcile 对账器）；`docs/STATUS.md`（机器实测数字绑定 commit）。
