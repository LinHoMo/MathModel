# 入口与产物模式

SyslabCC 常见目标分为三类：

## 1. 可执行文件模式 `app`

- 目标：生成 `.exe` 或 Linux 可执行文件。
- 入口要求：最终编译入口必须有 `main()`；如果用户源文件没有 `main()`，应优先在同目录新建 `build.jl`，由 `build.jl` `include` 用户源文件并补充 `main()`。
- 若通过 `build.jl` 补充 `main()`，必须先让用户明确指定 `main()` 最终调用的 Julia 函数或业务入口，不得自行假设。
- 常见命令形态：

```powershell
scc .\build.jl -o .\artifacts\{entry-name}\app\{entry-name}.exe --bundle --static-mingw
```

- 常见守卫写法：

```julia
function main()
    # ...
end

@static @isdefined(SyslabCC) || main()
```

适用场景：

- 命令行程序
- 批处理程序
- 部署到无 Julia / 无 Syslab 的机器

## 2. 动态库模式 `shared`

- 目标：生成 `.dll` / `.so`。
- 入口要求：最终编译入口必须使用 `SyslabCC.static_compile("导出名", 函数, (...))` 显式声明导出。若用户源文件已有合法导出签名，可以沿用直接导出；若需要新增包装函数，`(...)` 必须填写包装函数的完整 ABI 类型元组，既包括输入参数，也包括返回值对应的额外出参。
- 若用户源文件没有导出定义，应优先在同目录新建 `build.jl`，由 `build.jl` `include` 用户源文件并补充导出。
- 若通过 `build.jl` 补充导出，必须先让用户明确指定导出函数，不得自行假设。
- 常见命令形态：

```powershell
scc .\build.jl -o .\artifacts\{entry-name}\shared\{entry-name}.dll --bundle --experimental-gen-header
```

官方文档中的直接导出写法：

```julia
add_num(x, y) = x + y

@static if @isdefined(SyslabCC)
    SyslabCC.static_compile("add_num_i64", add_num, (Int64, Int64))
end
```

新增包装函数时的典型写法：

```julia
add_num(x, y) = x + y

function cwrap_add_num(x::Int64, y::Int64, outpara_1::Ptr{Int64})::Int32
    ret_1 = add_num(x, y)
    unsafe_store!(outpara_1, ret_1)
    return Int32(0)
end

@static if @isdefined(SyslabCC)
    SyslabCC.static_compile("add_num_i64", cwrap_add_num, (Int64, Int64, Ptr{Int64}))
end
```

适用场景：

- C/C++ 调用 Julia 算法
- Python `ctypes` / `cffi` 调用
- 作为其他宿主程序的计算内核

## 3. 源码工程模式 `source`

- 目标：只生成 C++ 源码工程，但暂不立即编译最终二进制。
- 说明：`source` 是本 skill 的交付模式名；`scc` 命令中使用 `-c` / `--no-compile` 生成源码工程，并继续用 `--mode app` 或 `--mode shared` 说明底层二进制语义。
- `-d <dir>` 指定 C++ 工程输出目录；`-o <path>` 仍表示未来构建产物的输出名或路径。
- 常见命令形态：

```powershell
scc .\build.jl -d .\artifacts\{entry-name}\source -o .\artifacts\{entry-name}\source\libdemo -c --mode shared
```

- 常见后续动作：
  - 进入 `artifacts/{entry-name}/source/` 工程目录
  - 使用 `julia make.jl all` 或 `make all -j <n>` 构建；只有显式使用 `--cmake` 时才按 CMake 工程处理

适用场景：

- 需要人工接入现有 C++ 构建系统
- 需要审查生成的工程结构
- 需要后续再集成 CMake / Visual Studio

## 模式判断规则

- 如果用户要“直接运行程序”，优先考虑 `app`。
- 如果用户要“让 C++ / Python 调函数”，优先考虑 `shared`。
- 如果用户要“先拿到 C++ 源码工程再自行构建”，优先考虑 `source`。
- 若需求同时包含二进制与工程导出，先明确主目标，再决定是否在验证阶段补做另一个产物。
