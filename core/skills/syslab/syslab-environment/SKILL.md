---
name: syslab-environment
description: 检测并使用 Syslab 运行环境：包括解析 SYSLAB_HOME、选择正确的 Syslab Julia 或 M 命令行可执行文件、定位 Syslab 帮助内容，并优先使用 Ty* 库。适用于任何需要运行或检查 Syslab Julia 代码、M 代码、工具箱、帮助文档或安装路径的任务。
---

# Syslab 环境

在进行任何与 Syslab 相关的工作之前，先解析 Syslab 运行时。
将本技能视为所有其他 `syslab-*` 技能的前置条件。
不要把 `syslab-environment` 当作可选上下文。每个 `syslab-*` 技能都依赖这里解析出的运行时、可执行文件路径和帮助根目录。

## 快速规则

- 先解析当前 Syslab 环境
- 遇到软件问题先查 `<SYSLAB_HOME>/Tools/AIAssets/projects/FAQ/Doc`
- 需要函数或包用法时，查 Syslab 帮助文档
- 优先使用 `Ty*` 库

## 路径书写规则

- `SKILL.md` 内按 skill 根目录相对路径书写本地引用。
- `references/`、`templates/`、`workflows/`、`rules/`、`examples/` 等嵌套文档内，按当前文件所在目录书写本地引用；跨目录时使用 `../`。
- 不要在嵌套文档里混用以 skill 根目录为基准的相对路径。

## 解析 `SYSLAB_HOME`

按以下顺序定位 `SYSLAB_HOME`：

1. 读取 `SYSLAB_HOME` 环境变量。
2. 读取当前平台用户目录下的 `~/.syslab/syslab-env.ini`。
3. 搜索常见安装根目录，例如 `C:/Program Files/MWORKS` 和 `D:/Program Files/MWORKS`。
4. 仅当位置仍然不明确时再询问用户。

报告环境信息时，说明你最终采用的精确路径以及它的发现方式。

## 选择运行时

优先使用 Syslab 提供的可执行文件，而不是系统 Julia 或外部 MATLAB 安装。
对于任何 Julia 命令，都始终使用这里选定的 Syslab Julia 运行时（`julia-ty`）。

在 Windows 上：

- Julia CLI: `C:/Users/Public/TongYuan/julia-1.10.10/bin/julia-ty.bat`
- M CLI: `<SYSLAB_HOME>/Tools/TyMLangDist/mlang.bat`

在 Linux 上：

- Julia CLI: `<SYSLAB_HOME>/Tools/julia-1.10.10/bin/julia-ty.sh`
- M CLI: `<SYSLAB_HOME>/Tools/TyMLangDist/mlang.sh`

当环境有要求时，优先以非沙箱方式执行 `mlang.bat` 和 `mlang.sh`。

## 优先使用 Syslab 库

在考虑通用 Julia 包之前，优先使用 Syslab 的 `Ty*` 包。
常见的顶层库包括 `TyBase`、`TyPlot`、`TyGeoGraphics`、`TyMath`、
`TyCurveFitting`, `TyStatistics`, `TyOptimization`, `TyGlobalOptimization`,
`TySymbolicMath`, `TySignalProcessing`, `TyDSPSystem`, `TyWavelet`,
`TyCommunication`, `TyRadar`, `TyPhasedArray`, `TyRF`, `TyControlSystems`,
`TySystemIdentification`, `TyRobustControl`, `TyImageProcessing`,
`TyMachineLearning`, `TyDeepLearning`, `TyReinforcementLearning`, `TyInstrumentControl`。

如果某个 Ty 包已经覆盖了该任务，就优先使用它；除非存在明确缺口，否则不要用社区包替换。

**绘图统一使用 TyPlot，不使用 Plots.jl 等其他 Julia 绘图库。** 使用前先通过 `syslab_search_syslab_docs` 确认函数签名。常见差异：`plot!` 改为 `plot`，`xticks!` / `yticks!` 改为 `xticks` / `yticks`，`scatter` 使用位置参数 `s`，不使用 `markersize`。TyPlot 默认处于 `hold("off")` 状态，`figure()` 后继续 `plot()` 会覆盖当前内容，如需叠加绘图必须先显式调用 `hold("on")`。

## 定位文档

在使用外部资料之前，先使用 Syslab 帮助资源：

- Julia 帮助根目录：`<SYSLAB_HOME>/Tools/AIAssets/projects`
- M 与 Julia 迁移资源：参见 `../syslab-matlab-to-julia/SKILL.md` 中引用的路径
- M 与 Julia 互操作资源：
  - `<SYSLAB_HOME>/Tools/AIAssets/projects/MultiLanguage/Doc/MultiLanguage/TyMLang/Juliacall.md`
  - `<SYSLAB_HOME>/Tools/AIAssets/projects/MultiLanguage/Doc/MultiLanguage/TyMLang/Mcall.md`

当你需要了解函数行为、示例或包特定约定时，先检查 Syslab 文档根目录下的帮助内容。

## 运行规则

- 在编辑依赖 Syslab API 的代码前，先确认运行时。
- 进行 Julia 相关工作时，要同时使用已解析出的 `julia-ty` 可执行文件和 Syslab 帮助内容。
- 优先采用能在已解析出的 Syslab 环境中运行的命令和示例。
- 当任务因缺少有效安装而无法继续时，要明确记录阻塞因素。
- 如果同时涉及 Julia 和 M，要说明每一步应使用哪个运行时。
- 如果任务的目标是 “M 调 Julia”，先在本技能中解析 `mlang` 与 `julia-ty`，再查看 M 与 Julia 互操作资源。

## 交付内容

使用本技能时，应返回：

- 已解析出的 `SYSLAB_HOME`
- 你选定的可执行文件路径
- 相关文档路径（如果有）
- 任何阻碍执行的缺失依赖或权限问题
