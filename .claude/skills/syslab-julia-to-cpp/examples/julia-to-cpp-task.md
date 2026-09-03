# 示例任务

用户请求：

> 将现有 Julia 脚本通过 scc 生成 C++ 可执行文件，并确认能在无 Syslab 环境的机器上运行。

标准处理方式：

1. 先确认 `scc -h` 或 `scc --help` 可用。
2. 识别源码是否已有 `main()`；若没有，先让用户明确指定 `main()` 最终调用的 Julia 函数或业务入口，再在用户源文件同目录新建 `build.jl`，在 `build.jl` 中 `include` 用户源文件并补充 `main()`，不要先回退到源码修改建议。
3. 检查是否存在非 `const` 全局变量、`Any[]`、未定义变量和明显动态调用。
4. 形成 `docs/{entry-name}/codegen_plan.md`，写清楚目标为 `app` 模式。
5. 默认优先尝试如下命令形态：

```powershell
scc .\build.jl -o .\artifacts\{entry-name}\app\{entry-name}.exe --bundle --static-mingw
```

6. 验证：
   - Julia 侧运行结果
   - 从 Julia 外部直接启动 `artifacts/{entry-name}/app/{entry-name}.exe` 的结果
   - 产物目录中是否包含 `lib/` 与核心依赖
7. 输出兼容性结论、最终命令和部署注意事项。

如果用户请求：

> 将 Julia 函数导出为供外部程序调用的动态库，并顺带生成头文件。

则应改为：

1. 确认目标为 `shared` 模式。
2. 先让用户明确指定每个导出函数、导出符号名以及导出 ABI 约定；已有合法 `static_compile(...)` 可沿用，只有需要新增包装层时才在 `build.jl` 中用包装函数和 `SyslabCC.static_compile(...)` 声明导出符号。
3. 检查包装函数的完整 ABI 类型元组是否符合受支持范围：输入参数、输入数组维度参数、返回值对应的额外出参都要分别校验。
4. 默认优先尝试如下命令形态：

```powershell
scc .\build.jl -o .\artifacts\{entry-name}\shared\{entry-name}.dll --bundle --experimental-gen-header
```

5. 追加 C++ 或 Python 侧调用验证。

如果用户请求：

> 生成源码工程到 `artifacts/{entry-name}/source`，后续再决定是否编译成动态库或可执行文件。

则应改为：

1. 确认目标为 `source` 模式，并在命令中使用 `-c` / `--no-compile`。
2. 判断最终二进制语义对应 `app` 还是 `shared`，并据此决定入口要求；若最终入口需要补到 `build.jl`，仍沿用对应模式下“先由用户明确指定入口或导出目标”的规则。
3. 默认优先尝试如下命令形态：

```powershell
scc .\build.jl -d .\artifacts\{entry-name}\source -o .\artifacts\{entry-name}\source\libdemo -c --mode shared
```

4. 验证 `artifacts/{entry-name}/source` 下是否同时包含源码、构建脚本与必要依赖目录。
