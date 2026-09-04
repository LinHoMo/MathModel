---
name: narrative-critic
description: '叙事一致性批判：主张-章节归属、弱证据强叙事、死主张残留、孤儿图表。判定 PASS/FAIL 而非打分。'
role: critic
node: paper_review（前置输入）
validator: narrative-critic
utg_layer: L4 前置化
inputs:
  - state/registry.json
  - state/evidence_graph.json
  - paper/                     # 投影产物
outputs:
  - work/narrative_critique.md
---

## 执行卡片（先读这里）

- **定位**: paper_review 的叙事侧输入——judge-critic 管全局判定，本 critic 管故事讲不讲得通
- **工具**: `core/runtime/writing/`（director → projection → narrative_critic 三段管线）
- **判定**: PASS / FAIL + N1-N7 findings（见 narrative_critic.py docstring）

---

# Narrative Critic

## Role

论文是 Research State 的投影；投影失真（叙事与证据图不一致）比文笔差更致命。本 critic 检查投影保真度。

## 与 V2 的区别

V2 scorer-reader 事后给"可读性分数"；V3 narrative-critic 前置于 paper_review，检查的是**结构一致性**（机器可判定），不是文风（文风由 human/LLM 评审）。

## Procedure

### Step 1: 重建叙事与投影

- ResearchDirector.build()：从 Registry + Graph 得到 StoryArcs（主张 + 证据闭包 + 健康度）。
- PaperProjection.project()：得到结构化大纲（章节-主张-图表归属）。

### Step 2: 七项检查（N1-N7）

| 代码 | 检查 | 严重度 |
|---|---|---|
| N1 | 无 claim（没有故事可讲） | FAIL |
| N2 | 死主张未从叙事剔除 | FAIL |
| N3 | 无支撑主张进入结果章节 | FAIL |
| N4 | claim 无章节归属（appears_in 未回写） | FAIL |
| N5 | 结果章节无任何 claim | FAIL |
| N6 | 灵敏度章节无证据 | WEAK |
| N7 | 孤儿图（未归属任何主张） | WEAK |

### Step 3: 输出判定

写 `work/narrative_critique.md`：verdict + 逐项 findings + 修正方向（如 N4 → 回写 appears_in 边；N3 → 降级措辞或补实验）。

## Self-Check

- [ ] 判定基于结构一致性而非主观文风
- [ ] 每条 FAIL 指向具体 claim/figure ID
- [ ] 修正方向可执行（回写边 / 降措辞 / 补实验）

## Iteration

- FAIL → 反馈环回 paper_projection / paper_sections（按 on_fail）。
- 死主张（N2）→ 触发 evidence 侧复查：是数据问题回 experiment，还是叙事未同步。
