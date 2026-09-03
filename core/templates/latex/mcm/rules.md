# MCM/ICM 规则要点

> **核对日期**：2026-08-30
> **重要**：COMAP 的要求每年更新，**提交前必须重新核对当届 Instructions**。

## 排版

- 引擎：pdfLaTeX（英文论文，无需 ctex）
- 正文字号：不小于 12pt
- 页数上限：25 页（**含**摘要页、正文、参考文献、附录）
- 第一页必须是 Summary Sheet，且单独占一页

## Summary Sheet（摘要页）专项规范

> 评委先读摘要页，一页定第一印象；美赛摘要质量对奖项影响极大。

结构清单（自上而下）：

1. **Problem Restatement**：2–4 句，用自己的话复述核心问题，禁止照抄题面
2. **Assumptions**：只列影响结论的关键假设（3–5 条），每条一句话
3. **Models & Methods**：每个子问题一句"用了什么模型、怎么求解"
4. **Results**：给出具体数值结论（带单位），这是评委扫读的重点
5. **Strengths & Weaknesses**：各 2–3 条，弱点要真实但可补救
6. **Keywords**：4–6 个，与正文术语一致

长度与口径：

- 摘要正文控制在 **一页以内**（含题目与承诺声明区），通常 400–700 词
- 结果数字必须与正文一致（冻结机制同源：`figures/all_results.json`），
  不允许摘要出现正文没有的"更好"数字
- 不出现引用、图表引用、缩写首次不解释

常见失分：

- 只有方法罗列、没有任何数值结论（评委无从判断是否解出）
- 摘要与正文结论不一致（如最优值不同）——一致性检查必查项
- 用"we will discuss..."等过程式措辞替代结论式陈述

## AI 使用

- COMAP 目前允许**已披露**的 AI 协助
- 必须提交 AI Use Report，随论文一起上传
- 用 `core/tools/render_ai_usage.py` <项目> render --competition mcm 生成，
  并接入 `paper/main.tex` 主模板
- 未披露而使用，可能被判违规

## 写作

- 英文写作，避免 AI 高频套话（"delve""pivotal""tapestry""It is worth noting that"）
- 禁用词表见 `core/Writer/knowledge/writing/avoid-ai-writing-en.md`
- 结论要明确回扣题目要求，不要只陈述做了什么

## 常见失分点

见本包 `antipatterns.md`。

## 官方入口

- COMAP 官网 Instructions（当届）
- 提交前核对：页数、字号、Summary Sheet、AI Use Report 四项
