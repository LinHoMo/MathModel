---
name: structure-planner
description: '规划论文结构与逐节字数预算，产出 paper_structure.json。撰写手的起始步骤。'
hand: writer
utg_layer: L1
stage: 1
inputs:
  - CODE_DELIVERABLES.md
  - core/env/config.yaml
  - core/knowledge/review/scoring-criteria.md
outputs:
  - work/paper_structure.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> writer structure-planner`
- **输入**：output/CODE_DELIVERABLES.md
- **输出**：`work/paper_structure.json`
- **核心步骤**：1. 定章节结构 → 2. 分配字数预算 → 3. 规划图表 → 4. 写 paper_structure.json
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Structure Planner

## Role

论文结构规划师：在撰写前把整篇论文的形式化骨架定下来——章节清单、字数分配、图表编号、公式数量、引用数量——并把所有交付阈值从 `core/env/config.yaml` 读出固化进 `work/paper_structure.json`，作为下游所有 agent 的契约源。

## UTG Layer

L1 形式化规约层：消除输入语义歧义。本 agent 把 `CODE_DELIVERABLES.md`（叙述性、半结构化的上游交付物）翻译为机器可校验的结构化规约（JSON），并锁定本手所有阈值。后续 agent 不再各自解释"该写多少字/几张图/几条引用"，全部回溯本 agent 输出。这是 UTG L1 在论文手的具体落地：把"该写什么"形式化，把"该写多少"参数化。

## Contract

- 输入：
  - `CODE_DELIVERABLES.md`（上游 Programmer 手输出，含子问题清单、模型概要、图表清单）
  - `core/env/config.yaml`（交付阈值与运行参数）
  - `core/knowledge/review/scoring-criteria.md`（真实赛区评分细则：章节结构须保证每个子问「模型+算法+结果」三件套成节，摘要独立成页，附录含程序）
- 读取的 env 键（通过 `from core.env.loader import get`）：
  - `get("paper.min_pages")`、`get("paper.min_words")`
  - `get("paper.min_figures")`、`get("paper.min_tables")`
  - `get("paper.min_equations")`、`get("paper.min_references")`
  - `get("runtime.template")`、`get("runtime.language")`、`get("runtime.strict_mode")`
- 输出：`work/paper_structure.json`，字段见下方 Procedure。

## Procedure

### Step 1: 读取上游交付物

读取 `CODE_DELIVERABLES.md`，抽取：
- 子问题清单（problem_id、标题、对应模型类型）
- 已生成图表清单（`figures/*.png` 文件名）
- 已生成结果汇总（`all_results.json` 路径与关键字段）

### Step 2: 读取交付阈值

```python
from core.env.loader import get
min_pages    = get("paper.min_pages")        # 默认 25
min_words    = get("paper.min_words")        # 默认 18000
min_figures  = get("paper.min_figures")      # 默认 6
min_tables   = get("paper.min_tables")       # 默认 4
min_equations= get("paper.min_equations")   # 默认 15
min_references=get("paper.min_references")  # 默认 10
template     = get("runtime.template")       # cumcm-zh / mcm-en / generic
language     = get("runtime.language")       # zh / en
strict_mode  = get("runtime.strict_mode")    # True
```

### Step 3: 选择论文结构模板

参考资源：
- `core/Writer/knowledge/writing/paper-structure-guide.md`：论文章节完整顺序
- `core/Writer/knowledge/profiles/cumcm-rules.md`：CUMCM 竞赛页数、评分、提交规则
- `core/Writer/knowledge/profiles/cumcm-profile.md`：CUMCM 竞赛配置
- `core/Writer/knowledge/profiles/profile-*.md`：各题型配置（分类/评价/机理/网络/优化/预测/仿真/统计）
- `core/Writer/knowledge/templates/mathmodel/`：LaTeX 模板目录

LaTeX 模板选择规则：
- `template == "cumcm-zh"` → `core/Writer/knowledge/templates/mathmodel/zh/cumcm/main.tex`
- `template == "mcm-en"` → `core/Writer/knowledge/templates/mathmodel/en/mcm/main.tex`
- `template == "generic"` → `core/Writer/knowledge/templates/mathmodel/generic/paper_template.tex`

### Step 4: 字数分配（以 `min_words` 为基准）

字数分配指南（以 **18000 字** 为基准，按 `min_words` 等比缩放；摘要受 writing_rules 400-600 字硬上限约束，不按百分比放大，其余章节按比例分配以保证总和 ≥ `get("paper.min_words")`）：

| 章节 | 字数占比 | 最低字数（18000 基准） | 说明 |
|------|---------|---------------------|------|
| 摘要 | 8% | 400-600字（硬上限） | 每个子问题：方法+结果+数值；末尾须含 3-5 个关键词（`\noindent\textbf{关键词：}`），GB/T 7714 引用上标 |
| 问题重述与分析 | 10% | 1890字 | 不是照抄题目，是分析思路 |
| 模型假设 | 5% | 950字 | 每条假设有必要性说明 |
| 符号说明 | 3% | 570字 | 表格形式，含量纲 |
| 模型建立与求解 | 45% | 8510字 | 每个子问题独立成节 |
| 结果分析与检验 | 12% | 2270字 | 数值结果+约束验证+误差分析 |
| 灵敏度分析 | 8% | 1510字 | 单参数扰动+结果稳定性 |
| 模型评价与推广 | 9% | 1700字 | 优点+缺点+改进+推广 |
| 参考文献 | - | >= min_references 篇 | 真实检索的文献 |
| 附录 | - | - | 核心代码 |

每个子问题"模型建立与求解"节必须包含：
1. 问题分析（200-300字）：分析问题特点，说明方法选择
2. 模型建立（300-500字）：写出核心公式（>=3个公式）
3. 模型求解（200-300字）：描述求解算法
4. 结果分析（200-300字）：分析结果，与预期对比

### Step 4.5: 页数预检

分配完成后做一次页数预检：`est_pages = 总字符数 / 800`，须满足 `est_pages >= get("paper.max_pages") × get("paper.page_fill_ratio")`（即 `≥ 30 × 0.8 = 24 页`）。若 `est_pages < 24`，按比例放大各章节 `word_budget`（摘要保持 400-600 字），保证排版后页数达到下限。

### Step 5: 写出 `work/paper_structure.json`

```json
{
  "paper_info": {
    "title": "<待 section-writer 填>",
    "template": "<cumcm-zh|mcm-en|generic>",
    "language": "<zh|en>",
    "target_pages": <min_pages>,
    "min_word_count": <min_words>
  },
  "sections": [
    {
      "id": "abstract",
      "title": "摘要",
      "word_budget": <int>,
      "word_ratio": 0.08,
      "content_type": "summary",
      "required": true
    },
    ...
  ],
  "figure_plan": [
    {"id": "fig_1_1", "filename": "paper/figures/fig_1_1.png", "source": "figures/xxx.png", "caption_required": true}
  ],
  "table_plan":  [...],
  "equation_target": <min_equations>,
  "reference_target": <min_references>,
  "latex_template_path": "<选定模板的相对路径>",
  "env_snapshot": {
    "min_pages": ..., "min_words": ..., "min_figures": ..., "min_tables": ...,
    "min_equations": ..., "min_references": ..., "template": ..., "language": ..., "strict_mode": ...
  }
}
```

## Self-Check

- [ ] `work/paper_structure.json` 存在且能被 `json.load` 解析
- [ ] `sections` 数组至少包含 5 项且覆盖必填章节（摘要/问题重述/假设/模型建立/结果分析/灵敏度/评价/参考文献/附录）
- [ ] 各章节 `word_budget` 之和 >= `get("paper.min_words")`（默认 18000，铁律 W13 基准）
- [ ] 摘要 `word_budget` 在 `get("paper.abstract_min_words")`（默认 400）– `get("paper.abstract_max_words")`（默认 600）范围内（铁律 W13）
- [ ] 页数预检 `est_pages = 总字符数 / get("paper.chars_per_page")`（默认 800）>= `get("paper.max_pages")`（默认 30）× `get("paper.page_fill_ratio")`（默认 0.8，即 80%，铁律 W14）
- [ ] `figure_plan` 长度 >= `get("paper.min_figures")`
- [ ] `table_plan` 长度 >= `get("paper.min_tables")`
- [ ] `equation_target` >= `get("paper.min_equations")` 且每个子问题节 >=3
- [ ] `reference_target` >= `get("paper.min_references")`
- [ ] `latex_template_path` 指向的模板文件真实存在（Glob/Read 校验）
- [ ] `env_snapshot` 字段与本 agent 调用 `get(...)` 的返回值完全一致

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "writer",
  "stage": 1,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "structure-planner",
      "stage": 1,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/Writer/knowledge/writing/paper-structure-guide.md`
- `core/Writer/knowledge/profiles/cumcm-rules.md`
- `core/Writer/knowledge/profiles/cumcm-profile.md`
- `core/Writer/knowledge/profiles/profile-*.md`（按题型匹配）
- `core/Writer/knowledge/templates/mathmodel/`（zh/cumcm、en/mcm、generic 三种模板）
- `core/knowledge/paper-cases/INDEX.md`、`METHOD-MAPPING.md`（题型-方法参考）
- `core/env/loader.py`（`load_config` / `get`）
- `core/Writer/laws/rules.md`（W1/W2/W3/W9/W10 的阈值来源）

## Iteration

自检失败时回退修正：
1. 字数总和不足：按比例放大各章节 `word_budget`，保证总和 >= `min_words`。
2. 图表数量不足：在 `figure_plan` 中补占位项，并在备注中标注"待 figure-generator 补生成"。
3. 公式数量不足：在子问题节的 `equation_target` 字段中提升到至少 3。
4. 模板路径不存在：按 `runtime.template` 回退到 `generic/paper_template.tex`。
5. 严格模式（`get("runtime.strict_mode") == True`）下任一阈值不达即标记 `status: "blocked"` 并返回上游 Modeler/Programmer 协商，不强行进入 section-writer。

## 评分点对齐（P2-7，评委视角）

规划结构时同步产出 `work/rubric_alignment.json`，把**赛题的每个得分点**
映射到具体论文章节。这解决一个常见失误：写得很好，但漏答了题目的某一问。

清单由三部分构成：

1. **赛题子问题**——逐条列出题目明确要求的结果
2. **通用评审维度**——结果检验、灵敏度、模型评价
3. **格式合规**——摘要数值、参考文献、AI 披露、匿名

格式：

```json
{
  "competition": "cumcm",
  "items": [
    {"id": "R1", "requirement": "题目要求的具体结果",
     "source": "问题一", "section": "4.1", "status": "covered"}
  ]
}
```

**每个评分点都必须映射到章节**，未映射的会被门禁拦下：
`python core/tools/gate.py <项目> writer structure-planner`。

终审时逐条核销——写之前就对齐，比写完再补省得多。
