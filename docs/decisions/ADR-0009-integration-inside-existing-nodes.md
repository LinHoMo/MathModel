# ADR-0009: Runtime Integration Inside Existing Nodes instead of New DAG Nodes / 机制在既有节点内集成而非新增 DAG 节点

- Status / 状态：Accepted
- Date / 日期：2026-09-10
- Context / 上下文：
  早期重构方案（`research/P15/analysis/ARCHITECTURE_FINAL.md` §3、`docs/architecture/STRATEGIC_VERDICT.md` Q11）
  主张把 Fidelity / Failure Diagnosis / Revision Draft / Model Comparison 提升为**独立 DAG 节点**，
  机制外显于图结构，便于观测与拆分。
  实际演进选择了另一条路——在既有 16 节点内部集成：

  | 能力 | 落地位置 | 锚点 |
  |---|---|---|
  | Fidelity | `do_model_execution` 内 | commit `2e6662a` |
  | Failure Diagnosis | `do_model_validation` 内 `_diagnose_and_draft` | commit `311a863` |
  | Model Comparison | `_compare_revision_chain` | commit `c4809d0`/`45a6390` |
  | Revision Loop | `_auto_revision` | commit `627598e`（标题明写「节点内」） |
  | Knowledge Guided | `_apply_knowledge_guide` | commit `cf5970c` |

  同时 `handlers.py:262` 留下一条自述教训：「只登记 `revision_of` 谱系边；`supersedes` 边与
  旧模型状态迁移由修订收口唯一负责……单一真源，避免双路径重复加边（GraphError）」。
  即：若再补一个 revision DAG 节点，等于重新引入第二条写边路径。

  该分岔此前**没有任何 ADR 记录**，导致「文档说该加节点、代码里没有节点」的持续歧义
  （架构审查报告列为风险 3/5）。

- Decision / 决策：
  1. 维持**节点内集成**为既定实现路线，不新增 Fidelity / Diagnosis / Revision / Comparison 独立 DAG 节点。
  2. 理由一（真源唯一）：写边路径必须唯一。新增节点会让 `supersedes` / `revision_of` 需要跨节点协调，
     重新打开双路径加边缺陷面。
  3. 理由二（可观测性以别的方式取得）：节点内集成的可观测性由 evidence artifact
     （`diagnosis` / `decision` 登记 + `diagnosed_by` / `compared_with` 边）与节点 reason 文本承担，
     不依赖 DAG 拓扑膨胀。
  4. 边界：**本条不禁止**未来新增 DAG 节点；它只声明「为集成既有能力而新增节点」不是当前选择。
     若未来确需新节点（例如引入需要独立重试语义的长任务），须另写 ADR 并给出写边路径设计。
  5. `handlers.py` 的规模问题（2124 行 / 70 方法）与本 ADR 解耦：拆分是**文件内重组**，
     不改变节点边界，作为独立任务处理。

- Consequences / 后果：
  - 正面：关闭「文档–代码方法论分岔」的歧义源；写边单真源原则被显式记录，后续 Agent 不会再按旧计划
    补一个 revision 节点；`handlers.py` 的体量问题与架构决策解耦，可单独治理。
  - 负面：机制内隐于 `DefaultNodeExecutor`，纯看 DAG 拓扑无法发现这些能力；须依赖
    `docs/STATUS.md` 的能力清单与 evidence artifact 才能观测。
  - 后续义务：新增此类能力时，在节点内集成并留下 evidence artifact，不要靠新增节点表达。

- Evidence / 证据：
  - `git log --follow --oneline -- src/modeling_harness/runtime/execution/handlers.py` 中的
    `2e6662a` / `311a863` / `c4809d0` / `45a6390` / `cf5970c` / `627598e`（机器确认）。
  - `handlers.py` 中 `_diagnose_and_draft` / `_compare_revision_chain` / `_auto_revision` /
    `_apply_knowledge_guide` 方法存在（机器确认）。
  - `handlers.py:262` 区注释原文（双路径加边 GraphError 教训）。
  - `docs/STATUS.md` 记录 P0-1/P0-2/P1-2/P1-3 均「✔ 完成」。
