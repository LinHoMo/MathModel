# 普通组件布局

App Designer 普通组件使用父子组件树管理布局。构造函数会从 parent 生成 `Parent` 路径，并把新组件 `Id` 加入 parent 的 `Children`。

## 父子关系

常见父子结构：

```text
Figure
  Panel
    Button / Label / Table / ...
  GridLayout
    Button / Label / Panel / ...
  TabGroup
    Tab
      GridLayout / Panel / Button / ...
```

创建子组件时把容器对象作为 parent：

```julia
app.UIFigure = TyAppDesigner.uifigure(Visible=false)
app.Panel = TyAppDesigner.uipanel(app.UIFigure)
app.RunButton = TyAppDesigner.uibutton(app.Panel)
```

不要手写：

```julia
app.RunButton.Parent = ...
push!(app.Panel.Children, ...)
```

## Position 布局

`Position` 使用 `[x, y, width, height]`：

```julia
app.RunButton.Position = [40, 40, 120, 30]
```

适合直接放在 `Figure`、`Panel`、`Tab` 等自由定位容器内的组件。

运行态 `Tab` 通常不写 `Position`；它由 `TabGroup` 管理显示区域。注意这只适用于生成后的 Julia 代码，不适用于 `.slapp` 设计态对象。

## GridLayout 布局

`GridLayout` 使用行列配置：

```julia
app.Grid = TyAppDesigner.uigridlayout(app.UIFigure)
app.Grid.ColumnWidth = ["1x", "2x"]
app.Grid.RowHeight = [32, "1x"]
```

放入 grid 的子组件使用 `LayoutRow` 和 `LayoutCol`：

```julia
app.Label = TyAppDesigner.uilabel(app.Grid)
app.Label.LayoutRow = [1]
app.Label.LayoutCol = [1]

app.Table = TyAppDesigner.uitable(app.Grid)
app.Table.LayoutRow = [2]
app.Table.LayoutCol = [1, 2]
```

规则：

- `ColumnWidth` 和 `RowHeight` 可包含数字、`"fit"`、`"1x"` 等设计器约定值。
- `LayoutRow` / `LayoutCol` 用向量表示范围；单格也写成 `[1]`。
- 在 grid 子组件上优先使用 `LayoutRow` / `LayoutCol`，不要依赖绝对 `Position`。
- 生成 `.slapp` 工程时，GridLayout 子组件布局必须三处同步：顶层 `layoutRow/layoutCol`、`state.layoutRow/state.layoutCol`、以及 `.slapp.code` / `app.jl` 中的 `LayoutRow/LayoutCol`。推荐单格范围统一写成 `[n, n]`。缺任意一处即判失败；运行后若任一 grid 子组件的 `LayoutRow` 或 `LayoutCol` 为 `missing`，说明布局生成失败，组件会覆盖或挤在一起。
- grid 自身仍可用 `Position` 放在父容器中，或作为另一个 grid 的子组件使用 `LayoutRow` / `LayoutCol`。

## Panel

`Panel` 是普通分组容器。适合需要标题、边框、滚动或局部自由定位时使用：

```julia
app.SettingsPanel = TyAppDesigner.uipanel(app.UIFigure)
app.SettingsPanel.Title = "Settings"
app.SettingsPanel.Position = [20, 20, 260, 200]
```

子组件以 panel 为 parent 创建。

## TabGroup 和 Tab

组件库面板只提供 `TabGroup`。`Tab` 是其内部子页，不能作为独立面板组件创建。拖入 `TabGroup` 时先按 `createChildren` 创建默认页签；只有用户明确要求增加、删除或修改页签时，才调整内部 `Tab`。

任务语义也可以授权调整默认页签，例如用户要求 Input/Output 两个页签。此时允许替换默认三个页签，但必须同步维护：

- `TabGroup.children` 中的实际页签集合。
- 每个 Tab 的 `pid`、`variableName`、`title` 和 `value`。
- 恰好一个默认选中页签。
- Julia 字段声明、构造顺序和父子关系。

`.slapp` 设计态 Tab 硬规则：

- 每个 `tab` 节点必须包含 `position: [0,0,0,0]`，即使运行态代码通常不设置 Tab `Position`。
- 每个 `tab` 节点必须包含 `children`、`pid`、`title`、`value`、`position`、`state`、`visible`、`type` 和 `variableName`。
- 同一个 `TabGroup.children` 中必须恰好一个 tab 的 `value` 为 `true`，其余为 `false`；`state.value` 应同步表达同一选中状态。
- Tab 内容组件必须以具体 tab 为直接父节点，`pid` 必须等于该 tab 的 `id`；不要把 tab 内组件挂到 `TabGroup` 或 `Figure`。

先创建 `TabGroup`，再创建 `Tab`：

```julia
app.TabGroup = TyAppDesigner.uitabgroup(app.UIFigure)
app.TabGroup.Position = [20, 20, 500, 360]

app.InputTab = TyAppDesigner.uitab(app.TabGroup)
app.InputTab.Title = "Input"

app.OutputTab = TyAppDesigner.uitab(app.TabGroup)
app.OutputTab.Title = "Output"
```

tab 内容组件以具体 tab 为 parent：

```julia
app.RunButton = TyAppDesigner.uibutton(app.InputTab)
```

## ButtonGroup

组件库面板不提供独立 `ButtonGroup`、`RadioButton` 或 `ToggleButton`。面板提供的是 `Radio Button Group` 和 `Toggle Button Group`；创建时必须带上 `createChildren` 定义的默认子按钮。以下运行时代码仅用于实现组合组件或向已有组内增加选项。

`ButtonGroup` 是选择类按钮容器：

```julia
app.ModeGroup = TyAppDesigner.uibuttongroup(app.UIFigure)
app.ModeGroup.SelectionChangedFcn = "ModeGroupSelectionChanged"

app.AutoRadio = TyAppDesigner.uiradiobutton(app.ModeGroup)
app.AutoRadio.Text = "Auto"
app.AutoRadio.Value = true

app.ManualRadio = TyAppDesigner.uiradiobutton(app.ModeGroup)
app.ManualRadio.Text = "Manual"
```

对于 `RadioButton` 或 `ToggleButton`，组内选择状态由运行时维护；业务逻辑放在组的 `SelectionChangedFcn`。

## 生成顺序

始终先创建父组件，再创建子组件。推荐顺序：

1. `UIFigure`
2. 顶层容器：`GridLayout`、`Panel`、`TabGroup`
3. 容器子层：`Tab`、嵌套 `Panel`、嵌套 `GridLayout`
4. 叶子组件：`Button`、`Label`、`Table`、`HTML` 等
5. 最后设置 `app.UIFigure.Visible = true`
