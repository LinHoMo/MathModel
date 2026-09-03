# ProgressBar 组件

`ProgressBar` 是 App 内部的进度条组件，用于固定显示任务进度。它和函数式 `waitbar(...)` 的区别是：`ProgressBar` 跟随 App 组件树，`waitbar` 是独立弹窗。

构造函数：

```julia
app.ProgressBar = TyAppDesigner.uiprogressbar(app.UIFigure;
    Value=0,
    Message="",
    ShowMessage=false,
    ShowPercentage=true,
    Indeterminate=false,
    ProgressColor=[0.02, 0.69, 0.15],
    TrackColor=[0.9, 0.9, 0.9],
    Position=[20, 20, 240, 40],
)
```

## 属性语义

| 属性 | 说明 |
|---|---|
| `Value` | 进度值，必须在 `0..1` |
| `Message` | 进度说明文本 |
| `ShowMessage` | 是否显示说明文本 |
| `ShowPercentage` | 是否显示百分比 |
| `Indeterminate` | 是否显示不确定进度动画 |
| `ProgressColor` | 进度填充色，RGB 向量 |
| `TrackColor` | 轨道背景色，RGB 向量 |
| `Visible` | 是否显示组件 |

`Value=0.69` 表示 69%。不要传 `69` 表示 69%。

拖拽组件库创建 ProgressBar 时，`ShowMessage=false`、`ShowPercentage=true`。更新 `Message` 只更新消息内容，不会也不应自动开启显示。只有用户要求显示说明文字时，才设置 `ShowMessage=true`。

## 推荐更新方式

连续更新 `Value` 和 `Message` 时，优先使用批量同步辅助函数，避免界面短暂错位：

```julia
TyAppDesigner.startprogress(app.ProgressBar, "Starting")
TyAppDesigner.updateprogress(app.ProgressBar, 0.5, "Processing 50%")
TyAppDesigner.finishprogress(app.ProgressBar, "Done")
TyAppDesigner.hideprogress(app.ProgressBar)
```

这些函数只同步 `Visible`、`Value`、`Message`，不会修改 `ShowMessage` 或 `ShowPercentage`。

## 典型回调

```julia
function StartButtonPushed(app, event)
    TyAppDesigner.startprogress(app.ProgressBar, "Starting")

    for i in 1:100
        sleep(0.02)
        TyAppDesigner.updateprogress(app.ProgressBar, i / 100, "Processing $(i)%")
    end

    TyAppDesigner.finishprogress(app.ProgressBar, "Done")
end
```

上例保持拖拽默认 `ShowMessage=false`。只有用户明确要求显示说明文字时，才额外设置：

```julia
app.ProgressBar.ShowMessage = true
```

## 不确定进度

任务无法预估百分比时：

```julia
app.ProgressBar.Indeterminate = true
app.ProgressBar.Visible = true
app.ProgressBar.Message = "Running..."
```

任务结束后关闭不确定状态：

```julia
app.ProgressBar.Indeterminate = false
TyAppDesigner.finishprogress(app.ProgressBar, "Done")
```

## 与 waitbar 的选择

| 场景 | 推荐 |
|---|---|
| 进度属于 App 工作流的一部分，需要固定显示 | `uiprogressbar` |
| 临时任务提示，不需要嵌入 App 布局 | `waitbar` |

## 约束

- `Value` 必须是有限实数，并且 `0 <= Value <= 1`。
- `ProgressBar` 当前没有独立用户交互回调。
- 普通属性赋值每次只同步一个属性；循环里同时改进度和文字时优先使用 `updateprogress`。
- 未要求特殊显示时保持组件库拖拽默认值：`ShowMessage=false`、`ShowPercentage=true`。
