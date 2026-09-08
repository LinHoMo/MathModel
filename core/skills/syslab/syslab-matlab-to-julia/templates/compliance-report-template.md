# 工作流遵从性检查报告

**项目名称**: {{PROJECT_NAME}}
**检查日期**: {{DATE}}
**检查人**: {{INSPECTOR}}
**检查依据**: `syslab-matlab-to-julia` skill

---

## 一、检查摘要

| 类别 | 通过数 | 总数 | 状态 |
|------|--------|------|------|
| 前置与解析 | {{PRE_PASSED}} | 7 | {{PRE_STATUS}} |
| 计划 | {{PLAN_PASSED}} | 9 | {{PLAN_STATUS}} |
| 转换 | {{CONVERT_PASSED}} | 9 | {{CONVERT_STATUS}} |
| 测试 | {{TEST_PASSED}} | 7 | {{TEST_STATUS}} |
| 报告与完成 | {{FINAL_PASSED}} | 7 | {{FINAL_STATUS}} |
| **总计** | **{{TOTAL_PASSED}}** | **39** | **{{TOTAL_STATUS}}** |

---

## 二、前置与解析检查

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 已首先阅读 `high_frequency_conversion_differences.md` | {{PRE_1_STATUS}} | {{PRE_1_NOTE}} |
| 已识别入口脚本 | {{PRE_2_STATUS}} | {{PRE_2_NOTE}} |
| 已盘点 `.m` 文件、NBNC 行数和目录结构 | {{PRE_3_STATUS}} | {{PRE_3_NOTE}} |
| 已识别工具箱依赖 | {{PRE_4_STATUS}} | {{PRE_4_NOTE}} |
| 已生成依赖关系图 | {{PRE_5_STATUS}} | {{PRE_5_NOTE}} |
| 已生成函数映射待办表 | {{PRE_6_STATUS}} | {{PRE_6_NOTE}} |
| 已读取所有被调用函数的完整实现 | {{PRE_7_STATUS}} | {{PRE_7_NOTE}} |

---

## 三、计划检查

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 已创建 `docs/plan.md` | {{PLAN_1_STATUS}} | {{PLAN_1_NOTE}} |
| 计划中已写入 `.m` 到 `.jl` 的一对一映射表 | {{PLAN_2_STATUS}} | {{PLAN_2_NOTE}} |
| 已写入逐脚本转换任务列表 | {{PLAN_3_STATUS}} | {{PLAN_3_NOTE}} |
| 已写入逐脚本测试任务列表 | {{PLAN_4_STATUS}} | {{PLAN_4_NOTE}} |
| 已写入整体测试任务列表 | {{PLAN_5_STATUS}} | {{PLAN_5_NOTE}} |
| 已写入报告任务列表 | {{PLAN_6_STATUS}} | {{PLAN_6_NOTE}} |
| 逐脚本转换任务满足“一脚本一任务” | {{PLAN_7_STATUS}} | {{PLAN_7_NOTE}} |
| 每个 `.m` 文件只生成 1 个目标 `.jl` 文件 | {{PLAN_8_STATUS}} | {{PLAN_8_NOTE}} |
| 每个主脚本 / 入口脚本都有对应整体测试任务 | {{PLAN_9_STATUS}} | {{PLAN_9_NOTE}} |

---

## 四、转换检查

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 每个待转换脚本开转前已对照高频转换差异 | {{CONVERT_1_STATUS}} | {{CONVERT_1_NOTE}} |
| 每个 MATLAB 函数都先做函数映射 | {{CONVERT_2_STATUS}} | {{CONVERT_2_NOTE}} |
| 每个 `.m` 文件都有唯一目标 `.jl` 文件 | {{CONVERT_3_STATUS}} | {{CONVERT_3_NOTE}} |
| 保留原始注释 | {{CONVERT_4_STATUS}} | {{CONVERT_4_NOTE}} |
| 每个转换后的 Julia 文件都完成基本语法检查 | {{CONVERT_5_STATUS}} | {{CONVERT_5_NOTE}} |
| 无法直接迁移的内容已记录到 `docs/issues.md` | {{CONVERT_6_STATUS}} | {{CONVERT_6_NOTE}} |
| 未发生未获批准的合并 / 拆分 / 重命名 / 算法重写 | {{CONVERT_7_STATUS}} | {{CONVERT_7_NOTE}} |
| 原始 MATLAB 代码未被修改 | {{CONVERT_8_STATUS}} | {{CONVERT_8_NOTE}} |
| 所有 `convert:<script>` 任务都有明确状态 | {{CONVERT_9_STATUS}} | {{CONVERT_9_NOTE}} |

---

## 五、测试检查

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 每个已转换脚本都有对应 `test-script:<script>` 任务 | {{TEST_1_STATUS}} | {{TEST_1_NOTE}} |
| 每个脚本级测试都记录了测试入口、输入和结果 | {{TEST_2_STATUS}} | {{TEST_2_NOTE}} |
| 所有脚本级测试任务都有明确状态 | {{TEST_3_STATUS}} | {{TEST_3_NOTE}} |
| 每个主脚本 / 入口脚本都有对应 `test-overall:<main-script>` 任务 | {{TEST_4_STATUS}} | {{TEST_4_NOTE}} |
| 已生成 `docs/test_design.md` | {{TEST_5_STATUS}} | {{TEST_5_NOTE}} |
| 已生成 `docs/test_report.md` | {{TEST_6_STATUS}} | {{TEST_6_NOTE}} |
| 主入口脚本已完成端到端运行验证 | {{TEST_7_STATUS}} | {{TEST_7_NOTE}} |

---

## 六、报告与完成检查

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 所有目标文件都有明确转换状态 | {{FINAL_1_STATUS}} | {{FINAL_1_NOTE}} |
| 所有脚本级测试任务都有明确结论 | {{FINAL_2_STATUS}} | {{FINAL_2_NOTE}} |
| 所有整体测试任务都有明确结论 | {{FINAL_3_STATUS}} | {{FINAL_3_NOTE}} |
| 关键指标在容差范围内 | {{FINAL_4_STATUS}} | {{FINAL_4_NOTE}} |
| 所有非 1:1 偏离都已写入 `docs/issues.md` | {{FINAL_5_STATUS}} | {{FINAL_5_NOTE}} |
| `docs/` 下包含全部必需文档 | {{FINAL_6_STATUS}} | {{FINAL_6_NOTE}} |
| 已生成 `docs/compliance_report.md`，且结论与测试报告、迁移报告一致 | {{FINAL_7_STATUS}} | {{FINAL_7_NOTE}} |

---

## 七、问题摘要

| 级别 | 数量 | 说明 |
|------|------|------|
| Critical | {{CRITICAL_COUNT}} | {{CRITICAL_NOTE}} |
| Important | {{IMPORTANT_COUNT}} | {{IMPORTANT_NOTE}} |
| Minor | {{MINOR_COUNT}} | {{MINOR_NOTE}} |

---

## 八、结论

**总体状态**: {{CONCLUSION_STATUS}}

{{CONCLUSION}}

---

*本报告由 syslab-matlab-to-julia skill 生成*
