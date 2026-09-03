---
name: syslab-digital-filter-design
description: Julia 数字滤波器设计专家：使用 TySignalProcessing 和 TyDSPSystem 在 Julia 中设计并验证数字滤波器。适用于创建、比较或调优 FIR/IIR 及低通、高通、带通、带阻、陷波滤波器，使用 filterDesigner 或 fvtool，选择直接设计函数或 fdesign 工作流，以及验证频率响应、相位、群延迟与零极点特性。
---

# Julia 数字滤波器设计专家

使用 `TySignalProcessing` 和 `TyDSPSystem` 在 Julia 中设计、实现并验证数字滤波器。
先使用 `syslab-environment`。相对路径：`../syslab-environment/SKILL.md`。

本技能必须使用由 `syslab-environment` 解析出的共享 Syslab 帮助文档和 Julia 运行器。

## 环境与兼容性

- 主要包：`TySignalProcessing` 和 `TyDSPSystem`
- 可选 GUI 包：`TyFilterDesigner`
- Julia 运行器：使用由 `syslab-environment` 解析出的 Syslab Julia CLI
- 本技能附带的 GUI 辅助脚本位于 `scripts/`
- GUI 支持是可选的。默认工作方式是代码驱动流程，即使 GUI 启动失败也必须保持可用。

## 目录说明

- `workflows/` 包含可重复使用的预检与验证流程。
- `templates/` 包含可直接复用的 Julia 设计模式模板。
- `scripts/` 包含可运行的辅助脚本，例如打过补丁的 GUI 启动器。
- `references/` 包含 API 路由说明、主题卡片和补充参考资料。
- `examples/` 包含已经验证过的任务示例。

## 必须遵循

- 选择 API 前先阅读 `references/INDEX.md`。
- 先通过 `syslab-environment` 解析 `<SYSLAB_HOME>`。
- 当 API 语法、选项、应用行为或支持的工作流不明确时，只使用 `<SYSLAB_HOME>/Tools/AIAssets/projects` 下的共享帮助页面。
- 运行每一个 Julia 脚本时，都使用由 `syslab-environment` 选定的 Syslab Julia CLI。不要在本技能中硬编码 `julia-ty.bat`。
- 优先把 Julia 代码写入 `.jl` 文件，再执行该文件。出错后编辑并重新运行。
- 当用户以 Hz 提供频率时，不要猜测 `Fs`。除非用户明确要使用归一化频率，否则应先询问。
- 当是否为流式处理还是离线处理会影响架构或相位行为时，不要自行猜测。
- 如果任务依赖模式或相位行为，而用户没有明确说明，就停下来询问，不要静默替用户做选择。
- 优先使用 `TySignalProcessing` 中直接的 FIR/IIR 设计函数，例如 `butter`、`cheby1`、`cheby2`、`ellip`、`remez`、`firpm`、`firpmord` 以及相关分析辅助函数。
- 仅在用户明确要求该工作流、方法发现本身很重要，或 `SystemObject` 是更合适输出形式时，才使用 `fdesign_* -> designmethods -> designoptions -> design`。
- 将 `filterDesigner()` 视为可选的 GUI 辅助工具。如果应用在当前环境中初始化失败，应立即退回到代码驱动工作流。
- 在本技能中，如果请求 GUI 辅助，优先使用附带的补丁版 GUI 启动器：
  - `scripts/launch_filterDesigner_patched.jl`
  - helper: `scripts/patched_filterDesigner.jl`
- 对于可部署的 IIR 和多速率处理链，优先使用 system-object 输出：
  - `design(..., "SystemObject", true)`
- 当给出了硬性指标时，不要只停留在绘图结果。若这些指标重要，应报告通带纹波、阻带衰减或群延迟变化的数值结果。

## 共享帮助路径

- 共享 Julia 帮助根目录：`<SYSLAB_HOME>/Tools/AIAssets/projects`
- 本技能中的所有帮助页引用都相对于该根目录。
- 本技能使用的路径类别：
  - `TySignalProcessing/Doc/TySignalProcessing/` 用于直接的信号处理 API，例如 `butter`、`cheby1`、`cheby2`、`ellip`、`remez`、`firpm`、`freqz`、`phasez` 和 `filtfilt`
  - `TyDSPSystem/Doc/TyDSPSystem/` 用于 `fdesign_*`、`design`、`designmethods`、`designoptions`、`fvtool`、`filterDesigner` 以及可部署的 system-object 工作流
  - `TySignalProcessing/App/TySignalProcessing/` 用于面向 GUI 的工作流，例如 Filter Designer、FVTool、Window Designer 和 Signal Analyzer
- 示例展开：
  - `TySignalProcessing/App/TySignalProcessing/FilterDesigner.md`
  - `TySignalProcessing/App/TySignalProcessing/GettingStartedwithFilterDesigner.md`
  - `TyDSPSystem/Doc/TyDSPSystem/FilterDesignAndAnalysis/FilterAnalysis/filterDesigner.md`
  - `TySignalProcessing/Doc/TySignalProcessing/DigitalAndAnalogFilters/DigitalFilterAnalysis/freqz.md`

- 读取最小且相关的帮助页，而不是扫描整棵目录树。

## 预检流程

1. 列出你预计要调用的 Julia 函数。
2. 针对每个函数或任务检查 `references/INDEX.md`。
3. 先解析 `<SYSLAB_HOME>`；当精确的 API 行为很重要时，在编写代码前阅读所需卡片以及对应的共享帮助页。
4. 在回复中写出 `Preflight: ...`。
5. 编写一个 `.jl` 文件，使用由 `syslab-environment` 解析出的 Syslab Julia CLI 运行它，并在呈现最终代码前修复错误。

## 选择架构前的强制停止点

如果以下任一信息缺失，且会实质性影响设计，就必须停下来请求澄清：

- 以 Hz 表示规格时所需的 `Fs`
- `streaming` 还是 `offline`
- 当零相位、线性相位或因果 IIR 行为会改变建议时，对相位的要求
- 关键边缘频率、纹波、衰减或阶数约束

## 设计需求收集清单

- `Fs`，单位为 Hz，除非用户明确要求归一化频率
- 响应类型：低通、高通、带通、带阻、陷波、多速率或任意幅度响应
- 边缘频率以及纹波或衰减目标
- 模式：`streaming` 或 `offline`
- 相位要求：零相位、线性相位，或不关心
- 约束条件，例如阶数、抽头数、延迟、内存或结构

## 工作流选择

### 在以下情况下使用直接设计函数：

- 用户希望基于已知的 FIR 或 IIR 家族快速得到一个实用滤波器
- 阶数已经固定，或很容易直接确定
- 用户需要紧凑的系数级代码
- 该设计天然适合映射到 `remez`、`firpm`、`butter`、`cheby1`、`cheby2` 或 `ellip`
- 不需要 `SystemObject` 输出，也不需要做设计方法发现

### 在以下情况下使用 `fdesign_*` 加 `design`：

- 用户明确要求使用 `fdesign` 工作流
- 你需要先检查可用方法，再决定使用哪一个
- 你希望在 FIR 和 IIR 之间采用一致的规格对象工作流
- 你需要 `SystemObject`
- 相比直接调用某个设计家族函数，该设计更适合表达为通带或阻带规格

## 参考文件

- 阅读 `workflows/filter-design-workflow.md` 以获取通用工作流和验证规范。
- 阅读 `templates/filter-design-patterns.md` 以获取可直接复用的 Julia 模板。
- 当过渡带较窄或效率很重要时，阅读 `references/efficient-filtering.md`。
- 当你需要权威的 API 名称、签名、选项、示例或应用使用细节时，阅读对应的共享帮助页。
- 将 `examples/` 中的脚本用作已经验证过的起点，适用于低通、带阻、陷波、带通加全通补偿，以及基于 Remez 的 FIR 工作流。

## 交付格式

- 回顾最终的规格说明块
- 说明所选架构及其原因
- 提供可作为 `.jl` 文件运行的 Julia 代码
- 展示验证调用，例如 `fvtool`、`freqz`、`grpdelay` 或 `zplane`
- 当给出了规格指标时，报告相应的数值验收检查结果
- 说明结果是系数形式还是 system object
