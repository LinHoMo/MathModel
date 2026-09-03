---
name: syslab-app-designer
description: Syslab App Designer 子技能：用于生成、审查和调试 `.slapp` 工程、普通 UI 组件与 App Designer ribbon/toolstrip，重点覆盖工程结构、普通组件选型、组件属性、组件回调、布局、ribbon 结构、回调通道、运行时消息链路和生成代码。
---

# App Designer
如果任务涉及 Julia 代码生成、运行或调试，应继续遵循顶层 Syslab skill 的 Ty 优先与本地文档优先原则。

本技能面向 Syslab App Designer 的 `.slapp` 工程结构、普通 UI 组件、ribbon/toolstrip 文档和生成任务。

`.slapp` 工程结构文档入口：`slapp-structure.md`。

普通 UI 组件正式文档入口：`components/README.md`。

Ribbon 正式文档入口：`ribbon/README.md`。

读取规则：

- 如果任务涉及 `.slapp` 生成、修改、审查、打开、运行或调试，必须先读 `slapp-structure.md`。
- 如果任务涉及创建、选择、修改、生成、审查或调试普通 UI 组件，先读 `components/README.md`，再按该文件的阅读路径进入具体组件文档。创建普通组件先以组件库拖拽结果为基线，再应用用户明确要求或完成任务必不可少的修改；交付完整 `.slapp` / `app.jl` 工程时，所有修改都必须通过实际运行验收。
- 如果任务涉及 ribbon 生成、修改、审查或调试，先读 `ribbon/README.md`，再读 `ribbon/workflow/generation-gate.md`。
- 同一任务同时涉及普通组件和 ribbon 时，先读 `slapp-structure.md`，再分别读取 `components/README.md` 与 `ribbon/README.md`。
- 对 ribbon 任务，再按 `ribbon/README.md` 的阅读路径进入当前任务需要的具体文档。
- 不要一次性加载 `components/` 或 `ribbon/` 下所有规则文档。
- 只读取当前任务真正需要的文件。
