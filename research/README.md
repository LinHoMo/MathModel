# Research Directory / 研究目录

> 本目录存放研究实验与审计报告，**不被 core/runtime 消费**。
> 所有 research 产物遵循 `research→core 无直接 import` 铁律。

## 目录总览

| 目录 | 性质 | 说明 |
|---|---|---|
| `ENGINEERING/` | 工程验证 | v3.1.0 架构验证闭环（G6 Replay / G7 Reconcile / G8 Failure Propagation）的正式结果与证据归档：`ARCHITECTURE_VALIDATION_CLOSE.md`（关闭报告）、`DEBT_REGISTER.md`（已观测架构债务登记）、`evidence/`（验证脚本与 gates 归档） |
| `P15/` | 当前活跃 | Competition Model Construction Program：以 CUMCM 真题为输入的能力训练 + 可控评测基准。K001 / K002 / K003 已 CLOSED，K004 进行中。**入口见 [P15/README.md](P15/README.md)** |

> **P15 保留在主树**：T-CONF-001 裁定（2026-09-10）——P15 是 Constructor 协议实验证据（K001–K004），与主仓库定位直接相关，**不移出**到独立仓库；全部实验数据随主仓库版本化保留。

## 铁律

- **research→core 无直接 import**：research/ 下的脚本不得 import core/ 模块
- **research 产物不回流 core/**：研究产物留在 research/，不迁入 core/
- **历史证据不删除**：实验产物（含 negative 结果、原始数据、落盘 registry/evidence graph）具有科研证据价值，禁止删除；P15 保留在主树，随仓库版本化完整保留数据、谱系与报告

## 历史目录说明

早期实验目录（P13 系列 / P14 / bench-m4 系列 / RC-SMOKE / REPOSITORY_AUDIT 等）已随 v3.2.2「V2 残留彻底清除」从主树移除，其相关状态与结论以 `docs/STATUS.md` 为准；本仓库当前保留的全部实验数据位于 `research/P15/`。
