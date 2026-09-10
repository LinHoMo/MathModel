# P15 — Competition Model Construction Program

> 本目录是 P15 实验的入口与索引。P15 是 `research/` 下当前唯一活跃实验线：
> 把 CUMCM 真题变成**能力训练 + 可控评测基准**，验证 Harness 的 Model Construction
> 能力差异（Alignment / Construction / Consistency / Solving / Validation）。
> 轨道纪律：全程不进 `core/`，`research→core 无直接 import`。

## 1. 研究目标

回答「Harness 的 Model Construction 能力差异能否跨模型家族泛化到 CUMCM 全题库」，
通过 K 系列受控实验（预注册 → 冻结 → 盲评 → 配对分析）逐题测量结构化表示与
执行闭环对建模质量的因果效应。

## 2. K 系列状态

| 实验 | 状态 | 主结论（实测，非占位） |
|---|---|---|
| **K001**（2×2 知识×案例 + Sham） | ✅ CLOSED | **NEGATIVE**：知识注入 Δ=+2.14，CI 触 0，符号置换 p=1.0；方法族命中率 22%——知识卡作为 Constraint/Prior 定位正确，但无法证明「knowledge → better construction」 |
| **K002**（Model Representation Efficacy，F/S/SV 三臂） | ✅ CLOSED | 主终点 **NEGATIVE**：S−F(MCQ) Δ=−4.85 CI[−7.98,−2.22]；**Validation POSITIVE**：SV−F(VAL) +4.81（STATUS 记录）——纯表示层（无执行）不产生价值，验证义务结构化有正效应 |
| **K003**（Executed Construction，F/S/SV 三臂） | ✅ CLOSED | **POSITIVE**：S−F(MCQ) +3.76 CI[+2.13,+5.44]（d=1.01）、SV−F(VAL) +39.92；正效应全部来自 L4 验证层，L2 构造层为负 →「验证义务 + 执行闭环 > 表示格式」实证；κ=0.260 如实披露 |
| **K004**（Constructor-Independent Benchmark） | 🔄 进行中 | 预注册 v1.0（4 Constructor × 2 Runtime × 8 题 × 2 seeds = 64 runs）；Reference Constructor（LLM-free）32 runs 已完成（exec 16/16、val 16/16）；待 gen/lin/mma 构造器与完整矩阵 |

详细数据与谱系见各正式报告（§4）。

## 3. 实验地图（目录用途）

| 目录 | 用途 |
|---|---|
| `protocol/` | **实验协议层**：预注册（`preregistration/P15-K00x-*.md`）、实验合同（`P15-EXPERIMENT-CONTRACT-v2.md`）、冻结规格（`frozen_specs*`：case/problem/knowledge set + prompt templates + hashes）、schema |
| `analysis/` | **分析层**：正式报告（`analysis/reports/` 为规范报告目录）、分析脚本、盲评产物（`raw_k002/ raw_k003/`）、审计文档 |
| `experiments/` | **运行实例层**：每次实验的实际运行产物（`P15-K00x/` 与 `p1-vs001/` 等），含落盘 registry / evidence graph / result / replay 报告 |
| `benchmark/` | **基准语料层**：`CUMCM-Bench-v2.json`（32 题 × 7 金标准字段）、`problem_cards/`、`manifests/`、`b0_manifests/`、`arena/`（能力竞技场） |
| `capability/` | 能力评测 rubric 与维度定义（`MODEL_CONSTRUCTION_RUBRIC.md` v1.1 等） |
| `cases/` | 案例集（K001 案例样本） |
| `catalog/` | P15 本地 catalog（indexes：by_family / by_capability / by_failure_mode） |
| `schemas/` | P15 本地 schema（`p15_capability_tags.schema.json` 等） |
| `scripts/` | 实验驱动脚本（k00x_*.py：预注册 / 盲打包 / 冻结 / 状态 / 泄漏扫描） |
| `reports/` | 基线报告（B0 baseline / measurement recovery / attribution） |
| `k004/`、`vs001_run/`、`m3_run/`、`m4_run/`、`dryrun/`、`knowledge_calibration/`、`measurement_recovery/`、`model_representation/` | 各专项实验/校准/测量的工作目录（运行器 + 落盘产物） |
| `constructor_integration/` | **Constructor 集成实证（T-CONF-003）**：外部 Agent 产物目录（`mma_out/`）→ MathModelAgentAdapter → ConstructionBundle → apply_bundle → 引擎主链真实执行，最小闭环证据（`run_demo.py`） |

## 4. 报告索引（规范路径）

正式（canonical）报告：

| 报告 | 路径 | 内容 |
|---|---|---|
| K001 正式报告 | `analysis/reports/P15-K001-REPORT.md` | 知识注入无效性（negative） |
| K002 正式报告 | `analysis/reports/P15-K002-REPORT.md` | 表示层负 / 验证义务正 |
| K003 正式报告 | `analysis/reports/P15-K003-REPORT.md` | 执行闭环正效应（positive） |
| K004 进度报告 | `k004/reports/P15-K004-REPORT.md` | Reference Constructor baseline（32 runs） |
| P1-VS001（2024_A 垂直切片） | `analysis/P1_VS001_REPORT.md` | 可执行模型构造闭环（2024_A Q1 正向运动学；C6–C10，890 passed） |
| P1-VS001（2019_C M0/M1/M2） | `experiments/p1-vs001/P1-VS001-REPORT.md` | 早期闭环（2019_C 排队模型；ids/evidence_graph 最小改动，882 passed） |
| P1-M3 / P1-M4 | `analysis/P1_M3_REPORT.md` / `analysis/P1_M4_REPORT.md` | M3 候选竞技场 / M4 知识引导构造 |
| B0 基线 | `reports/B0_BASELINE_REPORT.md`、`reports/B0_R2_BASELINE_REPORT.md` | P15.1 对齐基线（5 题） |
| 测量恢复 | `reports/MEASUREMENT_RECOVERY_REPORT.md`、`reports/MEASUREMENT_FAILURE_ATTRIBUTION.md` | 失败归因与测量恢复 |
| 能力增量 | `analysis/CAPABILITY_DELTA_REPORT.md` | 能力维度增量分析 |

> 注：`analysis/P1_VS001_REPORT.md` 与 `experiments/p1-vs001/P1-VS001-REPORT.md` 是
> **两个不同实验**（2024_A vs 2019_C），均保留为正文，不做合并。

其余运行级报告（precheck / dryrun / arena / 治理等）见各自目录内的 `*_REPORT.md`。

## 5. 铁律

- **预注册先行**：实验设计（假设、主终点、功效、判定规则、止损）必须先预注册并冻结，冻结后只读；任何偏离须走 REVISION 流程。
- **盲评隔离**：评估者只见匿名 bundle，不得见实验臂标签与构造来源；κ 值与锚定澄清如实披露。
- **配对分析**：同一 block 内配对比较（bootstrap / 符号置换），主检验 block 结构在预注册中固定。
- **负结果如实披露**：negative / inclusive 结果与 positive 同等有效，必须完整写入正式报告；禁止为「通过」调参或选择性报告。
- **随机种子 42**：多种子运行 ≥5 次，报告均值与标准差。
- **所有数值可追溯**：数字必须来自已验证的落盘 Result Artifact / registry / replay 报告，无占位符、无伪造引用。
