# Ribbon 任务模板

这份文档用于指导你如何向生成器提交一个 TyAppDesigner ribbon 生成任务。

如果目标是对标源应用，建议先一起阅读：

- `../reference/components.md`
- `../reference/layout-rules.md`
- `../rules/ribbon-rules.md`
- `../source/source-generation.md`
- `../rules/ribbon-validation.md`

如果调用方不能提供固定磁盘路径，推荐先让生成器在当前仓库内搜索：

- `ribbon/README.md`
- `../reference/api.md`
- `../reference/components.md`
- `../reference/layout-rules.md`
- `../rules/ribbon-rules.md`

## 文档定位

这份文档回答的是：

- 应该怎样向生成器提交 ribbon 生成任务
- 哪些输入必须补齐
- 提示词里最值得明确强调什么

这份文档不负责：

- 代替 API 文档定义正式字段契约
- 代替 golden spec 去保存某个具体工具的最终布局配方

## 必填输入

向生成器提交任务时，至少要明确这些内容：

1. app 名称
2. tabs
3. sections / groups
4. 控件文案
5. command id / callback 名称
6. 图标策略
   - `iconSrc`
   - `iconKind`
   - 需要先通过 `ribbon_icon_src_from_file(path)` 转换的本地图标
   - 源应用内部图标标识如何解析为可渲染 `iconSrc`
   - gallery item / 菜单 item 是否需要逐项图标
7. 是否允许 `preset`
8. 输出类型
   - `.slapp` 工程
9. 是否要求接近某个参考 UI

如果这些信息缺失，生成器大概率会生成一份更泛化的 ribbon 结果。

## 生成前 layout model

任何源应用对标任务，在生成 spec 或 `.slapp` 前必须先建立 source layout model。任何从零设计任务，也应建立 target layout model。模型可以作为单独 JSON、审计报告片段或生成器内部显式步骤存在，但交付说明必须能说明它来自哪些输入或证据。

layout model 至少包含：

- tab / section / column 顺序
- 每个 column 内控件数量和 command 控件数量
- 每个控件的源 class / role / control type；没有源应用时记录目标控件类型
- `Button`、`DropDownButton`、`SplitButton`、`ListItemWithCheckBox`、gallery item 等源类型；没有源应用时记录目标映射决策
- 每个控件的 `displayMode` / 大小按钮证据或目标设计依据
- 每个菜单项的 checkbox / radio / toggle / checked 语义或目标状态策略
- 每个控件和 item 的图标来源
- 源应用对标任务中，每个关键字段的 `evidenceSource`：`liveSnapshot`、`sourceCode`、`screenshot`、`manual`、`historySpec` 或 `unknown`

没有 source layout model 时，不得声明“按源应用对标完成”。源菜单证据、图标证据或 displayMode 证据缺失时，必须标记为 `unknown`，不得靠文本、图标大小或固定模板推断。从零设计任务不得伪造源证据。

如果目标是“尽量对标某个现有产品的 ribbon”，除了上面的必填项，最好再补：

1. `source_ribbon_snapshot.json` 或等价源运行时证据包
2. 至少一份可直接复用的 golden spec
3. 哪些 section 必须是 gallery / matrix / stack
4. 哪些按钮必须是 `displayMode = "large"`
5. 哪些 splitbutton 必须使用两行文案和指定 `layoutVariant`
6. 各 section / column 的宽度预算
7. 参考产品里每个 section 的列模型
8. 字段区、单选区、gallery 区各自的对齐方式
9. 哪些位置是空白占位，而不是缺少控件
10. 源应用源码路径、截图或录屏证据
11. 目标运行时快照 `target_ribbon_snapshot.json` 的采集方式；截图只是可选补充证据

## 给生成器的硬规则

通用规则统一收敛在：

- [rules/ribbon-rules.md](../rules/ribbon-rules.md)

给生成器提交任务时，至少要额外强调这些任务侧要求：

1. 所有业务文案、图标、命令、菜单项都必须写在 spec 里。
2. 如果目标是 `.slapp` / 设计器生成 app，要在任务里明确写出来。
3. 如果目标是对标源应用，要同时附上 `source_ribbon_snapshot.json`、源码路径、golden spec、截图等布局证据；没有源快照时不得声明对标完成。
4. 对复杂 ribbon 行为，优先要求最小可工作的模式，不要让生成器一次性拼装推测性大结构。
5. 运行代码中已知组件应使用 `uitoolstripbutton`、`uitoolstripdropdown` 等具体构造函数；`uitoolstripcontrol` 只用于兼容或高级字段场景。
6. 生成后必须优先产出目标运行时快照 `target_ribbon_snapshot.json`，并用 `visual_audit_report.json` 区分 `pass`、`fail`、`unknown` 与 `accepted_difference`。不要求截图；截图只是可选补充证据。
7. 如果当前 Syslab App Designer 插件提供 `syslab.app-designer.open(filePath)`、`syslab.app-designer.runSlapp(filePath)`、`syslab.app-designer.exportRuntimeRibbonSnapshot(filePath)` 或组合入口 `syslab.app-designer.auditSlapp(filePath)`，生成后目标运行时验收应优先走这些命令。`runSlapp` 必须复用设计器原有“运行”命令链路，不得用直接 `include(app.jl)` 或直接 `executeFile(app.jl)` 替代。
8. 如果当前环境需要从脚本或 AI 自动化触发上述命令，应读取 Syslab App Designer 插件的本机 IPC 发现索引：Windows 优先为 `%LOCALAPPDATA%\TongYuan\SyslabAppDesigner\automation\syslab-app-designer-automation.json`，否则为 `%USERPROFILE%\.syslab-app-designer\automation\syslab-app-designer-automation.json`；Linux/macOS 优先为 `$XDG_RUNTIME_DIR/syslab-app-designer/automation/syslab-app-designer-automation.json`，否则为 `$HOME/.syslab-app-designer/automation/syslab-app-designer-automation.json`。通过其中 `latestDiscoveryFile` 指向的 `http-over-ipc` 自动化入口调用 `auditSlapp`。不要假设 `Syslab.cmd` 能直接执行扩展 command，也不要再依赖系统临时目录里的旧 HTTP 发现文件。
9. 生成前先执行 [workflow/generation-gate.md](generation-gate.md) 的门禁；生成后按同一门禁检查唯一主 `.slapp`、图标渲染字段、菜单项状态、item 图标和 unknown 状态。

## Gallery 分组输入要求

如果源应用包含 `gallery` / `matlab-gallery`，给生成器的任务中必须显式提供或要求提取以下信息：

1. gallery 的完整扁平 item 列表，用于生成 `items`。
2. popup 分组来源，用于生成 `menuGroups`：
   - runtime snapshot 中的 `Popup.children` / `GalleryCategory`
   - 或 MATLAB 源码中的 `GalleryCategory(...)` / `popup.add(category)`
   - 或运行时对象树、配置表、截图等可验证证据
3. 每个分组的 `title`、分组顺序和组内 item 顺序。
4. group item 到原始 `items[]` 的匹配键，优先使用 `value`，其次使用 `tag` / `label`。
5. 如果 `source_ribbon_snapshot.json` 只有扁平 `items`、没有 popup category，不得直接交给生成器当作“无分组”证据；必须继续补充源码路径、运行时 popup 抽取结果或明确的无分组证据。

生成器必须按以下方式表达分组：

- 保留完整 `items` 扁平列表。
- 额外生成 `menuGroups`。
- `menuGroups[].items[]` 从 `items[]` 复制完整 item，不得只写 `label` / `value`。
- `.slapp.figure.toolstrip`、`.slapp.code` 和外部 `app.jl` 必须同步。

## 布局规则必须前置执行

生成 ribbon 时，必须先读取并遵守 `../reference/layout-rules.md` 和 `../rules/ribbon-rules.md`。不得先按控件列表、文本、图标或业务分组生成 ribbon，再把布局规则当作事后建议。

生成和同步顺序必须为：

1. 建立 source layout model 或 target layout model。
2. 基于 layout model 生成 `.slapp.figure.toolstrip`。
3. 对 `.slapp.figure.toolstrip` 执行 layout audit，并输出 `layoutRuleStatus`。
4. 只有 `layoutRuleStatus.status = "pass"` 后，才生成或同步 `app.jl` / `.slapp.code`。
5. 如果 layout audit 失败，必须先修正 `.slapp.figure.toolstrip`；不得只用 `app.jl`、运行态代码或后处理说明补救。

生成前必须先产出 source layout model 或 target layout model，不能直接从控件清单生成目标 ribbon。布局模型至少包含：

- tab / section / column 顺序
- 每个 column 内的控件列表
- 每个 column 的 `columnKind`、`commandCount`、`largeCommandCount`、`allowedDisplayMode`
- 每个控件的源类型或目标控件类型、下拉语义、图标状态、checked / radio 状态
- 源应用中的 `displayMode` / 大小按钮证据，或新设计中的目标显示层级依据
- 目标映射决策：
  - 单个 command column -> 可保留 `large`
  - 多个 command 同 column -> `column.layout = "stack"`，且所有 command `displayMode = "small"`
  - 字段型 column -> `stack` + 字段控件
  - gallery -> `gallery` / `matlab-gallery`
- 每个映射决策的证据或依据：运行时快照、源码、截图、golden spec、目标设计输入或 `unknown`

如果没有源布局模型，禁止声明“按源应用对标完成”。如果某个 column 无法判断布局语义，必须标记为 `unknown`，不得靠文本、图标大小或固定模板推断。

生成前必须先判断每个 section / column 的布局语义，包括：

- 单命令 column
- 多命令 column
- 字段型 stack column
- gallery column
- radio / checkbox stack

然后再创建目标 column 和控件。如果源布局信息不足以判断目标布局，必须标记为 `unknown` 并停止自动声明对标完成。

## 通用提示模板

```text
我有一套 TyAppDesigner 的通用 ribbon/toolstrip 插件。
这套插件只能通过声明式 API 使用。
不要修改渲染器内部实现、前端组件或 DOM 行为。

请为下面的目标 app 生成一份 ribbon/toolstrip 定义。

要求：
1. 只返回 JSON/spec。
2. 不要返回 Vue、HTML、CSS、JS 或 Julia 实现代码。
3. 使用结构：toolstrip -> tab -> section -> column -> control。
4. 每个元素都必须有稳定 id。
5. 统一遵守 `../rules/ribbon-rules.md` 里的通用规则。
6. 只能使用 `../reference/components.md` 中列出的公开控件类型。
7. 所有业务文案、命令、图标和菜单项都必须留在 spec 中。
8. 如果提供了本地图标，默认它们会先通过 ribbon_icon_src_from_file(path) 转换，再写入 iconSrc。
9. 如果目标是 .slapp / 设计器生成 app，要在结果中显式按设计器运行链约束处理。
10. 如果目标是对标源应用，要先根据源应用源码、golden spec、截图分析页面布局，再生成 spec。
11. 已知控件生成运行代码时，使用 `../reference/components.md` 中对应的具体构造函数，不要统一退回 `uitoolstripcontrol`。

目标 app：
- App name: <APP_NAME>
- Tabs: <TAB_LIST>
- Sections/groups: <SECTION_LIST>
- Visual reference: <NONE or REFERENCE DESCRIPTION>
- Output type: .slapp

生成前先给出或内部建立 source layout model 或 target layout model，至少记录每个 column 的控件数量、源 class 或目标控件类型、displayMode 证据或目标依据、菜单项 checked/radio/toggle 语义、item 图标来源。源应用对标任务还必须记录 evidenceSource；没有证据的字段标为 unknown，不得声明对标完成。

除非明确要求别的格式，否则只返回 JSON。
```

## 修改已有工程

如果调用方想修改一个现有 ribbon，应直接读取和修改现有 `.slapp.figure.toolstrip`
及其 `callbackFunctions`，再通过设计器重新生成并运行验证。

