# MATLAB -> Julia 验收清单

## 前置与解析

- [ ] 已首先阅读 `../references/high_frequency_conversion_differences.md`
- [ ] 已识别入口脚本
- [ ] 已盘点 `.m` 文件、NBNC 行数和目录结构
- [ ] 已识别工具箱依赖
- [ ] 已生成依赖关系图
- [ ] 已生成函数映射待办表
- [ ] 已读取所有被调用函数的完整实现

## 计划

- [ ] 已创建 `docs/plan.md`
- [ ] `docs/plan.md` 中已写入源 `.m` 到目标 `.jl` 的一对一映射表
- [ ] `docs/plan.md` 中已写入逐脚本转换任务列表
- [ ] `docs/plan.md` 中已写入逐脚本测试任务列表
- [ ] `docs/plan.md` 中已写入整体测试任务列表
- [ ] `docs/plan.md` 中已写入报告任务列表
- [ ] 逐脚本转换任务满足“一脚本一任务”
- [ ] 每个 `.m` 文件只生成 1 个目标 `.jl` 文件
- [ ] 每个主脚本 / 入口脚本都有对应整体测试任务

## 转换

- [ ] 每个待转换脚本在开转前都已对照 `../references/high_frequency_conversion_differences.md`
- [ ] 每个 MATLAB 函数都先做函数映射
- [ ] 每个 `.m` 文件都有唯一目标 `.jl` 文件，且默认保持同名映射
- [ ] 保留原始注释
- [ ] 每个转换后的 Julia 文件都完成基本语法检查
- [ ] 无法直接迁移的内容已记录到 `docs/issues.md`
- [ ] 未发生未获批准的合并 / 拆分 / 重命名 / 算法重写
- [ ] 原始 MATLAB 代码未被修改
- [ ] 所有 `convert:<script>` 任务都有明确状态

## 测试

- [ ] 每个已转换脚本都有对应 `test-script:<script>` 任务
- [ ] 每个脚本级测试都记录了测试入口、输入和结果
- [ ] 所有脚本级测试任务都有明确状态
- [ ] 每个主脚本 / 入口脚本都有对应 `test-overall:<main-script>` 任务
- [ ] 已生成 `docs/test_design.md`
- [ ] 已生成 `docs/test_report.md`
- [ ] 主入口脚本已完成端到端运行验证

## 报告与完成

- [ ] 所有目标文件都有明确转换状态
- [ ] 所有脚本级测试任务都有明确结论
- [ ] 所有整体测试任务都有明确结论
- [ ] 关键指标在容差范围内
- [ ] 所有非 1:1 偏离都已写入 `docs/issues.md`
- [ ] `docs/` 下包含 `plan.md`、`translation_report.md`、`test_design.md`、`test_report.md`、`issues.md`、`compliance_report.md`
- [ ] 已生成 `docs/compliance_report.md`
- [ ] 最终结论与测试报告、迁移报告一致
