---
name: section-writer
description: '按字数预算逐节撰写 LaTeX 正文，产出 paper/main.tex。数值必须来自 all_results.json，禁止正文重新估算。'
hand: writer
utg_layer: L2
stage: 2
inputs:
  - work/paper_structure.json
  - CODE_DELIVERABLES.md
  - figures/all_results.json
outputs:
  - paper/main.tex
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> writer section-writer`
- **输入**：work/paper_structure.json + all_results.json
- **输出**：`paper/main.tex`
- **核心步骤**：1. 按预算逐节写 → 2. 数值只取 all_results.json → 3. 禁列表、禁图表做主语 → 4. 写 main.tex
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Section Writer

## Role

论文章节撰写师：按 structure-planner 给出的字数预算与章节顺序，逐节写出 LaTeX 正文，是论文正文唯一的写入方。

## UTG Layer

L2 工具调用与生成层：把结构化规约（paper_structure.json）落地为可执行/可编译的实体产物（main.tex）。本 agent 的"工具调用"约束体现为：必须使用 LaTeX 模板（不是自由发挥）、必须遵守图表引用语法（`\ref{}`/`\citep{}`）、必须按字数预算写作而非凭感觉。L2 在本手的目标是"让 L1 的规约变成具体可编译文本"，为后续 L3-L6 的验证提供真实输入。

## Contract

- 输入：
  - `work/paper_structure.json`（structure-planner 的输出，含字数预算、图表编号、模板路径）
  - `CODE_DELIVERABLES.md`（叙述性内容来源）
  - `figures/all_results.json`（数值来源，正文每个数字必须可追溯至此）
- 输出：`paper/main.tex`（基于选定模板的单文件 LaTeX 正文）

## Procedure

### Step 1: 加载结构与模板

读取 `work/paper_structure.json`，按 `latex_template_path` 复制模板到 `paper/main.tex`，保留模板的 preamble 与 cumcmthesis/mcmthesis 类文件不动。从 `env_snapshot` 取 `language` 与 `template` 决定中英文与排版风格。

### Step 2: 按字数预算逐节撰写

按 structure-planner 的 `sections` 数组顺序撰写，写作顺序遵循以下推荐（与原 Writer SKILL 一致）：

1. **问题重述与分析** → 参考 `core/Writer/knowledge/writing/paper-structure-guide.md`
2. **模型假设** → 参考 `core/Writer/knowledge/writing/assumption-writing.md`，每条假设必含必要性说明
3. **符号说明** → 表格形式，含量纲
4. **模型建立与求解**（每个子问题独立成节）→ 含问题分析(200-300字) / 模型建立(300-500字,>=3公式) / 模型求解(200-300字) / 结果分析(200-300字)
5. **结果分析与检验** → 参考 `core/Writer/knowledge/writing/result-presentation.md`
6. **灵敏度分析** → 参考 `core/Writer/knowledge/writing/result-presentation.md`，对关键参数±10%、±20%扰动
7. **模型评价与推广** → 参考 `core/Writer/knowledge/writing/model-evaluation-writing.md`，必须诚实讨论缺点
8. **摘要**（最后撰写，内容全部确定后）→ 参考 `core/Writer/knowledge/writing/abstract-writing.md`，每个子问题：方法+模型+关键结果(含数值)；摘要总字数 **400-600 字**（writing_rules 硬规格，摘要只能出现正文已有数字）；摘要须含 **3-5 个关键词**，LaTeX 中以 `\noindent\textbf{关键词：} A；B；C` 置于摘要正文之后、`\end{abstract}` 之前（与 `abstract-writing.md` 一致）
9. **参考文献** → 占位由 reference-curator 填实，本 agent 只写 `\cite{key}` 调用点（GB/T 7714 顺序编码制上标 `[n]`，**禁止** `\citep{}`/`\citet{}` 作者—年份格式）
10. **附录**（代码）

每节字数不得低于 `paper_structure.json` 中的 `word_budget`。

### Step 3: 写作风格守则

> **🚨🚨 段落式写作强制规范（借鉴 MathModelAgent-main writer.py + opendraft Crafter）🚨🚨**
>
> **严格禁止分点式论述（bullet points / numbered lists）出现在论文正文中。**
> 必须将分点式内容转换为流畅的论文级段落式语言。
>
> ❌ 错误示例（分点式）：
> ```
> 关键发现：
> 1. 龙头速度在外圈被放大
> 2. 最大速度约为 2.4 m/s
> 3. 碰撞发生在内圈第三圈
> ```
>
> ✅ 正确示例（段落式）：
> ```
> 速度分析揭示了运动学的放大效应。由于各把手沿同一等距螺线
> 运动且链长约束要求外圈把手走过更多的弧长，龙头恒定 1 m/s
> 的速度在各节板凳传递过程中逐步放大，最外圈把手的速度可
> 达到龙头速度的 2.4 倍。进一步观察碰撞发生位置，首次碰撞
> 出现在盘入第三圈靠近中心轴线的区域，此时相邻板凳间的
> 夹角判据首次被违反。
> ```

- 学术过渡词汇（必须使用，每节至少出现 2 个）：
  | 类型 | 过渡词 |
  |------|--------|
  | 递进 | 此外，进一步，同时，值得注意的是 |
  | 因果 | 因此，由此可得，基于上述分析 |
  | 转折 | 然而，尽管如此，与此相对 |
  | 举例 | 具体地，以...为例，观察可知 |
  | 总结 | 综上所述，总体来看 |
- 段落间关系：**递进式**——每段末尾为下一段铺垫，或每段开头承接上一段结论；避免"由此引出下节"等空洞过渡
- 避免"首先…其次…最后…"等口语化表达
- 每段 3-5 句成文，禁止 `\begin{itemize}` / `\begin{enumerate}` 列表（附录豁免，铁律 W11）
- **图片插入强制规范**：
  - 图前 ≥2 句引导，图后 ≥3 句分析；连续图表之间至少一个完整段落（≥100字）
  - 图表引用一律用括号旁注 `（图X）` / `（表X）`，**禁止**以图表作主语开头
  - **每张图后必须"呼应"该图的数据特征**——指出关键数值点（峰值、阈值、突变位点、对比结论），而非仅说"结果如图X所示"
  - **同一节 ≥2 个 figure 时，正文（去除图表后）≥1000 字符**，否则视为"图表堆砌缺乏分析"
- **CLAIM CALIBRATION（声明校准）— 来自 opendraft Crafter**：
  | ❌ 禁止表述 | ✅ 替换表述 |
  |------------|------------|
  | "我们发现了" / "我们分析了" | "结果显示" / "计算表明" |
  | "无可争议" / "证明了" | "结果表明" / "支持了" |
  | "最优方法"（无证明） | "本文采用的方法" |
  | "总是" / "从不" | "通常情况下" / "在本参数范围内" |
  | "广泛的共识表明" | "已有研究表明 [n]" |
- 文献引用一律用 `\cite{key}`，由导言区 `\usepackage[numbers,square,super]{natbib}` + 文末 `\bibliographystyle{gbt7714-numerical}` 渲染为右上角上标 `[n]`（**禁止** `\citep{}`/`\citet{}` 作者—年份格式）
- 禁止 AI 痕迹词汇（铁律 W6）：参考 `core/Writer/knowledge/writing/forbidden-words.md`
- 文风自然化（先结论后论证 / 具体化取代空泛形容词 / 长短句交替 / 主动语态优先 / 一段一中心）：参考 `core/Writer/knowledge/writing/academic-style-methods.md`
- 写作总纲：参考 `core/Writer/knowledge/writing/guidelines.md`
- LaTeX 转义：参考 `core/Writer/knowledge/writing/latex-escape-cheatsheet.md`

### Step 4: 数值写入

正文中出现的每个数字必须来自 `figures/all_results.json`，禁止在论文阶段重新估算或换一套四舍五入口径（铁律 W1）。摘要数值与正文数值必须一致（铁律 W2）。

### Step 5: 图表占位与引用

对 `paper_structure.json` 中的 `figure_plan`/`table_plan`：
- 在对应章节插入 `\begin{figure}\includegraphics{figures/fig_x_y.png}\caption{...}\label{fig:...}\end{figure}`
- 正文用 `\ref{fig:...}` 引用，前后留分析文字
- 实际图片文件由 figure-generator 负责落地，本 agent 只写引用语法

### Step 6: 自检字数与公式

写完后统计各节字数与全文公式数，写入 `paper/main.tex` 末尾注释 `% word_count: N` 与 `% equation_count: M`，供下游 consistency-checker 与 final-validator 校验。

## Self-Check

- [ ] `paper/main.tex` 存在且可被 `latexmk -xelatex`/`pdflatex` 编译（不报 fatal error）
- [ ] `python core/tools/writing_check.py <项目路径>` 全绿（0 errors），warnings 已记录
- [ ] 各章节字数 >= `paper_structure.json` 中对应 `word_budget`
- [ ] 公式数量 >= `equation_target`，每个子问题节 >=3
- [ ] 摘要每个子问题包含具体数值（铁律 W2），且摘要总字数 `get("paper.abstract_min_words")`（默认 400）– `get("paper.abstract_max_words")`（默认 600）字（铁律 W13）
- [ ] 每条假设有必要性说明（铁律 W3）
- [ ] **图片呼应检查**：每张图后有数据特征引用（峰值/阈值/突变位点），非空洞的"如图X所示"
- [ ] **图表-文字平衡**：同一节 ≥2 个 figure 时，正文（去图表后）≥1000 字符
- [ ] **段落式写作检查**：全文无 \begin{itemize}/\begin{enumerate}（附录豁免），每段 3-5 句
- [ ] **CLAIM CALIBRATION**：无"我们发现了"/"无可争议"/"总是"等禁止表述
- [ ] 每张图表前后有分析文字（铁律 W4），图表引用以括号旁注 `（图X）` / `（表X）`，以数据/结论为主语，图表引用放括号中，不以图表作主语开头（铁律 W12）
- [ ] 模型评价诚实讨论缺点（铁律 W10）
- [ ] 灵敏度分析存在且扰动幅度为 ±10%、±20%（铁律 W9）
- [ ] 正文中无 `forbidden-words.md` 列出的禁用词（铁律 W6，统一禁用词表）
- [ ] 正文中无 TODO/FIXME/TBD 占位符（铁律 W8）
- [ ] 正文中无内部文件名、脚命名、临时目录（铁律 W7）

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "writer",
  "stage": 2,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "section-writer",
      "stage": 2,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/Writer/knowledge/writing/paper-structure-guide.md`
- `core/Writer/knowledge/writing/abstract-writing.md`
- `core/Writer/knowledge/writing/assumption-writing.md`
- `core/Writer/knowledge/writing/result-presentation.md`
- `core/Writer/knowledge/writing/transition-phrases.md`
- `core/Writer/knowledge/writing/model-evaluation-writing.md`
- `core/Writer/knowledge/writing/forbidden-words.md`
- `core/Writer/knowledge/writing/avoid-ai-writing-en.md`
- `core/Writer/knowledge/writing/academic-style-methods.md`
- `core/Writer/knowledge/writing/guidelines.md`
- `core/Writer/knowledge/writing/latex-escape-cheatsheet.md`
- `core/Writer/knowledge/templates/mathmodel/zh/cumcm/main.tex`（CUMCM 中文模板）
- `core/Writer/knowledge/templates/mathmodel/en/mcm/main.tex`（MCM/ICM 英文模板）
- `core/Writer/knowledge/templates/mathmodel/generic/paper_template.tex`（通用模板）
- `core/Writer/laws/rules.md`（W1-W10 全部适用）

## Iteration

自检失败时回退修正：
1. 字数不足：扩充该节内容，优先补充模型推导细节或结果分析。
2. 公式不足：在模型建立节补充定义式、约束式或目标函数式。
3. 摘要缺数值：回查 `all_results.json`，把对应子问题的关键数值写入摘要。
4. 禁用词命中：参考 `forbidden-words.md` 替换为学术表达。
5. 图表前后缺分析：补引导句与分析段落（铁律 W4）。
6. 编译失败：定位 LaTeX 错误行，修语法；若模板类文件缺失，回退到 `generic/paper_template.tex`。
7. 自检仍不通过且 `runtime.strict_mode == True`：标记阻塞，不进入 figure-generator。
