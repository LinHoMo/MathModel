# {{PROJECT_NAME}} MATLAB → Julia 测试报告

**项目名称**: {{PROJECT_NAME}}
**测试日期**: {{DATE}}
**测试执行者**: {{TESTER}}

---

## 一、测试摘要

| 类别 | 总数 | 通过 | 失败 | 阻塞 | 结论 |
|------|------|------|------|------|------|
| 逐脚本测试任务 | {{SCRIPT_TOTAL}} | {{SCRIPT_PASSED}} | {{SCRIPT_FAILED}} | {{SCRIPT_BLOCKED}} | {{SCRIPT_RESULT}} |
| 整体测试任务 | {{OVERALL_TOTAL}} | {{OVERALL_PASSED}} | {{OVERALL_FAILED}} | {{OVERALL_BLOCKED}} | {{OVERALL_RESULT}} |
| **总计** | **{{TOTAL_CASES}}** | **{{TOTAL_PASSED}}** | **{{TOTAL_FAILED}}** | **{{TOTAL_BLOCKED}}** | **{{TOTAL_RESULT}}** |

---

## 二、执行依据

| 项目 | 内容 |
|------|------|
| 转换计划 | `docs/plan.md` |
| 测试设计说明书 | `docs/test_design.md` |
| 问题清单 | `docs/issues.md` |

---

## 三、逐脚本测试结果

要求：本节应直接对应 `docs/plan.md` 中的 `test-script:<script>` 任务。

| 任务ID | 目标脚本 | 结果 | 测试入口 | 关键输出 | 偏差说明 | 问题编号 | 备注 |
|--------|----------|------|----------|----------|----------|----------|------|
{{SCRIPT_TEST_RESULTS}}

---

## 四、整体测试结果

要求：本节应直接对应 `docs/plan.md` 中的 `test-overall:<main-script>` 任务。

| 任务ID | 主脚本 / 入口脚本 | 结果 | 测试入口 | 主结论 | 关键指标对比 | 问题编号 | 备注 |
|--------|-------------------|------|----------|--------|--------------|----------|------|
{{OVERALL_TEST_RESULTS}}

---

## 五、关键指标对比摘要

| 指标名称 | MATLAB 值 | Julia 值 | 比较方式 | 容差要求 | 结论 |
|----------|-----------|----------|----------|----------|------|
{{KEY_METRIC_RESULTS}}

---

## 六、问题摘要

| 编号 | 级别 | 来源任务 | 问题描述 | 当前状态 |
|------|------|----------|----------|----------|
{{ISSUE_SUMMARY}}

---

## 七、任务状态回填确认

- [ ] 所有 `test-script:<script>` 任务状态已回填到 `docs/plan.md`
- [ ] 所有 `test-overall:<main-script>` 任务状态已回填到 `docs/plan.md`
- [ ] 阻塞项已写入 `docs/issues.md`

---

## 八、测试结论

### 8.1 逐脚本测试结论

{{SCRIPT_TEST_CONCLUSION}}

### 8.2 整体测试结论

{{OVERALL_TEST_CONCLUSION}}

### 8.3 总体结论

{{FINAL_CONCLUSION}}

---

*本测试报告由 syslab-matlab-to-julia skill 生成*
