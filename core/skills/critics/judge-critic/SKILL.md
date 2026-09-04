---
name: judge-critic
description: '评委视角终审：聚合证据门禁 + 叙事批判，输出 PASS/WEAK/FAIL/UNKNOWN 判定与风险清单。分数仅辅助，判定优先。'
role: critic
node: paper_review
validator: judge-critic
utg_layer: L4+L6 前置化
inputs:
  - work/narrative_critique.md
  - state/evidence_graph.json
  - paper/main.pdf
outputs:
  - work/judge_verdict.md
---

## 执行卡片（先读这里）

- **定位**: 终审。V2 的 5 人评审团（事后评分）在 V3 中降级为一个前置判定节点
- **判定**: PASS / WEAK / FAIL / **UNKNOWN**（信息不足时宁可 UNKNOWN 不可瞎判）
- **工具**: `core/runtime/writing/judge_critic.py`（聚合 evidence-gate + narrative-critic）

---

# Judge Critic

## Role

模拟评委视角做最终判定：这篇论文拿出去会不会被打穿？输出判定与风险清单，反馈环由引擎执行（V2 revision-planner/executor 的职责已代码化）。

## 与 V2 的区别

| V2（5 scorer + revision） | V3（judge-critic） |
|---|---|
| 5 个 agent 事后打分 | 1 个 critic 前置判定 |
| 分数驱动（阈值模糊） | 判定驱动（PASS/WEAK/FAIL/UNKNOWN） |
| revision-planner 规划回退 | 引擎 on_fail 反馈环自动回退 |
| 无 UNKNOWN 状态 | 信息不足显式 UNKNOWN（禁止瞎判） |

## Procedure

### Step 1: 聚合上游判定

- evidence_gate 报告（E1-E8）：证据结构完整性。
- narrative_critic 报告（N1-N7）：叙事投影保真度。

### Step 2: 判定规则

```
UNKNOWN ← 无 claim / 无章节投影 / 证据门禁缺报告（信息不足）
FAIL    ← 任一上游 FAIL（硬伤：无支撑主张 / 死证据 / 悬空章节）
WEAK    ← 无 FAIL 但有 weak 项（覆盖率不足 / 缺灵敏度 / 孤儿图）
PASS    ← 证据完整 + 叙事一致
```

### Step 3: 人类评委会怎么打（LLM 评审层，判定之外）

对 PASS/WEAK 的论文做评委会模拟：摘要是否 30 秒讲清贡献；图表是否自明；结论是否与证据强度匹配。产出风险清单（不计入判定，写入 verdict 文档的"人工复核建议"节）。

### Step 4: 输出

写 `work/judge_verdict.md`：verdict + 风险清单（按严重度排序）+ 反馈环建议（FAIL 时指明回退目标节点）。

## Self-Check

- [ ] UNKNOWN 只在信息不足时出现，不得用作逃避判定
- [ ] 每条风险标注来源（evidence-gate / narrative-critic / 人工复核）
- [ ] FAIL 时给出明确的反馈环目标节点

## Iteration

- FAIL → 引擎按 on_fail 回 paper_projection；证据侧硬伤升级回 evidence_gate 的 on_fail（experiment_design）。
- 连续 2 轮 FAIL → blocked，人工介入。
