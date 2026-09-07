# P13-3D Round 2 Pre-Registration

**Date**: 2026-09-07
**Status**: Draft

---

## 1. H8: Transmission Generalization

> **在未见题、不同题型、不同模型复杂度下，Model Quality 的差异是否稳定传导至 Paper Quality？**

### 1.1 实验设计

**样本**：7–10 道新题，覆盖多种题型

| 题型 | 题目来源 |
|---|---|
| Optimization | 2020_B, 2023_A, 2024_B |
| Mechanism | 2023_C, 2021_A |
| Data | 2022_A, 2024_D |
| Prediction | 2023_D |
| Synthesis | 2024_C |

**Arm**：B0 / MMA / B1-F（同 R1）
**Writer**：同 R1（同一盲评 Writer）
**评估**：同 R1（4 维独立评分 + 三仪表 Fidelity + Writer Failure Taxonomy）

### 1.2 主分析：配对 ΔModel → ΔPaper

每道题计算：

```
ΔModel(Q) = ModelQuality(Q, B1-F) - ModelQuality(Q, B0)
ΔPaper(Q) = PaperQuality(Q, B1-F) - PaperQuality(Q, B0)
```

**主表**：

| Question | ΔModel | ΔPaper | TE | Coverage | Additions | P1-P8 |
|---|---|---|---|---|---|---|
| Q1 | +40 | +32 | 0.80 | 29% | 2 | P1,P5,P6 |
| Q2 | +30 | +28 | 0.93 | 35% | 1 | P1,P5 |
| ... | ... | ... | ... | ... | ... | ... |

**Transmission Efficiency (TE)**：

$$
TE = \frac{\Delta Paper}{\Delta Model}
$$

解释：
- TE ≈ 1.0：传导高效（模型优势几乎完全传递到论文）
- TE ≈ 0.5–0.8：传导有效但有损耗
- TE < 0.5：Writer 是 bottleneck
- TE > 1.2：Writer 可能在自行补模型

### 1.3 泛化检验

**传导一致性**：TE 在 7–10 题中的方差。方差 < 0.1 表示稳定传导。

**题型异质性**：按题型分组计算 TE 均值，检验是否有题型差异。

### 1.4 判据

**H8 成立**：ΔPaper 与 ΔModel 的 Spearman ρ > 0.6，且 TE 在所有题型中均 > 0.4

---

## 2. H9: Writer Fidelity

> **同一 Writer 能否在不发生未经授权模型变异的情况下，将 Model Artifact 转换为 Paper？**

**R2 锁定**：不修 Writer prompt。全部跑完再做 P13-3D-R3 Writer intervention。

### 2.1 三仪表体系

| 仪表 | 定义 | 指标 |
|---|---|---|
| **Coverage Fidelity** | Artifact 元素在论文中的覆盖率 | 0–1 |
| **Unauthorized Mutation** | 论文新增/修改/删除模型元素 | 数量 |
| **Semantic Fidelity** | 论文与 artifact 的语义一致性 | 0–1 |

### 2.2 Writer Failure Taxonomy

| Code | 失败类型 | 说明 |
|---|---|---|
| P1 | Model omission | 论文遗漏模型组件 |
| P2 | Model mutation | 论文修改模型组件 |
| P3 | Unsupported claim | 论文声称无支持的结论 |
| P4 | Equation corruption | 方程错误 |
| P5 | Constraint corruption | 约束错误 |
| P6 | Parameter corruption | 参数错误 |
| P7 | Interpretation drift | 解释漂移 |
| P8 | Experiment/model mismatch | 实验与模型不匹配 |

### 2.3 判据

**H9 成立**（需同时满足）：
- Coverage Fidelity > 0.8（所有题、所有 arm）
- Semantic Fidelity > 0.85
- P1-P8 每类 ≤ 2 次（8 题累计）

**H9 不成立**：任一条件不满足

---

## 3. H10: Transmission Generalization

> **B1-F 相对 B0 的 Model Quality 优势，在大多数新题上仍形成正的 Paper Quality 优势。**

### 3.1 判据

**H10 成立**：≥6/8 题的 ΔPaper(B1-F, B0) > 0

### 3.2 补充

若 H10 不成立（<6/8），需逐案审查失败题，判断：
- 是 Artifact 质量问题（B1-F 在该题 Construction 失败）
- 还是 Writer 传导问题（Artifact 好但 Paper 差）

---

## 4. H11: Regime-dependent Transmission

> **TE 在不同 construction regime 间存在稳定差异，尤其 Hybrid/Mechanism 可能低于 Data/Optimization。**

### 4.1 判据

**H11 成立**：
- 按 regime 分组计算 TE 均值
- Hybrid TE < Data TE 或 Hybrid TE < Optimization TE

### 4.2 预期

| Regime | 预期 TE | 理由 |
|---|---|---|
| Data | 0.7–0.9 | 统计方法标准化，Writer 不易遗漏 |
| Optimization | 0.7–0.9 | 约束/目标明确，Writer 易忠实呈现 |
| Mechanism | 0.5–0.7 | 方程密度高，Writer 易遗漏或简化 |
| Hybrid | 0.4–0.7 | 多阶段链条长，Writer 最易产生 P1-P8 |

---

## 5. H12: Complexity–Fidelity Relationship

> **Artifact complexity 上升与 Coverage/Semantic Fidelity 下降相关，但不应自动导致 Paper Quality 下降；如果 Paper Quality 同时显著下降，才说明 Writer 成为实质 bottleneck。**

### 5.1 判据

**H12 成立**：
- Artifact 元素数与 Coverage Fidelity 的 Spearman ρ < -0.5（复杂度↑ → Coverage↓）
- 但 Artifact 元素数与 Paper Quality 的 Spearman ρ > -0.3（复杂度↑ 不自动导致 Paper↓）

**H12 不成立（Writer bottleneck）**：
- Artifact 元素数与 Paper Quality 的 Spearman ρ < -0.5（复杂度↑ → Paper↓）
- 且 Coverage Fidelity < 0.7（Writer 遗漏严重）

---

## 6. R2 执行清单

### Phase 1: 题目选择 ✅
- [x] 从题库中选出 8 题（2 Mechanism + 2 Data + 2 Optimization + 2 Hybrid）
- [x] 生成 difficulty profile（含 artifact_complexity_expected / paper_conversion_complexity）
- [x] 锁定题目清单（P13_3D_R2_QUESTIONS.md）

### Phase 2: Artifact 构建（8 × 3 = 24 份）
- [ ] 对每题 × arm 构建 MODEL_ARTIFACT v1 JSON
- [ ] SHA256 哈希 + 冻结
- [ ] 运行 G0 Input Freeze Gate 验证

### Phase 3: Writer 生成（8 × 3 = 24 份）
- [ ] 生成 24 份 Writer inputs
- [ ] 盲评映射（X/Y/Z 随机，每题独立 seed）
- [ ] 生成 24 份 papers

### Phase 4: Fidelity Gate v2
- [ ] 运行 run_fidelity_gate_v2.py
- [ ] 输出 Coverage / Mutation / Semantic 三仪表
- [ ] Writer Failure Taxonomy (P1-P8)

### Phase 5: Blind Paper Quality
- [ ] 生成 21–30 份盲评提示词
- [ ] LLM 评分（4 维独立）
- [ ] 解盲

### Phase 6: 配对分析
- [ ] 计算每题 ΔModel / ΔPaper / TE
- [ ] Spearman ρ 检验
- [ ] TE 方差分析

### Phase 7: 报告
- [ ] 更新 P13_3D_REPORT.md
- [ ] 回答 H8 / H9 / H10 / H11 / H12

---

## 7. 预期产出（四张预注册表）

### 表 1: 每题配对传导

| Question | Regime | ΔModel | ΔPaper | TE |
|---|---|---|---|---|
| 2019_A | Mech | ... | ... | ... |
| 2022_A | Mech | ... | ... | ... |
| 2017_B | Data | ... | ... | ... |
| 2022_C | Data | ... | ... | ... |
| 2020_B | Opt | ... | ... | ... |
| 2024_B | Opt | ... | ... | ... |
| 2023_C | Hybrid | ... | ... | ... |
| 2024_C | Hybrid | ... | ... | ... |

### 表 2: Writer 忠实度

| Question | Arm | Coverage | Semantic | Additions | Major P1-P8 |
|---|---|---|---|---|---|
| ... | B0/MMA/B1-F | ... | ... | ... | ... |

### 表 3: 复杂度关系

| Question | Artifact Complexity | Coverage | Semantic | Mutations |
|---|---|---|---|---|
| ... | 19–34 | ... | ... | ... |

### 表 4: 各 arm Paper Quality 总结

| Arm | Mean Paper Quality | 95% CI | Regime Breakdown |
|---|---|---|---|
| B0 | ... | ... | ... |
| MMA | ... | ... | ... |
| B1-F | ... | ... | ... |

### 聚合分析

- **Spearman ρ (ΔModel, ΔPaper)**：传导一致性（H8）
- **Mean TE**：平均传导效率
- **TE Variance**：传导稳定性（H11 regime-dependent）
- **Fidelity by Arm**：Coverage / Semantic 按臂分组
- **Writer Failure Distribution**：P1-P8 频次分布
- **Complexity Correlation**：Artifact 元素数 vs Coverage/Semantic/Paper Quality（H12）

---

## 5. 风险与缓解

| 风险 | 缓解 |
|---|---|
| TE 方差过大 | 按题型分组检验，识别异质性来源 |
| B1-F Coverage 过低 | 可能是检测算法问题，需人工抽查 |
| Additions 过多 | Writer 自行补模型，需报告 P3 频次 |
| 传导逆转（ΔPaper < 0） | 高度可疑，需逐案审查 |
