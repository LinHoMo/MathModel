# MATLAB -> Julia 强工作流合同

## 目的

定义唯一合法的执行路径。任务必须先做工程解析，再落计划，再按任务列表推进转换、测试和报告；阶段不适用时允许写 `N/A`，但不允许跳步。

## 唯一执行顺序

1. 工程解析
2. 建立转换计划
3. 逐脚本转换
4. 逐脚本测试
5. 整体测试
6. 输出迁移与测试报告

## 前置动作

进入正式迁移前，必须先完成：

- 首先读取 `../references/high_frequency_conversion_differences.md`
- 读取 `../rules/translation-rules.md`
- 盘点全部 `.m` 文件、目录结构、入口脚本和工具箱依赖
- 生成脚本级依赖关系图
- 生成函数映射待办表
- 盘点不清时，运行 `julia ../scripts/scan-matlab-project.jl <matlab-project-root>`

工程解析完成后，必须使用 `../templates/translation-plan-template.md` 创建 `docs/plan.md`。

`docs/plan.md` 必须直接包含：

- 工程解析结果
- 源 `.m` 到目标 `.jl` 的一对一映射表
- 逐脚本转换任务
- 逐脚本测试任务
- 整体测试任务
- 报告任务

没有 `docs/plan.md`，或 `docs/plan.md` 中没有完整任务列表，不允许开始任何代码转换。

## 一页总览

| 阶段 | 名称 | 必须产物 | 未完成时禁止事项 |
| --- | --- | --- | --- |
| 1 | 工程解析 | 文件清单 + 目录统计 + 依赖图 + 函数映射待办表 | 禁止承诺具体实现 |
| 2 | 建立转换计划 | `docs/plan.md` | 禁止改代码 |
| 3 | 逐脚本转换 | Julia 输出代码 + 映射记录 + `docs/issues.md` | 禁止跳过完整源代码阅读 |
| 4 | 逐脚本测试 | 每个脚本的测试结论回填 | 禁止进入整体测试 |
| 5 | 整体测试 | `docs/test_design.md` + `docs/test_report.md` + 主入口结论 | 禁止只用脚本级测试代替整体验证 |
| 6 | 输出迁移与测试报告 | `docs/translation_report.md` + `docs/compliance_report.md` | 禁止宣告完成 |

## 任务模型

`docs/plan.md` 中只允许使用下面四类任务：

- `convert:<script>`
- `test-script:<script>`
- `test-overall:<main-script>`
- `report:<artifact>`

任务约束：

- 1 个 MATLAB `.m` 文件对应 1 条 `convert:<script>` 任务。
- 1 条 `convert:<script>` 任务只能产出 1 个目标 Julia `.jl` 文件。
- 1 个已转换脚本对应 1 条 `test-script:<script>` 任务。
- 1 个主脚本 / 入口脚本对应 1 条 `test-overall:<main-script>` 任务。
- 禁止把多个脚本合并成同一条转换任务或整体测试任务。

每个任务至少记录：

- 任务标识
- 输入脚本或目标产物
- 前置依赖
- 当前状态：`⚪ pending`、`🟡 in_progress`、`🟢 done`、`🔴 blocked`、`⚫ N/A`
- 备注或阻塞原因

## 强制读取顺序

1. `../references/high_frequency_conversion_differences.md`
2. `../rules/translation-rules.md`
3. `../templates/translation-plan-template.md`
4. `../references/test_guide.md`
5. `../rules/translation-acceptance-checklist.md`

## 无效完成模式

出现下面任一情况，都不能判定为完成：

- 没有首先读取 `../references/high_frequency_conversion_differences.md`
- 没有完成工程解析就开始计划或转换
- 没有 `docs/plan.md`
- `docs/plan.md` 中缺失映射表或任务列表
- 把多个脚本合并成 1 条转换任务
- 把多个主脚本合并成 1 条整体测试任务
- 没有读取入口脚本和被调用函数的完整实现
- 没有做函数映射就手写替代实现
- 只做脚本级测试，没有整体测试
- 没有 `docs/translation_report.md`
- 没有 `docs/test_report.md`
- 没有 `docs/compliance_report.md`
