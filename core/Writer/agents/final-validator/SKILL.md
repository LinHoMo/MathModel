---
name: final-validator
description: '最终校验、哈希审计与 PDF 渲染，产出 PAPER_SPEC.md 与 paper/main.pdf。全流程最后一步。'
hand: writer
utg_layer: L6
stage: 7
inputs:
  - paper/main.tex
  - paper/references.bib
  - paper/figures/
  - figures/all_results.json
  - work/paper_structure.json
  - work/consistency_report.json
  - work/guardrails_report_writer.json
  - core/env/config.yaml
outputs:
  - output/PAPER_SPEC.md
  - paper/main.pdf
  - paper/main.docx
  - work/audit_log.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> writer final-validator`
- **输入**：全部 Writer 产物
- **输出**：`output/PAPER_SPEC.md + paper/main.pdf`
- **核心步骤**：1. 最终校验 → 2. 哈希审计 → 3. 编译 PDF → 4. 交付
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Final Validator

## Role

最终校验师 + 哈希审计员 + 渲染器：在前 6 个 agent 全部通过后，按 `core/schemas/paper_spec.schema.json` 做最终结构校验，按 env 中所有 `paper.*` 阈值做最终阈值校验，渲染 `paper/main.pdf`，并产出哈希审计日志。

## UTG Layer

L6 事后验证层：在前 5 层都通过后，对全部产物做一次"事后"复核，包括 schema 校验、阈值复核、哈希链审计、PDF 渲染。L6 是 UTG 最后一道防线：捕获 L1-L5 漏网的结构错误、阈值不达、文件缺失、哈希链断裂。本 agent 是 L6 在论文手的具体落地，与 Programmer 手的 `hash_chain.py` 共享哈希实现，保证跨手审计可追溯。

## Contract

- 输入：前 6 个 agent 的全部产物 + env 配置
- 输出：
  - `output/PAPER_SPEC.md`（最终交付清单，符合 `core/Writer/templates/PAPER_SPEC_TEMPLATE.md` 格式）
  - `paper/main.pdf`（最终论文 PDF）
  - `work/audit_log.json`（哈希审计日志）

## Procedure

### Step 1: 读取所有阈值并复核

```python
from core.env.loader import get

thresholds = {
    "min_pages":      get("paper.min_pages"),       # >=17（软目标，国赛正文硬上限 20）
    "min_words":      get("paper.min_words"),       # >=13000
    "min_figures":    get("paper.min_figures"),     # >=6
    "min_tables":     get("paper.min_tables"),      # >=4
    "min_equations":  get("paper.min_equations"),   # >=15
    "min_references": get("paper.min_references"),   # >=10
}
runtime = {
    "template":   get("runtime.template"),
    "language":   get("runtime.language"),
    "strict_mode":get("runtime.strict_mode"),
}
```

复核各 agent 输出是否满足阈值：
- 实际页数（PDF 渲染后）>= `min_pages`
- 实际字数（统计 main.tex）>= `min_words`
- 实际图表数 >= `min_figures`
- 实际表格数 >= `min_tables`
- 实际公式数 >= `min_equations`
- 实际引用数 >= `min_references`

任一不达即退回对应 agent。

### Step 2: Schema 校验

读取 `core/schemas/paper_spec.schema.json`，构造 PAPER_SPEC dict 并校验：

```python
import json, jsonschema
spec = build_paper_spec(...)  # 从所有产物汇总
schema = json.load(open("core/schemas/paper_spec.schema.json"))
jsonschema.validate(spec, schema)
```

必填顶层字段：`paper_info` / `sections` / `figures` / `tables` / `references` / `traceability` / `quality_checks`。

各字段约束（与 schema 一致）：
- `paper_info.title` minLength 5
- `paper_info.template` enum [cumcm-zh, mcm-en, generic]
- `paper_info.target_pages` minimum 8（官方硬上限 20 页）
- `paper_info.word_count` minimum 13000
- `sections` minItems 5
- `figures` minItems 6，`id` 匹配 `^fig_`
- `tables` minItems 4，`id` 匹配 `^tab_`
- `references.count` minimum 10
- `quality_checks` 必填 6 项

### Step 3: 加载子报告

读取并复核下游子报告：
- `work/consistency_report.json`：`passed == true` 且 `numbers_traced == true`
- `work/guardrails_report_writer.json`：`passed == true` 且 `has_errors == false`
- `work/reference_report.json`（reference-curator 输出）：`passed == true`

任一子报告不通过即阻塞。

### Step 4: 渲染 PDF（策略由 `get("runtime.compile_pdf")` 决定）

**Step 4.0 工具链探测与策略分派**：先探测主机 LaTeX 工具链（`where xelatex` / `where latexmk`，或 `shutil.which("xelatex")`），再按策略执行：

| `runtime.compile_pdf` | 有工具链 | 无工具链 |
|---|---|---|
| `auto`（默认） | 自动编译，PDF 检查按 HARD 执行 | **仅交付 `paper/main.tex`**（必须完整可编译：无未闭合环境、\cite/\ref 均有定义、图片文件齐全），PDF 相关检查降级为 WARN，在 final_report.json 记 `pdf_skipped_reason: "no_latex_toolchain"` |
| `always` | 自动编译，HARD | HARD 失败，提示用户安装 TeX Live/MiKTeX |
| `never` | 不编译，仅交付 TEX，PDF 检查降级 WARN | 同左 |

```bash
cd paper
# 固定编译链：xelatex -> bibtex -> xelatex -> xelatex
# 两次 xelatex 用于解决交叉引用（\ref/\cite）在首次编译后未更新问题
xelatex -interaction=nonstopmode main.tex
bibtex main
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
# 或：latexmk -xelatex -interaction=nonstopmode main.tex
```

**无论何种策略，`paper/main.tex` 与 `paper/references.bib` 都是必交付物（HARD）**；PDF 仅在实际执行编译时校验存在、>100KB、页数 >= `min_pages`。若渲染失败：
1. 定位 LaTeX 错误行
2. 退回 section-writer 修正
3. 重新渲染

### Step 4.6: PDF 视觉检查（借鉴 6verify Step 8）

编译通过后，如果模型具备视觉能力，必须将 PDF 每页导出为 PNG 并逐页检查版式错误（纯文本扫描和编译器无法发现的硬错误）。优先使用系统已有工具：

```bash
mkdir -p _tmp/pdf-pages
if command -v pdftoppm >/dev/null 2>&1; then
  pdftoppm -png -r 160 paper/main.pdf _tmp/pdf-pages/page
elif command -v magick >/dev/null 2>&1; then
  magick -density 160 "paper/main.pdf" _tmp/pdf-pages/page-%03d.png
fi
```

逐页检查项：
- 页面是否空白、缺页、页数异常
- 标题/摘要/正文字体是否缺字、乱码
- 表格是否超出页边距、单元格文字是否重叠或被截断
- 图片/图题/表题/公式是否与正文重叠
- 公式是否越界或压到页边距
- 列表/段落/脚注是否有异常大空白、重叠或孤立残行
- 封面/摘要页/目录/附录是否保留比赛要求的视觉结构

如果模型无视觉能力，必须在 `work/audit_log.json` 中明确记录"未执行视觉检查"，并至少完成 PDF 非空/页数/页面尺寸等程序化检查。

视觉检查发现的版式错误按严重度分级：裁切/重叠/乱码 → FAIL；轻微越界 → WARN。

### Step 4.7: DOCX 交付（策略由 `get("runtime.deliver_docx")` 决定，可选交付分支）

| `runtime.deliver_docx` | 行为 |
|---|---|
| `never`（默认） | 跳过，零成本 |
| `auto` | 调用 `python core/tools/tex_to_docx.py paper/main.tex paper/main.docx` |
| `always` | 同上，强制产出并纳入哈希链；降级版必须存在并如实标注 |

**tex_to_docx.py 三引擎回退链**（已实现，无需另写脚本）：

| 优先级 | 引擎 | 质量 | 条件 |
|---|---|---|---|
| 1 | pandoc | 高质量（公式 → OMML，图/表全保留） | 主机已装 pandoc |
| 2 | OOXML 结构化降级（`build_docx_text()`） | 中等（三线表+编号公式+标题样式+图占位） | Python 标准库，零三方依赖 |
| 3 | 纯文本最小版（终极 fallback） | 最低（纯文本编号列表） | 仅当 build_docx_text 也失败时 |

**降级标注规则**：
- pandoc 成功 → 在 PAPER_SPEC.md 写"DOCX 由 pandoc 高质量转换"
- 结构化降级版 → 写"DOCX 为结构化降级版（三线表+编号公式，图表/复杂公式以占位说明标注），正式评审以 main.pdf 为准"
- 纯文本版 → 写"DOCX 为纯文本降级版（图表/公式均未迁移），正式评审以 main.pdf 为准"

### Step 5: 哈希链审计

参考 `core/validators/modules/hash_chain.py`：

```python
from core.knowledge.validation.hash_chain import compute_hash, verify_chain

artifacts = {
    "paper/main.tex":       compute_hash("paper/main.tex"),
    "paper/main.pdf":       compute_hash("paper/main.pdf"),
    "paper/references.bib": compute_hash("paper/references.bib"),
    "output/PAPER_SPEC.md": compute_hash("output/PAPER_SPEC.md"),
}
```

写入 `work/audit_log.json`：

```json
{
  "audit_time": "<ISO8601>",
  "artifacts": {
    "paper/main.tex":       {"sha256": "...", "size": <int>},
    "paper/main.pdf":       {"sha256": "...", "size": <int>, "pages": <int>},
    "paper/references.bib": {"sha256": "...", "size": <int>},
    "output/PAPER_SPEC.md": {"sha256": "...", "size": <int>}
  },
  "thresholds": {...},
  "thresholds_passed": true,
  "schema_valid": true,
  "sub_reports": {
    "consistency": "passed",
    "guardrails":  "passed",
    "reference":   "passed"
  },
  "render": {"tool": "latexmk -xelatex", "exit_code": 0, "pages": <int>},
  "final_passed": true
}
```

### Step 6: 写出 PAPER_SPEC.md

按 `core/Writer/templates/PAPER_SPEC_TEMPLATE.md` 格式输出到 `output/PAPER_SPEC.md`，包含：
1. 论文文件清单（main.pdf / main.tex / references.bib）
2. 论文结构（章节 checklist）
3. 数值结果汇总（每个子问题关键指标 + 来源）
4. 图表清单
5. 参考文献清单
6. 校验结果（数值一致性 / 引用完整性 / 图表引用 / 占位符 / 禁用词）
7. 已知问题
8. 改进建议

### Step 7: 运行可执行门禁

运行 `py core/tools/validate_project.py --project <项目路径>`，确认本 agent 对接的 [HARD] 检查全部 PASS，退出码 0。任一 HARD 失败按 ## Iteration 回退修正后重跑。WARN 项记录到 work/audit_log.json 但不阻塞。`runtime.strict_mode == True` 时任一 HARD 失败即阻塞，不向上游宣告完成。

## Self-Check

### HARD 项（必须 PASS，任一失败阻塞交付）

- [ ] [HARD*] `paper/main.pdf` 存在且字节数 >= `get("paper.pdf_min_bytes")`（默认 102400，即 100KB）→ core/tools/validate_project.py: check_pdf（*仅当实际执行编译时为 HARD；`compile_pdf=auto` 且主机无 LaTeX 工具链、或 `compile_pdf=never` 时降级 WARN，改为 HARD 校验 main.tex 完整可编译）
- [ ] [HARD] `paper/main.tex`（或 main.md/main.typ）存在 → core/tools/validate_project.py: check_source
- [ ] [HARD*] PDF 页数 >= `get("paper.min_pages")`（默认 17，软目标）且 <= `get("paper.max_pages")`（默认 20，国赛硬上限）→ core/tools/validate_project.py: check_paper_pages（*未编译时降级 WARN，用 est_pages=总字符/`chars_per_page` 估算校验）
- [ ] [HARD] 字数 >= `get("paper.min_words")`（默认 13000）→ core/tools/validate_project.py: check_paper_words
- [ ] [HARD] 图数 >= `get("paper.min_figures")`（默认 6）→ core/tools/validate_project.py: check_paper_figures
- [ ] [HARD] 表数 >= `get("paper.min_tables")`（默认 4）→ core/tools/validate_project.py: check_paper_tables
- [ ] [HARD] 公式数 >= `get("paper.min_equations")`（默认 15）→ core/tools/validate_project.py: check_paper_equations
- [ ] [HARD] 引用数 >= `get("paper.min_references")`（默认 10）→ core/tools/validate_project.py: check_paper_references
- [ ] [HARD] LaTeX 编译链：`xelatex → bibtex → xelatex → xelatex`（引擎从 `get("runtime.latex_engine")` 读取，默认 xelatex）→ core/tools/validate_project.py: check_pdf_compile_chain
- [ ] [HARD] 版面填充率 >= `get("paper.page_fill_ratio")`（默认 0.8，即 80%，铁律 W14）→ core/tools/validate_project.py: check_page_fill_ratio
- [ ] [HARD] `output/PAPER_SPEC.md` 存在且非空 → core/schemas/paper_spec.schema.json
- [ ] [HARD] `output/PAPER_SPEC.md` 符合 `core/Writer/templates/PAPER_SPEC_TEMPLATE.md` 格式
- [ ] [HARD] 构造的 PAPER_SPEC dict 通过 `core/schemas/paper_spec.schema.json` 校验 → core/schemas/paper_spec.schema.json
- [ ] [HARD] 哈希链 `verify_chain() == True` → core/validators/modules/hash_chain.py
- [ ] [HARD] `work/consistency_report.json` `passed == true`
- [ ] [HARD] `work/guardrails_report_writer.json` `passed == true`
- [ ] [HARD] 子报告全 passed（consistency/guardrails/reference）
- [ ] [HARD] 编译产物无 undefined references（`grep 'undefined' main.log` 为空；交叉引用/文献均解析）→ core/tools/validate_project.py: check_no_undefined_refs
- [ ] [HARD] 正文（非附录）无 `\begin{itemize}` / `\begin{enumerate}` 列表（铁律 W11）→ core/tools/validate_project.py: check_body_no_lists
- [ ] [HARD] `work/audit_log.json` 含所有产物的 sha256 哈希 → core/validators/modules/hash_chain.py
- [ ] [HARD] `final_passed == true`

### WARN 项（记录但不阻塞；机理类赛题 is_physics=True 时升 HARD）

- [ ] [WARN] 论文含坐标系定义 → core/tools/validate_project.py: check_coordinate_system
- [ ] [WARN] 分析报告含物理过程校验表（坐标系/实体/轨迹/解析）→ core/tools/validate_project.py: check_analysis_report_physics
- [ ] [WARN] 代码 z 轴符号一致性 → core/tools/validate_project.py: check_code_coordinate_consistency
- [ ] [WARN] 几何判定（点到线段距离 + 投影区间）→ core/tools/validate_project.py: check_geometry_criterion
- [ ] [WARN] 解析验证/基准误差记录 → core/tools/validate_project.py: check_analytic_validation
- [ ] [WARN] 时间边界 T_MAX 约束 → core/tools/validate_project.py: check_time_bounds
- [ ] [WARN] `runtime.deliver_docx != never` 时产出 `paper/main.docx`（三引擎回退：pandoc 高质量 → OOXML 结构化降级 → 纯文本最小版），并纳入 PAPER_SPEC.md 交付清单与哈希链 artifacts；降级版在「已知问题」如实标注

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "writer",
  "stage": 7,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "final-validator",
      "stage": 7,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/schemas/paper_spec.schema.json`（最终结构化校验 schema）
- `core/Writer/templates/PAPER_SPEC_TEMPLATE.md`（输出格式模板）
- `core/validators/modules/hash_chain.py`（哈希链审计实现，跨手共享）
- `core/validators/modules/process_verifier.py`（可选：上游 Programmer 的过程验证器，复核 traceability）
- `core/Writer/knowledge/docx-delivery.md`（DOCX 交付线规则：LaTeX 主线 + DOCX 交付分支，策略 never/auto/always）
- `core/tools/tex_to_docx.py`（LaTeX→DOCX 转换工具，零依赖，优先 pandoc 无则纯文本降级）
- `core/env/loader.py`（读取所有 `paper.*` 与 `runtime.*` 阈值）
- `core/Writer/laws/rules.md`（W1-W14 全部对应本 agent 的最终复核项）
- `core/Writer/laws/COMPLETE_PAPER_LAW.md`（最终交付规则单一真相源，本 agent 执行其"最终门禁"）
- `work/paper_structure.json` / `work/consistency_report.json` / `work/guardrails_report_writer.json` / `work/reference_report.json`（下游子报告）

## Iteration

自检失败时回退修正：
1. Schema 校验失败：定位缺失字段，退回对应 agent 补全（如缺 `references` 退回 reference-curator）。
2. 阈值不达：
   - 字数不足 → 退回 section-writer 扩写
   - 图表不足 → 退回 figure-generator 补生成
   - 引用不足 → 退回 reference-curator 补条目 + section-writer 补 `\citep{}`
   - 公式不足 → 退回 section-writer 补公式
   - 页数不足 → 退回 section-writer 扩写或调整排版（不可缩字号/行距作弊）
3. 子报告不通过：退回对应 agent 修正后重新进入本 agent。
4. PDF 渲染失败：定位 LaTeX 错误行，退回 section-writer 修语法；若模板类文件缺失，回退 `generic/paper_template.tex` 重渲染。
5. 哈希链断裂：定位被篡改文件，重算哈希并复核。
6. `runtime.strict_mode == True` 下 `final_passed == false` 即标记阻塞，不向上游 Modeler/Programmer 手宣告完成；论文手输出未通过即整体回退。

## External Skills

本 agent 可使用以下外部 skill：

- **latex-compiler**: 编译 LaTeX 文件为 PDF
  - 类型: system
  - 必需: false
  - 降级策略: 仅交付 .tex 源文件，不编译 PDF（从 env/runtime.compile_pdf 读取策略）
