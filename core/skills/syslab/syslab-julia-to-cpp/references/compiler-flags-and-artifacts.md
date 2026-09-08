# 常用编译选项与产物

## 常用选项

- `--bundle`
  - 打包运行所需动态库依赖，便于部署。
- `--static-mingw`
  - Windows 下静态链接 MinGW 运行时，减少目标机器缺 DLL 的风险。
- `--experimental-gen-header`
  - 动态库模式下生成 `.h` 头文件。
- `-d <dir>`
  - 指定生成的 C++ 工程输出目录。
- `-c` / `--no-compile`
  - 只生成 C++ 代码或源码工程，不执行最终 C++ 编译；`source` 是本 skill 的交付模式名，`-c` 是 `scc` 命令开关。
- `--mode app|shared`
  - 显式指定输出模式。
- `--mode static`
  - 官方支持的静态库目标，通常与 `--cmake` 同用；只有用户明确要求静态库时才进入高级路由。
- `--cmake`
  - 使用 CMake 构建系统生成工程。
- `--os win|linux` / `--arch x64|arm64`
  - 指定目标操作系统或架构；跨平台任务必须记录目标平台和限制。
- `--no-blas`
  - 不在初始化时加载 BLAS，常用于交叉编译或跨平台 CMake 工程。
- `--collect-instance`
  - 启用用例驱动代码生成，处理部分动态调用场景。
- `--dispatch-limit <n>`
  - 限制动态分派方法实例的收集数量。
- `--debugtrace`
  - 运行时报错时输出 Julia 调用栈。
- `--verbose`
  - 输出更详细的编译过程日志。
- `--no-gc`
  - 禁用垃圾回收，使用自定义内存管理，适合排查特殊 GC 兼容问题。

## 常见命令骨架

可执行文件：

```powershell
scc .\build.jl -o .\artifacts\{entry-name}\app\{entry-name}.exe --bundle --static-mingw
```

动态库：

```powershell
scc .\build.jl -o .\artifacts\{entry-name}\shared\{entry-name}.dll --bundle --experimental-gen-header
```

C++ 源码：

```powershell
scc .\build.jl -d .\artifacts\{entry-name}\source -o .\artifacts\{entry-name}\source\libdemo -c --mode shared
```

带用例驱动：

```powershell
scc .\build.jl -o .\artifacts\{entry-name}\app\{entry-name}.exe --bundle --static-mingw --collect-instance --dispatch-limit 4
```

## 典型产物

可执行文件模式通常得到：

```text
artifacts/
└── {entry-name}/
    └── app/
        ├── {entry-name}.exe
        ├── lib/
        └── ...
.syslabcc-cache/
└── {entry-name}/
    └── app/
```

动态库模式通常得到：

```text
artifacts/
└── {entry-name}/
    └── shared/
        ├── {entry-name}.dll
        ├── {entry-name}.lib
        ├── {entry-name}.h    # 使用 --experimental-gen-header 时
        ├── lib/
        └── ...
.syslabcc-cache/
└── {entry-name}/
    └── shared/
```

C++ 源码模式通常得到：

```text
artifacts/
└── {entry-name}/
    └── source/
        ├── make.jl
        ├── Makefile
        ├── src/
        └── ...
```

若显式使用 `--cmake`，源码工程中还应检查 `CMakeLists.txt`；否则不要把缺少 `CMakeLists.txt` 误判为默认源码工程失败。

## 选项选择原则

- 交付二进制时，默认先考虑 `--bundle`。
- Windows 可执行文件交付默认先考虑 `--static-mingw`。
- `source` 模式必须同时记录 `-c` / `--no-compile`、`-d <dir>` 和底层 `--mode app|shared`。
- 静态库、CMake、Visual Studio 项目和交叉编译只在用户明确要求时启用，并记录对应官方高级文档来源。
- 先尝试通过改代码消除动态调用，再考虑 `--collect-instance`。
- 出现运行时错误时优先补 `--debugtrace`。
- 编译时间长或过程不明时补 `--verbose`。
- 请求头文件时，不要只看编译是否成功；还要实际检查 `.h` 是否落到目标产物目录或当前工作目录。
