---
name: syslab-performance-optimization
description: "Syslab Julia 性能优化：按照固定的四阶段流程处理 Syslab Julia 性能问题，包括制定计划、逐脚本优化、整体性能优化和生成结案报告。默认任务必须创建并持续更新 docs/performance-plan.md；在计划文档、逐脚本优化结果、整体性能优化结论或 docs/performance-report.md 未完成前，不得宣告任务完成。"
---

# Syslab Performance Optimization

先使用 `syslab-environment`。相对路径：`../syslab-environment/SKILL.md`。

优化时优先依赖 Syslab 运行时、Syslab 帮助文档和 `Ty*` 库；不要基于通用 Julia 安装直接下性能结论。

## 核心约束

- 先保证正确性，再要性能。
- 未经用户明确允许，不要用降低精度换速度。
- 未写入计划的“顺手优化”不执行。

## 任务分流

### 小任务

相关本地 `.jl` 文件总代码不超过 `100` 行时，按小任务处理。

最低交付：

- 优化后的代码
- benchmark 对比数据
- 正确性验证结论
- 必要的 A-H 检查结论

### 默认任务

不满足小任务条件时，按默认任务处理。

要求：

- 创建并持续更新 `docs/performance-plan.md`
- 按四阶段工作流推进
- 生成 `docs/performance-report.md`

`docs/performance-plan.md` 是默认任务的主控文档；未先写入计划的改动，不执行。

## 四阶段工作流

1. 建立计划
2. 逐脚本性能优化
3. 整体性能优化
4. 生成结案报告

不要跳阶段。详细准入条件和执行规则见 `workflows/performance-plan-execution-rules.md`。

## 默认任务的执行骨架

### 阶段 1. 建立计划

产出：

- `docs/performance-plan.md`
- 目标定义
- 依赖分析
- 初始基线与热点证据
- 逐脚本主表
- 逐脚本执行顺序

### 阶段 2. 逐脚本性能优化

对每个本地脚本（包括入口脚本）都要给出结果：

- `done`
- `blocked`
- `N/A`
- `dropped`

本阶段不允许因为局部热点已经提速，就跳过剩余脚本。

### 阶段 3. 整体性能优化

必须回答：

- 局部优化后，瓶颈有没有转移
- 是否存在跨脚本的共享缓存、重复初始化、重复 I/O、重复 plan 创建、公共缓冲区复用机会
- 外部调用方式、输入输出路径和关键副作用顺序是否保持不变

### 阶段 4. 生成结案报告

必须输出：

- `docs/performance-report.md`

没有正式报告，不宣布完成。

## 默认任务最低交付

- `docs/performance-plan.md`
- `docs/performance-report.md`
- 依赖分析结论
- 初始基线、热点证据、最终复测结果
- 每个本地脚本的 A-H 覆盖结论
- 每个脚本的函数化结论，或 `N/A`
- 每个脚本的优化与验证结论，或 `N/A`
- 整体性能优化结论

## 参考入口

- 工作流合同：`workflows/performance-plan-contract.md`
- 阶段执行规则：`workflows/performance-plan-execution-rules.md`
- 计划模板：`templates/performance-plan-template.md`
- 报告模板：`templates/performance-report-template.md`
- A-H 检查：`rules/performance-checklist.md`
- 性能分析规则：`rules/performance-analysis-rules.md`
- 示例任务：`examples/performance-optimization-task.md`
