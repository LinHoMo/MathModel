# R3.2 Pre-Registration — Real Writer Paired Experiment

**Full name**: P13-3D-R3.2 — Structure-Preserving Model-to-Paper Transmission Intervention (Real Writer, Paired Design)
**Date**: 2026-09-07
**Status**: FROZEN (locked before confirmatory generation)
**Supersedes**: `P13_3D_R3_PREREG.md` (R3.1) — R3.1 的 W0 定义废止

---

## 0. 为什么重做（R3.1 的失效点）

R3.1 已完成 48 次评估，但结论不可用于假设检验，原因有二：

1. **W0 是模板产物，不是真实 Writer 产物。**
   `projects/P13-3D-R2/output/papers/*.md` 由 `generate_r2_papers.py` 按固定模板拼装，
   不是 LLM Writer 在 prompt 下生成的文本。用它做对照，测的是"模板 vs LLM"，不是"无映射 vs 有映射"。
2. **测量器本身曾经失效，已修复并校准。**
   STC v1 测的是 Artifact Completeness 而非 Paper Coverage，导致 W0 STC=1.0（与 R2 结论矛盾）。
   STC v2 已重写并通过 Golden Set 校准（Mean F1 = 1.000，阈值 ≥0.90），见 `R3_1_CALIBRATION_REPORT.md`。
   测量链现已可靠，**本次不再修改测量器**。

因此 R3.2 不再修测量器，而是**重建对照组**。

---

## 1. 实验设计

```text
                Frozen Artifact (24: 8Q × 3 arms, SHA256 冻结)
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
      W0 Real Writer                   W1 Real Writer
      (Artifact only)                  (Artifact + Frozen Map)
              │                               │
              ▼                               ▼
        Paper (W0)                       Paper (W1)
              │                               │
              └───────────────┬───────────────┘
                              ▼
                  Same Evaluation Stack
              (STC v2 / Fidelity Gate / Blind PQ)
```

### 1.1 单元与规模

| 项 | 值 |
|---|---|
| 题目 | 8（2019_A, 2022_A, 2017_B, 2022_C, 2020_B, 2024_B, 2023_C, 2024_C） |
| Model arms | 3（B0, MMA, B1-F） |
| Writer conditions | 2（W0, W1） |
| **论文总数** | **8 × 3 × 2 = 48** |

### 1.2 唯一自变量

```text
W0:  Frozen MODEL_ARTIF ──────────────────► Same Writer
W1:  Frozen MODEL_ARTIFACT ─► Frozen
                              MODEL_PAPER_MAP ─► Same Writer
```

除此之外全部冻结：Writer 模型、system prompt、user prompt 模板、论文模板、
temperature / top-p / max tokens / seed、工具权限、上下文、数据访问。

### 1.3 成对生成铁律（R3.2 核心）

> **每一个 (question, arm) 单元的 W0 与 W1 必须在同一批次、由同一 Writer、连续背靠背生成。**

- 禁止"先跑完全部 W0、再看结果、再决定 W1 prompt"。W1 prompt 与 mapping protocol **已经冻结**，
  写入 `projects/P13-3D-R3/prompts/*_W1.json`，本次只执行不修改。
- 生成顺序固定为 **W0 → W1**，W0 落盘后不得回头修改。
- 每篇论文记录 `batch_id` 与 `generated_at`，供批次效应敏感性分析。

### 1.4 旧语料的处置

| 语料 | 位置 | 状态 |
|---|---|---|
| 旧模板 W0（24 篇） | `projects/P13-3D-R2/output/papers/` | `non-confirmatory / template-generated / excluded from R3 hypothesis testing` |
| 旧模板 W1（24 篇） | `projects/P13-3D-R3/output/papers/` | 同上，保留为工程历史 |
| R3.1 pilot 真实 Writer（8 篇） | `projects/P13-3D-R3/pilot_batchA/` | `non-confirmatory / provenance-incomplete`；其中 2019_A 两篇 arm 归属不可判定（B0 覆盖 0.727 vs MMA 0.600），6 篇 2017_B/2022_A 只有 W0 无配对 W1。**仅用作同会话 Writer 稳定性漂移对照（W0_A vs W0_B）** |

---

## 2. 假设集（重新预注册）

记 `STC_meta = mean(candidate_models, selected_model, sensitivity_plan)`，
`STC_core = mean(variables, parameters, constraints, mechanism, assumptions, objective)`。
Δ 一律为 **W1 − W0**，在 24 个 (question, arm) 单元上做**配对**比较。

| ID | 假设 | 判据 |
|---|---|---|
| **H13** | Structural Transmission：映射层提升元模型结构传输 | `ΔSTC_meta ≥ +0.15`（15pp），配对 t / Wilcoxon 单侧 p<0.05 |
| **H14** | Paper Quality：映射层提升论文质量 | `ΔPQ ≥ +0.5`（5 分制 / 或 100 分制 +5），配对单侧 p<0.05 |
| **H15** | Capability Transmission Recovery：B1-F 相对 B0 的 Paper 优势在 W1 下大于 W0 | `(PQ(B1F,W1)−PQ(B0,W1)) > (PQ(B1F,W0)−PQ(B0,W0))`，差值 ≥ +10（100 分制） |
| **H16** | No Unauthorized Mutation：W1 不显著增加篡改 | `Mutations(W1) ≤ Mutations(W0) + 2`（8 题合计），且逐单元配对不劣化 |
| **H17** | Mechanism Evidence：结构增益与质量增益正相关 | 逐单元 `Spearman(ΔSTC_meta, ΔPQ) > 0.5` |
| **H18** | **Core Preservation（零假设式 guard）**：W1 不得靠牺牲核心数学结构换取元模型覆盖 | `ΔSTC_core ≥ −0.05`，且无单元出现 `STC_core` 下降 > 0.15 |

### 2.1 为什么必须加 H18

Mapping Layer 最危险的失败模式是**元模型表达变好、核心模型反而被压缩**：

```text
candidate_models ✔   selected_model ✔   sensitivity_plan ✔
但 objective / constraints / mechanism 被压掉
```

理想结果必须同时满足：

```text
STC_meta ↑      STC_core ≈      PQ ↑      Mutation ≈
```

只追 meta coverage 不算成功。

### 2.2 四象限判定

| PQ | STC_meta | Mutation | 判读 |
|---|---|---|---|
| ↑ | ↑ | ≈ | **理想**：映射恢复结构传输 |
| ↑ | ↓ | ≈ | Writer 压缩模型 |
| ↓ | ↑ | ≈ | 表达问题，非结构问题 |
| ↑ | ↑ | ↑ | **危险**：Writer 借机改模型 |

---

## 3. 执行顺序（已锁定，不得跳步）

```text
R3-G0  Freeze Writer protocol v2 + 本预注册 + 归档旧语料       ✅
R3-G1  Generate 24 real W0 papers  ┐ 每个 (Q,arm) 单元
R3-G1  Generate 24 real W1 papers  ┘ W0→W1 背靠背
R3-G2  Freeze + SHA256 + 完整性门禁（48/48、章节齐全、长度达标）
R3-G3  STC v2（core / meta / overall，逐元素）
R3-G4  Mutation / Fidelity Gate v2
R3-G5  Blind Paper Quality（随机化编号、评审盲态）
R3-G6  Paired W0/W1 analysis → H13–H18
R3-G7  Report
```

**禁止**：在 G2 完成前查看任何 W1 的 STC/PQ 结果以调整 prompt 或映射。

---

## 4. 冻结资产

| 资产 | 位置 | 数量 | 校验 |
|---|---|---|---|
| Model Artifacts | `projects/P13-3D-R2/output/artifacts/*.json` | 24 | `freeze_manifest.json` SHA256 |
| Model→Paper Maps | `projects/P13-3D-R3/output/maps/*_map.json` | 24 | `freeze_manifest.json` SHA256（24/24 gate passed） |
| Writer Prompts | `projects/P13-3D-R3/prompts/{W0,W1}/*.json` | 48 | `prompts/manifest.json` |
| STC v2 | `core/tools/evaluation/stc_evaluator.py` | — | Golden Set F1=1.000 |
| Fidelity Gate | `core/tools/evaluation/fidelity_gate.py` | — | R2 已用 |

---

## 5. 风险

| 风险 | 处置 |
|---|---|
| 生成长度不足/截断 | G2 门禁：字数下限 + 10 章节齐全，不合格重生成（每单元最多 2 次） |
| 子批次 Writer 漂移 | 记录 batch_id；若 H13 显著则额外报告"仅 batch 内配对"的敏感性分析 |
| W1 引入未授权元素 | H16 + Fidelity Gate addition 检测 |
| H15 仍不成立 | 结论为"瓶颈不在结构映射，而在 scientific argument construction / rhetorical synthesis"，同样有价值 |

---

## 附录 A — 修订记录（分析启动前，未发生任何偷看结果）

### A1. 生成规格缺陷 → 首轮 24 篇作废重生成（2026-09-07 13:35）

`GENERATION_SPEC.md` v1 的规则 6 要求 Writer 在 `sensitivity_plan` 为空时明写
"本构件未给出灵敏度计划（sensitivity_plan 为空）"，且 W1 被引导写"依据结构化映射…"。
执行后发现 **48 篇候选中的全部 24 篇已生成论文都含实验用语**，
属于元叙述泄漏：盲评人可据此反推条件，**H14/H15 的盲态被破坏**。

处置：
1. 修订 `GENERATION_SPEC.md` 第 6、7 条，明确列举禁止词表；
2. 同步进 `r3g_corpus_check.py::LEAK_PATTERNS` 作为门禁项；
3. 首轮 24 篇**作废并覆盖重生成**（不是挑选性重生成——全部 24 篇同判据作废，无选择性偏差）；
4. 门禁通过前不运行任何 STC / PQ 评估，故本次修订**未接触任何结果数据**，不构成 p-hacking。

### A2. 单元批次与"背靠背"定义的操作化

- 一个 (question, arm) 单元的 W0 与 W1 由**同一个子 agent 在同一次会话内连续生成**，中间不插入其他单元。
- 每篇记录 `mtime` 与 `batch_id`（格式：`G2-<日期>-<子agent序号>`）。
- 若 H13 显著，额外报告"仅同批次内单元"的敏感性分析，以排除批次效应。

### A3. 已知限制

- "同一 Writer 模型"在本环境下的含义是：**同一平台的同一默认模型**，由同质子 agent 执行，
  非 API 级的固定 model version + seed。seed 无法锁定，故本设计靠
  **24 单元配对 + 大样本** 而非 seed 复现来控制随机性。
- 论文长度受生成能力约束，规格限定 6000–11000 字符；长度本身不是假设变量，
  但会在分析中作为协变量检查（若 W1 显著更长，需在讨论中说明）。
