# 完整论文铁律

本文件是 MathModelSkills 最终交付规则的单一真相源，优先级高于任何 skill、profile、提示词或历史说明。由 final-validator（L6）执行最终门禁。

## 最终交付物

必须交付完整且最新的 `paper/main.pdf`。提纲、章节草稿、源文件、代码、图表或验证报告均不能替代最终 PDF。

完整论文至少包含适用的题名与摘要、问题重述与分析、假设、符号说明、模型建立与求解、结果分析与检验、灵敏度分析、模型评价与推广、真实参考文献。profile 可增加要求，不得削弱此契约。

## 项目真相源

- 配置：`core/env/config.yaml`。
- 运行状态：`projects/<项目>/work/state.json`。
- 数值账本：`projects/<项目>/figures/all_results.json`。
- 论文源：`projects/<项目>/paper/main.tex`（或 main.typ）。
- 最终论文：`projects/<项目>/paper/main.pdf`。
- 验证记录：`projects/<项目>/work/audit_log.json`、`consistency_report.json`、`guardrails_report.json`。
- 改进记录：`work/execution_report.json`（Reviewer 手产出）。

论文中的每个定量结果必须能从账本追溯到计算入口、参数、单位和产物。不得直接修改正文数字来掩盖计算差异（铁律 W1 / P2）。

## 最终门禁

```powershell
py validate_project.py --project projects/<项目>
```

适用检查全部为 `PASS` 才成功。`FAIL` 表示业务条件未满足；`ERROR` 表示依赖、网络或执行异常；`NOT_APPLICABLE` 仅用于确实没有触发条件的检查。最终门禁不得把警告、跳过或异常解释为成功。

以下阶段不可跳过（force）：

- `writer.section-writer`
- `writer.guardrails-checker`
- `writer.final-validator`

## 必须阻塞的情形

- `paper/main.pdf` 缺失、过小、损坏或不是当前源文件的完整渲染。
- 论文或提交材料含占位符、模板残留或内部 AI 工作痕迹。
- `figures/all_results.json` 缺失、无效，或定量结论无法追溯。
- 引用虚构、符号或单位矛盾、适用质量阈值失败。
- 显式启用的 external_skill 缺依赖、网络失败或执行异常。
- 任一适用检查为 `FAIL` 或 `ERROR`。

## 渲染主线

LaTeX 是完整门禁主线；Typst 为可选渲染器。任何渲染器都必须落到同一个 `paper/main.pdf` 契约。编译策略由 `get("runtime.compile_pdf")` 控制（`auto` 默认：有工具链即编译，无工具链仅交付 main.tex 并降级 WARN）。