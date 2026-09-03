# Ribbon 生成门禁

本文档是 Syslab App Designer ribbon/toolstrip 生成、修改和审查任务的第一入口。它只收敛生成前建模、生成后自检和一票否决项；具体 API、布局、控件和验收细节见相关规则文档。

核心原则：

- 源图标线索不是图标完成状态；只有生成可渲染 `iconSrc` / `IconSrc` 才算图标完成。
- 图标解析流程和失败门禁以 [source/icon-resolution.md](../source/icon-resolution.md) 为准。

## 生成前门禁

生成或修改 ribbon 前，必须先确认下面的信息。信息不足时标记为 `unknown`，不得自行补洞后声明对标完成。

如果任务不是源应用对标，而是从零设计新 ribbon，应建立 target layout model，记录目标 tab / section / column / control 决策；不需要伪造源证据，也不得声明“源应用对标完成”。

### 1. 唯一主产物

- 当输出包含 `.slapp` 时，本次最终交付只能有一个主 `.slapp`。
- 不得未说明地同时交付 `app.slapp` 和业务命名 `.slapp`。
- 如果存在中间 `.slapp`，必须在交付说明或审计报告中标明它不是主入口。
- 如果输出目录也是 Syslab App Designer 的打开/运行目录，主工程推荐命名为 `app.slapp`，避免设计器运行时默认生成或覆盖 `app.slapp` 后出现两个候选 `.slapp`。
- 如果调用方要求使用业务命名 `.slapp`，必须在验收报告中说明运行后可能产生 `app.slapp` 副产物，并在最终交付前清理或标记该副产物不是主入口。
- 生成 `app.slapp` 后，必须同步生成同目录 `app.jl`。当前 Syslab App Designer 打开工程时要求 `.slapp` 与同目录 `app.jl` 同时存在；缺少任一文件都不能作为可打开工程交付。
- `.slapp` 仍是 App Designer 工程描述真相源；`app.jl` 是同目录必要伴随源码，必须与本轮 `.slapp` 生成结果同步，不得把过期或手工残留的 `app.jl` 当作通过依据。

### 2. 工程名与模块名

- `.slapp.name` 会被 App Designer 代码生成器用作 Julia `module` 名，必须是合法 Julia 标识符。
- `.slapp.name` 不得包含空格、连字符、标点、中文或其它不能直接出现在 `module <Name>` 中的字符。
- 源应用显示标题、产品名或带空格的人类可读名称，应写入 `figure.name`、`info.name` 或窗口标题字段，不得写入 `.slapp.name`。
- 生成后必须检查 `.slapp.code` 和设计器重新生成的 `app.jl` 第一行，不能出现类似 `module Antenna Array Designer Ribbon` 的非法模块声明。
- `.slapp.userLoadedModule` 等可编辑代码片段字段缺省时必须写为空字符串，不能缺字段导致设计器生成裸标识符 `undefined`。

### 3. Layout Model

源应用对标任务必须建立 source layout model；从零设计任务必须建立 target layout model。至少记录：

- 每个 tab / section / column 的顺序。
- 每个 column 内的控件列表和 command 控件数量。
- 每个 column 的 `columnKind`：`singleCommand`、`stackedCommands`、`fieldStack`、`gallery`、`mixed` 或 `unknown`。
- 每个 column 的 `commandCount`、`largeCommandCount`、`allowedDisplayMode` 和 `columnLayoutDecision`。
- 源应用对标任务中，每个 source column 的边界：`sourceColumnId` / `sourceIndex`、父 section、按顺序排列的 control id / tag / text、以及是否被目标拆分或合并。
- 每个控件的源 class / role / control type；没有源应用时记录目标控件类型和决策依据。
- 每个控件是否有菜单、popup、gallery item 或动态菜单。
- 每个菜单项是否有 checkbox / radio / toggle / checked 语义。
- 每个控件和 item 是否有源图标；没有源应用时记录目标图标策略。
- 源应用对标任务中，每个关键字段的 `evidenceSource`：`liveSnapshot`、`sourceCode`、`screenshot`、`manual`、`historySpec` 或 `unknown`。
- `recursiveExtractionStatus`：每个 popup / gallery / category / submenu 容器是否已递归展开到可交互叶子项。MATLAB `GalleryCategory` 必须继续读取 `Children`，不能只把 category 数量当作 item 数量。

`columnKind = "unknown"` 时，生成器可以产出草稿或不完整报告，但不得声明“对标完成”“验证通过”或“符合 skills”。

`recursiveExtractionStatus.status` 不是 `pass` 时，源应用对标任务不得声明 ribbon 内容完整对标；只能标为 `unknown` / `incomplete` / `accepted_difference`，并写入差异报告。

源运行时、源码或等价证据已经证明的 source column 边界优先于默认 displayMode 启发式。生成器不得因为 `large`、文本换行、图标大小、业务分组名或固定模板，静默拆分或合并源 column。确因目标平台能力限制无法保持时，必须写入 `known_differences.json` 或验收报告，并标记为 `accepted_difference` / `unknown`，不得声明完全对标。

### 4. 图标解析计划

源应用对标任务中，只要源证据显示 control 或 item 有图标线索，就必须建立 `iconResolutionPlan`。图标线索包括但不限于：

- 独立图片路径
- icon id
- icon class
- CSS class
- resource key
- theme token
- object handle
- sprite sheet / atlas
- background-position
- crop rect
- runtime image object
- 源截图中可见图标
- 人工标注的源图标

`iconResolutionPlan` 至少包含：

- source control/item id
- source icon evidence
- evidence type
- planned lookup path
- expected output file
- expected `.slapp` `iconSrc`
- expected `app.jl` / `.slapp.code` `IconSrc`
- evidenceSource

`iconResolutionPlan` 必须驱动生成器写入 `iconSrc` / `IconSrc`。不得先生成 ribbon，再只用静态检查发现缺图标；发现 `pending`、`unknown` 或 `unresolved` 时，必须继续解析，或在调用方明确接受差异时写入 `known_differences.json` 并保持整体 `incomplete` / `accepted_difference` 状态。

非独立图片文件的图标线索必须按 [source/icon-resolution.md](../source/icon-resolution.md) 解析；该文档是解析路径、状态分类、缓存映射、运行后回归检查和失败门禁的唯一详细规则源。

没有 `iconResolutionPlan` 时，不得进入源应用对标生成。

### 4. 源 Class 强映射

必须保留源控件类型语义，不能仅按文本重猜控件类型。例如：

- 源 command button -> Syslab `button`
- 源 toggle -> Syslab `toggle`
- 源 dropdown action -> Syslab `dropdownbutton`
- 源 split action -> Syslab `splitbutton`
- 源 checkbox item -> item `Checked` + 父控件 `menuSelectionMode = "multiple"`
- 源 radio / mutually exclusive menu -> 父控件 `menuSelectionMode = "single"` + `menuItemMarkStyle = "radio"`

不得因为 dropdown 和 split 都有下拉入口而互换映射，除非调用方明确授权并记录差异。

### 5. 菜单证据

- 空 `Popup`、空 `children`、空 `items` 或空 `menuGroups` 只能表示当前提取路径没有拿到菜单项。
- 这些空结果不能证明源菜单为空，也不能作为降级为普通 `button` 的依据。
- 从源码、截图、人工标注或历史 spec 补出的菜单项必须记录 `evidenceSource`。
- 源控件类型已经是 `DropDownButton`、`SplitButton`、`ListItemWithPopup` 或等价 popup 控件时，即使菜单项暂时为空，也必须保留下拉语义并继续补证据；不得生成普通 `button` 后声明通过。
- 源控件为带 checkbox / multiple 菜单项的 `DropDownButton` 或等价 popup 控件时，目标必须保留为带图标、非空菜单和 multiple checkbox 语义的 `dropdownbutton`，否则标为 `fail`、`unknown` 或 `incomplete`。

## 生成后门禁

最终答复或交付前，必须按实际输出类型执行下面的检查。输出包含 `.slapp`、`app.jl` 或资源目录时，分别检查对应产物。

### 0. App Designer 工程伴随文件

输出包含 `.slapp` 时，必须先检查工程目录能否作为 Syslab App Designer 可打开工程：

- 主 `.slapp` 必须存在，推荐为 `app.slapp`。
- 同目录 `app.jl` 必须存在；不能只交付 `.slapp`。
- `app.jl` 必须与本轮 `.slapp` 同步生成或同步更新，不能是旧工程残留。
- `app.jl` 必须可被 Julia `Meta.parseall` 解析。
- `.slapp.callbackFunctions`、`.slapp.figure.toolstrip` 中的回调、图标和菜单状态必须能在同步生成的 `app.jl` / `.slapp.code` 中找到对应运行态表达。
- 只要目标是“可打开/可运行/可交付 App Designer 工程”，缺少同目录 `app.jl` 就是失败；不得把 `.slapp` 单独存在解释为已完成。

### 1. 多 Command Column

command 控件只包括普通命令型 ribbon control：`button`、`toggle`、`splitbutton`、`dropdownbutton`。字段型控件、label/spacer、`matlab-gallery` / `gallery` 的 item 不按普通 command column 审计。

- 同一 column 内有两个或以上 command 控件时，column 必须是 `layout = "stack"`。
- stack 内 command 控件必须全部是 `displayMode = "small"`。
- `displayMode = "large"` 的 command 必须独占 command column；它不能与其它 command 共用同一个 column。
- `column.layout = "stack"` 中不得出现 `displayMode = "large"` 的 command。
- 同一 column 内三个 button / toggle / splitbutton / dropdownbutton 都为 `large` 是生成错误。
- large command 布局失败是硬失败门禁，不能被 JSON 解析、Julia include、图标存在、回调存在、App Designer open 成功或其它检查覆盖。

### 2. 图标字段

- `.slapp.figure.toolstrip` 的正式设计态渲染字段是 `iconSrc`。
- `app.jl` / Julia 构造器的正式运行态渲染字段是 `IconSrc`。
- `iconFile`、`sourceIconId`、`sourceIconClass`、`sourceIconPath`、CSS class、resource key、object handle、sprite sheet 路径、sprite 坐标和 crop rect 只能作为审计或中间字段。
- 审计字段不能替代渲染字段。
- 父控件 `iconSrc` / `IconSrc` 不能替代菜单 item 或 gallery item 自己的图标。
- 源证据显示 control 或 item 有图标线索时，目标 control 或 item 必须有可渲染 `iconSrc`，运行代码必须有对应 `IconSrc`。

### 3. 图标解析验收

生成后必须检查：

- 每个有源图标线索的 control/item 是否有可渲染 `iconSrc`。
- `app.jl` / `.slapp.code` 是否有对应 `IconSrc`。
- 输出资源文件是否真实存在。
- `iconResolutionStatus = "unresolved"` 的数量是否为 0。
- 只记录 `sourceIconClass` / `sourceIconId` / `sourceIconKey` / `sourceIconPath` / sprite 坐标但没有渲染字段的数量是否为 0。

如果 unresolved > 0，只能标记为 `incomplete`、`unknown` 或 `accepted_difference`，不能声明源应用图标对标完成。

### 4. 菜单项状态

- 源 item 有 checkbox / checked / toggle 语义时，父控件必须有 `menuSelectionMode = "multiple"`，item 必须保留 `checked` / `Checked`。
- 源 item 有 radio / mutually exclusive 语义时，父控件必须有 `menuSelectionMode = "single"` 和 `menuItemMarkStyle = "radio"`。
- 不能只生成普通 `ToolstripItem(Label, Value, CommandId)` 后声明选择语义已保留。

### 5. 目标能力差异

- 如果 Syslab 当前正式控件不能表达源菜单层级、动态 popup 或视觉细节，必须写入 `known_differences.json` 或验收报告。
- 降级结果只能标为 `accepted_difference` 或 `unknown`，不能标为完全 `pass`。

### 6. 设计器打开后运行门禁

输出包含 `.slapp` 时，最终验收必须覆盖 Syslab App Designer 打开 `.slapp` 后的真实运行链路：

- 必须用 Syslab App Designer 打开主 `.slapp`。
- 必须通过设计器自己的 Run 命令运行，不能只用 Julia `include(app.jl)`、`Meta.parseall` 或外部 `executeFile(app.jl)` 替代。
- 运行后必须检查设计器重新生成的 `app.jl`，至少确认：
  - `module` 声明合法。
  - 不存在裸标识符 `undefined`。
  - Julia 语法可解析。
  - 绑定的回调函数仍存在。
  - `IconSrc` 仍保留且指向存在的资源文件。
  - 主 `.slapp` 仍是唯一主入口；运行产生的副产物必须清理或标记为非主入口。
- 如果自动化服务或运行链路暂不可用，不得立刻放弃。必须先尝试启动 Syslab 宿主并打开主 `.slapp`，等待 App Designer 扩展激活，轮询插件本机 IPC 发现索引，并通过 `latestDiscoveryFile` 中的 `http-over-ipc` `/health` 接口确认服务可用。发现索引位置：Windows 优先为 `%LOCALAPPDATA%\TongYuan\SyslabAppDesigner\automation\syslab-app-designer-automation.json`，否则为 `%USERPROFILE%\.syslab-app-designer\automation\syslab-app-designer-automation.json`；Linux/macOS 优先为 `$XDG_RUNTIME_DIR/syslab-app-designer/automation/syslab-app-designer-automation.json`，否则为 `$HOME/.syslab-app-designer/automation/syslab-app-designer-automation.json`。
- 只有启动失败、连接超时、health 不通或接口持续报错后，才允许在 `visual_audit_report.json` 或验收报告中记录 `targetRuntimeSnapshot = "unknown"` / `unavailable`。
- 命令行 Julia `include(app.jl)` 不能作为启动 App Designer 服务端或完成运行验收的替代。命令行运行到 `uifigure` / `create_figure` 失败时，应先区分 UI 服务连接失败与代码语法错误。

## 一票否决

命中以下任一项时，不能声明符合 skills：

- 输出包含 `.slapp` 时，未说明地同时交付多个候选 `.slapp`。
- 输出包含 `.slapp`，但同目录缺少 `app.jl`。
- 生成或修改 `.slapp` 后，没有同步生成或同步更新同目录 `app.jl`，却声明该目录是可打开 App Designer 工程。
- 同目录 `app.jl` 是过期残留，和当前 `.slapp` 的模块名、回调、ribbon 控件、菜单状态或图标运行态表达不一致。
- 输出包含 `.slapp` 时，主 `.slapp` 仍是默认 `Home / Section / Command` 壳。
- 输出包含 `.slapp` 时，`.slapp` 中只有 `iconFile` / `sourceIcon*`，缺少正式 `iconSrc`。
- 源证据显示 control 或 item 有图标线索，但生成器只保留内部 id、CSS class、资源 key、对象句柄、sprite 坐标或其它中间字段，没有继续解析到真实图片资源并写入 `iconSrc` / `IconSrc`。
- 源 control 或 item 有图标，但目标缺少可渲染 `iconSrc` / `IconSrc`。
- `iconResolutionStatus = "unresolved"` 或 `unknown` 被汇总为通过。
- 源 item 有 checkbox / radio / toggle 语义，但目标缺少父级选择模式或 item `Checked`。
- 源 `DropDownButton` 被映射为 `splitbutton`，或源 `SplitButton` 被映射为 `dropdownbutton`，且没有调用方明确授权。
- 源 `DropDownButton` / popup 控件被降级为普通 `button`，包括因空 popup、空 children 或空 items 被降级。
- 源控件是带 checkbox / multiple 菜单项的 `DropDownButton` 或等价 popup 控件，但目标不是 `dropdownbutton`、缺少父控件图标、缺少非空菜单，或缺少 `menuSelectionMode = "multiple"`。
- 源运行时、源码或等价证据已经证明的 source column 边界被目标静默拆分或合并，且没有 `known_differences.json` / `accepted_difference` / `unknown` 说明。
- 菜单项不是来自 live snapshot，却在报告中声称由 live snapshot 直接证明。
- `displayMode = "large"` 的 command 与其它 command 共用同一个 column。
- 多 command column 不是 `layout = "stack"`，或 stack 内任一 command 不是 `displayMode = "small"`。
- `column.layout = "stack"` 中包含 `displayMode = "large"` 的 command。
- `unknown` / `unavailable` 被汇总为通过。
- 输出包含 `.slapp`，但没有通过 Syslab App Designer 打开主 `.slapp` 并执行设计器 Run 命令完成运行验收，却声明可运行通过。
- 设计器 Run 后重新生成的 `app.jl` 出现非法 `module`、裸 `undefined`、语法错误、缺失回调、缺失 `IconSrc` 或资源路径失效。

## 相关文档

- [reference/api.md](../reference/api.md)：字段与运行契约。
- [reference/components.md](../reference/components.md)：组件和构造函数。
- [reference/layout-rules.md](../reference/layout-rules.md)：布局规则。
- [source/source-generation.md](../source/source-generation.md)：源证据和生成规则。
- [source/icon-resolution.md](../source/icon-resolution.md)：源图标线索解析和图标完成门禁。
- [rules/ribbon-control-selection.md](../rules/ribbon-control-selection.md)：控件选型。
- [rules/ribbon-validation.md](../rules/ribbon-validation.md)：生成后验收。
