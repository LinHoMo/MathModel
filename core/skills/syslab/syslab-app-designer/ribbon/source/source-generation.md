# Ribbon 生成规则

本文档约束基于源应用的 Syslab ribbon 生成行为。生成结果不仅要还原 ribbon 外观，还必须为可交互组件生成可运行的回调入口。

生成前先按 `../reference/components.md` 确认可用结构与控件类型，并按
`../reference/layout-rules.md` 确认布局约束。

## 1. 对标来源

生成 ribbon 时必须以源应用安装目录、源应用工程文件或源应用运行时中可验证的真实定义为准。

- ribbon tab、section/group、column、button、dropdown、gallery、split button 等布局必须对标源应用。
- 图标必须尽可能从源应用安装目录、源应用工程文件、源应用 CSS、源应用资源目录、运行时对象或等价证据中读取和转换，不能自行替换、猜测或使用兜底图标。
- 如果无法读取某个布局或图标，生成流程应显式失败并说明缺失来源，不能静默生成近似结果。
- 禁止使用 HTML 伪造 ribbon；必须走 Syslab App Designer 支持的正式 toolstrip/ribbon 结构。

源图标线索不是图标完成状态；只有生成可渲染 `iconSrc` / `IconSrc` 才算图标完成。图标 id、CSS class、资源 key、对象句柄、sprite 坐标或其它非文件型线索的解析流程和失败门禁统一见 [source/icon-resolution.md](icon-resolution.md)。

“不要使用兜底图标”不等于“允许空图标”；无法解析源图标时应标记失败或不完整，不能静默当作源应用没有图标。

源应用对标任务还必须遵守 [source/runtime-snapshot.md](runtime-snapshot.md)。不要把规则写死到某个源平台；源应用可以来自 MATLAB、Syslab、已有 JSON spec、截图标注、录屏解析或人工导出的控件树。无论来源是什么，都必须先形成 `source_ribbon_snapshot.json` 或等价证据包，再生成目标 ribbon。

生成器必须区分证据来源。来自 live snapshot、源码、截图、人工标注和历史 spec 的字段可信范围不同；从非 live snapshot 来源补出的菜单项、图标或状态必须记录 `evidenceSource`。

如果没有 `source_ribbon_snapshot.json` 或等价证据：

- 只能交付“结构草稿”或“待对标初版”，不得声明“与源应用对标完成”。
- 不得凭控件文本推断 `displayMode`、图标、下拉项、选中状态、换行和列布局。
- 不能因为生成结果能运行，就把视觉、布局或源语义视为通过。

## 2. 字段列宽提取规则

当源应用使用 `EditField`、字段型 `DropDown()` 或等价字段控件，并通过父列声明宽度时，该列宽属于需保留的布局证据。

- 对 MATLAB `addColumn('Width', W)` 这类字段容器声明，生成对应 Syslab `layout = "stack"` 列并写入 `width = "Wpx"`。
- 生成的 `app.jl` / `.slapp.code` 必须保留该字段列的 `Width`，使 `editbox` / `dropdown` / `combobox` 按源列宽渲染。
- 字段控件通常不重复写 `control.width`；只有源应用对单个控件另有独立宽度定义时，才保存控件自身宽度。
- 普通 command button / split button / dropdown button 列不因设计态宽度自动获得固定运行宽度。

## 2.1 源语义抽取规则

从源应用对标生成 ribbon 时，抽取结果必须保留足够信息用于后续控件选型和布局判断。不要只抽显示文本。

至少记录：

- 源控件类型标识，例如运行时 class、组件 type、role 或等价字段。
- 源交互语义：command、toggle、checkbox item、radio item、field value、split action、menu action、gallery item 等。
- 源布局上下文：父容器、同列控件数量、column / group 顺序、显式宽度、空白占位。
- 源 column 边界：`section`、`column`、`row`、`columnLayout`、`columnKind`、`commandCountInColumn`、`largeCommandCountInColumn`。
- 源显示层级证据：`displayMode`、`allowedDisplayMode`、是否独占 command column，以及该判断的 `evidenceSource`。
- 下拉与 gallery 内容：popup、children、menu item、gallery category、dynamic / lazy popup 展开结果。
- 源图标引用：图标 class、CSS class、文件名、资源路径、资源 key、内部 icon id、对象句柄、sprite sheet 坐标、background-position 或可转换的源资源标识。
- gallery item 级图标引用：每个 gallery item 自己的图标 class、CSS class、文件名、资源路径、资源 key、内部 icon id、对象句柄、sprite sheet 坐标、background-position 或可转换源资源标识。不要只记录父 gallery 控件图标。
- 源视觉字段：`displayMode`、实际文本换行、是否有图标、下拉箭头、运行时 bounds、可见项数量、hover/active 区域或可从截图判断的等价信息。
- 源证据来源：每个关键字段来自运行时控件树、源码、截图、录屏、JSON spec 还是人工标注。

源应用对标时必须抽取真实容器树，而不是只抽扁平控件列表。最低结构应能表达：

```text
tab -> section -> source column -> controls
```

每个 source column 至少记录：

- `sourceIndex` 或稳定 `sourceColumnId`
- 父 section / group
- 源 column class / sourceType / layout / width，如果可取得
- 该 column 内按顺序排列的 control id / tag / text
- `commandCountInColumn` 与 `largeCommandCountInColumn`
- 目标是否保持同一 column 边界，或是否拆分 / 合并及其理由

如果源运行时、源码或等价证据显示多个 command 同属一个 source column，目标生成不得静默拆成多个 column。确因目标平台能力限制无法表达源 column 时，必须记录为 `known_differences.json`、`accepted_difference` 或 `unknown`；不得把默认布局策略生成的结果声明为源应用布局对标完成。

## 2.2 Popup / Gallery 递归抽取规则

源应用对标抽取不得只停在第一层 `Popup`、`children`、`items` 或 category 容器。遇到容器型节点时必须继续递归到可交互叶子项，并在快照中同时保留容器分组与叶子项。

必须递归的典型节点包括：

- MATLAB `matlab.ui.internal.toolstrip.GalleryPopup`
- MATLAB `matlab.ui.internal.toolstrip.GalleryCategory`
- MATLAB `matlab.ui.internal.toolstrip.PopupList`
- MATLAB `matlab.ui.internal.toolstrip.ListItemWithPopup`
- 其它源平台等价的 popup / category / menu group / submenu 容器

MATLAB gallery 的结构通常是：

```text
Gallery
  Popup / GalleryPopup
    GalleryCategory
      ToggleGalleryItem / GalleryItem
```

生成器必须把 `GalleryCategory.Title` 映射为目标 `menuGroups[].title`，把 `GalleryCategory.Children` 中的 `ToggleGalleryItem` / `GalleryItem` 映射为真正的 gallery item。不得把 `GalleryCategory` 本身计作 gallery item，也不得因为只抽到 category 数量就认为 gallery 条目完整。

对于 MATLAB `PopupList` 与 `ListItemWithPopup`，必须递归抽取子菜单项。若直接读取 `Popup` 得到 `double`、空对象、空 `Children` 或无法索引，只能说明当前读取路径没有拿到动态 popup 内容，必须继续尝试：

- 触发动态 popup 回调后读取运行时对象。
- 查找创建 popup 的源码，例如 `PopupList()`、`ListItemWithCheckBox()`、`GalleryCategory()`。
- 递归读取 `Children`、`Popup.Children` 或源平台等价字段。
- 若仍无法取得，标记 `unknown` / `incomplete`，并在差异报告中说明。

源快照必须记录 `recursiveExtractionStatus`。至少包含：

- `status`: `pass|fail|unknown|unavailable`
- 每个 popup / gallery / submenu 容器是否已递归展开
- 每个 category / menu group 的标题、顺序和叶子项数量
- 未能展开的容器、尝试过的读取路径和失败原因

如果 `recursiveExtractionStatus.status` 不是 `pass`，不得声明源 ribbon 内容完整对标。

如果来源是 MATLAB，可以把 `matlab.ui.internal.toolstrip.*` class 作为源控件类型证据；如果来源是其它应用，应记录其等价类型标识。生成器必须基于这些字段做语义映射，不得丢弃源类型后再用文本启发式重猜。

`displayMode`、`controlType`、`interaction`、`textLines`、`hasIcon`、`checked`、`section`、`column`、`row` 等字段一旦在源快照中存在，生成器必须直接使用。只有字段缺失时，才允许标记为 `unknown` 并进入人工复核；不得自行用“看起来更合理”的布局替换。

如果缺少 column 边界、同列 command 数量或 displayMode 证据，不得根据文本、图标大小、按钮重要程度、File / Session / Export 等业务分组或固定模板推断多个 command 可以共享普通 column。此时应将对应 column 标为 `unknown`，或按明确的安全规则生成 `stack + small` 并在验收报告中说明证据不足；不得声明源应用布局完全对标。

源菜单项如果是可勾选或单选项，必须将选择语义提升到父菜单控件：

- 多选项：父控件设置 `menuSelectionMode = "multiple"`。
- 单选项：父控件设置 `menuSelectionMode = "single"`。
- item 本身保留 `checked` / `value` / `commandId`。

例如 MATLAB `ListItemWithCheckBox` 应作为 checkbox item 处理，而不是普通 command item。

`Popup = double`、空 `Popup`、空 `children`、空 `items` 或空 `menuGroups` 只能表示当前提取路径没有拿到菜单项，不能证明源菜单为空。遇到这种情况时，应继续从源码、动态 popup 回调、运行时交互、配置、截图或人工标注中补证据；无法补证据时必须标记为 `unknown` 或“源菜单提取不完整”，不得自动降级为普通 `button` 或声明 live snapshot 已证明菜单为空。

源控件 class / sourceType / runtime class 已经是 `DropDownButton`、`SplitButton`、`ListItemWithPopup` 或等价下拉入口时，即使第一轮 `Popup`、`children`、`items`、`menuGroups` 为空，也必须保留下拉控件语义并继续抽取菜单。不得把空 popup 当作普通按钮证据。

源类型为 `DropDownButton` 且菜单项具有 checkbox / multiple 语义时，应作为高风险源控件处理：目标必须是 `dropdownbutton`，必须有可渲染父控件图标，且菜单项应保留 checkbox / multiple 语义。若菜单项或图标未抽取到，状态必须为 `unknown` / `incomplete` / `fail`，不得生成普通 `button` 后声明通过。

源应用 gallery 如果有首选可见项数量，抽取结果还应记录或计算 `itemWidth`、`frameWidth`、所在 column 宽度和必要的 section 宽度；只保留 `visibleCount` 不足以保证运行时布局对齐。

源应用 gallery item 如果显示图标，生成器必须逐项解析这些 item 图标资源，并在对应 item 上写入可渲染的 `iconSrc` / `IconSrc`。父 gallery 控件的图标只能作为父控件图标，不能作为 item 图标抽取完成的证据。

抽取到源应用内部图标标识、CSS class、资源 key、对象句柄、sprite sheet 坐标或其它非文件型图标线索时，必须转入 [source/icon-resolution.md](icon-resolution.md)。该文档是图标解析流程、状态分类和失败门禁的唯一详细规则源。

证据字段如 `sourceIconId`、`sourceIconClass`、`sourceIconPath` 可以保留在中间 spec、审计日志或 `commandDescriptor` 中，但不得写入 `TyAppDesigner.ToolstripItem(...)` 不支持的构造参数。最终 `app.jl` 中的 `ToolstripItem` 图标应使用 `IconSrc`，并指向真实存在的资源文件或可直接渲染的图片数据。

## 3. 回调生成原则

所有可交互 ribbon 组件必须配置回调字段，确保用户点击后能够进入 Julia 业务函数。

可交互组件包括：

- button
- toggle button
- checkbox / radio
- dropdown / combobox / editbox
- split button 主按钮和菜单项
- dropdown button 菜单项
- gallery item / gallery popup item
- 其他具有点击、选择、输入或值变化语义的 toolstrip control

非交互结构不生成回调：

- toolstrip
- tab
- section / group
- column
- separator
- label
- spacer
- 纯布局容器

## 4. 回调字段映射

根据组件交互类型选择回调字段。

- 普通点击组件使用 `buttonPushedFcn`
- 值变化组件使用 `valueChangedFcn`
- 命令型或菜单型组件使用 `commandInvokedFcn`，如果当前组件实现只支持按钮回调，则使用其可运行的等价回调字段
- split button / dropdown button 的菜单项必须能把被点击的菜单项信息传入事件对象
- gallery item 必须能把被选中的条目信息传入事件对象

生成器不得只写空字符串回调字段。只要组件可交互，就必须绑定到一个 Julia 回调函数。

如果输出目标是 `.slapp` / 设计器生成 app，控件回调名还必须存在于 `.slapp.callbackFunctions` 中；只在生成后的 `app.jl` 中补函数，下一次设计器点击“运行”时会被重新生成结果覆盖。

`.slapp.callbackFunctions[].code` 只能写回调函数体，不能写完整的 `function <name>(app, event) ... end`。App Designer 会用 `callbackFunctions[].name` 生成外层函数签名，并把 `code` 插入函数体内部。生成器不得把外部 `app.jl` 中的完整函数原样复制进 `.slapp.callbackFunctions[].code`。

最小工程结构示例：

```json
{
  "callbackFunctions": [
    {
      "name": "RibbonFeedback",
      "code": "item = event.Item\n# read commandId/value/lastMenuItem here"
    }
  ],
  "figure": {
    "toolstrip": {
      "tabs": []
    }
  }
}
```

任何 control 写入非空 `buttonPushedFcn`、`valueChangedFcn` 或 `commandInvokedFcn` 时，必须能够在 `callbackFunctions[].name` 中找到同名函数定义。

## 5. 默认占位回调

当真实业务尚未实现时，必须生成显式占位回调，不能让按钮静默无响应。

默认可以统一绑定到：

```julia
RibbonFeedback(app, event)
```

该函数至少需要识别并展示：

- ribbon 分组名
- 组件名
- 组件值，如果该组件有值
- 菜单项或 gallery item 的标签/值，如果触发源是子项

占位弹窗格式：

```text
分组名 + 组件名
```

值变化、下拉、菜单项或 gallery item 的弹窗格式：

```text
分组名 + 组件名 + 值
```

如果某个源应用功能暂时无法在 Syslab 中实现，占位回调必须明确提示：

```text
暂未实现：分组名 + 组件名
```

## 6. 真实业务函数

Syslab 插件负责把 ribbon 交互事件送回 Julia；具体业务必须在生成的 `app.jl` 中实现。

如果源应用中的某个按钮具有明确业务功能，在 Syslab 生成结果中不能只保留按钮外观。生成器必须为它生成回调入口，并在可实现时调用 Syslab 对应能力。

业务映射示例：

- Open File / Open：打开文件选择界面并加载目标文件
- Save / Save As：保存当前 App 数据或导出文件
- Export：导出到工作区、脚本或指定格式
- 对象类型切换：更新 App 内部业务模型
- 组件类型切换：更新当前选中对象或配置
- Analysis / Result：调用对应计算、分析或绘图逻辑
- Settings / Parameters：打开参数配置界面
- Layout / View：切换或恢复界面布局

如果真实业务暂未具备实现条件，仍然必须保留可运行的占位回调，并在后续实现时替换为真实业务逻辑。

## 7. 事件数据要求

回调事件对象必须包含足够信息，使 `app.jl` 能够分发业务。对于 `.slapp` / 设计器生成 app，控件载荷位于 `event.Item`；生成的回调不得假设 `CommandId`、`Value` 或 `LastMenuItem` 直接位于 `event` 顶层。

建议至少包含：

- `event.Item.CommandId` / `event.Item.commandId`：推荐格式为 `分组名|组件名`
- `event.Item.Text` / `event.Item.text` 或 `Label` / `label`：组件显示名称
- `event.Item.ControlType` / `event.Item.controlType`：组件类型
- `event.Item.Value` / `event.Item.value`：当前值
- `event.Item.LastMenuItem` / `event.Item.lastMenuItem`：菜单或 gallery 子项触发时的实际子项
- `event.Item.Tag` / `event.Item.tag` 或 `Id` / `id`：稳定组件标识

事件字段中不能保留协议不支持的 `null` 值。传入 Julia 前应删除空字段，或转换为协议支持的缺省值。

## 8. 验收标准

生成结果必须满足以下条件：

- ribbon 布局与源应用对齐
- 图标来自源应用安装目录或资源目录
- 可交互组件全部有回调字段
- 点击任意可交互按钮都有可见反馈或真实业务行为
- 下拉、菜单项、gallery item 能返回具体选择值
- 无法实现的业务显示明确的“暂未实现”提示
- 不允许出现点击无响应的可交互 ribbon 组件
- 源应用已声明字段列宽时，设计态 spec 与生成后的运行代码均保留对应字段列宽
- 生成后必须取得目标运行截图或 `target_ribbon_snapshot.json`，并与源快照生成 `visual_audit_report.json`
- 视觉审计必须至少覆盖大/小按钮、图标渲染、文本换行、文本重叠、下拉箭头、section/column 顺序、checked/radio/toggle 状态
- `py_compile`、Julia `include`、`.slapp.code == app.jl` 只能证明运行性，不能替代源应用视觉对标验收

如果目标组件无法完全复现源应用视觉或交互，必须生成 `known_differences.json` 并说明差异来源；不得静默降级或宣称完全一致。

如果目标平台当前无法表达源菜单层级，例如源菜单中存在子菜单而目标结果只能扁平化为 `items` / `menuGroups`，该扁平化必须写入 `known_differences.json` 或 `visual_audit_report.json`，并标为 `accepted_difference` 或 `unknown`；不得声明结构或视觉完全对标。
