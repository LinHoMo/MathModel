# 负样本：正文使用 itemize / enumerate 列表

> 对应反模式：antipatterns.md #24「正文使用 itemize / enumerate 列表——最典型的 AI 痕迹」

## 问题切片

某论文"模型假设"与"结果分析"两节中出现大量 LaTeX 列表，例如：

```latex
本模型的优势主要体现在以下几点：
\begin{itemize}
    \item 计算效率高，求解时间短；
    \item 可扩展性强，适用于不同规模的问题；
    \item 结果直观，便于工程人员理解。
\end{itemize}

问题二的求解步骤为：
\begin{enumerate}
    \item 建立以总成本最小为目标的整数规划模型；
    \item 利用 CPLEX 求解器进行求解；
    \item 对所得解进行敏感性分析。
\end{enumerate}
```

全篇累计出现 9 处 `itemize` / `enumerate`，分布在摘要之后、每问开头、结论之前，
几乎每一段核心内容都是"先列个表、再展开"。假设一节更是把 8 条假设直直地叠成一个
`enumerate`。

## 失分归因

1. **命中 #24 原文"正文使用 itemize / enumerate 列表"**：这是反模式清单里标注的
   **最典型 AI 痕迹**。大模型生成文本天然倾向"分点罗列"，评委一眼可辨；竞赛论文
   正文应使用连贯段落，列表形式留给论文外的 checklist（如本题解的附录/说明书），
   而非 `\section` 正文。——严重度 `major`。
2. **累加到 9 处意味着不是偶发**：即使单看一处只是"风格问题"，密度一高就构成
   weakness-hunter 的 `major` 命中，且是"全文写作风格"范畴，回退范围是 section-writer
   整节，而非改一两个 `\item`。
3. 列表还会**掩盖论证缺失**：`itemize` 的三条"优势"没有数据支撑（"求解时间短"是
   多短？"可扩展性强"用什么证据？），本质上是 #23「图表/要点前后没有分析文字」的
   变体——列表让"堆砌而不分析"更容易发生。

## 正确做法

| 错误 | 修正 |
|---|---|
| `\begin{itemize}\item 计算效率高…\end{itemize}` | 改写为连贯段落："相较穷举法，本模型的求解时间从 O(n!) 降至 O(n²)，在 200 节点的实例上由 30 分钟缩短到 2.3 秒（见 4.2 节表 2）" |
| 8 条假设叠成 `enumerate` | 假设在正文中逐条用**陈述句 + 必要性一句**展开（每个假设一段），编号只在文内以"假设 1"字样自然出现，不用 `enumerate` 环境 |
| 求解步骤用 `enumerate` | 把步骤写进**流程描述段**（"首先…随后…最后…"），或把步骤移入算法伪代码（`algorithm` 环境），正文只做文字串联 |
| 核心段落统统"先列表后展开" | 删除列表，直接在段落里给出结论 → 数据 → 解读的因果链 |

可转成 revision-planner 验收标准：`grep -n 'itemize\|enumerate' paper/main.tex` 输出为空
（除参考文献等允许位置）；若确有架构性罗列需求，改放"附录/说明书/伪代码"，正文零列表。

## 涉及阶段

- **产生环节**：
  - Writer 手 `section-writer`（L2 撰写正文时把内容写成了列表，是 AI 痕迹高发点）；
  - Writer 手 `structure-planner`（L1 未在结构规范里明确"正文禁用 itemize/enumerate"）。
- **检出环节**：
  - Writer 手 `guardrails-checker`（L5 运行时护栏，禁用词/占位符/AI 痕迹，本应拦截，
    若漏检即该 agent 失职）；
  - Reviewer 手 `weakness-hunter`（扫描命中 `antipatterns#24`，严重度 major）。
- **回退建议**：纯写作风格问题 → 只回 `section-writer`，不动代码（revision-planner 的
  "全文写作风格问题"局部回修路径）。locks 门禁若已内置 `itemize` 检测，则 `guardrails-checker`
  应能自动挡下，否则需在护栏规则里补一条。