---
name: syslab-matlab-to-julia
description: MATLAB 到 Julia 迁移：按强工作流完成工程解析、任务列表生成、1:1 逐脚本转换、逐脚本测试、整体测试和报告输出；默认保持文件名、函数名、目录结构、入口关系和主要控制流，未经用户明确允许禁止重构、合并、拆分或重命名实现。用于将 MATLAB 工程迁移到 Syslab Julia，以及处理迁移过程中的函数映射、测试设计、端到端验证、问题记录和流程合规检查。
---

# Syslab MATLAB 到 Julia 迁移

先使用 `syslab-environment`。相对路径：`../syslab-environment/SKILL.md`。
迁移时优先依赖 Syslab 运行时、Syslab 帮助文档、函数映射表和 `Ty*` 工具箱。涉及绘图时，遵循 `syslab-environment` 中的 TyPlot 规则，不要按 Plots.jl 风格编写。

## 前置阅读顺序

1. 经验总结: `references/high_frequency_conversion_differences.md`   
2. 工作流合同: `workflows/translation-plan-contract.md`
3. 执行规则: `rules/translation-rules.md`

`high_frequency_conversion_differences.md` 是经验总结来源，必须最先阅读，不能后补。

## 核心原则

- 默认按 1:1 保真转换，不做重构或算法再设计。
- 默认要求：1 个 MATLAB `.m` 文件对应 1 个同名 Julia `.jl` 文件；1 个 MATLAB 函数对应 1 个同名 Julia 函数。
- 未经用户明确允许，禁止合并、拆分、重命名文件或函数。
- 转换代码时，必须将源码注释一并转换到目标 Julia 文件中，不能省略；注释位置与语义应尽量保持一致。
- 工具箱优先级固定为：Syslab/Ty 工具箱 > Julia 标准库 > 其他方案。

## 唯一工作流

所有任务都必须按下面顺序推进，不允许跳步：

1. 工程解析
2. 建立转换计划
3. 逐脚本转换
4. 逐脚本测试
5. 整体测试
6. 输出迁移与测试报告

## 强门禁

- 先读 `high_frequency_conversion_differences.md`，再做工程解析、计划、映射和转换。
- 先完成工程解析，再创建 `docs/plan.md`。
- 任务列表必须直接写在 `docs/plan.md` 中，不能只存在于对话或临时输出中。
- 逐脚本转换必须满足：
  - 1 个 `.m` 文件对应 1 条 `convert:<script>` 任务
  - 1 个 `.m` 文件对应 1 个目标 `.jl` 文件
- 逐脚本测试必须满足：1 个已转换脚本对应 1 条 `test-script:<script>` 任务。
- 逐脚本测试相关测试脚本必须统一放在 `tests/` 文件夹中，不要散落在源码目录或其他目录。
- 整体测试必须满足：1 个主脚本 / 入口脚本对应 1 条 `test-overall:<main-script>` 任务。
- 脚本级测试不能替代整体测试。

## 如何落计划

工程解析完成后，读 `templates/translation-plan-template.md`，创建并持续更新 `docs/plan.md`。

默认输出目录结构：

```text
<project-name>-translated/
├── julia/                  # 转换后的 Julia 代码，保持原 MATLAB 工程目录结构
├── tests/                  # 测试脚本与测试产物
├── docs/                   # 计划、报告、问题清单
└── logs/                   # 运行日志
```

计划中至少要有：

- 工程解析结果
- 源 `.m` 到目标 `.jl` 的一对一映射表
- 逐脚本转换任务
- 逐脚本测试任务
- 整体测试任务
- 报告任务

## 小任务与默认任务

- 小任务：整个工程仅包含 1 个本地 `.m` 文件，且该文件代码不超过 `100` 行。
- 只要不满足上面条件，就按默认任务处理。
- 小任务也必须走完整工作流，只是最终文档可以精简。

## 何时读哪些文件

- 工作流约束：`workflows/translation-plan-contract.md`
- 阶段执行：`workflows/translation-plan-execution-rules.md`
- 转换规则：`rules/translation-rules.md`
- 测试设计：`references/test_guide.md`
- 验收：`rules/translation-acceptance-checklist.md`
- 模板：`templates/`
- 示例：`examples/matlab-to-julia-task.md`

## 最低交付

默认任务至少交付：

- `docs/plan.md`
- `docs/translation_report.md`
- `docs/test_design.md`
- `docs/test_report.md`
- `docs/issues.md`
- `docs/compliance_report.md`
- 独立输出目录（见上方默认输出目录结构）

小任务至少交付：

- `docs/plan.md`
- 转换后的 Julia 文件
- 验证结论
- 函数映射与未解决问题记录

## 参考资料

- MATLAB 与 Julia 函数映射：`<SYSLAB_HOME>/Tools/AIAssets/static/FunctionTable/函数映射表.json`
- MATLAB 与 Julia 语言差异：
  - `<SYSLAB_HOME>/Tools/AIAssets/projects/JuliaLanguage/Doc/JuliaLanguage/DifferencesWithMatlab.md`
  - `<SYSLAB_HOME>/Tools/AIAssets/projects/FromMatlabToSyslab`
  - `<SYSLAB_HOME>/Tools/AIAssets/projects/JuliaLanguage/Doc/JuliaLanguage/DifferencesWithMatlab`
- M 与 Julia 互操作：
  - `<SYSLAB_HOME>/Tools/AIAssets/projects/MultiLanguage/Doc/MultiLanguage/TyMLang/Juliacall.md`
  - `<SYSLAB_HOME>/Tools/AIAssets/projects/MultiLanguage/Doc/MultiLanguage/TyMLang/Mcall.md`
