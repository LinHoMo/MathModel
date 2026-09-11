# ADR-0008: Problem Understanding Layer Ownership and Runtime Edit Authorization / 问题理解层归属与 runtime 修改授权

- Status / 状态：Accepted
- Date / 日期：2026-09-10
- Context / 上下文：
  AGENTS §5 禁止新增第三方运行时依赖、禁止改动 `src/modeling_harness/runtime/` 业务逻辑；
  ADR-0001 声明自 2026-09-07 起架构冻结，治理例外须经 `docs/architecture/RUNTIME_CONTRACTS.md` 授权。
  但交付实例暴露出一个**能力缺口**（不是架构缺陷）：生产路径没有「赛题文本 → 问题特征」这一环。

  机器实测证据（2026-09-10 工作树）：
  1. `runtime/execution/session.py` 的 `RuntimeSession(features=None)` 在全部生产入口都不传 features；
     `runtime/execution/handlers.py` 的 `DefaultNodeExecutor.__init__` 于是回退 `_LEGACY`
     ——把任何题硬编码成 `problem_types=["evaluation"]`。
  2. 后果同源两症状：`projects/p151-2024a-b0/state/e2e_metrics_report.json` 实测
     `decomposition_coverage=20.0`（金标准 5 问，实际产出 1 问）、
     `structure_alignment=0.0`（纯几何题选出 `mc-monte-carlo`）。
  3. 三份 `projects/cumcm2024a|2026a|2026b` 的 `state/` 四件套由项目内脚本
     `artifacts/code/build_state.py` **手工**构造，未走 runtime 受控路径——说明机制有价值却在生产空转。
  4. `validators/modules/problem_spec_parser.py` 具备子问题切分能力，但对三题真实题面实测
     **全部产出 0 个子问题**（其正则要求「问题N：」带冒号，真实题面是「问题1　」全角分隔或
     「问题 1 」空格分隔），且其 `topic_type` 取值与方法卡 `problem_types` 词汇表不同构
     —— 不能直接充当特征来源（计划中风险 H3 由此证实）。
  5. 三题 `state/status.json` 为扁平结构（无 `state` 嵌套键），与 `runtime/state/model.py`
     的 `ProjectState` 契约不符；`cli/e2e_metrics.py` 读取时抛 `KeyError: 'state'`
     —— harness 自身工具读不了自身交付实例。
  6. 三题 registry 含已退役类型 `narrative`，加载时被跳过并告警。

- Decision / 决策：
  1. **归属**：问题理解（题面 → 子问题分解 + 问题类型 + 检索特征）定位为 **Runtime 前置确定性层**，
     归属 `src/modeling_harness/runtime/modeling/`（与既有 `problem_repr.py` 同子域），
     **不新建顶层目录、不新建 runtime 子域**。理由是它必须 LLM-free、可重放、可审计，
     不能落到可替换的 Constructor 层——否则 features 又变成外部注入的自由变量，根因不消失。
  2. **形态**：新增 `runtime/modeling/problem_profile.py`，导出确定性 `ProblemProfile`；
     `runtime/modeling/problem_repr.py` 的纯文本分支接入同一子问题切分，使逐题
     描述可写入 Question artifact。`question_spec.json` 既有契约不变。
  3. **授权范围（收窄）**：本 ADR 授权改动**仅限**下列文件，且仅限「问题理解链路」意图：
     - `runtime/modeling/problem_profile.py`（新增）
     - `runtime/modeling/problem_repr.py`（纯文本分支增强）
     - `runtime/execution/session.py`（questions / features 缺省派生）
     - `runtime/execution/handlers.py`（`_LEGACY` 回退移除 → fail-closed；选型无特征时 BLOCKED）
     不改 schema、不改 workflow DAG 拓扑、不改 evidence gate、不新增依赖。
  4. **fail-closed 语义**：未取得真实特征时，选型节点返回 BLOCKED 并给出可读理由，
     **禁止**用 `["evaluation"]` 之类的默认标签冒充选型；显式注入的 features 优先于派生。
  5. **不改 DAG 拓扑**：Fidelity / Diagnosis / Revision / Comparison 继续沿用「现有节点内集成」
     （既有实现选择），不新增独立 DAG 节点——该分岔由本 ADR 一并与 ADR-0009 记录，避免后续
     Agent 按旧计划书中「新增节点」的表述重复实现。

- Consequences / 后果：
  - 正面：「输入赛题 → 输出 MODEL_IR」的前馈在无外部 Constructor 时也能闭环；
    分解覆盖与选型命中具备可测量改善；问题理解成为可重放、可审计的确定性层。
  - 负面：`runtime/` 出现一次受控修改（仅限上述四个文件），需在 RUNTIME_CONTRACTS 登记授权；
    `_LEGACY` 移除改变了「无特征也能跑完」的旧行为，依赖旧回退的下游须显式提供 features。
  - 后续义务：新增问题类型标签须同时登记到方法卡 `problem_types` 与 `catalog/model_families.yaml`；
    该层**不得**引入 LLM 调用或第三方依赖。

- Evidence / 证据：
  - `git log -1 --format=%h` 于工作树；`handlers.py` `_LEGACY` 定义与 `session.py` 调用点（机器确认）。
  - 三题实测：`parse_problem_spec` 对 `projects/cumcm2024a|2026a|2026b/inputs/problem.txt`
    均返回 `problems=0`（机器实测输出）。
  - 指标实测：`p151-2024a-b0` → `decomposition_coverage=20.0 / structure_alignment=0.0 /
    computed=3, absent=5`。
  - 结构不符实测：对三题调用 `compute_e2e_metrics` → `KeyError: 'state'`（`runtime/state/model.py`
    `_empty()` 含嵌套 `state` 键）。
  - 退役类型实测：加载三题 `state/registry.json` → 警告 `跳过已退役类型 'narrative'`。
  - `ARTIFACT_TYPES` 中已无 `narrative`（`runtime/artifacts/ids.py`）。
