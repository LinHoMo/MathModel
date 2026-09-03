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

1. **加权均分**：`final_score = Σ(score_i × weight_i)`
2. **最低分否决制**：任一评分员最终分 < `review.pass_score` (默认 6) → `verdict = block/refine`
3. **对抗票决**：scorer-adversarial 有 `blocking_issues` 非空 → 必须逐项整改，verdict 至少为 `refine_partial`
4. **维度底线**：5 个评分员中任一关键维度子分 < 5 → 单独处理

### Verdict 映射

| verdict | 含义 | 触发条件 | 后续动作 |
|---------|------|----------|----------|
| `block` | 存在阻塞级缺陷 | 加权均分 < 6 或任一评分员最终分 < 5 或 adversarial blocking_issues 含致命项 | 必须修复，禁止提交，回退对应手 |
| `refine` | 整体不达标 | 加权均分 < 6 或 ≥2 个评分员最终分 < 6 | 整篇修改后重跑评审 |
| `refine_partial` | 仅个别子问不达标 | 仅 1 个评分员最终分 < 6 或 adversarial 仅有非致命 blocking_issues | **只改受影响的子问** (Per-Qi)，不推翻全文 |
| `pass_with_review` | 达标但有建议 | 加权均分 ≥ 6 且所有评分员最终分 ≥ 6，但有遗留建议 | 可提交，建议采纳 |
| `pass` | 全部达标 | 加权均分 ≥ 7 且所有评分员最终分 ≥ 7，无建议 | 可提交 |

**最低分不被均分掩盖**：加权均分用于排序，但任一关键维度低于门槛（默认 6/10）都必须单独处理，不能靠其他维度的高分拉平。

## Env Bindings

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `review.max_rounds` | 4 | 评审—修改循环的最大轮数 |
| `review.pass_score` | 6 | 通过分（满分 10），最低分否决线 |
| `review.improvement_max_rounds` | 2 | 单轮修改内的最大改进次数 |
| `review.figure_as_subject_max` | 3 | 图表做主语句式的最大允许次数 |

## 执行卡片

- **门禁**：`python core/tools/score_artifact.py <项目>`
- **输入**：`paper/main.tex` + `figures/all_results.json` + `work/frozen_numbers.json` + 5 个评分卡
- **输出**：`work/score_card.json` (聚合后) / `work/weakness_report.json` / `work/revision_plan.json` / `work/execution_report.json`
- **失败**：verdict 为 `block` 或 `refine` 时回退到对应手修正，最多 `max_rounds` 轮

## Aggregation Logic (供 score_artifact.py 实现)

```python
def aggregate_verdict(score_cards: List[dict], weakness_report: dict, topic_type: str = None) -> dict:
    # 题型差异化权重（已归一化，sum=1.0）；无法解析题型时回退固定基础权重
    try:
        from weight_profiles import get_weights
        weights = get_weights(topic_type) if topic_type else {
            "scorer-academic": 0.25, "scorer-engineering": 0.20,
            "scorer-judge": 0.25, "scorer-reader": 0.15, "scorer-adversarial": 0.15,
        }
    except ImportError:
        weights = {
            "scorer-academic": 0.25, "scorer-engineering": 0.20,
            "scorer-judge": 0.25, "scorer-reader": 0.15, "scorer-adversarial": 0.15,
        }
    
    # 1. 计算各评分员最终分
    scores = {}
    for card in score_cards:
        name = card["scorer"]
        if "final_score" in card:
            scores[name] = card["final_score"]
        elif "weighted_score" in card:
            scores[name] = card["weighted_score"]
    
    # 2. 加权均分
    weighted_avg = sum(scores[name] * weights[name] for name in weights)
    
    # 3. 最低分检查
    min_score = min(scores.values())
    min_scorer = min(scores, key=scores.get)
    
    # 4. 对抗视角检查
    adversarial = next(c for c in score_cards if c["scorer"] == "scorer-adversarial")
    blocking = adversarial.get("blocking_issues", [])
    has_fatal_blocking = any("致命" in str(b) or "fatal" in str(b).lower() for b in blocking)
    
    # 5. Verdict 判定
    if weighted_avg < 6 or min_score < 5 or has_fatal_blocking:
        verdict = "block"
    elif weighted_avg < 6 or list(scores.values()).count(lambda x: x < 6) >= 2 or blocking:
        verdict = "refine_partial" if (list(scores.values()).count(lambda x: x < 6) == 1 and not has_fatal_blocking) else "refine"
    elif weighted_avg >= 7 and min_score >= 7 and not blocking:
        verdict = "pass"
    else:
        verdict = "pass_with_review"
    
    return {
        "verdict": verdict,
        "weighted_avg": round(weighted_avg, 2),
        "min_score": round(min_score, 2),
        "min_scorer": min_scorer,
        "individual_scores": {k: round(v, 2) for k, v in scores.items()},
        "blocking_issues": blocking,
        "pass_score": 6
    }
```