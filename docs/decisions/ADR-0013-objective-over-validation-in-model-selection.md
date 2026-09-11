# ADR-0013: 模型选择必须比目标函数值，基线对照链必须闭环

- Status / 状态：Accepted
- Date / 日期：2026-09-11
- Context / 上下文：

  一份外部评审指出：本仓「验证工程很强，但模型本身中等」，尤其缺 **model competition /
  baseline / optimality gap**。逐条核验后，结论需要被**精确化**（外部断言不因格式完整而采信）：

  **框架层并不缺机制，缺的是闭环。** 现存三件东西彼此不接：

  1. `runtime/modeling/planner.py:150` 会在计划里**声明**「朴素基线（均值/最近值/穷举小规模等
     同口径对照）」这条 `baseline_comparison` 要求；
  2. `runtime/evaluation/deterministic_metrics.py:115` 有 `baseline_comparison()` 函数，
     比较两个 execution outputs；
  3. `runtime/execution/handlers.py:1881` 会在计划声明了 `baseline_comparison` 时，给结果
     artifact **打上 `baseline` 标签**。

  但 `baseline_comparison()` 在 `src/` 与 `tests/` 内**零调用点**（只有定义、以及 planner 的
  同名字段与 handlers 的字面量标签）。也就是说：**计划声明了对照、产物被打了对照标签、
  而对照从未真正执行** —— 一条被声明、被标记、却从不产出数值的静默失效链。

  同时两处度量语义缺陷：
  - `baseline_comparison()` 的 docstring 承诺按目标方向给出 `better: "a"/"b"`，**实现只返回
    `"tie"` / `"different"`** —— 无法回答「谁更好」，也没有 minimize/maximize 方向，
    更没有 gap（绝对差与相对百分比）的量化；
  - `runtime/modeling/comparison.py::compare_models()` 在两模型都通过验证时，判定「更优」的
    依据是 **`checks_passed` 更高**。这会把**验证做得更细的模型**判为更优，而不管其目标函数
    值是否更好 —— 即「Model Quality 被 Validation Quality 替代」，与评审指出的现象在机制上
    完全对应。

- Decision / 决策：

  1. **`baseline_comparison()` 必须能判定优劣并量化 gap。** 新增目标方向参数
     （`direction="minimize"|"maximize"`，可对单个 key 覆盖），返回 `better: "a"|"b"|"tie"|
     "incomparable"`，并对每个比较键给出 `abs_gap` 与 `rel_gap`（相对基线）。docstring 与
     实现必须一致。
  2. **基线对照链必须闭环。** 计划声明了 `baseline_comparison` 时，执行路径必须**真正调用**
     该函数并把结果落进产物（而非只打标签）。未实际执行不得打 `baseline` 标签——
     标签是执行的回执，不是声明的同义词。
  3. **模型选择不得以验证检查数替代目标函数值。** `compare_models()` 在两侧均有
     `objective_value` 时，必须优先按目标方向比较目标值；仅在目标值不可得时才回退到
     验证质量（且须在返回中显式声明回退原因）。
  4. **门禁侧加守卫**：plan 声明了 `baseline_comparison` 而结果中无实际对照数值时，
     校验应判失败（而不是静默通过）。

- Consequences / 后果：

  正面：
  - 「模型是否更好」有了可机检的定义，不再由验证检查数代偿；
  - 静默失效链被掐断：声明、执行、标签三者一致；
  - 评审指出的 optimality gap 有了落点 —— 每个模型都可与朴素基线给出相对差距。

  负面 / 约束：
  - 需要为每个问题定义「朴素基线」与「目标方向」，这是一项建模判断，不能自动生成；
  - 若某模型的 execution outputs 未携带可数值化的目标量，对照会退化为 `incomparable`——
    这是**如实报缺**而非失败，不得为凑结果编造基线数值。

  后续义务：
  - 修改 `runtime/` 下上述文件须引用本 ADR；
  - 新增「模型选择 / 基线对照」类能力时，须同时补守卫测试。

- Evidence / 证据：

  - 零调用点：`grep -rn "baseline_comparison" src/ tests/ --include=*.py` 命中仅
    `deterministic_metrics.py`（定义）、`planner.py`（同名字段与说明）、`handlers.py:1881/1944`
    （字面量标签 `("baseline", "baseline_comparison")`），无任何函数调用。
  - 实现与 docstring 不一致：`deterministic_metrics.py:115-160`，`better` 仅取
    `"tie"` / `"different"` / `"incomparable"`，docstring 却写 `"a" / "b"` 与
    `objective_less_is_better` 翻转。
  - 判定依据错位：`comparison.py::compare_models` 的 `elif m1.get("valid") and m2.get("valid")`
    分支按 `checks_passed` 多寡决定 `better`。
  - 实例侧佐证：`projects/cumcm2026b/model.md` 内 `grep -n "baseline|最优性差距|optimality|下界"`
    **零命中** —— 该实例（Q1–Q4 四个问题）从未报告过与任何基线的差距。
