# Research Directory

> 本目录存放研究实验与审计报告，**不被 core/runtime 消费**。
> 所有 research 产物遵循 `research→core 无直接 import` 铁律。

## 目录结构

| 目录 | 性质 | 说明 |
|---|---|---|
| `P13-3D/` | 历史证据 | P13 首轮实验（negative but informative） |
| `P13-3D-R2/` | 历史证据 | P13 复现实验（冻结 output） |
| `P13-3D-R3/` | 历史证据 | P13 真实 Writer 对照实验 |
| `P14/` | 历史证据 | P14 pilot PASS（21/21 replay match） |
| `P15/` | **当前活跃** | Competition Model Construction Program |
| `bench-m4-2000c/` | 基准 | M4 基准运行（regression test 引用） |
| `bench-m4-2000c-p131-b/c/` | 历史 | P13-1 变体 |
| `bench-m4-2000c-p132-a/b/c/` | 历史 | P13-2 变体 |
| `bench-p132-2023c/` | 历史 | P13-2 2023C 题 |
| `RC-SMOKE/` | 历史证据 | RC-S1/S3 PASS 证据 |
| `REPOSITORY_AUDIT/` | 审计 | 仓库审计系列文档 |

## 铁律

- **research→core 无直接 import**：research/ 下的脚本不得 import core/ 模块
- **research 产物不回流 core/**：研究产物留在 research/，不迁入 core/
- **历史证据不删除**：P13/P14/RC-SMOKE 等实验产物具有科研证据价值，禁止删除
