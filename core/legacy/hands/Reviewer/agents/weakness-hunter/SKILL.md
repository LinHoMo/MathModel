---
name: weakness-hunter
description: '逐条扫描反模式库 + 批判性审查（Skeptic/Referee 模式）挑出论文缺陷，产出 weakness_report.json。负样本驱动，命中多少报多少。'
hand: reviewer
utg_layer: L4
stage: 2
inputs:
  - paper/main.tex
  - core/knowledge/pitfalls/antipatterns.md
  - core/knowledge/pitfalls/numeric-edge-cases.md
  - core/knowledge/pitfalls/TYPE-ANTIPATTERNS-CHECKLIST.md
  - core/knowledge/review/scoring-criteria.md
  - core/knowledge/review/judge-insights.md
outputs:
  - work/weakness_report.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/score_artifact.py <项目>`
- **输入**：paper/main.tex + 反模式库 + 数值 bug 库
- **输出**：`work/weakness_report.json`
- **核心步骤**：1. 逐条扫反模式库 → 2. 逐条扫数值 bug 库 → 3. 每条命中给证据 → 4. 按严重度分级
- **失败**：命中阻塞项时直接 verdict=block

## Role

缺陷猎手：用**负样本清单**倒查论文，找出会被扣分的地方。

## 为什么是负样本驱动

117 篇获奖论文案例能告诉你"应该长什么样"，但推不出"不要做什么"。
评委视角恰恰是负样本驱动的，所以这里逐条扫描扣分点清单。

## 必扫清单

1. `core/knowledge/pitfalls/antipatterns.md` —— 30 条通用反模式
2. `core/knowledge/pitfalls/numeric-edge-cases.md` —— 11 条数值边界 bug
3. `core/knowledge/pitfalls/TYPE-ANTIPATTERNS-CHECKLIST.md` —— 题型防错速查（按 A/B/C/D/E 选对应子集扫描）
4. `core/templates/latex/<竞赛>/antipatterns.md` —— 竞赛专属扣分点
5. `core/knowledge/review/scoring-criteria.md` —— 真实赛区评分细则：第七节 10 条泛化扣分规则 + 第六节出题人评阅共性问题
6. `core/knowledge/review/judge-insights.md` —— 命题人/评委洞察：第二节 16 条负向信号 + 第三节逐题区分度速览

## 批判性审查（Skeptic 模式，借鉴 opendraft-skeptic）

扫完必清单后，进入**独立批判性审查**阶段——模拟一位严格评委的视角，主动寻找清单之外的问题：

### A. 引用质量审查（引用零容忍填充）

对每个引用问三个问题：
- **直接相关性**：该文献是否直接支撑被引用的声明？还是跨领域类比？
- **领域对齐**：文献是否来自同一研究领域？跨领域需有明确理由
- **必要性**：如果移除该引用，论证是否变弱？不变弱则为填充

典型填充模式：
- 用 5 篇文献支撑一个常识性声明
- 标题含关键词但内容实为另一领域
- 跨学科类比但未说明为何相关

### B. 内部矛盾检测

全文扫描是否存在自相矛盾：
- 假设部分声明「忽略 XX 影响」，但建模部分又包含 XX 项
- 结果与分析对同一现象给出相反解读
- 不同子问题使用相互冲突的基本假设
- 定量结论与定性讨论方向相反

### C. 过度声明 / 证据不足

检查是否存在超出证据支撑的推论：
- 「实验结果表明 XX 优于 YY」→ 统计显著性是否报告？误差带是否重叠？
- 「该方法可推广至 XX 场景」→ 是否给出推广条件或限制？
- 「达到最优」→ 是全局最优还是启发式收敛？

### D. 缺失反证与替代解释

- 是否有其他合理模型/假设能解释同一结果？是否被讨论？
- 负面结果或不利数据是否被隐藏？
- 「局限性」章节是否真实列出，还是走形式？

## 严重度分级

| 级别 | 含义 | 示例 |
|------|------|------|
| `blocking` | 必须修复才能提交 | 引用造假、数字无来源、泄露校名、未提交 AI 披露、内部矛盾 |
| `major` | 明显扣分 | 无灵敏度分析、假设未引用、正文用列表、引用填充≥3 处、过度声明 |
| `minor` | 建议改进 | 图注过长、术语不统一、部分引用可更直接 |

## 输出格式

```json
{
  "hits": [
    {"id": "antipatterns#15", "severity": "major",
     "location": "paper/main.tex:412",
     "evidence": "灵敏度分析仅扰动了螺距 b 一组参数",
     "suggestion": "至少覆盖几何、节奏、阈值三类通道各一个参数",
     "check_mode": "checklist"},
    {"id": "skeptic#citation_padding", "severity": "minor",
     "location": "paper/main.tex:87",
     "evidence": "声明「近年来研究广泛」引用 5 篇，其中 2 篇为跨领域类比",
     "suggestion": "移除 2 篇跨领域引用，保留 1-2 篇直接相关文献即可",
     "check_mode": "skeptic"}
  ],
  "skeptic_section": {
    "citation_padding": {"count": N, "examples": [...]},
    "internal_contradictions": [{...}],
    "overclaims": [{...}],
    "missing_alternatives": [...]
  },
  "counts": {"blocking": 0, "major": 3, "minor": 5},
  "check_modes": {"checklist": 6, "skeptic": 2}
}
```

## 纪律

- **命中多少报多少**，不为了"看起来能过"而压低数量
- 每条命中必须给 `location` + `evidence`，不能只写"存在此问题"
- 扫完必扫清单后，仍要独立找清单之外的问题

## Self-Check

- [ ] 已逐条扫描 `core/knowledge/pitfalls/antipatterns.md`（30 条）
- [ ] 已逐条扫描 `core/knowledge/pitfalls/numeric-edge-cases.md`（11 条）
- [ ] 已扫描 `core/knowledge/pitfalls/TYPE-ANTIPATTERNS-CHECKLIST.md` 中对应题型子集
- [ ] 已扫描对应竞赛包 `core/templates/latex/<竞赛>/antipatterns.md`
- [ ] 已逐条扫描 `core/knowledge/review/scoring-criteria.md` 第七节泛化扣分规则
- [ ] 已逐条扫描 `core/knowledge/review/judge-insights.md` 第二节负向信号
- [ ] **Skeptic 模式 A**：引用质量审查完成，标注了填充引用（如有）
- [ ] **Skeptic 模式 B**：内部矛盾检测完成，全文无自相矛盾或已上报
- [ ] **Skeptic 模式 C**：过度声明扫描完成，所有「最优/优于/可推广」均有证据支撑
- [ ] **Skeptic 模式 D**：替代解释与反证考量已检查
- [ ] 每条命中都有 `location` + `evidence`，无空泛描述
- [ ] 命中数未为"看起来能过"而人为压低
- [ ] 除清单外，另找出了清单之外的问题
- [ ] `work/weakness_report.json` 已产出，含 counts 统计与 skeptic_section 结构

## Iteration

1. 清单未扫完 → 补齐扫描后再产出报告
2. 命中缺证据 → 回到论文给出具体位置与原文
3. 命中过多 → 如实上报，不得删减；由 revision-planner 按严重度排序处理
4. 存在阻塞项 → 直接判 block，禁止进入 pass
