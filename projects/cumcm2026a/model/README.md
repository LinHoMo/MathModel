# cumcm2026a

> 建模产出目录。Source of truth = Artifact Registry + Evidence Graph。

## 元信息

- **竞赛**: cumcm
- **状态**: 已建模（四件套契约已产出）

## 产出物索引（均位于项目根目录）

| 产物 | 位置 | 状态 |
|------|------|------|
| 赛题原文 | `inputs/problem.txt` | 已导入 |
| 模型表示（MODEL_IR） | `model_ir.json` | 已生成 |
| 模型描述文档 | `model.md`（含 Mermaid） | 已生成 |
| 数值结果台账 | 结果 JSON（项目根） | 已生成 |
| 执行证据 | `artifacts/results/` | 已生成 |
| 运行状态 | `state/`（registry / evidence_graph / decision_log / status） | 已初始化 |

## 目录索引（V3）

| 目录 | 说明 |
|------|------|
| `inputs/` | 赛题原文（唯一输入） |
| `state/` | runtime 状态 |
| `artifacts/` | Artifact Registry 落盘区（code/results） |
| `model/` | 交接文档与附加说明 |

> 交付物统一位于**项目根目录**，与 V3 校验契约一致（不在 `model/` 子目录）。
