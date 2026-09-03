# 示例任务

## 用户请求

将 `project-a` 中的 MATLAB `.m` 工程迁移到 Syslab Julia，保留目录结构，给出脚本级转换和测试任务清单，并输出测试结论与剩余问题清单。

## 期望执行路径

1. 先读 `high_frequency_conversion_differences.md`
2. 完成工程解析，盘点 `.m` 文件、入口脚本、目录结构、工具箱依赖
3. 生成依赖图和函数映射待办表
4. 创建 `docs/plan.md`，写入：
   - 源 `.m` 到目标 `.jl` 的映射表
   - `convert:<script>` 逐脚本转换任务
   - `test-script:<script>` 逐脚本测试任务
   - `test-overall:<main-script>` 整体测试任务
   - `report:*` 任务
5. 按依赖顺序完成逐脚本转换，并记录函数映射与未解决问题
6. 完成逐脚本测试，并回填每个脚本的验证结论
7. 执行主入口整体测试，生成 `docs/test_design.md` 和 `docs/test_report.md`
8. 生成 `docs/translation_report.md` 和 `docs/compliance_report.md`

## 最低交付

- 独立输出目录：`<project-name>-translated/`，至少包含 `docs/`、`julia/`、`tests/`
- 六份文档：`plan.md`、`translation_report.md`、`test_design.md`、`test_report.md`、`issues.md`、`compliance_report.md`
- 主入口脚本端到端运行结论
- 每个脚本的转换状态和测试状态
- 函数映射与未解决问题记录
