# 设计器面板等价规则

普通组件 skill 的默认创建语义是：用户说“创建一个 `<组件>`”，就等同于用户从 App Designer 左侧组件库拖入该组件。生成结果必须具有相同的设计态对象、默认属性和运行时效果，不需要用户额外说明“使用默认属性”或“和面板拖出来一样”。

组件库拖拽结果是创建基线。AI 可以应用用户明确要求的修改，也可以应用完成任务目标不可缺少的修改；例如“HTML Data 通信”需要设置 HTMLSource、Data 和回调，“Input/Output 选项卡”需要调整默认页签。

前端拖拽对象优先：生成 `.slapp` 时，先生成能被 App Designer 前端打开、渲染、选中和保存的设计态对象，再同步运行态 `app.jl`。不要从 Julia 构造函数反推一个简化 `.slapp`；简化对象即使能生成代码，也可能在 Shape 渲染、容器命中、遮罩选择或重新保存时失败。

任务必要修改不是自由设计授权。与任务目标无关的属性必须保持拖拽默认值，不能省略、猜测或自行调整。每项修改都必须生成类型正确且可执行的 Julia 代码。

组件库对外暴露边界同样属于拖拽语义：

- 只有 `meta.js` 具有 `group` 字段的组件才显示在组件库面板，才可以响应用户的普通“创建组件”请求。
- `figure`、`buttongroup`、`radiobutton`、`togglebutton`、`tab` 没有 `group`，是内部结构节点，不能作为 UIFigure 下的独立面板组件生成。
- 用户说“创建单选按钮”“创建切换按钮”或“创建选项卡”时，默认创建对应的组组件。
- 只有用户明确要求向已有组内增加选项或页签时，才创建内部子节点。

例如，用户只说“创建一个文本区域”时：

- 使用组件库 TextArea 的全部默认属性。
- 保留默认 `Label`、字体、颜色、交互属性、回调字段等。
- 仅根据真实拖拽流程设置变量名、展示名、父组件和落点。
- 不要因为任务没有提到 `Label`，就删除或省略 `Label`。
- 不要因为 Julia 构造函数存在默认值，就省略 `.slapp` 顶层设计态字段。

权威来源：

- 设计态默认值：`app-designer/webview/src/uicomponents/*/meta.js` 中的组件类构造函数。
- 属性面板可见项：`app-designer/webview/src/uicomponents/*/props.js`。
- 运行时代码生成：`app-designer/webview/src/utils/generateCode.js`。
- Julia 运行时默认值：`tyappdesigner.jl/src/uifigureBasedApps/*.jl`。

## 设计态和运行态的区别

`.slapp.figure.children[]` 保存设计态组件节点。拖拽组件时，前端会：

1. 调用 `uicomponents[type].render()` 创建 `meta.js` 组件对象。
2. 生成唯一 `variableName`。
3. 如果组件有 `title` 且不是 `uiaxes`，把 `title` 改为变量名拆词。
4. 如果组件有 `label`，把 `label` 改为变量名拆词。
5. 如果组件有 `text`，把 `text` 改为变量名拆词。

运行态 `app.jl` 则由 `generateCode.js` 生成：先调用 `TyAppDesigner.<juliaMethod>(parent)`，再把设计态 `state`、顶层 `position`、顶层 `limits` 等写成属性赋值。

因此：每次创建普通组件时，必须先按 `meta.js` 构造函数创建完整顶层对象，再模拟真实拖拽流程，最后应用用户明确提出或完成任务必需的修改。不要用手写的“常用默认值表”代替完整对象，也不要把所有顶层默认字段复制进 `state`。

## 必须保留的展示字段

下列字段如果组件设计态存在，就不能因为 Julia 构造函数有默认值而省略：

- `label`：`DropDown`、`EditField`、`NumericEditField`、`TextArea`、`Spinner`、`Slider`、`FilePicker` 等。
- `title`：面板组件中的 `Panel` 和 `UIAxes` 必须保留默认标题；内部 `ButtonGroup` 和 `Tab` 只在实现组合组件时保留其组内默认标题或页签标题。
- `text`：`Button`、`ToggleButton`、`CheckBox`、`RadioButton`、`Menu` 等。
- `value`：输入类、选择类、表格、滑块、进度条等。
- `position`：面板拖拽默认尺寸必须保留，除 `Tab` 通常不写运行态 position。

示例：TextArea 从 UI 面板拖出来后应该有 Label。

设计态节点应保留：

```json
{
  "type": "textarea",
  "variableName": "TextArea",
  "label": "Text Area",
  "value": "",
  "placeholder": "",
  "horizontalAlignment": "left",
  "wordWrap": true,
  "fontName": "Helvetica",
  "fontSize": 12,
  "fontWeight": "normal",
  "fontAngle": "normal",
  "fontColor": [0, 0, 0],
  "backgroundColor": [1, 1, 1],
  "visible": true,
  "editable": true,
  "enable": true,
  "tooltip": "",
  "contextMenu": [],
  "position": [0, 0, 200, 60],
  "state": {
    "label": "Text Area"
  },
  "interruptible": false,
  "busyAction": "queue",
  "valueChangedFcn": "",
  "valueChangingFcn": "",
  "tag": ""
}
```

运行时代码应能生成等价视觉：

```julia
app.TextArea = TyAppDesigner.uitextarea(app.UIFigure)
app.TextArea.Position = [0, 0, 200, 60]
app.TextArea.Label = "Text Area"
app.TextArea.Value = ""
```

如果变量名不是默认名，例如 `DescriptionTextArea`，拖拽逻辑会把 label 改成 `"Description Text Area"`。生成 `.slapp` 时应把该值同步到组件顶层字段和 `state.label`。

## `.slapp` 顶层字段和 state 规则

对 `.slapp` 生成任务，组件顶层字段是完整设计态对象，`state` 只记录设计器流程实际修改过、需要生成进 Julia 代码的字段。两者不能混为一谈。

- 顶层字段：完整复制 `meta.js` 构造函数创建出的字段，包括属性面板当前未展示的字段。
- `state`：初始为 `{}`，随后只加入 `setComponentState` 实际写入的字段。
- 普通拖拽新增组件时，`generateComponentName` 会把存在的 `label`、`title` 或 `text` 按变量名更新，并同步写入 `state`。
- 拖拽落点只直接修改顶层 `position`，不写 `state.position`。`generateCode.js` 会单独读取顶层 `data.position`。
- 顶层 `value` 等默认字段不能省略，但没有经过修改时通常不应写入 `state.value`。
- 用户明确修改属性时，同时修改顶层字段并把该字段写入 `state`。
- 回调绑定同时写入顶层回调字段、`state.<callbackField>` 和 `callbackFcns`。
- `limits` 与 `position` 类似，由 `generateCode.js` 单独从顶层读取；不要仅凭通用规则塞进 `state`。

判断 `state` 的唯一可靠方式是模拟真实编辑器调用路径，而不是把顶层字段批量复制到 `state`。

错误示例：

```json
{
  "type": "textarea",
  "variableName": "TextArea",
  "value": "",
  "position": [0, 0, 200, 60],
  "state": {}
}
```

这个节点缺少 TextArea 的大量顶层设计态默认字段，不等价于面板拖拽组件。

同样错误的做法：

```json
{
  "type": "textarea",
  "variableName": "TextArea",
  "position": [0, 0, 200, 60],
  "label": "Text Area",
  "value": "",
  "state": {
    "position": [0, 0, 200, 60],
    "label": "Text Area",
    "value": ""
  }
}
```

它只保留了少量人工挑选字段，并把未修改的默认 `value` 和拖拽落点 `position` 错误写进 `state`。

## 面板拖拽默认值速查

以下是最容易影响视觉等价的默认字段：

| type | 必须关注的拖拽默认字段 |
|---|---|
| `button` | `text="Button"`, `position=[0,0,100,32]` |
| `checkbox` | `text="Check Box"`, `value=false`, `position=[0,0,90,24]` |
| `dropdown` | `label="Drop Down"`, `value="Option 1"`, `items=["Option 1","Option 2","Option 3","Option 4"]`, `position=[0,0,180,24]` |
| `editfield` | `label="Edit Field"`, `value=""`, `inputType="text"`, `characterLimits=[0,"Inf"]`, `position=[0,0,180,24]` |
| `numericeditfield` | `label="Edit Field"`, `value=0`, `limits=["-Inf","Inf"]`, `position=[0,0,190,24]` |
| `textarea` | `label="Text Area"`, `value=""`, `position=[0,0,200,60]` |
| `spinner` | `label="Spinner"`, `value=0`, `limits=["-Inf","Inf"]`, `step=1`, `position=[0,0,190,24]` |
| `slider` | `label="Slider"`, `value=0`, `limits=[0,100]`, `position=[0,0,250,60]` |
| `table` | `columnName=["Column1","Column2","Column3","Column4"]`, `columnWidth="auto"`, `position=[0,0,304,185]` |
| `html` | `hTMLSource=""`, `hTMLSourceType="inline"`, `position=[0,0,100,100]` |
| `image` | `imageSource=""`, `position=[0,0,100,100]` |
| `panel` | `title="Panel"`, `position=[0,0,400,160]`, `children=[]` |
| `radiobuttongroup` | `title="Button Group"`, `position=[0,0,180,120]`, 默认 3 个子单选项来自 `createChildren`，首项选中 |
| `togglebuttongroup` | `title="Button Group"`, `position=[0,0,180,120]`, 默认 3 个子切换项来自 `createChildren`，首项选中 |
| `tabgroup` | `tabLocation="top"`, `position=[0,0,260,220]`, `children=[]` |
| `gridlayout` | `rowSpacing=10`, `columnSpacing=10`, `padding=[10,10,10,10]`, `position=[0,0,300,200]`, `children=[]` |
| `uiaxes` | `title="Title"`, `xLabel=""`, `yLabel=""`, `position=[0,0,400,285]` |
| `progressbar` | `value=0`, `message=""`, `showMessage=false`, `showPercentage=true`, `position=[0,0,300,40]` |

内部结构节点默认值只用于组合组件内部，不属于面板可直接拖拽组件：

| internal type | 适用范围 | 默认字段 |
|---|---|---|
| `radiobutton` | `radiobuttongroup` 子项，或向已有单选按钮组增加选项 | 组合默认子项为 `Button`、`Button2`、`Button3`，首项 `value=true`，其余为 `false` |
| `togglebutton` | `togglebuttongroup` 子项，或向已有切换按钮组增加选项 | 组合默认子项为 `Button`、`Button2`、`Button3`，首项 `value=true`，其余为 `false` |
| `tab` | `tabgroup` 子页，或向已有选项卡组增加页签 | 默认标题和选中状态来自 `createChildren` 或用户明确修改 |

`radiobuttongroup` 和 `togglebuttongroup` 会自动创建子按钮，子按钮的 `state.value` 和 `state.text` 必须保留。

## 生成验收规则

创建或生成普通组件后，必须逐个组件执行以下验收。任一必需项不满足即为不通过。

### 1. 组件来源

- 对外创建的组件必须存在 `meta.js group` 字段，并属于 [component-map.md](component-map.md) 的“面板可创建组件”。
- 内部结构组件不得作为 UIFigure 下的独立面板组件生成；仅允许出现在规定的根节点或组合组件父节点下。
- 组件 `type`、Julia 类型和构造函数与 [component-map.md](component-map.md) 一致。
- 默认属性来自该组件当前 `meta.js` 构造函数，而不是人工记忆、Julia 默认值或通用模板。
- 组合组件必须具有与组件库 `createChildren` 一致的默认子组件结构。

### 2. 默认属性完整性

- 用户只要求“创建组件”时，组件顶层包含真实组件库拖拽后拥有的全部字段。
- 用户未明确修改的字段，其值和数据类型与组件库默认值一致。
- 不得遗漏未显示在属性面板中、但存在于 `meta.js` 的字段。
- 不得擅自增加组件库对象不存在的属性。

### 3. 用户覆盖项

- 只覆盖用户明确指定或完成任务目标必不可少的属性与内部结构。
- 每个覆盖值满足 [properties.md](properties.md) 中的类型、范围和特殊约束。
- 与任务目标无关的属性保持拖拽默认值，不因布局、美化、示例完整性或代码简化而改变。
- 任务必要修改必须能够说明其与用户目标的直接关系。

### 4. 命名与展示字段

- `variableName` 唯一并符合设计器命名规则。
- 组件存在 `label`、`title` 或 `text` 时，默认展示值与真实 `generateComponentName` 行为一致。
- 用户明确给出展示文本时，以用户值为准。

### 5. `.slapp` state

- 顶层字段表示完整设计态对象。
- `state` 只包含真实新增、命名、属性修改或回调绑定流程会记录的字段。
- 拖拽落点只写顶层 `position`，不得无故写入 `state.position`。
- 未修改的默认 `value` 等字段保留在顶层，但不得无故写入 `state`。
- 回调绑定同时存在于顶层回调字段、`state` 和 `callbackFcns`。

### 6. 父子关系与布局

- 组件挂在正确父组件下，`pid` 与组件树一致；根下组件 `pid` 必须为 `"Figure"`，容器内组件 `pid` 必须为直接父节点 `id`。缺少或错误的 `pid` 会让设计器拖动/移动时把已有组件误判为新增或复制组件。
- 同一 App 内 `variableName`、字段名和组件 `id` 必须唯一。重新生成或修复任务时不得把同一业务控件重复加入 `field_inits`、`figure.children[]` 或运行时代码；重复的按钮、表格等会导致 `duplicate field name` 或设计器显示多个同名对象。
- 容器和组合组件的 `children` 完整；普通叶子组件应省略 `children`。不要给叶子组件写空 `children: []`，否则前端会误判它不是叶子组件，设计期遮罩不会出现，HTML/iframe 等组件会因为内部点击不冒泡而选不中对象。
- Shape 渲染字段必须完整：凡会被前端 Shape 渲染的节点都必须有顶层 `position`；容器节点必须有 `children`；叶子节点不得写 `children: []`；所有节点必须有正确 `pid`、`visible`、`type`、`variableName` 和 `state`。缺少这些字段视为设计态失败，不能只用 `app.jl` 运行成功抵消。
- 任务要求调整 TabGroup 等组合组件时，调整后的子节点数量、`pid`、选中状态和生成顺序必须一致。
- 普通绝对布局使用顶层 `position`；GridLayout 子组件使用正确的 `layoutRow` 和 `layoutCol`。在 `.slapp` 设计态中，GridLayout 子组件的 `layoutRow` / `layoutCol` 必须写成范围数组，例如 `[1, 1]`、`[2, 2]`；不要写成数字 `1`、`2`。设计器画布按 `item.layoutRow[0]` / `item.layoutCol[0]` 过滤网格子项，数字会导致子组件不显示，看起来像空白。GridLayout 的 `columnWidth` / `rowHeight` 固定尺寸也应写成字符串，例如 `["120", "1x"]`、`["36", "36", "42"]`；不要混用数字 `120`、`36`，因为前端尺寸计算会调用字符串方法并导致控件挤成极小块或文本不显示。
- GridLayout 子组件布局是硬性三处同步规则：同一个子组件必须同时具有 `.slapp` 顶层 `layoutRow/layoutCol`、`.slapp.state.layoutRow/state.layoutCol`、以及 `.slapp.code` 和同目录 `app.jl` 中对应的 `LayoutRow/LayoutCol` 赋值。三处值必须表达同一范围，推荐统一写 `[n, n]`。缺任意一处都视为生成失败；不得用 `position` 代替 GridLayout 布局。否则常见症状是设计器中看得到，点击运行重新生成后 `LayoutRow/LayoutCol == missing`，所有 grid 子组件挤到一起或相互覆盖。
- 不手写 Julia 运行时 `Parent` 或 `Children`。

### 7. 运行时代码

- 使用 `TyAppDesigner.<constructor>(parent)` 创建组件。
- 生成的 Julia 属性赋值必须与 App Designer 正确的设计态到运行态语义等价。不要盲目复制当前 `generateCode.js` 的错误输出；如果现有生成器会产生非法 Julia，应生成合法运行时代码并把生成器缺陷作为产品问题标记。
- 生成完整 `.slapp` / `app.jl` 工程时，必须在运行后检查每个 GridLayout 子组件的 `LayoutRow` 和 `LayoutCol` 均不是 `missing`，并且与 `.slapp.state.layoutRow/state.layoutCol` 一致。只检查 `.slapp` 顶层 `layoutRow/layoutCol` 不足以通过验收。
- 数组、矩阵、字典和字符串等结构化属性必须生成类型正确且可执行的 Julia 字面量；例如 `Table.Data` 的二维文本数据必须生成字符串矩阵，不能丢失引号或被扁平化。JSON 对象递归生成为 `Dict{String,Any}(...)` 或 `Dict(...)`，数组递归生成为合法 Julia 数组，字符串必须带引号并正确转义。
- 对复杂 `Table.Data`、HTML `Data` 等结构化运行时状态，优先在 `StartupFcn` 中赋值，而不是强行塞进组件构造参数或 HTML 字符串。这样可以避免 `[Name, Value]` 未加引号、`[object Object]`、构造参数类型错误等生成问题。
- HTML `Data` 的 `[object Object]` 需要先判断出现位置：页面内部出现时检查 HTMLSource 是否直接显示对象；属性面板出现时是对象型 `data` 被 `customTextarea` 字符串化；生成的 `app.jl` 出现时检查 `.slapp` 是否把对象放进 `state.data` 并走了通用代码生成格式化。
- 禁止把 JavaScript 字符串化残留写入 Julia，例如 `[object Object]`。
- 用户要求的属性、回调和布局在运行后仍然生效。
- `.slapp` 内嵌 `code` 与独立 `app.jl` 内容一致。
- GridLayout 子组件的顶层 `layoutRow/layoutCol`、`state.layoutRow/state.layoutCol`、`.slapp.code` / `app.jl` 中的 `LayoutRow/LayoutCol` 三处一致；运行后不为 `missing`。
- 交付完整 `.slapp` / `app.jl` 工程时，必须使用 Syslab 实际运行生成的 `app.jl`；任何解析错误、未定义变量、类型错误或运行异常都判定为失败。仅交付代码片段时，至少执行类型、字面量和组件边界检查，并说明未做完整工程运行验收。

### 8. 完成判定

满足以下条件才可以报告组件创建完成：

- 打开 `.slapp` 后组件外观、属性和层级与相同操作在设计器中产生的结果一致。
- 与任务目标无关的属性仍是组件库默认值。
- 保存并重新打开不会丢失属性、回调或子组件。
- 运行生成代码不会改变用户在设计态看到的预期效果。
- Syslab 实际运行 `app.jl` 无异常，且运行后任务要求的通信、回调和交互行为有效。

## AI 生成检查清单

- 创建任何普通组件时，默认按组件库拖拽行为处理，先看 `meta.js` 默认类，不只看 Julia 构造函数。
- 普通“创建组件”请求只从具有 `group` 字段的面板组件中选择；不要独立创建内部结构组件。
- 用户明确要求或任务必需的属性可以修改；其他属性保持组件库默认值。
- `.slapp` 顶层节点必须包含 `meta.js` 实例的全部字段，不能只写“常用属性”。
- `.slapp` 设计态先通过前端 Shape 字段审计：Shape 节点有 `position`，容器有 `children`，叶子没有 `children: []`，并且 `pid/visible/type/variableName/state` 完整。
- `state` 只包含真实编辑器通过 `setComponentState` 修改的字段，不能等于顶层属性子集或完整副本。
- 有 `label/title/text` 的普通组件，新增命名流程会把展示名同步到顶层和 `state`。
- 生成纯 Julia 时，如果视觉依赖 `Label/Title/Text`，显式赋值。
- TextArea、DropDown、EditField、NumericEditField、Spinner、Slider、FilePicker 都应保留 `Label`。
- 变量名自动命名后，展示名应跟随拖拽逻辑用 `camelCaseToSpaces(variableName)`，除非用户明确给了展示文本。
- 用户明确指定展示名时优先级最高。例如变量名为 `DescriptionTextArea` 但用户要求界面标签显示“任务说明”，则顶层 `label` 和 `state.label` 都必须保留“任务说明”，不能再被自动转换成 `"Description Text Area"`。
- 生成完成前检查代码中不存在 `[object Object]`、未加引号的文本矩阵单元格或被错误扁平化的二维数据。
