---
name: syslab-testing
description: Syslab Julia 测试：使用 Syslab 运行时和 Julia 的 Test标准库，为 Syslab Julia 代码设计、补充、运行和调试单元测试。适用于创建测试计划、组织runtests.jl、补充 @test或@test_throws 覆盖、比较预期行为，以及诊断失败的 Syslab 测试。
---

# Syslab 测试

先使用 `syslab-environment`。相对路径：`../syslab-environment/SKILL.md`。
只要代码依赖 Syslab 包或帮助资源，就使用 Syslab Julia 运行时来执行测试。
不要用通用的 `julia` 可执行文件来运行 Syslab Julia 测试。

本技能以 `references/Test.md` 为基础。
除非项目已经要求使用额外的测试工具，否则使用 Julia 的 `Test` 标准库。

## 组织测试结构

- 当项目采用包布局时，在 `test/runtests.jl` 中保留一个根级 `@testset`。
- 按功能、模块或行为来组织子 `@testset`。
- 使用 `include(...)` 将大型测试套件拆分为更聚焦的文件。
- 测试名称优先描述行为，而不是实现细节。

## 编写有用的断言

- 用 `@test` 做直接的行为检查。
- 用 `@test_throws` 检查预期失败。
- 在浮点比较中使用 `isapprox` 或 `≈`，并显式给出容差。
- 当日志行为很重要时，使用 `@test_logs`。
- 如果 `@test value == 0` 已经表达了相同意图，就避免写出 `@test value == 0.0` 这类噪声断言。

## 以可测试性为目标设计代码

- 将性能关键或逻辑较重的代码放入函数，而不是顶层脚本。
- 通过参数传递依赖项和输入。
- 在可能的情况下，将纯计算与 I/O、绘图或环境初始化隔离开。
- 修复缺陷时补充有针对性的回归测试。

## 可靠地运行测试

- 在根据耗时或编译开销较大的失败做结论之前，先让相关代码路径预热一次。
- 先运行最小的相关测试范围，再逐步扩大到包级或项目级测试套件。
- 始终使用由 `syslab-environment` 解析出的 Syslab Julia CLI 来调用 Julia 测试。
- 如果失败看起来与环境有关，报告你使用的确切 Syslab 运行时。

## 诊断失败

测试失败时，记录以下信息：

- 失败的表达式
- 实际值与期望值
- 问题属于逻辑缺陷、异常不匹配、环境问题，还是不稳定的数值容差

如果失败来自缺失的 Syslab 资源，应先通过 `syslab-environment` 解决，再修改测试代码。

## 输出期望

当你新增或修复测试时，输出中应包含：

- 覆盖了哪些行为
- 使用了什么命令或运行时
- 是运行了完整测试套件，还是只运行了一个聚焦的子集
- 仍然存在、还需要补充覆盖的缺口

## 资料来源

在需要了解宏行为或 `testset` 模式时，再阅读完整参考：

- `references/Test.md`
