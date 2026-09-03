# 兼容性报告

## 目标

- 目标产物：
- 目标平台：

## 环境

- `scc` 可用性：
- `scc` 版本：
- Syslab 运行时：
- `julia-ty.bat` / `julia-ty.sh` 启动器：
- Syslab Julia depot / active project：
- `scc` 依赖包 `TyJuliaCAPI` / `TyRandom` / `MethodAnalysis`：

## 代码检查结果

- 入口模式判断：
- `main()` / `static_compile(...)` 状态：
- 是否使用同目录 `build.jl` 作为编译入口：
- 若 `build.jl` 承担入口或导出，用户明确指定的函数：
- 非 `const` 全局变量：
- 未定义变量：
- 类型稳定性风险：
- 导出签名合法性：

## 结论

- 是否适合直接代码生成：
- 是否需要先改 Julia 源码：
- 是否需要 `--collect-instance`：
- 若未授权直接改源码，`build.jl` 方案是否足够：
- 若 `build.jl` 方案不足，是否已生成 `docs/{entry-name}/source_change_suggestions.md`：

## 备注

- 其他限制或兼容性说明：
