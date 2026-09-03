# Ribbon 组件参考

本文档说明 Ribbon 中可以创建哪些实际组件，以及新生成代码应使用哪个 Julia 构造函数。

本文件列出的结构和控件是新生成 Ribbon 可使用的公开组件范围。

## 结构组件

| 函数 | 对应内容 | 用途 |
| --- | --- | --- |
| `uitoolstrip(...)` | 整条 Ribbon | 创建 ribbon 根容器 |
| `uitoolstriptab(...)` | 标签页 | 例如 `Home`、`Design` |
| `uitoolstripsection(...)` | 带标题的分组 | 例如 `File`、`Design Frequency` |
| `uitoolstripcolumn(...)` | 分组中的列 | 安排一列或一块控件 |

## 控件组件

| 函数 | 实际组件 | 常用数据 | 常用回调 |
| --- | --- | --- | --- |
| `uitoolstripbutton(...)` | 普通按钮 | `Text`、`IconSrc` | `ButtonPushedFcn` |
| `uitoolstriptoggle(...)` | 可保持选中状态的按钮 | `Value` | `ValueChangedFcn` |
| `uitoolstriplabel(...)` | 文字标签 | `Text` | 无 |
| `uitoolstripspacer(...)` | 留白占位 | 无 | 无 |
| `uitoolstripeditbox(...)` | 单行输入框 | `Value`、`Placeholder` | `ValueChangedFcn` |
| `uitoolstripdropdown(...)` | 不可编辑的值选择下拉框 | `Items`、`Value` | `ValueChangedFcn` |
| `uitoolstripcombobox(...)` | 可输入并可选择的下拉输入框 | `Options`、`Value` | `ValueChangedFcn` |
| `uitoolstripcheckbox(...)` | 复选框 | `Text`、`Value` | `ValueChangedFcn` |
| `uitoolstripradio(...)` | 单选项 | `Text`、`GroupName`、`Value` | `ValueChangedFcn` |
| `uitoolstripdropdownbutton(...)` | 仅展开动作菜单的按钮 | `Items` / `MenuGroups` | `CommandInvokedFcn` |
| `uitoolstripsplitbutton(...)` | 主按钮加下拉菜单 | `Items` / `MenuGroups` | `ButtonPushedFcn` + `CommandInvokedFcn` |
| `uitoolstripgallery(...)` | 普通 gallery | `Items` | `CommandInvokedFcn` |
| `uitoolstripmatlabgallery(...)` | MATLAB 风格 gallery | `Items`、`Value`、`VisibleCount`、`ItemWidth`、`FrameWidth` | `ButtonPushedFcn` + `CommandInvokedFcn` |

`uitoolstripmatlabgallery` 的父控件 `IconSrc` 只表示 gallery 控件本身的图标。源应用对标场景中，gallery item 的最终图标字段必须是 item 级 `IconSrc` / `iconSrc`，并且应是 Syslab 前端可直接渲染的图片资源。`IconLabel` 是文本兜底，不是源应用内部图标解析字段；`IconKind` 只适用于 Syslab 前端已知的内置图标类别，不适用于任意源应用内部 icon id。不要用父 gallery 图标代替 item 图标。

`uitoolstripmatlabgallery` 作为 MATLAB-style 单选 gallery 使用时，当前/默认项写在父控件 `Value` / `.slapp` 的 `value` 上。`Items` 与 `MenuGroups` 中的 item 不要写 `Checked` / `checked` 来重复表达当前项，否则前端会同时保留默认项高亮和用户点击项高亮。只有源证据显示 item 本身是 checkbox、multiple 或独立 toggle 状态时，才使用 item 级 `Checked` / `checked`。

## 图标字段分层

- 来源 / 审计字段：`sourceIconId`、`sourceIconClass`、`sourceIconPath`、`iconFile`。
- `.slapp.figure.toolstrip` 设计态渲染字段：`iconSrc`。
- `app.jl` / Julia 构造器运行态渲染字段：`IconSrc`。

审计字段不能替代渲染字段。只要源图标已经解析成功，最终 control、menu item 和 gallery item 必须写入正式渲染字段。父控件 `IconSrc` / `iconSrc` 不能替代 item 级图标。

## 下拉控件区别

- `dropdown`：选择一个值，对标字段区中的 MATLAB `DropDown()`。
- `combobox`：既能输入也能选择，对标 MATLAB `ComboBox()`。
- `dropdownbutton`：展开动作菜单，不代表一个字段值。
- `splitbutton`：按钮主体可执行动作，同时带动作菜单。

## 通用底层入口

`uitoolstripcontrol(parent; ...)` 仍然保留，用于兼容旧代码、处理未覆盖的控件类型或必须直接设置高级协议字段的场景。

新生成代码不要优先使用它。已知组件应调用上表中的具体构造函数，使代码直接表达实际组件语义。

## 回调读取

- 普通按钮读取控件本身信息。
- 输入框、值选择下拉框读取控件值。
- 动作菜单与 gallery 读取被选择的 item 信息。
- 设计器生成 app 时，控件状态和交互信息从 `event.Item` 获取。

具体布局规则见 [reference/layout-rules.md](layout-rules.md)，源应用生成要求见 [source/source-generation.md](../source/source-generation.md)。
