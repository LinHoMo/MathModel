# ADR-0014: 候选选型必须以目标函数值为首要依据（延伸 ADR-0013 到 P1-M3 路径）

- Status / 状态：Accepted
- Date / 日期：2026-09-11
- Context / 上下文：

  ADR-0013 确立了「模型选择不得以验证检查数替代目标函数值」，但它只落在了
  `runtime/modeling/comparison.py::compare_models` 一处。真正跑生产的选型节点是
  P1-M3 的 `model_selection_decision`（`runtime/execution/handlers.py::do_model_selection_decision`），
  它走的是 `DefaultNodeExecutor._rank_candidates` 这条独立的排序键。

  `_rank_candidates` 的排序键为
  `mathematical_valid → constraint_violation_max → execution_valid → 域合规 →
  empirical_valid → mir_id`，**完全不读 `objective_value`**。后果：两个都合规
  （`constraint_violation_max=0`）的候选，由 `mir_id` 字典序决胜 —— 目标函数值更优者
  可能落选。即 ADR-0013 想根除的「模型质量被验证质量替代」，在生产选型路径上仍然存在。

  项目级 `projects/cumcm2026b/artifacts/code/candidate_select.py`（M-SELECT-001）已在真实任务
  上实现并验证了正确的选择器（feasibility gate → objective → 配对显著性），但它是
  `projects/` 内的脚本，未回灌到框架层 —— 因此只对该实例生效，harness 本身仍带缺口。

- Decision / 决策：

  1. **`_rank_candidates` 引入 objective-first 排序**：在原键的
     `constraint_violation_max` **之前**插入
     `(有目标值标志, 目标值按 objective_direction 归一)` 两项。`mathematical_valid`
     仍是首要键（可行性先于最优性），无证据候选恒排最后；`objective_value` 缺失或
     为 NaN/Inf 的候选排在有名者之后，不得因不可比值抢先。
  2. **`SELECTION_CRITERIA` 登记 `objective_value` / `objective_direction`**，
     使选型决策的 `criteria` 字段如实反映「以目标值为首要依据」。
  3. **选型 reasoning 说明目标值依据**：最优候选有目标值时，`reasoning` 报目标值
     与方向；落选者优先按目标值给出「劣于」对照，目标值不可比时回退到
     `constraint_violation_max` 对照。目标值不可得时显式标注「回退验证质量」。
  4. 边界：本 ADR 不改变 `chosen` 的 UNSELECTED 语义（无证据仍 UNSELECTED），
     也不引入新的候选生成机制；只修正「可行候选之间如何判定更优」。

- Consequences / 后果：

  正面：
  - ADR-0013 的判据在生产选型路径上闭环，不再只覆盖 `compare_models`；
  - 「目标值更优但 id 靠后」的候选不再被字典序淘汰（对应缺陷有 RED 测试锁定）；
  - 目标值缺失时仍可回退验证质量，但回退在 reasoning 中可审计。

  负面 / 约束：
  - 排序依赖候选 VR 证据携带 `objective_value` / `objective_direction`；未携带者
    退化到验证质量排序（如实标注，不得为凑比较编造目标值）；
  - 修改 `runtime/execution/handlers.py` 的选型路径须引用本 ADR。

- Evidence / 证据：

  - 缺口（RED 锁定）：`tests/unit/test_selection_objective_rank.py` —— 首跑 5 failed /
    3 passed（`test_minimize_prefers_smaller_objective` 等 4 项 objective 用例 + NaN 用例
    失败，证明旧 `_rank_candidates` 不读目标值）；实现后 8 passed。
  - 排序键原件：`runtime/execution/handlers.py::_rank_candidates`（改动前键无
    `objective_value` 项）。
  - ADR-0013 覆盖范围：`docs/decisions/ADR-0013-objective-over-validation-in-model-selection.md`
    决策 3 仅点名 `comparison.py::compare_models`。
  - 项目级已验证实现：`projects/cumcm2026b/artifacts/code/candidate_select.py`
    （feasibility → objective → paired significance，M-SELECT-001，commit `a147a1d`）。
