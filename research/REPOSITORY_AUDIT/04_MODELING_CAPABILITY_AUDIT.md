# 04 — Mathematical Modeling Capability Audit（数学建模能力模型审计）

- 审计日期：2026-09-08
- 审计范围：MathModel 仓库全部能力度量、benchmark、实验证据（P13/P14/P15）
- 审计员：Repository Audit Agent
- 状态：**DRAFT v1**
- 上游文档：`research/P15/PRE_REGISTRATION.md`、`docs/architecture/P13_3C_REPORT.md`、`research/P13-3D-R3/real_evaluation/R3_2_FINAL_REPORT.md`、`research/P14/PILOT_REPORT.md`、`docs/architecture/CAPABILITY_ROADMAP_P13_P17.md`、`docs/BENCHMARK.md`、`docs/METRICS.md`

---

## ⚠️ 更正说明（2026-09-08 方向纠偏）

本文档记录的是审计时点（2026-09-08）的旧方向状态。方向纠偏后，以下术语与定位已更正：

- **`core_methods` → `allowed_model_families`**：benchmark 不再定义"核心方法"作为唯一答案，而是定义兼容的模型族（允许的模型族）。
- **方法卡定位**：从"答案库"改为"约束/先验/验证"（constraint/prior/validation）。方法卡不告诉 LLM "必须用 X"，而是"如果你考虑 X，需要满足这些条件"。
- **`method_selection` 指标**：从"方法选择/参考方法匹配"重定义为"方法兼容性评估"（method compatibility assessment），测量的是测量工具效度而非 Agent 能力。
- **知识库目标**：从"全方法覆盖"改为"核心建模知识覆盖（Tier 0-3 策略）"，不追求穷尽所有方法。

> 本文档的审计发现与结论为历史记录，不做重写；上述更正适用于方向纠偏后的系统定位。详见 `docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md`。


## 0. 审计摘要

本审计的核心结论可以用三句话概括：

1. **Model Construction 是整个 Harness 的能力瓶颈与质量上限决定因素。** P13-3C-R5（7 题三臂）证明 B1-F 的优势不在数学计算（Mathematical 71.4 甚至低于 B0 的 73.6），而在 Structural（94.3 vs 28.4）与 Alignment（92.9 vs 9.3）。P13-3D-R3 进一步证明：在数学内容冻结条件下，Writer 侧结构映射对论文质量无可测收益（H13/H14 FAIL，ΔPQ = −0.01），质量方差由构件质量（arm）主导。
2. **当前 P15 的 5 维能力模型 + 6 类 22 种 failure mode 不足以覆盖真实建模失败空间。** 缺少 wrong abstraction / wrong causal structure / wrong objective / wrong mechanism 等"模型选择层"失败；FM-PA 与 FM-MC 存在大量 overlap；FM-CS 三类全部为空（0 题标注），说明 Claim Support 失败模式尚未被有效观察。
3. **Method correctness ≠ Model correctness 必须成为独立评测原则。** P15.1-2024A-B0 是教科书级案例：TOPSIS 本身可以数学完全正确，但用于运动学问题 = 完全错配（method_selection = 0%）。当前 evaluator 无法区分"数学有效但对齐失败"与"数学错误"，必须分离。

---

## 1. 能力模型重建（C0–C15）

### 1.1 设计原则

当前 P15 使用 5 维枚举（alignment / construction / consistency / solving / validation），P13-3 使用 3 维拆分（structural / mathematical / alignment），e2e_metrics 使用 8 项指标。三套体系并存且口径不统一。本审计建立 **C0–C15 十六级能力模型**，每一级对应建模认知管线的一个可独立审计的阶段，遵循以下原则：

- **线性依赖**：C_n 的输出是 C_{n+1} 的输入，前级失败会污染后级测量。
- **独立可测**：每一级必须有独立的 evaluator 或至少独立的诊断指标，不能混成一个 composite 分数。
- **失败可归因**：每一级的失败必须能映射到 F0–F11 归因体系（见 §5）。

### 1.2 C0–C15 能力定义与测量现状

| ID | 能力 | 定义 | 已有 evaluator？ | 已有 benchmark？ | 已有 evidence？ | 测量状态 |
|---|---|---|---|---|---|---|
| **C0** | Problem Understanding | 正确解析题目文本、数据附件、隐含约束与交付要求 | `problem-parser` agent（legacy）；无独立量化 evaluator | CUMCM-Bench-v2 有 `required_deliverables` 字段 | P15.1 2024_A：Q001 空壳，payload=[]——解析失败未被量化 | **只有 qualitative judgment** |
| **C1** | Problem Alignment | 子问题分解覆盖率 + 题目要求→模型元素的强制映射 | `e2e_metrics.py: decomposition_coverage`；`model_construction.py: alignment` 维度 | CUMCM-Bench-v2 `sub_questions[]` 金标准（36 题） | P13-3C-R5：B0 alignment 9.3 vs B1 92.9；P15.1：UNRESOLVED（produced 无子问题） | **有 evaluator + benchmark + evidence** |
| **C2** | Subproblem Decomposition | 将复合题拆为独立可解子问题，识别子问题间依赖 | 无独立 evaluator；`problem_analysis` 节点不做分解（P15.1 Evaluator Gap #1） | CUMCM-Bench-v2 `sub_questions[]` 可作为 GT | P15.1 2024_A：5 子问题被压成 1 个空壳 Q001，count-ratio=20% | **完全没有 measurement**（evaluator gap 已记录） |
| **C3** | Variable / Parameter Identification | 识别关键变量、参数、常量，区分可观测/不可观测/决策变量 | `model_construction.py: structural` 维度部分覆盖；无独立参数声明检查 | CUMCM-Bench-v2 `key_variables[]` | P13-3C 盲评实锤：B1 多题存在未声明参数（μ/ω/η/δ/φ/R0 等）；checklist §5 已固化 | **部分测量**（structural 维度包含，但未独立） |
| **C4** | Assumption Construction | 构建合理、显式、可检验的假设集，区分投影假设/校准锚/机制假设 | `assumption-validator` agent（legacy）；无量化 evaluator | 无独立 benchmark 字段 | P13-3B 2000C：A4 校准锚（λ=1.0636）被判定生物不合理→双分支括弧干预 | **只有 qualitative judgment** |
| **C5** | Model Construction | 从问题到数学模型的完整构造：变量→参数→假设→目标→约束→机制→方程 | `model_construction.py`（structural + mathematical + alignment 三维）；`model_construction_checklist.md`（7 类干预清单） | P13-3C rubric（mc_2024A.json 等）；CUMCM-Bench `key_constraints[]` | P13-3B：math 55→95（干预）；P13-3C：B1 93.9 > MMA 83.9 > B0 50.0；R5：B1 86.2 > MMA 69.5 > B0 37.1 | **有 evaluator + benchmark + 强 evidence**（核心能力） |
| **C6** | Mathematical Formalization | 方程推导正确性、量纲一致、符号/索引/边界正确 | `model_construction.py: mathematical` 维度（错误分类学扣分制） | rubric `math_error_taxonomy`（量纲/索引/符号/边界/校准/缺失约束/未陈述假设） | P13-3C-R4：B1-A 对齐干预导致 math 暴跌 65→45、85→20；P13-3B：math 55→95 | **有 evaluator + evidence** |
| **C7** | Model-family Selection | 选择正确的模型家族（运动学/优化/统计/评价/机理…） | `e2e_metrics.py: method_selection`（top-3 GT hit）；`method-matcher` agent | CUMCM-Bench-v2 `allowed_model_families[]` + `family[]`（19 个家族） | P15.1 2024_A：选 TOPSIS（评价族）而非运动学/几何族，method_selection=0%；P13-1/P13-2 retriever 消融 | **有 evaluator + benchmark + evidence** |
| **C8** | Cross-question Model Interface | 多子问题间模型接口、变量复用、参数传递、结果级联 | 无独立 evaluator | 无 | P13-3C 2022_B：月期量与年率需求无折算（跨子问题口径不一致）；MMA 臂 constraints 空置 | **完全没有 measurement** |
| **C9** | Solving Strategy | 选择合适的求解算法（解析/数值/优化/模拟），处理可解性 | `template-selector` + `code-implementer`（legacy）；无独立策略 evaluator | 无独立 benchmark | P13-3C 2022_B B1：年率 g 按月复利（index_error）——求解策略与模型口径不匹配 | **只有 qualitative judgment** |
| **C10** | Computational Reliability | 代码执行确定性、多 seed 稳定性、数值收敛、无崩溃 | `e2e_metrics.py: experiment_validity`（multi_run≥5 + robustness tags）；P14 21/21 replay match | env `code.random_seed=42`, `multi_run_count=5` | P14：21/21 Execution replay match；P15 PRE_REG：seeds [42,43,44,45,46] | **有 evaluator + evidence** |
| **C11** | Validation | 模型验证充分性：对照基线、灵敏度分析、残差分析、交叉验证 | `e2e_metrics.py: experiment_validity` + `validation_reliability`；P14 Evidence→Claim 链 | CUMCM-Bench `evaluation_targets[]` | P14：9 Claim 中 5 supported / 4 refuted；P15 FM-VA-01 覆盖 29/36 题（最广） | **有 evaluator + benchmark + evidence** |
| **C12** | Sensitivity / Robustness | 参数扰动下的结论稳定性、鲁棒性边界、不确定性传播 | `e2e_metrics.py` robustness tags；P13-3B 不确定性传播干预 | P15 PRE_REG：±20%, 10 steps, relative（默认） | P13-3B：λ 锚区间 [1.0545, 1.0727] 传播至全部下游；P14 CLM005 弹性 −0.464 | **部分测量**（有标签检查，无独立评分） |
| **C13** | Result Interpretation | 结果的物理/现实意义解释、量级合理性检查、反直觉结论的说明 | 无独立 evaluator | 无 | P13-3B 2000C：幼龄份额 61% 被判定生物不合理→触发校准修复；P14 CLM003 极端坏天气 C1 违反风险被 REFUTED | **只有 qualitative judgment** |
| **C14** | Claim Support | 每个结论/主张必须有可追溯的 Evidence 支持，区分 supported/refuted/unresolved | P14 `p14_integrity_gate.py`（G0–G7）；`e2e_metrics.py: validation_reliability`（claims_supported/total） | 无独立 benchmark（FM-CS-01/02/03 全部为空） | P14：5 supported / 4 refuted / 0 unresolved；P15 FM-CS 三类 0 题标注 | **有 evaluator（P14）+ evidence，但 benchmark 缺失** |
| **C15** | Model → Paper Transmission | 模型构件到论文的结构传输、内容忠实度、无未授权变异 | P13-3D STC v2 + Fidelity v2 + Blind PQ；`r32_eval.py` | P13-3D-R3 48 篇论文语料（8 题 × 3 arm × 2 condition） | R3：H13/H14/H15/H17 FAIL（映射无效果），H16 PASS（无害），ΔPQ=−0.01 | **有 evaluator + benchmark + evidence（negative but informative）** |

### 1.3 测量覆盖率统计

| 测量状态 | 能力数 | 占比 | 能力列表 |
|---|---|---|---|
| 有 evaluator + benchmark + evidence | 5 | 31% | C1, C5, C7, C10, C11 |
| 有 evaluator + evidence（无独立 benchmark） | 3 | 19% | C6, C14, C15 |
| 部分测量 | 2 | 13% | C3, C12 |
| 只有 qualitative judgment | 4 | 25% | C0, C4, C9, C13 |
| 完全没有 measurement | 2 | 13% | C2, C8 |

**关键发现**：16 项能力中只有 5 项（31%）具备完整的 evaluator + benchmark + evidence 闭环。C2（Subproblem Decomposition）和 C8（Cross-question Model Interface）完全没有测量——而 P15.1 已经证明 C2 失败是 2024_A B0 的首要根因（5 子问题被压成 1 个空壳）。

---

## 2. Model Construction 必须成为核心能力

### 2.1 为什么 Model Construction 是核心

P13 系列四轮实验（P13-3B 干预 → P13-3C 泛化 → P13-3C-R4 消融 → P13-3C-R5 扩展 → P13-3D 传输）构成了一条完整的证据链，共同指向同一个结论：

> **Model → Paper 的瓶颈不是写作，而是 Model Construction。**

具体证据：

**证据 1 — P13-3C 三题三臂（主矩阵）**：

| Arm | Mechanism (2024_A) | Data (2021_C) | Optimization (2022_B) | **mean** |
|---|---|---|---|---|
| B0 | 55.7 | 63.7 | 30.7 | **50.0** |
| MMA | 83.3 | 85.0 | 83.3 | **83.9** |
| B1 | 96.7 | 96.7 | 88.3 | **93.9** |

B1 mean 93.9 > MMA 83.9 > B0 50.0，三 regime 全胜。分维度看：

| 维度 | B0 | MMA | B1 |
|---|---|---|---|
| Structural | 51.7 | 86.7 | **100** |
| Mathematical | **76.7** | 73.3 | 81.7 |
| Alignment | 21.7 | 58.3 | **100** |

Mathematical 是最平的维度（三臂 73–82），真正的分界在 Structural 与 Alignment。

**证据 2 — P13-3C-R5 扩展基准（7 题）**：

| Arm | Structural | Mathematical | Alignment | Composite |
|---|---|---|---|---|
| B0 | 28.4 | **73.6** | 9.3 | 37.1 |
| MMA | 72.9 | 59.3 | 76.2 | 69.5 |
| B1-F | **94.3** | 71.4 | **92.9** | **86.2** |

H7 以最强形式成立：**B1 的 Mathematical（71.4）甚至低于 B0（73.6）**——B1 的优势不是数学计算能力，而是 Structural（94.3 vs 28.4）与 Alignment（92.9 vs 9.3）。

**证据 3 — P13-3D-R3（Model → Paper）**：

在真实 LLM Writer、数学内容冻结条件下，显式 `MODEL_PAPER_MAP` 未能提升结构传输（H13: ΔSTC = −0.035, FAIL）与论文质量（H14: ΔPQ = −0.01, FAIL）。但 arm 间 PQ 差异巨大（如 2024_B：B1-F ≈82.7 vs B0 ≈64.3，跨 arm 差约 18 分），而同单元 W0/W1 差均值仅 −0.01。

> **结论：质量方差由构件质量（arm）主导，不由 Writer 条件主导。Model→Paper 的质量上限由 Model Construction 决定。**

**证据 4 — P13-3B 数学正确性干预（55→95）**：

P13-3 首测 2000C 暴露 math=55，扣分明细指向三类失败：校准不合理（m=4.42 → 幼龄份额 61%）、约束缺失（密度制约/搬迁上限未入模）、不确定性不传播（λ 区间在下游消失）。施加 `model_construction_checklist.md` 三项干预后，自评 math 升至 95（后经盲评降级为诊断指标，但干预方向被 P13-3C 交叉验证）。

### 2.2 Model Construction 的层级分解

Model Construction 不是单一能力，而是一条 11 层认知管线。每一层都可以独立审计、独立失败、独立干预。

```
Problem (C0)
  → Mathematical abstraction (C1/C7)
    → Variables (C3)
      → Parameters (C3)
        → Assumptions (C4)
          → Objective (C5)
            → Constraints (C5)
              → Mechanism (C5/C6)
                → Equations (C6)
                  → Solvability (C9)
                    → Validation (C11)
```

#### 层级 1：Problem → Mathematical abstraction

- **定义**：将自然语言问题转化为数学问题类型（优化/机理/统计/评价/几何…），确定建模范式。
- **当前测量**：C7 Model-family Selection 有 `method_selection` evaluator（top-3 GT hit），但"抽象是否正确"与"方法是否选对"被混为一谈。
- **当前 skill 支持**：`type-classifier` agent（legacy）、`problem_profile` DTO（P13-1）、方法卡 retriever（P13-2）。
- **失败归因**：F3 Alignment failure 或 F4 Modeling failure。P15.1 2024_A 是典型案例：type-classifier 将运动学/几何题误分类为评价类，导致整个 pipeline 方向错误。
- **Adversarial test 设计**：构造"表面像评价题、实质是机理题"的混淆题（如含"评价"关键词但需要动力学建模），观察 type-classifier 是否被关键词误导。

#### 层级 2：Variables

- **定义**：识别状态变量、决策变量、观测变量、常量，区分内生/外生。
- **当前测量**：C3 部分包含在 `model_construction.py: structural` 维度中，但无独立的"变量识别正确率"指标。
- **当前 skill 支持**：CUMCM-Bench `key_variables[]` 金标准；checklist §5"声明完备性"。
- **失败归因**：F4 Modeling failure（变量遗漏）或 F5 Formalization failure（变量域不一致）。
- **Adversarial test 设计**：在题目中隐藏关键变量（如"忽略空气阻力"暗示需要速度变量），观察是否被识别。

#### 层级 3：Parameters

- **定义**：识别模型参数、区分可观测/不可观测/校准参数，声明每个参数的来源与取值。
- **当前测量**：无独立测量。P13-3C 盲评多次抓到"未声明参数"（μ/ω/η/δ/φ/R0、ρ/v/w、V0/p̄/shift/Foot_max），但这是作为 math deduction 出现的，不是独立指标。
- **当前 skill 支持**：checklist §5"机制方程中引用的每一个参数必须全部列入 parameters 声明"。
- **失败归因**：F5 Formalization failure（未声明参数 = 形式化不完备）。
- **Adversarial test 设计**：构造方程中引用了未声明参数的模型，检查 evaluator 能否自动检测（当前只能靠盲评人工发现）。

#### 层级 4：Assumptions

- **定义**：构建显式、合理、可检验的假设集，区分投影假设/校准锚/机制假设/简化假设。
- **当前测量**：C4 只有 `assumption-validator` agent（legacy），无量化 evaluator。
- **当前 skill 支持**：P13-3B 2000C 的 A1–A6 假设体系是范例；checklist §1"校准合理性"。
- **失败归因**：F4 Modeling failure（假设不合理）或 F2 Problem understanding failure（假设与题面矛盾）。
- **Adversarial test 设计**：构造"假设与题面数据矛盾"的模型（如题面说种群增长 6%，假设说 λ=1.003），观察是否被捕获。P13-3B 2000C 的 A4 校准锚就是这种失败的真实案例。

#### 层级 5：Objective

- **定义**：明确优化目标/估计量/预测目标，确保目标与题目要求一致。
- **当前测量**：无独立测量。包含在 alignment 维度中，但"目标函数是否正确"与"是否回答了题目"是不同的失败。
- **当前 skill 支持**：无专门 skill。
- **失败归因**：F3 Alignment failure（优化目标错误 = 答非所问）。
- **Adversarial test 设计**：题目要求"最小化成本"，模型优化"最大化产出"，检查 evaluator 能否区分"目标方向错误"与"约束缺失"。

#### 层级 6：Constraints

- **定义**：识别并形式化所有约束（物理/工程/经济/逻辑/边界），确保约束完备且方向正确。
- **当前测量**：C5 structural 维度部分覆盖；checklist §2"约束完备性"；P13-3C-R4 B1-C 消融专门测试约束干预。
- **当前 skill 支持**：`model_construction_checklist.md` §2 + §6（符号方向）。
- **失败归因**：F4 Modeling failure（约束缺失）或 F5 Formalization failure（约束方向错误，如 P13-3C 2022_B 的 s_e 符号错误使约束越松）。
- **Adversarial test 设计**：构造"约束符号方向错误"的模型（短缺变量以正号进入上界），这是 P13-3C 盲评实锤的真实失败。

#### 层级 7：Mechanism

- **定义**：选择正确的机理（微分方程/差分方程/马尔可夫/质量作用/效用函数…），确保机理与问题物理/现实一致。
- **当前测量**：无独立测量。这是当前最大的测量盲区——"机理选错"与"方程写错"被混在 mathematical 维度中。
- **当前 skill 支持**：方法卡（53 个 methodology .md）提供机理参考，但无"机理选择正确性"evaluator。
- **失败归因**：F4 Modeling failure（wrong mechanism）。
- **Adversarial test 设计**：对连续动力学问题使用静态评价方法（如 P15.1 的 TOPSIS for kinematics），这是 wrong mechanism 的极端案例。

#### 层级 8：Equations

- **定义**：方程推导正确性、量纲一致、符号/索引/边界正确。
- **当前测量**：C6 `model_construction.py: mathematical` 维度，错误分类学扣分制（量纲/索引/符号/边界/校准/缺失约束/未陈述假设）。
- **当前 skill 支持**：checklist §6"数值口径与符号"。
- **失败归因**：F5 Mathematical formalization failure。
- **Adversarial test 设计**：P13-3C-R4 B1-A 已经是天然的 adversarial——对齐干预单独施加时 math 暴跌（65→45、85→20），因为新主张没有数学承载。

#### 层级 9：Solvability

- **定义**：模型是否可解（解析/数值/模拟），求解策略是否与模型口径匹配。
- **当前测量**：C9 无独立 evaluator。P13-3C 2022_B B1 的"年率 g 按月复利"是 solvability 层的失败（求解步长与参数口径不匹配）。
- **当前 skill 支持**：`template-selector` + `code-implementer`（legacy），但无策略级评估。
- **失败归因**：F6 Solving failure。
- **Adversarial test 设计**：构造刚性 ODE 但使用显式欧拉法，观察是否数值发散。

#### 层级 10：Validation

- **定义**：验证模型正确性——对照基线、灵敏度分析、残差分析、交叉验证、极限检验。
- **当前测量**：C11 有 `experiment_validity` + `validation_reliability`；P14 完整 Evidence→Claim 链。
- **当前 skill 支持**：P14 `p14_integrity_gate.py`；P15 sensitivity plan（±20%, 10 steps）。
- **失败归因**：F7 Validation failure。
- **Adversarial test 设计**：构造"通过了内部一致性检验但与现实数据矛盾"的模型，验证是否能被外部检验捕获。

#### 层级 11：Result Interpretation

- **定义**：结果的物理/现实意义解释、量级合理性、反直觉结论的说明。
- **当前测量**：C13 无独立 evaluator。
- **当前 skill 支持**：checklist §1"校准合理性"隐含量级检查。
- **失败归因**：F8 Evidence failure（结果解释无证据支撑）或 F13（见 §5 扩展）。
- **Adversarial test 设计**：P13-3B 2000C 的"幼龄份额 61%"是天然案例——公式能运行但结果生物不合理，需要量级合理性检查捕获。

### 2.3 Claim Surface × Support Surface 框架

P13-3C 四轮实验共同确立了 Model Construction 的二维分解（`P13_3C_REPORT.md` §4.6）：

```
                    Support Surface
                  （Formal Consistency：
                   方程/参数/约束/域——
                   模型能兑现什么）
                         ↑
                         │      ● B1-F（大主张 + 强支持）
                         │
                         │  ● MMA（中主张 + 中支持）
          ● B0（小主张 + 中支持       │
            少说所以少错）             │
                         │   ● B1-A（大主张 + 弱支持
                         │      = unsupported claims）
                         └──────────────────→
                              Claim Surface
                         （Problem Alignment：
                          模型声称回答什么）
```

**关键派生指标**（P13-3C §4.7 预注册，R5 已实测）：

- **Claim Coverage** = 题目要求中被产物明确承载的对齐点比例（= alignment 维度）
- **Support Coverage** = 产物主张中有正式数学承载的比例（三条件：①存在生成该主张的机制方程；②方程引用的参数全部已声明；③主张类型与模型结构相容）
- **Claim-Support Gap** = Claim Coverage − Support Coverage

R5 实测（7 题均值）：

| Arm | Claim Cov | Support Cov | Gap |
|---|---|---|---|
| B0 | 9.3 | 14.3 | −5.0 |
| MMA | 76.2 | 41.7 | +34.5 |
| B1-F | 92.9 | 55.9 | +37.0 |

**B1-F 的 Support Coverage（55.9）仍未达满**——残差缺口 = 未声明参数/符号类缺陷的总和，即清单的下一步靶点。

---

## 3. Failure Taxonomy 重审

### 3.1 当前 P15 Taxonomy

P15 PRE_REGISTRATION §4 定义了 6 类 22 种 failure mode：

| 类别 | 代号 | 种数 | 编号 |
|---|---|---|---|
| Problem Alignment | FM-PA | 3 | 01-03 |
| Model Construction | FM-MC | 5 | 01-05 |
| Formal Consistency | FM-FC | 4 | 01-04 |
| Solving | FM-SV | 3 | 01-03 |
| Validation | FM-VA | 4 | 01-04 |
| Claim Support | FM-CS | 3 | 01-03 |

从 `by_failure_mode.json` 的实际标注看：

| FM | 标注题数 | 占比（36题） | 状态 |
|---|---|---|---|
| FM-PA-01 | 1 | 3% | 稀疏 |
| FM-PA-02 | 11 | 31% | 常用 |
| FM-PA-03 | 0 | 0% | **空** |
| FM-MC-01 | 4 | 11% | 常用 |
| FM-MC-02 | 8 | 22% | 常用 |
| FM-MC-03 | 11 | 31% | 常用 |
| FM-MC-04 | 14 | 39% | 最广 |
| FM-MC-05 | 0 | 0% | **空** |
| FM-FC-01 | 10 | 28% | 常用 |
| FM-FC-02 | 6 | 17% | 常用 |
| FM-FC-03 | 5 | 14% | 常用 |
| FM-FC-04 | 0 | 0% | **空** |
| FM-SV-01 | 11 | 31% | 常用 |
| FM-SV-02 | 3 | 8% | 稀疏 |
| FM-SV-03 | 0 | 0% | **空** |
| FM-VA-01 | 29 | 81% | **几乎全题** |
| FM-VA-02 | 6 | 17% | 常用 |
| FM-VA-03 | 0 | 0% | **空** |
| FM-VA-04 | 8 | 22% | 常用 |
| FM-CS-01 | 0 | 0% | **空** |
| FM-CS-02 | 0 | 0% | **空** |
| FM-CS-03 | 0 | 0% | **空** |

**22 种 failure mode 中有 7 种（32%）标注为 0 题**，包括全部 FM-CS 三类。这说明当前 taxonomy 存在严重的"定义了但观察不到"的问题。

### 3.2 逐类审查

#### FM-PA（Problem Alignment）

1. **是否互斥？** 与 FM-MC 不互斥。P15.1 2024_A 同时标注 FM-PA-02 和 FM-MC-03——子问题未分解（PA）和方法族不匹配（MC）是同一根因（type-classifier 误分类）的两个表现。
2. **是否存在大量 overlap？** 是。FM-PA-02（子问题分解失败）与 FM-MC-03（模型结构不完整）在 11 题上同时出现。
3. **是否遗漏关键 failure mode？** 是。缺少"wrong abstraction"（问题类型误判，如运动学→评价）——这是 P15.1 的首要根因，但当前 taxonomy 只能归到 FM-PA-02 或 FM-MC-03，无法精确表达。
4. **是否能被 evaluator 观察？** FM-PA-02 可以（decomposition_coverage / count-ratio），但 FM-PA-01/03 无对应 evaluator。
5. **是否可以从真实 CUMCM 论文中找到实例？** 是。P15.1 2024_A B0 是 FM-PA-02 的完整实例。
6. **是否可以构造 adversarial test？** 是。构造多子问题但子问题间有隐藏依赖的题目，观察分解是否遗漏依赖关系。
7. **是否能迁移到科研建模？** 部分。科研问题通常没有明确的"子问题列表"，alignment 的定义需要从"覆盖题目子问"变为"覆盖研究问题的各个方面"。

#### FM-MC（Model Construction）

1. **是否互斥？** 内部 5 种之间不互斥。FM-MC-03（结构不完整）与 FM-MC-04（约束缺失）经常同时出现。
2. **是否存在大量 overlap？** 是。FM-MC-04 覆盖 14 题（39%），是最广的 failure mode，但其定义"约束缺失"与 FM-FC-01（形式不一致）边界模糊。
3. **是否遗漏关键 failure mode？** **严重遗漏**。当前 FM-MC 只覆盖"结构不完整/约束缺失/参数未声明"等"缺少了什么"的失败，完全没有覆盖"选错了什么"的失败：
   - wrong mechanism（机理选错，如用评价方法解动力学）
   - wrong causal structure（因果结构错误，如把结果当原因）
   - wrong objective（优化目标错误）
   - wrong scale（尺度错误，如连续模型用于离散事件）
   - wrong boundary（边界条件错误）
4. **是否能被 evaluator 观察？** 部分。`model_construction.py: structural` 可以检测缺失，但无法检测"选错"——选错的模型结构可以是完整的。
5. **是否可以从真实 CUMCM 论文中找到实例？** 是。P15.1 2024_A 的 TOPSIS for kinematics 是 wrong mechanism 的真实实例。
6. **是否可以构造 adversarial test？** 是。这是最容易构造 adversarial 的类别——给一个需要机理建模的题目，观察是否退化为评价方法。
7. **是否能迁移到科研建模？** 是。科研建模中 wrong mechanism / wrong causal structure 是最常见的评审拒稿理由。

#### FM-FC（Formal Consistency）

1. **是否互斥？** 与 FM-MC 边界模糊。"变量域不一致"既可以是形式化问题，也可以是建模问题。
2. **是否存在大量 overlap？** 是。FM-FC-01 与 FM-MC-04 在 10 题上同时出现。
3. **是否遗漏关键 failure mode？** 缺少"量纲不一致"的独立分类（当前混在 math deduction 中）。
4. **是否能被 evaluator 观察？** 理论上可以（确定性检查），但当前无自动化形式一致性检查器。
5. **是否可以从真实 CUMCM 论文中找到实例？** 是。P13-3C 2021_C MMA：M1 计数与质心相加量纲不一致。
6. **是否可以构造 adversarial test？** 是。构造量纲不一致的方程（如米 + 秒），检查是否被捕获。
7. **是否能迁移到科研建模？** 是。形式一致性是通用能力。

#### FM-SV（Solving）

1. **是否互斥？** 内部基本互斥（求解失败/数值发散/精度不足）。
2. **是否存在大量 overlap？** 较少。
3. **是否遗漏关键 failure mode？** 缺少"求解策略与模型不匹配"（如刚性 ODE 用显式欧拉）。
4. **是否能被 evaluator 观察？** `experiment_validity` 可以检测执行失败，但无法检测"策略不当"。
5. **是否可以从真实 CUMCM 论文中找到实例？** 是。P13-3C 2022_B B1：年率 g 按月复利（求解步长与参数口径不匹配）。
6. **是否可以构造 adversarial test？** 是。
7. **是否能迁移到科研建模？** 是。

#### FM-VA（Validation）

1. **是否互斥？** FM-VA-01 覆盖 29/36 题（81%），说明其定义过于宽泛——"验证不充分"几乎适用于所有题。
2. **是否存在大量 overlap？** FM-VA-01 与几乎所有其他 FM 同时出现。
3. **是否遗漏关键 failure mode？** 缺少"验证了错误的东西"（validation of wrong target）——模型验证了内部一致性但没有验证与题目的对应关系。
4. **是否能被 evaluator 观察？** `experiment_validity` + `validation_reliability` 可以检测"有没有做验证"，但不能检测"验证是否有效"。
5. **是否可以从真实 CUMCM 论文中找到实例？** 是。
6. **是否可以构造 adversarial test？** 是。构造"做了灵敏度分析但扰动的是不敏感参数"的模型。
7. **是否能迁移到科研建模？** 是。科研中"验证了错误的东西"是常见问题。

#### FM-CS（Claim Support）

1. **是否互斥？** 无法判断——三类全部为空（0 题标注）。
2. **是否存在大量 overlap？** 无法判断。
3. **是否遗漏关键 failure mode？** 整个类别需要重新定义。P14 已经证明 Claim 可以被判定为 supported/refuted/unresolved，但 P15 benchmark 没有将 Claim Support 失败模式标注到任何题目。
4. **是否能被 evaluator 观察？** P14 `p14_integrity_gate.py` 可以观察，但 P15 未接入。
5. **是否可以从真实 CUMCM 论文中找到实例？** P14 已有 4 条 refuted claim 的实例。
6. **是否可以构造 adversarial test？** 是。构造"论文结论与实验结果矛盾"的模型。
7. **是否能迁移到科研建模？** **是，这是科研迁移的核心能力。** 科研论文的核心就是 claim-evidence 对应关系。

### 3.3 遗漏的关键 Failure Mode

基于 P13/P14/P15 的全部证据，以下 failure mode 在当前 taxonomy 中缺失或定义不足：

| 遗漏 FM | 定义 | 真实实例 | 可观察性 |
|---|---|---|---|
| **wrong abstraction** | 问题类型/建模范式误判 | P15.1 2024_A：运动学→评价类 | 高（method_selection 可检测） |
| **wrong causal structure** | 因果方向错误、混淆相关与因果 | P13-3C 2021_C B0：标签极性矛盾（p_hat 定义为误报概率却按降序优先） | 中（需语义判断） |
| **wrong objective** | 优化目标/估计量与题目要求不一致 | P13-3C 2022_B B0：四问对齐 0，目标函数完全偏离 | 高（alignment 可检测） |
| **wrong constraints** | 约束方向错误/约束了错误的量 | P13-3C 2022_B B1：s_e 以正号进入发电上界（短缺越大约束越松） | 中（需符号检查） |
| **wrong mechanism** | 机理选择错误（用评价方法解动力学） | P15.1 2024_A：TOPSIS for 运动学 | 高（family mismatch 可检测） |
| **wrong scale** | 时间/空间尺度错误（连续 vs 离散、宏观 vs 微观） | P13-3C 2022_B：年率参数在月步长上按期复利 | 中（需量纲/步长检查） |
| **wrong boundary** | 边界条件错误/遗漏边界 | P13-3C 2024_A B1：噪声可产生 R<0，与 R≥0 边界冲突 | 中 |
| **wrong optimization target** | 优化了错误的目标函数（如最大化利润而非最小化成本） | 需构造 | 中 |
| **wrong stochastic assumptions** | 随机过程假设错误（如用正态分布建模非负变量） | P13-3C 2024_A B1：ε~N(0,σ²) 可产生 R<0 | 中 |
| **wrong dependency between submodels** | 子模型间依赖关系错误（独立 vs 级联 vs 反馈） | P13-3C 2022_B MMA：月期量与年率需求无折算 | 低（当前无测量） |
| **wrong interpretation of parameters** | 参数物理意义解释错误 | P13-3B 2000C：m=4.42 校准放大被误读为真实生育率 | 低 |

**核心问题**：当前 taxonomy 偏向"缺少了什么"（omission），严重缺少"选错了什么"（commission）。而 P13-3C 的核心发现——B1 的优势不在数学计算而在结构与对齐——恰恰说明"选错"比"缺少"更根本。

---

## 4. Method Correctness ≠ Model Correctness（核心原则）

### 4.1 原则陈述

> **一个方法可以在数学上完全正确，但在建模上完全错误。**
> Evaluator 必须能够判定：**mathematically valid BUT problem-alignment FAIL**。
> 这两个维度必须分离，不能混成一个分数。

### 4.2 教科书级案例：P15.1-2024A-B0

2024_A 是运动学/几何建模题（七鳃鳗/龙吐水类螺旋运动），金标准 5 个子问题：
- Q1: 300s 时龙头把手位置坐标
- Q2: 碰撞检测（螺线进出碰撞时间）
- Q3: 最小螺距设计
- Q4: 进入与盘出的螺距变化方案
- Q5: 速度控制（龙头匀速条件下各把手最大速度）

B0 pipeline 的产出：
- 子问题分解：**UNRESOLVED**（1 个空壳 Q001，无 payload）
- 方法兼容性评估：**mc-topsis (TOPSIS)**，备选 AHP(73) / PCA(63)，全部属于评价类方法族
- 可接受的解变体（acceptable_solution_variants）族：**运动学/几何建模 (kinematics/geometric)**
- method_selection = **0%**

TOPSIS 本身是一个数学上完全正确的多属性决策方法。它的公式、计算、排序逻辑都没有问题。但用 TOPSIS 来解"螺旋运动的碰撞检测"——这就像用尺子量温度——工具本身没错，但用错了地方。

**当前 evaluator 的问题**：如果只看 mathematical correctness，TOPSIS 的实现可以得高分；但如果看 problem alignment，应该得 0 分。当前 `model_construction.py` 的三维拆分（structural / mathematical / alignment）已经部分实现了这个分离，但 `e2e_metrics.py` 的 `model_correctness` 指标仍然是一个混合分数。

### 4.3 六维分离模型

基于 P13-3C 的三维拆分和 P15 的五维模型，本审计提出 **六维分离评测模型**：

| 维度 | 评测什么 | 不评测什么 | 对应能力 |
|---|---|---|---|
| **1. Problem Alignment** | 模型是否回答了题目要求（子问题覆盖、目标对齐） | 数学是否正确 | C1, C2 |
| **2. Model-family Selection** | 选择的模型家族是否适合问题类型 | 家族内的具体实现是否正确 | C7 |
| **3. Model Construction** | 模型结构是否完整（变量/参数/假设/目标/约束/机制） | 方程推导是否正确 | C5, C3, C4 |
| **4. Mathematical Correctness** | 方程推导、量纲、符号、索引、边界是否正确 | 模型是否适合问题 | C6 |
| **5. Solving Correctness** | 求解策略、代码执行、数值结果是否正确 | 模型本身是否正确 | C9, C10 |
| **6. Validation** | 验证是否充分、结论是否有证据支持 | 以上各项 | C11, C12, C14 |

**关键规则**：
- 维度 1 和 2 失败时，维度 3-6 的高分**不能补偿**。一个选错方法的模型，即使数学完全正确，整体仍然是 FAIL。
- 维度 4（Mathematical Correctness）必须独立报告。P13-3C-R5 证明 B1 的 math（71.4）甚至低于 B0（73.6），但 B1 的 composite 仍然远高于 B0（86.2 vs 37.1）——如果混成一个分数，这个关键发现就会被掩盖。
- 每个维度必须有独立的 PASS/FAIL 判定，而不是只有一个 composite 分数。

### 4.4 实现建议

1. **`model_construction.py` 已具备三维拆分**（structural / mathematical / alignment），应将其升级为六维，并将 `method_selection` 从 `e2e_metrics.py` 迁入。
2. **新增 `model_family_mismatch` 二元判定**：如果 selected_model 的 family 与题目 allowed_model_families 无交集，直接标记 FAMILY_MISMATCH，此时 mathematical correctness 仅作参考，不作为质量指标。
3. **composite 分数改为条件聚合**：
   - 如果 Problem Alignment < 阈值或 Model-family Selection = FAIL → composite = FAIL，不计算加权平均。
   - 否则 composite = 加权平均，但六维分数必须同时展示。
4. **在 rubric 中增加"mathematically valid but misaligned"标签**，让评委可以明确标注这种情况。

---

## 5. 失败归因一等能力（F0–F11）

### 5.1 原则

> **每一次失败必须尝试归类。不要把所有问题都归到 Agent capability。**

当前仓库的失败归因倾向于"Agent 不够强"，但 P13/P14/P15 的证据表明，大量失败的根因不在 Agent 能力，而在输入、感知、基础设施或 evaluator 本身。

### 5.2 F0–F11 归因体系

| ID | 归因层级 | 定义 | 诊断方法 | 证据要求 |
|---|---|---|---|---|
| **F0** | Input failure | 题目文本/数据附件缺失、损坏、格式错误 | 检查输入文件 hash、完整性、编码 | 输入文件的 sha256 + 解析错误日志 |
| **F1** | Perception failure | Agent 未能正确读取/理解输入（OCR 错误、截断、编码问题） | 对比 Agent 上下文中的题目文本与原始文件 | Agent 上下文 dump + 原文 diff |
| **F2** | Problem understanding failure | Agent 理解了文本但误解了题意（C0 失败） | 检查 problem-parser 输出与题面的对应关系 | problem_analysis artifact + 题面逐条对照 |
| **F3** | Alignment failure | 子问题分解错误或模型未承载题目要求（C1/C2 失败） | decomposition_coverage + alignment_hit 检查 | 金标准子问题列表 vs produced 子问题列表 |
| **F4** | Modeling failure | 模型构造错误——选错机理/目标/约束/因果结构（C5/C7 失败） | model_construction.py structural + alignment 维度 + family mismatch 检查 | MODEL_ARTIFACT + rubric 扣分明细 |
| **F5** | Mathematical formalization failure | 方程推导错误、量纲/符号/索引/边界错误（C6 失败） | model_construction.py mathematical 维度（错误分类学扣分制） | math_deductions 列表（tag/count/evidence） |
| **F6** | Solving failure | 求解策略错误、代码 bug、数值发散、不收敛（C9/C10 失败） | 执行日志 + replay match 检查 + 多 seed 方差 | Execution artifact + code sha256 + 错误日志 |
| **F7** | Validation failure | 验证不充分、验证了错误的目标、灵敏度分析缺失（C11/C12 失败） | experiment_validity + validation_reliability 检查 | Evidence artifact + robustness tags |
| **F8** | Evidence failure | 结果无法追溯到实验、Claim 无 Evidence 支持、证据与结论矛盾（C14 失败） | Evidence Graph 闭合检查 + Claim 判定 | Evidence→Result→Execution→Spec 哈希链 |
| **F9** | Paper transmission failure | 模型到论文的传输丢失/变异/结构错误（C15 失败） | STC v2 + Fidelity v2 + Mutation log | 论文 vs Artifact 逐项比对 |
| **F10** | Evaluator failure | 评测工具本身有 bug、评分标准不合理、金标准错误 | 复现评测 + 交叉验证 + 人工抽检 | evaluator 输出 + 人工复核记录 |
| **F11** | Infrastructure failure | 基础设施问题——API 超时、环境不一致、依赖缺失、seed 未固定 | 运行环境指纹 + 重试对比 + 依赖版本锁定 | env fingerprint + retry log |

### 5.3 归因优先级与反模式

**归因必须从 F0 开始向上排查，不能跳过。** 典型反模式：

- **反模式 1**：看到数学错误就归 F5，但实际根因是 F3（对齐失败导致模型构造了错误的方程）。P13-3C-R4 B1-A 就是这种情况：math 暴跌（65→45）的根因是对齐干预扩大了主张面而支持面未跟上，不是推导能力下降。
- **反模式 2**：看到结果不对就归 F6，但实际根因是 F0（输入数据缺失）或 F11（环境不一致）。P14 强调 21/21 replay match 就是为了排除 F11。
- **反模式 3**：看到分数低就归 F4（Agent 建模能力差），但实际根因是 F10（evaluator 无法测量）。P15.1 2024_A 的 decomposition_coverage = UNRESOLVED 就是 F10——不是 Agent 没有分解，而是 evaluator 无法从空壳 artifact 中提取子问题。

### 5.4 归因矩阵（真实案例）

| 案例 | 表面现象 | 正确归因 | 错误归因（反模式） |
|---|---|---|---|
| P15.1 2024_A TOPSIS | method_selection=0% | F3（type-classifier 误分类→对齐失败）+ F4（wrong mechanism） | 直接归 F5（数学错误）——TOPSIS 数学没错 |
| P13-3C-R4 B1-A math 暴跌 | math 45/20 | F4（对齐干预扩大主张面，支持面缺位→unsupported claims） | 归 F5（推导能力下降）——同 LLM 推导能力不会突变 |
| P13-3B 2000C 幼龄 61% | 结果不合理 | F4（校准假设不合理，单参数吸收缺口） | 归 F6（求解错误）——代码运行正常 |
| P13-3C 2022_B B1 s_e 符号 | 约束越松 | F5（符号错误）+ F4（约束方向建模错误） | 仅归 F5——符号错误的根因是约束建模时方向判断错误 |
| P15.1 decomposition UNRESOLVED | 无法评分 | F10（evaluator gap：Q001 空壳无法提取子问题） | 归 F3（Agent 未分解）——Agent 可能分解了但 artifact 未承载 |
| P13-3D-R3 H13 FAIL | 映射无效果 | F10（STC v2 为元素提及式，不含组织质量维度） | 归 F9（Writer 能力差）——Writer 条件间差仅 −0.01 |

---

## 6. 最小充分能力集

### 6.1 问题

> 完成高质量数学建模真正需要的最小能力集合是什么？不是 100 个 Skills，而是几个不可约简的核心能力。

### 6.2 候选集评估

基于 C0–C15 的测量现状和 P13/P14/P15 的证据，评估以下候选能力：

| 候选能力 | 是否核心 | 理由 |
|---|---|---|
| **Problem Alignment** | ✅ 核心 | P13-3C-R5：B0 alignment 9.3 是全实验最大信号；没有对齐，一切归零 |
| **Model Construction** | ✅ 核心 | P13-3C 四轮实验证明这是质量上限决定因素；P13-3D 证明 Writer 无法补偿 |
| **Formal Consistency** | ✅ 核心 | P13-3C-R4 消融证明：没有约束纪律的对齐干预会制造 unsupported claims |
| **Solving** | ✅ 核心 | 模型不可解 = 模型不可用；P14 证明确定性求解是 Evidence 的前提 |
| **Validation** | ✅ 核心 | P14 证明 Evidence→Claim 链是结论可靠性的唯一基础 |
| **Evidence** | ✅ 核心 | 与 Validation 互补：Validation 测"有没有验证"，Evidence 测"验证是否支持结论" |
| **Communication** | ✅ 核心 | P13-3D 证明虽然 Writer 不能提升质量上限，但没有 Communication 模型无法交付 |
| Research | ❌ 非核心 | 文献检索是辅助能力，不是建模能力的必要组成；P15 五维模型不包含 |
| Data analysis | ⚠️ 条件核心 | 数据驱动类题目（Data regime）需要，但机理/优化类题目不需要；应作为 Model Construction 的子能力 |
| Literature | ❌ 非核心 | 同 Research，是辅助而非核心 |
| Experiment design | ⚠️ 条件核心 | P14 证明实验设计是 Model→Evidence 的关键环节，但属于 Validation 的子能力 |

### 6.3 Capability Core 定义

**Capability Core = 7 项不可约简能力**：

```
Problem Alignment
    ↓ （输入：正确理解的问题）
Model Construction
    ↓ （输入：对齐的子问题 + 选择与问题兼容的模型家族）
Formal Consistency
    ↓ （输入：构造好的模型结构）
Solving
    ↓ （输入：形式化一致的方程）
Validation
    ↓ （输入：可求解的模型 + 实验设计）
Evidence
    ↓ （输入：验证结果）
Communication
    （输出：可审计的论文/报告）
```

### 6.4 每个核心能力的最小可测量标准

| 核心能力 | 最小可测量标准 | 测量工具 | 通过阈值 |
|---|---|---|---|
| **Problem Alignment** | 子问题覆盖率 ≥ 80%；每个子问题能指认模型中承载它的变量/方程 | `decomposition_coverage` + `alignment_hit` | coverage ≥ 0.8 且无"文字有映射、模型无通道"的对齐点 |
| **Model Construction** | 结构完整性 ≥ 90%（变量/参数/目标/约束/机制全部声明）；无 wrong family | `model_construction.py: structural` + family mismatch 检查 | structural ≥ 90 且 FAMILY_MISMATCH = false |
| **Formal Consistency** | 所有方程引用的参数已声明；量纲一致；约束方向正确；无未陈述假设 | 参数声明检查 + 量纲检查 + 符号方向检查 | 0 个未声明参数；0 个量纲错误；0 个约束方向错误 |
| **Solving** | 代码可执行；多 seed（≥5）replay match；结果收敛 | `experiment_validity` + replay check | 执行成功率 100%；replay match ≥ 95% |
| **Validation** | 至少 1 个对照基线 + 1 个灵敏度分析 + 1 个极限检验 | robustness tags + evaluation_targets 覆盖 | 三类验证各至少 1 项 |
| **Evidence** | 每个 Claim 绑定 ≥1 条 Evidence；Claim 判定为 supported/refuted（非 unresolved） | Evidence Graph 闭合检查 + Claim 判定 | unresolved = 0；evidence_claim_ratio ≥ 1.0 |
| **Communication** | 模型构件到论文的结构传输 ≥ 85%；无 critical mutation | STC v2 + Fidelity v2 | STC ≥ 0.85；critical mutation = 0 |

### 6.5 与当前 29 agent 的对应

当前 legacy 29 agent 可以映射到 7 项核心能力：

| 核心能力 | 对应 agent | 冗余/缺失 |
|---|---|---|
| Problem Alignment | problem-parser, type-classifier, dag-builder | type-classifier 是 P15.1 失败根因，需强化 |
| Model Construction | method-matcher, model-builder, assumption-validator, spec-auditor | 4 个 agent 但无独立的"机理选择"agent |
| Formal Consistency | assumption-validator, spec-auditor | 无自动化形式一致性检查器 |
| Solving | template-selector, code-implementer, test-runner, result-verifier | 4 个 agent，相对完备 |
| Validation | test-runner, result-verifier | 缺少独立的 validation-planner |
| Evidence | 无直接对应 | **缺失**——P14 证明这是核心能力，但 legacy 无对应 agent |
| Communication | structure-planner, section-writer, figure-generator, reference-curator, consistency-checker, final-validator | 6 个 agent，过度配置 |

**关键发现**：Evidence 能力在 legacy 29 agent 中没有直接对应，但 P14 已经证明它是核心能力。这是 V3 重组为 5 Role（analyst/modeler/experimenter/critic/writer）的合理性依据——experimenter role 覆盖了 Solving + Validation + Evidence。

---

## 7. 科研迁移分析

### 7.1 原则

> P15 最终不能成为一个封闭的 CUMCM 系统。每个能力都必须回答：是否可迁移到科研？迁移需要什么变化？哪些是比赛特有？哪些是通用建模能力？

### 7.2 逐能力迁移分析

| 能力 | 可迁移性 | 迁移需要的变化 | 比赛特有部分 | 通用建模能力部分 |
|---|---|---|---|---|
| **C0 Problem Understanding** | 高 | 科研问题没有明确的"子问题列表"和"交付物要求"，需要从研究目标中自发生成问题分解 | 题目有明确的子问编号和交付要求 | 理解问题域、识别关键约束、确定研究范围 |
| **C1 Problem Alignment** | 中 | 比赛 alignment = 覆盖题目子问；科研 alignment = 覆盖研究问题的各个方面 + 与文献的对话 | 子问题覆盖率有金标准可比对 | 模型是否回答了研究者真正关心的问题 |
| **C2 Subproblem Decomposition** | 高 | 科研中子问题分解是研究者的核心创造力，不是题目给定的 | 题目通常已隐含子问题结构 | 将复杂研究问题分解为可解子问题 |
| **C3 Variable/Parameter ID** | 高 | 科研中参数来源更多元（文献/实验/校准/先验），可观测性判断更重要 | 比赛参数通常在题面中给出 | 识别内生/外生变量、区分可观测/不可观测参数 |
| **C4 Assumption Construction** | 高 | 科研假设需要与文献对话、需要可证伪性、需要显式标注假设对结论的影响 | 比赛假设通常是"合理简化" | 构建显式、可检验、可证伪的假设集 |
| **C5 Model Construction** | **最高** | 科研建模更强调机理的创新性和与已有模型的对话；比赛更强调"覆盖题目" | 比赛有"标准答案"方向（allowed_model_families 参考） | 从问题到数学模型的完整构造能力——完全通用 |
| **C6 Mathematical Formalization** | **最高** | 无变化——数学是通用语言 | 无 | 方程推导、量纲一致、符号正确——完全通用 |
| **C7 Model-family Selection** | 高 | 科研中模型家族选择需要文献依据，不是"选对方法"而是"选择最适合研究问题的范式" | 比赛有 allowed_model_families 参考标签 | 根据问题类型选择合适的建模范式 |
| **C8 Cross-question Interface** | 中 | 科研中子模型间的依赖关系更复杂（反馈循环、多尺度耦合） | 比赛子问题通常是串行的 | 子模型间接口设计、变量复用、参数传递 |
| **C9 Solving Strategy** | 高 | 科研求解更强调可复现性和计算效率，可能需要 HPC | 比赛时间受限，求解策略偏实用 | 选择合适的求解算法、处理可解性 |
| **C10 Computational Reliability** | **最高** | 科研更严格——需要完整的环境锁定、版本控制、数据管理 | 比赛 seed 固定即可 | 确定性、可复现、数值稳定——完全通用 |
| **C11 Validation** | **最高** | 科研验证更严格——需要外部数据验证、交叉验证、与已有结果对比 | 比赛验证通常是内部一致性 | 模型验证的方法论——完全通用 |
| **C12 Sensitivity/Robustness** | 高 | 科研中不确定性量化（UQ）是独立领域，比比赛的 ±20% 扰动更复杂 | 比赛 sensitivity plan 标准化（±20%, 10 steps） | 参数扰动下的结论稳定性分析 |
| **C13 Result Interpretation** | 高 | 科研结果解释需要与文献对话、讨论局限性、提出未来工作 | 比赛结果解释通常是"回答题目" | 结果的物理/现实意义、量级合理性 |
| **C14 Claim Support** | **最高** | 科研的核心就是 claim-evidence 对应关系；P14 的 supported/refuted/unresolved 三分法直接可用 | 比赛 claim 通常是"答案" | 每个结论必须有可追溯的证据支持——完全通用 |
| **C15 Model→Paper Transmission** | 中 | 科研论文结构不同（IMRAD），但"模型构件到论文的忠实传输"原则通用 | 比赛论文有固定结构（问题重述/假设/模型/求解/结果） | 模型到论文的忠实传输、无未授权变异 |

### 7.3 必须设计为 domain-independent 的能力

以下 5 项能力必须设计为领域无关（domain-independent），这是科研迁移的基础：

1. **Problem Alignment**：从"覆盖题目子问"泛化为"覆盖研究问题的各个方面"。测量方法从"与金标准子问题比对"变为"与研究目标的逐条映射"。
2. **Model Construction**：从"比赛模型构造"泛化为"通用科学建模"。`model_construction_checklist.md` 的 7 类检查（校准合理性/约束完备性/不确定性传播/口径一致性/声明完备性/数值口径符号/主张-支持配对）完全通用。
3. **Formal Consistency**：数学形式一致性是领域无关的。参数声明检查、量纲检查、符号方向检查在任何领域都适用。
4. **Validation**：验证方法论（对照/灵敏度/极限/交叉验证）是通用科学方法。
5. **Evidence**：claim-evidence 对应关系是科学方法的核心。P14 的六实体链（Model→ExperimentSpec→Execution→Result→Evidence→Claim）完全通用。

### 7.4 比赛特有、需要解耦的部分

| 比赛特有 | 解耦方案 |
|---|---|
| 题目有明确子问题编号和金标准 | 科研模式下子问题由研究者生成，alignment 测量改为"研究目标覆盖率" |
| allowed_model_families 参考标签（非唯一答案） | 科研模式下方法兼容性评估需要文献依据，改为"方法兼容性评估的文献支持率" |
| CUMCM rubric 评分细则 | 科研模式下使用通用审稿标准（novelty/correctness/significance/clarity） |
| 20 页篇幅限制 | 科研无篇幅限制，但 Communication 能力仍需测量 |
| 3 天时间限制 | 科研无时间限制，但 Solving 效率仍需测量 |

---

## 8. 能力训练路线（从"刷题"到"能力训练"）

### 8.1 原则

> **不是刷 50 道题，而是：Problem → Baseline → Failure diagnosis → Targeted intervention → Fresh problem → Cross-family validation → Generalization test。**

P13 系列已经证明了这种训练范式的有效性：P13-3B（干预实验，55→95）→ P13-3C（泛化验证，3 题三臂）→ P13-3C-R5（扩展基准，7 题）。每一步都有明确的测量指标和停止条件。

### 8.2 七阶段训练路线

#### 阶段 1：Problem（选题）

- **操作**：从 CUMCM-Bench-v2（36 题）中选择目标题目，生成 `question_profile`（regime/difficulty/subproblem_count/family/mechanism_depth/ambiguity_level）。
- **测量指标**：题目难度标签（5 维 × low/medium/high）、模型家族标签。
- **停止条件**：题目 profile 冻结，difficulty 在看到结果之前锁定（P13-3C-R5 纪律）。
- **关键纪律**：**difficulty 必须前置锁定**，不能在看到结果后回溯标注（post-hoc 标注不进入难度控制分析）。

#### 阶段 2：Baseline（首跑基线）

- **操作**：B0 条件（无干预）跑完整 pipeline，记录全部 8 项 e2e metrics + 3 维 model_construction 分数。
- **测量指标**：
  - decomposition_coverage
  - method_selection（含 family mismatch 二元判定）
  - model_construction 三维（structural/mathematical/alignment）
  - experiment_validity
  - validation_reliability
  - end_to_end
- **停止条件**：基线分数稳定（多 seed 方差 < 10%），所有指标如实记录（包括 n/a 和 UNRESOLVED）。
- **关键纪律**：**首跑的意义不是分数高，而是让失败第一次变得可测量。** 预期基线分数很低——这正是价值。

#### 阶段 3：Failure diagnosis（失败诊断）

- **操作**：对基线失败进行 F0–F11 归因，定位到具体能力层级（C0–C15）和具体 failure mode。
- **测量指标**：
  - 归因结果（F0–F11 中的哪一级）
  - 失败模式标签（FM-XX-NN）
  - Claim-Support Gap（如果适用）
  - major 缺陷计数（severity/category/evidence）
- **停止条件**：每个失败都有明确的归因 + 证据指针，不允许"Agent 能力不足"这种模糊归因。
- **关键纪律**：**归因必须从 F0 开始向上排查**，不能跳过输入/感知/基础设施层直接归 F4/F5。

#### 阶段 4：Targeted intervention（定向干预）

- **操作**：针对诊断出的具体失败，施加定向干预（修改 Brain 指令/知识卡/策略），不做全局改动。
- **测量指标**：干预前后的目标指标 Δ（如 math 55→95、alignment 9.3→92.9）。
- **停止条件**：目标指标有显著 Δ（≥10 个百分点或从 FAIL 到 PASS），且其他指标不回退。
- **关键纪律**：
  - **任何能力升级，如果没有 baseline，就不算能力升级。**（P13-3C 治理铁律）
  - 干预实验（同题前后对照）与能力实验（跨题迁移）是两种不同的证明，治理上分开锁死。
  - P13-3C-R4 的教训：**单独施加对齐干预可能有害**（math 65→45），干预必须考虑 Claim Surface × Support Surface 的交互效应。

#### 阶段 5：Fresh problem（新题验证）

- **操作**：在**未触碰过的新题**上重复 B0 vs B1 对比，验证干预是否可迁移。
- **测量指标**：新题上的 Δscore（同题配对差值），per-regime Δ，per-dimension Δ。
- **停止条件**：在 ≥3 道未见题、≥2 个 regime 上，B1 > B0 全部成立。
- **关键纪律**：**必须用未见题**，不能用干预时用过的题目（否则是过拟合，不是能力提升）。P13-3C 用 2024_A/2021_C/2022_B 三题三 regime 验证了迁移性。

#### 阶段 6：Cross-family validation（跨家族验证）

- **操作**：在不同模型家族（机理/数据/优化/混合）上验证干预的泛化性。
- **测量指标**：
  - 按 family 分组的 B1 > B0 成立率
  - 按 regime 分组的 mean Δ
  - 例外题目的深度剖析（如 P13-3C-R5 的 2025_B MMA 反超）
- **停止条件**：在 ≥4 个 regime 上 B1 > B0 成立率 ≥ 80%，且例外题目有合理解释（不是干预失败，而是能力剖面互补）。
- **关键纪律**：**例外题目比平均分数更有价值。** P13-3C-R5 的 2025_B（MMA 81.7 > B1 60）揭示了"清单干预不是万能护身符"，指向 Planner 层的互补能力。

#### 阶段 7：Generalization test（泛化测试）

- **操作**：在 ≥10 题、覆盖全部主要家族的题库上跑完整评测，形成能力台账。
- **测量指标**：
  - 八项 e2e metrics 的题集均值 + per-problem 明细
  - 三维 model_construction 分数
  - Claim Coverage / Support Coverage / Gap
  - major 缺陷计数（按类别分布）
  - 与上一轮的 Δscore 台账
- **停止条件**：形成"每轮改动 → Δ"台账，至少 2 个完整测评轮次，八项指标无一回退。
- **关键纪律**：**end-to-end 是最终指标，不是开发指标。** 开发指标 = 7 项分指标，每个改动只认"它让哪个分指标动了多少"。

### 8.3 训练路线与 P13/P14/P15 的对应

| 训练阶段 | 已完成的实验 | 关键数据 |
|---|---|---|
| Problem + Baseline | P13-0, P15.1 | 2000C baseline 63.0；2024_A B0 decomposition UNRESOLVED |
| Failure diagnosis | P13-3 首测 | structural 80 / math 55 / alignment 100——短板"结构好、数学弱" |
| Targeted intervention | P13-3B | math 55→95（三项干预：校准/约束/不确定性传播） |
| Fresh problem | P13-3C 3 题 | B1 93.9 > MMA 83.9 > B0 50.0，三 regime 全胜 |
| Cross-family | P13-3C-R5 7 题 | B1 86.2 > MMA 69.5 > B0 37.1；H5 7/7；H6 6/7 |
| Generalization | P15（进行中） | 32→36 题 benchmark；P15.1 首题 B0 已测量 |
| Model→Paper | P13-3D-R3 | 48 篇论文；映射无效果但无害；质量上限由 Model Construction 决定 |
| Model→Evidence | P14 | 6 spec / 21 execution / 9 claim；5 supported / 4 refuted |

### 8.4 停止条件汇总

| 阶段 | 停止条件 | 失败处理 |
|---|---|---|
| Problem | profile 冻结 | 题目不适合则换题 |
| Baseline | 多 seed 方差 < 10% | 方差过大→查 F10/F11 |
| Failure diagnosis | 每个失败有 F0–F11 归因 + 证据 | 无法归因→标记为 evaluator gap（F10） |
| Targeted intervention | 目标指标 Δ ≥ 10pp 且无回退 | Δ ≤ 0→就地停止，不为转正继续修改 |
| Fresh problem | ≥3 未见题 ≥2 regime 全胜 | 不成立→干预是过拟合，回滚 |
| Cross-family | ≥4 regime 成立率 ≥ 80% | 例外题→深度剖析，不强行掩盖 |
| Generalization | ≥2 轮次台账，八项指标无回退 | 回退→回滚改动，记录 regression |

---

## 9. 行动建议（优先级排序）

基于以上审计，按优先级排序的行动建议：

### P0（立即执行）

1. **修复 C2 Subproblem Decomposition 的 evaluator gap**：P15.1 已证明 `problem_analysis` 节点不做子问题分解，Q001 是空壳。这是当前最阻塞的测量盲区。
2. **将 method_selection 升级为 family mismatch 二元判定**：TOPSIS for kinematics 这种错配必须被直接标记为 FAMILY_MISMATCH，而不是给一个 0% 的 method_selection 分数。
3. **填补 FM-CS 三类全空的问题**：将 P14 的 Claim 判定能力接入 P15 benchmark，至少标注"哪些题目容易出现 claim-evidence 不匹配"。

### P1（短期，1–2 周）

4. **扩展 failure taxonomy**：增加 wrong abstraction / wrong mechanism / wrong causal structure / wrong objective / wrong constraints 等"选错类"失败模式。
5. **将 model_construction.py 从三维升级为六维**：分离 Problem Alignment / Model-family Selection / Model Construction / Mathematical Correctness / Solving Correctness / Validation。
6. **建立 C8 Cross-question Model Interface 的测量**：当前完全没有测量，但 P13-3C 已暴露多子问题口径不一致的失败。

### P2（中期，1 个月）

7. **为 C4 Assumption Construction 建立量化 evaluator**：当前只有 qualitative judgment，但 P13-3B 证明假设质量是 math 55→95 的关键杠杆。
8. **将 P14 的 Evidence 能力固化为 core evaluator**：P14 已证明 6 项能力全部 PASS，但仍在 research/ 轨道，需要迁入 core/evaluation/。
9. **建立 domain-independent 的 Problem Alignment 测量**：从"覆盖题目子问"泛化为"覆盖研究目标"，为科研迁移做准备。

### P3（长期）

10. **完成 P15 的 15 题 Model Construction 跨家族泛化验证**（P15.2）。
11. **建立能力训练路线的自动化执行框架**：将七阶段训练路线固化为可重复执行的 protocol。
12. **科研迁移试点**：选择 1–2 个真实科研问题，验证 Capability Core 的 7 项能力是否可迁移。

---

## 10. 附录：证据索引

| 结论 | 证据来源 | 具体数据 |
|---|---|---|
| Model Construction 是质量上限 | P13-3D-R3 §4 | arm 间 PQ 差 ~18 分，Writer 条件间差 −0.01 |
| B1 优势不在数学计算 | P13-3C-R5 §8.1 | Mathematical: B1 71.4 < B0 73.6；Structural: 94.3 vs 28.4 |
| 三题三臂主矩阵 | P13-3C §2.1 | B1 93.9 > MMA 83.9 > B0 50.0 |
| 对齐干预单独有害 | P13-3C-R4 §4.2 | math 65→45、85→20；major 缺陷 4→6、3→5 |
| math 55→95 干预 | P13-3B MODEL_SPEC §8 | 三项干预：双分支括弧/约束完备/不确定性传播 |
| 2024_A B0 完全错配 | P15.1 §4 | TOPSIS for 运动学；method_selection=0%；decomposition UNRESOLVED |
| P14 验证链通过 | P14 PILOT_REPORT §1 | 6/6 能力 PASS；5 supported / 4 refuted / 0 unresolved |
| FM-CS 三类全空 | by_failure_mode.json | FM-CS-01/02/03 均为 0 题 |
| FM-VA-01 覆盖 81% | by_failure_mode.json | 29/36 题标注 FM-VA-01 |
| 7 种 FM 标注为 0 | by_failure_mode.json | FM-PA-03, MC-05, FC-04, SV-03, VA-03, CS-01/02/03 |
| Claim×Support 平面 | P13-3C §4.6/§8.4 | B1 Claim 92.9 / Support 55.9；Gap +37.0 |
| 2025_B MMA 反超 | P13-3C-R5 §8.3 | MMA 81.7 > B1 60；B1 有真实符号错误 |
| 八项能力指标 | CAPABILITY_ROADMAP §1 | decomposition/method/model/experiment/validation/innovation/writing/e2e |
| 29 agent 映射 | METRICS.md + AGENTS.md | modeler 8 / programmer 6 / writer 7 / reviewer 8 |

---

*报告结束。本文件为审计产出，不修改任何仓库核心文件。*
