# 代码生成计划

## 1. 任务概述

- 目标产物：
- 目标平台：
- 交付物：

## 2. 源码与入口盘点

- Julia 源文件：
- 主入口文件：
- `main()` 入口：
- `static_compile(...)` 导出项：
- 若 `main()` 位于 `build.jl`，用户明确指定的业务入口函数：
- 若 `static_compile(...)` 位于 `build.jl`，用户明确指定的导出函数：

## 3. 兼容性检查

- `julia-ty.bat` / `julia-ty.sh` 启动器：
- Syslab Julia depot / active project：
- `scc -h` / `scc --help` 环境验证：
- `scc --version`：
- `scc` 依赖包 `TyJuliaCAPI` / `TyRandom` / `MethodAnalysis`：
- 非 `const` 全局变量：
- 未定义变量 / 未定义函数：
- 类型稳定性风险：
- 是否需要 `--collect-instance`：

## 4. 编译方案

- 编译命令草案：
- 产物输出目录：
- 关键编译选项：
- 选项原因：

## 5. 验证方案

- Julia 侧验证：
- 产物侧验证：
- `app` / `shared` 外部调用验证：
- 头文件存在性验证（若请求）：

## 6. 风险与待确认项

- 风险：
- 待确认项：
- 源码修改建议文档（若未授权直接改用户脚本）：
