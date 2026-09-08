# .slapp 工程结构规则

本文档约束 Syslab App Designer `.slapp` 工程文件的结构。它属于 App Designer 工程级规则，不只属于 ribbon/toolstrip。任何生成、修改、审查或调试 `.slapp` 的任务，都必须先满足本文档，再进入具体组件或 ribbon 规则。

本文档已经把当前 App Designer 插件前端和 Julia 后端的 `.slapp` 读写、设计器状态、代码生成与运行态字段契约提取为规则。后续使用本 skill 时，应直接遵守本文档，不需要再访问或依赖某个插件源码目录。

规则来源类型包括：

- 设计器编辑器状态字段。
- `.slapp` 打开时写入 editor store 的配置字段。
- figure 组件默认结构。
- toolstrip 默认结构与 normalize 规则。
- 设计器从 `.slapp` 生成 `app.jl` 的代码生成规则。
- Julia 后端 figure、toolstrip、toolstrip item、toolstrip control 的运行态协议字段。

## 1. 顶层字段

`.slapp` 顶层必须包含下列字段。缺省字段不得省略后等待设计器猜测；生成器应显式写入安全空值。

```json
{
  "name": "AppModuleName",
  "info": {
    "name": "Human Readable App Name",
    "version": "1.0",
    "author": "",
    "description": "",
    "icon": "",
    "startupFcn": ""
  },
  "userLoadedModule": "",
  "startUpFunctions": [],
  "callbackFunctions": [],
  "customPrivateFunctions": [],
  "customPublicFunctions": [],
  "customPrivateProperties": [],
  "customPublicProperties": [],
  "figure": {},
  "code": ""
}
```

字段要求：

- `name` 会被代码生成器写成 `module <name>`，必须是合法 Julia module 标识符；显示名应写入 `info.name` 或 `figure.name`。
- `info` 必须是 object；至少保留 `name/version/author/description/icon/startupFcn`。
- `userLoadedModule` 是可编辑代码文本，空值写 `""`。
- `startUpFunctions`、`callbackFunctions`、`customPrivateFunctions`、`customPublicFunctions`、`customPrivateProperties`、`customPublicProperties` 是集合字段，空值写 `[]`。
- `figure` 必须是 object，不能是 `[]`、`null` 或缺失。
- `code` 是设计器生成代码快照，不是工程真相源；不能用它替代 `figure`、`figure.toolstrip` 或 `callbackFunctions`。
- `savePath` 可由设计器打开后注入；离线生成时可省略，但不能依赖它补全其它字段。

注意：历史代码编辑槽在前端字符串模板中可接受空数组或空文本，但生成 `.slapp` 时应使用上面的统一类型，避免 `undefined` 被写进 Julia 代码。

关键交付规则：用户在 App Designer 中打开的是 `.slapp`，不是旁边的 `app.jl`。任何生成或修复任务都必须把 `.slapp` 作为主交付物和真相源：组件树写入 `.slapp.figure`，回调写入 `.slapp.callbackFunctions`，启动逻辑写入 `.slapp.startUpFunctions` 和 `info.startupFcn`，ribbon 写入 `.slapp.figure.toolstrip`。外部 `app.jl` 只能作为从 `.slapp` 生成出来的运行快照；只修改 `app.jl` 会在下次打开 `.slapp` 或点击 Run 后被覆盖，不能视为修复完成。

设计器前端模型优先规则：`.slapp.figure` 首先必须是 App Designer 前端能打开、渲染、选择和保存的设计态对象树，不只是能生成 Julia 代码的数据。生成 `.slapp` 时先按前端拖拽对象建模，再同步 `.slapp.code` 和同目录 `app.jl`。如果设计态对象缺少前端渲染必需字段，即使 `app.jl` 能直接运行，也不能视为合格工程。

## 2. figure 结构

`figure` 是 App Designer 组件树根。最小安全结构如下：

```json
{
  "id": "Figure",
  "type": "figure",
  "variableName": "UIFigure",
  "name": "Syslab App",
  "position": [100, 100, 640, 480],
  "color": [0.94, 0.94, 0.94],
  "tag": "",
  "visible": true,
  "state": {},
  "callbackFcns": {},
  "children": [],
  "toolstrip": {}
}
```

字段要求：

- `type` 必须是 `"figure"`。
- `variableName` 必须存在；默认值应为 `"UIFigure"`。代码生成器会使用 `app.<variableName>`。
- `state` 必须存在且为 object。`generateCode.js` 会解构 `data.state`；缺失时会触发运行时错误。
- `children` 必须是数组；没有普通 UI 组件时写 `[]`。
- `callbackFcns` 是普通 UI 组件使用的回调字段；figure 上可为空 object。不要给 toolstrip 实体发明 `callbackFcns`。
- `toolstrip` 可以是禁用的默认结构，也可以是完整业务 ribbon。输出目标包含 ribbon 时，完整业务结构必须保存在 `figure.toolstrip`。

## 3. 普通组件节点

非 toolstrip 的 UI 组件应遵循前端 `uicomponents/*/meta.js` 的组件结构。每个组件至少应包含：

- `id`
- `pid`
- `type`
- `variableName`
- `state`
- `callbackFcns`
- 容器/组合组件：`children`

代码生成器会用 `uicomponents[data.type].juliaMethod` 创建组件，并用 `data.variableName` 生成 `app.<variableName>` 字段。缺少 `type` 或 `variableName` 会导致组件无法生成或生成无效代码。

前端渲染字段审计是 `.slapp` 交付硬规则：

- 每个会被 Shape 渲染的节点都必须有顶层 `position`。即使运行态通常不设置该属性，设计态仍需要它计算 shape 的 left/top/width/height。
- 容器/结构节点必须有 `children`，例如 `figure`、`panel`、`gridlayout`、`tabgroup`、`tab`、`radiobuttongroup`、`togglebuttongroup`。
- 普通叶子组件不得写 `children: []`；叶子节点误写 children 会让前端把它当容器，导致设计期遮罩、选中和内部点击行为异常。
- 所有节点都必须有正确的 `pid`、`visible`、`type`、`variableName` 和 `state`；`pid` 必须和父节点 `children[]` 中的实际层级一致。
- 普通组件必须保留 skill 中记录的当前前端 meta 字段，不能只写少量“常用属性”，也不能依赖某台机器上的插件源码路径补全字段。

`pid` 必须等于直接父组件的 `id`。挂在 `figure.children[]` 下的组件写 `pid="Figure"`；挂在 `Panel`、`GridLayout`、`Tab`、`ButtonGroup` 等容器下的子组件写对应父节点 `id`。生成器不得只依赖父节点 `children[]` 表达层级；缺少 `pid` 会导致设计器拖动、移动、容器落点和选择逻辑把“移动已有组件”误判为“新增/复制组件”。

`children` 只给真正的容器/组合组件写，例如 `figure`、`panel`、`gridlayout`、`tabgroup`、`tab`、`radiobuttongroup`。普通叶子组件不要写空 `children: []`；前端 `Shape` 会用 `children === undefined` 判断是否给叶子组件盖设计期遮罩，HTML/iframe 组件尤其依赖该遮罩来响应设计器选中。叶子组件误写 `children: []` 会导致点击 HTML 内部时选不中组件。

## 4. toolstrip 结构

`figure.toolstrip` 是 ribbon 设计态真相源。它应使用前端 `toolstrip.js` 的实体类型：

```json
{
  "id": "Toolstrip",
  "type": "toolstrip",
  "variableName": "Toolstrip",
  "enabled": false,
  "visible": false,
  "activeTab": "",
  "tabs": []
}
```

无 ribbon 和空 ribbon 必须区分：普通无 ribbon 工程必须写禁用隐藏的空 toolstrip，例如 `enabled:false`、`visible:false`、`activeTab:""`、`tabs:[]`。只有任务明确要求 ribbon/toolstrip 时，才允许 `enabled:true`、`visible:true`，且 `tabs` 必须非空并包含真实业务结构，`activeTab` 指向真实 tab。`enabled:true, visible:true, tabs:[]` 是“空 ribbon 壳”，视为失败状态。

层级字段：

- toolstrip: `tabs`
- tab: `sections`
- section: `columns`
- column: `controls`
- control: `items`、`menuGroups`、`options`

各层必需字段：

- toolstrip：`id`、`type="toolstrip"`、`variableName`、`enabled`、`visible`、`activeTab`、`tabs`
- tab：`id`、`type="toolstriptab"`、`variableName`、`title`、`sections`
- section：`id`、`type="toolstripsection"`、`variableName`、`title`、`layout`、`columns`
- column：`id`、`type="toolstripcolumn"`、`variableName`、`layout`、`width`、`controls`
- control：`id`、`type="toolstripcontrol"`、`variableName`、`controlType`、`displayMode`、`text`

设计器 `normalizeToolstrip` 可以补默认值和兼容 `children`，但生成任务不得依赖隐式补全作为最终合规依据。最终 `.slapp.figure.toolstrip` 应显式包含 `type` 与 `variableName`，便于设计器重新生成代码和审计。

## 5. toolstrip control 默认字段

toolstrip control 推荐显式保留以下空值，特别是有菜单、下拉、gallery 或命令状态时：

```json
{
  "items": [],
  "menuGroups": [],
  "options": [],
  "commandDescriptor": {},
  "commandState": {},
  "commandContext": {},
  "lastCommand": {},
  "lastMenuItem": {}
}
```

字段语义：

- `items` 用于 dropdown、combobox、dropdownbutton、splitbutton、gallery、matlab-gallery 等条目。
- `menuGroups` 用于分组菜单。
- `options` 用于选项列表。
- `commandDescriptor` / `commandState` / `commandContext` / `lastCommand` / `lastMenuItem` 是运行态命令状态字段；空值优先用 `{}`，不要写 `null` 后再让运行代码做对象转换。

### matlab-gallery 的 `menuGroups` 契约

对于 `controlType = "matlab-gallery"` 或源应用风格 gallery 控件：

- `items` 必须保留为完整扁平列表，不能用 `menuGroups` 替代、删除或缩减。
- `menuGroups` 只表示右侧下拉 popup 的视觉分组，不是新的唯一数据源。
- `menuGroups` 中每个 group 必须使用小写设计态字段：`id`、`title`、`items`。
- `menuGroups[].items[]` 必须从同一控件的 `items[]` 中复制完整 item 对象，不能只写 `label` / `value`。
- 分组 item 必须保留原 item 已有的 `label`、`value`、`commandId`、`iconSrc`、`enable` 和其它交互字段。
- 对 `menuSelectionMode = "single"` 的 MATLAB 风格 gallery，当前/默认项必须写在父控件 `value` / Julia `Value` 上；`items[]` 与 `menuGroups[].items[]` 不得写 `checked` / `Checked`，否则会造成默认项和点击项同时高亮。
- 只有源对象是真正的 checkbox、多选菜单项、toggle 状态项，或父控件 `menuSelectionMode = "multiple"` 时，才允许在 item 上写 `checked` / Julia `Checked`。
- group `id` 必须在同一控件内唯一。中文或非 ASCII `title` 清洗后为空时，应使用稳定回退值，例如 `group-1`、`group-2`，不得都写成同一个 `group`。
- `.slapp.figure.toolstrip`、`.slapp.code` 和外部 `app.jl` 中的 gallery 分组信息必须同步；只修改其中一处会在设计器 Run 或重新打开后丢失分组。

## 6. toolstrip item 结构

下拉项、菜单项和 gallery item 应使用小写设计态字段：

```json
{
  "label": "Item",
  "value": "itemValue",
  "commandId": "Group|Control|Item",
  "enable": true,
  "iconSrc": "data:image/png;base64,..."
}
```

代码生成器会把 item 写成 `TyAppDesigner.ToolstripItem[...]`，并将小写字段转换为 Julia 构造器关键字，例如 `label -> Label`、`iconSrc -> IconSrc`、`checked -> Checked`。

`checked` 不是通用 item 必填字段。只有 checkbox、multiple、独立 toggle 或等价持久勾选状态 item 才写 `checked`；MATLAB-style single gallery 的当前/默认项使用父控件 `value` / Julia `Value`。

图标字段规则：

- `.slapp.figure.toolstrip` 中正式设计态图标字段是 `iconSrc`。
- `app.jl` / `.slapp.code` 中正式运行态图标字段是 `IconSrc`。
- `iconFile`、`sourceIconPath`、`sourceIconId`、`iconKind`、`iconLabel` 只能作为审计字段，不能替代 `iconSrc` / `IconSrc`。

## 7. 回调结构

任何普通组件或 toolstrip control 绑定了非空回调名时，`.slapp.callbackFunctions` 中必须存在同名函数定义。

toolstrip 常用回调字段：

- `buttonPushedFcn`
- `valueChangedFcn`
- `commandInvokedFcn`

`.slapp.callbackFunctions[]` 最小结构：

```json
{
  "name": "RibbonFeedback",
  "code": "item = event.Item\n# function body only"
}
```

`callbackFunctions[].code` 只能写函数体，不能再包一层完整的 `function <name>(app, event) ... end`。App Designer 代码生成器会根据 `callbackFunctions[].name` 自动生成外层函数签名；如果 `code` 中再写完整函数，会生成嵌套函数或错误结构。

对于 `.slapp` / 设计器生成 app，最终真相源是 `.slapp.callbackFunctions`。只修改外部 `app.jl`，下次点击设计器 Run 后会被重新生成覆盖。

## 8. 生成代码规则

设计器 Run 会根据 `.slapp` 重新生成 `app.jl`：

- `generateCode(data)` 使用 `data.name` 写 Julia `module`。
- `generateCode(data)` 使用 `data.figure` 生成组件树。
- `generateCode(data)` 使用 `normalizeToolstrip(data.figure?.toolstrip)` 和 `flattenToolstripEntities` 逐层生成 `uitoolstrip*` 代码。
- toolstrip 运行代码必须使用 `TyAppDesigner.uitoolstrip*` 构造器和 `TyAppDesigner.ToolstripItem[...]`。
- `.slapp.code` 只是代码快照；不能作为 `figure.toolstrip` 或 `callbackFunctions` 的替代。

## 9. 常见失败模式

以下问题必须视为结构不合规：

- 顶层缺少 `userLoadedModule`，导致生成代码出现裸 `undefined`。
- 顶层函数/属性集合缺失或类型错误，导致代码编辑槽生成非法文本。
- `figure` 缺少 `variableName`，导致生成 `app.undefined` 或无法引用根 figure。
- `figure` 缺少 `state`，导致 `generateCode.js` 解构 `data.state` 时报错。
- 普通 UI 组件缺少 `pid`，或 `pid` 与父节点 `children[]` 所表达的层级不一致，导致设计器移动/拖拽时复制出新组件或落入错误容器。
- toolstrip 实体缺少 `type`，导致 `flattenToolstripEntities` 无法识别子层级或代码生成器跳过实体。
- toolstrip 实体缺少 `variableName`，导致运行代码无法为实体生成稳定字段。
- 业务 ribbon 同时存在于 `figure.toolstrip` 和 startup/code 中，导致运行后 tab 重复。
- `.slapp.figure.toolstrip` 只有 `iconFile` / `sourceIcon*`，没有 `iconSrc`。
- control 绑定了回调名，但 `.slapp.callbackFunctions` 中没有同名定义。
- `.slapp.callbackFunctions[].code` 中写入完整 `function ... end`，而不是只写函数体。

## 10. 验收清单

生成或修改 `.slapp` 后，至少检查：

1. 目录中只有一个明确主 `.slapp`。
2. `.slapp.name` 是合法 Julia module 标识符。
3. 顶层必需字段存在，空值类型符合本文档。
4. `figure` 是 object，且有 `type`、`variableName`、`state`、`children`。
5. 所有普通 UI 组件都有 `pid`，且 `pid` 与父节点 `children[]` 的组件树一致；根下组件的 `pid` 为 `"Figure"`。
6. 前端渲染字段通过审计：Shape 节点有 `position`，容器有 `children`，叶子节点没有 `children: []`，所有节点有正确 `pid/visible/type/variableName/state`。
7. `figure.toolstrip` 中每个 toolstrip 实体都有 `type` 和 `variableName`；无 ribbon 工程使用 `enabled:false, visible:false, tabs:[]`，不得交付空 ribbon 壳。
8. 所有绑定回调名都能在 `callbackFunctions[].name` 找到。
9. 所有 `callbackFunctions[].code` 都只是函数体，不包含外层 `function ... end` 包裹。
10. 图标使用正式 `iconSrc` / `IconSrc` 字段。
11. 设计器打开主 `.slapp` 成功。
12. 通过设计器 Run 命令重新生成并运行成功。
13. 运行后 `app.jl` 中不存在裸 `undefined`，Julia 语法可解析，回调和 `IconSrc` 仍保留。

## 11. 与 ribbon 文档的关系

本文档只定义 `.slapp` 工程结构。涉及 ribbon/toolstrip 的布局、控件选型、图标解析、菜单状态、源应用对标和运行时视觉验收时，还必须继续遵守：

- `ribbon/README.md`
- `ribbon/workflow/generation-gate.md`
- `ribbon/rules/ribbon-rules.md`
- `ribbon/rules/ribbon-validation.md`
- `ribbon/source/icon-resolution.md`
