# 官方 CodeGenerator 文档核对点

本文件只记录核对路线，不替代官方文档内容。需要确认 SyslabCC 当前行为时，应通过当前 Syslab 环境定位 CodeGenerator 文档，不在 skill 中写安装绝对路径。

## 常用核对路线

- `<SYSLAB_HOME>/Tools/AIAssets/projects/CodeGenerator/Doc/CodeGenerator.md`：总体能力、三类常见产物、文档入口。
- `<SYSLAB_HOME>/Tools/AIAssets/projects/CodeGenerator/Doc/CodeGenerator/SyslabCC/get-started.md`：`scc` 基本命令、`app` / `shared` 示例、`--bundle`、`--experimental-gen-header`、`-c` / `-d` 源码工程示例。
- `<SYSLAB_HOME>/Tools/AIAssets/projects/CodeGenerator/Doc/CodeGenerator/SyslabCC/CodeGenerationWorkflow.md`：推荐工作流、`main()`、`static_compile(...)`、部署与验证口径。
- `<SYSLAB_HOME>/Tools/AIAssets/projects/CodeGenerator/Doc/CodeGenerator/SyslabCC/Troubleshooting/compiler-flags.md`：编译选项详情，尤其是 `-d`、`-c` / `--no-compile`、`--mode`、`--cmake`、`--os`、`--arch`、`--no-blas`。
- `<SYSLAB_HOME>/Tools/AIAssets/projects/CodeGenerator/Doc/CodeGenerator/SyslabCC/Advanced-Settings/SccCompilerEnvironmentFix.md`：`scc` 环境修复；重点核对 Julia 全局环境依赖 `TyJuliaCAPI`、`TyRandom`、`MethodAnalysis`。
- `<SYSLAB_HOME>/Tools/AIAssets/projects/CodeGenerator/Doc/CodeGenerator/SyslabCC/Supported-Domains/supported-target.md`：官方支持目标包括可执行文件、动态链接库、C++ 源代码和静态链接库；C 源代码不支持。
- `<SYSLAB_HOME>/Tools/AIAssets/projects/CodeGenerator/Doc/CodeGenerator/SyslabCC/Supported-Domains/codegen-limits.md` 与 `SyslabCC/Troubleshooting/collect-instance.md`：动态调用、类型不稳定、用例驱动代码生成和限制策略。
- `<SYSLAB_HOME>/Tools/AIAssets/projects/CodeGenerator/Doc/CodeGenerator/SyslabCC/Advanced-Settings/gen-cmake-project.md`、`gen-vs-project.md`、`cross-platform.md`：只有用户明确要求 CMake、Visual Studio、静态库或交叉编译时再读取。

## 本 skill 的默认边界

- 默认交付模式仍是 `app`、`shared`、`source` 三类；`source` 是本 skill 对源码工程交付的命名，命令层使用 `-c` / `--no-compile` 加 `--mode app|shared`。
- `--mode static`、`--cmake`、Visual Studio 工程和交叉编译不进入默认流程；命中明确需求时，按官方高级文档另行规划。
- 官方允许合规函数直接 `static_compile(...)` 导出；本 skill 的包装函数 ABI 规则只用于新增包装层或原始签名不适合直接对外暴露的场景。
