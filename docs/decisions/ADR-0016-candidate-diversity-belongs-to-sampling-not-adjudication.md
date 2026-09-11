# ADR-0016: 候选多样性属于「采样与预算」层，不属于「裁决」层

- Status / 状态：Accepted
- Date / 日期：2026-09-11
- Context / 上下文：

  一次外部提案指出：Harness 擅长筛出「正确、可证明、可执行」的模型，但选择压力会把它
  推向「稳健保守的局部最优」。本 ADR 记录对该命题的**机器核验结果**与据此做出的决策。

  核验（全部 file:line 可复核）——命题成立，且机制比「奖励偏保守」更尖锐：
  **收敛发生在证据产生之前。**

  1. `runtime/modeling/candidates.py:177` `CandidateArena.generate_candidates` 生成 4 类候选
     （baseline / improved / hybrid / innovation）；
  2. `runtime/modeling/candidates.py:322-324` `rank()` 的排序键是 `(-score, candidate_id)`，
     而 `score` 全部来自**先验**：`:196` baseline = 检索分、`:220` improved = +2、
     `:241` hybrid = max−2、`:265` innovation = 检索分 + novelty − cost。
     **无一项来自执行证据或目标函数值**；
  3. `runtime/execution/handlers.py:1789` 把 rank 结果写入 `shared[qid]["candidates"]`；
  4. `runtime/execution/handlers.py:1876-1879` `do_experiment_design` **只取 `cands[0]`**；
  5. ⇒ 除第 0 名外，其余候选（含**全部** innovation 候选）**从未被实例化、从未执行、
     从未产生证据**。

  于是「选择」发生在还没有目标值的时刻——这正是 ADR-0013 想根除的形态，只是位置从
  「执行后排序」前移到了「执行前闸门」。ADR-0014 只覆盖了执行后的 `_rank_candidates`。

  另有一处**确定性缺陷**（非设计选择）：`handlers.py:1880-1885` 重建 `Candidate(...)` 时
  **未传 `innovations`**，而 `candidates.py:75` 该字段默认 `[]`，导致
  `runtime/modeling/planner.py:184` 的创新专用分支 `for inno in candidate.innovations`
  恒空转——`decision_rule=gain > cost`、`failure_detection=inno.risk[0]`、
  `baseline="未采用创新的 <card> 基线"` 永不生成；创新要求只以普通字符串残留在
  `required_experiments` 中，从「创新验证」降级为「候选方案要求」。

- Decision / 决策：

  1. **候选序列化必须保真**：新增 `Candidate.from_dict()` / `InnovationCandidate.from_dict()`
     与既有 `as_dict()` 对称；`runtime/execution/handlers.py` 的重建路径必须走它，
     不得再手写 `Candidate(...)` 字段子集（漏字段即静默降级）。
  2. **多样性只保证在「采样与预算」层，不得进入「裁决」层。**
     明确**否决**配额制（「selection 必须保留 1 Safe / 1 Strong / 1 Speculative」）：
     把没有证据的候选强制带进裁决，会同时违反 ADR-0013（不得以非目标值因素替代目标值判定）
     与本提案自设的第 6 条原则（Correctness 为硬门、其余按证据竞争）。
     允许的做法是：给不同候选**各自的执行预算**，让它们都产生真实证据，然后**仍按证据裁决**。
  3. **novelty 只能作为并列观测**：可写入 decision artifact 的观测字段供审计，
     **不得参与胜负判定**（守 ADR-0013）。
  4. **候选必须先成为可执行 MIR 才谈「进执行」**：core 是 LLM-free 的，候选的方法组合
     不自动等于可执行模型；不得为凑「多候选」而伪造执行产物或证据。

- Consequences / 后果：

  正面：
  - 创新候选的信息不再在重建处静默丢失（含 validations / dependencies / assumptions）；
  - 「保守偏移」有了可机检的入口（候选保真 + novelty 观测 + 执行预算），
    而不是靠新增一个不参与裁决的角色；
  - 明确「探索」与「裁决」的分界，避免用配额冒充探索。

  负面 / 约束：
  - 修改 `runtime/modeling/candidates.py`、`runtime/modeling/planner.py`、
    `runtime/execution/handlers.py` 的相关路径须引用本 ADR；
  - 多候选真实进执行会**增加执行预算**（每候选一次执行 + 验证），
    须在计划里显式声明预算上限，不得默认无限扩张。

- Evidence / 证据：

  - 缺口（RED 锁定）：`tests/unit/test_candidate_plan_fidelity.py`；
  - 排序键与 score 来源：`runtime/modeling/candidates.py:196/220/241/265/322-324`；
  - 只取第 0 名：`runtime/execution/handlers.py:1876-1879`；
  - 重建丢字段：`runtime/execution/handlers.py:1880-1885` + `candidates.py:75`
    + `runtime/modeling/planner.py:184`；
  - 项目 backlog 同项：交接文档「下一步 4：把 baseline_comparison 接进 CandidateArena
    的自动淘汰」——与本 ADR 是同一件事的两端。
