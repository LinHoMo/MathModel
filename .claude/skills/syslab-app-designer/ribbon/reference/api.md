# Ribbon API 中文说明

这份文档只描述 TyAppDesigner ribbon/toolstrip 的核心契约。
生成器只能通过声明式 API 生成、修改和读取 ribbon。

## 相关文档

- `components.md`
- `layout-rules.md`
- `../rules/ribbon-rules.md`
- `../source/source-generation.md`
- `../rules/ribbon-control-selection.md`
- `../rules/ribbon-validation.md`

## 文档定位

这份文档回答的是：

- ribbon API 正式支持什么
- 字段和结构契约是什么
- 运行链和 patch 约束是什么

这份文档不负责：

- 代替任务模板去组织提示词
- 代替 golden spec 去描述某个具体 app 的业务结构

## 核心原则

- 只返回 JSON/spec 或 patch payload
- 不生成 Vue、HTML、CSS、JS 渲染器改动
- 不直接操作 DOM
- 不把任何具体 app 的业务结构写进插件核心

## 严格规则

通用硬规则统一收敛在：

- [rules/ribbon-rules.md](../rules/ribbon-rules.md)

这份 API 文档只补充 API 侧的专属要求：

1. 除非调用方明确要求别的格式，否则只返回 JSON/spec 或 patch payload。
2. 只能围绕固定结构 `toolstrip -> tab -> section -> column -> control` 工作。
3. API 层优先关心“字段契约是否成立”，而不是“前端当前是否碰巧能渲染”。

## 对外 API

| 函数 | 用途 |
| --- | --- |
| `ribbon_icon_src_from_file(path)` | 读取本地图标文件并转为 ribbon 控件可使用的 `iconSrc` 数据 |

实现位置：TyAppDesigner ribbon/toolstrip API 源码。

## 数据结构

ribbon 树结构固定为：

`toolstrip -> tab -> section -> column -> control`

生成器只应围绕这套结构工作。

## 组件创建 API

设计器根据 `.slapp.figure.toolstrip` 生成 `app.jl` 时，使用下面的结构函数：

| 函数 | 用途 |
| --- | --- |
| `uitoolstrip(...)` | 创建整条 Ribbon |
| `uitoolstriptab(...)` | 创建标签页 |
| `uitoolstripsection(...)` | 创建分组 |
| `uitoolstripcolumn(...)` | 创建分组中的布局列 |

具体控件函数如下。

`uitoolstripcontrol(parent; ...)` 是包含全部字段的底层通用入口，适合协议构建、
兼容旧代码或需要高级字段的场景。普通生成代码和手写代码优先使用按类型拆分的函数：

完整组件映射和回调选择见 [reference/components.md](components.md)；
布局细节见 [reference/layout-rules.md](layout-rules.md)。

| 函数 | 用途 |
|---|---|
| `uitoolstripbutton(...)` | 普通按钮 |
| `uitoolstriptoggle(...)` | 可切换按钮 |
| `uitoolstriplabel(...)` | 文字标签 |
| `uitoolstripspacer(...)` | 空行或间距占位 |
| `uitoolstripeditbox(...)` | 单行输入框 |
| `uitoolstripdropdown(...)` | 不可编辑的值选择下拉框，选项写入 `Items` |
| `uitoolstripcombobox(...)` | 可输入/可选择组合框，候选值写入 `Options` |
| `uitoolstripcheckbox(...)` | 复选控件 |
| `uitoolstripradio(...)` | 单选控件 |
| `uitoolstripdropdownbutton(...)` | 动作下拉按钮 |
| `uitoolstripsplitbutton(...)` | 主按钮加下拉菜单 |
| `uitoolstripgallery(...)` | 通用 gallery |
| `uitoolstripmatlabgallery(...)` | MATLAB 风格 gallery |

示例：

```julia
column = TyAppDesigner.uitoolstripcolumn(section; Layout="stack", Width="95px")
TyAppDesigner.uitoolstriplabel(column; Text="Frequency")
TyAppDesigner.uitoolstripeditbox(
    column;
    Value="1.0",
    CommandId="Input|Frequency",
    ValueChangedFcn="RibbonFeedback",
)
```

说明：

- 快捷函数内部仍创建同一种 `ToolstripControl` 运行时对象，不改变通信协议。
- 只有快捷函数没有覆盖的高级字段，才需要直接调用 `uitoolstripcontrol(...)`。
- `collapse` 是 gallery/overflow 使用的内部入口，不作为普通业务控件推荐生成。

## 支持的控件类型

当前支持：

- `button`
- `toggle`
- `radio`
- `checkbox`
- `label`
- `spacer`
- `dropdown`
- `dropdownbutton`
- `gallery`
- `matlab-gallery`
- `combobox`
- `editbox`
- `splitbutton`

说明：

- 不要因为前端“碰巧能渲染”就输出隐藏/内部控件
- `label` 适合 section 内部的字段标题或说明文本
- `spacer` 是无交互占位控件，适合源应用风格字段区里的空白行
- `editbox` 是单行文本输入框，适合和 `dropdown`/`combobox` 组合成源应用风格参数区
- 当前实现中，`dropdown` 是不可编辑的值选择下拉框，候选值写入 `items`；适合对标源应用字段区中的 `DropDown()`
- 当前实现中，`combobox` 是可输入/可选择控件，候选值写入 `options`；适合对标源应用 `ComboBox()`
- `combobox` 仍不等同于完整源应用 `ComboBox()`；其键盘行为与自动完成能力存在实现差距
- `dropdownbutton` 现在对标源应用 `DropDownButton`
- `splitbutton` 现在对标源应用 `SplitButton`
- `matlab-gallery` 对标源应用中“一个长方形 gallery 控件 + 右侧下拉”的组件
- 这组控件的当前真实行为与源应用对照，统一见：
  [rules/ribbon-control-selection.md](../rules/ribbon-control-selection.md)

## Gallery 行为说明

当前 gallery 行为有几条必须明确的硬规则：

- 当 section 的 `layout = "gallery"` 时，除了 `layout = "more-slot"` 以外的所有 column，都会被渲染成 gallery item
- 这意味着你不能在同一个 gallery section 内，再放一个位于 gallery 主体外侧的普通附属按钮
- 如果你需要源应用风格的 MATLAB gallery，应优先使用控件级 `controlType = "matlab-gallery"`，不要再把整个 section 设成 `layout = "matlab-gallery"`
- gallery item 的持久选中态由 `control.value` 驱动
- `variant` 只负责视觉风格，不等同于选中状态
- gallery overflow 当前会把隐藏 gallery item 和 collapse 自身的 items 扁平合并成一个列表
- 这和普通 dropdown / splitbutton 的 `menuGroups` 不是同一种能力

## 源应用风格 Gallery 行为说明

如果调用方明确要求源应用风格 gallery，应优先使用控件级 `controlType = "matlab-gallery"`，而不是普通 `gallery`，也不是 section 级 `layout = "matlab-gallery"`。

当前 `matlab-gallery` 的正式契约是：

- `matlab-gallery` 是一个原子控件：一个长方形 frame，内部是一排相邻 item，最右侧是该控件自己的下拉按钮
- gallery item 写在该控件的 `items` 中，不再由 section 的 column 自动收集
- `visibleCount` 写在控件上，表示首选可见 item 数
- `itemWidth` 可选；未提供或值无效时，渲染器使用默认源应用风格 item 宽度
- `frameWidth` 可选；通常不需要填写
- 如果显式填写 `frameWidth`，它必须能容纳 `min(visibleCount, items.length) * itemWidth + 右侧下拉槽位 + frame 内边距`；否则渲染器会按可用宽度压缩可见 item 数，可能只显示第一个 item
- 默认首选可见数上限为 `5`
- 如果控件里的实际 item 数少于 `5`，就显示实际 item 数
- 横向空间不足时会压缩可见 item 数，但至少保留 `1` 个可见 item，并且右侧下拉槽位始终保留
- 下拉 popup 外框宽度应与当前 gallery frame 一致；frame 压缩后，popup 内 item 必须随可用宽度减少每行列数，不能互相重叠
- 如果要保持源应用风格 gallery 的持久选中态，必须维护控件 `value` 或 item `checked`
- `commandInvokedFcn` / `buttonPushedFcn` 回调收到的事件中，`LastMenuItem` / `lastMenuItem` 表示当前 item；`GallerySource` / `gallerySource = "gallery-item"` 表示点击可见 item，`GallerySource` / `gallerySource = "menu"` 表示从右侧下拉选择
- 为兼容不同运行链，`matlab-gallery` 建议同时设置 `commandInvokedFcn` 和同名 `buttonPushedFcn`；前端会优先用 `buttonPushedFcn` 触发 gallery item 点击/选择，仍保留 `commandInvokedFcn` 作为命令语义字段
- `matlab-gallery` 所在 section 和 column 必须允许 flex shrink；不要把外层 section / column / frame 全部写成不可收缩固定宽度，否则窗口压缩时 gallery 不会逐项折叠
- 如果 `matlab-gallery` 与普通控件共存在同一个 section，section 最小宽度必须同时计入普通列宽度和列间距；压缩只应减少 gallery 内可见 item，不能让普通列覆盖 gallery
- 同一个 tab 中有多个 `matlab-gallery` 时，可见 item 数必须由 tab 统一、确定性地分配；不能让各 gallery 根据瞬时剩余宽度独立伸缩，否则拉伸时会出现先显示又隐藏的跳动
- 旧的 section 级 `layout = "matlab-gallery"` 已废弃，不要在新生成内容中使用

## 源应用优先页面布局契约

如果调用方明确要求“对标源应用”，页面布局必须先遵守 `source-first`，只有在源应用的证据不完整时，才允许退回插件默认布局。

布局证据优先级：

1. 源应用源码 / 可验证运行时结构
2. 已验证的 golden spec
3. 明确截图或录屏
4. 插件默认布局规则

这意味着：

- 先还原源应用的 tab 顺序、section 顺序、section 标题，再决定控件类型和布局
- 不要先按插件默认规则生成，再事后“尽量像源应用”
- 如果源应用的源码、截图、golden spec 已经明确某个 section 的列数、列宽、控件层级或对齐方式，就应直接采用
- 只有当源应用没有给出足够证据时，才允许退回通用默认布局

## 源应用风格 section 内布局规则

当目标是源应用风格 ribbon 时，至少遵守这些页面布局规则：

- gallery 型 section：
  - 优先在普通 `columns` section 中放置控件级 `controlType = "matlab-gallery"`
  - 该 gallery 控件本身承载右侧下拉/展开槽位
  - 不要把普通按钮、radio、analyze 等附属控件塞进 section 级 gallery 渲染器
- 表单型 section：
  - 优先按源应用的“列模型”建模，而不是只按控件类型拼接
  - 典型模式是 `label column + value column + unit / option column`
  - 如果源应用存在空白占位行，优先使用 `spacer`，不要让别的控件被强行拉伸去凑高度
  - 如果源应用以 `addColumn('Width', W)` 或等价定义为字段列给出宽度，应将该字段型 `stack` 列写为 `width: "Wpx"`，并在运行代码中保留该列宽
  - `editbox` / `combobox` 通常通过字段列宽度继承视觉预算；只有源应用为单个控件提供独立宽度证据时，才额外写 `control.width`
- 选项型 section：
  - `radio` / `checkbox` 应视为表单行，而不是按钮
  - 选项列按内容自然宽度排布
  - 纵向 option stack 不应参与普通按钮列的剩余高度分配
- 普通大按钮 section：
  - 每个 large command 通常独占一个 column
  - 优先保持源应用的按钮顺序、文本换行、图标层级
- `matrix + stack` 混合 section：
  - 先保留源应用的主次层级，再决定 `matrixColumns` 或 `stack`
  - 不要为了“更均匀”而改掉源应用的按钮大小层级

## 源应用风格对齐规则

默认对齐应先对齐源应用，而不是先对齐插件自己的通用视觉：

- section 内容区默认优先让整组控件在垂直方向上与源应用一致
- 表单型 stack 列应优先保持“整列居中、列内紧凑”
- `label` 文本默认左对齐
- `editbox` / `dropdown` / `combobox` 用于字段区时按字段逻辑对齐；动作菜单使用 `dropdownbutton` 或 `splitbutton`，不能替代字段选择控件
- 字段型 `stack` 列若有显式 `column.width`，该宽度是运行态布局约束，不应被当作普通命令列设计态空槽丢弃
- 同一列中纵向排列的多个 `small` 命令（包括 `button` 与 `splitbutton` 混排，例如 New/Open/Save）必须使用 column `layout = "stack"`，以共享图标和文字的左对齐基线
- `radio` / `checkbox` 默认不应带按钮式整块 hover / active 背景，除非源应用明确有这种表现
- gallery、field、option 三类 section 不应共用同一套宽度和对齐口径

## 源应用风格布局保真要求

如果调用方要求“尽量完全一样”，至少要把下面这些信息作为正式布局契约保存下来：

- 每个 section 的标题与顺序
- 每个 section 内 column 的顺序
- 每个 column 的宽度预算
- 每个控件的显示层级：
  - `large`
  - `small`
  - `stack`
  - `matrix`
- 字段区的行数模型
- 哪些位置是空白占位，而不是缺失控件
- 哪些控件必须保持自然宽度，哪些控件允许拉伸

如果这些信息已经从源应用中提取出来，后续生成任务应直接复用，不要重新猜。

## 运行模型说明

正式运行链路只有一条：

```text
AI 生成 .slapp -> 设计器读取 figure.toolstrip -> 点击运行生成 app.jl -> app.jl 调用 uitoolstrip* 创建 Ribbon
```

不要在启动函数或嵌入代码中再解析另一份 Ribbon spec 创建第二棵组件树。

## 设计器生成 app 的额外约束

如果目标是 `.slapp` / 设计器生成 app，还要额外遵守这些规则：

- 设计器里能预览到 ribbon，并不等于生成出来的 app 一定能稳定运行
- 设计画布中的 ribbon 不执行业务回调；按钮、gallery item 与下拉项的弹框/业务行为必须在点击“运行”后打开的 app 窗口中验证
- 点击“运行”时，会根据 `.slapp` 重新生成 `app.jl`；单独维护的外部 `app.jl` 不是最终真相源
- Ribbon 回调实现必须写入 `.slapp.callbackFunctions`；仅修改外部 `app.jl` 或仅向 `.slapp.code` 填入函数，不足以保证下一次设计器重新生成后仍然存在该回调
- 任何 toolstrip control 的 `buttonPushedFcn`、`valueChangedFcn` 或 `commandInvokedFcn` 为非空时，`.slapp.callbackFunctions[].name` 中必须存在同名定义
- `.slapp.callbackFunctions[].code` 只能写函数体，不能包含完整 `function <name>(app, event) ... end`；完整函数签名由 App Designer 根据 `callbackFunctions[].name` 自动生成
- `.slapp.code` 是生成代码快照，不得替代 `figure.toolstrip`、`callbackFunctions`、`startUpFunctions` 等结构化工程字段
- 不要给 toolstrip 实体发明未文档化的 `callbackFcns` 字段；只能使用契约正式暴露的 toolstrip 回调字段
- 不要假设通过 `customPublicFunctions` 插入的 helper，一定能在 startup 或 toolstrip callback 中直接可见，除非该调用方式已经被明确验证
- 对复杂 toolstrip 行为，必须在设计器点击“运行”后打开的 app 窗口中验证

## 设计器运行时回调事件

在 `.slapp` / 设计器生成 app 中，回调签名为：

```julia
function RibbonFeedback(app, event)
    item = event.Item
end
```

上面的完整函数签名是设计器生成后的 `app.jl` 形态。写入 `.slapp.callbackFunctions[].code` 时只能写函数体，例如 `item = event.Item`，不要把 `function RibbonFeedback(app, event)` 和结尾 `end` 一起写进去。

交互控件的当前状态和触发载荷应从 `event.Item` 读取，不应假设它们直接位于 `event` 顶层。

通用读取字段包括：

- `event.Item.CommandId` / `event.Item.commandId`，推荐格式为 `分组名|组件名`
- `event.Item.Text` / `event.Item.text`
- `event.Item.ControlType` / `event.Item.controlType`
- `event.Item.Value` / `event.Item.value`
- `event.Item.LastMenuItem` / `event.Item.lastMenuItem`
- `event.Item.GallerySource` / `event.Item.gallerySource`

按钮、值选择、编辑输入、菜单项和 gallery item 都应在实际“运行”窗口中验证事件内容。占位反馈回调至少应按以下逻辑分发：

```julia
function RibbonFeedback(app, event)
    item = event.Item
    command_id = get(item, "commandId", get(item, "CommandId", "Ribbon|Unknown"))
    parts = split(command_id, "|")
    group = parts[1]
    component = length(parts) >= 2 ? parts[2] : "Unknown"
    value = get(item, "value", get(item, "Value", missing))

    message = "$group + $component"
    !ismissing(value) && (message *= " + $(value)")
    TyAppDesigner.msgbox(message, "Ribbon", "none")
end
```

如果触发源是菜单或 gallery 子项，值应优先从 `event.Item.LastMenuItem` / `event.Item.lastMenuItem` 中读取。

## 对标能力边界

- 源应用对标必须覆盖 section/column 顺序、控件语义、宽度预算、候选值、图标和回调行为。
- 像素级外观只要求在 Syslab 当前正式组件支持范围内尽量对齐。
- 如果 Syslab 当前控件不能复现源应用控件的视觉或交互细节，生成结果必须显式报告差异，不得宣称完全一致。

## 复杂场景指导

复杂 ribbon 场景应优先采用保守、可验证的模式，不要凭推测组合行为。

高风险场景包括：

- 单选 gallery 的状态保持
- gallery + overflow
- 两行 splitbutton
- 设计器生成 app 中 startup / callback 的状态保留

如果调用方要求这些场景，优先采用最小、端到端可工作的模式，避免依赖未文档化的渲染器或代码生成行为。

## 布局语义速查

下面这些值属于正式支持的显式布局语义，外部生成器不应再靠猜测使用：

- section `layout`
  - 空 / `columns`：普通列布局
  - `gallery`：所有非 `more-slot` column 都会成为 gallery item
  - `matlab-gallery`：已废弃的 section 级源应用风格 gallery；新内容不要使用
  - `overflow-gallery`：普通大按钮条 + collapse overflow
- column `layout`
  - 空：普通大按钮列
  - `stack`：纵向 small 控件堆叠
  - `matrix`：small 控件矩阵；可配合 `matrixColumns`
  - `more-slot`：gallery / overflow 的专用展开槽位
- control `controlType`
  - `matlab-gallery`：源应用风格原子 gallery 控件；`items` 定义 item，`visibleCount` 定义可见数，`itemWidth` 可选定义 item 宽度
- control `layoutVariant`
  - `splitbutton` 可用：
    - 空：默认布局
    - `two-line-dropdown`
    - `two-line-dropdown-attached-arrow`

补充规则：

- 当 `splitbutton.layoutVariant` 是两行变体时，`text` 里必须真的包含换行符
- `gallery` / `overflow-gallery` 中 collapse 的下拉项会与隐藏项扁平合并，不支持 `menuGroups` 式分组标题
- `controlType = "matlab-gallery"` 的 popup 外框必须与当前 gallery frame 同宽；窗口压缩后，应通过 item 换行/减少列数避免重叠
- `controlType = "matlab-gallery"` 的 item 不要求显式 `itemWidth`；缺省值由 Syslab 统一渲染
- 如果显式设置 `frameWidth` 和 `itemWidth`，应先按 `可见项数量 * itemWidth + 下拉槽位 + 内边距` 校验，避免 gallery 中间出现空白但 item 被压缩隐藏
- `matlab-gallery` 回调可以通过 `event.Item.LastMenuItem` 或 `event.Item.lastMenuItem` 取得被点击/选择的 item，并通过 `event.Item.GallerySource` 或 `event.Item.gallerySource` 区分可见 item 点击和下拉选择；item 内部的 `Value/Label` 与 `value/label` 都应兼容读取
- `matlab-gallery` 的直接点击和下拉选择应都能触发回调；生成 spec 时建议 `buttonPushedFcn` 与 `commandInvokedFcn` 指向同一个回调函数
- 如果要长期维持 gallery 选中态，必须同步维护控件 `value`

## 标识符说明

请统一按下面的规则理解标识：

- spec 里的 `id` 是稳定的外部标识
- ribbon API 默认通过 `Tag` 语义来使用这个稳定标识
- runtime 组件的 `Id` 是内部生成标识，不应假设它等于 spec `id`
- 稳定定位优先使用 `id` / `tag`
- 只有在你明确要定位某个运行时实例时，才使用 `controlId`

## 图标规则

图标字段属于控件定义本身，不存在单独的 `set_icon(...)` API。

图标字段分为三层：

- 来源 / 审计字段：`sourceIconId`、`sourceIconClass`、`sourceIconPath`、`iconFile`。
- `.slapp.figure.toolstrip` 设计态渲染字段：`iconSrc`，应为设计器可直接渲染的 `data:image/...` 或等价可渲染数据。
- `app.jl` / Julia 构造器运行态渲染字段：`IconSrc`，可由 `TyAppDesigner.ribbon_icon_src_from_file(joinpath(...))` 生成。

`iconFile`、`sourceIconId`、`sourceIconClass`、`sourceIconPath` 只能作为审计或中间字段，不能替代 `iconSrc` / `IconSrc`。如果 `.slapp` 中只有审计字段而没有 `iconSrc`，设计器不会把它视为已完成图标渲染契约。

源应用对标时，图标来源必须尽可能从源应用证据链中解析出来。源证据可能是独立图片文件，也可能只是内部图标 id、CSS class、资源 key、对象句柄、sprite sheet、雪碧图坐标或运行时对象引用。这些值只能作为来源证据，不能直接写成最终图标。生成器必须继续定位源码、应用 CSS、资源目录、资源映射表、运行时导出图片或等价证据，解析到真实图片资源后再进入正式图标链。

支持字段：

- `iconSrc`
- `iconKind`
- `icon`
- `iconLabel`
- `iconColor`

推荐优先级：

1. `iconSrc`
2. `iconKind`
3. `icon`
4. `iconLabel`

补充规则：

- 业务图标优先由调用方通过 `iconSrc` 提供
- 不要假设插件内置业务图标库
- 当前内置 fallback `iconKind` 只应视为最小集合：
  - `new`
  - `open`
  - `save`
  - `scope`
- 源应用对标场景中，源应用内部图标标识、图标 class、主题 icon id、资源 key、对象句柄、CSS class、sprite sheet 路径、background-position、裁切矩形、`iconLabel`、`iconKind`、`icon` 都不能替代可渲染 `iconSrc`
- 只要源证据显示有图标，生成器必须尽可能继续查找源应用 CSS、资源目录、源码、运行时对象或已知映射表；无法解析时应标记为图标提取失败或 `unknown`，不得静默改成无图标
- gallery item、菜单项等 item 级图标必须落到 item 自己的 `iconSrc`；父控件 `iconSrc` 不能作为 item 图标的隐式替代

本地图标推荐流程：

1. `ribbon_icon_src_from_file(path)`
2. 把返回值写入 `iconSrc`

源应用图标解析流程：

1. 从源证据记录 `sourceIconId` / `sourceIconClass` / `sourceIconPath` 或等价来源字段。
2. 如果来源不是独立图片文件，继续定位源应用 CSS、资源目录、源码、资源映射表、运行时导出图片或等价证据。
3. 如果来源是 CSS class、sprite sheet 或雪碧图坐标，根据 CSS 坐标、资源映射或源平台图标表裁切出独立 PNG，并写入 `resources/ribbon-icons` 或等价资源目录。
4. `.slapp.figure.toolstrip` 写入裁切 PNG 转成的 `iconSrc` data URL。
5. `app.jl` / `.slapp.code` 使用 `IconSrc = TyAppDesigner.ribbon_icon_src_from_file(joinpath(@__DIR__, "resources", "ribbon-icons", "<icon>.png"))`。

## 任务模板

如何给生成器提交 ribbon 生成任务，请看：

- [workflow/generation-task.md](../workflow/generation-task.md)
- [source/source-generation.md](../source/source-generation.md)
- [examples/ribbon-example-spec.json](../examples/ribbon-example-spec.json)

