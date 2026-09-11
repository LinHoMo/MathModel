# cumcm2024a-harness

> 建模产出目录。Source of truth = Artifact Registry + Evidence Graph + Result Artifact。
> 布局遵循仓库 V3 项目级门禁口径（项目根放置 MODEL_IR、模型描述文档与结果聚合文件）。

## 元信息

- **竞赛**: cumcm 2024 A「板凳龙闹元宵」
- **模型结构**: geometric_motion / kinematic（刚性链 + 曲线约束运动学）
- **状态**: 已建模（Q1–Q5 全部有真实执行结果与证据链）

## 产出物索引

| 产物 | 路径 | 状态 |
|------|------|------|
| 赛题 | `inputs/problem.txt` | 已导入（SHA256 已绑定进 MODEL_IR） |
| MODEL_IR | `model_ir.json` | 已生成（v1.0，jsonschema PASS） |
| 模型描述 | `model.md` | 已生成（含 Mermaid） |
| 分问结果 | `artifacts/results/result{1..5}.xlsx` | 已生成 |
| 实现代码 | `artifacts/code/` | 已生成 |
| 模型图表（人看） | `artifacts/figures/model-map.html` + `evidence-graph.html` | 已生成（`mh diagram project cumcm2024a`） |
| 运行状态 | `state/` | 已初始化（registry / evidence_graph / decision_log / status） |

## 目录说明（V3）

| 目录 | 说明 |
|------|------|
| `inputs/` | 赛题原文（唯一输入，规范名 `problem.txt`） |
| `state/` | runtime 状态：registry / evidence_graph / decision_log / status + runs/ |
| `artifacts/` | Artifact Registry 落盘区：`code/`（实现）、`results/`（结果）、`figures/`（模型图表） |
| `model/` | 目录说明（MODEL_IR 与模型描述文档按门禁口径置于项目根） |

## 结果速查

| 问 | 量 | 结果 |
|---|---|---|
| Q1 | 0–300 s 全队位置速度 | 67424 行；连杆残差 3.29e-13 m |
| Q2 | 盘入终止时刻 | 397.7836 s |
| Q3 | 最小螺距 | 0.444260 m（44.426 cm） |
| Q4 | 调头曲线 R₁ / R₂ / ψ / L | 3.005418 m / 1.502709 m / 173.118° / 13.621245 m |
| Q5 | 龙头最大速度 | 1.247011 m/s |
