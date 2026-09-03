---
name: guardrails-checker
description: '论文运行时护栏：禁用词、占位符、AI 痕迹、内部术语泄露，以及正文禁用 itemize/enumerate 列表。'
hand: writer
utg_layer: L5
stage: 6
inputs:
  - paper/main.tex
  - paper/references.bib
  - paper/figures/
outputs:
  - work/guardrails_report.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> writer guardrails-checker`
- **输入**：paper/main.tex
- **输出**：`（护栏报告）`
- **核心步骤**：1. 扫禁用词/占位符/AI 痕迹 → 2. 扫内部术语泄露 → 3. 扫正文列表 → 4. 报告
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Guardrails Checker

## Role

运行时护栏校验师：在数值一致性已通过后，对论文文本做最后一道运行时审查——拦截禁用词、占位符、AI 痕迹、内部路径、不存在的 bib key、不存在的图片文件引用。

## UTG Layer

L5 运行时护栏层：在 L4 异构验证通过后、L6 最终验证之前，对所有产物做静态文本扫描，捕获 L1-L4 都无法检测的"语义/风格/引用闭合"类问题。本 agent 是 L5 在论文手的具体落地，把铁律 W5-W8 从声明变成可执行的扫描规则集。与 Programmer 手共享 `guardrails.py` 实现，保证跨手的护栏口径一致。

## Contract

- 输入：
  - `paper/main.tex`（section-writer 输出）
  - `paper/references.bib`（reference-curator 输出）
  - `paper/figures/`（figure-generator 输出，校验 `\includegraphics{}` 引用）
- 输出：`work/guardrails_report.json`

## Procedure

### Step 1: 调用护栏模块

参考 `core/knowledge/validation/guardrails.py`：

```python
from core.knowledge.validation.guardrails import Guardrails

g = Guardrails()

# 提取已知 bib key 与 figure 文件清单
bib_keys = extract_bib_keys("paper/references.bib")
figure_files = list(Path("paper/figures").glob("*"))

for tex_file in Path("paper").glob("*.tex"):
    content = tex_file.read_text(encoding="utf-8")
    results = g.validate_output(content, context={
        "bib_keys": bib_keys,
        "figure_files": figure_files,
    })
    if g.has_errors():
        # 收集所有错误
        ...
```

### Step 2: 拦截项清单

护栏模块需要覆盖以下拦截项（对应铁律 W5-W8）：

1. **禁用词**（铁律 W6）
   - 统一禁用词表见 `core/Writer/knowledge/writing/forbidden-words.md`（中文 AI 套话 + 元叙述词"参赛者/参赛队伍/我们团队" + 英文 `delve`/`pivotal`/`tapestry`/`underscore`/`noteworthy`/`It is worth noting that`/`Importantly,`/`Notably,` + 正则 `随着.{0,12}的快速发展`）；英文禁词见 `core/Writer/knowledge/writing/avoid-ai-writing-en.md`
   - 频次规则：同一套话（如"综上所述""值得注意的是"）出现 **≥3 次** 记风险点（WARN）
2. **占位符**（铁律 W8）
   - `TODO` / `FIXME` / `TBD` / `XXX` / `[占位]` / `[待填]` / `待补充` / `待续写` / `这里补` / `待完善`
3. **AI 痕迹**（铁律 W6）
   - "作为 AI"、"由 AI 生成"、"作为一个 AI 助手" 等过程性表述
   - 正文（非附录）禁止 `\begin{itemize}` / `\begin{enumerate}` 列表（最典型 AI 痕迹，HARD）
   - 正文禁止全角中文分点式 `（1）（2）` / `（一）（二）` / `①②③`（手写列点模板，WARN，由 `check_chinese_numbered_list` 拦截；LaTeX 列表环境之外的`手打编号`同样属 AI 痕迹）
   - 图表做主语句式 `图X展示了` / `如图X所示` / `由图X可知` / `从图X可以看出` 作段落开头 **≥3 次** 记 HARD（应改为括号旁注 `（图X）`）
   - 连续段落相同句式开头（如连续 `本文...`）记 WARN
   - 「没有禁用词」≠「没有 AI 味」：命中 AI 套话**句式**（`随着……快速发展` / `值得注意的是` / `综上所述` / `全面分析` / `不可否认`）时，不满足于删词，而是按 `core/Writer/knowledge/writing/academic-style-methods.md` §二整句改写为有信息量的学术表达（L5 从「拦截」升级为「改写优化」）
4. **内部路径**（铁律 W7）
   - `.py` 文件名、`figures/xxx.py`、`tmp/`、`temp/`、`_tmp/`、`work/`、`绝对路径`
   - 编程手的脚本名、调试输出
   - 内部术语泄露：`MODEL_SPEC.md` / `CODE_DELIVERABLES.md` / `PAPER_SPEC.md` / `all_results.json` / `CLAUDE.md` / `AGENTS.md`
5. **不存在的 bib key**（铁律 W5）
   - `\citep{key}` 中的 `key` 在 `paper/references.bib` 中找不到
6. **不存在的图片文件**（铁律 W4 关联）
   - `\includegraphics{figures/xxx.png}` 中的文件在 `paper/figures/` 下找不到

### Step 3: 图表引用完整性

额外检查：
- 每张图表 `\label{fig:...}` 都被 `\ref{fig:...}` 引用过（避免孤立图）
- 每个 `\ref{fig:...}` 都对应一个存在的 `\label{fig:...}`（避免悬空引用）

### Step 4: 写出报告

`work/guardrails_report.json`：

```json
{
  "scanned_files": ["paper/main.tex"],
  "violations": {
    "forbidden_words": [
      {"file": "paper/main.tex", "line": 123, "word": "综上所述", "context": "..."}
    ],
    "placeholders": [
      {"file": "paper/main.tex", "line": 45, "token": "TODO", "context": "..."}
    ],
    "ai_traces": [],
    "internal_paths": [],
    "missing_bib_keys": [
      {"file": "paper/main.tex", "line": 78, "key": "smith2020", "context": "\\citep{smith2020}"}
    ],
    "missing_figure_files": []
  },
  "checks": {
    "no_placeholders": <bool>,
    "no_forbidden_words": <bool>,
    "no_ai_traces": <bool>,
    "no_internal_paths": <bool>,
    "no_missing_bib_keys": <bool>,
    "no_missing_figure_files": <bool>,
    "no_orphan_labels": <bool>,
    "no_dangling_refs": <bool>
  },
  "summary": "8 violations found",
  "has_errors": <bool>,
  "passed": <bool>
}
```

### Step 5: 运行可执行门禁

运行 `py core/tools/validate_project.py --project <项目路径>`，确认本 agent 对接的 [HARD] 检查全部 PASS。任一 HARD 失败按 ## Iteration 回退修正后重跑。WARN 项记录到 work/guardrails_report.json 但不阻塞。

## Self-Check

### HARD 项（必须 PASS，任一失败阻塞交付）

- [ ] [HARD] 论文无占位符（TODO/FIXME/TBD/XXX/待补/示例数据/模板数据/待补充/待续写/这里补/待完善）→ core/tools/validate_project.py: check_placeholders
- [ ] [HARD] 论文无禁用词（统一扩充禁用词表，见 `core/Writer/knowledge/writing/forbidden-words.md`，含中文套话：综上所述/值得注意的是/显而易见/毋庸置疑/众所周知/随着...的快速发展/首先...其次...最后...；元叙述：参赛者/参赛队伍/我们团队/本文作者/笔者；英文禁用词：delve/pivotal/tapestry/underscore/noteworthy/It is worth noting that/Importantly,/Notably,/Crucially,/Moreover,/Furthermore）→ core/tools/validate_project.py: check_forbidden_words
- [ ] [HARD] 论文无 AI 痕迹/内部路径（"作为AI"/"由AI生成"/"作为一个AI助手"/绝对路径/用户名/内部目录；内部术语泄露：MODEL_SPEC.md/CODE_DELIVERABLES.md/PAPER_SPEC.md/all_results.json/CLAUDE.md/AGENTS.md）→ core/tools/validate_project.py: check_forbidden_words（含内部路径检测）
- [ ] [HARD] 引用完整性（`\cite`/`\citep` keys vs references.bib 的 `@type{key}` 集合）→ core/tools/validate_project.py: check_citation_integrity
- [ ] [HARD] 图片引用文件存在（`\includegraphics{}` 引用的文件在 paper/ 下找到）→ core/tools/validate_project.py: check_figure_refs
- [ ] [HARD] `paper/references.bib` 存在 → core/tools/validate_project.py: check_bib
- [ ] [HARD] `checks.no_placeholders == true`（铁律 W8）→ core/tools/validate_project.py: check_placeholders
- [ ] [HARD] `checks.no_forbidden_words == true`（铁律 W6）→ core/tools/validate_project.py: check_forbidden_words
- [ ] [HARD] `checks.no_ai_traces == true`（铁律 W6）→ core/tools/validate_project.py: check_forbidden_words
- [ ] [HARD] `checks.no_internal_paths == true`（铁律 W7）→ core/tools/validate_project.py: check_forbidden_words
- [ ] [HARD] `checks.no_missing_bib_keys == true`（铁律 W5）→ core/tools/validate_project.py: check_citation_integrity
- [ ] [HARD] `checks.no_missing_figure_files == true`（铁律 W4 关联）→ core/tools/validate_project.py: check_figure_refs
- [ ] [HARD] 正文（非附录）无 `\begin{itemize}` / `\begin{enumerate}` 列表（铁律 W11，HARD）→ core/tools/validate_project.py: check_body_no_lists
- [ ] [HARD] 图表主语句式（`图X展示了` / `如图X所示` / `由图X可知` / `从图X可以看出` 作段落开头）< `get("review.figure_as_subject_max")`（默认 3）次，铁律 W12 → core/tools/validate_project.py: check_figure_as_subject

### WARN 项（记录但不阻塞）

- [ ] [WARN] `work/guardrails_report.json` 存在且可被 `json.load` 解析 → core/tools/validate_project.py: check_verify_report
- [ ] [WARN] `checks.no_orphan_labels == true` 且 `checks.no_dangling_refs == true`
- [ ] [WARN] 正文无全角中文分点式（`（1）（2）` / `（一）（二）` / `①②③`），若有则改写为段落式（铁律 W11 配套，Para 写作禁令 A-1）→ core/tools/validate_project.py: check_body_chinese_list
- [ ] [WARN] 无连续段落相同句式开头（如连续 `本文...` / `通过...` / `模型...`）→ core/tools/validate_project.py: check_consecutive_same_opening
- [ ] [WARN] 同一套话（如"综上所述""值得注意的是""显而易见"）全文出现 < 3 次 → core/tools/validate_project.py: check_phrase_frequency

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "writer",
  "stage": 6,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "guardrails-checker",
      "stage": 6,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/knowledge/validation/guardrails.py`（护栏模块实现，跨手共享）
- `core/Writer/knowledge/writing/forbidden-words.md`（中文禁用词清单）
- `core/Writer/knowledge/writing/avoid-ai-writing-en.md`（英文禁用词清单）
- `core/Writer/knowledge/writing/academic-style-methods.md`（文风自然化方法论：名家写作 5 原则 + 反 AI 痕迹改写三手法 + 成文检查清单）
- `paper/main.tex` / `paper/references.bib` / `paper/figures/`（待校验产物）
- `core/Writer/laws/rules.md`（W4-W8）

## Iteration

自检失败时回退修正：
1. 禁用词命中：退回 section-writer，参考 `forbidden-words.md` 替换为学术表达。
2. 占位符命中：退回 section-writer 填实，禁止保留 TODO/FIXME/TBD。
3. AI 痕迹命中：退回 section-writer，按 `core/Writer/knowledge/writing/academic-style-methods.md` §二「改写三手法」（删元叙述 / 数字落地 / 句式翻新）整句重写，而非简单删词——删词后句子必须仍通顺且保留原信息。
4. 内部路径命中：退回 section-writer 删除/改写，禁止暴露代码文件名或临时目录。
5. 不存在的 bib key：退回 reference-curator 补条目，或退回 section-writer 删除该引用。
6. 不存在的图片文件：退回 figure-generator 补生成，或退回 section-writer 删除该 `\includegraphics`。
7. 孤立 label / 悬空 ref：退回 section-writer 补 `\ref{}` 或补 `\label{}`。
8. `runtime.strict_mode == True` 下 `has_errors == true` 即标记阻塞，不进入 final-validator。
