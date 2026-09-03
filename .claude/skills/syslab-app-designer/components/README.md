# 普通 UI 组件文档

本目录是 Syslab App Designer 普通 UI 组件的 skill 引用文档包。普通组件指 `figure/button/dropdown/html/table/gridlayout` 等非 ribbon/toolstrip 组件。

权威来源是当前实现源码：

- `tyappdesigner.jl/src/uifigureBasedApps/*.jl`
- `tyappdesigner.jl/src/app_protocol.jl`
- `app-designer/webview/src/uicomponents/*/meta.js`
- `app-designer/webview/src/uicomponents/*/props.js`

## 核心规则

- 创建普通组件的默认语义就是从 App Designer 组件库拖入该组件。只要任务涉及创建或生成普通组件，必须先读 [designer-parity.md](designer-parity.md)，按组件库默认对象生成；不需要用户额外说明“和面板一样”。
- 对外可创建组件以 `meta.js` 是否具有 `group` 字段为准。`figure`、`buttongroup`、`radiobutton`、`togglebutton`、`tab` 是内部结构节点，不作为独立面板组件推荐或生成。
- 用户说“创建单选按钮”“创建切换按钮”或“创建选项卡”时，默认分别创建单选按钮组、切换按钮组或选项卡组；只有明确要求向已有组合组件增加子项时，才使用内部节点。
- 创建组件时先以组件库拖拽结果为基线，再应用用户明确要求或完成任务必不可少的修改。与任务目标无关的属性必须保持拖拽默认值。
- 任务必要修改同样必须满足设计态结构、Julia 类型和运行时代码契约。不能把 JavaScript 对象字符串化结果直接写入 Julia，也不能因为修改是任务所需就跳过运行验收。
- 创建或生成完成后，必须按 [designer-parity.md](designer-parity.md) 中的“生成验收规则”自检；任一必需项不满足都不能视为完成。
- 生成完整 `.slapp` / `app.jl` 工程后，必须确认修改首先落在 `.slapp` 的结构化字段中，再同步 `.slapp.code` 与 `app.jl`。验收优先以 App Designer 打开 `.slapp` 并 Run 后重新生成的结果为准；只修改或只运行外部 `app.jl` 不能视为完成。仅回答代码片段或规则说明时，至少检查 Julia 字面量、属性类型和组件边界，并明确说明未执行完整工程运行验收。
- 生成 Julia 代码时统一使用 module-qualified 调用：`TyAppDesigner.uibutton(...)`、`TyAppDesigner.uihtml(...)`，不要依赖普通组件函数被 `export`。
- 在 App 结构体中使用 `TyAppDesigner.<JuliaType>` 和 `TyAppDesigner.create_<lowercase_type>()` 初始化组件字段。
- 回调属性写函数名字符串，例如 `ButtonPushedFcn="RunButtonPushed"`；回调实现写 `function RunButtonPushed(app,event)`。
- 不手写运行时 `Id`、`Type`、`Parent`、`Children`。构造函数会生成 `Id`、设置 `Type`、拼接 `Parent` 并把子组件加入父组件 `Children`。
- `.slapp` 工程结构仍先遵守 `../slapp-structure.md`；普通组件细节再读本目录文档。

## 阅读路径

生成或审查普通组件代码：

1. 创建或生成任何普通组件时，先读 [designer-parity.md](designer-parity.md)。
2. 读 [component-map.md](component-map.md)，确认前端 type、Julia 类型和构造函数。
3. 读 [properties.md](properties.md)，确认构造参数、可改属性和特殊约束。
4. 如果涉及交互，读 [callbacks.md](callbacks.md)。
5. 如果涉及容器或自适应布局，读 [layout.md](layout.md)。

HTML 组件通信：

1. 读 [html.md](html.md)。
2. 按需再读 [callbacks.md](callbacks.md) 中 HTML 回调规则。

App 内部进度条：

1. 读 [progressbar.md](progressbar.md)。
2. 按需读 [properties.md](properties.md) 中 ProgressBar 字段约束。

## 最小生成样式

```julia
app.Button = TyAppDesigner.uibutton(app.UIFigure)
app.Button.Position = [100, 100, 120, 30]
app.Button.ButtonPushedFcn = "ButtonPushed"

function ButtonPushed(app, event)
    app.Button.Text = "Done"
end
```

设计器生成的完整 App 仍应包含 `using TyAppDesigner`、`using ObjectOriented`、`@oodef mutable struct App`、`createComponents(app)`、`initApp(app)` 和 `TyAppDesigner.registerApp(app, app.UIFigure)`。
