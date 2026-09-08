# 普通组件属性

本文件列出普通组件构造函数的关键参数、常用属性和运行时约束。所有运行时属性更新最终走 `app/uifigureBasedApps` JSON-RPC 通道。

## 通用字段

多数有界面位置的组件支持：

- `Visible=true`
- `Enable=true`，部分组件不支持
- `Tooltip=""`
- `ContextMenu=[]`
- `Position=[]`，语义为 `[x, y, width, height]`
- `Interruptible=false`
- `BusyAction="queue"`
- `LayoutRow=missing`
- `LayoutCol=missing`
- `Tag=""`

不要修改 `Id`、`Type`、`Parent`。这些字段由构造函数和运行时协议维护。

## 组件构造参数速查

### Figure

`TyAppDesigner.uifigure(; Name="", Position=[], Color=[0.94,0.94,0.94], LayoutRow=missing, LayoutCol=missing, Tag="", Visible=true)`

根组件。创建普通组件时把 `app.UIFigure` 或容器组件作为 parent。

### Button

`TyAppDesigner.uibutton(parent; Text="Button", WordWrap=true, HorizontalAlignment="center", VerticalAlignment="center", Icon="", IconAlignment="left", FontName="Helvetica", FontSize=12, FontColor=[0,0,0], BackgroundColor=[0.94,0.94,0.94], ButtonPushedFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

用于命令按钮。点击回调用 `ButtonPushedFcn`。

### ToggleButton

内部结构组件。不能作为组件库面板组件独立创建；仅在已有切换按钮组内增加选项时使用。

`TyAppDesigner.uitogglebutton(parent; Text="Toggle Button", Value=false, WordWrap=true, HorizontalAlignment="center", VerticalAlignment="center", Icon="", IconAlignment="left", FontName="Helvetica", FontSize=12, FontColor=[0,0,0], BackgroundColor=[0.94,0.94,0.94], Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

用于保持按下状态的按钮。当前构造函数没有独立回调参数；通常放入 `ButtonGroup` 后由组的 `SelectionChangedFcn` 处理选择变化。

### CheckBox

`TyAppDesigner.uicheckbox(parent; Value=false, Text="Check Box", WordWrap=false, FontName="Helvetica", FontSize=12, FontColor=[0,0,0], ValueChangedFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

`Value` 必须是 `Bool`。

### RadioButton

内部结构组件。不能作为组件库面板组件独立创建；仅在已有单选按钮组内增加选项时使用。

`TyAppDesigner.uiradiobutton(parent; Text="Radio Button", Value=false, WordWrap=true, FontName="Helvetica", FontSize=12, FontColor=[0,0,0], Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

通常放在 `ButtonGroup` 内。组内单选逻辑由运行时在同类型子组件间维护。

### ButtonGroup

内部运行时容器。不能作为组件库面板组件独立创建；对外应创建 `Radio Button Group` 或 `Toggle Button Group`。

`TyAppDesigner.uibuttongroup(parent; Title="Button Group", TitlePosition="left", ForegroundColor=[0,0,0], BackgroundColor=[0.94,0.94,0.94], BorderType="solid", BorderWidth=1, BorderColor=[0.49,0.49,0.49], Value="", SelectionChangedFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

容纳 `RadioButton` 或 `ToggleButton`，选择变化用 `SelectionChangedFcn`。

### DropDown

`TyAppDesigner.uidropdown(parent; Label="Drop Down", Value="Option 1", Items=["Option 1","Option 2","Option 3","Option 4"], ItemsData=[], Placeholder="", HorizontalAlignment="left", BackgroundColor=[1,1,1], ValueChangedFcn="", DropDownOpeningFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

`Value` 应和 `Items` 或 `ItemsData` 的业务语义一致。

### EditField

`TyAppDesigner.uieditfield(parent; Label="Edit Field", Value="", CharacterLimits=100, InputType="", Placeholder="", WordWrap=true, HorizontalAlignment="left", Editable=true, ValueChangedFcn="", ValueChangingFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

文本输入。提交后用 `ValueChangedFcn`，输入中变化用 `ValueChangingFcn`。

### NumericEditField

`TyAppDesigner.uinumericeditfield(parent; Label="Edit Field", Value=0, Limits=[], Placeholder="", HorizontalAlignment="right", WordWrap=true, Editable=true, ValueChangedFcn="", ValueChangingFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

数值输入。`Limits=[]` 表示当前构造默认不限制；若提供，使用 `[min, max]`。

### TextArea

`TyAppDesigner.uitextarea(parent; Label="Text Area", Value="", Placeholder="", HorizontalAlignment="left", WordWrap=true, Editable=true, ValueChangedFcn="", ValueChangingFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

多行文本。`Value` 可为字符串或字符串数组风格内容。

### Spinner

`TyAppDesigner.uispinner(parent; Label="Spinner", Value=0, Limits=[-Inf, Inf], Step=1, Placeholder="", HorizontalAlignment="right", ValueChangedFcn="", Editable=true, Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

运行时把 `Value` 和 `Limits` 转成字符串传输，用于兼容 `Inf`。读取 `spinner.Value` 和 `spinner.Limits` 时会尝试解析为数值。

约束：

- `Step` 必须是有限正数。
- `Value` 必须在 `Limits` 范围内。
- `Limits` 必须是长度为 2 的非递减实数向量，可用 `-Inf` / `Inf`。

### Slider

`TyAppDesigner.uislider(parent; Label="Slider", Value=0, Limits=[0,100], MajorTicks=[0,20,40,60,80,100], MajorTickLabels=["0","20","40","60","80","100"], MinorTicks=[...], MajorTicksMode="auto", MajorTickLabelsMode="auto", MinorTicksMode="auto", ValueChangedFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Visible=true, Enable=true, Tag="")`

约束：

- `Limits` 必须是长度为 2 的有限递增实数向量。
- `Value` 必须在 `Limits` 内。
- 设置 `MajorTicks`、`MajorTickLabels`、`MinorTicks` 会把对应 mode 改为 `manual`。

### Table

`TyAppDesigner.uitable(parent; Data=[], Selection=[], RowName=[], ColumnName=["Column1","Column2","Column3","Column4"], ColumnWidth="auto", ColumnEditable=[], ColumnSortable=[], ColumnFormat=[], Editable=true, CellEditCallback="", DisplayDataChangedFcn="", SelectionChangedFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

约束：

- `Data` 必须是矩阵；给向量时运行时会 reshape 成单列。
- 当前 `.slapp` 设计态 Table 字段使用大写 `Data` 和 `Selection`，不是 `data`、`selection`。
- Table 设计态默认字段必须按前端 meta 对象保留，至少包括：`Data=""`、`Selection=[]`、`columnName=["Column1","Column2","Column3","Column4"]`、`columnWidth="auto"`、`columnEditable=[]`、`columnSortable=[]`、`rowName=[]`、`columnFormat=[]`、`horizontalAlignment="left"`、`wordWrap=true`、`fontName="Helvetica"`、`fontSize=12`、`fontWeight="normal"`、`fontAngle="normal"`、`fontColor=[0,0,0]`、`backgroundColor=[1,1,1]`、`visible=true`、`enable=true`、`tooltip=""`、`contextMenu=[]`、`position=[0,0,304,185]`。
- `.slapp` 顶层 `Data` 和 `state.Data` 如需保存设计态数据，必须保持二维 JSON 数组结构；不要写扁平数组或未加引号文本。
- 生成 Julia 代码时，二维数据必须保持矩阵结构，字符串单元格必须带引号。例如：`Any["Alpha" 1; "Beta" 2]`。
- 禁止生成 `[Alpha,1,Beta,2]`、`[Result,Ready]` 或其他被扁平化且文本未加引号的形式；它们会把文本当作未定义变量。
- 复杂或异构表格数据不要直接塞进设计态 `Data`；优先在组件创建后赋值。构造阶段创建空表并设置 `ColumnName`、`ColumnEditable` 等轻量属性，在 `StartupFcn` 中写 `app.Table.Data = Any[...]` 或字符串矩阵。这样避免设计态 JSON 到 Julia 构造参数转换时丢引号、扁平化或生成无效字面量。
- `Enable` 可接受 `true/false` 或字符串 `"on"|"off"|"inactive"`。
- 表格编辑回调用 `CellEditCallback` 或 `DisplayDataChangedFcn`，选择变化用 `SelectionChangedFcn`。

### Label

`TyAppDesigner.uilabel(parent; Text="Label", HorizontalAlignment="center", VerticalAlignment="center", WordWrap=false, FontName="Helvetica", FontSize=12, FontColor=[0,0,0], BackgroundColor=[], Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

静态文本，不提供普通交互回调。

### Image

`TyAppDesigner.uiimage(parent; ImageSource="", HorizontalAlignment="center", VerticalAlignment="center", BackgroundColor=[], Url="", AltText="", ImageClickedFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

显示图片。点击回调用 `ImageClickedFcn`。

### HTML

`TyAppDesigner.uihtml(parent; HTMLSource="", HTMLSourceType="inline", ResourceBasePath="", Data=missing, DataChangedFcn="", HTMLEventReceivedFcn="", HtmlEventReceivedFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

`.slapp` 中 HTML 使用小写 `data` 字段。设置结构化 Data 时，设计态顶层 `data` 可保存 JSON 对象或数组；Julia 运行代码优先在 `uihtml` 创建完成后赋值，通常放在 `StartupFcn` 中写 `app.HTML.Data = Dict(...)` 或数组。字符串必须带引号并正确转义；禁止生成 `[object Object]`，也不要把结构化对象直接拼进 HTML 字符串。

`[object Object]` 要按出现位置区分根因：如果出现在 HTML 页面内部，是页面脚本把 `htmlComponent.Data` 对象直接写入 `textContent/innerText`，页面应使用 `JSON.stringify(value, null, 2)` 或自定义渲染；如果出现在属性面板，是前端把对象型 `data` 放进 `customTextarea` 导致对象被字符串化；如果出现在生成的 `app.jl`，通常是对象型 `state.data` 经过通用格式化生成了无效 Julia 代码，应避免把结构化 HTML Data 放入 `state.data` 并改用 `StartupFcn` 赋值。

如果任务语义是“Syslab 设置 Data 后 HTML 显示数据”，优先让设计态 `data` 保持设计器默认空字符串 `""`，只在 `StartupFcn` 或业务回调中设置 `app.HTML.Data`。不要把 Julia `nothing` 序列化成 JSON `null` 作为普通设计态 Data，也不要把结构化对象放进设计态 `data`。这样右侧属性面板不会显示 `null` 或 `[object Object]`，同时运行态仍能通过 `DataChanged` 把结构化数据送到页面。

详细通信规则见 [html.md](html.md)。

### FilePicker

`TyAppDesigner.uifilepicker(parent; Label="File Picker", Value="", ValueChangedFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

用于选择文件路径。路径变化用 `ValueChangedFcn`。

### Menu

`TyAppDesigner.uimenu(parent; Text="Menu", HorizontalAlignment="center", VerticalAlignment="center", WordWrap=false, MenuSelectedFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

可作为菜单项树。选择回调用 `MenuSelectedFcn`。

### Panel

`TyAppDesigner.uipanel(parent; Title="Panel", TitlePosition="left", BackgroundColor=[0.94,0.94,0.94], BorderType="solid", BorderWidth=1, BorderColor=[0,0,0], Scrollable=false, Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

容器组件。子组件应以 panel 为 parent 创建。

### TabGroup

`TyAppDesigner.uitabgroup(parent; TabLocation="top", SelectionChangedFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

容器组件。子组件通常是 `Tab`。普通拖拽创建时按 `createChildren` 生成默认页签；任务明确要求其他页签结构时允许调整，但调整后的父子关系、选中状态和运行代码必须同步。

### Tab

内部结构组件。不能作为组件库面板组件独立创建；仅在已有选项卡组内增加页签时使用。

`TyAppDesigner.uitab(parent; Value=false, Title="Tab", ForegroundColor=[0,0,0], BackgroundColor=[0.94,0.94,0.94], Scrollable=false, Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

通常以 `TabGroup` 为 parent。设计器生成普通 tab 时一般不写 `Position`。

### GridLayout

`TyAppDesigner.uigridlayout(parent; ColumnWidth=["1x","1x"], RowHeight=["1x","1x"], RowSpacing=10, ColumnSpacing=10, Padding=[10.0,10.0,10.0,10.0], Position=[], LayoutRow=missing, LayoutCol=missing, Visible=true, Tag="")`

容器组件。子组件放入 grid 时设置子组件 `LayoutRow` 和 `LayoutCol`。

### UIAxes

`TyAppDesigner.uiaxes(parent; Title="Title", XLabel="", YLabel="", Legend=false, Grid=false, Hold=false, XLim=[0,1], XLimMode="auto", YLim=[0,1], YLimMode="auto", DownSampling=true, SamplingMethod="grid", SamplingSize=50000, Data=Trace[], ButtonDownFcn="", Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

用于绘图显示。绘图辅助函数如 `plot`、`grid`、`hold` 等由 `TyAppDesigner` 提供。

### ProgressBar

`TyAppDesigner.uiprogressbar(parent; Value=0, Message="", ShowMessage=false, ShowPercentage=true, Indeterminate=false, ProgressColor=[0.02,0.69,0.15], TrackColor=[0.9,0.9,0.9], Visible=true, Position=[], LayoutRow=missing, LayoutCol=missing, Tag="")`

详细用法见 [progressbar.md](progressbar.md)。`Value` 必须是 `0..1`。拖拽默认 `ShowMessage=false`；只有任务明确要求显示说明文字时才改为 `true`，仅更新 `Message` 不构成修改 `ShowMessage` 的理由。

## 属性赋值规则

普通属性可直接赋值：

```julia
app.Button.Text = "Run"
app.DropDown.Items = ["A", "B"]
app.DropDown.Value = "A"
```

运行时会校验部分字段：

- `HorizontalAlignment` 只允许 `"left"|"center"|"right"`。
- `VerticalAlignment` 只允许 `"top"|"center"|"bottom"`。
- 多数组件的 `Enable` 字符串只允许 `"on"|"off"`；`Table.Enable` 还允许 `"inactive"`。
- `Id`、`Type`、`Parent` 不支持修改。
