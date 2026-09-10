# Prompt Library / 提示词库

> 本目录存放四个 Agent 角色的提示词与任务卡模板，供外部 Agent（Doubao / GPT / Claude Code / 人工）接入本仓库时使用。
> 权威协议见根目录 `AGENTS.md`——提示词是 AGENTS.md 的角色化实例化，冲突时以 AGENTS.md 为准。

## 文件说明

| 文件 | 用途 |
|---|---|
| `planner.md` | 规划 Agent：只读，输出实现计划、风险、验收标准 |
| `implementer.md` | 实现 Agent：只改任务卡指定文件，产出 diff 与验证输出 |
| `tester.md` | 测试 Agent：只写/跑测试，报告失败原因 |
| `reviewer.md` | 审查 Agent：只读 diff，检查越界/伪造/数字来源 |
| `task-template.md` | 任务卡模板：五要素（目标/上下文/验收/禁止/验证/回滚） |

## 使用方式

1. 从 `TASKS.md` 认领任务，用 `task-template.md` 生成任务卡。
2. 按任务卡选用对应角色提示词（`planner.md` → `implementer.md` → `tester.md` → `reviewer.md`）。
3. 每完成一步运行任务卡中的验证命令；四件套全过才提交。
4. 汇报时单列「范围外修正清单」（如有）。

## 必读顺序（开始前）

1. `AGENTS.md`（根目录，工作协议）
2. `docs/STATUS.md`（状态真源）
3. `docs/architecture/V3.1_ARCHITECTURE.md`（架构真源）
4. `docs/ONTOLOGY_TERMINOLOGY.md`（术语真源）
5. `TASKS.md`（任务看板）
