# P15 预注册（v1 freeze）：Competition Modeling Capability Program

- Status: **FROZEN v1 (2026-09-08)** · 轨道：`research/P15/`（全程不进 core/）
- 上游：v3.1.0 已发布；P13-3C closed（Model Construction 能力差异可迁移）
- 定位：P15 不是"让 Agent 多刷题"，而是把 CUMCM 真题变成**能力训练 + 可控评测基准**

## 1. 研究问题

> Harness 的 Model Construction 能力差异（P13-3C 中 B1=86.2 > MMA=69.5 > B0=37.1）能否跨模型家族泛化到 CUMCM 全题库？

## 2. 本轮范围（P15.0–P15.2）

| Phase | 内容 | Exit Criteria |
|---|---|---|
| P15.0 | Benchmark & Capability Ontology Freeze | 4 gates 全绿 |
| P15.1 | Alignment baseline（5题） | B0 baseline 建立 |
| P15.2 | Model Construction（15题） | 跨家族泛化验证 |

## 3. 能力维度（5维枚举）

| 维度 | 定义 | 评测方式 |
|---|---|---|
| alignment | 子问题覆盖率 vs 金标准 | decomposition_coverage |
| construction | 结构正确性 + 数学正确性 | mc rubric 三维评分 |
| consistency | 变量-约束-目标自洽 | consistency_gate（确定性） |
| solving | 求解可靠性 | solving_reliability（多 seed） |
| validation | 验证充分性 | validation_thoroughness |

枚举值：`low` / `medium` / `high`（机器可读，不使用自由文本评分）。

## 4. 失败模式分类（6 类 22 种）

| 类别 | 代号 | 种数 |
|---|---|---|
| Problem Alignment | FM-PA | 3 (01-03) |
| Model Construction | FM-MC | 5 (01-05) |
| Formal Consistency | FM-FC | 4 (01-04) |
| Solving | FM-SV | 3 (01-03) |
| Validation | FM-VA | 4 (01-04) |
| Claim Support | FM-CS | 3 (01-03) |

两个 taxonomy（capability_dimensions vs failure_modes）**独立定义，不混用**。

## 5. 金标准字段（每题 7 字段）

```text
sub_questions[]              Alignment 金标准
required_deliverables[]      交付物完整性
core_methods[]               方法参考（非唯一答案）
key_variables[]              变量识别
key_constraints[]            约束建模
evaluation_targets[]         验证目标
capability_dimensions{}      难度枚举（5维 × low/medium/high）
failure_modes[]              已知失败模式（FM-XX-NN 格式）
```

## 6. 执行协议

### Determinism Gate（可重放性）
```text
fixed seed 42
same input / same provider / same code
→ replay identical (hash chain verification)
```

### Stochastic Robustness（性能方差）
```text
pre-registered seeds: [42, 43, 44, 45, 46]
record: provider / model / version / temperature
→ mean ± std per capability dimension
```

### Sensitivity Plan（per-problem）
```text
default: ±20%, 10 steps, relative
override: must preregister + justification
测的是"有没有进行有效敏感性分析"，不是"有没有跑 10×20%"
```

## 7. 纪律

- **Baseline first**：P15.1 建立 B0 前不做任何 intervention
- research/ 轨道：发现 core 缺陷 → failure → experiment → intervention
- 随机种子 42；≥5 次运行报告 mean±std
- Negative results 同样是合格产出
- 不改变 v3.1.x 核心架构边界
- Benchmark 可以引用 core，**不要反过来把实验标签灌进 core**

## 8. 论文质量（P15.6）

使用 **MST（Model Structure Transmission）+ Fidelity + Claim Support + Question Alignment** 作为质量 gate。篇幅/图数/公式数仅作为 sanity check，不作为质量 gate。

## 9. P15.0 冻结条件

```text
INPUT:   32 CUMCM problems
SCHEMA:  7 gold fields + capability_dimensions (enum) + failure_modes[] (enum)
GATES:   schema / completeness / family coverage / failure-mode coverage / duplicate / hash / baseline snapshot
PROHIBITION: no Agent output / no intervention / no scoring result / no capability conclusion / no core/ architecture change
```

## 10. 待冻结项

- [x] Benchmark schema (`p15_capability_tags.schema.json`)
- [x] CUMCM-Bench-v2.json (32 problems × 7 gold fields)
- [x] Catalog indexes (by_family / by_capability / by_failure_mode)
- [x] Validation scripts (4 gates)
- [x] Baseline snapshot (5 problems)
- [ ] P15.1 首批 5 题 B0 baseline（下 phase）
