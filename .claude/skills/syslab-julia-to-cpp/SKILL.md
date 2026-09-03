---
name: syslab-julia-to-cpp
description: 使用 SyslabCC 或 scc 将 Julia 或 Syslab Julia 代码生成、编译、打包、验证或排障为 `app`、`shared`、`source` 三类产物的技能；对应交付物包括 DLL、共享库、SO、动态库、EXE、可执行文件和 C++ 源码工程。只要任务涉及 `SyslabCC`、`scc`、`static_compile`、`collect-instance`、导出头文件、兼容性报告、验证报告、代码生成排障，或要求产物严格落在 `artifacts/{entry-name}/`、`tests/{entry-name}/`、`docs/{entry-name}/`、`.syslabcc-cache/{entry-name}/` 目录结构下，就必须优先使用本 skill，而不是直接凭经验运行 `scc`。`docs/{entry-name}/` 下文档统一用中文；`app` 和 `shared` 模式必须生成并实际运行 `tests/{entry-name}/` 下的验证脚本。
---

# Syslab Julia 到 C++ 代码生成

先使用 `syslab-environment`，相对路径：`../syslab-environment/SKILL.md`。  
只要任务涉及产物验证、回归或补测，继续使用 `syslab-testing`，相对路径：`../syslab-testing/SKILL.md`。

本 skill 的目标是：在不偏离用户原始 Julia 设计的前提下，稳定生成、验证并交付 `app`、`shared` 或 `source` 产物；所有命令、目录和文档都以本 skill 附带规则为准，不凭经验猜测。

## 触发优先级

- 用户只要提到以下任一类需求，就必须先读取并遵循本 skill，再决定是否调用 `scc`：
  - 生成动态库、DLL、共享库、SO、EXE、可执行文件或 C++ 源码工程
  - `SyslabCC`、`scc`、`static_compile`、`collect-instance`
  - 导出头文件、兼容性报告、验证报告
  - 代码生成失败、代码生成排障、动态库调用失败
- 命中触发条件后，不得跳过本 skill 直接写命令、改源码或在项目根目录散落交付物。
- 如果任务明显属于 Julia 到 C++ / 二进制代码生成，而本 skill 尚未被读取，应立即补读，并以本 skill 覆盖临时假设。

## 前置阅读顺序

1. 入口与产物模式：`references/codegen-entry-modes.md`
2. 工作流约束：`workflows/codegen-plan-contract.md`
3. 执行规则：`rules/codegen-rules.md`

如果任务以排障为主，再补读：

- `references/compiler-flags-and-artifacts.md`
- `references/common-failures.md`

## 适用范围

- 将一个或多个 Julia 入口文件生成为 `app`、`shared` 或 `source` 产物
- 设计并校验 `SyslabCC.static_compile(...)` 导出接口
- 为动态分派代码设计 `collect-instance` 方案
- 按固定目录结构组织产物、缓存、文档和回归脚本
- 对类型不稳定、导出不兼容、链接失败和生成失败做结构化排障

## 核心原则

- 先定模式，再定命令；不要混用 `app`、`shared`、`source` 的入口要求。
- 默认保持用户现有算法、入口关系和文件结构；不要因为代码生成顺带重构。
- 默认不直接修改用户源码；若只是缺入口或导出，优先创建同目录 `build.jl`。
- `app` 必须有稳定 `main()`；`shared` 必须有显式 `SyslabCC.static_compile(...)`；`source` 必须同时说明 `-c` 的使用方式和其底层对应的 `app` / `shared` 语义。
- 官方文档中的 `--mode static`、`--cmake`、Visual Studio 项目和交叉编译属于高级路由；除非用户明确要求，不并入本 skill 默认三模式。
- 若 `build.jl` 承担入口或导出，计划和报告中必须标明：哪些函数、导出项和签名来自用户明确指定。
- 若 `build.jl` 为 `shared` 模式新增包装函数，包装函数完整 ABI 签名必须按 `references/wrapper-arg-conversion.md` 推导；输入数组参数要显式补 `Ptr{Int64}` 维度参数，并在包装层内用 `unsafe_wrap(...; own=false)` 还原。
- 若用户函数存在返回值，包装函数签名还必须继续追加返回值对应的出参指针；标量返回值用 `Ptr{T}`，数组返回值用 `Ptr{element_type}`，包装函数最后统一 `return Int32(0)`。
- 最终交付必须围绕 `artifacts/{entry-name}/`、`tests/{entry-name}/`、`docs/{entry-name}/`、`.syslabcc-cache/{entry-name}/` 组织，不得把最终文件散落在项目根目录。
- 优先从 Julia 源码层修复问题，例如非 `const` 全局变量、未定义变量、明显动态调用和类型不稳定。
- 只有在确实无法避免动态分派时，才考虑 `--collect-instance`、`dispatch_limit` 或 `block_method_instance`。
- 交付 EXE 时默认优先考虑 `--bundle`；Windows EXE 交付默认优先考虑 `--static-mingw`。

## 标准工作流

所有任务按以下顺序推进：

1. 环境验证
2. 目标产物与入口模式识别
3. 兼容性与类型稳定性检查
4. 代码生成计划建立
5. 代码生成执行
6. 生成并运行验证测试脚本（仅 `app` 和 `shared`）
7. 测试脚本验证与交付说明输出

## 测试脚本生成规则（app / shared 模式）

- `app` 模式必须在 `tests/{entry-name}/app/` 下生成并运行 `runtests.jl`，至少覆盖：
  - 启动 `artifacts/{entry-name}/app/{entry-name}.exe`
  - 抓取输出
  - 用 `@test` 与 Julia 基线结果对比
- `shared` 模式必须在 `tests/{entry-name}/shared/` 下生成并运行验证脚本，至少覆盖：
  - 产物完整性检查：DLL、`.lib`、`.h`
  - 头文件导出签名校验
  - 外部调用验证：优先 C++ 或 Python，其次 Julia `ccall`
- 测试脚本必须使用 `using Test` 和 `@test`。
- 测试脚本中引用产物时，必须使用相对于脚本自身的路径，不得硬编码绝对路径。
- 测试结果必须写入 `docs/{entry-name}/verification_report.md`。

## 强门禁

- 首次编译前必须确认 `scc -h` 或 `scc --help` 可用。
- 必须确认使用的是当前 Syslab 安装目录下的 `Tools/SyslabCC/scc.exe`；不要默认使用 PATH 中的同名命令。
- `scc` 的运行依赖 `julia-ty.bat` / `julia-ty.sh` 启动后的 Syslab Julia 全局环境。检查依赖时，应确认该环境中已存在 `TyJuliaCAPI`、`TyRandom`、`MethodAnalysis`，禁止临时安装到项目环境。
- 未明确目标模式前，不得开始生成最终产物。
- 未完成目录规划和计划落地前，不得把最终交付文件直接写入项目根目录。
- `app` 缺 `main()` 时，必须先通过同目录 `build.jl` 补入口；未补入口不得宣称完成 `app` 交付。
- `shared` 缺 `static_compile(...)` 时，必须先通过同目录 `build.jl` 补导出；未补导出不得宣称完成 `shared` 交付。
- 若 `app` / `shared` 通过 `build.jl` 补入口或导出，计划中必须记录：
  - `build.jl` 与用户源文件的 `include` 关系
  - 用户明确指定的入口函数或导出函数
  - `shared` 时每个导出项的参数类型和返回类型
- `source` 模式的计划中必须说明：
  - 生成目录
  - `-c` / `--no-compile` 的使用方式
  - 底层对应 `app` 还是 `shared`
- 导出动态库前，必须先检查导出签名是否落在受支持的标量、复数、`Nothing`、`Cstring`、`Ptr{T}` 等范围内，并遵守额外限制。
- 验证阶段必须创建 `tests/{entry-name}` 并提供可运行测试脚本；缺脚本即判定为失败。
- 未获授权却直接修改用户源码，判定为失败。

## 计划落地

完成目标模式识别后，读取 `templates/codegen-plan-template.md`，创建并持续更新 `docs/{entry-name}/codegen_plan.md`。

默认输出目录结构：

```text
<project-root>/
├── artifacts/
│   └── {entry-name}/
│       ├── source/
│       ├── shared/
│       └── app/
├── tests/
│   └── {entry-name}/
│       ├── app/
│       └── shared/
├── docs/
│   └── {entry-name}/
└── .syslabcc-cache/
    └── {entry-name}/
        ├── source/
        ├── shared/
        └── app/
```

- 默认不保留空目录；某模式本次未生成，则对应目录可不存在。
- 单模式任务只覆盖对应模式目录，不顺带删除同一入口下其他已有模式目录。

## 目录合规要求

- 最终交付产物必须落在 `artifacts/{entry-name}/app`、`artifacts/{entry-name}/shared` 或 `artifacts/{entry-name}/source` 之一。
- 最终交付文档必须落在 `docs/{entry-name}/`，且统一用中文。
- 最终交付验证脚本或回归结果必须落在 `tests/{entry-name}/`。
- 中间缓存与编译副产物必须归档到 `.syslabcc-cache/{entry-name}/`。
- 若用户明确要求严格目录结构，应将其视为硬门禁，而不是偏好建议。
- 下列文件若作为最终交付直接出现在 `<project-root>/`，视为目录不合规：
  - `{entry-name}.dll`
  - `{entry-name}.lib`
  - `{entry-name}.h`
  - `{entry-name}.exe`
  - `bdwgc.dll`
  - `syslabcrt-io.lib`
- 若工具默认行为曾在根目录短暂产生这些文件，最终交付前必须整理到规定目录，并在 `docs/{entry-name}/verification_report.md` 记录最终路径。

计划中至少包含：

- 目标模式：`app` / `shared` / `source`
- 源文件与入口文件清单
- `main()` 或 `static_compile(...)` 清单
- 编译命令草案与关键选项
- 产物输出目录
- 类型稳定性与兼容性检查结果
- 验证方案
- 风险与待确认项

## 小任务与默认任务

- 小任务：单个本地 `.jl` 文件，且只生成一个简单 EXE 或一个简单动态库。
- 只要涉及多文件入口、多个导出符号、C++/Python 联调、跨平台参数或多轮排障，就按默认任务处理。
- 小任务也必须走完整工作流，但最终文档可以精简。

## 何时读取哪些文件

- 工作流约束：`workflows/codegen-plan-contract.md`
- 阶段执行规则：`workflows/codegen-plan-execution-rules.md`
- 规则与门禁：`rules/codegen-rules.md`
- 验收清单：`rules/codegen-acceptance-checklist.md`
- 官方文档核对点：`references/official-codegenerator-docs.md`
- `shared` 包装函数 ABI 规则：`references/wrapper-arg-conversion.md`
- 模板：`templates/`
- 示例：`examples/julia-to-cpp-task.md`
- 快速盘点入口：`scripts/scan-julia-codegen-entrypoints.jl`
- 如果用户输入缺少 `main()` 或 `SyslabCC.static_compile(...)`，优先创建同目录 `build.jl`，由 `build.jl` `include` 用户源文件并补充入口或导出，再继续生成产物。

## 最低交付

默认任务至少交付：

- `docs/{entry-name}/codegen_plan.md`
- `docs/{entry-name}/compatibility_report.md`
- `docs/{entry-name}/verification_report.md`
- `docs/{entry-name}/issues.md`
- `docs/{entry-name}/source_change_suggestions.md`（仅当 `build.jl` 方案也不足，且未获授权直接改源码时）
- `tests/{entry-name}/app/runtests.jl`（`app` 模式必须）
- `tests/{entry-name}/shared/` 下验证脚本（`shared` 模式必须）
- 编译命令或生成命令
- 至少一种有效验证结果

小任务至少交付：

- `docs/{entry-name}/codegen_plan.md`
- `tests/{entry-name}/app/runtests.jl`（`app` 模式必须）
- `tests/{entry-name}/shared/` 下验证脚本（`shared` 模式必须）
- 编译命令
- 验证结论
- 未解决问题记录

## 失败判定

- 出现以下任一情况，不得宣称“已完成交付”：
  - 命中本 skill 触发条件，但未先读取本 skill
  - 未先确认 `scc -h` 或 `scc --help` 可用
  - 未明确 `app` / `shared` / `source` 模式就开始生成最终产物
  - 缺少 `main()` 或 `static_compile(...)`，却既未创建同目录 `build.jl`，也仍宣称完成交付
  - 最终产物散落在项目根目录，未整理到 `artifacts/{entry-name}/...`
  - 缺少 `docs/{entry-name}/codegen_plan.md`
  - 缺少基本验证结论，或未区分 Julia 基线验证与产物验证
  - `app` 模式未在 `tests/{entry-name}/app/` 生成并运行测试脚本
  - `shared` 模式未在 `tests/{entry-name}/shared/` 生成并运行测试脚本
  - 未获授权却直接修改用户源码
- 发生失败判定时，至少要在 `docs/{entry-name}/issues.md` 记录失败原因、当前状态和下一步建议。

## 参考资料

- 本 skill 自带资料优先从以下相对路径读取：
  - `references/`
  - `rules/`
  - `templates/`
  - `workflows/`
  - `examples/`
  - `scripts/`
- 若任务需要进一步核对 `SyslabCC` 能力或本地帮助文档，应通过当前 Syslab 环境定位，不在 skill 中写安装绝对路径。
