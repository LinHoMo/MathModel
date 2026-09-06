# P11 Paper Quality Report — Controlled Scientific Expression 实施报告

## 1. 交付物

| 交付 | 位置 |
|---|---|
| 写作审计 | `docs/architecture/SCIENTIFIC_WRITING_AUDIT.md` |
| Expression Contract | `docs/architecture/EXPRESSION_CONTRACT.md` + `core/runtime/writing/expression.py` |
| Paragraph IR / ArgumentUnit / Planner / Bindings / Renderers | `core/runtime/writing/paragraphs.py` |
| WritingPattern 蒸馏（WP-001~007） | `core/runtime/writing/patterns.py` |
| Comparative 数值化（P11-4） | `core/runtime/writing/findings.py`（MetricComparison + decision rule 裁决） |
| 冗余/AI 模式检测（P11-17） | `core/runtime/writing/redundancy.py`（RED-1~6） |
| Claim 引用溯源 + W9（P11-5） | `handlers.py`（experiment_refs/literature_refs）+ `fact_check.py` |
| Abstract 结构化（P11-15） | `narrative_ir.py`（五要素：problem/method/key result/validation/contribution） |
| 红队 W1–W15 + A/B | `tests/integration/test_writing_redteam.py`（13 项）+ `test_controlled_expression.py`（20 项） |
| 本报告 | `docs/architecture/P11_PAPER_QUALITY_REPORT.md` |

## 2. 最终十二问的回答（任务书 §27）

1. **LLM 能否绕过 Narrative IR？** 不能——渲染器只接受 ExpressionInput
  （ParagraphPlan+最小权限 Context），无任何文件系统访问。
2. **LLM 能否创造 Research State？** 不能——渲染路径不产生 Artifact/Evidence/
  Decision；hard_reject 的输出直接丢弃。
3. **新数字能否进入论文？** 不能——RenderedNumbers ⊆ AllowedNumbers，违者
  hard_reject（W1 测试）。
4. **新 citation 能否进入论文？** 不能——RenderedCitations ⊆ bib（W2 测试）。
5. **dead claim 能否复活？** 不能——P11 FAIL（W6）。
6. **superseded result 能否复活？** 不能——P12/谱系退役（W5）。
7. **hypothesis 能否伪装 conclusion？** 不能——derive_conclusion 只取 PASS
  finding（W10）。
8. **Paper 可否由当前 Research State 完全重建？** **YES**——IR/Findings/Abstract
  全部派生式（G/H 幂等测试）。
9. **更换 Renderer 模型是否影响事实层？** **NO**——事实来自 Context 允许集，
  后验校验与渲染器无关。
10. **删除 Renderer 后确定性投影可否运行？** **YES**——llm_fn=None 退化为
  DeterministicRenderer；P10 路径完整保留。
11. **Controlled rendering 相比 baseline 提升了什么？** A/B 实测：解释密度提升
  （interpretation/limitation/sensitivity 段落由 ArgumentUnit 派生），冗余为 0，
  unsupported = 0。
12. **提升是语言表面还是论证质量？** 论证结构：每段带 purpose/required_content/
  evidence_level，"为什么存在"首次可回答。

## 3. 验收（P11 最终）

| 指标 | 结果 |
|---|---|
| pytest | 705 passed, 11 skipped, 0 failed |
| validate | 57/57, 0 warning |
| catalog | OK |
| doctor | 0 blocking |
| V3 execute | PASS（16/16） |
| Paper red-team W1–W15 | PASS（prevention + post-check 双层） |
| A/B | 事实不变（两边 0 blocker）+ B 解释密度 ≥ A + B 冗余 0 |

## 4. W1–W15 防线映射

| W | 攻击 | 防线（prevention / post-check） |
|---|---|---|
| W1 | 幻觉数字 | Context 最小权限 + RenderedNumbers ⊆ Allowed → hard_reject |
| W2 | 幻觉引用 | 同上（P7 回查） |
| W3/W4 | 未支撑 best/显著 | check_wording 硬禁 + RED-5 |
| W5 | 陈旧 superseded 结果 | 谱系退役 + P12 |
| W6 | 死 claim 复活 | P11 + derive_conclusion 只取 PASS |
| W9 | 文献 ≠ 自己的实验 | claim 双 refs + P2 literature 检查 |
| W10 | hypothesis 冒充 conclusion | 四态校准 + 结论派生 |
| W11 | 结论加新主张 | 结论只含 validated statements |
| W12 | 摘要陈旧数字 | 派生幂等（无缓存载体）+ P3 |
| W13 | 跨问题污染 | P9.5 L 已验 + finding 按 question 隔离 |
| W14/W15 | 冗余/因果滥用 | RED-1~6 + 措辞校准 |
