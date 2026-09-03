# 示例任务

## 用户请求示例

请优化 `src/demo/main.jl` 的性能，要求保留现有输出精度与外部调用方式。

## 推荐执行方式

1. 先加载 `syslab-environment`，确认当前 Syslab 运行时与可用 `Ty*` 库。
2. 用 `../templates/performance-plan-template.md` 创建 `docs/performance-plan.md`。
3. 若入口已明确，运行 `julia ../scripts/analyze-script-deps.jl src/demo/main.jl`，把依赖分析结果回填到计划。
4. 按 `../rules/performance-analysis-rules.md` 建立基线与热点证据。
5. 在开始代码修改前，完成 `../rules/performance-checklist.md` 中的 A-H 检查。
6. 在计划中显式写出任务 ID，例如：
   - `baseline:src/demo/main.jl`
   - `precheck:src/demo/main.jl`
   - `optimize:src/demo/main.jl`
   - `verify:src/demo/main.jl`
   - `report:performance`
7. 按 `../workflows/performance-plan-execution-rules.md` 逐脚本推进优化，再生成 `docs/performance-report.md`。

## 预期产物

- `docs/performance-plan.md`
- `docs/performance-report.md`
- 逐脚本事实表、基线与复测证据
- 整体性能优化结论与剩余风险
