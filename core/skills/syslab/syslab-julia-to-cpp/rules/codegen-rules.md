# 代码生成规则

## 入口规则

- `app` 模式必须有稳定的 `main()`；若用户源文件缺少 `main()`，优先在同目录新建 `build.jl`，由 `build.jl` `include` 用户源文件并补充 `main()`。
- `shared` 模式必须显式列出全部 `SyslabCC.static_compile(...)`；若用户源文件缺少导出，优先在同目录新建 `build.jl`，由 `build.jl` `include` 用户源文件并补充导出。
- 已有 `static_compile(...)` 的直接导出签名若落在官方支持范围内，可以沿用；本 skill 的出参和 `Int32` 状态码约定只强制用于新增包装函数。
- 若 `app` 模式通过 `build.jl` 补充 `main()`，必须先让用户明确指定 `main()` 最终调用的 Julia 函数或业务入口，不得自行假设。
- 若 `shared` 模式通过 `build.jl` 补充导出，必须先让用户明确指定导出函数，不得自行假设。
- 如果同时存在多个入口文件，先确定主入口，不要在编译阶段临时切换。

## 代码修改规则

- 未经用户明确授权，默认不直接修改用户 Julia 源文件。
- 若判断只是缺少编译入口、导出声明，优先新增同目录 `build.jl`、导出包装函数，而不是直接改用户源文件。
- 若 `shared` 模式通过 `build.jl` 新增导出包装函数，包装函数入参和 `SyslabCC.static_compile(...)` 参数元组必须按 `references/wrapper-arg-conversion.md` 从原始 Julia 入参推导，不得临时自造协议。
- 若用户函数有返回值，`shared` 包装函数必须优先按 `references/wrapper-arg-conversion.md` 把业务返回值改写为额外出参，并让包装函数自身返回 `Int32` 状态码；不得混用两套返回协议。
- 若 `build.jl` 方案仍不足以满足代码生成要求，再在 `docs/{entry-name}/source_change_suggestions.md` 中记录建议修改点、原因、影响范围和示例改法。
- 不因为代码生成任务主动重命名用户文件、函数或导出符号，除非用户明确要求。
- 优先通过补充包装函数、入口函数或类型标注解决问题，而不是大规模重写算法。
- 若为了动态库导出而新增包装函数，必须保持原始算法函数可读可测。
- 若原始入参是数组，包装函数必须显式拆成“数据指针 + `Ptr{Int64}` 维度参数”，并在包装层内用 `unsafe_wrap(...; own=false)` 还原；不要把数组 ABI 直接伪装成标量 ABI。
- 若原始返回值是标量，包装函数要新增 `Ptr{T}` 出参并用 `unsafe_store!` 写回。
- 若原始返回值是数组，包装函数要新增 `Ptr{element_type}` 出参并逐元素 `unsafe_store!` 写回。
- 若原始返回值是 `Tuple(...)`，包装函数要把每个返回项平铺成独立出参；`Nothing` 项不生成出参。

## 类型稳定规则

- 看到 `[]`、`Dict()`、`Vector{Any}`、抽象字段、非 `const` 全局变量时，默认将其视为风险点。
- 优先消除类型不稳定，而不是立刻加入 `--collect-instance`。
- 若保留动态调用，必须说明为何无法或不值得改成静态调用。

## 编译选项规则

- 默认先写出最小可解释的命令，不要堆叠无关选项。
- 对交付类任务，优先考虑 `--bundle`。
- 对 Windows 可执行文件交付，优先考虑 `--static-mingw`。
- `source` 模式必须使用 `-c` / `--no-compile` 和 `-d <dir>`，并明确底层 `--mode app|shared`；不要写 `--mode source`。
- `--mode static`、`--cmake`、Visual Studio 项目和交叉编译只在用户明确要求时启用。
- `--debugtrace` 仅用于运行时排障；问题解决后可在最终交付中移除。

## 验证规则

- 可执行文件至少验证一次目标产物运行结果，并记录一次从 Julia 外部直接启动产物的验证方式。
- 动态库至少验证一次外部调用结果，优先 C++ 或 Python。
- 若只生成 C++ 源码工程，也要验证 `artifacts/{entry-name}/source/`、`src/`、`make.jl` 或 `Makefile` 是否完整；只有显式使用 `--cmake` 时才要求 `CMakeLists.txt`。
- 若请求生成头文件，还要单独验证头文件是否实际存在；优先检查目标产物目录和当前工作目录中的同名 `.h`。
- 验证结论必须区分"编译成功"和"行为正确"，两者不能混为一谈。

## 测试脚本规则（app / shared 模式）

- `app` 模式必须在 `tests/{entry-name}/app/` 下生成 `runtests.jl`：
  - 启动生成的 `artifacts/{entry-name}/app/{entry-name}.exe`
  - 抓取 stdout 输出
  - 使用 `@test` 与 Julia 基线结果对比
  - 测试脚本引用产物时必须使用 `joinpath(@__DIR__, "..", "..", "..", "artifacts", ...)`
- `shared` 模式必须在 `tests/{entry-name}/shared/` 下生成验证脚本（优先 `runtests.jl`）：
  - 产物完整性检查：`@test isfile(dll)`、`@test isfile(lib)`、`@test isfile(h)`
  - 头文件导出签名校验：读取 `.h` 内容，用 `@test contains(...)` 校验每个导出函数签名
  - 外部调用验证（至少其一）：
    - C++ 测试程序：生成 `test_shared.cpp`，使用 zig 编译并链接 `.lib`，运行对比基线
    - `ccall` 调用：若可从 Julia `ccall` 直接加载符号，对比基线结果
    - 若因 `-fvisibility=hidden` 等原因 `ccall` 不可用，至少完成编译验证并在 `docs/{entry-name}/issues.md` 记录
- 测试脚本必须使用 `using Test`
- 测试脚本生成后必须实际运行一次，不得只生成不运行

## 文档规则

- 计划文档必须记录最终使用的 `scc` 命令。
- 出现报错时，记录报错类别、触发命令、定位文件和处理结论。
- 若使用 `dispatch_limit`、`block_method_instance` 或 `--no-gc`，必须记录原因。
- 若未获授权而不能直接修改用户源码，必须先判断能否通过同目录 `build.jl` 解决；只有确认 `build.jl` 方案不足时，才创建 `docs/{entry-name}/source_change_suggestions.md`。
- 若 `build.jl` 承担 `app` / `shared` 的入口或导出，必须在文档中标明哪些函数、符号或签名来自用户明确指定。
