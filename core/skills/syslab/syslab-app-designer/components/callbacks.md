# 普通组件回调

普通组件回调字段存储的是函数名字符串。生成代码时，组件属性和函数定义必须同时存在。

```julia
app.RunButton.ButtonPushedFcn = "RunButtonPushed"

function RunButtonPushed(app, event)
    app.StatusLabel.Text = "Running"
end
```

## 回调函数签名

- 普通交互回调：`function CallbackName(app, event)`
- Startup 回调：`function StartupFcn(app)`，不接收 `event`
- `.slapp.callbackFunctions[].code` 只写函数体，不写外层 `function ... end`

运行时收到前端事件后，会根据 `event.Item` 更新对应组件实例，再读取该组件回调字段中保存的函数名并调用。

## 回调字段速查

| 组件 | 回调字段 | 触发场景 |
|---|---|---|
| `Button` | `ButtonPushedFcn` | 按钮点击 |
| `CheckBox` | `ValueChangedFcn` | 勾选状态变化 |
| `DropDown` | `ValueChangedFcn` | 选择值变化 |
| `DropDown` | `DropDownOpeningFcn` | 下拉打开 |
| `EditField` | `ValueChangedFcn` | 文本提交后变化 |
| `EditField` | `ValueChangingFcn` | 文本输入中变化 |
| `NumericEditField` | `ValueChangedFcn` | 数值提交后变化 |
| `NumericEditField` | `ValueChangingFcn` | 数值输入中变化 |
| `TextArea` | `ValueChangedFcn` | 多行文本提交后变化 |
| `TextArea` | `ValueChangingFcn` | 多行文本输入中变化 |
| `Spinner` | `ValueChangedFcn` | 数值变化 |
| `Slider` | `ValueChangedFcn` | 滑块值变化 |
| `Radio Button Group` / `Toggle Button Group` | `SelectionChangedFcn` | 组内选择变化 |
| `TabGroup` | `SelectionChangedFcn` | 当前 tab 变化 |
| `Table` | `CellEditCallback` | 单元格编辑 |
| `Table` | `DisplayDataChangedFcn` | 显示数据变化 |
| `Table` | `SelectionChangedFcn` | 选中单元变化 |
| `Image` | `ImageClickedFcn` | 图片点击 |
| `Menu` | `MenuSelectedFcn` | 菜单选择 |
| `HTML` | `DataChangedFcn` | HTML 页面设置 `htmlComponent.Data` |
| `HTML` | `HTMLEventReceivedFcn` | HTML 页面调用 `sendEventToSyslab` |
| `UIAxes` | `ButtonDownFcn` | 坐标区点击 |

`Label`、`Panel`、`GridLayout`、`ProgressBar` 通常不作为用户交互回调入口。`ButtonGroup`、`RadioButton` 和 `ToggleButton` 是组合组件内部节点，不作为独立回调组件推荐；只有在实现 `radiobuttongroup` 或 `togglebuttongroup` 时，才通过内部 `ButtonGroup.SelectionChangedFcn` 承载组内交互。`TabGroup.SelectionChangedFcn` 用于面板可创建的选项卡组切换；`UIAxes.ButtonDownFcn` 用于坐标区点击。

## HTML 回调别名

`HTML` 运行时兼容 `HtmlEventReceivedFcn`，内部会映射到 `HTMLEventReceivedFcn`。新代码统一使用全大写前缀：

```julia
app.HTML.HTMLEventReceivedFcn = "HTMLHTMLEventReceived"
```

回调中读取：

```julia
function HTMLHTMLEventReceived(app, event)
    name = event.HTMLEventName
    data = event.HTMLEventData
end
```

## `.slapp` 生成规则

如果普通组件节点的 `callbackFcns` 或运行时属性绑定了非空回调名，`.slapp.callbackFunctions` 中必须存在同名函数定义：

```json
{
  "name": "RunButtonPushed",
  "code": "app.StatusLabel.Text = \"Done\""
}
```

不要在 `code` 字段里再写完整函数外壳。

## 常见错误

- 只设置 `ButtonPushedFcn`，但没有生成同名函数。
- 在 `.slapp.callbackFunctions[].code` 中写完整 `function Callback(app,event) ... end`。
- HTML 事件回调读取 `event.Data`；HTML event 通道应读 `event.HTMLEventName` 和 `event.HTMLEventData`。
- 把 `ValueChangingFcn` 当作所有组件都有的回调；它只适合输入类组件。
