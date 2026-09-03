# Ribbon 控件选型规则

本文档用于区分 Ribbon 中容易混淆的下拉、输入和菜单组件。具体构造函数列表见 [reference/components.md](../reference/components.md)。

## 当前正式语义

| 源应用语义 | Syslab 控件类型 | Julia 构造函数 | 数据字段 | 回调字段 |
| --- | --- | --- | --- | --- |
| 普通命令按钮 | `button` | `uitoolstripbutton` | - | `ButtonPushedFcn` |
| `EditField` 单行输入 | `editbox` | `uitoolstripeditbox` | `Value` | `ValueChangedFcn` |
| `DropDown()` 字段选择 | `dropdown` | `uitoolstripdropdown` | `Items`、`Value` | `ValueChangedFcn` |
| `ComboBox()` 可输入选择 | `combobox` | `uitoolstripcombobox` | `Options`、`Value` | `ValueChangedFcn` |
| `DropDownButton` 动作菜单 | `dropdownbutton` | `uitoolstripdropdownbutton` | `Items` / `MenuGroups` | `CommandInvokedFcn` |
| `SplitButton` 主动作加菜单 | `splitbutton` | `uitoolstripsplitbutton` | `Items` / `MenuGroups` | `ButtonPushedFcn` + `CommandInvokedFcn` |
| MATLAB 风格 gallery | `matlab-gallery` | `uitoolstripmatlabgallery` | `Items`、`Value` | `ButtonPushedFcn` + `CommandInvokedFcn` |

## 源 class 强映射

生成器必须优先依据源控件 class / role / interaction 选型，不得只靠显示文本、图标大小、是否有下拉箭头或控件重要程度推断。

| 源 class / 语义 | Syslab 目标 | 禁止 |
| --- | --- | --- |
| MATLAB `Button` | `button` / `uitoolstripbutton` | 不得仅因有图标或是主操作改成 `splitbutton` / `dropdownbutton` |
| MATLAB `DropDownButton` | `dropdownbutton` / `uitoolstripdropdownbutton` | 不得映射为 `splitbutton` |
| MATLAB `SplitButton` | `splitbutton` / `uitoolstripsplitbutton` | 不得映射为 `dropdownbutton` |
| MATLAB `ListItemWithCheckBox` 或等价 checkbox menu item | item `Checked` + 父 `menuSelectionMode = "multiple"` | 不得降级为普通 command item |
| radio / mutually exclusive menu item | 父 `menuSelectionMode = "single"` + `menuItemMarkStyle = "radio"` | 不得只写 item `Checked` 而缺少父级选择模式 |
| MATLAB-style gallery 单选当前项 | 父控件 `value` / `Value` + `menuSelectionMode = "single"` | 不得在 item 上重复写 `checked` / `Checked` |
| checkbox / multiple / 独立 toggle 菜单项 | item `checked` / `Checked` + 对应父级选择模式 | 不得只用 `variant` 伪装选中态 |

如果源证据显示控件有下拉入口，但当前提取路径没有拿到菜单项，结果必须标记为 `unknown` 或“源菜单提取不完整”，不得自动改成普通 `button`。

### 下拉入口的强证据

出现以下任一证据时，源控件必须按下拉控件建模，不能生成普通 `button`：

- 源 class / sourceType / runtime class 是 `DropDownButton`、`SplitButton`、`PopupList`、`ListItemWithPopup` 或等价 popup/menu 控件。
- 源控件包含非空 `Popup`、`popup`、`children`、`items`、`menuGroups`、`DynamicPopupFcn` 或等价动态 popup 回调。
- 源快照记录 `hasDropdown = true`、`interaction = "menuCommand"` / `"menuCheck"` / `"menuRadio"`，或截图中可见下拉箭头。
- 源控件的子项是 `ListItemWithCheckBox`、radio item、check item 或其它可选菜单项。

多选动作菜单必须使用 `dropdownbutton`，并设置 `menuSelectionMode = "multiple"`。如果源控件是带 checkbox 菜单项的 `DropDownButton`，应生成 `uitoolstripdropdownbutton`，不能因为它在 ribbon 上看起来像一个大图标命令就生成 `uitoolstripbutton`。

## 选择原则

1. 字段区中只能选择已有值的 MATLAB `DropDown()`，映射为 `dropdown`。
2. 用户可键入任意文字并可选择建议项的 MATLAB `ComboBox()`，映射为 `combobox`。
3. 点击后展示命令项的菜单入口，映射为 `dropdownbutton` 或 `splitbutton`，不要映射成字段 `dropdown`。
4. `splitbutton` 的主体点击与菜单项选择保留不同回调语义。
5. 下拉菜单和 gallery 的 item 文字、值、命令 id 与源图标都属于运行契约，不得省略。

## 源语义保真

生成器必须优先依据源控件语义和布局上下文选型，不得只靠显示文本、文本长度、是否换行或图标尺寸推断控件类型和显示层级。

- 源控件是普通命令、可保持状态命令、字段输入、字段选择、动作菜单、主按钮加菜单、gallery item 等语义时，应分别映射到对应 Syslab 控件。
- 源菜单项如果具有可勾选、多选、单选或持久选中状态，生成结果必须保留该选择语义，但必须区分“单选当前值”和“item 自身可勾选状态”。
- 多选菜单项要求父菜单控件设置 `menuSelectionMode = "multiple"`，并按源样式选择 `menuItemMarkStyle`。
- 单选菜单项要求父菜单控件设置 `menuSelectionMode = "single"`，必要时使用 radio mark。
- 生成 `.slapp` 与 `app.jl` 时，多选、checkbox、radio 菜单项或独立 toggle item 的状态必须落到 item 的 `checked` / `Checked` 字段；单选 MATLAB-style gallery 的当前项必须落到父控件 `value` / `Value`，item `checked` / `Checked` 不得重复表达。
- 普通动作菜单项才可以使用无选择状态的 command item。
- 单控件独占命令列通常表示主命令显示层级；多个命令共享同一列时才优先映射为 `stack` 小命令。不要用“文本是否换行”作为主命令/小命令的唯一判断。

示例：

- MATLAB `ListItemWithCheckBox` 属于可勾选菜单项，应生成 checkbox item，并让父 `dropdownbutton` / `splitbutton` 使用 `menuSelectionMode = "multiple"`。
- MATLAB `ToggleGalleryItem` 如果表达单选 gallery 的当前项，应把当前 item 写入父 `matlab-gallery` 的 `Value` / `value`，并避免 item 级 `Checked` / `checked` 造成默认双高亮；只有当源证据显示它是独立可保持状态、checkbox 或 multiple 选择项时，才保留 item 级 `Checked` / `checked`。
- MATLAB 普通 `Button` 如果在源运行时独占一个 command column，应优先按主命令按钮生成；如果与其它小命令同列，则按源列结构生成小命令 stack。

## 生成代码

- 新生成代码使用对应的具体构造函数。
- `uitoolstripcontrol(...)` 是兼容和高级字段入口，不作为已知普通组件的首选写法。
- 字段区列宽与对齐规则见 [reference/layout-rules.md](../reference/layout-rules.md)。

## 审查重点

- 源应用 `DropDown()` 被错误映射为 `dropdownbutton` 或 `splitbutton`，视为字段语义错误。
- 源应用 `DropDownButton` 被错误映射为 `splitbutton`，视为源 class 映射错误。
- 源应用 `SplitButton` 被错误映射为 `dropdownbutton`，视为源 class 映射错误。
- 动作菜单被错误映射为 `dropdown`，视为菜单语义错误。
- 有 item 图标来源却只保留文字，视为图标信息丢失。
- 源菜单项有 checkbox / radio / toggle 语义，但生成结果只保留普通 command item，视为选择语义丢失。
- 源布局显示主命令独占列，但生成结果仅因单行文本而使用小按钮，视为布局语义丢失。
