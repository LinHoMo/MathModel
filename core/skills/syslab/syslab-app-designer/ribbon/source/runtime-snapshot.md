# Ribbon Runtime Snapshot

本文档定义源应用对标任务的通用运行时快照与视觉审计契约。它不绑定任何具体源平台；MATLAB、Syslab、已有 JSON spec、截图标注、录屏解析、人工导出的控件树都只是不同的 source adapter。

## 核心原则

源应用对标不能只依赖提示词、静态源码阅读或生成器经验。必须把“源应用真实表现”和“目标应用真实表现”落成可复查证据。

对标任务至少应产出：

- `source_ribbon_snapshot.json`：源应用运行时或等价证据快照。
- `target_ribbon_snapshot.json` 或目标运行截图：生成后目标应用的运行时表现。
- `visual_audit_report.json`：源快照与目标结果的结构、语义和视觉差异报告。

没有源快照时，可以继续做“结构草稿”或“初版迁移”，但不得声明“与源应用对标完成”。没有目标运行截图或目标运行时快照时，不得声明“视觉通过”。

## Snapshot 来源

`source_ribbon_snapshot.json` 的来源必须写清楚：

```json
{
  "source": {
    "kind": "matlab|syslab|json|image|video|manual|other",
    "appName": "...",
    "capturedAt": "...",
    "adapter": "...",
    "evidence": ["source file path", "screenshot path", "runtime dump path"]
  }
}
```

不同来源的可信字段可能不同：

- `runtime` / `json` 控件树通常可信于控件类型、层级、tag、value、checked、菜单结构。
- 截图 / 录屏通常可信于实际显示大小、换行、图标是否渲染、重叠、下拉箭头、视觉对齐。
- 源码通常可信于构造逻辑、资源路径、动态 popup 回调、默认状态来源。
- 人工标注必须写明标注者和依据，不能伪装成运行时事实。

## Gallery popup / category 证据

对 MATLAB 或等价源应用的 gallery，对标分组时必须递归记录 popup 结构。推荐形态：

```json
{
  "tag": "waveformGallery",
  "controlType": "matlab-gallery",
  "items": [],
  "Popup": {
    "children": [
      {
        "class": "matlab.ui.internal.toolstrip.GalleryCategory",
        "Title": "NR (5G)",
        "children": [
          {"Tag": "Downlink", "Value": "Downlink"}
        ]
      }
    ]
  }
}
```

规则：

- `Popup.children` 中的 `GalleryCategory` / category title 是生成 `menuGroups` 的直接证据。
- 只抽到扁平 `items`、没有 `Popup.children` 时，不能据此判定源 gallery 无分组；应把 popup category 标记为 `missingEvidence`，并继续检查源源码、运行时对象或截图。
- 如果源码中存在 `GalleryCategory(...)`、`popup.add(category)`、`constructGalleryView` / `dispatchGalleryItems` 等构造逻辑，即使当前 snapshot 没抽到 popup，也应把该 gallery 标记为“需要分组恢复”。
- 对已知 MATLAB App 的 gallery，源 snapshot 应尽量同时记录扁平 item 身份和 popup category 层级，便于目标生成 `items + menuGroups`。

## 控件字段

每个可见控件、菜单项和 gallery item 建议记录：

```json
{
  "id": "...",
  "tag": "...",
  "sourceType": "...",
  "controlType": "button|splitbutton|dropdownbutton|dropdown|combobox|editbox|gallery|matlab-gallery|radio|checkbox|toggle|menuItem|galleryItem|separator|label|spacer",
  "interaction": "command|toggle|radio|checkbox|field|menuCommand|menuCheck|menuRadio|galleryCommand|galleryToggle|layout",
  "tab": "...",
  "section": "...",
  "column": 0,
  "row": 0,
  "displayMode": "large|small|compact|field|unknown",
  "text": "...",
  "textLines": ["..."],
  "hasIcon": true,
  "iconSource": "...",
  "hasDropdown": false,
  "checked": false,
  "value": "...",
  "enabled": true,
  "visible": true,
  "bounds": {"x": 0, "y": 0, "w": 0, "h": 0}
}
```

字段缺失时不要猜。缺失字段应保留为 `unknown` 或写入 `missingEvidence`，并在审计报告中标记为无法确认。

## Source Column 字段

源应用对标 snapshot 不应只保存 section 下的扁平控件数组。只要来源能提供容器树，必须记录真实 source column 边界：

```json
{
  "tab": "...",
  "section": "...",
  "sectionSourceType": "...",
  "columns": [
    {
      "sourceIndex": 1,
      "sourceColumnId": "...",
      "sourceType": "...",
      "layout": "default|stack|matrix|unknown",
      "width": "unknown",
      "controls": [
        {"id": "...", "tag": "...", "text": "...", "sourceType": "..."}
      ],
      "commandCountInColumn": 0,
      "largeCommandCountInColumn": 0,
      "evidenceSource": "liveSnapshot|sourceCode|screenshot|manual|historySpec|unknown"
    }
  ]
}
```

如果源 runtime 对象树显示 `Section -> Column -> Controls`，snapshot 必须保留该结构。不能把同一个 source column 内的多个控件扁平化为 section 控件列表后再由生成器重新分列。缺失 source column 边界时，应标记为 `unknown`，不得声明源布局已完整对标。

### 下拉按钮字段要求

对 `DropDownButton`、`SplitButton`、`ListItemWithPopup` 和等价下拉入口，snapshot 必须尽量记录：

- 源 class / `sourceType`
- `hasDropdown = true`
- popup / children / items / menuGroups / dynamic popup callback
- 子项的 check / radio / command 类型
- 截图中是否可见下拉箭头

如果源控件看起来像大图标按钮，但存在 popup、children、checkbox menu item 或下拉箭头，生成器必须把它视为下拉控件。源菜单项是多个可勾选选项时，目标应为 `dropdownbutton` + `menuSelectionMode = "multiple"`，不是普通 `button`。

## 视觉审计项

`visual_audit_report.json` 至少检查：

- 源为大按钮时，目标是否被生成成小按钮或 stack 内按钮。
- 源控件有图标时，目标运行截图中是否实际渲染图标。
- 源文本换行、空格、大小写和顺序是否保留。
- 按钮、gallery item、菜单项文字是否溢出、裁剪或互相重叠。
- splitbutton / dropdownbutton 的下拉箭头是否存在，箭头位置是否与源证据一致。
- section、column、row 顺序是否一致。
- radio / checkbox / toggle / checked menu 的选中状态是否一致。
- gallery 可见项数量、右侧下拉槽位和 popup 布局是否合理。
- 目标运行截图是否出现空白 ribbon、默认 Home 壳、图标占位文本或明显一列挤压。

审计结果应区分：

- `pass`：有证据证明一致。
- `fail`：有证据证明不一致。
- `unknown`：缺少源或目标证据，不能判断。
- `accepted_difference`：目标平台能力差异，已写入 `known_differences.json` 并经调用方接受。

## 生成器约束

生成器必须优先读取 snapshot 字段，而不是重新推断：

- `controlType` / `interaction` 决定控件类型和回调语义。
- `displayMode` 决定大按钮/小按钮，不得因文字长短自行改小。
- `textLines` 决定换行，不得通过加宽控件替代源换行。
- `hasIcon` 和 `iconSource` 决定是否必须生成可渲染 `iconSrc`。
- `checked` / `value` 决定 radio、checkbox、toggle、可选菜单和 gallery item 状态。
- `section` / `column` / `row` 决定布局顺序。

如果目标组件无法表达源语义或视觉，生成器必须写入 `known_differences.json`，不能静默降级。
