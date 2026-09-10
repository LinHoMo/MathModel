# Task Board / 任务看板

> 本文件是 Agent 任务的唯一登记处（见 AGENTS.md §1 必读顺序第 4 项）。
> 状态真源：`docs/STATUS.md`；本看板登记**任务级**状态（进行中/待办/已完成），两者不重复记账。
> 已裁定项（T-CONF-xxx）关闭时在「已完成」登记裁定结果。

## In Progress / 进行中

| ID | Task | Agent | Status | Acceptance |
|----|------|-------|--------|------------|
| — | 阶段七（新实验模板 P3）待启动；前置：T-CONF-003（K004 已存在，方向确认） | MainAgent | 待确认 | 阶段六已交付，等待用户裁定后进入 |

## Todo / 待办

| ID | Task | Priority | Acceptance | Blocked By |
|----|------|----------|------------|------------|
| T-P3-01 | K005 模板 + K004 protocol 整理（K004 实验已存在于 P15/k004） | P3 | protocol/ 下模板存在；含 6 节 | — |
| T-P3-02 | 新实验方向决策（K 系列 vs Constructor 集成实证） | P3 | 决策记录进 TASKS.md | T-CONF-003 |
| T-CONF-003 | 待确认：K004 已有实验与报告——继续补 K005，还是转向 Constructor 集成实证 | — | 裁定后执行 T-P3-01/02 | 用户 |

## Done / 已完成

| ID | Task | Commit | Date |
|----|------|--------|------|
| T-REBUILD-01 | 技术层重构（src/ layout、modeling_harness 包、mh CLI、MH_* env、.mh/ 配置、MH- ID、modeling_harness.* schema、迁移脚本） | `1b5e2e7`+`e4add47`+`65be4d8`+`ef2afe8`+`8838fda`+`1cebd09`+`68e90be`+`6ee233c`+`bdaddbc`+`9913a2b`+`86e087e`+`b684856`+`6408f35`+`63f5ddc`+`40d1989`+`1b58fee`+`062c357` | 2026-09-10 |
| T-REBUILD-02 | 终审整改：L1.1 校验真实输入规约（44/1 修复）；schemas/legacy → retired 归档更名；domains/ adapters/ 上提顶层（ADR-0006）；迁移垃圾清理（build/、__pycache__、.pytest_cache、worktree 残留、一次性脚本） | `40d1989`+`1b58fee`+`062c357`（垃圾清理不入库） | 2026-09-10 |
| T-BRAND-01 | 品牌迁移 MathModel → Modeling-Harness（品牌层替换 + 发行名 + MIGRATION.md + CHANGELOG 条目 + GitHub 改名/description/topics） | `9809047`+`6663d02`+`550f9ef`；GitHub 已改名 | 2026-09-10 |
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
| T-P0-08 | 重写 AGENTS.md（中英双语，323 行，12 节） | `0a1e425` | 2026-09-10 |
| T-P0-09 | 创建 TASKS.md（本文件） | `0a1e425` | 2026-09-10 |
| T-P0-10 | 创建 prompts/（6 文件） | `0a1e425` | 2026-09-10 |
| T-P1-06 | 创建 docs/README.md 文档索引（33 链接全通） | `0a1e425` | 2026-09-10 |
| T-P1-07 | 创建 ADR 体系（7 文件） | `0a1e425` | 2026-09-10 |
| T-P1-08 | CONTRIBUTING.md 补分层依赖说明 | `0a1e425` | 2026-09-10 |
| T-P1-09 | core/runtime/README.md（23 行，12 子域） | `71a0310` | 2026-09-10 |
| T-P1-10 | core/tools/README.md（25 行，15 CLI） | `71a0310` | 2026-09-10 |
| T-P1-11 | core/knowledge/README.md（32 行，含历史目录说明） | `71a0310` | 2026-09-10 |
| T-P1-12 | catalog/README.md（21 行，双视图） | `71a0310` | 2026-09-10 |
| T-P1-13 | tests/README.md（20 行，分层+夹具） | `71a0310` | 2026-09-10 |
| T-P1-14 | 14 份 architecture 文档补版本头（Version/Status/Updated） | `71a0310` | 2026-09-10 |
| T-P2-06 | AGENTS.md 七处修正（六要素/去硬编码/CI 门禁/§5 禁令/§7.1 文档纪律） | `117aecb` | 2026-09-10 |
| T-P2-07 | 代码内断裂引用修复（e2e_metrics/benchmark/catalog_check） | `0eddf45` | 2026-09-10 |
| T-P2-08 | 顶层 9 个 V2 schema 归档 legacy/ + 双 README | `596e756` | 2026-09-10 |
| T-P2-09 | fixture 处置：删 sample_paper_project，保留 sample_incomplete + README | `fdfa2ec` | 2026-09-10 |
| T-P2-03 | paper-cases → cases 更名（T-CONF-004 裁定：更名保留，117 文件） | `514bb17` | 2026-09-10 |
| T-CONF-005 | 裁定：VS001 两份报告保留，不删除不合并 | 阶段一裁定（无 commit） | 2026-09-10 |
| T-CONF-001 | 裁定：P15 **保留在主树**（撤销移出决策；K001–K004 为 Constructor 实验证据） | 用户裁定 + `ae8ca2a` | 2026-09-10 |
| T-CONF-004 | 裁定：paper-cases 更名 cases 保留（建模知识，非论文产物） | `514bb17` | 2026-09-10 |
| T-P2-04 | pyproject version 1.0.0 → 3.2.2（T-CONF-002 裁定：改） | `528b277` | 2026-09-10 |
| T-P2-05 | 发布流程文档 docs/RELEASE.md（4 节） | `531dd22` | 2026-09-10 |
| T-P2-10 | AGENTS.md 冻结 v1.0 + CHANGELOG 记录 | `7d03bfc` | 2026-09-10 |
| T-CONF-002 | 裁定：pyproject version 改为 3.2.2（与 tag 一致） | `528b277` | 2026-09-10 |
