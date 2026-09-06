# P13-3 Report — Model Construction 首测（三维基线）

> 日期：2026-09-06 · 核心问题：**选对方法以后，Agent 能不能把数学模型正确地
> 建立出来？** 测量对象 = P13-0 真实求解产出的模型（`projects/bench-m4-2000c/
> output/MODEL_SPEC.md` + `figures/all_results.json`）。
> 禁令生效：本轮不碰 Cross-question synthesis / 新 Relation / 新 IR /
> 新 Validator / 新 Artifact / Agent 数量扩张——只在 Brain/Knowledge/
> Evaluation 层工作。

## 1. 测量仪（预注册后打分）

- **Rubric**：`core/knowledge/bench/e2e/mc_2000C.json`（v1，打分前落盘）——
  按任务类型定义结构组件（估计/干预模拟/韧性模拟/泛化各不同），对齐点 =
  题目要求 → 模型元素的强制映射，数学错误分类学（7 类，权重 5-15）。
- **评分器**：`core/tools/evaluation/model_construction.py`（确定性重算，
  fail-closed 校验：未知组件/越索引/未知错误分类直接报错）。
- **口径披露**：scorecard 由 agent 对照 rubric 自评、证据指针可审计
  （`projects/bench-m4-2000c/work/mc_scorecard.json`）——与 P13-0 的
  model_correctness 同一自评模式；后续轮次可引入独立评委打破自评环。

## 2. 三维基线（2000C）

| 维度 | 值 | 构成 |
|---|---|---|
| Structural correctness | **80** | 组件 20/20 齐全；−2×10 结构级一致性问题（校准乘子不确定性未传入泛化表；生存率口径与年龄结构口径未统一交叉引用） |
| Mathematical correctness | **55** | 5 项扣分：校准不合理性 15（m=4.42 → 幼龄份额 61% 人口学不合理）+ 缺失约束 2×10（密度制约/搬迁能力）+ 未陈述假设 5（避孕效期）+ 边界 5（70 岁截断） |
| Problem alignment | **100** | 10/10 对齐点命中——模型回答了题目（含 Task3 权衡、Task5 报告支撑） |
| **Composite（等权）** | **78.3** | 校验零错误 |

## 3. 读数解读（诚实版）

- **对齐满分 ≠ 高枕无忧**：本模型"回答了题目"，但 **mathematical 55 是
  三维最低**——结构齐全、方向正确，但校准合理性（61% 幼龄份额）与缺失
  约束（密度制约/搬迁能力）是实打实的数学缺陷。这正是三维拆开的价值：
  单一 composite 78.3 会掩盖"结构好、数学弱"的短板分布。
- **alignment 100 的含金量受自评环限制**：agent 既造模型又判对齐——
  P13-3 后续轮次应引入 rubric 交叉出题（用未见过的题打分）来破环。
- 与 e2e `model_correctness`（基线 70，自评）的关系：P13-3 三维 composite
  是其细化替代，后续 e2e 运行可直接以 mc composite 作为
  model_correctness_pct 输入。

## 4. Δ 改进回路（P13-3 剩余目标）

| 候选改进 | 预期维度 | 验证方式 |
|---|---|---|
| 幼体存活与校准口径一致化（消解 61% 幼龄份额矛盾） | mathematical +15 | 同 rubric 重打分 |
| 密度制约（承载力 K）入模 | mathematical +10 | 同上 + 2023C 复测防过拟合 |
| 校准不确定性传播到泛化表 | structural +10 | 同上 |
| 未知新题对齐测试（破自评环） | alignment 可信度 | 新题 rubric + 独立打分 |

Exit criteria（P13-3）：≥3 题（含未见题）三维基线齐全，且 mathematical
或 alignment 之一 +10 个百分点；composite 成为 e2e model_correctness 的
正式输入。

## 5. 禁令重申

本轮及 P13-3 全程：不碰 Runtime（synthesis/relation/IR/validator/artifact/
agent 扩张全部冻结）。测量仪 `model_construction.py` 属 Evaluation 层。
