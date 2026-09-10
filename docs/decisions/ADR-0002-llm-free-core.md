# ADR-0002: LLM-Free Core / core 内 LLM-free

- Status / 状态：Accepted
- Date / 日期：2026-09-10
- Context / 上下文：项目的不可替代资产是 Harness（Artifact Registry + Evidence Graph + Execution Substrate + Validation Gates + State Machine），而非「会建模的 Agent」。K001–K003 实验证明核心价值在 Runtime/Evidence 层，不在 Constructor 层。
- Decision / 决策：core 内 LLM-free——Agent / LLM（Doubao / GPT / Claude Code / MathModelAgent / 人工）只是外部 Executor（Constructor），通过 Constructor Protocol（MODEL_IR + Code + Intent）接入；核心不包含 LLM 执行器，认知工作由外部 Agent 在 harness 下完成。铁律：**The Agent Is Not The State**；ExecutionResult.status 只来自真实 subprocess。
- Consequences / 后果：核心逻辑全部确定性可验证、可重放；禁止在 core 内构建 LLM 调用或把项目做成完整数模 Agent；外部 Constructor 通过 `core/runtime/constructors/` 适配器接入（不触碰 Runtime 信任核心）。
- Evidence / 证据：`docs/architecture/V3.1_ARCHITECTURE.md`（§1.7 Agent/Skill、§1.14 DAG 无人工审批节点）；`docs/architecture/STRATEGIC_VERDICT.md`（§1 定位、K001/K002/K003 实验证据）；根 `AGENTS.md`（§0 定位与权威声明）。
