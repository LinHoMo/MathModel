# MATLAB 到 Julia 转换报告

**项目名称:** {{PROJECT_NAME}}
**转换日期:** {{DATE}}
**转换工具:** syslab-matlab-to-julia skill v{{VERSION}}

---

## 一、项目概况

{{PROJECT_DESCRIPTION}}

| 项目 | 内容 |
|------|------|
| 原始路径 | {{SOURCE_PATH}} |
| 目标路径 | {{TARGET_PATH}} |
| MATLAB 版本 | {{MATLAB_VERSION}} |
| Julia 目标版本 | {{JULIA_VERSION}} |
| 转换模式 | {{TRANSLATION_MODE}} |
| 严格模式 | {{STRICT_MODE}} |
| 保留注释 | {{KEEP_COMMENTS}} |

---

## 二、转换统计

代码行统计标准：NBNC（非空非注释行）

| 指标 | 数量 |
|------|------|
| 处理文件总数 | {{TOTAL_FILES}} |
| 成功转换文件数 | {{SUCCESS_FILES}} |
| 跳过文件数 | {{SKIPPED_FILES}} |
| 失败文件数 | {{FAILED_FILES}} |
| MATLAB 代码行数 | {{MATLAB_LINES}} |
| Julia 代码行数 | {{JULIA_LINES}} |
| 函数数量 | {{TOTAL_FUNCTIONS}} |
| 类数量 | {{TOTAL_CLASSES}} |

### 2.1 目录分布

| 目录 | MATLAB 文件数 | Julia 文件数 | 说明 |
|------|---------------|--------------|------|
{{DIRECTORY_DISTRIBUTION}}

### 2.2 文件清单

| MATLAB 文件 | Julia 文件 | 状态 | 备注 |
|-------------|------------|------|------|
{{FILE_LIST_SUCCESS}}

### 2.3 未完成文件

| MATLAB 文件 | 状态 | 原因 |
|-------------|------|------|
{{UNFINISHED_FILES}}

---

## 三、映射与偏离

### 3.1 函数映射摘要

| MATLAB 函数 | Julia 函数 | 状态 | 备注 |
|-------------|-----------|------|------|
{{FUNCTION_MAPPING_SUMMARY}}

### 3.2 非 1:1 偏离摘要

| 源位置 | 目标位置 | 原因 | 影响范围 | 批准状态 |
|--------|----------|------|----------|----------|
{{DEVIATION_SUMMARY}}

---

## 四、问题摘要

| 级别 | 数量 | 已解决 | 遗留 |
|------|------|--------|------|
| Critical | {{CRITICAL_COUNT}} | {{CRITICAL_RESOLVED}} | {{CRITICAL_PENDING}} |
| Important | {{IMPORTANT_COUNT}} | {{IMPORTANT_RESOLVED}} | {{IMPORTANT_PENDING}} |
| Minor | {{MINOR_COUNT}} | {{MINOR_RESOLVED}} | {{MINOR_PENDING}} |
| **总计** | **{{ISSUE_TOTAL}}** | **{{ISSUE_RESOLVED}}** | **{{ISSUE_PENDING}}** |

详见：`docs/issues.md`

---

## 五、测试摘要

| 项目 | 结论 |
|------|------|
| 逐脚本测试 | {{SCRIPT_TEST_RESULT}} |
| 整体测试 | {{OVERALL_TEST_RESULT}} |
| 主入口脚本 | {{ENTRY_RESULT}} |
| 关键指标 | {{KEY_METRIC_RESULT}} |

详见：`docs/test_report.md`

---

## 六、交付确认

- [ ] `docs/plan.md` 已完成
- [ ] `docs/translation_report.md` 已完成
- [ ] `docs/test_design.md` 已完成
- [ ] `docs/test_report.md` 已完成
- [ ] `docs/issues.md` 已完成
- [ ] `docs/compliance_report.md` 已完成

---

## 七、结论与后续

### 7.1 总体结论

{{FINAL_CONCLUSION}}

### 7.2 后续建议

{{NEXT_STEPS}}

---

*本报告由 syslab-matlab-to-julia skill 自动生成*
