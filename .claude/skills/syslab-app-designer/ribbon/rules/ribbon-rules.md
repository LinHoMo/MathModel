# Ribbon 通用规则

这份文档收敛 TyAppDesigner ribbon 生成时会反复出现的通用规则。

用途：

- API 文档引用它，避免重复抄写相同规则
- 任务模板引用它，避免每个模板都复制一整段限制
- 外部生成器生成 ribbon 时，可以把它视为统一约束源

## 0. 文档发现规则

不要在提示词里写死绝对路径。

如果外部生成器需要先找到这套规则，推荐它按下面顺序在当前 skill 或当前仓库内搜索：

1. `ribbon/README.md`
2. `../reference/api.md` 与 `../reference/components.md`
3. `../reference/layout-rules.md`
4. `ribbon-rules.md`

如果仓库位置变了，只要文件名和相对目录结构还在，这套入口依然成立。

## 1. 输出边界

生成器只能生成：

- `.slapp` 中的结构化 ribbon 定义与所需回调

生成器不应生成：

- Vue
- HTML
- CSS
- JS 渲染器改动
- Julia 插件内部实现
- 未文档化控件类型

## 2. 组件与字段规则

1. 只能使用 `../reference/components.md` 中列出的公开控件类型。
2. 不要依赖未文档化的运行时行为、隐藏前端支持或渲染器内部实现。
3. `preset` 只是可选样式提示，不是主要布局契约。
4. 优先使用显式布局字段：
   - `layout`
   - `layoutVariant`
   - `alignItems`
   - `width` / `height`
5. 不要假设插件核心内置业务图标库、业务 preset 或 app 专属兜底逻辑。
6. 组件支持范围、布局规则和源应用生成约束分别由对应 Markdown 文档维护。

## 3. 文件编码规则

1. 输出文本统一使用 UTF-8。
2. `.md` / 普通 `.json` 如果主要用于 Windows 直接查看，优先使用 `UTF-8 with BOM`。
3. `.slapp` 和任何会被 `JSON.parse` 直接读取的 JSON，必须使用 `UTF-8 without BOM`。

## 4. Gallery 规则

1. 当 `section.layout = "gallery"` 时，除了 `layout = "more-slot"` 的 column 之外，其余 column 都会进入 gallery 主体。
2. 不要在同一个 gallery section 内建模“位于 gallery 主体外侧的普通附属按钮”，除非插件已明确支持该能力。
3. 如果要保留 gallery 的持久选中态，必须同步维护 `control.value`，不要只依赖 `variant`。
4. 不要假设 gallery overflow 支持像 `menuGroups` 那样的分组标题；当前 gallery overflow 本质上是扁平列表。
5. 带下拉入口的 ribbon 控件，其下拉内容必须作为正式运行契约保留；如果源应用下拉项有图标，必须保留 item 级图标字段，不能生成空 popup 或纯文字退化项。具体控件选型约束见 `ribbon-control-selection.md`。

## 5. 源应用风格 Gallery 规则

1. 如果调用方明确要求源应用风格 gallery，优先使用控件级 `controlType = "matlab-gallery"`。
2. `matlab-gallery` 是一个原子控件：一个 frame 内包含可见 item 区和右侧下拉区。
3. gallery item 必须写入控件的 `items`，不要再让 section column 自动变成 gallery item。
4. `control.visibleCount` 表示首选可见数，不是无条件强制显示数。
5. 生成 `matlab-gallery` 时必须显式写入控件级 `visibleCount`、`itemWidth` 和 `frameWidth`。不得依赖插件默认值，也不得只写 section 级 `visibleCount`。
6. 默认首选可见数上限为 `5`；如果控件实际 item 数少于 `5`，就显示实际个数。无法从源应用取得首选可见数时，`visibleCount = min(5, items.length)`。
7. `itemWidth` 必须按源应用实测或文本内容估算；`frameWidth` 必须按 `itemWidth * visibleCount + 4 * (visibleCount - 1) + 18 + 2 + 1 + 12` 计算或使用等价实测宽度。
8. 横向空间不足时会压缩可见 item 数，但至少保留 `1` 个可见 item，并且右侧下拉槽位始终保留。
9. `controlType = "matlab-gallery"` 的下拉 popup 外框应与当前 gallery frame 同宽；frame 收缩后，popup item 必须按可用宽度换行或减少列数，不能重叠。
10. 旧的 section 级 `layout = "matlab-gallery"` 已废弃，新生成内容不要使用。
11. 同一 tab 内存在多个 `matlab-gallery` 时，响应式可见项必须由共同容器统一分配，并保持稳定优先级；禁止各 gallery 独立按当前余量重新扩张。
12. Gallery item 宽度不得用统一保守值撑大。`itemWidth` 应按源应用真实 UI 或文本内容计算，目标是覆盖图标和最长一行文字，再加最小 padding。
13. 计算 gallery `itemWidth` 时应先保留源应用换行，再按最长显示行估算宽度。推荐宽度为 `clamp(max(iconWidth + 16, longestLineWidth + 12), 64, 88)`。
14. 只有源应用截图、真实 UI 测量或明确源规范证明需要更宽时，`itemWidth` 才允许超过 `88px`。不得为了避免换行、避免 hover 挤压、或掩盖下拉/文本提取不完整，而统一写成 `96px`、`120px` 或更大的宽度。
15. 如果源应用 gallery item 有图标，最终生成结果必须为每个对应 `items[]` 写入 item 级 `iconSrc`。`iconSrc` 必须是 Syslab 前端可直接渲染的图片资源，例如 `.slapp.figure.toolstrip` 中的 `data:image/...`，或运行代码中可转换为 `data:image/...` 的本地图标引用。
16. 源应用内部图标标识、图标 class、主题 icon id、资源 key、对象句柄、`iconLabel`、`iconKind`、`icon` 等只能作为提取证据或中间态，不能作为源应用图标对标的最终渲染字段，除非目标平台已明确支持该标识并经过实际渲染验证。
17. 只给 `matlab-gallery` 控件本身设置 `iconSrc` 不等于完成 gallery item 图标抽取；父控件图标不得代替 item 图标。
18. 源应用 item 图标存在但生成结果中 `items[]` 缺少可渲染 `iconSrc` 时，必须视为源信息提取不完整，不得声明与源应用对标完成。
19. 当源应用 runtime snapshot、源码或运行时对象中存在 `GalleryPopup` / `GalleryCategory` / popup category，目标 `matlab-gallery` 必须生成 `menuGroups`，不得只把 category 下的 item 展平成单层 `items`。
20. `items` 是 gallery 主体、状态和兼容回调的主数据源；`menuGroups` 只表达下拉 popup 的分组视图。生成 `menuGroups` 时必须保留原 `items` 扁平列表。
21. `menuGroups[].items[]` 必须从同一控件的 `items[]` 复制完整 item 对象，保留 `label`、`value`、`commandId`、`iconSrc`、`checked` 等字段；不得只生成轻量 `{label,value}`。
22. `menuGroups` 必须使用小写设计态字段 `id`、`title`、`items`。不得使用 `Title`、`Items` 等运行时或源平台字段作为 `.slapp.figure.toolstrip` 的最终字段。
23. group `id` 必须唯一。由中文或非 ASCII 标题生成 id 时，如果清洗结果为空，应使用 `group-1`、`group-2` 等稳定唯一回退值。
24. 如果 `source_ribbon_snapshot.json` 中某个 MATLAB gallery 只有扁平 `items`、没有 `Popup.children`，这只能说明当前抽取路径没有拿到 popup 分组，不能作为“MATLAB 无分组”的证据。对标 MATLAB 时必须继续检查源码中的 `GalleryCategory`、运行时 popup 对象、配置表或可验证截图。
25. 对 MATLAB Antenna / Wireless / Signal 等 App 中已知使用 `GalleryCategory` 的 gallery，生成器必须优先从 runtime popup category 或源码 category 恢复分组；只有可验证证据证明源 UI 确实无分组时，才允许不生成 `menuGroups`。
26. 添加 `menuGroups` 不得改变原有 `visibleCount`、`itemWidth`、`frameWidth`、`menuSelectionMode`、`menuItemMarkStyle`、回调名和主 gallery 可见项顺序。

## 6. `.slapp` / 设计器运行链规则

1. 如果目标是 `.slapp` / 设计器生成 app，要在任务中明确写出来。
2. 默认理解为：点击“运行”会根据 `.slapp` 重新生成 `app.jl`，而不是使用单独手改的外部 `app.jl`。
3. 不要给 toolstrip 实体发明未文档化的 `callbackFcns` 字段。
4. 不要假设通过 `customPublicFunctions` 插入的 helper，一定能在 startup 或 toolstrip callback 中直接调用，除非调用方明确要求并验证过这种模式。
5. 对复杂 ribbon 行为，优先选择最小可工作的模式，而不是一次性拼装大而全的推测性结构。
6. 生成 `.slapp` 时，ribbon 必须只有一个真相源：完整业务结构保存在 `.slapp.figure.toolstrip`。
7. `startUpFunctions`、`info.startupFcn` 和嵌入 `code` 中不得再解析第二份 Ribbon spec 或创建第二棵 Ribbon；否则会导致运行后 tab 重复。
8. 不再支持以启动函数动态应用整份 Ribbon spec 的生成模式。
9. 生成后必须检查是否混用了静态 toolstrip 与额外创建代码；混用会导致运行后 tab 重复，例如 `New / Designer / New / Designer`。
10. Ribbon 回调实现必须保存到 `.slapp.callbackFunctions`；不得只修补设计器生成后的外部 `app.jl`。
11. 任何 toolstrip control 绑定的非空回调名，都必须在 `.slapp.callbackFunctions[].name` 中有同名定义。
12. `.slapp.callbackFunctions[].code` 只能保存函数体，不能包含完整 `function <name>(app, event) ... end` 包裹；外层函数由 App Designer 根据 `callbackFunctions[].name` 自动生成。
13. `.slapp.code` 仅作为生成快照，不能替代 `figure.toolstrip`、`callbackFunctions` 或其它结构化工程字段。
13. 用于代码生成的可选字段必须有明确空值：空代码文本使用 `""`，空函数/属性集合使用 `[]`，不得将 JavaScript `undefined` 写入 Julia 源代码。

`.slapp` 的空工程代码槽至少应初始化为：

```json
{
  "userLoadedModule": "",
  "customPublicFunctions": "",
  "customPublicProperties": [],
  "customPrivateFunctions": [],
  "customPrivateProperties": [],
  "startUpFunctions": [],
  "callbackFunctions": []
}
```

## 7. 源应用对齐规则

1. 如果目标是对标源应用，先分析源应用的布局证据，再生成 spec；不要先套插件默认布局。
2. 布局证据优先级：
   - 源应用运行时快照 / 可复查控件树
   - 源应用源码 / 运行时结构
   - golden spec
   - 截图 / 录屏
   - 插件默认规则
   通用快照契约见 `../source/runtime-snapshot.md`。
3. 对标源应用时，必须尽量保留：
   - section 顺序
   - column 顺序
   - 控件层级
   - 宽度预算
   - 对齐方式
   - 空白占位行
   - `displayMode`
   - 实际文本换行
   - 图标渲染状态
   - checked / radio / toggle 状态
4. `radio` / `checkbox` 在源应用风格 section 中应视为表单行，而不是按钮。
5. 对标源应用的字段区，优先使用明确列模型，例如 `label column + value column + unit/option column`。
6. 只有 `displayMode = "small"` 的多个纵向命令才可以共享 `layout = "stack"` column。File / New / Open / Save 命令组也必须满足这一前提；不得因为它属于 File 组就把 `large` 命令放入 stack。
7. `column.layout = "stack"` 不是通用竖排大按钮容器。禁止把 `displayMode = "large"` 的 `button`、`toggle`、`splitbutton` 或 `dropdownbutton` 放进同一个 `stack` column。
8. 如果源应用是大图标命令按钮，应为每个大按钮生成独立的 `layout = "default"` column；即使这些按钮属于同一个 File / Session / New-Open-Save 命令组，也必须每个 `large` 控件独占一个 column。
9. 只有源应用明确是小图标纵向命令组时，才使用 `layout = "stack"`，且该 column 内所有命令控件必须为 `displayMode = "small"`。
10. 带下拉入口的源控件必须保留源应用语义。生成器不得为了通过验证、避免空菜单、或适配当前前端显示效果，而把源应用中的 `splitbutton`、`dropdownbutton` 或等价下拉控件降级为普通 `button`。
11. 如果源控件具有下拉入口，但当前提取结果没有非空 `items` 或 `menuGroups`，这表示源信息提取不完整，生成任务不得视为完成。生成器必须继续从源应用结构、运行时对象、菜单子项、popup / list item、动态 popup 构造逻辑、配置文件或可验证源规范中提取菜单项。
12. 提取下拉控件时，不能只检查控件本体的 `items` 字段。必须递归检查与该控件关联的 popup、children、menu item、list item、menu groups、dynamic popup callback、运行时对象树和可验证源规范。第一轮结果为空时，不得直接降级。
13. 只有在有可验证证据证明源控件本身没有下拉菜单项，或调用方明确要求降级时，才允许建模为普通 `button`。该决定必须写入生成说明，并说明证据来源。
14. 两行文字的 `splitbutton` / `dropdownbutton` 若源应用箭头位于第二行文字右侧，必须设置 `layoutVariant = "two-line-dropdown-attached-arrow"`，例如 `text = "打开\n会话"` 时箭头贴在“会话”右侧。
15. 显示文本必须保留源应用文本结构，包括换行、空格、大小写和顺序。gallery item、按钮和菜单项在源应用中显示为两行时，生成结果必须使用 `\n` 表示两行文本。不得通过增大 `itemWidth`、`width` 或其它布局字段替代源应用中的换行。
16. 源应用对标任务的验收优先级高于“能运行”和“无硬错误”。`py_compile`、Julia `include`、`.slapp.code == app.jl` 只能证明运行性，不能证明控件语义、文本结构、下拉入口和视觉布局已经对标完成。
17. `Popup = double`、空 `Popup`、空 `items` 或空 `menuGroups` 不能作为“源控件无菜单”的充分证据；它只能说明当前抽取路径没有拿到菜单。生成器不得把这类空结果当成降级依据。
18. 动态 popup、lazy menu、运行时构造菜单或状态相关菜单必须通过交互触发、状态初始化、回调执行路径、源对象树递归或源配置继续提取。未完成这些提取前，不得把控件改为普通 `button`。
19. 生成脚本、审计脚本和修复脚本不得包含自动降级逻辑，例如 `if not items: return button(...)`、`empty splitbutton -> button`、`empty dropdownbutton -> button`。遇到下拉项为空时应 fail 或记录“源菜单提取不完整”，而不是修成可交付结果。
20. 审计脚本只能做确定性的格式和一致性修复，例如编码、JSON 排版、callback 补齐、gallery 宽度下限、`.slapp.code` 与 `app.jl` 同步；不得改变源控件语义、删除下拉箭头、删除源 UI 中存在的换行或把字段型控件改成动作按钮。
21. 源应用截图、录屏或真实 UI 观察显示为两行文本时，生成结果必须保留 `\n`。运行时 log 的 `Text` 字段如果没有换行，不能单独作为删除换行的依据。
22. 对 gallery、button、splitbutton、dropdownbutton 的视觉还原必须检查控件类型、下拉箭头、文字换行、hover 区域、图标文字是否重叠、同组按钮对齐。没有完成运行后视觉检查时，不得声明“与源应用对标完成”。
23. 源快照中已有 `displayMode`、`controlType`、`interaction`、`textLines`、`hasIcon`、`checked`、`section`、`column`、`row` 时，生成器必须直接使用这些字段；不得因为文本长短、统一模板或插件默认布局而重猜。
24. 视觉对标必须有目标运行证据，优先使用 `target_ribbon_snapshot.json`。静态 JSON、`.slapp.code == app.jl`、Julia `include OK` 只能证明结构或运行性，不能证明大/小按钮、图标、文字重叠、下拉箭头和布局对齐。
25. 如果无法取得源快照或目标运行时快照 `target_ribbon_snapshot.json`，应把结果标记为 `unknown` 或“待视觉验收”，不得写成 `pass`。目标截图不是必需项，只作为可选补充证据。

## 8. 运行时横向间距规则

1. Ribbon 运行时横向间距统一使用 `4 CSS px` 作为基准。
2. section 分组线到第一个组件外框之间必须是 `4 CSS px`。
3. 最后一个组件外框到 section 分组线之间必须是 `4 CSS px`。
4. 相邻组件外框之间、相邻 column 外框之间必须是 `4 CSS px`。
5. `matlab-gallery` 的可见 item 外框之间也必须使用 `4 CSS px`，与普通组件间距一致。
6. 普通按钮、`splitbutton`、`dropdownbutton`、`radio` / `checkbox` stack 等内容型组件应按内容自适应宽度布局，不应通过固定 section / column `width` 撑开横向空白。
7. Gallery 相关宽度可以作为运行时宽度约束保留，例如 `matlab-gallery` 所在 section / column 的宽度预算、`visibleCount`、`itemWidth`、`frameWidth` 等用于响应式可见项分配的字段。
8. 源应用明确给出字段型 `stack` 列宽时，该 `column.width` 也是运行时约束：适用于由 `label` / `spacer` / `editbox` / `combobox` / 字段型 `dropdown` / `checkbox` 组成且至少包含一个交互字段的列，使字段控件继承源列宽。
9. `.slapp.figure.toolstrip` 可以继续保存设计态 JSON；生成 `app.jl` 运行代码时，应保留 gallery 和字段型 `stack` 列的有效 `width`，不得输出普通命令列的设计态固定宽度。
10. 如果同一个 section 中同时包含 `matlab-gallery` 和普通命令列，压缩策略只能减少 gallery 的可见 item 数；普通命令列应保持内容宽度，不得用历史设计态固定宽度制造额外空槽。
11. 生成 `matlab-gallery` 的 `column.width` 或 `frameWidth` 时必须按运行时槽位计算，不得手写估计值。最小宽度公式为：

```text
requiredWidth =
itemWidth * visibleCount
+ 4 * (visibleCount - 1)
+ 18
+ 2
+ 1
+ 12
```

其中 `4` 是 item 间距，`18` 是右侧下拉槽宽，`2` 是下拉槽间距，`1` 是边框余量，`12` 是安全余量。生成器必须保证 `column.width >= requiredWidth` 或 `frameWidth >= requiredWidth`，否则右侧下拉槽可能被裁剪。
12. gallery item、按钮和菜单项的换行必须来自源应用显示结构或可验证源规范。不得仅根据英文空格自动猜测换行；也不得在源应用明确两行显示时删除 `\n` 并通过增大 `itemWidth`、`width` 或其它布局字段掩盖文本挤压。

## 9. 组件化运行代码规则

1. `.slapp.figure.toolstrip` 继续作为设计态 JSON 真相源；保存、打开、打包流程不需要迁移历史 schema。
2. 新生成的 `app.jl` / `.slapp.code` 必须使用组件化 ribbon 运行代码：
   - `TyAppDesigner.uitoolstrip(app.UIFigure)`
   - `TyAppDesigner.uitoolstriptab(app.Toolstrip)`
   - `TyAppDesigner.uitoolstripsection(app.<Tab>)`
   - `TyAppDesigner.uitoolstripcolumn(app.<Section>)`
   - control 优先按类型使用 `TyAppDesigner.uitoolstripbutton(...)`、
     `TyAppDesigner.uitoolstripeditbox(...)`、`TyAppDesigner.uitoolstripdropdown(...)`、
     `TyAppDesigner.uitoolstripmatlabgallery(...)` 等快捷函数
   - 仅当控件类型没有对应快捷函数或必须使用高级协议字段时，才使用
     `TyAppDesigner.uitoolstripcontrol(app.<Column>)`
   - 对已知普通组件生成 `uitoolstripcontrol(...)` 应作为审查项处理
3. 新生成运行代码不得把整棵 ribbon 写成 `app.<Figure>.Toolstrip = Dict{String,Any}(...)`。
4. Ribbon 下拉项、gallery item 等 item 实体应优先生成 `TyAppDesigner.ToolstripItem[...]`，不要退回 `Any[Dict{String,Any}(...)]`。
5. 为兼容运行时复合业务载荷，`commandDescriptor`、`commandState`、`commandContext` 等内部字段仍可使用 `Dict`；但这些 `Dict` 不能替代 ribbon 实体本身。
6. 旧的 `app.<Figure>.Toolstrip = Dict{String,Any}(...)` 产物可以继续作为兼容输入运行；新生成内容不得再产生这种形式。
7. 生成 `app.jl` / `.slapp.code` 时，带换行的显示文本应生成单行转义字符串，例如 `"Import\nChannel"`；不要生成跨行 `raw"Import ... Channel"`，以免 `.slapp.code` 可读性下降并干扰后续审查。
8. 生成 `app.jl` / `.slapp.code` 时，Ribbon 图标的 `IconSrc` 不应直接内联很长的 `data:image/...;base64,...` 字符串；应优先写入 `resources/ribbon-icons` 并生成短引用，例如 `TyAppDesigner.ribbon_icon_src_from_file(joinpath(@__DIR__, "resources", "ribbon-icons", "...png"))`。
9. `.slapp.figure.toolstrip` 中的设计态图标数据可以继续保留 `iconSrc` data URL，用于打开工程后直接预览；运行代码精简不应迁移或删除设计态 JSON 字段。

## 10. 回调载荷规则

1. `.slapp` / 设计器生成 app 的控件回调参数使用 `event.Item` 承载 toolstrip control 的当前状态和交互载荷。
2. 通用控件回调应从 `event.Item.CommandId`、`event.Item.Text`、`event.Item.ControlType`、`event.Item.Value` 读取组件身份与值。
3. 菜单项和 gallery item 应从 `event.Item.LastMenuItem` 读取实际选项；gallery 还可从 `event.Item.GallerySource` 区分可见 item 点击与 popup 选择。
4. 生成器不得仅为 gallery 特判 `event.Item`，普通 button、dropdown/combobox、editbox、toggle、checkbox 与 radio 也必须使用同一设计器事件层级。

## 11. 对标能力说明规则

1. 对标声明必须区分“结构/语义/交互已对齐”和“像素级视觉一致”。
2. 当 Syslab 正式组件在外观、键盘交互、自动完成或状态行为上不能完全复现源应用时，生成结果必须列出差异。
3. 不得因使用了语义最接近的 Syslab 控件就宣称其外观与源应用完全一致。
4. 视觉结论必须来自 `visual_audit_report.json` 或等价运行后审计记录。报告中的 `unknown` 不是通过，必须单独列出。

## 12. 推荐引用方式

如果要在提示词中复用这份规则，建议写成：

- “除显式任务要求外，统一遵守 `ribbon-rules.md` 中的通用规则。”

## 13. 生成后审查

如果要防止外部生成器退回到 HTML 假 ribbon 或多真相源混用，生成后还应执行：

- `../workflow/generation-gate.md`
- `ribbon-validation.md`
