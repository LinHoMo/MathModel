# Syslab Skills 总宪法

本文件是 Syslab skills 的顶层总入口与最高规则。所有 Syslab 相关任务都应先遵循本文件，再按需进入具体子 skill。

## 核心规则

- 在规划、编写或执行 Julia 代码之前，先检查当前 Syslab 与 Julia 环境。
- 使用 Julia 代码绘图时，默认使用 TyPlot 库。
- 只要 Ty 库能够满足需求，就优先使用 Ty 库。
- 如果 Ty 库不足以满足需求，则优先使用当前环境中已经安装的 Julia 库。
- 只有在 Ty 库与当前环境已有 Julia 库都无法满足需求时，才允许建议或引入新的社区 Julia 包。
- 当 API 细节、函数行为、参数格式或工作流不明确时，先查询本地 Syslab / Ty 帮助文档，不要直接猜测。
- 一旦确定了 Syslab 安装目录、Julia 运行时、Ty 包集合和帮助文档路径，后续步骤必须复用同一套环境结论，不要反复切换假设。
- 除非用户明确要求切换工作目录，否则不要改变持久的 Syslab / Julia 工作目录：不要生成 `cd(...)`、`Base.cd(...)`、`chdir(...)` 等持久切目录代码；调用 `restart_julia` 时默认不要传 `working_directory`；运行文件时不要把文件所在目录当作需要切换到的工作目录。需要定位文件时优先使用绝对路径、`joinpath`、`@__DIR__`。

## 默认流程

1. 先解析当前 Syslab 环境、安装目录、Julia 运行时、Ty 包以及本地帮助文档路径。
2. 如果任务是将 MATLAB / Syslab M 代码迁移为 Julia 代码，并且安装了 Syslab MCP，优先调用 `map_matlab_functions_to_julia` 获取候选映射，不要直接凭经验手写替换。
3. 再选择最相关的下游 Syslab skill。
4. 只读取当前任务真正需要的最小范围参考材料。
5. 优先给出与当前环境一致、可直接运行、且不引入不必要新依赖的 Julia 方案。
6. 按任务类型完成对应的验证、测试或结果校验。

## 子 Skill 路由

- `syslab-environment`：用于解析 Syslab 安装目录、运行时选择、Ty 包、本地文档路径以及共享环境假设。
- `syslab-mds-docs`：用于通过可选的 `mdsSearch` 检索 Syslab 官方知识库，回答概念、教程、工作流、排障和最佳实践问题；具体函数签名仍优先使用函数文档工具。
- `syslab-code-style`：用于整理 Syslab Julia 代码结构、命名、API 设计与风格。
- `syslab-testing`：用于设计与执行测试、回归检查和验证流程。
- `syslab-performance-optimization`：用于测量性能、定位瓶颈并优化 Syslab Julia 代码。
- `syslab-matlab-to-julia`：用于将 Syslab M 或 MATLAB 风格代码迁移为遵循 Ty 优先策略的 Syslab Julia 实现。进入该类任务时，先调用 `map_matlab_functions_to_julia`，再按需查阅文档和生成代码。
- `syslab-julia-to-cpp`：用于将 Syslab Julia 代码生成可执行文件、动态库或 C++ 工程，并处理 `scc`、`SyslabCC.static_compile`、类型稳定性检查、用例驱动代码生成和产物验证。
- `syslab-digital-filter-design`：用于基于 `TySignalProcessing` 与 `TyDSPSystem` 的数字滤波器设计与验证。
- `syslab-app-designer`：用于生成、审查和调试 Syslab App Designer 工程，尤其是普通 UI 组件、ribbon/toolstrip 结构、回调通道、运行时消息链路和生成代码。

## 使用要求

- 不要在任务开始时一次性完整加载所有子 skill。
- 先使用本文件作为总规则入口，再按需打开最相关的子 skill。
- 当多个 Syslab skill 同时适用时，以本文件的规则为最高优先级。
- 当用户要求将 MATLAB / Syslab M 代码转换为 Julia 代码时，若已安装 Syslab MCP，优先调用 `map_matlab_functions_to_julia`。
- 当对 Julia 代码进行性能优化时，优先调用 `syslab-performance-optimization`。
