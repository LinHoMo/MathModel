# Ribbon 图标解析规则

本文档约束源应用对标任务中的图标解析流程。它不绑定某个源平台；源应用可以来自 MATLAB、Syslab、Web 应用、桌面应用、已有 JSON spec、截图标注、录屏解析或人工导出的控件树。

核心原则：

- 源图标线索不是图标完成状态。
- 只有生成可渲染的 `.slapp.figure.toolstrip[*].iconSrc` 和运行代码中的 `IconSrc`，才算图标完成。
- “不允许兜底图标”不等于“允许空图标”。正确含义是：不能用无关图标替代源图标，必须继续追踪源图标证据链；无法解析时应标记失败或不完整。

## 图标线索

以下任一字段或等价信息都表示源应用存在图标线索：

- 独立图片路径
- icon id
- icon class
- CSS class
- resource key
- theme token
- object handle
- sprite sheet / atlas
- background-position
- crop rect
- runtime image object
- 源截图中可见图标
- 人工标注的源图标

这些线索只能作为来源证据或中间字段，不能替代最终渲染字段。

## 正式渲染字段

生成结果必须使用正式渲染字段：

- `.slapp.figure.toolstrip` / item：`iconSrc`
- `app.jl` / `.slapp.code`：`IconSrc`

以下字段只能用于审计或中间 spec，不能作为图标完成依据：

- `sourceIconClass`
- `sourceIconId`
- `sourceIconKey`
- `sourceIconPath`
- `sourceIconHandle`
- `spriteSheet`
- `backgroundPosition`
- `cropRect`
- `iconFile`
- `iconKind`
- `iconLabel`
- `icon`

## 通用解析顺序

当源图标不是直接图片文件时，必须继续解析。推荐按以下顺序查找：

1. 源应用运行时对象。
2. 源应用工程文件、配置文件或声明式 spec。
3. 源应用源码。
4. 源应用 CSS、theme、style 表或 token 表。
5. 源应用资源目录。
6. 资源映射表、manifest、bundle map 或 asset registry。
7. sprite sheet、atlas、background-position、crop rect。
8. 同产品、同插件、同工具箱或同模块共享资源目录。
9. 运行时导出图片或可验证截图裁剪。
10. 人工标注资源。

每一步都应记录 evidence，包括来源文件、字段名、class/id/key、坐标、尺寸、输出文件路径和解析状态。

## 图标解析计划

源应用对标任务必须生成 `iconResolutionPlan`，可以作为独立 `icon_resolution_plan.json`，也可以作为 `source_ribbon_snapshot.json` 中的明确字段。计划必须在生成前建立，并驱动实际产物生成；不能先生成 ribbon，再只用静态检查发现缺图标。

每条计划至少包含：

- source control/item id 或可追踪路径。
- source icon evidence，例如路径、class、id、key、token、对象句柄、sprite 坐标或截图标注。
- evidence type。
- lookup paths 或 runtime lookup method。
- expected output file。
- expected `.slapp` `iconSrc`。
- expected `app.jl` / `.slapp.code` `IconSrc`。
- resolution status。
- evidenceSource。

如果源证据显示存在图标线索，但对应计划不存在，源应用对标生成不得继续；如果调用方要求先生成结构草稿，必须将图标状态标为 `incomplete`，并禁止声明对标完成。

## 计划驱动生成

生成器必须从 `iconResolutionPlan` 的已解析结果写入 `.slapp` 和运行代码：

- `resolved-*` 项必须写入可渲染 `iconSrc` 和 `IconSrc`。
- `pending` / `unknown` / `unresolved` 项不能被静默跳过。
- 未解析项必须触发继续解析流程，或在调用方明确接受差异时写入 `known_differences.json`。
- 不得把未解析图标从主 ribbon 中删掉来让静态检查通过。

生成后必须校验：

- 源图标线索数量等于 `resolved-* + accepted_difference + unresolved/unknown` 数量。
- 所有 `resolved-*` 项的输出资源文件存在。
- 所有 `resolved-*` 项在 `.slapp` 中有对应 `iconSrc`。
- 所有 `resolved-*` 项在 `app.jl` / `.slapp.code` 中有对应 `IconSrc`。
- 设计器重新生成 `app.jl` 后，`IconSrc` 仍然存在且资源路径有效。

## 资源映射缓存

对同一源应用版本、插件版本或资源包版本，已解析出的 icon id / class / key / token / sprite 坐标应写入版本化缓存映射。缓存文件名可按源平台或资源包自定义，例如：

```text
resources/ribbon-icons/icon_resource_map.json
```

缓存条目应包含：

- source key。
- source version 或 resource package version。
- resolution status。
- evidence file / manifest / CSS / runtime object。
- sprite sheet 与 crop rect（如适用）。
- output file。
- checksum 或可复查标识（如可用）。

后续遇到相同源 key 时应先读取缓存并验证输出资源存在；缓存缺失或资源不存在时必须重新解析，不能把缓存命中直接当作完成。

## 解析结果分类

图标解析状态应使用下面的分类之一：

- `resolved-exact-file`：源线索直接指向独立图片文件。
- `resolved-css-sprite`：从 CSS、style 或 theme 的 sprite/atlas 裁剪得到。
- `resolved-resource-map`：通过资源映射表或 manifest 定位得到。
- `resolved-shared-source-resource`：从同产品、同插件、同工具箱或同模块共享资源得到。
- `resolved-runtime-export`：通过运行时对象或运行时导出得到。
- `resolved-manual-evidence`：调用方提供可验证人工资源或标注。
- `unresolved`：已查证但仍无法解析。

`unresolved` 不能被汇总为通过。

## CSS / Sprite 解析

如果源图标线索是 CSS class、theme class、sprite sheet 或 atlas key，应：

1. 定位 class / key 所在 CSS、theme 或资源映射。
2. 找到 background image、sprite sheet 或 atlas 文件。
3. 读取 background-position、width、height 或 crop rect。
4. 从 sprite / atlas 中裁剪出独立图片。
5. 写入 `resources/ribbon-icons` 或当前工程约定的资源目录。
6. `.slapp` 写入裁剪结果的 `iconSrc`。
7. `app.jl` / `.slapp.code` 写入指向该资源文件的 `IconSrc`。

示例：

```text
sourceIconClass = "open"
CSS rule = ".open_24 { background: url(images/toolstrip.png); background-position: -24px -48px; width: 24px; height: 24px; }"
output = resources/ribbon-icons/open.png
```

这个示例只说明 CSS sprite 解析方法，不要求源平台必须使用 CSS。

## 失败门禁

命中以下任一情况，源应用对标结果不得声明完成：

- 源证据显示 control 或 item 有图标，但生成结果没有可渲染 `iconSrc`。
- `app.jl` / `.slapp.code` 中对应 control 或 item 没有 `IconSrc`。
- 只有 `sourceIconClass`、`sourceIconId`、`sourceIconKey`、`sourceIconPath`、`spriteSheet`、`backgroundPosition` 或 `cropRect`，没有真实图片资源。
- 输出资源文件不存在或无法读取。
- `iconResolutionStatus = "unresolved"` 被汇总为通过。
- 用无关通用 fallback 图标替代源图标，却声明源应用对标完成。

如果调用方接受部分图标无法解析，必须写入 `known_differences.json` 或验收报告，状态只能是 `unknown`、`unresolved` 或 `accepted_difference`，不能是 `pass`。

## 验收摘要

验收报告应包含 `iconResolutionStatus` 摘要：

- `totalSourceIconHints`
- `resolvedExactFile`
- `resolvedCssSprite`
- `resolvedResourceMap`
- `resolvedSharedSourceResource`
- `resolvedRuntimeExport`
- `resolvedManualEvidence`
- `unresolved`
- `missingIconSrc`
- `missingIconFile`

只有关键源图标均解析为可渲染资源，且缺失数量为 0 时，才能声明图标对标完成。
