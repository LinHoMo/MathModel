# 常见失败模式

## 非 `const` 全局变量

典型报错：

```text
Compiler Error(...): non-constant global variable
```

处理方式：

- 优先改为 `const` 全局变量。
- 如果需要可变性，优先改成 `const x = Ref(...)`，通过 `x[]` 读写。

## 未定义变量或未定义函数

典型报错：

```text
Compiler Error(...): undefined variable
```

处理方式：

- 检查拼写、作用域、`include(...)` 和模块导入是否完整。
- 不要依赖“运行不到的分支不会出错”这种动态语言假设。

## 动态调用

典型现象：

- 默认模式可编译，但运行时报 `dynamic call(...)`

处理方式优先级：

1. 改源码，消除 `Any`、抽象容器、类型不稳定分支
2. 用 `isa` 分支把动态性收敛到静态分支
3. 确实无法改写时，再使用 `--collect-instance`

## 原语函数的类型不稳定调用

典型场景：

- `tuple(...)`
- 某些 `Core.Builtin` / `Core.IntrinsicFunction`

处理方式：

- 先封装为普通用户函数，必要时加 `@noinline`
- 再结合用例驱动
- 不要指望所有原语动态调用都能直接由 `--collect-instance` 解决

## 动态库导出签名不受支持

动态库导出参数/返回值应限制在受支持的标量、复数、`Nothing`、`Cstring`、`Ptr{T}` 范围内。

额外限制：

- 参数不能是 `Nothing`
- 返回值不能是 `Cstring`

如果导出签名不合规：

- 已有 `static_compile(...)` 可以在签名合规时直接导出，不必强行改成包装函数
- 优先写一层稳定的导出包装函数
- 在包装函数中把复杂 Julia 类型转换为可导出的标量或指针协议
- 若业务返回值不适合直接作为 ABI 返回值，优先改写为额外出参，并让包装函数自身返回 `Int32` 状态码

## 请求头文件但未实际生成

典型现象：

- 使用 `--experimental-gen-header` 后，DLL 编译成功，但目标目录中没有 `.h`
- 头文件实际上生成在当前工作目录，导致只检查 DLL 目录时误判为缺失

处理方式：

- 先确认命令中确实包含 `--experimental-gen-header`
- 再同时检查目标目录和当前工作目录，而不是只看编译成功日志
- 若 `.h` 缺失，记录到 `docs/{entry-name}/issues.md`
- 在未拿到头文件前，不要宣告“动态库和头文件均已交付”

## 方法实例收集过多

典型现象：

- `--collect-instance` 后编译规模膨胀
- 收集到无关方法实例导致新的编译错误

处理方式：

- 降低动态调用面
- 针对单个函数使用 `SyslabCC.dispatch_limit`
- 必要时使用 `SyslabCC.block_method_instance`
- 将限制策略写入 `docs/{entry-name}/issues.md` 或计划文档
