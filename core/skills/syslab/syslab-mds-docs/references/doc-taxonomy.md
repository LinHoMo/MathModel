# Syslab 帮助主题分类

先按用户意图选择一个主要文档域，再将域名、具体目标和预期做法自然地写进假设性答案。分类来自 Syslab 帮助源仓库的项目结构，仅用于路由，不代表 `mdsSearch` 支持栏目过滤。

## 产品与基础使用

| 用户信号 | 文档域 | 查询中应体现 |
|---|---|---|
| Syslab 是什么、快速入门、界面与基本流程 | Syslab / Quickstart | 产品目标、典型操作顺序、预期结果 |
| 环境、包管理、工程与数据分析 | SyslabEnv / PackageDevelop | 环境或工程上下文、配置目标 |
| App Designer、App 构建 | Syslab / AppDesigner / AppBuild | App 类型、设计或构建阶段 |
| 安装、卸载、升级、许可 | SetupHelp | 操作系统、安装阶段、许可现象 |
| 常见报错、数学问题、故障定位 | FAQ | 可观察现象、可能原因、排查顺序 |

## 语言、迁移与互操作

| 用户信号 | 文档域 | 查询中应体现 |
|---|---|---|
| Julia 入门、语言差异、最佳实践 | JuliaLanguage | Julia 语境、行为差异、推荐写法 |
| Julia 性能与性能分析 | JuliaHigh-PerformanceProgramming | 性能症状、分析方法、优化原则 |
| MATLAB/M 迁移到 Julia | FromMatlabToSyslab | 原语言写法、目标 Julia 行为、迁移注意点 |
| M 与 Julia 互调、Python 调包 | MultiLanguage | 调用方向、数据传递、运行边界 |
| 外部接口与开放体系 | OpenSystemArchitecture | 扩展点、接口层、开发目标 |

## AI、构建与执行工作流

| 用户信号 | 文档域 | 查询中应体现 |
|---|---|---|
| Syslab AI、提示词、Skills | SyslabAI / SyslabPrompts | Agent 任务、提示策略、预期产物 |
| Syslab MCP Server、工具接入 | SyslabAI / SyslabMCPServer | MCP 场景、工具职责、连接目标 |
| Julia 生成 C++、SyslabCC | CodeGenerator / SyslabCC | 入口形式、目标产物、约束 |
| 应用打包、部署、C 库 | ApplicationDeployment | 部署目标、产物类型、运行环境 |
| 多进程、多线程、集群 | ParallelComputing | 并行模型、任务粒度、执行环境 |

## Ty 工具箱

帮助源包含 `TyBase`、`TyPlot`、`TyMath`、`TySignalProcessing`、`TyDSPSystem`、`TyControlSystems`、`TyOptimization`、`TyStatistics`、`TyImageProcessing`、`TyMachineLearning`、`TyDeepLearning` 等工具箱。

- 工具箱概念、完整工作流、算法选择、排障和最佳实践：使用 MDS。
- 已明确函数名，询问语法、参数、返回值或精确示例：优先 `mdocsSearch` 或本地函数文档工具。
- 只说“这个函数怎么用”但没有函数名：先从上下文提取；仍无法确定时询问函数名，不要用宽泛 MDS 结果冒充函数签名。

## 路由原则

- “怎么用 Syslab”这类宽泛问题从 Syslab 快速入门开始。
- 同时涉及产品流程和具体 API 时，先用 MDS 确定工作流，再用函数文档工具核对 API。
- 版本差异或发布变化需要命中明确版本信息；没有版本依据时不要断言“最新版就是如此”。
- 编码、迁移、性能优化或测试任务在取得文档依据后，转交相应 `syslab-*` 技能完成执行和验证。
