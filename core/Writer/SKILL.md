---
name: writer
description: "撰写手编排器：串联 7 个写作 agent（结构规划 → 章节撰写 → 图表 → 文献 → 一致性 → 护栏 → 终验），消费 CODE_DELIVERABLES.md 产出 PAPER_SPEC.md 与 paper/main.pdf。"
---

# Writer Skill（手级编排器）

## Role

论文撰写师（Writer）：本手是 MathModelSkills 四手架构（Modeler/Programmer/Writer/Reviewer）中负责撰写的一手（其后由 Reviewer 做评审），负责把上游 Programmer 产出的代码交付物转化为最终论文。本 SKILL.md 是手级编排器，不再承担单一流程，而是按 UTG（通用可信生成架构）六层机制编排 7 个子 agent，由各 agent 分层落地论文撰写、图表生成、引用整理、一致性校验、运行时护栏、最终验证。

## Contract

- 输入：`CODE_DELIVERABLES.md`（上游 Programmer 手输出，含子问题清单、模型概要、图表清单、`figures/all_results.json` 路径）
- 输出：
  - `output/PAPER_SPEC.md`（论文交付物清单，符合 `core/Writer/templates/PAPER_SPEC_TEMPLATE.md` 与 `core/schemas/paper_spec.schema.json`）
  - `paper/main.pdf`（最终论文 PDF）
  - `paper/main.tex` / `paper/references.bib` / `paper/figures/`（源文件）
  - `work/audit_log.json`（哈希审计日志）

## Agent Orchestra

本手把单一流程拆分为 7 个 agent，按 stage 串联执行。每个 agent 对应 UTG 一层，独立 SKILL.md 见 `core/Writer/agents/<name>/SKILL.md`。

| 序号 | name | utg_layer | stage | 职责 | 输出 |
|---|---|---|---|---|---|
| 1 | structure-planner | L1 | 1 | 论文结构规划 + 字数分配 + 阈值固化 | `work/paper_structure.json` |
| 2 | section-writer | L2 | 2 | 按字数预算撰写各章节 LaTeX 内容 | `paper/main.tex` |
| 3 | figure-generator | L2 | 3 | 图表生成与规范命名（`fig_<problem_id>_<seq>.png`） | `paper/figures/` |
| 4 | reference-curator | L3 | 4 | 参考文献整理 + 引用完整性核验 | `paper/references.bib` + `work/reference_report.json` |
| 5 | consistency-checker | L4 | 5 | 论文-代码数值一致性回溯 | `work/consistency_report.json` |
| 6 | guardrails-checker | L5 | 6 | 运行时护栏（禁用词/占位符/AI痕迹/内部路径/缺失bib key/缺失图片） | `work/guardrails_report.json` |
| 7 | final-validator | L6 | 7 | 最终校验 + 哈希审计 + 渲染 PDF + 输出 PAPER_SPEC.md | `output/PAPER_SPEC.md` + `paper/main.pdf` + `work/audit_log.json` |

**串联顺序**（任一 stage 失败即在本手内回退，不向下游推进）：

```
structure-planner (L1)
        ↓ work/paper_structure.json
section-writer (L2)        ← 同时/之后触发
        ↓ paper/main.tex         ↓ paper_structure.json
figure-generator (L2) ──────┘
        ↓ paper/figures/
reference-curator (L3)
        ↓ paper/references.bib + work/reference_report.json
consistency-checker (L4)
        ↓ work/consistency_report.json
guardrails-checker (L5)
        ↓ work/guardrails_report.json
final-validator (L6)
        ↓ output/PAPER_SPEC.md + paper/main.pdf + work/audit_log.json
```

注：`figure-generator` 与 `section-writer` 都属 L2，可并行启动（都依赖 `paper_structure.json`）；但 `figure-generator` 落地图片文件后，`section-writer` 才能在 `\includegraphics{}` 引用真实存在的文件，实践中建议 figure-generator 先于或与 section-writer 同步进行，section-writer 完成后再统一推进 L3 及以后。

## Stage Gates

每个 agent 输出后必须通过自检才能进入下一 stage。任一 stage 自检失败，在本手内回退到对应 agent 修正，不向下游传递错误。各 stage 的通过条件：

| stage | agent | Stage Gate 通过条件 | 失败回退目标 |
|---|---|---|---|
| 1 | structure-planner | `paper_structure.json` 解析通过；字数总和 >= `min_words`；图表/公式/引用数达阈值；模板路径存在 | structure-planner 自行修正；严格模式下退回上游 Modeler/Programmer 协商 |
| 2 | section-writer | `main.tex` 可编译；各节字数达标；公式数达标；摘要每子问题含数值；假设有必要性；图表前后有分析；模型评价诚实；无禁用词/占位符 | section-writer 自行扩写/改写 |
| 3 | figure-generator | `paper/figures/` 非空；文件名匹配 `^fig_\d+_\d+\.(png\|pdf\|eps)$`；编号连续；矢量优先；位图 >=300 dpi；无孤立文件 | figure-generator 自行补生成/重命名；缺数据时退回 Programmer |
| 4 | reference-curator | `references.bib` 存在；引用数 >= `min_references`；`missing_keys_in_bib` 为空；所有 `verified == true`；引用格式 `\citep{}` | reference-curator 补条目；无来源时退回 section-writer 删除引用 |
| 5 | consistency-checker | `numbers_traced == true`；`untraceable_count == 0`；摘要与正文数值一致；图表数值与代码一致 | 误写退回 section-writer；缺字段退回 Programmer |
| 6 | guardrails-checker | `has_errors == false`；6 项 checks 全 true；无孤立 label/悬空 ref | 退回 section-writer / reference-curator / figure-generator 对应修正 |
| 7 | final-validator | schema 校验通过；PDF 页数 >= `min_pages`；字数/图表/表格/公式/引用全达标；子报告全 passed；哈希链完整 | 按缺失项退回对应 agent |

`runtime.strict_mode == True` 时，任一 stage 不达即阻塞，不进入下一 stage。

## Env Bindings

本手从 `core/env/config.yaml`（经 `core/env/loader.py` 的 `load_config()` / `get(key)` 接口）读取以下参数。**structure-planner** 与 **final-validator** 是唯二直接读取所有 `paper.*` 阈值的 agent；其他 agent 通过 `paper_structure.json` 间接获得阈值。

| env 键 | 默认值 | 读取者 | 用途 |
|---|---|---|---|
| `paper.min_pages` | 25 | structure-planner / final-validator | 目标页数下限（上限 `paper.max_pages`=30） |
| `paper.min_words` | 18000 | structure-planner / final-validator | 总字数下限，按比例分配到各章节 |
| `paper.min_figures` | 6 | structure-planner / final-validator / figure-generator | 图表数量下限 |
| `paper.min_tables` | 4 | structure-planner / final-validator | 表格数量下限 |
| `paper.min_equations` | 15 | structure-planner / final-validator / section-writer | 公式数量下限，每个子问题节 >=3 |
| `paper.min_references` | 10 | structure-planner / final-validator / reference-curator | 参考文献数量下限 |
| `runtime.template` | cumcm-zh | structure-planner / section-writer | LaTeX 模板选择（cumcm-zh / mcm-en / generic） |
| `runtime.language` | zh | structure-planner / section-writer | 论文语言（zh / en） |
| `runtime.strict_mode` | True | 所有 agent | 严格模式：阈值不达即阻塞，不强行推进 |

读取示例：

```python
from core.env.loader import get
min_pages = get("paper.min_pages")          # 25
min_words = get("paper.min_words")          # 18000
template  = get("runtime.template")         # "cumcm-zh"
language = get("runtime.language")         # "zh"
strict   = get("runtime.strict_mode")       # True
```

## UTG Layer Mapping

UTG 六层防御体系在本手由 7 个 agent 承载，对应关系如下（与原单一流程的 Six-Layer Defense 表保持映射）：

| UTG 层 | 机制 | 承载 agent | 拦截目标 | 对应铁律 |
|---|---|---|---|---|
| L1 | 形式化规约层 | structure-planner | 输入语义歧义、阈值缺失、模板路径不存在 | W2 / W3 / W10 |
| L2 | 工具调用与生成层 | section-writer + figure-generator | LaTeX 编译错误、图表命名不规范、文件缺失、图表无分析 | W4 |
| L3 | 过程验证层 | reference-curator | 引用关系不闭合、引用捏造 | W5 |
| L4 | 异构验证层 | consistency-checker | 论文数值与代码输出不一致 | W1 / W2 |
| L5 | 运行时护栏层 | guardrails-checker | 禁用词、占位符、AI痕迹、内部路径、悬空 bib key / 图片 | W5 / W6 / W7 / W8 |
| L6 | 事后验证层 | final-validator | schema 不符、阈值不达、PDF 渲染失败、哈希链断裂 | W1 / W9 / W10 |

各 agent 的详细职责、契约、流程、自检清单见 `core/Writer/agents/<name>/SKILL.md`。

## Laws

详见 `core/Writer/laws/rules.md`。W1-W10 完整保留，由对应 UTG 层的 agent 承载执行。

### W1: 论文中每个数值必须能追溯到 figures/all_results.json
- 防御层次：L1 + L6（structure-planner 规约 + final-validator 复核）+ L4（consistency-checker 异构验证）
- 承载 agent：consistency-checker（主）+ final-validator（复核）

### W2: 摘要必须包含每个子问题的具体数值结果
- 防御层次：L1（structure-planner 规约摘要节）+ L4（consistency-checker 校验摘要数值一致性）
- 承载 agent：section-writer（撰写）+ consistency-checker（校验）

### W3: 每个假设必须有必要性说明
- 防御层次：L1（structure-planner 规约）
- 承载 agent：section-writer（撰写）

### W4: 每张图表前后必须有分析文字
- 防御层次：L2（section-writer 保证）+ L5（guardrails-checker 校验引用闭合）
- 承载 agent：section-writer（撰写）+ figure-generator（落地图表）

### W5: 参考文献必须真实存在，不可捏造
- 防御层次：L3（reference-curator 过程验证）+ L5（guardrails-checker 校验 bib key 闭合）
- 承载 agent：reference-curator（主）+ guardrails-checker（复核）

### W6: 禁止使用AI痕迹词汇
- 防御层次：L5（guardrails-checker 运行时护栏）
- 承载 agent：guardrails-checker

### W7: 禁止出现内部文件名、脚本名、临时目录
- 防御层次：L5（guardrails-checker 运行时护栏）
- 承载 agent：guardrails-checker

### W8: 禁止有占位符残留
- 防御层次：L5（guardrails-checker 运行时护栏）
- 承载 agent：guardrails-checker

### W9: 灵敏度分析必须存在
- 防御层次：L3 + L6（final-validator 复核）
- 承载 agent：section-writer（撰写 ±10%/±20% 扰动）+ final-validator（复核）

### W10: 模型评价必须诚实讨论缺点
- 防御层次：L1（structure-planner 规约评价节）
- 承载 agent：section-writer（撰写）

## Knowledge

本手引用以下知识资源（不在本 SKILL.md 重复内容，详见各 agent SKILL.md 的 Resources 段）：

- `core/Writer/knowledge/templates/` - LaTeX 论文模板（CUMCM/MCM/通用 + 学术期刊/学科/海报/幻灯片）
- `core/Writer/knowledge/writing/` - 11 个写作规范文档（abstract/assumption/result-presentation/transition-phrases/model-evaluation/forbidden-words/avoid-ai-writing-en/guidelines/latex-escape-cheatsheet/paper-structure-guide）
- `core/Writer/knowledge/reference/` - 3 个图表规范文档（figure-rules / figure-rules-enhanced / figure-guide）
- `core/Writer/knowledge/profiles/` - 10 个竞赛配置文档（cumcm-profile / cumcm-rules / profile-{classification,evaluation,mechanism,network,optimization,prediction,simulation,statistics}）
- `core/knowledge/paper-cases/` - 分析文档（INDEX / METHOD-MAPPING / INNOVATION-TAGS / CROSS-ANALYSIS / CODE-FRAMEWORKS + 2 个 JSON 图）
- `core/knowledge/validation/consistency_checker.py` - 本手数值一致性校验脚本
- `core/Writer/laws/rules.md` - 论文手铁律（W1-W10）
- `core/schemas/paper_spec.schema.json` - 结构化输出 Schema（L1）
- `core/Writer/templates/PAPER_SPEC_TEMPLATE.md` - PAPER_SPEC.md 输出格式模板
- `core/env/loader.py` - 环境变量加载器（`load_config()` / `get(key)`）
- `core/knowledge/validation/guardrails.py` - 运行时护栏（跨手共享）
- `core/knowledge/validation/hash_chain.py` - 哈希链审计（跨手共享）
- `core/knowledge/validation/process_verifier.py` - 上游过程验证器（参考）

## Output Contract

输出 `output/PAPER_SPEC.md`（格式见 `core/Writer/templates/PAPER_SPEC_TEMPLATE.md`）、`paper/main.pdf`、`work/audit_log.json`。

**输出有效性条件**（全部满足才算本手输出成功，由 final-validator 在 stage 7 校验）：

1. `output/PAPER_SPEC.md` 存在且非空
2. `paper/main.pdf` 存在且可被 PDF 阅读器打开
3. PAPER_SPEC 通过 `core/schemas/paper_spec.schema.json` 校验
4. 包含 5 个必要章节（摘要/问题重述/假设/模型建立/结果分析）
5. 摘要每个子问题有具体数值（铁律 W2）
6. 图表数 >= `get("paper.min_figures")`，表格数 >= `get("paper.min_tables")`
7. 公式数 >= `get("paper.min_equations")`
8. 参考文献数 >= `get("paper.min_references")`，全部 `verified == true`（铁律 W5）
9. 字数 >= `get("paper.min_words")`，PDF 页数 >= `get("paper.min_pages")`
10. 数值全部可追溯到 `all_results.json`（铁律 W1，consistency-checker `passed == true`）
11. 护栏检查通过（无禁用词、无占位符、无 AI 痕迹、无内部路径、无悬空 bib key / 图片，铁律 W5-W8，guardrails-checker `passed == true`）
12. 哈希审计日志完整，所有产物 sha256 已记录

任一条件不满足，由 final-validator 标记阻塞并按 Stage Gates 回退到对应 agent 修正，本手未通过即整体不向下游宣告完成。

## Iteration

当某 stage 自检不通过时：
1. 由失败 agent 在自身 SKILL.md 的 `## Iteration` 段说明回退修正策略。
2. 修正后重新进入该 stage 的自检。
3. 循环直到通过。
4. `runtime.strict_mode == True` 下，若某 agent 反复修正仍不通过，标记阻塞，本手未通过即整体回退（不强行推进到下游 Modeler/Programmer 协商之外）。
