# src/modeling_harness/knowledge — 知识库导航

> 治理规则真源：`docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md`。
> 核心哲学：**方法卡 = Constraint / Prior / Validation，不是答案库**。

## 目录结构

| 目录 | 内容 | 规模（实测） |
|---|---|---|
| `methods/cards/` | 方法卡（mc-*.yaml） | 27 |
| `methodology/` | 方法论条目 | 54 |
| `failures/` | 失败模式库 | 22 |
| `cookbooks/` | 操作手册 | 8 |
| `playbooks/` | 战术剧本 | 14 |
| `patterns/` | 模式 | 6 |
| `pitfalls/` | 易错点 | 4 |
| `problems/` | 问题档案 | 5 |
| `_negative/` | 负例/反模式 | 8 |
| `competition/` | 竞赛规则知识 | — |
| `data-sources/` | 数据源说明 | — |
| `review/` / `validation/` | 评审与校验条目 | — |
| `bench/cumcm/` | 国赛基准语料 | — |
| `bench/e2e/artifacts/` | e2e 运行产物（按赛题归档，含 blind/） | 2019_C~2025_B + p13_3d |
| `empirical/` | 实证数据 | 1 |
| `cases/` | 建模案例知识（原 paper-cases，T-CONF-004 更名：从论文提取的方法-主题图谱/创新点/赛题案例，非论文产物） | 117 |

## 检索入口

```powershell
py -3.12 src/modeling_harness/cli/knowledge.py recommend --types evaluation,ranking
# 可选：--no-data（无题给数据）/ --sample small|medium|large / --timeseries
```

## 历史数据目录说明

- `bench/e2e/artifacts/`：e2e 引擎演练产物（每赛题一个目录，含盲评 blind/ 子目录）——**保留为实验证据，不删除**。
- `empirical/`：实证研究数据，1 个文件。
- `cases/`：建模案例知识（原 `paper-cases/`，T-CONF-004 裁定 2026-09-10 更名）。内容为从论文提取的建模知识（方法-主题图谱、创新点标签、按 A–E 主题与年份组织的赛题案例），服务建模而非论文生成；V3 术语表中 `paper` 为残留词，故更名。
