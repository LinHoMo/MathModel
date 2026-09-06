# Three-Layer Architecture — 三层架构与方向门禁（2026-09-06 起）

> 本文件是项目方向的**治理文档**：把全部资产归位到三层，宣布下层冻结，
> 并立下后续所有开发的准入门禁。背景：P7–P12 完成了 Runtime 与 Guardrails
> 的地基建设；继续向下挖掘只会得到一个"科研操作系统"而不是"数模 Agent"。
> 自本文件起，研发主战场是 **Agent Brain**，度量工具是**能力基线**。

## 1. 三层结构

```text
                 ┌────────────────────────────┐
                 │        Agent Brain         │
                 │                            │
                 │ Problem → Model → Experiment│
                 │ → Validation → Writing     │
                 └─────────────┬──────────────┘
                               │
                         Research Runtime
                               │
                 ┌─────────────┴──────────────┐
                 │ Registry / Workflow / State │
                 │ Evidence / Recovery        │
                 └─────────────┬──────────────┘
                               │
                           Guardrails
                               │
                 ┌─────────────┴──────────────┐
                 │ Quality / FactCheck / Gate │
                 └────────────────────────────┘
```

## 2. 资产归位

| 层 | 资产 | 规模 | 状态 |
|---|---|---|---|
| **Agent Brain** | `core/<Hand>/agents/*/SKILL.md`（29 agent 指令）、`core/skills/critics/*`、知识层（16 方法卡 / 10 失败案例 / 6 创新模式 / retriever / decision log）、`knowledge.py recommend`、Modeling 层（ExperimentPlanner / candidate arena） | ≈3.5 万行指令 + 知识层 | **主战场**（P13–P17 全部投入于此） |
| **Research Runtime** | `core/runtime/`：Artifact Registry、Evidence Graph、State、Workflow DAG / WaveExecutor、RuntimeSession、retry/resume/rerun/invalidation、P12 依赖/关系/跨问题上下文、legacy 适配 | ≈8.4 千行 | **冻结** |
| **Guardrails** | `core/validators/modules/`（21 模块 L1–L6）、gate/gatelib、citation_check、writing_check、fact_check、hash_chain、score_compute → aggregate_scores 五维评分链 | ≈7 千行 | **冻结**（仅修 bug） |

事实基线（2026-09-06）：Runtime 与 Guardrails 全部为确定性 Python（零 LLM
调用）；Brain 的"智能"由宿主 LLM 会话按 SKILL.md 执行。因此"让 Brain 变聪明"
的工作 = 改进指令与知识层 + 用真实赛题测量宿主 LLM 在此脚手架上的解题表现。

## 3. 冻结声明（change-by-exception）

- **Research Runtime 冻结**：P7–P12 的全部契约（Registry 生命周期、Evidence
  Graph 14 关系、P7 resume/rerun/recompute、P8 知识运行时、P9 质量层、
  P10 Paper Intelligence、P11 Expression Contract、P12 依赖/关系/上下文）
  交付即冻结。契约文本见各 `*_CONTRACT.md` / `RUNTIME_CONTRACTS.md`；
  P12 收口见 `CROSS_QUESTION_SYNTHESIS_CONTRACT.md`。
- **Guardrails 冻结**：仅接受 bug 修复与误报修正，不接受新语义层。
- 例外流程：出现**真实需求**（来自真实赛题执行，而非推演）→ 按下节门禁
  评估 → 修订契约文档 → 再动代码。禁止"顺手加固"。
- **已批准例外登记**：
  - 2026-09-06 `handlers.features_for()`（~6 行，P13-1 Problem→Method
    接口，Q1 门禁通过）：`RuntimeSession(features)` 现有插座的逐题画像
    合并。见 `P13_1_REPORT.md`。
  - 2026-09-06 `validate.py _live_project_dirs` 误报修正：bench e2e 基线
    项目不适用论文交付门禁。见 `BASELINE_REPORT.md`。
  - 2026-09-06 `retriever.py` 类型命中权重 +3→+6（P13-2 Ranking 修正，
    Q1 门禁通过）：两题消融 + 评价类反向检查 + 零测试回归验证。见
    `P13_2_REPORT.md`。

## 4. 三问门禁（每个新阶段 / 能力 PR 的准入检查）

> **Q1** 它是否提升 Agent 的科研解题能力？
> （更好的问题分解 / 方法选择 / 建模 / 实验设计 / 结果解释 / 论文表达）
>
> **Q2** 它是否让 Agent 更可靠？
> （crash 后可恢复、结果可追溯、错误可归因）
>
> **Q3** 它只是让内部语义更严谨吗？
> （新增契约 / 中间层 / 关系系统，但没有直接提高 Q1 或 Q2）

**裁决规则：仅 Q3 成立 → 不做**（最多写进文档）。Q1 或 Q2 成立 → 做，
且必须定义它的能力指标与预期 Δ。

## 5. 能力进步判据（Δscore 论英雄）

自 P13 基线（`BASELINE_REPORT.md`）建立起，**任何能力升级 PR 必须回答：
相比 BASELINE，哪个能力指标提升了、提升多少**。八项指标定义见
`CAPABILITY_ROADMAP_P13_P17.md` / `bench e2e`：

```text
decomposition / method selection / model correctness / experiment validity
/ validation reliability / innovation / writing completeness / end-to-end
```

- `method selection 42% → 57%（+15）` = 实打实的进步；
- `新增 800 行 / 新增 37 tests / 新增 5 contracts` 但
  `end-to-end 31% → 31%` = **判定为没有能力进步**。
- 测试数量的意义是守住下层冻结的两层不回归，不再作为进度度量。

## 6. 路线图指针

P13–P17 见 `CAPABILITY_ROADMAP_P13_P17.md`（Capability Roadmap，非
Runtime Roadmap）。基线数据见 `BASELINE_REPORT.md`。
