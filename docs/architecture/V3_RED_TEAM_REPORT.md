# V3 Red Team Report — P9.5 跨层完整性审计

> 攻击范围：Plan → Evidence → Decision → Quality → Rerun 十个攻击面。
> 方式：对抗测试先行（`tests/integration/test_red_team.py`，23 项），跑出真实
> 失败 → 只修证实的真 bug（不放宽语义）→ 全部发现按六类归类。
> 最终：**pytest 653 passed, 0 failed；validate 57/57；catalog OK；doctor 0 blocking。**

## 1. Attack Surface（攻击面覆盖）

| # | 攻击面 | 测试 |
|---|--------|------|
| 1 | Plan → Evidence（计划是否真被执行 / hypothesis 是否进证据 / 计划 V2 与 V1） | RT1–RT3 |
| 2 | Evidence → Decision（失效证据的六处消费方逐一检查） | attack2 |
| 3 | Decision → Quality（当前事实 vs 创建时快照） | R3/D4 |
| 4 | Quality → Rerun（旧报告污染 / 跨谱系证据 / 混谱系 DecisionLog） | R11×2 |
| 5 | Rerun → Evidence（retry/resume/rerun/recompute 四语义必须不同） | R4/R5/R6/R7 |
| 6 | Crash → Resume（7 个切点恢复同一世界 / 不重算新 ID） | crash×5 |
| 7 | Quality → Research State（WEAK/FAIL 对问题状态的影响） | state×2 |
| 8 | Competition Pack 污染（偏好 ≠ 真值） | R9 |
| 9 | Knowledge → Quality 反向污染（循环论证） | R10 |
| 10 | 完整闭环 + 中途注入（失效/崩溃/rerun 组合） | e2e |

## 2. Invariants（12 条全部落为测试）

R1–R12 全部通过。其中 R1/R2/R5/R8/R9/R10/R12 的防线在红队前即成立
（P7/P8/P9 既有契约），22 项直接通过；**R3/R4/E8 相关防线被攻破**，见 §4。

## 3. Cross-Layer Scenarios

* 失效传播的六处消费方（EvidenceGraph/DecisionLog/QualityReport/ResearchState/
  PaperProjection/FailureMemory）逐个验证：claim 被传播判死 ✓、coverage 不计死
  claim ✓、投影排除死主张 ✓、Gate 剪死边 ✓——**一处失败**：ResearchState 的
  问题状态不因 claim 死亡而回退（见 §7 设计债 SD-2）。
* Crash→Resume 在 after_plan/after_model/after_experiment/after_evidence 切点
  全部重建同一世界（Artifact 集合 + 关系逐项相等）。

## 4. Bugs Found（真 bug，均已修复）

| ID | 缺陷 | 根因 | 修复 |
|----|------|------|------|
| B1 | **E8 死循环**：实验链重建后 Evidence Gate 永久 WEAK（E6 需复查） | invalidation 传播标记（requires_revalidation/dirty）只写不清——reval 语义说"需复查"，但复查通过后无人清除 | `_clear_revalidation_marks()`：链重建（fresh）与复验（reuse）时对活跃产物调用 `clear_invalidation()`（终态不可清，lifecycle fail-closed 保持） |
| B2 | **计划↔执行断链**：experiment 无 plan_ref/hypothesis_ref，且依赖内存 shared（resume 后必然断链） | S1 不变量残留违规 | `_plan_artifact_for()` Registry 派生；experiment 创建携带 plan_ref/plan_entry/hypothesis_ref；reuse 分支回填缺失 provenance |
| B3 | **重跑后双 active 实验计划**：新计划落地旧计划仍 active，`_plan_for` 可能取到旧计划 | do_experiment_design 未退役旧计划 | 新建前 supersede 同模型依赖的旧计划（审计保留） |
| B4 | **R3 违规：双 active 选型决策**——确定性重选型（同 chosen）也产生第二条 active 决策 | select() 只记录不退役旧决策 | select() 落地后自动 invalidate 同问题旧 active 选型决策（invalidated_by=新决策） |
| B5 | **DecisionLog 从未持久化**（P9 期间发现，红队确认影响所有决策消费者） | session.checkpoint 遗漏 | checkpoint 补 decisions.save() |

## 5. Contract Violations

**无。** P7（生命周期/四分执行语义）、P9（Quality 四态/Pack 只读）契约本身
未发现内部矛盾。B1 属于契约的**实现遗漏**（clear_invalidation 已存在于
Artifact API 但无调用方），不构成契约缺陷。

## 6. Test Defects（已修）

* R6 测试在已完成的 session 上打补丁——flaky 永不触发（改为 run=False）。
* `test_prior_invalidated_decision_not_conflicting` 在 R3 修复后手动 invalidate
  变成双重推翻（改为断言自动失效）。
* resume 测试未排除 quality memory 决策（D 前缀是合法新增，不是重算产物）。

## 7. Architecture Risks → Accepted Risks / Remaining Debt

### Semantic Debt（同实体跨层歧义——本项目当前最大风险类）

| SD-# | 歧义 | 现状 | 处置 |
|------|------|------|------|
| SD-1 | "experiment" 三义：ExperimentEntry（计划条目）/ experiment Artifact（执行记录）/ legacy pipeline 实验概念 | plan_ref/plan_entry/hypothesis_ref 已把执行挂回计划，但条目级映射只记首条 entry | P10 接真实实验执行时按 entry 逐一落 Artifact |
| SD-2 | "validated" 问题状态 vs Quality WEAK/FAIL：state 晋级不考虑质量判定，WEAK 后问题仍 validated | **显式设计决定**（advisory 不阻断确定性流程），测试记录在案；若改须先改契约文档 | P10 决策：要么 Quality FAIL 参与 refresh_from 晋级条件，要么维持现状并写死文档 |
| SD-3 | "current decision"：DecisionLog status=active ≠ "当前生效"——R3 修复后单选型场景唯一，但不同问题/类型的 active 决策共存合法 | 按问题前缀区分 | 已足够；跨类型 active 共存是审计语义 |
| SD-4 | "evidence independence"按"同一产出实验"近似，未覆盖共享数据集/共享假设的弱独立 | EQ-independence 现规则 | P10 扩展 uses/assumes 共享检测 |

### Accepted Risks

* deterministic handler 的 decision_rule 判定（ACCEPT/REJECT 落库）未实现——
  无真实数值可判；P10 接真实实验执行时补（I3/I5/E7 的 UNKNOWN 即此占位）。
* `claim.data.compared_against` 无人写入 → CQ-baseline 常驻 advisory。

## 8. Fixed Issues（本轮修复清单）

B1–B5（§4）+ 3 项测试缺陷（§6）+ `catalog_check` validator 路径兼容包型目录
（P9 遗留）。全部修复均未放宽任何既有语义；test_model_selection 的一处断言
按新契约更新（自动失效替代手动失效）。

## 9. Accepted Risks（维持现状 + 理由）

见 §7 Accepted Risks。另：quality_evaluation 的 WEAK/UNKNOWN 为 advisory
不阻断——替代方案（WEAK 也触发重建）在同输入下必然死循环，违反确定性原则。

## 10. Remaining Debt → P10

1. SD-1 条目级执行映射（真实实验执行时补齐）。
2. decision_rule 结果回填（ACCEPT/REJECT/REFINE 判定落 Artifact/Evidence）。
3. SD-2 的 Quality↔State 晋级语义决策。
4. SD-4 弱独立性检测。
5. 16 张卡中 12 张的 applicability/risk 仍未 enrich（P8 遗留，按需补）。
