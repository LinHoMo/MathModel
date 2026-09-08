# Ribbon 布局规则

本文档集中说明 Ribbon 的布局与视觉约束；组件范围见 `components.md`。

## 层级

Ribbon 的基本层级为：

```text
toolstrip -> tab -> section -> column -> control
```

- `section` 是有标题的分组。
- `column` 是分组中用于摆放控件的一列或一块区域。
- `control` 是按钮、输入框、下拉框、gallery 等实际可见组件。

## Section 布局

| `layout` | 含义 |
| --- | --- |
| `""` / `"columns"` | 常规分组，按照 column 从左到右显示 |
| `"gallery"` | 分组中的普通列作为 gallery item 显示，`more-slot` 作为展开入口 |
| `"overflow-gallery"` | 可折叠的命令条，空间不足时把内容收到 overflow 中 |

MATLAB 风格 gallery 新代码使用控件级 `controlType = "matlab-gallery"`，不要再新建 section 级 `"matlab-gallery"` 布局。

## Column 布局

| `layout` | 含义 |
| --- | --- |
| `""` / `"default"` | 常规大控件列 |
| `"stack"` | 控件在一列内上下排列 |
| `"matrix"` | 控件按紧凑网格排列，列数由 `matrixColumns` 控制 |
| `"more-slot"` | gallery / overflow 的展开位置 |

## Command DisplayMode 硬规则

`displayMode = "large"` 表示 command 控件独占一个 command column，不表示“这个按钮很重要”。

- `displayMode = "large"` 的 `button`、`toggle`、`splitbutton`、`dropdownbutton` 必须每个控件独占一个 column。
- 同一 column 内有两个或以上 command 控件时，该 column 必须是 `layout = "stack"`，且其中所有 command 控件必须是 `displayMode = "small"`。
- 同一 column 内三个 `button` / `toggle` / `splitbutton` / `dropdownbutton` 都设置为 `large` 是生成错误，会导致图标和文字布局异常。
- 不得只根据文本长度、图标大小、按钮重要程度或 File / Session 组名把多控件 column 里的 command 改成 `large`。
- 如果源快照缺少 displayMode，但源 column 中明确有多个 command，应先按 stack + small 建模，或标记为 `unknown` 等待人工确认。

### 可执行判定表

command 控件只包括 `button`、`toggle`、`splitbutton`、`dropdownbutton`。`matlab-gallery` / `gallery` 的 item、字段型控件、label 和 spacer 不按普通 command column 审计。

| 条件 | 判定 |
| --- | --- |
| `commandCount == 0` | 按 field / gallery / layout 规则继续判断 |
| `commandCount == 1` 且该 command 为 `displayMode = "large"` | pass，但该 command 必须是 column 中唯一 command |
| `commandCount == 1` 且该 command 为 `displayMode = "small"` | pass |
| `commandCount >= 2` 且 `column.layout != "stack"` | fail |
| `commandCount >= 2` 且存在 `displayMode = "large"` | fail |
| `column.layout = "stack"` 且存在 `displayMode = "large"` 的 command | fail |
| `largeCommandCount >= 2` | fail |

不得因为 File / Session / Export / Generate 等业务分组，把多个 large command 放入同一普通 column。业务分组只决定 section 归属，不决定 column 共享资格。

## 字段列宽

字段列是包含输入或值选择控件的 `stack` 列，例如标签加 `editbox`，或标签加 `dropdown`。

如果源应用为字段列给出列宽，例如 MATLAB `addColumn('Width', W)`：

- 生成 spec 时保留为 `column.width = "Wpx"`。
- 生成运行代码时保留为 `app.<Column>.Width = "Wpx"`。
- 列内 `editbox`、`dropdown`、`combobox` 通常继承列宽，不重复写控件宽度。

普通按钮、`splitbutton`、`dropdownbutton` 等命令列按内容自适应，不因设计态列宽产生固定空白。

## Gallery

- `gallery` 分组中的非 `more-slot` 列是 gallery item。
- `matlab-gallery` 是一个独立控件，可与普通命令列放在同一个 `"columns"` section 中。
- `matlab-gallery.items` 是可见 item 与 popup item 的共同数据源。
- `visibleCount`、`itemWidth`、`frameWidth` 是控件级可见数量与尺寸契约；新生成的 `matlab-gallery` 必须显式写入这三个字段。
- 压缩时至少保留一个可见 item 与右侧下拉入口；popup 内容不得重叠。

生成 `matlab-gallery` 不能只写 `items`，也不能只写 `visibleCount`。生成结果必须保存足够的宽度契约，使初始渲染能达到源应用的可见项数量；如果无法取得源应用首选可见项数量，使用 `min(5, items.length)`：

- 控件级 `visibleCount`
- 控件级 `itemWidth`
- 控件级 `frameWidth`
- 必要时 gallery 所在 `column.width` 或 `section.width` 作为额外外层预算

宽度至少满足：

```text
itemWidth * visibleCount + 4 * (visibleCount - 1) + 18 + 2 + 1 + 12
```

其中 `4` 是 item 间距，`18` 是右侧下拉槽宽，`2` 是下拉槽间距，`1` 是边框余量，`12` 是安全余量。只写 `visibleCount` 而缺少宽度预算时，响应式渲染可能合法折叠到一个可见项，但这不等于已对标源应用。

## 源应用对齐

- 布局、顺序、宽度、空白行和图标必须依据可验证的源应用信息。
- 源运行时、源码或等价证据证明的 source column 边界是布局证据，优先于默认 displayMode 启发式。
- 如果源 column 中包含多个 command，目标应优先保持同一 source column 边界；不得因为 `large`、文本换行、图标大小、业务分组名或固定模板，静默拆成多个目标 column。
- 如果目标平台无法在保持源 column 边界的同时满足 command displayMode 视觉要求，必须记录为 `known_differences.json`、`accepted_difference` 或 `unknown`，不能静默改布局后声明源应用对标完成。
- 字段型 MATLAB `DropDown()` 使用值选择控件 `dropdown`。
- 动作菜单使用 `dropdownbutton` 或 `splitbutton`。
- 图标必须来自源资源；无法取得时应显式报告，不能使用兜底图标冒充源图标。
- 源控件的父容器、同列控件数量、列布局和源控件语义都属于布局证据；不要只按显示文本换行、文本长度或图标大小推断控件显示层级。
- 单控件独占命令列通常保持主命令显示层级；多个命令同列时才使用 `stack` 小命令布局，且 stack 内命令控件必须是 `displayMode = "small"`。
- `displayMode = "large"` 的 `button`、`toggle`、`splitbutton`、`dropdownbutton` 必须每个控件独占一个 column。File / Session / New-Open-Save 命令组也不例外。

验收规则见 [rules/ribbon-validation.md](../rules/ribbon-validation.md)。
