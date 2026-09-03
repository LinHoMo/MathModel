# 组件映射

本表来自 `app-designer/webview/src/uicomponents/*/meta.js` 与 `tyappdesigner.jl/src/uifigureBasedApps/*.jl`。

组件库面板只展示 `meta.js` 中具有 `group` 字段的组件：

```js
Object.values(uicomponents).filter((item) => item.group)
```

用户要求“创建组件”时，只能从“面板可创建组件”中选择。没有 `group` 的类型是设计器内部节点，不能作为独立面板组件生成。

## 面板可创建组件

| UI 界面名称 | 前端 type | Julia 类型 | Julia 构造函数 | 前端组件 |
|---|---|---|---|---|
| Button | `button` | `Button` | `uibutton` | `UIButton` |
| Check Box | `checkbox` | `CheckBox` | `uicheckbox` | `UICheckBox` |
| Drop Down | `dropdown` | `DropDown` | `uidropdown` | `UIDropDown` |
| Edit Field (Text) | `editfield` | `EditField` | `uieditfield` | `UIEditField` |
| Edit Field (Numeric) | `numericeditfield` | `NumericEditField` | `uinumericeditfield` | `UINumericEditField` |
| Text Area | `textarea` | `TextArea` | `uitextarea` | `UITextArea` |
| Spinner | `spinner` | `Spinner` | `uispinner` | `UISpinner` |
| Slider | `slider` | `Slider` | `uislider` | `UISlider` |
| Table | `table` | `Table` | `uitable` | `UITable` |
| Label | `label` | `Label` | `uilabel` | `UILabel` |
| Image | `image` | `Image` | `uiimage` | `UIImage` |
| HTML | `html` | `HTML` | `uihtml` | `UIHtml` |
| File Picker | `filepicker` | `FilePicker` | `uifilepicker` | `UIFilepicker` |
| Progress Bar | `progressbar` | `ProgressBar` | `uiprogressbar` | `UIProgressBar` |
| Axes | `uiaxes` | `UIAxes` | `uiaxes` | `UIAxes` |
| Radio Button Group | `radiobuttongroup` | `ButtonGroup` | `uibuttongroup` | `UIButtonGroup` |
| Toggle Button Group | `togglebuttongroup` | `ButtonGroup` | `uibuttongroup` | `UIButtonGroup` |
| Panel | `panel` | `Panel` | `uipanel` | `UIPanel` |
| Tab Group | `tabgroup` | `TabGroup` | `uitabgroup` | `UITabGroup` |
| Grid Layout | `gridlayout` | `GridLayout` | `uigridlayout` | `UIGridLayout` |
| Menu | `menu` | `Menu` | `uimenu` | `UIMenu` |

## 内部结构组件

以下类型在前端和 Julia 运行时中存在，但不显示在组件库面板。只在工程根节点或组合组件内部使用。

| 内部用途 | 前端 type | Julia 类型 | Julia 构造函数 | 使用限制 |
|---|---|---|---|---|
| App 根节点 | `figure` | `Figure` | `uifigure` | 每个 App 的根节点，不是面板组件 |
| 选择组运行时容器 | `buttongroup` | `ButtonGroup` | `uibuttongroup` | 由单选按钮组或切换按钮组使用 |
| 单选按钮组子项 | `radiobutton` | `RadioButton` | `uiradiobutton` | 仅在已有单选按钮组内创建 |
| 切换按钮组子项 | `togglebutton` | `ToggleButton` | `uitogglebutton` | 仅在已有切换按钮组内创建 |
| 选项卡组子页 | `tab` | `Tab` | `uitab` | 仅在已有选项卡组内创建 |

## 用户名称映射

- 用户说“创建单选按钮”或“创建单选选项”，默认创建 `radiobuttongroup`，不能生成独立 `radiobutton`。
- 用户说“创建切换按钮”或“创建切换选项”，默认创建 `togglebuttongroup`，不能生成独立 `togglebutton`。
- 用户说“创建选项卡”或“创建 tab”，默认创建 `tabgroup`，不能生成独立 `tab`。
- 只有用户明确说“在已有单选按钮组中增加选项”时，才创建组内 `radiobutton`。
- 只有用户明确说“在已有切换按钮组中增加选项”时，才创建组内 `togglebutton`。
- 只有用户明确说“在已有选项卡组中增加页签”时，才创建组内 `tab`。

## 组合组件

`radiobuttongroup`、`togglebuttongroup` 和 `tabgroup` 是设计器组件库里的组合组件：

- `radiobuttongroup` 使用 `ButtonGroup` 作为容器，子组件使用 `RadioButton`。
- `togglebuttongroup` 使用 `ButtonGroup` 作为容器，子组件使用 `ToggleButton`。
- `tabgroup` 使用 `TabGroup` 作为容器，子组件使用 `Tab`。
- 从组件库创建组合组件时，必须执行对应 `meta.js` 的 `createChildren`，保留默认子节点。
- 运行时构造时应先创建 `TyAppDesigner.uibuttongroup(parent)`，再向组内创建 `TyAppDesigner.uiradiobutton(group)` 或 `TyAppDesigner.uitogglebutton(group)`。
- `tabgroup` 运行时构造时应先创建 `TyAppDesigner.uitabgroup(parent)`，再向组内创建 `TyAppDesigner.uitab(group)`。

## 生成器约定

代码生成器会从前端 type 读取 `juliaMethod` 并生成：

```julia
app.ComponentName = TyAppDesigner.<juliaMethod>(app.ParentName)
```

组件字段类型生成：

```julia
ComponentName::TyAppDesigner.<JuliaType> = TyAppDesigner.create_<lowercase_juliatype>()
```

示例：

```julia
RunButton::TyAppDesigner.Button = TyAppDesigner.create_button()
Table::TyAppDesigner.Table = TyAppDesigner.create_table()
HTML::TyAppDesigner.HTML = TyAppDesigner.create_html()
```
