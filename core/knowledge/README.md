# core/knowledge — 知识库导航

> 治理规则真源：`docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md`。
> 核心哲学：**方法卡 = Constraint / Prior / Validation，不是答案库**。

## 目录结构

| 目录 | 内容 | 规模（实测） |
|---|---|---|
| `methods/cards/` | 方法卡（mc-*.yaml） | 24 |
| `methodology/` | 方法论条目 | 54 |
| `failures/` | 失败模式库 | 17 |
| `cookbooks/` | 操作手册 | 8 |
| `playbooks/` | 战术剧本 | 13 |
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
| `paper-cases/` | 历史论文案例（V2 时代遗留，阶段五待裁定更名 T-CONF-004） | 10 |

## 检索入口

```powershell
py -3.12 core/tools/knowledge.py recommend --types evaluation,ranking
# 可选：--no-data（无题给数据）/ --sample small|medium|large / --timeseries
```

## 历史数据目录说明

- `bench/e2e/artifacts/`：e2e 引擎演练产物（每赛题一个目录，含盲评 blind/ 子目录）——**保留为实验证据，不删除**。
- `empirical/`：实证研究数据，1 个文件。
- `paper-cases/`：V2 论文链时代的案例；V3 不含论文生成，该目录为历史遗留，更名/归档状态见 T-CONF-004。
