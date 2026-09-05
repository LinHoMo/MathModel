---
name: literature-searcher
description: "文献检索 Agent (Stage 1.5)：在题型识别后、方法匹配前，按问题关键词检索 5-8 篇高质量文献，提取方法证据支撑模型选择，标注期刊含金量。硬上限 5 次搜索。"
utg_layer: L2
stage: 1.5
hand: modeler
inputs:
  - work/question_spec.json
  - work/type_classification.json
outputs:
  - work/literature_evidence.json
---

# Literature Searcher Skill (文献检索 Agent)

## Role

Stage 1.5 承载 Agent：在 `type-classifier` 完成题型识别后、 `method-matcher` 进行方法匹配前，执行**强制文献检索**（可配置跳过）。目标是用学术证据支撑后续的模型选择，避免"凭空捏造模型"。

## Contract

- **输入**：
  - `work/question_spec.json` (problem-parser 输出)
  - `work/type_classification.json` (type-classifier 输出)
  - 环境变量 `modeling.literature_search_enabled` (默认 true)
  - 环境变量 `modeling.literature_max_searches` (默认 5)
  - 环境变量 `modeling.literature_target_count` (默认 5-8)

- **输出**：`work/literature_evidence.json`

- **中间产物**：`work/literature_raw/` 目录下的原始检索结果

## Procedure

### 1. 构建检索查询

从 `question_spec.json` 提取：
- `domain_keywords` (领域关键词)
- `sub_questions[].math_essence` (数学本质)
- `sub_questions[].constraints` (约束条件)

从 `type_classification.json` 提取：
- `topic_type` (A/B/C/D/E)
- `recommended_directions` (推荐方法方向)

构建 3 类查询（每类 ≤2 条，总计 ≤5 条）：
1. **问题导向**："数学建模 + {domain} + {math_essence} + 优化/预测/评价"
2. **方法导向**："{recommended_method} + {application_domain} + 案例研究"
3. **竞赛导向**："CUMCM/MCM/ICM + {topic_type} + 题 + 解法 + 获奖论文"

### 2. 执行检索 (硬上限 5 次)

按查询顺序执行，每次检索返回 Top 10，去重后合并。

**检索源优先级**：
1. Google Scholar / Semantic Scholar (学术主流)
2. CNKI / 万方 (中文核心)
3. IEEE Xplore / ACM DL / SpringerLink / Elsevier (会刊)
4. arXiv (预印本，标注预印本属性)

**必需字段**：title, authors, year, venue, doi, abstract, citation_count (若可得)

### 3. 文献筛选与评级

对合并后的候选文献评分（满分 10）：

| 维度 | 权重 | 评分规则 |
|------|------|---------|
| 期刊含金量 | 30% | SCI Q1=10, Q2=8, Q3=6, Q4=4; 中文核心/CCF-A=8, CCF-B=6, 普刊=4; 会议 CCF-A=8, CCF-B=6; 预印本=2 |
| 方法相关性 | 30% | 直接给出同类问题完整建模流程=10; 给出关键算法/模型=7; 仅提及相关概念=4 |
| 问题相似度 | 25% | 同竞赛同题型=10; 同领域同数学本质=7; 仅领域相同=4 |
| 引用影响力 | 15% | 引用>100=10, >50=8, >20=6, >10=4, 其他=2 |

**筛选规则**：
- 评分 ≥ 6.0 进入候选池
- 去除年份 > 赛题年份的"未来文献"（HARD BLOCK）
- 最终保留 5-8 篇，优先保证：中英文各半、覆盖所有子问题、含至少 1 篇竞赛获奖论文

### 4. 证据提取

对每篇入选文献，提取结构化证据：

```json
{
  "paper_id": "doi_or_hash",
  "title": "...",
  "authors": [...],
  "year": 2023,
  "venue": "Journal Name",
  "venue_tier": "SCI_Q1|CCF_A|Chinese_Core|ArXiv",
  "score": 8.2,
  "relevance": {
    "sub_question_id": "Q1",
    "matched_method": "NSGA-II + 代理模型",
    "key_formula": "min f(x) = (f1, f2) s.t. g(x) ≤ 0",
    "algorithm_details": "种群200, 迭代500, SBX交叉, 多项式变异",
    "validation_approach": "对比 MOEA/D, HV 指标, 30次独立运行",
    "limitations": "高维决策变量收敛慢, 建议引入局部搜索"
  },
  "evidence_quote": "原文关键段落(≤300字)",
  "citation_count": 45
}
```

### 5. 输出聚合

`work/literature_evidence.json` 结构：

```json
{
  "search_queries": [...],
  "total_candidates": 42,
  "selected_count": 7,
  "papers": [...],  // 上述证据数组
  "coverage": {
    "Q1": ["paper_1", "paper_3"],
    "Q2": ["paper_2", "paper_5"],
    "Q3": ["paper_4", "paper_6", "paper_7"]
  },
  "method_evidence_map": {
    "NSGA-II": ["paper_1", "paper_3"],
    "代理模型": ["paper_1", "paper_4"],
    "TOPSIS": ["paper_2", "paper_5"]
  },
  "search_timestamp": "2026-09-01T10:30:00Z",
  "skipped": false
}
```

## Resources

- `core/knowledge/data-sources/DATA-SOURCES.md` - 权威数据源目录与检索策略
- `core/validators/modules/scholar_fetch.py` - 学术检索工具 (已有 scholar_fetch.py)
- `core/env/loader.py` - 读取 `modeling.literature_*` 参数
- `core/schemas/literature_evidence.schema.json` - 输出 Schema (需新建)

## Self-Check

- [ ] `literature_evidence.json` 存在且非空
- [ ] `selected_count` 在 [5, 8] 区间 (或 `skipped==true`)
- [ ] 无年份 > 赛题年份的文献
- [ ] 每篇文献含 `venue_tier`、`score`、`relevance`、`evidence_quote`
- [ ] `coverage` 覆盖所有子问题
- [ ] `method_evidence_map` 非空，为 method-matcher 提供候选支撑
- [ ] 通过 `core/schemas/literature_evidence.schema.json` 校验

## Iteration

- 检索结果不足：放宽查询词、增加检索源、或标记 `skipped=true` 并记录原因
- 评分偏低：人工复核评分权重，或引入 `modeling.literature_score_threshold` 调整
- 覆盖不全：针对未覆盖子问题追加专用查询 (消耗额外搜索额度)

## Env Bindings

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `modeling.literature_search_enabled` | true | 总开关，false 则直接输出 skipped=true |
| `modeling.literature_max_searches` | 5 | 最大检索次数 (硬上限) |
| `modeling.literature_target_count` | 7 | 目标入选文献数 |
| `modeling.literature_score_threshold` | 6.0 | 入选最低评分 |
| `modeling.literature_chinese_ratio` | 0.5 | 中文文献最低占比 |

## UTG Layer Mapping

| UTG 层 | 机制 | 本 Agent 落地 |
|--------|------|--------------|
| L1.5 | 形式化规约 + 外部知识注入 | 结构化检索查询 + 评分规约 + 证据结构化输出 |

## 注意事项

1. **不编造文献**：无检索结果时必须标记 `skipped=true`，不得生成假 DOI/标题
2. **版权合规**：仅存储元数据+摘要引用(≤300字)，不存全文
3. **可跳过**：`literature_search_enabled=false` 时直接输出最小结构，不阻塞流程
4. **赛题年份推断**：从 `projects/<项目名>` 目录名或 `question_spec.json` 的 `contest_year` 字段获取