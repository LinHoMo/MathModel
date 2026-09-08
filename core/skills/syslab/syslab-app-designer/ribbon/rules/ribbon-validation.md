# Ribbon 生成后验证规则

这份文档用于把“生成后是否合格”从经验判断，收口成可检查规则。

目标：

- 不再只靠阅读提示词判断外部生成器是否遵守了契约
- 对明显退回旧策略的产物，能快速一眼判错
- 为后续自动化审查脚本提供规则来源

## 布局规则必须参与验收

生成后验收不能只检查 JSON、include、控件数量、图标数量、回调是否存在。必须按 `../reference/layout-rules.md` 和 `ribbon-rules.md` 检查最终 `.slapp.figure.toolstrip` 布局。

如果最终 ribbon 违反任一布局规则，即使 JSON 可解析、Julia include 成功、图标和回调存在，也必须判为失败。

验收状态必须统一使用：

- `pass`：有证据证明通过。
- `fail`：有证据证明失败。
- `unknown`：缺少源或目标证据，不能判断。
- `unavailable`：当前环境或工具不可用，无法执行检查。
- `accepted_difference`：目标平台能力差异已记录并被调用方接受。

`unknown` 和 `unavailable` 不能汇总为通过；最终结论必须单独列出这些状态。

验收报告必须明确说明布局规则检查结果；缺少布局规则检查结果时，不得声明符合 skills。

验收必须逐 column 检查最终 `.slapp.figure.toolstrip` 是否符合 source layout model 或 target layout model，以及布局规则。验收报告必须单独列出 `layoutRuleStatus`，至少包含：

- 每个 section / column 是否存在
- column 顺序是否与 source / target layout model 一致
- 同一 column 内控件数量是否一致
- 多 command column 是否为 `layout = "stack"`
- stack 内 command 是否全部为 `displayMode = "small"`
- `displayMode = "large"` 的 command 是否独占 column
- 源控件为下拉 / split / popup 时，目标是否保留下拉语义；从零设计任务按目标模型检查
- 源菜单项有图标时，目标 item 是否有可渲染 `iconSrc`；从零设计任务按目标图标策略检查
- 源菜单项有 checkbox / multiple / 独立 toggle 语义时，目标是否有 checked 状态和对应 mark 样式；源 MATLAB-style gallery 单选当前项是否使用父控件 `value` / `Value` 而不是 item `checked`；从零设计任务按目标状态策略检查
- 是否存在文字重叠、图标缺失、大按钮变小、小按钮变大等视觉退化

缺少 `layoutRuleStatus` 时，不得声明符合 skills。只通过 JSON、Julia include、控件数量、图标数量、回调检查，不得声明布局验收通过。

### `layoutRuleStatus` 必填结构

验收报告必须包含下面的结构，且 `violations` 不得被其它成功项抵消：

```json
{
  "layoutRuleStatus": {
    "status": "pass|fail|unknown|unavailable",
    "checkedCommandTypes": ["button", "toggle", "splitbutton", "dropdownbutton"],
    "violations": [
      {
        "rule": "largeCommandMustBeExclusive|multiCommandColumnMustBeStackSmall|stackColumnCannotContainLargeCommand",
        "tab": "...",
        "section": "...",
        "columnId": "...",
        "columnLayout": "...",
        "controls": [
          {
            "id": "...",
            "controlType": "...",
            "displayMode": "...",
            "text": "..."
          }
        ]
      }
    ]
  }
}
```

`layoutRuleStatus.status = "fail"` 时，最终结论必须是失败。JSON 解析、Julia include、图标检查、回调检查、App Designer open 成功都不能覆盖该失败。

源应用对标任务还必须输出 `sourceColumnBoundaryStatus`。示例：

```json
{
  "sourceColumnBoundaryStatus": {
    "status": "pass|fail|unknown|accepted_difference|unavailable",
    "violations": [
      {
        "rule": "sourceColumnSplitWithoutAcceptedDifference|sourceColumnMergedWithoutAcceptedDifference",
        "tab": "...",
        "section": "...",
        "sourceColumn": ["controlA", "controlB"],
        "targetColumns": [["controlA"], ["controlB"]],
        "evidenceSource": "liveSnapshot"
      }
    ]
  }
}
```

如果 `sourceColumnBoundaryStatus.status = "fail"`，最终结论必须失败；不能用 JSON 解析、Julia include、回调存在或默认 layout 规则通过来覆盖。

审计脚本必须至少检查：

- `displayMode = "large"` 的 command 是否与其它 command 共用同一个 column。
- 多 command column 是否为 `layout = "stack"`。
- 多 command stack column 内 command 是否全部为 `displayMode = "small"`。
- `column.layout = "stack"` 内是否存在 `displayMode = "large"` 的 command。
- `matlab-gallery` / `gallery` item 是否被误当成普通 command column。

## 高频错误专项验收

验收报告还必须包含以下专项状态：

- `mainSlappStatus`：输出包含 `.slapp` 时，目录中是否有唯一主 `.slapp`，是否清楚标明交付入口。
- `iconRenderFieldStatus`：`.slapp.figure.toolstrip` 是否使用正式 `iconSrc`，而不是只有 `iconFile` / `sourceIcon*`。
- `iconResolutionStatus`：源图标线索是否已解析为真实图片资源和可渲染 `iconSrc` / `IconSrc`，而不是停留在 id、class、key、sprite 坐标或审计字段。
- `multiCommandColumnDisplayModeStatus`：多 command column 是否使用 `layout = "stack"` 且全部 command 为 `displayMode = "small"`。
- `menuCheckedStateStatus`：源 checkbox / multiple / 独立 toggle menu item 是否保留父级选择模式和 item `checked` / `Checked`；源 MATLAB-style gallery 单选当前项是否保留为父控件 `value` / `Value`，且 item / `menuGroups` item 不重复写 `checked` / `Checked`。
- `menuItemIconStatus`：源 menu item / gallery item 有图标时，目标 item 是否有可渲染 `iconSrc` / `IconSrc`。
- `sourceEvidenceStatus`：源应用对标任务中，菜单项、图标、选择状态和布局判断是否记录了可信 evidenceSource；非对标任务可标为 `unavailable` 并说明不适用。
- `callbackFunctionBodyStatus`：`.slapp.callbackFunctions[].code` 是否只包含函数体，且没有完整 `function ... end` 包裹。
- `sourceDropdownControlStatus`：源 `DropDownButton` / `SplitButton` / popup 控件是否仍保留为对应下拉控件，且没有因为空 popup 被降级为普通 `button`。
- `multiCheckDropdownControlStatus`：源 `DropDownButton` / popup 控件含 checkbox / multiple 菜单项时，目标是否为带图标、非空菜单和 multiple checkbox 语义的 `dropdownbutton`。
- `sourceColumnBoundaryStatus`：源运行时、源码或等价证据已证明的 source column 边界是否在目标中保持；若被拆分或合并，是否有 `known_differences.json` / `accepted_difference` / `unknown` 说明。
- `recursiveExtractionStatus`：源 popup、gallery、category、submenu 是否已递归展开到可交互叶子项；不能只抽第一层容器或 category 数量。

缺少这些专项状态时，不得声明符合 skills。

`iconResolutionStatus` 至少应包含：

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

图标解析状态分类和详细流程见 [source/icon-resolution.md](../source/icon-resolution.md)。这里仅保留生成后验收字段和失败判定。

源应用对标任务中，`unresolved`、`missingIconSrc` 或 `missingIconFile` 大于 0 时，不得声明图标对标完成。

## 验证脚本

如果项目提供 ribbon 生成产物验证脚本，应在生成后运行。脚本位置由当前项目约定提供，不应在文档中写死本机绝对路径。

用法示例：

```powershell
python <audit_generated_ribbon.py> <generated-ribbon-dir>
```

源应用对标任务必须优先执行运行时快照与视觉审计流程，契约见 `../source/runtime-snapshot.md`。验证脚本不应写死某个源平台；应接受通用 `source_ribbon_snapshot.json` 和目标运行时快照 `target_ribbon_snapshot.json`，并输出 `visual_audit_report.json`。目标截图不是必需项，只作为可选补充证据。

## 目标运行时验收推荐命令链

如果当前 Syslab App Designer 插件提供以下命令，目标运行时验收应优先使用这条链路：

1. 使用现有 App Designer 打开入口打开 `.slapp`：
   - `syslab.app-designer.open(filePath)`，或项目环境提供的等价 `openFile(message)`。
2. 调用 `syslab.app-designer.runSlapp(filePath)`。
   - 该命令必须通过设计器 webview 执行原有 `run` 命令链路，不得直接 `include(app.jl)` 或直接 `executeFile(app.jl)` 替代。
3. 调用 `syslab.app-designer.exportRuntimeRibbonSnapshot(filePath)`。
   - 该命令应输出 `target_ribbon_snapshot.json` 和 `visual_audit_report.json`。
   - 该命令应在运行窗口内遍历所有 ribbon tab 后再生成快照，避免只采集当前 active tab。
4. 如果提供 `syslab.app-designer.auditSlapp(filePath)`，可作为上述流程的组合入口。

如果这些命令不可用，应在验收报告中记录为 `unavailable`，并将目标运行视觉验收标为 `unknown`。不得用 Julia `include OK`、`Meta.parseall OK` 或静态 JSON 检查代替目标运行时视觉/布局验收。

## 插件外部自动化入口

如果需要从脚本、命令行或 AI 工作流触发目标运行时验收，应优先使用 Syslab App Designer 插件提供的本机自动化入口，而不是尝试通过 `Syslab.cmd` 直接执行 VS Code command。`Syslab.cmd` 只负责启动宿主或打开文件，不保证能调用扩展 command。

插件启动后会启动本机 IPC 自动化服务。发现信息优先写入当前用户的稳定可写目录；如果插件私有 `globalStorage/automation` 可写，也会写入一份兼容镜像。

```text
Windows:
%LOCALAPPDATA%\TongYuan\SyslabAppDesigner\automation\syslab-app-designer-automation.json

Windows fallback:
%USERPROFILE%\.syslab-app-designer\automation\syslab-app-designer-automation.json

Linux/macOS:
$XDG_RUNTIME_DIR/syslab-app-designer/automation/syslab-app-designer-automation.json

Fallback:
$HOME/.syslab-app-designer/automation/syslab-app-designer-automation.json
```

该固定文件是发现索引。调用方应按上述平台路径查找，必要时再兼容读取插件 `globalStorage/automation/syslab-app-designer-automation.json`。找到索引后，先读取其中的 `latestDiscoveryFile`，再读取对应进程的发现文件，使用其中的 `ipcPath` / `socketPath` 和 `endpoints` 发起 `http-over-ipc` 请求。常用入口：

```text
GET  /health
POST /app-designer/open
POST /app-designer/runSlapp
POST /app-designer/exportRuntimeRibbonSnapshot
POST /app-designer/auditSlapp
```

POST 请求体统一使用：

```json
{ "filePath": "<absolute path to app.slapp or app.jl>" }
```

`filePath` 应传入 `app.slapp` 或 `app.jl` 的绝对路径；自动化入口会将该路径交给插件既有命令链路处理，不要求目标文件位于当前 Syslab / VS Code 打开的 workspace 内。

推荐 Node 调用流程：

```javascript
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");

function getAutomationIndexPath() {
  const candidates = [];
  if (process.platform === "win32") {
    candidates.push(path.join(
      process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"),
      "TongYuan",
      "SyslabAppDesigner",
      "automation",
      "syslab-app-designer-automation.json",
    ));
    candidates.push(path.join(
      os.homedir(),
      ".syslab-app-designer",
      "automation",
      "syslab-app-designer-automation.json",
    ));
  } else if (process.env.XDG_RUNTIME_DIR) {
    candidates.push(path.join(
      process.env.XDG_RUNTIME_DIR,
      "syslab-app-designer",
      "automation",
      "syslab-app-designer-automation.json",
    ));
    candidates.push(path.join(
      os.homedir(),
      ".syslab-app-designer",
      "automation",
      "syslab-app-designer-automation.json",
    ));
  } else {
    candidates.push(path.join(
      os.homedir(),
      ".syslab-app-designer",
      "automation",
      "syslab-app-designer-automation.json",
    ));
  }
  const indexPath = candidates.find((candidate) => fs.existsSync(candidate));
  if (!indexPath) {
    throw new Error(`App Designer automation discovery index not found: ${candidates.join(", ")}`);
  }
  return indexPath;
}

const indexPath = getAutomationIndexPath();
const index = JSON.parse(fs.readFileSync(indexPath, "utf8"));
const info = JSON.parse(fs.readFileSync(index.latestDiscoveryFile, "utf8"));
const body = JSON.stringify({ filePath: "<absolute path to app.slapp or app.jl>" });

const req = http.request({
  socketPath: info.socketPath || info.ipcPath,
  path: info.endpoints.auditSlapp,
  method: "POST",
  headers: {
    "content-type": "application/json",
    "content-length": Buffer.byteLength(body),
  },
}, (res) => {
  let data = "";
  res.setEncoding("utf8");
  res.on("data", (chunk) => { data += chunk; });
  res.on("end", () => {
    if (res.statusCode < 200 || res.statusCode >= 300) {
      throw new Error(`auditSlapp failed: ${res.statusCode} ${data}`);
    }
    console.log(data);
  });
});
req.on("error", (error) => { throw error; });
req.end(body);
```

`auditSlapp` 必须复用插件内部现有命令链：打开 `.slapp`、通过设计器 webview 执行原有 `run` 命令、再从运行窗口导出 `target_ribbon_snapshot.json`。不得在外部入口中重新实现运行逻辑。

如果发现自动化发现索引不存在、`latestDiscoveryFile` 不存在、IPC 服务不可达或 Syslab 宿主未启动，不得立刻记录为 `unavailable`。应先尝试启动 Syslab 宿主并打开主 `.slapp`，等待 App Designer 扩展激活，轮询发现索引，并通过 `http-over-ipc` `/health` 接口确认服务可用。

只有启动失败、连接超时、health 不通或接口持续报错后，才允许在 `visual_audit_report.json` 中记录 `targetRuntimeSnapshot = "unknown"` 或 `unavailable`，且不得声明运行时视觉验收通过。

命令行 Julia `include(app.jl)`、`Meta.parseall` 或直接执行 `app.jl` 只能作为语法/代码片段辅助检查，不能替代 App Designer 运行时验收。命令行运行到 `uifigure`、`create_figure` 或其它 UI runtime API 失败时，应先判断是否为 App Designer 服务端未连接，而不是直接归类为文件语法错误。

## 一票否决项

命中下面任一项，默认直接判为不合格：

1. 输出包含 `.slapp` 时，未说明地同时交付多个候选 `.slapp`，例如 `app.slapp` 和业务命名 `.slapp` 都存在但未标明唯一主入口。
2. 退回 `uihtml` / `HTMLSource` / 内嵌 HTML ribbon
3. 大量使用 `file:///...` 本地图标路径
4. 输出包含 `.slapp` 时，`.slapp` 里还是默认 `Home / Section / Command` toolstrip 壳，而真实业务结构并没有落到 ribbon tree 上
5. 普通无 ribbon App 写成 `enabled:true, visible:true, tabs:[]`；无 ribbon 必须写 `enabled:false, visible:false, tabs:[]`，有 ribbon 则 `tabs` 必须非空。
6. 没有正式 ribbon 定义路径，只依赖 HTML 仿制品
7. 同时混用多套真相源，例如 HTML shell、业务 toolstrip tree 和额外创建脚本。
8. `.slapp.figure.toolstrip.tabs` 已经包含真实业务 tab 时，`startUpFunctions`、`info.startupFcn` 或嵌入 `code` 中仍然解析另一份 Ribbon spec 或尝试创建整份 Ribbon。
9. 新生成的 `app.jl` / `.slapp.code` 中仍然把整棵 ribbon 写成 `app.<Figure>.Toolstrip = Dict{String,Any}(...)`。新运行代码必须使用 `TyAppDesigner.uitoolstrip*` 构造器逐层创建组件，并用 `TyAppDesigner.ToolstripItem[...]` 表达下拉项 / gallery item。
10. `.slapp.name` 不是合法 Julia module 标识符，或 `.slapp.code` / 设计器生成后的 `app.jl` 中出现类似 `module Antenna Array Designer Ribbon` 的非法模块声明。
11. `.slapp.code` 或设计器生成后的 `app.jl` 中出现裸标识符 `undefined`。
12. 任一 toolstrip control 绑定非空 `buttonPushedFcn`、`valueChangedFcn` 或 `commandInvokedFcn`，但 `.slapp.callbackFunctions` 中不存在同名函数定义。
13. `.slapp.callbackFunctions[].code` 包含完整 `function <name>(app, event) ... end` 包裹，而不是只包含函数体。
14. 新生成的已知控件仍统一使用 `TyAppDesigner.uitoolstripcontrol(...)`，而不是对应的具体组件构造函数。
15. 调用方要求源应用对标，但交付物没有 `source_ribbon_snapshot.json` 或等价可复查证据，却声明“已对标源应用”。
16. 调用方要求视觉对标，但交付物没有 `target_ribbon_snapshot.json` 或 `visual_audit_report.json`，却声明“视觉通过”。目标截图不是必需项。
16. 输出包含 `.slapp` 时，`.slapp.figure.toolstrip` 中只有 `iconFile`、`sourceIconId`、`sourceIconClass` 或其它审计字段，而缺少正式 `iconSrc`。
17. 源 menu item / gallery item 有图标，但目标 item 缺少可渲染的 item 级 `iconSrc` / `IconSrc`。
18. 源证据显示控件或 item 有图标线索，例如内部 icon id、CSS class、资源 key、对象句柄、sprite sheet 坐标或 background-position，但生成结果没有继续解析源应用 CSS、资源目录、源码、运行时对象或映射表，也没有生成真实图片资源。
19. control/item 存在 `sourceIconClass`、`sourceIconId`、`sourceIconKey`、`sourceIconPath`、`spriteSheet`、`backgroundPosition`、`cropRect` 或等价源图标线索，但缺少可渲染 `iconSrc`。
20. `app.jl` / `.slapp.code` 中对应 control/item 缺少 `IconSrc`，或 `IconSrc` 指向不存在的资源文件。
21. `iconResolutionStatus = "unresolved"` 却报告为完成。
22. 审计字段非空但渲染字段为空。
23. 源 item 是 checkbox / multiple / 独立 toggle / checked item，但目标缺少 item `checked` / `Checked` 或父级 `menuSelectionMode` / `menuItemMarkStyle`；源 MATLAB-style gallery 单选当前项除外，该场景必须使用父控件 `value` / `Value`，不得要求 item `checked` / `Checked`。
24. 菜单项不是来自 live snapshot，却在报告中声称由 live snapshot 直接证明。
25. `unknown` 或 `unavailable` 被汇总为通过。
26. 输出包含 `.slapp`，但没有通过 Syslab App Designer 打开主 `.slapp` 并执行设计器 Run 命令完成运行验收，却声明可运行通过。
27. 设计器 Run 后重新生成的 `app.jl` 出现非法 `module`、裸 `undefined`、语法错误、缺失回调、缺失 `IconSrc` 或资源路径失效。
28. `layoutRuleStatus.status = "fail"`，但最终报告仍声明完成、通过、可对标或符合 skills。
29. 源应用包含 `GalleryPopup`、`GalleryCategory`、`PopupList`、`ListItemWithPopup` 或等价容器，但源快照没有递归展开到叶子 item，或目标只按 category / 容器数量生成 item，却声明内容完整对标。
30. MATLAB `GalleryCategory` 被当作 gallery item 处理，而不是映射为 `menuGroups[]`；或者没有读取 `GalleryCategory.Children` 就声明 gallery item 完整。

## 高风险项

命中下面这些，默认至少要人工复核：

1. 在 toolstrip 实体上出现未文档化的 `callbackFcns`
2. 通过生成脚本直接拼大段 HTML / CSS / DOM
3. 生成产物以“可运行网页仿真”为主，而不是正式 ribbon spec 为主
4. 嵌入 `code` 中同时出现结构化 toolstrip 与额外整树创建逻辑
5. 带下拉入口的控件存在 `items` / `menuGroups`，但源 item 有图标时缺少 item 级可渲染 `iconSrc`。主按钮图标不能作为菜单项图标的隐式替代；`iconLabel`、`iconKind`、`icon` 或源内部图标 id 也不能作为可渲染图标验收依据。如果源应用确实没有 item 图标，应在迁移说明中显式记录。
6. 源应用字段型 `DropDown()` 被映射为动作菜单控件 `dropdownbutton` / `splitbutton`，且没有明确说明例外理由。
7. 回调从 `event.CommandId`、`event.Value` 或 `event.LastMenuItem` 顶层读取设计器 toolstrip 交互载荷，而不是从 `event.Item` 读取。
8. 源应用已经提供字段型 `stack` 列宽，但 `.slapp.figure.toolstrip` 或设计器生成后的 `app.jl` 未保留该列的 `width` / `Width`，导致 `editbox` 或字段下拉退回默认宽度。
9. 源菜单项带有 checkbox / multiple / 独立 toggle / checked 语义，但父菜单控件没有设置对应 `menuSelectionMode`。
10. 源运行时证据显示某个命令按钮独占 command column，但生成结果仅因文本是单行而使用 `displayMode = "small"`。
11. 源菜单项带有 checkbox / multiple / 独立 toggle / checked 状态，但生成结果的 `.slapp` item 缺少 `checked`，或 `app.jl` / `.slapp.code` 中对应 `ToolstripItem` 缺少 `Checked`。如果源为 MATLAB-style gallery 单选当前项，则父控件必须有 `value` / `Value`，item 不得写 `checked` / `Checked`。
12. 同一源 action group / radio cluster 被生成成多个 `radio` 控件，但没有共享同一个 `groupName` / `GroupName`。
13. 仅因为控件是 `splitbutton` / `dropdownbutton` / `matlab-gallery` 就推断下拉项需要 `checked`。只有源对象为 `ListItemWithCheckBox`、multiple check item、独立 toggle item，或运行时证据显示 item 自身是持久勾选状态时，才允许生成 item `checked`；MATLAB-style gallery 的单选当前项应生成父控件 `value` / `Value`。
14. 源快照中存在 `displayMode = "large"`、`hasIcon = true`、`textLines`、`bounds` 或明确截图证据，但生成结果没有逐项说明这些视觉字段如何保留。
15. 视觉审计报告中存在 `unknown` 项，却被汇总为完全通过。

## Layout hard errors

新生成内容出现以下情况时，必须视为错误，不能交付：

1. 任意 `column.layout = "stack"` 中包含 `displayMode = "large"` 的 `button`、`toggle`、`splitbutton` 或 `dropdownbutton`。
   File / Session / New-Open-Save 命令组不是例外；只要是 `large` 命令控件，就必须独占一个 column。
2. 任意 column 中如果包含多个命令型控件，则必须符合 `../reference/layout-rules.md` 中的多命令 column 布局要求；否则必须判为错误。命令型控件包括 `button`、`toggle`、`splitbutton`、`dropdownbutton`。
3. 源应用中具有下拉入口的控件，在生成结果中被降级为普通 `button`，但没有提供可验证证据或调用方明确授权。
4. 源应用中具有下拉入口的控件，生成结果仍为 `splitbutton` / `dropdownbutton` / 等价下拉控件，但没有非空 `items` 或 `menuGroups`。
5. 生成说明中没有列出下拉项提取证据，却声称源控件没有菜单项或允许降级。下拉项提取证据应说明检查过哪些源结构、运行时对象、popup / children / menu item / list item / dynamic popup callback 或可验证源规范。
6. 源控件 class / sourceType / runtime class 是 `DropDownButton`、`SplitButton`、`ListItemWithPopup` 或等价 popup 控件，但目标 `controlType` 是普通 `button`。
7. 源控件是含 checkbox / multiple 菜单项的 `DropDownButton` 或等价 popup 控件，但目标不是 `dropdownbutton`，或缺少父控件 `iconSrc`，或缺少非空 `items` / `menuGroups`，或缺少 `menuSelectionMode = "multiple"`。
8. 源运行时、源码或等价证据已经证明的 source column 边界被目标拆分或合并，且没有 `known_differences.json` / `accepted_difference` / `unknown` 说明。
9. 任意 `matlab-gallery` 的 `column.width` 或 `frameWidth` 小于：

```text
itemWidth * visibleCount + 4 * (visibleCount - 1) + 18 + 2 + 1 + 12
```

10. 两行文字的 `splitbutton` / `dropdownbutton` 需要箭头贴在第二行文字右侧，但缺少：

```json
"layoutVariant": "two-line-dropdown-attached-arrow"
```

11. 源应用中 gallery item、按钮文字或菜单文字存在换行，但生成结果丢失换行，或通过增大 `itemWidth` / `width` 替代换行。
12. 源 gallery 有首选可见项数量且 `visibleCount > 1`，但生成结果缺少足够的 `frameWidth`、gallery `column.width` 或等价宽度预算，导致初始渲染可能折叠为一个可见项。
13. 源菜单项有可勾选多选语义，但父控件缺少 `menuSelectionMode = "multiple"`。
14. 源菜单项有单选语义，但父控件缺少 `menuSelectionMode = "single"` 或等价单选分组约束。
15. 任一菜单项设置了 `checked = true`，但同级父控件缺少 `menuItemMarkStyle = "check"` / `"radio"` 或等价勾选渲染样式。
16. 源普通菜单为互斥选择项时，同一组中生成结果不是“恰好一个 `checked = true`”；除非源运行时证据明确显示没有默认项，否则全 false 或多个 true 都视为错误。MATLAB-style gallery 单选当前项不适用此条，应由父控件 `value` / `Value` 表达当前项。
17. 源 radio 组生成结果中同组控件没有相同 `groupName`，或同组默认值不是恰好一个 `value = true`。
18. 如果当前 Syslab 版本不能原生表达源菜单/单选语义，生成结果必须显式实现等价回调状态同步，并在验收报告中标记为组件差异；不得静默降级为普通命令。
19. 源导出、打开、保存等命令型菜单项为普通 `ListItem` / `ListItemWithPopup`，但生成结果添加了 `checked` 或父控件 `menuSelectionMode`，造成命令菜单被误渲染为选择菜单。
20. 源快照中控件为大按钮，但生成结果将其放入 `stack` 列或改为 `displayMode = "small"`，且没有调用方明确授权或 `known_differences.json` 记录。
21. 源快照或源截图显示控件有图标，但目标运行时快照显示图标未渲染、退化为文字占位或缺失。
22. 目标运行时快照显示按钮文字、菜单文字或 gallery item 文字重叠、裁剪、覆盖相邻控件，且未被 `visual_audit_report.json` 标为失败。
23. 同一 column 内三个或以上 command 控件均被设置为 `displayMode = "large"`。
24. 源 `DropDownButton` 被映射为 `splitbutton`，或源 `SplitButton` 被映射为 `dropdownbutton`，且没有调用方明确授权或 `known_differences.json` 记录。

## 源应用对标 hard errors

源应用对标任务出现以下情况时，必须判定为生成失败；审计脚本不得把这些问题自动修成通过：

1. 源应用控件具有 split / dropdown / menu / popup 语义，但生成结果是普通 `button`，且没有调用方明确授权。
2. 生成脚本、审计脚本或修复脚本包含 `if not items: return button(...)`、`empty splitbutton -> button`、`empty dropdownbutton -> button`、在空下拉处理分支中把 `controlType` 改为 `button` 等自动降级逻辑，用于掩盖空下拉或提取不完整。
3. 以 `Popup = double`、空 popup、空 `items` 或空 `menuGroups` 作为“无菜单证据”并交付。
4. 未对动态 popup / lazy menu 做交互触发、状态初始化、回调路径检查或递归对象树抽取，却声称下拉内容为空。
5. 源应用真实 UI、截图或录屏中按钮、gallery item 或菜单项为两行显示，但生成结果丢失换行。
6. 只执行 `py_compile`、Julia `include`、`.slapp.code == app.jl` 或结构自洽检查，没有进行运行后 ribbon 视觉验收，却声明“对标完成”。
7. 审计脚本改变源控件语义，例如 `splitbutton -> button`、`dropdownbutton -> button`、字段型 `dropdown` / `combobox` -> `button`、删除下拉箭头、删除源 UI 中存在的换行。
8. 生成器丢弃源控件类型标识、源交互语义或同列控件数量后，只按文本、图标或固定模板重新推断控件类型。
9. 源菜单项是可选择项，但生成结果只作为普通命令项交付，导致用户不能切换或保持选择状态。
10. splitbutton / dropdownbutton 的源菜单项有独立图标，但生成结果只给父控件设置图标，或用父控件图标批量代替 item 图标。
11. 生成器只记录 `sourceIconPath`、`sourceIconClass`、`iconLabel`、CSS class、资源 key、内部 class name、对象句柄、sprite sheet 坐标或 background-position，却没有继续解析源应用资源并在 control/item 上生成可渲染 `iconSrc` / `IconSrc`。
12. 生成器声称使用了 checked / radio / multiple 语义，但 `.slapp.figure.toolstrip`、`.slapp.code` 与外部 `app.jl` 三者中任一处缺少对应状态字段；MATLAB-style gallery 单选当前项的对应状态字段是父控件 `value` / `Value`，不是 item `checked` / `Checked`。
13. 生成器丢弃 `source_ribbon_snapshot.json` 中已有的 `displayMode`、`controlType`、`interaction`、`textLines`、`hasIcon`、`checked`、`section`、`column`、`row` 字段，改用文本启发式或固定模板重猜。
14. 视觉审计报告发现大按钮变小、图标缺失、文字重叠、下拉箭头缺失、section/column 顺序错误，却仍将结果标为通过。
15. 从源码、截图、人工标注或历史 spec 补出的菜单项没有记录 `evidenceSource`，却被当作 live snapshot 事实。
16. 源菜单存在子菜单或层级结构，目标结果被扁平化为普通 `items`，但未写入 `known_differences.json` 或未标记为 `accepted_difference` / `unknown`。
17. 源 gallery / popup 只抽取到第一层 category / popup 容器，未递归读取其 `Children` / `Popup.Children` / 等价字段，却据此生成目标 ribbon 或声明通过。
18. 比对报告只检查 tab / section / control 数量、回调和图标，不比较源 gallery / menu 叶子项数量、文本、tag/value 与分组顺序。

## MATLAB-style Gallery 验证

新生成内容如果涉及源应用风格 gallery，还要检查：

1. 新 spec 不应使用 `section.layout = "matlab-gallery"`；这属于废弃的 section 级模型。
2. 源应用风格 gallery 应建模为普通 `columns` section 内的 `controlType = "matlab-gallery"` 控件。
3. `controlType = "matlab-gallery"` 必须包含非空 `items`。
4. gallery item 的显示文字应写在 `items[].label`，允许包含 `\n` 表示两行文字。
5. `visibleCount` 必须写在 `matlab-gallery` 控件上，不应依赖 section 级 `visibleCount`；缺失视为生成错误。
6. `itemWidth` 和 `frameWidth` 必须写在 `matlab-gallery` 控件上；缺失视为生成错误。不得通过 gallery item column 宽度推导。
7. 如果同一个 section 中既有 gallery 又有普通按钮、radio、checkbox 或 Analyze 类命令，section 必须保持 `layout = "columns"`。
8. 无法从源应用取得首选可见数时，应显式设置 `visibleCount = min(5, items.length)`；不得省略后依赖默认值。
9. 横向空间不足时，gallery 至少保留 `1` 个可见 item，右侧下拉槽位必须始终可见。
10. 下拉 popup 外框应与当前 gallery frame 同宽；压缩状态下应按可用宽度减少 item 列数，避免多个 item 重叠。
11. `.slapp` 生成回调中调用的 helper 必须实际存在于最终生成的 `code` 中；不能只存在于外部编辑过的 `app.jl`，否则设计器重新生成后会出现 `UndefVarError`。
12. 必须校验 `frameWidth >= min(visibleCount, items.length) * itemWidth + 右侧下拉槽位 + frame 内边距`；否则会出现可见区域空白但后续 item 被压缩隐藏。
13. 如果需要区分“点击可见 gallery item”和“从右侧下拉选择”，回调应读取 `event.Item.GallerySource` / `event.Item.gallerySource`，并从 `event.Item.LastMenuItem` / `event.Item.lastMenuItem` 读取被点击/选择的 item；item 内部应兼容 `Value/Label` 与 `value/label`。
14. `matlab-gallery` 应同时配置 `commandInvokedFcn` 和同名 `buttonPushedFcn`，并在点击“运行”后打开的 app 窗口中验证直接点击 item 与下拉选择均能触发同一回调；设计画布不作为回调验证结果。
15. 如果源应用 gallery item 有图标，每个对应 item 必须包含非空且可渲染的 `iconSrc`。`.slapp.figure.toolstrip` 中的 `iconSrc` 应为 `data:image/...`；`app.jl` / `.slapp.code` 中可以使用 `TyAppDesigner.ribbon_icon_src_from_file(joinpath(...))` 指向真实存在的本地图标文件。
16. `iconLabel`、`iconKind`、`icon`、`sourceIconId`、`sourceIconClass`、`sourceIconPath`、源内部图标 id 或资源 key 不能作为可渲染图标验收依据。验证脚本不得以这些字段非空作为 gallery item 图标通过条件。
17. 只给父级 `matlab-gallery` 控件设置 `iconSrc`，但 `items[]` 缺少可渲染 `iconSrc`，不能视为 item 图标已完成；源 item 有图标时这属于生成错误。
18. `matlab-gallery` 所在 section / column / frame 必须允许 flex shrink；窗口压缩时应从最多 `5` 个可见 item 逐步压缩，最少保留 `1` 个 item 和右侧下拉。
19. 如果 `matlab-gallery` 与普通 button、radio、checkbox、Analyze 类命令在同一个 section 中共存，section 的最小宽度必须包含：`1 个 gallery item + gallery 下拉槽位 + 所有非 gallery column 宽度 + column gap + section padding`；不要只按 gallery 自身计算最小宽度，否则窗口压缩时普通列会覆盖 gallery。
20. gallery 压缩到较少可见 item 后，section / gallery column 不应保留无意义的尾部空白；frame 应随实际可见 item 数收口，右侧下拉槽位仍保留。
21. gallery 下拉 popup 应在压缩状态下验证内容无重叠。
22. 同一个 tab 中存在两个或以上 `matlab-gallery` 时，应验证连续拉伸/压缩过程中的可见项数量单调稳定；已恢复显示的左侧 gallery item 不应因另一 gallery 扩张而再次隐藏。
23. `itemWidth` 应接近内容宽度，不得使用统一保守大宽度撑开 gallery；如果 `itemWidth > 88px`，必须提供源应用截图、真实 UI 测量或明确源规范。
24. 如果 gallery item 文本在源应用中为两行，但生成结果通过增大 `itemWidth` 改成一行，视为错误。
25. 如果多个 gallery item 两侧出现明显大空白，导致 gallery frame 或 ribbon 宽度明显超过源应用，应判为视觉对标失败。
26. 源 snapshot、源码或运行时对象中存在 `GalleryCategory` / popup category，但目标 `matlab-gallery` 缺少非空 `menuGroups`，视为生成错误。
27. 目标添加了 `menuGroups`，但删除、清空或缩减了原 `items` 扁平列表，视为生成错误。
28. `menuSelectionMode = "single"` 的 MATLAB-style gallery 必须把当前/默认项写在父控件 `value` / `Value`；`items[]` 与 `menuGroups[].items[]` 不得写 `checked` / `Checked`，否则会造成默认项和点击项同时高亮。只有源证据显示该 gallery item 是 checkbox / multiple / 独立 toggle 状态时，才允许 item 级 `checked` / `Checked`。
29. `menuGroups[].items[]` 只包含 `label` / `value`，缺少原 item 的 `commandId`、`iconSrc` 或其它交互字段，视为生成错误；`checked` / `Checked` 仅在源 item 是 checkbox / multiple / 独立 toggle 状态时才属于必需字段。
30. `menuGroups` 使用 `Title` / `Items` 等大写字段作为 `.slapp.figure.toolstrip` 最终字段，而不是小写 `title` / `items`，视为生成错误。
31. 同一控件内 group `id` 重复，或多个中文分组都被写成同一个 `group`，视为生成错误。
32. `.slapp.figure.toolstrip`、`.slapp.code`、外部 `app.jl` 三者中的 gallery `items` / `menuGroups` 不一致，视为生成错误。
33. 运行后 gallery 主体可见 item 可点，但 popup item 不可点；或 popup 可打开但点击不触发同一回调，视为交互失败。
34. 对标 MATLAB 时，如果当前 `source_ribbon_snapshot.json` 只有扁平 `items`，但源码或截图显示该 gallery 有分组，生成器不得以“snapshot 无分组”为由交付无 `menuGroups` 结果。
35. 对标 MATLAB 时，必须递归读取 `GalleryCategory.Children` 中的 `ToggleGalleryItem` / `GalleryItem`。若只读取到 `GalleryPopup.Children` 的 category 列表，`recursiveExtractionStatus.status` 必须为 `fail` 或 `unknown`，不得继续声明 gallery 内容完整。
36. MATLAB gallery 验收必须同时比较 category 数量、category title 顺序、叶子 item 总数、每个 item 的 `Text`、`Tag`、选中状态和值语义。只比较 gallery 控件本身存在或 category 数量不足以通过。

## 为什么这些规则重要

这些规则主要是在防下面几类退化：

- 从正式 ribbon API 退回到 HTML 假 ribbon
- 从 `source-spec-first` 退回到脚本打包优先
- 从单一真相源退回到多处重复定义
- 从正式图标链退回到本地文件 URI 依赖

## 预期验证结果

理想产物至少应满足：

1. 业务结构真实存在于 `.slapp.figure.toolstrip` 中
2. 不依赖 `uihtml` 伪装 ribbon
3. 不依赖 `file:///` 本地路径图标
4. 不混用互相覆盖的多条定义链
5. 如果 `.slapp` 已有静态业务 ribbon，则启动函数不再重复设置整份 ribbon
6. 源应用风格 gallery 使用控件级 `matlab-gallery`，并且能与同 section 内普通控件共存
7. 新生成运行代码使用组件化 Toolstrip 构造链；不再用整树 `Dict{String,Any}` 表达 ribbon 实体。复合业务载荷内部为兼容运行时仍可使用 `Dict`，但不能替代 `Toolstrip` / `ToolstripTab` / `ToolstripSection` / `ToolstripColumn` / `ToolstripControl` / `ToolstripItem` 实体。

## `.slapp` 端到端验收清单

`.slapp` 交付必须执行以下验证：

1. 使用 Syslab App Designer 打开 `.slapp`。
2. 点击“运行”，确认重新生成后的 `app.jl` 中不存在裸 `undefined`。
3. 确认生成后的 `app.jl` 包含所有控件已绑定的回调函数，且 `.slapp.callbackFunctions` 存在同名定义。
4. 点击普通 button，确认反馈格式为 `分组名 + 组件名`。
5. 修改 `editbox`，确认反馈格式为 `分组名 + 组件名 + 值`。
6. 选择字段型下拉值，确认值可变化并返回正确反馈；源应用 `DropDown()` 字段不得误用 `dropdownbutton` / `splitbutton`。
7. 点击 `splitbutton` / 菜单项，确认回调能读取具体子项值。
8. 点击 gallery 可见 item 与 popup item，确认都能读取具体选项，并能区分触发来源。
9. 关闭并重新打开 `.slapp` 后重复第 2 至 8 项，确认设计器重新生成不会丢失回调或重引入非法代码。
10. 对源应用有显式字段列宽的 section，确认设计器预览与运行窗口中的 `editbox` / 字段型下拉均继承相同列宽。
11. 源应用对标任务必须记录运行后 ribbon 视觉验收结果，至少包括控件类型、下拉箭头、文本换行、hover 区域、图标文字重叠、同组按钮对齐。
12. 验收报告必须区分运行性检查、结构检查、视觉检查和未完成项；不能用 Julia `include OK` 代替源应用对标验收。
13. 对标任务必须把 `visual_audit_report.json` 中的 `fail`、`unknown`、`accepted_difference` 分开展示；只有全部关键项为 `pass` 或调用方接受的 `accepted_difference` 时，才允许声明视觉验收完成。

## 与其它文档的关系

- 通用规则：`ribbon-rules.md`
- 组件说明：`../reference/components.md`
- 布局规则：`../reference/layout-rules.md`
- 源应用风格规则：`../source/source-generation.md`
