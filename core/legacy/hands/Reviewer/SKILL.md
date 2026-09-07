---
name: reviewer
description: '评审手编排器：串联 5 个评分员 + weakness-hunter + revision-planner + revision-executor，共 8 个 agent。5 人评审团（学术/工程/评委/读者/对抗）加权投票，最低分否决制。评分由脚本重算，不信任模型自评。'
utg_layer: L4
stage_order: 4
output_contract: work/revision_plan.json
---

# Reviewer Skill（评审手编排器 v2.0）

## Role

评审手：在前三手（Modeler / Programmer / Writer）全部完成后，模拟评委视角对论文做审查。
它负责四件事：**多视角打分**、**挑缺陷**、**给出可执行的修改清单**、**按清单落地执行修改**。

## 为什么需要独立成手

撰写手自检天然倾向"自己写的东西没问题"。把评审独立出来，
且**评分由脚本重算而非模型自评**，才能避免"模型给自己打高分"的循环论证。

## Agent Orchestra

```
[5 人评审团并行] → weakness-hunter → revision-planner → revision-executor
```

### 5 人评审团 (Stage 1, 并行)

| 序号 | agent | utg_layer | 职责 | 权重 | 输出 |
|------|-------|-----------|------|------|------|
| 1 | scorer-academic | L4 | 学术严谨性：推导/假设/验证/数学正确性 | 25% | work/score_card_academic.json |
| 2 | scorer-engineering | L4 | 工程落地：可复现/性能/鲁棒/规范 | 20% | work/score_card_engineering.json |
| 3 | scorer-judge | L4 | 评委视角：创新/完整/规范/亮点 | 25% | work/score_card_judge.json |
| 4 | scorer-reader | L4 | 可读性：结构/语言/图表叙事/逻辑流 | 15% | work/score_card_reader.json |
| 4 | scorer-adversarial | L4 | 对抗视角：漏洞/边界/造假风险/反模式 | 15% | work/score_card_adversarial.json |

### 后续串联 Agents

| 序号 | agent | stage | 职责 | 输出 |
|------|-------|-------|------|------|
| 6 | weakness-hunter | 2 | 逐条扫描反模式库挑缺陷 | work/weakness_report.json |
| 7 | revision-planner | 3 | 把缺陷转成可执行的修改清单 (支持 Per-Qi 差异化) | work/revision_plan.json |
| 8 | revision-executor | 4 | 按修改清单执行修改并验收 | work/execution_report.json |

## Verdict 状态机

由 `core/tools/score_artifact.py` **脚本重算**（不信任模型自评分数）：

### 聚合规则

聚合由 `core/tools/aggregate_scores.py` 做，verdict 由 `core/tools/score_artifact.py` 做——**两步分离，不要手写 `work/score_card.json`**：手写了也会被 `--verify` 重算比对判为伪造。

1. **取分**：4 张常规卡取 `weighted_score`，对抗卡取 `final_score`（该卡没有 `weighted_score` 字段）
2. **权重**：`weight_profiles.get_weights(题型)`，乘子 clamp 到 [0.7, 1.5] 后归一化至 sum=1.0；题型解析不出时回退固定权重 academic .25 / engineering .20 / judge .25 / reader .15 / adversarial .15
3. **加权均分**：`Σ(score_i × weight_i) / Σ(weight_i)`
4. **最低分否决制**：任一评分员分 < `review.pass_score`（默认 6）→ 不给 pass，均分再高也不行
5. **blocking 归集两路**：① 对抗卡 `deductions` 中含「致命 / fatal / blocking」的扣分项，以及 `verdict_contribution == "fail"` 时的 `fail_reason`；② `weakness_report.hits[]` 中 `severity == "blocking"`。按 `(source, issue)` 去重后把条数写回 `counts.blocking`，`decide()` 才看得见——否则聚合卡的 `blocking[]` 是死数据

### Verdict 映射

`score_artifact.decide()` 是**命中即返回**的短路判定，按下表自上而下的顺序检查：

| verdict | 触发条件 | EXIT | 后续动作 |
|---------|----------|------|----------|
| `block` | 合并去重后 blocking > 0；或无任何有效评分 | 2 | 必须修复，禁止提交，回退对应手 |
| `refine` | 最低分 < 6；或加权均分 < 6 | 1 | 整篇修改后重跑评审 |
| `refine_partial` | 均分与最低分都达标，但仍有 major 缺陷且集中在特定子问（scope 不是「全文」） | 1 | **只改受影响的子问** (Per-Qi)，不推翻全文 |
| `pass_with_review` | 达标但有全文级 major 或 minor 建议；或最低分 < 6 但已达 `review.max_rounds` 轮次上限 | 0 | 可提交，建议采纳 / 需人工确认 |
| `pass` | 均分 ≥ 6、最低分 ≥ 6、无 major/minor 遗留 | 0 | 可提交 |

**最低分不被均分掩盖**：加权均分用于排序，但任一关键维度低于门槛（默认 6/10）都必须单独处理，不能靠其他维度的高分拉平。

## Env Bindings

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `review.max_rounds` | 4 | 评审—修改循环的最大轮数 |
| `review.pass_score` | 6 | 通过分（满分 10），最低分否决线 |
| `review.improvement_max_rounds` | 2 | 单轮修改内的最大改进次数 |
| `review.figure_as_subject_max` | 3 | 图表做主语句式的最大允许次数 |

## 执行卡片

- **门禁**：`python core/tools/gate.py <项目> reviewer scorer-adversarial`（校验聚合卡）
- **判定**：`python core/tools/score_artifact.py <项目>`（出 verdict，EXIT 即结论）
- **输入**：`paper/main.tex` + `figures/all_results.json` + `work/frozen_numbers.json` + 5 张评分卡
- **输出**：`work/score_card.json`（由 `aggregate_scores.py` 生成）/ `work/weakness_report.json` / `work/revision_plan.json` / `work/execution_report.json`
- **失败**：verdict 为 `block` 或 `refine*` 时回退到对应手修正，最多 `max_rounds` 轮

## 聚合与判定的真源

5 张分卡齐全后依次跑这两条，顺序不可颠倒：

```bash
python core/tools/aggregate_scores.py <项目>   # 生成 work/score_card.json
python core/tools/score_artifact.py <项目>     # 判 verdict，写进 state.json 的 review 段
```

任何一张分卡或 `work/weakness_report.json` 改过，就必须重跑第一条，否则 gate 上的 `--verify` 断言会拦下来。

**顺序上的坑**：scorer-adversarial 是 stage 1e，weakness-hunter 是 stage 2。第一次聚合时 `weakness_report.json` 往往还不存在，聚合卡的 `blocking[]` 只含对抗卡那一路；weakness-hunter 跑完必须重跑一次聚合，否则 revision-planner 读到的是过期卡。verdict 不会因此漏判——`score_artifact.merge_blocking()` 会直接读 `weakness_report.json` 把另一路补上。

| 事项 | 真源 | 说明 |
|------|------|------|
| 聚合卡的生成 | `core/tools/aggregate_scores.py` | 5 张分卡 → `work/score_card.json`，唯一合法生成者 |
| 聚合卡是否手写/过期 | `aggregate_scores.py <项目> --verify` | 重算并逐维比对分数/权重/证据/blocking，不一致 EXIT 1 |
| verdict 判定 | `score_artifact.py` 的 `decide()` | 只读裁判：不写聚合卡，只依据聚合卡 + weakness_report 出结论 |
| blocking 合并 | `score_artifact.py` 的 `merge_blocking()` | 把聚合卡的 `blocking[]` 折回 `counts.blocking`，转换与去重规则复用 `aggregate_scores` |
| 题型权重 | `core/tools/weight_profiles.py` | `review.weight_profiles.{base,multipliers,clamp}` 可覆盖 |
| 阈值 | `core/env/config.yaml` 的 `review.*` | 见上方 Env Bindings |

**为什么判定逻辑不写在这里**：此前本节末尾放着一份 `aggregate_verdict` 伪代码，从未被实现，而且自身就跑不通——`list(scores.values()).count(lambda x: x < 6)` 不是合法用法（`count` 按相等比较，恒返回 0），读的 `adversarial["blocking_issues"]` 字段在真实对抗卡上也不存在。一份跑不通的规格只会诱使后来者实现第二套判定，于是同一条流水线出现两个互相矛盾的 verdict。判定逻辑只存在于代码里，本文件只描述它现在是什么。