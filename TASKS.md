# Task Board / 任务看板

> 本文件是 Agent 任务的唯一登记处（见 AGENTS.md §1 必读顺序第 4 项）。
> 状态真源：`docs/STATUS.md`；本看板登记**任务级**状态（进行中/待办/已完成），两者不重复记账。
> 已裁定项（T-CONF-xxx）关闭时在「已完成」登记裁定结果。

## In Progress / 进行中

| ID | Task | Agent | Status | Acceptance |
|----|------|-------|--------|------------|
| T-P0-08 | 重写 AGENTS.md（中英双语，10 节） | MainAgent | 实现中（阶段三） | ≥180 行；10 节齐全；`grep -c "" AGENTS.md` ≥ 180 |

## Todo / 待办

| ID | Task | Priority | Acceptance | Blocked By |
|----|------|----------|------------|------------|
| T-P0-09 | 创建 TASKS.md（本文件） | P0 | Todo ≥15 条、Done ≥8 条；含 ID/优先级/验收/依赖 | — |
| T-P0-10 | 创建 prompts/ 目录（6 文件） | P0 | planner/implementer/tester/reviewer/task-template/README 存在；每份含角色/输入/输出/禁止 | — |
| T-P1-06 | 创建 docs/README.md 文档索引 | P1 | 覆盖 docs/ 全部 .md；无断裂链接 | — |
| T-P1-07 | 创建 ADR 体系（7 文件） | P1 | 每份含 6 字段；与 V3.1_ARCHITECTURE 一致 | — |
| T-P1-08 | CONTRIBUTING.md 补分层依赖说明 | P1 | 含「运行时零依赖」与「测试依赖 pyyaml/jsonschema/ripgrep」两节 | — |
| T-P1-09 | core/runtime/README.md | P1 | 子域说明；≤80 行；指向真源 | — |
| T-P1-10 | core/tools/README.md | P1 | 15 个 CLI 一句话说明；≤80 行 | — |
| T-P1-11 | core/knowledge/README.md | P1 | 知识库结构与检索入口；≤80 行 | — |
| T-P1-12 | catalog/README.md | P1 | 双视图元数据说明；≤80 行 | — |
| T-P1-13 | tests/README.md | P1 | 测试分层说明；≤80 行 | — |
| T-P2-01 | research/P15 移出主树（迁移 ≠ 删除） | P2 | 主仓不含 research/P15；research/README 含新地址 | T-CONF-001 |
| T-P2-02 | 顶层 V2 schema 归档（legacy/） | P2 | core/schemas/README 明确 v3/ 唯一 canonical | — |
| T-P2-03 | 空目录与 V2 词清理（paper-cases→cases） | P2 | git status 干净；pytest 通过 | T-CONF-004 |
| T-P2-04 | pyproject version 同步 | P2 | 若改：与 tag v3.2.2 一致 | T-CONF-002 |
| T-P2-05 | 发布流程文档 docs/RELEASE.md | P2 | 含版本号/tag/release notes/CI 四节 | — |
| T-P3-01 | K004/K005 实验模板 | P3 | protocol/ 下 2 个模板存在；含 6 节 | — |
| T-P3-02 | 新实验方向决策（K 系列 vs Constructor 集成） | P3 | 决策记录进 TASKS.md | T-CONF-003 |
| T-CONF-001 | 待确认：research/P15 独立仓库地址 | — | 地址回填 research/README.md 与 TASKS.md | 用户 |
| T-CONF-002 | 待确认：pyproject version 是否改为 3.2.2 | — | 裁定后执行 T-P2-04 | 用户 |
| T-CONF-003 | 待确认：K004/K005 具体研究问题 | — | 裁定后执行 T-P3-01/02 | 用户 |
| T-CONF-004 | 待确认：paper-cases 更名是否影响外部引用 | — | 引用扫描后裁定 | 用户 |

## Done / 已完成

| ID | Task | Commit | Date |
|----|------|--------|------|
| T-P0-01 | 重写 research/README.md（仅 ENGINEERING/ 与 P15/） | `d3c4f83` | 2026-09-10 |
| T-P0-02 | 创建 research/P15/README.md（K 系列状态+实验地图+报告索引） | `d3c4f83` | 2026-09-10 |
| T-P0-03 | 清理 docs/architecture/ 论文残留（6 文件 14 处） | `d3c4f83` | 2026-09-10 |
| T-P0-04 | 修复 pyproject.toml markers（COMPATIBILITY_POLICY/Syslab/LaTeX） | `d3c4f83` | 2026-09-10 |
| T-P0-05 | 修复数字不一致（58→45；五组→六组） | `d3c4f83` | 2026-09-10 |
| T-P0-06 | 清理 .gitignore LaTeX 段 + main.aux 残留 | `d3c4f83` | 2026-09-10 |
| T-P0-07 | VS001 报告核验：两份为不同实验，保留正文 | `d3c4f83` | 2026-09-10 |
| T-P1-01 | LICENSE（MIT，LinHoMo） | `b34cb4e` | 2026-09-10 |
| T-P1-02 | .python-version（3.12） | `b34cb4e` | 2026-09-10 |
| T-P1-03 | CI 添加与修复（push main；pyyaml/jsonschema/ripgrep） | `b34cb4e`+`e19a24a`+`18e49ea` | 2026-09-10 |
| T-P1-04 | CONTRIBUTING.md（个人仓库声明，不接受 PR） | `b34cb4e` | 2026-09-10 |
| T-P1-05 | v3.2.2 tag + GitHub Release | `b34cb4e`（tag 锚点） | 2026-09-10 |
| T-CONF-005 | 裁定：VS001 两份报告保留，不删除不合并 | 阶段一裁定（无 commit） | 2026-09-10 |
