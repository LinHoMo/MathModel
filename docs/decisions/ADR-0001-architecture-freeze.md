# ADR-0001: Architecture Freeze / 架构冻结（V3.1）

- Status / 状态：Accepted
- Date / 日期：2026-09-10
- Context / 上下文：V3.1 认知工作流运行时已经过 P0–P6 硬化收口（Artifact Registry / Evidence Graph / DAG 引擎 / 验证门禁 / Replay / Reconcile），真实项目端到端验证通过。为避免架构频繁变动消耗治理成本，需要冻结边界。
- Decision / 决策：自 2026-09-07 起架构冻结：`core/runtime/` 与 Guardrails（validators + gates）冻结，不再接受架构革命；治理例外须经 `docs/architecture/RUNTIME_CONTRACTS.md` 授权。能力进步以基线 Δscore 度量，不以「新增契约/测试数量」度量。
- Consequences / 后果：变更必须先走契约授权或 ADR；冻结物不可被普通任务修改（AGENTS.md §5 强制执行）；冻结不阻止 bug 修复与文档/配置/基线任务。
- Evidence / 证据：`docs/architecture/V3.1_ARCHITECTURE.md`（18 概念问题 + 实施门）；`docs/STATUS.md` 阶段历史（Hardening P0–P6 全部 ✅）；`docs/architecture/RUNTIME_CONTRACTS.md`（P7 契约冻结）。
