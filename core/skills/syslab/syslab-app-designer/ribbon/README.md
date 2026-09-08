# Ribbon 文档

本目录是 Syslab App Designer ribbon/toolstrip 的正式对外文档包。

文档只保留 ribbon 生成、结构契约、回调绑定、控件映射、验证规则和示例规格相关内容。开发草稿、重复语言版本、历史问题复盘和内部收尾项不在本目录对外暴露。

## 适用场景

- 生成或审查 Syslab App Designer ribbon/toolstrip。
- 从源应用对标生成 ribbon。
- 为 ribbon 组件补齐 `buttonPushedFcn`、`valueChangedFcn`、`commandInvokedFcn` 等回调入口。
- 调试 ribbon 点击、下拉选择、gallery item 等交互无响应问题。
- 检查 App Designer 前端、扩展层、JSON-RPC、Julia 回调之间的消息链路。
- 维护 `app.jl`、`.slapp`、插件前端或运行时回调协议中的 ribbon 相关内容。

## 工作原则

- 任何 ribbon 生成、修改或审查任务，先读 [workflow/generation-gate.md](workflow/generation-gate.md)。
- ribbon 布局、资源和图标必须来自可验证的源应用定义或资源目录。
- 不允许猜测 ribbon 布局，不允许用兜底图标静默替代缺失资源。
- 源图标线索不是图标完成状态；只有生成可渲染 `iconSrc` / `IconSrc` 才算图标完成。
- 可交互 ribbon 组件必须有回调字段；没有真实业务时也要生成显式占位回调。
- Syslab 插件负责把交互事件送回 Julia；具体业务应在生成的 `app.jl` 中实现。
- 点击无响应时，优先检查事件是否从前端进入扩展层，再检查是否送达 Julia 回调。
- 事件对象传入 Julia 前不应包含协议不支持的 `null` 字段。
- 只读取当前任务真正需要的规则文档，不要一次性加载整个文档包。

## 目录布局

入口：

- [README.md](README.md)：文档包入口和阅读路径。

生成流程：

- [workflow/generation-gate.md](workflow/generation-gate.md)：生成前建模、生成后自检和一票否决门禁。
- [workflow/generation-task.md](workflow/generation-task.md)：提交 ribbon 生成任务时需要提供的信息、输出格式和约束。

API 与结构参考：

- [reference/api.md](reference/api.md)：ribbon API、结构字段和运行时约束。
- [reference/components.md](reference/components.md)：实际组件、具体构造函数、参数与回调选型。
- [reference/layout-rules.md](reference/layout-rules.md)：section / column / 字段列宽 / gallery 的布局规则。

源应用对标：

- [source/source-generation.md](source/source-generation.md)：从源应用生成 ribbon 时必须遵守的规则。
- [source/icon-resolution.md](source/icon-resolution.md)：源应用图标线索解析、sprite 裁剪、渲染字段和失败门禁。
- [source/runtime-snapshot.md](source/runtime-snapshot.md)：源应用运行时快照、目标运行截图和视觉审计契约。

## 规则文档

- [rules/ribbon-rules.md](rules/ribbon-rules.md)：ribbon 通用规则。
- [rules/ribbon-control-selection.md](rules/ribbon-control-selection.md)：控件选型规则。
- [rules/ribbon-validation.md](rules/ribbon-validation.md)：生成后验证规则。

## 示例文档

- [examples/ribbon-example-spec.json](examples/ribbon-example-spec.json)：可复用的 ribbon 示例规格。

## 阅读路径

生成新 ribbon：

1. 先读 [workflow/generation-gate.md](workflow/generation-gate.md)，确认生成前模型和生成后门禁。
2. 阅读 [reference/api.md](reference/api.md) 与 [reference/components.md](reference/components.md)，确认运行模型和具体组件。
3. 阅读 [reference/layout-rules.md](reference/layout-rules.md) 与 [rules/ribbon-rules.md](rules/ribbon-rules.md)，确认布局和硬规则。
4. 使用 [workflow/generation-task.md](workflow/generation-task.md) 组织输入和输出要求。

从源应用对标生成：

1. 先读 [workflow/generation-gate.md](workflow/generation-gate.md)，确认 source layout model、唯一主产物和高频错误门禁。
2. 阅读 [reference/components.md](reference/components.md)、[source/source-generation.md](source/source-generation.md)、[source/icon-resolution.md](source/icon-resolution.md)、[source/runtime-snapshot.md](source/runtime-snapshot.md) 与 [reference/layout-rules.md](reference/layout-rules.md)。
3. 按需阅读 [rules/ribbon-control-selection.md](rules/ribbon-control-selection.md)。
4. 生成后按 [rules/ribbon-validation.md](rules/ribbon-validation.md) 做验证。

调试点击或回调：

1. 先看 [workflow/generation-gate.md](workflow/generation-gate.md) 中的生成后门禁，排除主产物、图标字段、菜单状态和布局硬错误。
2. 再看 [source/source-generation.md](source/source-generation.md) 中的回调生成原则。
3. 最后看 [reference/api.md](reference/api.md) 中的设计器运行链约束。

## 输出期望

处理 App Designer 或 ribbon 任务时，应说明：

- 修改了哪些工程文件或生成产物。
- 是否涉及 Syslab 安装目录或仅涉及外部插件/工程目录。
- 回调链路验证到了哪一层。
- 如果有无法实现的源应用业务功能，应生成或保留明确的占位反馈。
