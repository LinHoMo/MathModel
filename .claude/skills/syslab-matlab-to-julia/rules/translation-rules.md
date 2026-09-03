# MATLAB -> Julia 转换规则

## 参考资料优先级

- 首先阅读 `../references/high_frequency_conversion_differences.md`
- 先使用 `syslab-environment` 提供的 Syslab 环境与文档路径
- 先查 Syslab 函数映射表、Syslab 文档和 `Ty*` 工具箱
- 只有 Syslab/Ty/标准库都不满足时，才考虑替代方案
- 未经用户明确允许，不要引入新的外部包

## 工作流规则

- 先完成工程解析，再建立 `docs/plan.md`，再开始代码转换。
- 任务列表必须直接写在 `docs/plan.md` 正文中。
- 先写任务，再执行任务。
- 不允许只写“整体完成”，必须能回溯到每个脚本和每个主脚本的任务状态。

## 映射与粒度规则

- 1 个 MATLAB `.m` 文件对应 1 条 `convert:<script>` 任务。
- 1 个 MATLAB `.m` 文件对应 1 个目标 Julia `.jl` 文件，默认保持同名。
- 1 个已转换脚本对应 1 条 `test-script:<script>` 任务。
- 1 个主脚本 / 入口脚本对应 1 条 `test-overall:<main-script>` 任务。
- 禁止把多个脚本合并成同一条转换任务或整体测试任务。

## 工程解析规则

- 盘点全部源文件路径、目录结构和入口脚本。
- 生成脚本级依赖关系图。
- 列出待映射 MATLAB 函数。
- 从入口脚本出发，读取被调用函数的完整实现，不要只看函数签名。

## 转换规则

- 每个待转换脚本开转前，都要对照一次 `../references/high_frequency_conversion_differences.md`。
- 每个 MATLAB 函数转换前，先查 `函数映射表.json` 或 调用 Syslab MCP 的 `map_matlab_functions_to_julia`。
- 转换代码时，必须将源码注释一并转换到目标 Julia 文件中，不能省略；注释位置与语义应尽量保持一致。
- MATLAB `pause` / `pause(...)` 暂无等价 Julia 实现，转换时建议注释掉。
- 参数顺序、返回值和调用方式应与 Syslab 文档一致。
- 不要修改原始 MATLAB 目录；转换结果必须写到独立输出目录。
- 默认输出目录：源工程同级的 `<project-name>-translated/`。
- 未经用户明确允许，禁止合并、拆分、重命名文件或函数。
- 找不到等价函数时，记录到 `docs/issues.md`，不要伪造“已支持”。

## 测试规则

- 脚本级测试至少记录：测试入口、输入、结果、结论。
- 逐脚本测试相关测试脚本必须统一写入 `tests/` 文件夹，不要放在 `julia/`、源码目录或其他临时目录。
- 脚本级测试完成前，不允许进入整体测试。
- 整体测试必须依赖 `docs/test_design.md`。
- 每条整体测试任务都应单独记录测试入口、执行结果和结论。
- 主入口脚本端到端运行是强制项。
- 脚本级测试通过不能替代整体测试。

## 问题记录规则

- `Critical`：无等价函数、Simulink 依赖、主入口无法运行
- `Important`：需要适配实现、I/O 或图形接口差异、脚本级测试受阻
- `Minor`：语法差异、注释差异、局部重写
- 所有未闭环问题都写入 `docs/issues.md`
