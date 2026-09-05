# 禁用词与表达规范（forbidden-words.md）

> 学术论文的"AI 味"来自某些高频表达模式。不是不能用这些词，而是不要滥用。
> 本文件基于 2020-2025 年国赛 92 篇获奖论文 + Beacon/PaperPip/Modex 工程实践总结。

---

## 一、必须替换的"AI 套话"

| 禁用/高风险表述 | 替代方案 | 原因 |
|--------------|---------|------|
| 深入探讨/深入研究 | 研究/分析/考察 | 虚词堆砌 |
| 至关重要/举足轻重 | 关键/重要 | 夸大 |
| 不难看出/显而易见/众所周知 | 删除整句开头 | 评委视角不是"你" |
| 在某种意义上/在某种程度上 | 删除或具体化为数值 | 模糊化不是学术语言 |
| 具有十分重要的意义 | 直接说为什么重要 | 套话 |
| 为...提供理论依据 | 直接说结论 | 论文不是申报书 |
| 研究表明/大量研究表明 | 引具体文献编号 [X] | 无引用就是忽悠 |
| 具有重要的理论意义和实践价值 | 删除 | 让评委判断 |
| 首先，/其次，/最后，/此外，/总而言之， | 段落间用自然过渡或"与此同时/另一方面" | 机械排比 = AI 痕迹 |
| 本文的创新点在于 | 直接描述贡献，让读者判断 | 宣称式写作不可信 |
| 本文的研究填补了...的空白 | 描述与已有工作的区别 | 空白需要证明 |
| 基于以上分析/综上所述 | 直接进入结论 | 冗余过渡 |
| 值得注意的是 | 删除整句开头或改写为具体说明 | 评委视角词（套话） |
| 创新性地 | 直接描述创新点，避免宣称式写作 | 宣称式写作 |
| 具有重要意义 | 直接说明为何重要（给依据） | 套话 |
| 实现了良好效果 | 用具体指标 + 数值替代 | 虚词堆砌 |
| 具有较高价值 | 用具体价值/数值替代 | 套话 |
| 在当今 | 删除或具体化为背景说明 | 虚词堆砌 |
| 随着.{0,12}的快速发展（正则） | 删除或改为具体趋势/数据描述 | 虚词堆砌/套话 |
| 参赛者 / 参赛队伍 / 我们团队 | 删除或改为"本研究" | 元叙述词（暴露参赛身份） |
| delve | 替换为具体动词 | 英文 AI 痕迹 |
| pivotal | 替换为具体形容词 | 英文 AI 痕迹 |
| tapestry | 删除（隐喻堆砌） | 英文 AI 痕迹 |
| underscore | 删除或改为具体动词 | 英文 AI 痕迹 |
| noteworthy | 删除或改为具体表述 | 英文 AI 痕迹 |
| It is worth noting that | 删除整句开头 | 英文评委视角词 |
| Importantly, | 删除整句开头 | 英文评委视角词 |
| Notably, | 删除整句开头 | 英文评委视角词 |
| 赋能 | 删除或改写 | 中文企业黑话（原 19 词基线） |
| 抓手 | 删除或改写 | 中文企业黑话（原 19 词基线） |
| 闭环 | 删除或改写 | 中文企业黑话（原 19 词基线） |
| 颗粒度 | 删除或改写 | 中文企业黑话（原 19 词基线） |
| 底层逻辑 | 删除或改写 | 中文企业黑话（原 19 词基线） |
| 打法 | 删除或改写 | 中文企业黑话（原 19 词基线） |
| 对齐 | 删除或改写 | 中文企业黑话（原 19 词基线） |
| 倒逼 | 删除或改写 | 中文企业黑话（原 19 词基线） |
| 复盘 | 删除或改写 | 中文企业黑话（原 19 词基线） |
| 作为 AI | 删除整句开头 | 元叙述词（暴露 AI 身份，原 19 词基线） |
| token | 删除或改写 | 英文内部术语（原 19 词基线） |

---

> **统一词表与频次规则**：本文件是禁用词 / 占位符 / 内部术语的**单一事实源**，对标 `mmagent-codex-main` 的 `writing_rules.md`（第 391-402 行 + 第 152-156 行）。上表已并入参考系统黑名单（中文新增 + 元叙述 + 英文 + 正则）。**频次规则**：同一套话（如"综上所述""值得注意的是"）在全文出现 **≥3 次** 记风险点（WARN），由 guardrails-checker 拦截。

## 二、中文学术写作用词规范（从 Beacon 铁规提炼）

### 2.1 冒号与括号规范

**正确**：`**关键词**：建模、优化`（冒号在 `**` 外面）
**错误**：`**关键词：**建模、优化`

**正确**：公式编号用半角括号 `(1)` `(2)`
**错误**：全角括号 `（1）` `（2）`

### 2.2 数字与单位

- 数字与单位之间加空格：`10 m`、`5 kg`（中文论文可用 `10m`、`5kg`，全文统一）
- 四位以上数字不加逗号分隔（中文习惯）：`10000` 不写 `10,000`
- 百分比：`15.3%` 不写 `百分之十五点三`

### 2.3 标点与排版

- **破折号**：全文总计不超过 2 处
- **分号**：≤2 个/千字
- **冒号+列表**：禁止连续 ≥3 段以冒号+列表开头
- **禁止连续 ≥5 段句数相同**
- 段落长度控制在 3-8 句，避免"一句一段"和"一段二十句"
- 中文标点用全角，英文+数字用半角
- 句号后跟一个空格（LaTeX 中不需手动加空格）

---

## 三、定性词的量化替代

| 模糊表述 | 替代方案 | 示例 |
|---------|---------|------|
| 效果很好 | 具体指标+数值 | "准确率从 78.3% 提升到 92.1%" |
| 显著提升 | p<0.01 + 效应量 | "t(28)=4.32, p<0.001, Cohen's d=1.58" |
| 基本一致 | 具体偏差 | "最大相对误差不超过 2.3%" |
| 趋于稳定 | 收敛判据 | "相邻两次迭代的目标函数变化<1e-6" |
| 略大于 | 具体数值 | "比 A 方法高出 3.7 个百分点" |

---

## 四、禁用与需要清洗的内部痕迹

### 4.1 绝对禁用（直接删除整句）

- TODO / FIXME / XXX / TBD / 待补 / 略 / 待补充 / 待续写 / 这里补 / 待完善
- PaperCritic / Claim / Evidence / Reasoning（流程痕迹泄漏）
- issue / 回应 / 超时
- 李华 / 张三 / 王五（测试数据名）
- `[待补充]` / `[数据缺失]` / `(此处需要数据)`

### 4.2 需要替换

| 内部痕迹 | 替换为 |
|---------|--------|
| 代码[数字] | 代码实现/编程求解 |
| 根据代码输出 | 计算结果表明 |
| LLM 生成 | （直接删除） |
| AI 辅助 | （直接删除） |
| 我/我们 | 本文/本研究（全文中文学术规范） |

### 4.3 内部术语泄露检测（论文正文出现即 FAIL）

> 对标 `mmagent-codex-main` 的 `writing_rules.md` 与 `writing_check.sh`。以下内部文件名 / 路径 / 产物名不得在论文正文出现：

- `MODEL_SPEC.md` / `CODE_DELIVERABLES.md` / `PAPER_SPEC.md`
- `all_results.json` / `RESULTS_REPORT` / `ANALYSIS_MODELING_REPORT` / `PROBLEM_ANALYSIS`
- `CLAUDE.md` / `AGENTS.md`
- `work/` / `_tmp/` / `figures/.*\.json`（正则）
- `.py` / `.ipynb` / `code/*.py` / `tmp/` / `__pycache__/` / `.pytest_cache/`

---

## 五、MCM/ICM 英文写作特殊规范

- 禁止中式英文：`in the following we will` → `we`
- 禁止过度被动语态，适当使用第一人称复数 we
- 数字与单位间加空格：`10 m`，不是 `10m`
- 缩写首次出现必须全称+括号：`Analytic Hierarchy Process (AHP)`

---

## 六、执行检查

写作完成后运行检查：
1. 全文搜索"首先|其次|最后"合计出现次数应 ≤3
2. 全文搜索"至关重要|举足轻重|显而易见|众所周知"返回空
3. 全文搜索"TODO|FIXME|待补|略"返回空
4. 全文搜索"PaperCritic|Claim|Evidence|Reasoning"返回空
5. 全文搜索"我们"→应仅在致谢/非正文中出现
6. 全文搜索半角冒号后紧跟`**`（检查 `**关键词：**` 模式）

---

## 七、AI 痕迹去除 Prompt 集（来源：awesome-ai-research-writing 26.9K star）

> 来源：[awesome-ai-research-writing](https://github.com/daniel-saqib/awesome-ai-research-writing)（GitHub 26.9K star，R10 调研发现）。
> 交叉验证：见 [knowledge/laws/cross-validation-record.md](../laws/cross-validation-record.md) X-03。
>
> 本节提供两层 prompt 模板用于去除 AI 痕迹：
> - **减法层**：识别并删除 AI tells（机械排比、虚词堆砌、套话）
> - **加法层**：注入个人 voice（场景化、具象化、对比化）
>
> 与 §一 至 §六 的规则检测互补：规则检测负责"硬匹配"，prompt 负责软重写。

### 7.1 减法层 — AI tells 识别清单

AI 生成文本的高频"指纹"（出现即视为 AI tells，需重写）：

| 类别 | 中文 tells | 英文 tells | 处置 |
|------|-----------|-----------|------|
| 机械排比 | 首先 / 其次 / 最后 / 此外 / 另外 | First, / Second, / Third, / Finally, / Moreover, / Furthermore, | 替换为自然过渡 |
| 虚词堆砌 | 深入探讨 / 深入研究 / 至关重要 / 举足轻重 / 具有重要意义 | delve into / in-depth study / paramount / pivotal / of great significance | 替换为具体动词 |
| 评委视角词 | 不难看出 / 显而易见 / 众所周知 / 显然 | it is obvious that / it is well known that / clearly / evidently | 删除整句开头 |
| 模糊量化 | 在某种意义上 / 在某种程度上 / 大量研究表明 / 研究表明 | in some sense / to some extent / studies show / research indicates | 替换为具体数值或文献编号 |
| 套话过渡 | 综上所述 / 基于以上分析 / 总而言之 | in summary / based on the above analysis / in conclusion | 直接进入结论 |
| 宣称式写作 | 本文的创新点在于 / 本文填补了...的空白 / 具有重要的理论意义和实践价值 | the innovation of this paper lies in / this paper fills the gap / has important theoretical and practical value | 删除；让读者自行判断 |
| 重复结构 | 连续 ≥3 段以"主语+谓语+宾语"开头 / 连续 ≥5 段句数相同 | repetitive sentence structures | 拆分长短句，错落节奏 |

### 7.2 减法层 Prompt 模板

#### 7.2.1 中文版

```text
你是一位严格的学术论文编辑，任务是识别并标记下文中的 AI tells（AI 生成痕迹）。

识别规则：
1. 机械排比：首先/其次/最后/此外/另外 等连续出现
2. 虚词堆砌：深入探讨/至关重要/举足轻重/具有重要意义 等
3. 评委视角词：不难看出/显而易见/众所周知/显然 等
4. 模糊量化：在某种意义上/研究表明（无引用） 等
5. 套话过渡：综上所述/基于以上分析 等
6. 宣称式写作：本文的创新点在于/填补了...的空白 等
7. 重复结构：连续 ≥3 段同结构开头

输出格式：
- 每条 AI tell 单独列出，包含：原文片段 / 类别 / 建议处置（删除/替换/重写）
- 末尾统计各类别总数

待审文本：
---
[在此粘贴待审文本]
---
```

#### 7.2.2 英文版

```text
You are a strict academic paper editor. Identify and flag AI tells in the text below.

Detection rules:
1. Mechanical enumeration: First/Second/Third/Finally/Moreover/Furthermore used in sequence
2. Filler phrases: delve into / in-depth study / paramount / pivotal / of great significance
3. Reviewer-perspective words: it is obvious that / it is well known that / clearly / evidently
4. Vague quantifiers: in some sense / to some extent / studies show (without citation)
5. Boilerplate transitions: in summary / based on the above analysis / in conclusion
6. Claim-style writing: the innovation of this paper lies in / fills the gap
7. Repetitive structure: ≥3 consecutive paragraphs with the same opening structure

Output format:
- List each AI tell with: original snippet / category / suggested action (delete/replace/rewrite)
- Provide a category count at the end

Text to review:
---
[paste text here]
---
```

### 7.3 加法层 — 个人 voice 注入策略

减法层删除 AI tells 后，文本可能变得"干瘪"。加法层负责注入个人 voice：

| 策略 | 含义 | 示例 |
|------|------|------|
| **场景化** | 将抽象主张落到具体场景 | ❌"该方法效果好" → ✅"在 2024 年国赛 A 题的龙-数独约束求解中，该方法将求解时间从 12.3s 降至 0.8s" |
| **具象化** | 用具体数值/案例替代模糊描述 | ❌"显著提升" → ✅"t(28)=4.32, p<0.001, Cohen's d=1.58" |
| **对比化** | 通过与已有工作对比突出差异 | ❌"本文创新" → ✅"与 Smith et al. (2023) 的暴力枚举相比，本文的约束传播在保持最优性的同时将复杂度从 O(2^n) 降至 O(n^2)" |
| **限定化** | 主动声明方法的边界 | ❌"适用于所有场景" → ✅"在 n ≤ 50 的小规模实例中表现稳定；当 n > 100 时需结合启发式剪枝" |
| **过程化** | 描述思考/试错过程，体现"人"在思考 | ❌"经分析我们选择 X" → ✅"初步尝试线性回归后发现 R²=0.32，残差呈异方差；改用广义可加模型后 R²=0.78" |

### 7.4 加法层 Prompt 模板

#### 7.4.1 中文版

```text
你是一位资深学术作者，任务是将下文从"AI 味干瘪"重写为"有个人 voice 的学术文本"。

重写原则：
1. 场景化：抽象主张落到具体场景（题号/数据/实验设置）
2. 具象化：用具体数值替代模糊描述（p 值/效应量/百分比/置信区间）
3. 对比化：通过与已有工作对比突出差异（引用文献编号 [X]）
4. 限定化：主动声明方法的边界与适用条件
5. 过程化：必要时描述思考/试错过程，体现"人"在思考

约束：
- 不得新增虚构数值或文献（仅基于原文已有信息重写）
- 不得引入新的 AI tells（参照减法层识别清单）
- 保持学术严谨，不口语化
- 中文标点用全角，公式中变量用斜体

输出格式：
- 重写后的全文
- 末尾列出"重写要点"（每条说明改了哪里、为什么改）

待重写文本：
---
[在此粘贴待重写文本]
---
```

#### 7.4.2 英文版

```text
You are a senior academic author. Rewrite the text below from "AI-flavored and dry" to "academic text with personal voice".

Rewriting principles:
1. Situate: ground abstract claims in concrete scenarios (problem ID / dataset / experimental setup)
2. Quantify: replace vague descriptions with concrete numbers (p-values / effect sizes / percentages / CIs)
3. Contrast: highlight differences by comparing with prior work (cite [X])
4. Delimit: proactively state method boundaries and applicability conditions
5. Processual: when needed, describe the thinking/trial-and-error process to show "a human is thinking"

Constraints:
- Do not invent new numbers or references (rewrite only based on existing information)
- Do not introduce new AI tells (refer to the subtraction layer list)
- Maintain academic rigor; avoid colloquialisms
- Use first-person plural "we" sparingly and only for methodological choices

Output format:
- The fully rewritten text
- A "rewriting notes" section at the end (each note: what was changed, why)

Text to rewrite:
---
[paste text here]
---
```

### 7.5 推荐使用流程

```
原始草稿
   ↓
[减法层 prompt] → 识别 AI tells 清单
   ↓
人工/agent 重写（按清单逐条处置）
   ↓
[加法层 prompt] → 注入个人 voice
   ↓
人工/agent 复核（确认无虚构数值/文献）
   ↓
运行 §六 执行检查（脚本硬匹配）
   ↓
运行 core/validators/modules/guardrails.py（D1-D5 维度 AI 痕迹检测）
   ↓
最终稿
```

### 7.6 与既有检测脚本的关系

| 工具 | 职责 | 触发时机 |
|------|------|---------|
| §一 至 §六 规则 | 硬匹配（关键词/正则） | 写作完成后立即检查 |
| `core/validators/modules/guardrails.py` | 占位符 / AI 痕迹（D1-D5）/ 句式人性化检测 | 终稿前 |
| **本节减法层 prompt** | 软重写（语义级 AI tells 识别） | 规则检测后、guardrails 前 |
| **本节加法层 prompt** | 软重写（注入个人 voice） | 减法层之后、guardrails 前 |

**优先级**：硬匹配规则 > 减法层 prompt > 加法层 prompt > 软检测脚本。任一环节 FAIL 必须回到上游修复。

---

## §八 LaTeX 转义清单

详见 [latex-escape-cheatsheet.md](latex-escape-cheatsheet.md)

---

## §九 英文模式库链接

详见 [avoid-ai-writing-en.md](avoid-ai-writing-en.md)

> **用途**：补全本文件 §1-7（中文模式为主）的英文 AI 痕迹模式库缺位。
>
> **覆盖**：53 类 AI tells（按语法 / 词汇 / 句式 / 逻辑 4 维分类）+ 80+ 英文高频 AI 词汇黑名单 + 30+ 英文 AI 句式黑名单 + 210+ 中文短语对照表 + 检测与改写示例（Before/After 对照）+ 与本文件 §1-7 的关系说明。
>
> **触发场景**：MCM/ICM 英文论文写作、学术路径英文期刊投稿、中文论文去 AI 化（§四 中文短语对照表）、终稿前 AI 检测（与本文件 §六 / §七 联合使用）。
>
> **交叉验证**：见 [knowledge/laws/cross-validation-record.md](../laws/cross-validation-record.md) P1-8 / C4-W1。
