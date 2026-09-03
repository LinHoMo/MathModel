# 代码生成执行规则

## 阶段 1：环境验证

- 必须通过 `syslab-environment` 确认当前 Syslab 安装目录、Syslab Julia 启动器 `julia-ty.bat` / `julia-ty.sh`、Julia depot 及 active project。
- `scc` 的运行依赖由 `julia-ty.bat` / `julia-ty.sh` 启动并解析出的 Syslab Julia 全局环境；后续 Julia 侧依赖检查和基线运行必须基于该环境执行，禁止将依赖临时安装到项目环境。
- 定位 `scc` 时优先使用当前 Syslab 安装目录下的 `Tools/SyslabCC/scc.exe`；不要默认使用 PATH 中的同名命令。
- 确认 `scc -h` 或 `scc --help` 可用。
- 确认 `scc --version` 可用，并在计划或报告中记录实际版本。
- 在 `julia-ty.bat` / `julia-ty.sh` 启动后的 Syslab Julia 全局环境中确认 `TyJuliaCAPI`、`TyRandom`、`MethodAnalysis` 已安装。
- 记录当前 Syslab 运行时与目标平台。

## 阶段 2：识别目标产物与入口

- 确认任务是 `app`、`shared` 还是 `source`。
- 扫描 `.jl` 文件中的 `main()`、`include(...)` 和 `SyslabCC.static_compile(...)`。
- 必要时使用 `scripts/scan-julia-codegen-entrypoints.jl` 输出盘点表。
- 若用户源文件缺少 `main()` 或 `SyslabCC.static_compile(...)`，立即规划同目录 `build.jl`，并在计划中记录 `build.jl` 与用户源文件的 `include` 关系。
- 若已有 `static_compile(...)`，先判断其参数和返回值是否落在官方支持范围内；合规时可以直接沿用，不必改写为包装函数。
- 对 `app` 模式，若 `main()` 需要落在 `build.jl`，先向用户确认 `main()` 最终调用的 Julia 函数或业务入口。
- 对 `shared` 模式，若导出需要落在 `build.jl`，先向用户确认导出函数。

## 阶段 3：兼容性与类型稳定性检查

- 检查非 `const` 全局变量。
- 检查 `Any` 容器、抽象字段和明显动态调用。
- 对动态库，检查每个导出项的参数与返回值类型。
- 如果发现只是缺少 `main()`、`SyslabCC.static_compile(...)`，则优先通过同目录 `build.jl` 继续代码生成；只有确认必须调整用户 Julia 源码且未获授权时，才在 `docs/{entry-name}/source_change_suggestions.md` 中记录建议并继续以“阻塞项”方式推进文档。

## 阶段 4：建立代码生成计划

- 在 `docs/{entry-name}/codegen_plan.md` 中写明入口、命令、风险和验证方案，并标明哪些入口/导出项来自用户明确指定。
- 在计划中写明目标产物目录，默认使用 `artifacts/{entry-name}/source`、`artifacts/{entry-name}/shared`、`artifacts/{entry-name}/app`。
- 若预计用到 `--collect-instance`，同步记录用例来源和限制策略。

## 阶段 5：执行代码生成

- 先执行最小编译命令。
- 若失败，按“源码问题 > 入口问题 > 选项问题 > 环境问题”的顺序排查。
- 如需增强诊断，优先补 `--verbose` 或 `--debugtrace`。
- `source` 模式默认将源码工程输出到 `artifacts/{entry-name}/source/`，不要只生成到临时目录却不回填最终产物目录。

## 阶段 6：验证产物

- `app`：运行目标可执行文件，并至少记录一次从 Julia 外部直接启动产物的验证。
- `shared`：做一次外部调用验证，优先 C++ 或 Python；受环境限制时可用 Julia `ccall` 兜底，并记录限制。
- `source`：确认 `artifacts/{entry-name}/source/` 下工程目录、`src/`、`make.jl` 或 `Makefile` 齐全；只有显式使用 `--cmake` 时才要求 `CMakeLists.txt`，必要时做一次构建验证。
- 若 `shared` 模式使用 `--experimental-gen-header`，必须额外检查 `.h` 是否实际生成；优先同时检查目标产物目录和当前工作目录，不要只检查 DLL 所在目录。
- 若 `.h` 缺失，记录到 `docs/{entry-name}/issues.md`，不能仅因 DLL 编译成功就视作头文件交付成功。

## 阶段 7：生成测试脚本（仅 app / shared 模式）

- `app` 模式：在 `tests/{entry-name}/app/` 下创建 `runtests.jl`：
  - 使用 `using Test`
  - 启动 `artifacts/{entry-name}/app/{entry-name}.exe`，抓取 stdout
  - 用 `@test` 对比 Julia 基线结果
  - 路径使用 `joinpath(@__DIR__, "..", "..", "..", "artifacts", ...)`
  - 生成后立即运行，确认测试通过
- `shared` 模式：在 `tests/{entry-name}/shared/` 下创建验证脚本（优先 `runtests.jl`）：
  - 产物完整性：`@test isfile(dll)`、`@test isfile(lib)`、`@test isfile(h)`
  - 头文件签名校验：读取 `.h`，`@test contains(...)` 校验导出签名
  - 外部调用验证（至少其一，按优先级降序）：
    1. C++ 测试程序编译+运行：生成 `test_shared.cpp`，用 zig 编译链接 `.lib`，运行对比基线
    2. Python `ctypes` / `cffi` 调用：对比基线结果
    3. Julia `ccall` 直接调用：对比基线结果
    4. 若受符号可见性或工具链限制无法完成外部调用，至少完成编译验证并记录到 `docs/{entry-name}/issues.md`
  - 测试必须使用 `using Test`，路径用 `joinpath(@__DIR__, ...)`
  - 生成后立即运行，确认测试通过

## 阶段 8：输出结果

- 更新验证报告。
- 更新问题清单。
- 记录最终命令、最终产物与残余风险。
