# Contributing / 贡献指南

## 仓库性质

这是一个**个人研究仓库**（GitHub：LinHoMo/MathModel），定位为可信 Harness
（V3 认知工作流运行时）：输入赛题，产出 MODEL_IR（JSON）+ 模型描述文档（MD/Mermaid）。
core 内 LLM-free，不含论文生成，不向后兼容 V2。

- **欢迎 issue 讨论**：研究问题、实验设计、文档勘误、术语争议等都可以开 issue。
- **不接受 PR**：本仓库为单作者直推模式（无 PR 流程），外部改动请先在 issue 中讨论；
  作者会在需要时自行合入对应内容。

## 本地环境

- Python：`3.12`（仓库根目录 `.python-version` 已固定，Windows 下用 `py -3.12`）
- 运行时依赖：**零第三方依赖**（不新增任何第三方运行时依赖是硬约束）

## 如何跑测试

```powershell
py -3.12 -m pytest tests -q          # 全量测试（基线：595 passed）
```

## 如何跑三件套校验（每阶段/每次提交前必跑）

```powershell
py -3.12 core/tools/validate.py                # 项目级 45 项校验
py -3.12 core/tools/catalog_check.py --check   # catalog 双视图三方一致
py -3.12 core/tools/catalog_check.py --check-terminology  # 术语一致性
py -3.12 -m pytest tests -q                    # 基线测试
```

四项全部通过才允许提交。

## Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

- `feat` / `fix` / `refactor` / `chore` / `test` / `docs`
- 单 commit 单意图：每个提交只做一件事
- 示例：`docs(p0): fix stale V2 references and doc inconsistencies`

## 行为约束（详见 AGENTS.md）

- 禁止修改 `core/schemas/v3/` 下的 canonical schema
- 禁止修改 `core/runtime/` 下的业务逻辑代码（文档/配置/基线任务除外）
- 禁止伪造 ExecutionResult 或回填 STATUS.md 数字
- 允许"同类事实修正"，但须在汇报中单列范围外修正清单并附证据

## 更多信息

- 状态真源：`docs/STATUS.md`
- Agent 开发协议：根目录 `AGENTS.md`
- 任务看板：`TASKS.md`
