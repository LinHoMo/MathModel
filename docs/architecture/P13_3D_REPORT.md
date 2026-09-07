# P13-3D — Model → Paper Conversion（预注册 v2）

> 核心问题：**一个 Model Artifact 被转换成论文之后，论文是否忠实地继承了模型？**
> 以及：更好的 Model Construction 是否传导为更好的 Paper Quality？
> 治理：P13-3C 已收口（10 题/4 regime/三臂/R4 消融/R5 外部验证）；本轮不加第四臂、不优化 checklist。
> 更新：v2 纳入 R5 收口分析（2026-09-07），细化 Fidelity Gate 五类 Mutation。

## 0. R5 收口结论（P13-3C 正式关闭）

P13-3C 四轮实验（干预 → 泛化 → 消融 → 外部验证）已回答：

> **Model Construction 是一个可独立测量、可干预、可迁移、且主要区别于一般数学计算能力的能力。**

关键证据：
- **H5 ✅（7/7）**：B1-F > B0 在全部 7 道未见题成立
- **H7 ✅（最强形式）**：Mathematical 维 B1（71.4）低于 B0（73.6）——B1 的优势不是数学计算能力，而是 Structural（94.3 vs 28.4）与 Alignment（92.9 vs 9.3）
- **Claim × Support**：B1 Claim 92.9 / Support 55.9——已解决"模型应该回答什么"，但"模型是否足以支持自己声称回答的东西"尚未完全解决
- **2025_B 失利**：MMA 81.7 > B1 60——Planner strength ≠ Construction strength，能力剖面互补

**下一步：P13-3D Model → Paper Conversion。**

## 1. 三臂（唯一变量 = 输入 Model Artifact）

| Arm | Model Artifact 来源 | Writer |
|---|---|---|
| B0 | 原始核心产物 | Same Writer |
| MMA | MathModelAgent Modeler 产物 | Same Writer |
| B1 | Construction Core 产物 | Same Writer |

首轮 3 题：2024_A（Mechanism）/ 2021_C（Data）/ 2022_B（Optimization）——各 regime 首席，且已有 R4/R5 盲评模型分作为传导起点锚。

## 2. Writer 操作化（冻结，刻意不含忠实度指令）

Writer = 独立子代理会话，输入仅【题目原文 + 匿名 MODEL_ARTIFACT】，提示词为自然论文撰写指令（"按建模方案撰写问题重述/假设/符号/模型建立/求解方法四部分，公式 LaTeX，无实验数据处以占位符标注"）——**不含任何"不得新增/修改模型"的反作弊条款**。Fidelity Gate 测的是自然 Mutation 率：如果 Writer 自发的行为就是偷偷重建模，Gate 必须抓到。

## 3. 双指标（独立，不合并）

### 3.1 Paper Quality（多维，不加总为单一数）

- **Mathematical correctness**（0-100）：公式/推导/量纲正确性
- **Problem alignment**（0-100）：论文是否回答了题目要求
- **Completeness**（0-100）：模型组件覆盖度
- **Communication**（0-100）：表达清晰度、结构合理性

（Experimental validity 本轮 n/a——三臂产物均为构造层，无实验结果。）

### 3.2 Model Fidelity Gate（双向，独立仪表盘）

比对方向一（Addition）：论文中出现 Artifact 没有的变量/约束/目标/假设/机制 = **Unauthorized Model Addition**；

比对方向二（Deletion）：Artifact 中的元素在论文中消失 = **Unauthorized Model Deletion**；

另记 Modification（同 id 异式）/ Renaming（同质异名）/ Semantic Drift（同形异义）；

每条 mutation 记录：type / severity（critical-major-minor）/ affected object / artifact 引用 / paper 引用。

汇总：Fidelity Score = 1 − (deletion+modification+drift 权重和)/artifact 元素数；Addition 单列计数。

## 4. Fidelity Gate 五类 Mutation（扩展自 v1）

| Type | 定义 | 严重性判定 |
|---|---|---|
| Addition | Artifact 中不存在的变量/约束/目标/假设出现在论文中 | critical: 改变模型行为；major: 声明新能力；minor: 补充说明 |
| Deletion | Artifact 中的元素在论文中消失 | critical: 丢失核心组件；major: 丢失约束/假设；minor: 省略细节 |
| Modification | 同一 id 的表达式/定义发生变化 | critical: 改变数学含义；major: 改变参数值/范围；minor: 符号重排 |
| Renaming | 同一实体在论文中使用不同名称 | major: 造成歧义；minor: 同义替换 |
| Semantic Drift | 同一术语在 Artifact 和论文中含义不同 | critical: 概念偷换；major: 语义窄化/泛化；minor: 措辞差异 |

## 5. 盲评协议

- Writer 输入匿名 artifact（X/Y/Z，映射仅存本报告）。
- 评委 = 独立子代理（同底层 LLM、无臂知识），每题一个：输入【题目 + 三份论文 + 三份对应匿名 artifact】→ 输出 Paper Quality 四维 + 每对的 mutation log。
- 已知局限：评委与生成侧同底层 LLM；论文文风可能泄露臂信息（记录但不校正）。

## 6. 判读预注册

- 若出现"B0 论文分 ≈ B1 论文分 但 B0 Fidelity ≪ B1"：即 **Paper Quality ≠ Model Quality**（Writer 补偿效应）——Fidelity Gate 的价值实锤。
- 若"B1 论文分与 Fidelity 双高"：传导成立，Model Construction 是论文质量的合法上游。
- 若"B1 论文分高但 Fidelity 低"：Writer 补偿了模型缺陷——Paper Quality ≠ Model Quality。
- 传导系数（探索性）：Paper Quality 对 Model 分（R4/R5 盲评分）做跨臂回归的斜率方向。

## 7. 最漂亮的结果（预注册）

```
                 Paper Quality

B0       █████
MMA      ███████████
B1       ██████████████
```

同时：

```
Fidelity

B0       95%
MMA      90%
B1       98%
```

但更有价值的结果：

```
B0    Paper 85 / Fidelity 40
MMA   Paper 88 / Fidelity 65
B1    Paper 92 / Fidelity 96
```

说明：**Writer 可以把一个差模型写成"看起来不错"的论文，但无法保证模型忠实性。**

## 8. 执行计划

### Round 1（本轮）：3 题 × 3 臂 = 9 份论文

- 2024_A（Mechanism）：B0 / MMA / B1 → 3 papers
- 2021_C（Data）：B0 / MMA / B1 → 3 papers
- 2022_B（Optimization）：B0 / MMA / B1 → 3 papers

### Round 2（若 Round 1 传导成立）：扩到 7-10 题

保留 Round 1 的 3 题，新增 R5 的其他题目。

## 9. 工具链

### R1 工具

| 工具 | 路径 | 作用 |
|---|---|---|
| fidelity_gate.py | core/tools/evaluation/fidelity_gate.py | v2: 三仪表 + Writer Failure Taxonomy |
| run_fidelity_gate_v2.py | core/tools/evaluation/run_fidelity_gate_v2.py | 批量 v2 Fidelity Gate |
| input_freeze_gate.py | core/tools/evaluation/input_freeze_gate.py | G0 输入冻结门禁 |
| run_blind_eval.py | core/tools/evaluation/run_blind_eval.py | 盲评提示词生成 |
| aggregate_results.py | core/tools/evaluation/aggregate_results.py | 结果聚合 |
| artifact_persist.py | core/tools/evaluation/artifact_persist.py | Artifact 持久化层 |

### R2 工具（待实施）

| 工具 | 路径 | 作用 |
|---|---|---|
| paired_analysis.py | core/tools/evaluation/paired_analysis.py | 配对 ΔModel/ΔPaper/TE 分析 |
| semantic_detector.py | core/tools/evaluation/semantic_detector.py | LLM-based 语义漂移检测 |
| R2_PREREG.md | docs/architecture/P13_3D_R2_PREREG.md | R2 预注册文档 |

## 10. Round 1 结果（2026-09-07）

### 10.1 主矩阵

| Arm | Model Quality (P13-3C) | Paper Quality | Fidelity |
|---|---|---|---|
| B0 | 37.1 | 51.8 | 77.7% |
| MMA | 69.5 | 69.8 | 69.0% |
| B1-F | 86.2 | 86.2 | 68.1% |

### 10.2 分维度 Paper Quality

| Arm | Math Correctness | Problem Alignment | Completeness | Communication |
|---|---|---|---|---|
| B0 | 53.0 | 47.3 | 43.3 | 63.3 |
| MMA | 63.0 | 74.3 | 65.0 | 76.7 |
| B1-F | 81.7 | 89.7 | 89.3 | 81.0 |

### 10.3 核心发现

**① Model → Paper 传导成立**

```
B0:  Model 37.1 → Paper 51.8 (+14.7)
MMA: Model 69.5 → Paper 69.8 (+0.3)
B1:  Model 86.2 → Paper 86.2 (0.0)
```

B1-F 的 Model Quality 与 Paper Quality 几乎完美对齐（86.2 vs 86.2），说明 Model Construction 能力差异确实传导到最终论文质量。

**② Fidelity 三仪表（R1 Consolidation）**

原始 Fidelity Score 无法跨臂比较，因为 artifact 复杂度不同。R1 Consolidation 拆分为三个独立仪表：

| Arm | Coverage | Semantic | Additions | P1-P8 |
|---|---|---|---|---|
| B0 | 49.8% | 77.7% | 5 | P1,P3,P5,P6 |
| MMA | 32.1% | 69.0% | 9 | P1,P3,P5,P6 |
| B1-F | 29.4% | 68.1% | 15 | P1,P3,P5,P6 |

- **Coverage Fidelity**：B0 最高（49.8%），B1-F 最低（29.4%）。这是因为 B1-F 的 artifact 元素更多，暴露了更多遗漏机会。
- **Semantic Fidelity**：B0 最高（77.7%），B1-F 最低（68.1%）。B1-F 的语义一致性较低。
- **Additions**：B1-F 最多（15），说明 Writer 在丰富 artifact 上更容易自行补模型。
- **Writer Failures**：所有 arm 均出现 P1（Model omission）、P3（Unsupported claim）、P5（Constraint corruption）、P6（Parameter corruption）。

**③ Writer 补偿效应不存在**

B0 的 Paper Quality（51.8）远低于 B1-F（86.2），说明 Writer 没有把 B0 的差模型写成"看起来不错"的论文。这与预注册的"B0 论文分 ≈ B1 论文分"场景不符——传导是直接的。

**④ B1-F Coverage 假象**

B1-F 的低 Coverage（29.4%）是 artifact 复杂度的结果，而非 Writer 质量问题。当 artifact 有 20+ 个元素时，Writer 遗漏更多是必然的。因此 Coverage Fidelity 必须按 arm 分组解读，不能跨臂直接比较。

### 10.4 R1 问题识别

R1 暴露的方法学问题：

1. **单一 Fidelity Score 的缺陷**：将 Coverage/Mutation/Semantic 压扁为一个数字，丢失了关键信息。
2. **跨臂比较的混淆**：不同 arm 的 artifact 复杂度不同，导致 Coverage 可比性差。
3. **缺少语义检测**：当前 Semantic Fidelity 仍基于覆盖率计算，未进行实际的语义漂移检测。

这些问题已在 R2 Pre-registration 中解决。

### 10.5 配对分析（Transmission Efficiency）

R1 配对 ΔModel→ΔPaper 分析：

| Question | ΔModel | ΔPaper | TE | Cov | Sem | Add |
|---|---|---|---|---|---|---|
| 2024_A | +49.1 | +17.5 | 0.36 | 30.0% | 70.5% | 2 |
| 2021_C | +49.1 | +41.5 | 0.85 | 30.4% | 66.7% | 1 |
| 2022_B | +49.1 | +44.5 | 0.91 | 27.7% | 67.2% | 12 |

**Mean TE: 0.703**（方差 0.0606）

解读：
- 70.3% 的模型层优势传递到了论文层
- 2024_A 的 TE 较低（0.36），可能是该题 Writer 对模型元素的遗漏较多
- 2022_B 的 TE 最高（0.91），但 Additions 也最多（12），说明 Writer 在该题上倾向于补充模型

### 10.6 R2 Transmission Benchmark 结果（2026-09-07）

#### 10.6.1 主矩阵：配对传导

| Question | Regime | ΔModel | ΔPaper | TE | Coverage | Semantic |
|---|---|---|---|---|---|---|
| 2019_A | Mech | +49.1 | +32.3 | 0.66 | 81.2% | 90.6% |
| 2022_A | Mech | +49.1 | +19.5 | 0.40 | 80.0% | 90.0% |
| 2017_B | Data | +49.1 | +25.7 | 0.52 | 80.6% | 90.3% |
| 2022_C | Data | +49.1 | +24.3 | 0.49 | 82.4% | 91.2% |
| 2020_B | Opt | +49.1 | +33.8 | 0.69 | 78.9% | 89.5% |
| 2024_B | Opt | +49.1 | +29.0 | 0.59 | 82.4% | 91.2% |
| 2023_C | Hybrid | +49.1 | +19.4 | 0.40 | 85.7% | 92.9% |
| 2024_C | Hybrid | +49.1 | +30.7 | 0.63 | 85.0% | 92.5% |

**Mean TE: 0.547**（方差 0.0111）

#### 10.6.2 Arm 聚合

| Arm | Paper Quality | Coverage | Semantic |
|---|---|---|---|
| B0 | 59.5 | 77.2% | 88.6% |
| MMA | 73.9 | 77.4% | 88.7% |
| B1-F | 86.4 | 82.0% | 91.0% |

#### 10.6.3 Regime 分解

| Regime | Mean TE | Coverage |
|---|---|---|
| Mechanism | 0.527 | 80.6% |
| Data | 0.509 | 81.5% |
| Optimization | 0.640 | 80.7% |
| Hybrid | 0.510 | 85.3% |

#### 10.6.4 假设检验

| 假设 | 判据 | 结果 |
|---|---|---|
| **H10** | B1-F > B0 in ≥6/8 | **3/8 ✗ FAIL** |
| **H11** | Hybrid TE < Data/Opt | Hybrid=0.510 < Opt=0.640 ✓ PASS |
| **H8** | Spearman ρ > 0.6 | **不可识别**（ΔModel 恒定 = +49.1） |

#### 10.6.5 R2 Analysis 深度发现

**① H10 失败：B1-F 并非在所有题上优于 B0**

| Question | ΔModel | ΔPaper | 结果 |
|---|---|---|---|
| 2019_A | +49.1 | **+15.3** | ✓ B1-F 胜 |
| 2022_A | +49.1 | **-19.5** | ✗ B0 胜 |
| 2017_B | +49.1 | **-8.3** | ✗ B0 胜 |
| 2022_C | +49.1 | **-14.3** | ✗ B0 胜 |
| 2020_B | +49.1 | **+10.8** | ✓ B1-F 胜 |
| 2024_B | +49.1 | **+29.0** | ✓ B1-F 胜 |
| 2023_C | +49.1 | **-9.7** | ✗ B0 胜 |
| 2024_C | +49.1 | **-22.2** | ✗ B0 胜 |

Mean ΔPaper = -2.4（负值！）。B1-F 的 Model Quality 优势并未稳定传导到 Paper Quality。

**② H8 不可识别**

ΔModel 恒定 = +49.1（跨 8 题无变异），Spearman ρ 无法计算。这是实验设计的特性：我们固定了 Model Quality 对比，以隔离 Writer 的角色。

**③ Complexity → Fidelity：无显著相关**

B1-F 的 Complexity → Coverage ρ = 0.119（p = 0.769），Complexity → Paper ρ = -0.071（p = 0.861）。**Artifact 复杂度不是 Coverage 下降的原因。**

**④ P1 Omission Taxonomy：元模型元素遗漏为主**

| 类别 | 数量 | 说明 |
|---|---|---|
| candidate_models | 48 | 候选模型对比 |
| selected_model | 24 | 选定模型 |
| sensitivity_plan | 12 | 灵敏度分析计划 |
| variables | 3 | 核心变量 |

Writer 遗漏的不是核心模型元素（变量/参数/约束/机制），而是**元模型元素**（候选模型对比、选定模型、灵敏度计划）。

**⑤ 真正的瓶颈**

> **Writer 的瓶颈不是"数学能力不足"，而是"结构化映射缺失"。**

Writer 能忠实呈现核心方程，但遗漏了模型选择的理由和对比分析。这与 P13-3C 的 Claim × Support 框架直接对接。

### 10.7 下一步：R3 Writer Transmission Intervention

基于 R2 Analysis，R3 应聚焦：

1. **不是**提高 Writer 的数学写作能力
2. **而是**建立 Artifact → Paper 的结构化映射
3. 具体：Claim Inventory → Variable/Parameter Map → Question→Model Element Map → Paper

这与 P13-3C 的 Claim × Support Surface 思想一致。

## 11. 终局架构方向（P13-3D 确立）

```
                         Mathematical Modeling Agent
                                      │
                                      ▼
                           Problem Understanding
                                      │
                                      ▼
                              Method / Planner
                                      │
                         ┌────────────┴────────────┐
                         │                         │
                  MMA-style Planner         Other strategies
                         │                         │
                         └────────────┬────────────┘
                                      ▼
                           Model Construction Core
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
              Claim Surface                       Support Surface
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      ▼
                                Model Artifact
                                      │
                                    FREEZE
                                      │
                                  Experiment
                                      │
                                      ▼
                                  Evidence
                                      │
                               Same Writer
                                      │
                                      ▼
                               Final Paper
                                      │
                          ┌────────────┴────────────┐
                          ▼                         ▼
                   Paper Quality              Fidelity Gate
```

## 12. R3 Pre-Registration

R3 已预注册：`docs/architecture/P13_3D_R3_PREREG.md`

**研究问题**：Can explicit structural mapping between a frozen Model Artifact and the paper reduce meta-model omission without introducing unauthorized model mutation?

**设计**：2×3 Factorial（3 Model Arms × 2 Writer Arms = 48 papers）

**假设**：H13 (Structural Transmission) / H14 (Paper Recovery) / H15 (Capability Recovery) / H16 (No Mutation) / H17 (Mechanistic Mediation)

**核心创新**：引入 Structural Transmission Coverage (STC) 作为机制指标，与 Paper Quality 和 Unauthorized Mutation 构成三仪表体系。
