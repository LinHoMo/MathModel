# HTML 组件

`HTML` 组件用于在 Syslab App Designer 中嵌入自定义 HTML/CSS/JavaScript 页面，并支持 Syslab 与页面之间的数据和事件通信。

构造函数：

```julia
app.HTML = TyAppDesigner.uihtml(app.UIFigure;
    HTMLSource="",
    HTMLSourceType="inline",
    ResourceBasePath="",
    Data=missing,
    DataChangedFcn="",
    HTMLEventReceivedFcn="",
    Position=[20, 20, 480, 320],
)
```

## HTMLSource

### Inline HTML

```julia
app.HTML.HTMLSource = """
<!DOCTYPE html>
<html>
<body>
  <h1>Hello Syslab</h1>
</body>
</html>
"""
```

### 本地 HTML 文件

推荐使用 `@__DIR__` 生成稳定路径：

```julia
app.HTML.HTMLSource = joinpath(@__DIR__, "resources", "parent.html")
app.HTML.HTMLSourceType = "file"
```

本地 HTML 可以引用相对资源：

```html
<link rel="stylesheet" href="parent.css">
<script src="parent.js"></script>
<img src="child/child_image.svg">
```

## Data 通道

Data 适合同步当前状态、表单值、配置、选择结果。

设计态和运行态必须分别使用正确表示：

- `.slapp` 顶层 `data` 与 `state.data` 保存 JSON 对象或数组。
- Julia 运行时代码把 JSON 对象递归生成为 `Dict{String,Any}(...)` 或 `Dict(...)`，把数组递归生成为合法 Julia 数组，例如 `Any[...]`。
- 字符串值必须生成 Julia 合法字符串字面量，包含引号并正确转义；数字、布尔值和 `nothing` 保持对应 Julia 值。
- 禁止把 JavaScript 对象隐式转字符串后写入 Julia；`[object Object]` 是非法生成结果。

Syslab 发送 Data 到 HTML：

```julia
app.HTML.Data = Dict("source" => "Syslab", "value" => 123)
```

对应 `.slapp` 设计态示例：

```json
{
  "data": {
    "source": "Syslab",
    "value": 123
  },
  "state": {
    "data": {
      "source": "Syslab",
      "value": 123
    }
  }
}
```

HTML 接收：

```js
function setup(htmlComponent) {
  htmlComponent.addEventListener("DataChanged", function (event) {
    console.log(event.Data);
  });
}
```

HTML 发送 Data 到 Syslab：

```js
htmlComponent.Data = {
  source: "JavaScript",
  value: 123
};
```

Syslab 回调：

```julia
app.HTML.DataChangedFcn = "HTMLDataChanged"

function HTMLDataChanged(app, event)
    data = event.Data
end
```

## Event 通道

Event 适合按钮点击、命令提交、一次性动作通知。

HTML 发送事件到 Syslab：

```js
htmlComponent.sendEventToSyslab("ButtonClicked", {
  id: "run",
  value: 456
});
```

Syslab 回调：

```julia
app.HTML.HTMLEventReceivedFcn = "HTMLHTMLEventReceived"

function HTMLHTMLEventReceived(app, event)
    eventName = event.HTMLEventName
    eventData = event.HTMLEventData
end
```

Syslab 发送事件到 HTML：

```julia
payload = Dict("source" => "Syslab", "message" => "Hello HTML")
TyAppDesigner.sendEventToHTMLSource(app.HTML, "DisplayFromSyslab", payload)
```

HTML 接收：

```js
function setup(htmlComponent) {
  htmlComponent.addEventListener("DisplayFromSyslab", function (event) {
    console.log(event.Data);
  });
}
```

`sendEventToHTMLSource` 会更新 `HTMLEventName`、`HTMLEventData`、`HTMLEventSerial`，其中 serial 用于保证连续发送同名事件也能被页面收到。

## HTML 页面 API

HTML 页面中定义全局 `setup` 函数：

```js
function setup(htmlComponent) {
  htmlComponent.addEventListener("DataChanged", function (event) {
    console.log(event.Data);
  });

  document.getElementById("send").addEventListener("click", function () {
    htmlComponent.sendEventToSyslab("SendButtonPushed", {
      time: new Date().toLocaleTimeString()
    });
  });
}
```

`htmlComponent` 提供：

- `htmlComponent.Data`
- `htmlComponent.addEventListener(name, callback)`
- `htmlComponent.removeEventListener(name, callback)`
- `htmlComponent.sendEventToSyslab(name, data)`

## 选择 Data 还是 Event

| 场景 | 使用 |
|---|---|
| 当前值、配置、表单状态、选择结果 | `Data` |
| 点击、提交、命令、一次性动作 | `sendEventToSyslab` / `sendEventToHTMLSource` |

## 常见错误

- 本地 HTML 路径写相对当前工作目录；应使用 `joinpath(@__DIR__, ...)`。
- HTML event 回调中读取 `event.Data`；事件通道应读取 `event.HTMLEventName` 和 `event.HTMLEventData`。
- 忘记定义全局 `setup(htmlComponent)`，导致页面无法绑定 Syslab 通信对象。
- 高频大数据通过 `Data` 连续传输；`Data` 更适合状态同步，不适合大量高频数据流。
- 把 `.slapp` 中的 Data 对象生成成 `app.HTML.Data = [object Object]`；应生成合法 `Dict(...)`。
