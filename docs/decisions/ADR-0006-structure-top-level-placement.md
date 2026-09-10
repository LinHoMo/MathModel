# ADR-0006: Structure Top-Level Placement for domains / adapters / retired schemas / 顶层结构归位

- Status / 状态：Accepted
- Date / 日期：2026-09-10
- Context / 上下文：品牌迁移与技术重构（src/ layout）完成后，终审发现三处结构偏离目标：
  1. `runtime/domain/`（Canonical Domain Model 纯定义层，零 import 引用）与目标顶层 `domains/` 不符；
  2. `runtime/constructors/adapters/`（外部 Constructor 适配器：MathModelAgentAdapter / PiAdapter / ReferenceConstructor）与目标顶层 `adapters/` 不符；
  3. `schemas/legacy/`（V2 schema 归档）目录名含 "legacy"，与"无历史兼容"的品牌承诺冲突，且 validate L1.1 曾依赖其 `question_spec.schema.json` 存在性（历史基线 44/1 中那个失败即由此路径引起）。
  另：P3-4 曾记录"目录重组：评估后暂缓（顶层大迁移 import 回归风险 > 收益，改渐进式）"，本 ADR 在人工确认"目录结构的变化也要搞，要搞的彻底"后推翻该暂缓决定。
- Decision / 决策：
  1. `git mv src/modeling_harness/runtime/domain src/modeling_harness/domains` —— Canonical Domain Model 归位顶层 `domains/`（纯定义层，零行为不变）；同步更新 `runtime/contracts.py` 与 `docs/architecture/CANONICAL_DOMAIN.md` 的代码真源路径。
  2. `git mv src/modeling_harness/runtime/constructors/adapters src/modeling_harness/adapters` —— 外部 Constructor 适配器归位顶层 `adapters/`；`tests/unit/test_constructor_adapters.py` 三处 import 同步更新。`runtime/constructors/` 仅保留 protocol / registry / __init__（运行时注册契约，不 import 具体 adapter）。
  3. `git mv src/modeling_harness/schemas/legacy src/modeling_harness/schemas/retired` —— V2 schema 归档更名为 `retired/`（只读归档，非运行时真源）；目录内 README 同步更新。
  4. validate L1.1 语义修复：不再检查 V2 归档 `question_spec.schema.json` 存在性，改为校验活跃项目真实输入规约（`inputs/question_spec.json` 有效 JSON 且顶层 object，或 `inputs/problem.txt`；两者皆缺 → 失败；库模式无活跃项目 → 跳过），与 `runtime/modeling/problem_repr.py` 解析契约一致。
  5. `runtime/execution/adapters/`（执行适配器：LocalPythonAdapter 等）与顶层 `adapters/`（Constructor 适配器）语义不同，**保持原址不动**。
  6. 目标结构中的 `profiles/`（competition/research）与 `domains/` 子域（optimization/statistics/differential_equations/machine_learning/inverse_problems）、`adapters/` 子目录（llm/solver/notebook/export）：当前无实现资产，**不建空壳目录**；待有真实模块时按本 ADR 的命名规范落位。
- Consequences / 后果：
  - 正面：目录结构对齐目标顶层布局；"legacy" 兼容歧义消除；validate L1.1 从"守卫 V2 归档"变为"守卫 V3 真实输入规约"（45 项校验项数不变，语义真实）。
  - 负面：`constructors/adapters` 路径变更属一次性破坏性移动（项目无运行时兼容承诺，符合 V3 无向后兼容定位）；`domains/`、`adapters/` 成为顶层包后，后续新模块须按职责归位。
  - 后续义务：新增领域/适配器/档案模块时参照本 ADR 命名规范；不恢复 `legacy/` 命名。
- Evidence / 证据：
  - `git mv` 后文件存在性：`src/modeling_harness/domains/__init__.py`、`src/modeling_harness/adapters/mathmodel_agent.py`、`src/modeling_harness/schemas/retired/question_spec.schema.json` 均存在（机器确认）。
  - 引用面实测：`constructors/adapters` 外部引用仅 `tests/unit/test_constructor_adapters.py`（3 处 import）；`runtime/domain` 零代码 import，仅 `contracts.py` / `CANONICAL_DOMAIN.md` 文档路径引用（已同步）。
  - validate 实测：`py -3.12 src/modeling_harness/cli/validate.py` → 45 通过 / 0 失败 / 0 警告。
  - L1.1 四场景函数测试：valid spec=True / missing=False / bad json=False / problem.txt=True（机器实测）。
  - 历史基线：worktree @9809047 实测 44/1（L1.1 指向失效归档路径）→ 本 ADR 修复后 45/0。
