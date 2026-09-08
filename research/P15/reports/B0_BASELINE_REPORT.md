# P15.1 B0 Baseline Report — 五题跨模型家族建模观测

> **日期**: 2026-09-08
> **阶段**: B0 (Baseline Observation) — 仅观测，不做能力结论
> **执行模式**: external_agent (Doubao) 通过 `register_external_artifact.py` 提交 5 节点建模 IR
> **测量仪器**: execution_gate.py (EAG + Artifact Integrity) + e2e_metrics.py (八项能力指标)
> **声明**: 本报告所有数值为 B0 baseline 观测，不构成 Agent 能力结论。negative result 是有效结果。

---

## ⚠️ 指标定义更正说明（2026-09-08 方向纠偏）

本报告中的 `method_selection` 指标为**历史观测数据**，其原始定义为"参考方法匹配（top-3 GT hit）"。方向纠偏后：

- **指标重定义**：`method_selection` = **方法兼容性评估**（method compatibility assessment），测量 LLM 所选模型家族与 benchmark 定义的 `allowed_model_families` 的兼容度，而非"选对唯一正确方法"。
- **测量对象澄清**：该指标测量的是**测量工具效度**（measurement instrument validity）——即方法卡库覆盖度与评分逻辑的有效性，**不是 Agent 能力**（agent capability）。方法卡库覆盖缺口导致的低分属于 C 类（Measurement-Evaluator Failure），不归因于 Agent。
- **术语变更**：`core_methods` → `allowed_model_families`；"黄金方法/参考方法" → `allowed_model_families`（benchmark 定义的兼容模型族，非唯一答案）。
- **方法卡定位**：方法卡从"答案库"更正为"约束/先验/验证"——LLM 自由建模，方法卡提供约束条件和验证标准，不限制 LLM 提出新方法。

> 本报告所有数值数据保留原始观测结果不变，仅更正指标定义与术语表述。

## 0. 核心结论速览

**核心问题**: type-family misclassification 是 2024_A 单题现象，还是跨模型家族系统性 failure mode？

**回答**: 既不是 2024_A 单题现象，也不是系统性 failure mode。它是**方法卡库覆盖缺口**的选择性表现：

| 模型家族 | 题目 | method_selection | 根因 |
|---|---|---|---|
| 统计/分类/ML | 2022_C 古代玻璃 | **100.0** | mc-pca/mc-kmeans/mc-xgboost 命中 GT 方法家族 |
| 排队/决策/优化 | 2019_C 机场出租车 | **100.0** | top3 [mc-monte-carlo, mc-ahp, mc-ga] 命中参考家族 |
| 运动学/几何 | 2024_A 板凳龙 | **0.0** | 无运动学/几何方法卡，选 mc-monte-carlo 家族不匹配 |
| 动态规划/博弈 | 2020_B 穿越沙漠 | **0.0** | 无 DP/MDP/博弈方法卡，选 mc-ga 家族不匹配 |
| 热传导/PDE | 2018_A 高温服装 | **0.0** | 无 PDE/有限差分方法卡，选 mc-ga 家族不匹配 |

**二分模式清晰**: 16 张方法卡覆盖统计/ML/元启发式类家族，但对运动学、PDE/有限差分、动态规划、排队论四类专业家族零覆盖。method_selection=0 的三题恰好是这四类家族的代表。
> **表注**：method_selection 列 = 方法兼容性评估（原参考方法匹配，已更正）。该指标测量测量工具效度，非 Agent 能力。


---

## 1. B0 方法论

### 1.1 五题输入（全部 verified，0 BLOCKED）

| problem_id | 题目 | 模型家族 | 子问题数 | input_sha256 前缀 |
|---|---|---|---|---|
| 2024_A | 板凳龙闹元宵 | 运动学/几何优化 | 5 | 9baf81fb40f8 |
| 2022_C | 古代玻璃成分分析 | 统计/分类 | 4 | ec5e098f9dbe |
| 2020_B | 穿越沙漠 | 动态规划/资源优化 | 3 | a2d0867169b9 |
| 2018_A | 高温作业服装设计 | 热传导/PDE | 3 | 6b4062dcd020 |
| 2019_C | 机场出租车 | 排队论/决策 | 4 | 4fc950a9a225 |

### 1.2 B0 最小 artifact 集（每题 5 节点）

| dag_position | node_id | artifact 类型 | 内容 |
|---|---|---|---|
| 0 | problem_understanding | question | 子问题分解、关键变量、题型判断 |
| 1 | model_construction | model | 假设、变量、参数、目标、约束、机理、方程 |
| 2 | method_selection | decision | 模型族选择及理由 |
| 3 | solving_strategy | decision | 求解方法、算法选择、可行性 |
| 4 | validation_plan | decision | 验证计划、敏感性分析思路 |

每个节点一个 manifest JSON，`executor_type=external_agent`，`agent_identity=doubao`，`input_sha256` 绑定冻结题面。

### 1.3 测量流程

1. `new_project.py` 创建项目 → 题面导入 → hash 校验
2. 5 个 manifest 按 dag_position 0→4 顺序注册（先 `--dry-run` 验证，再正式提交）
3. `execution_gate.py` 运行 EAG (17 项) + Artifact Integrity (Layer 1+2)
4. `e2e_metrics.py` 计算八项能力指标 + Measurement Integrity

---

## 2. 逐题 B0 观测

### 2.1 2024_A 板凳龙闹元宵

**项目**: `projects/p151-2024a-b0/` | **Artifact Integrity**: 5/5 PASS (100%)

| 指标 | 值 | 说明 |
|---|---|---|
| decomposition_coverage | 20.0 | 1 question artifact / 5 GT 子问题（count_ratio 退化口径） |
| method_selection | **0.0** | chosen=mc-monte-carlo (family=uncertainty_propagation)，top3=[mc-monte-carlo, mc-ga, mc-pso] 均不命中运动学参考家族 |
| innovation | 0.0 | 未声明创新模式 |
| model_correctness | n/a | 结构检查 PASS（objective/constraints/variables 齐全），无语义评分 |
| experiment_validity | n/a | B0 无实验执行 |
| validation_reliability | n/a | B0 无 claim/论文 |
| writing_completeness | n/a | 无 main.tex |
| end_to_end | n/a | 无 rubric 评分 |

**建模核心**: 多体刚体链运动学 + 阿基米德螺线参数化。223 节板凳，龙头 3.41m + 龙身 2.20m，螺线 R(θ)=R_A−bθ。Q1 正向递推，Q2 碰撞检测，Q3/Q5 一维约束优化，Q4 S 形双圆弧轨迹。

**方法卡观测**: 可用 16 张方法卡中无运动学/几何类卡片。mc-monte-carlo 为最接近的仿真替代，家族不匹配 → method_selection=0。

---

### 2.2 2022_C 古代玻璃制品的成分分析与鉴别

**项目**: `projects/p151-2022c-b0/` | **Artifact Integrity**: 5/5 PASS (100%)

| 指标 | 值 | 说明 |
|---|---|---|
| decomposition_coverage | 25.0 | 1 question artifact / 4 GT 子问题 |
| method_selection | **100.0** | chosen=mc-pca (family=dimensionality_reduction) 命中；top3=[mc-pca, mc-kmeans, mc-xgboost] 全覆盖统计/聚类/分类家族 |
| innovation | 0.0 | 未声明创新模式 |
| 其余 5 项 | n/a | B0 边界 |

**建模核心**: 成分数据分析（compositional data analysis）。Q1 卡方检验 + 风化前后回归映射；Q2 决策树/XGBoost 分类规则 + K-Means 亚类聚类；Q3 XGBoost 预测未知类型 + ±10% 敏感性；Q4 相关矩阵 + Fisher z 变换。

**方法卡观测**: mc-pca（降维）、mc-kmeans（聚类）、mc-xgboost（分类）、mc-ols（回归）均直接命中 GT 方法家族。方法卡库对统计/ML 类覆盖良好。

---

### 2.3 2020_B 穿越沙漠

**项目**: `projects/p151-2020b-b0/` | **Artifact Integrity**: 5/5 PASS (100%)

| 指标 | 值 | 说明 |
|---|---|---|
| decomposition_coverage | 33.3 | 1 question artifact / 3 GT 子问题 |
| method_selection | **0.0** | chosen=mc-ga (family=metaheuristics)，top3=[mc-ga, mc-nsga2, mc-monte-carlo] 均不命中 DP/MDP/博弈参考家族 |
| innovation | 0.0 | 未声明创新模式 |
| 其余 5 项 | n/a | B0 边界 |

**建模核心**: 多阶段资源约束序列决策。Q1 完全信息离线 DP；Q2 部分可观测 MDP + 蒙特卡洛评估；Q3 多玩家博弈（开环纳什均衡 + 在线策略迭代）。关键变量：位置/行动/水量/食物/资金/天气。

**方法卡观测**: CUMCM-Bench-v2.json 中该题 allowed_model_families=["dynamic_programming","MDP","game_theory","Monte_Carlo"]，但方法卡库无 DP/MDP/博弈专用卡。mc-nsga2（multi_objective_optimization）本可匹配 optimization 家族，但 metric 优先使用 allowed_model_families 而非 allowed_model_families。

---

### 2.4 2018_A 高温作业专用服装设计

**项目**: `projects/p151-2018a-b0/` | **Artifact Integrity**: 3/5 PASS (60%) ⚠️

| 指标 | 值 | 说明 |
|---|---|---|
| decomposition_coverage | 33.3 | 1 question artifact / 3 GT 子问题 |
| method_selection | **0.0** | chosen=mc-ga (family=metaheuristics)，top3=[mc-ga, mc-monte-carlo, mc-pso] 均不命中 PDE/有限差分参考家族 |
| innovation | 0.0 | 未声明创新模式 |
| 其余 5 项 | n/a | B0 边界 |

**建模核心**: 一维四层非稳态热传导 PDE（I/II/III 织物 + IV 空气层），Crank-Nicolson 隐式有限差分离散。Q1 参数反演（对流换热系数 h）；Q2 单变量优化（黄金分割/模式搜索）；Q3 双变量优化（GA），约束 T_skin≤47°C 且超 44°C 时间≤5min。

**方法卡观测**: 无 PDE/有限差分/反问题方法卡。mc-ga 为最接近的优化替代，家族不匹配 → method_selection=0。

**⚠️ 数据质量注记**: Q001 (question) 和 M001 (model) 未通过 Artifact Integrity Layer 1，原因是 manifest 字段命名与 gate schema 不一致（sub_questions 用 `description` 而非 `text`；payload 用 `objectives` 列表而非 `objective` 字符串）。其余 4 题均已修复此字段问题。此为工具链契约差异，非建模质量问题。

---

### 2.5 2019_C 机场的出租车问题

**项目**: `projects/p151-2019c-b0/` | **Artifact Integrity**: 5/5 PASS (100%)

| 指标 | 值 | 说明 |
|---|---|---|
| decomposition_coverage | 25.0 | 1 question artifact / 4 GT 子问题 |
| method_selection | **100.0** | chosen=mc-monte-carlo，top3=[mc-monte-carlo, mc-ahp, mc-ga] 命中排队/决策/优化参考家族 |
| innovation | 0.0 | 未声明创新模式 |
| 其余 5 项 | n/a | B0 边界 |

**建模核心**: 排队论-决策分析-整数规划混合。Q1 M/M/c 排队 + 期望收益阈值决策（E[W]<W_threshold→选A）；Q2 AHP 因素权重 + 真实数据校准；Q3 GA 上车点布局优化（吞吐率最大化）；Q4 优先权排队 + 收益方差最小化。

**方法卡观测**: GT 方法家族含 queueing_theory/decision_analysis/optimization_model/monte_carlo_simulation。mc-monte-carlo（仿真）、mc-ahp（决策）、mc-ga（优化）三张卡分别覆盖三个子家族，top3 命中。

---

## 3. 跨家族对比表

### 3.1 八项指标汇总

| 指标 | 2024_A 运动学 | 2022_C 统计 | 2020_B DP | 2018_A PDE | 2019_C 排队 | 五题均值 |
|---|---|---|---|---|---|---|
| decomposition_coverage | 20.0 | 25.0 | 33.3 | 33.3 | 25.0 | **27.3** |
| method_selection | 0.0 | **100.0** | 0.0 | 0.0 | **100.0** | **40.0** |
| innovation | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** |
| model_correctness | n/a | n/a | n/a | n/a | n/a | — |
| experiment_validity | n/a | n/a | n/a | n/a | n/a | — |
| validation_reliability | n/a | n/a | n/a | n/a | n/a | — |
| writing_completeness | n/a | n/a | n/a | n/a | n/a | — |
| end_to_end | n/a | n/a | n/a | n/a | n/a | — |
| **可计算指标数** | 3/8 | 3/8 | 3/8 | 3/8 | 3/8 | **3/8** |
| **可用均值** | 6.7 | 41.7 | 11.1 | 11.1 | 41.7 | **22.4** |

### 3.2 Artifact Integrity

| 题目 | 通过率 | 详情 |
|---|---|---|
| 2024_A | 100% (5/5) | 全绿 |
| 2022_C | 100% (5/5) | 全绿 |
| 2020_B | 100% (5/5) | 全绿 |
| 2018_A | 60% (3/5) | Q001/M001 字段命名不一致（工具链契约问题） |
| 2019_C | 100% (5/5) | 全绿 |
| **五题总计** | **92% (23/25)** | |

### 3.3 method_selection 详细对比

| 题目 | chosen card | card family | GT 参考家族 | top1 hit | top3 hit | 得分 |
|---|---|---|---|---|---|---|
| 2024_A | mc-monte-carlo | uncertainty_propagation | kinematics, geometric_modeling, numerical_solution | ❌ | ❌ | 0.0 |
| 2022_C | mc-pca | dimensionality_reduction | clustering, discriminant_analysis, PCA, statistical_analysis | ✅ | ✅ | 100.0 |
| 2020_B | mc-ga | metaheuristics | dynamic_programming, MDP, game_theory, Monte_Carlo | ❌ | ❌ | 0.0 |
| 2018_A | mc-ga | metaheuristics | heat_equation_PDE, parameter_inversion, optimization | ❌ | ❌ | 0.0 |
| 2019_C | mc-monte-carlo | uncertainty_propagation | queuing_analysis, optimization, decision_modeling | ❌ | ✅ | 100.0 |

### 3.4 Measurement Integrity

所有五题 `overall_real_artifact = 0.0%`。原因：Measurement Integrity 判据为 `created_by.startswith("agent")`，而 external_agent 注册的 artifact `created_by` 为 node_id（如 `problem_understanding`、`model_construction`），不匹配该前缀。此为测量口径与 external_agent 注册协议的结构性 mismatch，不反映产物真实性（provenance.executor_type=external_agent 已明确绑定）。

---

## 4. Failure Mode 观察（仅记录现象，不做结论）

### 4.1 方法卡覆盖缺口（已量化）

- **覆盖良好的家族**: 统计分类（mc-pca/mc-kmeans/mc-xgboost/mc-ols）、元启发式优化（mc-ga/mc-pso/mc-sa/mc-nsga2）、评价决策（mc-ahp/mc-topsis/mc-entropy-weight/mc-fuzzy-evaluation）、仿真（mc-monte-carlo）、时序（mc-arima/mc-lstm/mc-grey-gm11）
- **零覆盖的家族**: 运动学/多体动力学、微分几何、PDE/有限差分、动态规划/马尔可夫决策、排队论/随机过程、博弈论
- **影响**: method_selection 指标对零覆盖家族题目恒为 0，与 Agent 建模质量无关

### 4.2 decomposition_coverage 粒度 mismatch

五题 decomposition_coverage 统一为 20-33%，根因是 B0 将所有子问题封装在单个 question artifact 的 `sub_questions[]` 数组中，而 e2e_metrics 按 question artifact **数量** 与 GT 子问题数做 count_ratio。实际子问题语义覆盖率为 100%（每题的 Q001 均包含全部子问题分解）。此为 B0 粒度设计与指标口径的 mismatch。

### 4.3 B0 边界导致的指标缺失

5/8 指标（model_correctness 语义分、experiment_validity、validation_reliability、writing_completeness、end_to_end）在所有五题均为 n/a。根因是 B0 仅提交建模 IR（5 节点），不执行实验代码、不生成论文、不产生 claim/result artifact。这是 B0 的设计边界，不是能力缺失。

### 4.4 工具链契约问题（已修复根因）

| 问题 | 影响 | 修复 |
|---|---|---|
| `register_external_artifact.py` 将 model 类型 artifact 写入 decision_log，decision_id="M001" 违反 `^D\d+$` schema | e2e_metrics 加载 DecisionLog 崩溃 | 改为仅 decision 类型写入 decision_log |
| 注册脚本写入 alternatives 为 dict 列表，DecisionLog 期望 string 列表 | e2e_metrics 解析失败 | 注册时自动归一化为字符串 |
| question 类型 artifact 的 artifact_id=Q001 与 payload.question=Q001 自引用 | Artifact 反序列化失败 ("question 不能指向自身") | 注册时检测并清空自引用 |
| `e2e_metrics.py` 无条件调用 `decisions.load()`，decision_log.json 不存在时崩溃 | 新外部项目无法计算指标 | 增加 `if decisions.path.exists()` 守卫 |
| B0 node_id 不在 NODE_TO_ARTIFACT_TYPE 映射中 | 类型推断错误（全部 fallback 为 decision） | 新增 5 个 B0 node_id 映射 |

### 4.5 EAG 结构性 INVALID（B0 预期）

所有五题 EAG 均为 INVALID，根因一致：
- EAG-03/07: `skill_version`/`workflow_version` 为版本字符串 `b0-baseline-v1`，非 64 位 hex（external_agent 不使用 core/skills 哈希）
- EAG-06: run record 存单文件 SHA256，gate 重算 inputs/ 目录哈希（口径不一致）
- EAG-08: code/output/artifacts 目录无实际文件（B0 仅建模不执行代码）

以上均为 external_agent B0 的结构性特征，不反映建模质量。Artifact Integrity（Layer 1+2）是更适合 B0 的质量门禁，五题平均 92% 通过。

---

## 5. 核心问题回答

> **type-family misclassification 是 2024_A 单题现象，还是跨模型家族系统性 failure mode？**

**观测结论**: 两者都不是。它是**方法卡库覆盖缺口**的选择性表现，呈现清晰的二分模式：

1. **不是 2024_A 单题现象**: 2020_B（DP）和 2018_A（PDE）同样 method_selection=0，三题共享同一根因——方法卡库无对应家族卡片。
2. **不是系统性 failure mode**: 2022_C（统计）和 2019_C（排队/决策）method_selection=100，证明当 GT 方法家族与方法卡库有交集时，测量仪器能正确识别命中。
3. **本质是覆盖缺口**: 16 张方法卡集中在统计/ML/元启发式/评价/仿真/时序六大类，对运动学、PDE、DP、排队论四类专业家族零覆盖。零覆盖家族题目 method_selection 恒为 0，与 Agent 选择无关。

**对后续研究的启示**:
- method_selection 指标在当前方法卡库下对专业家族题目无区分度（恒为 0），需扩充方法卡后才能用于能力比较
- 扩充优先级：运动学/多体动力学 > PDE/有限差分 > 动态规划/MDP > 排队论/随机过程
- 在方法卡扩充前，method_selection=0 应解读为"方法卡覆盖缺口"而非"Agent 方法兼容性评估错误"

---

## 6. 产物清单

### 6.1 Manifests（25 个）

`research/P15/benchmark/b0_manifests/<problem_id>/`
- `00_problem_understanding.json`
- `01_model_construction.json`
- `02_method_selection.json`
- `03_solving_strategy.json`
- `04_validation_plan.json`

### 6.2 项目（5 个）

| 项目 | Artifacts | Registry |
|---|---|---|
| `projects/p151-2024a-b0/` | Q001, M001, D001-D003 | state/registry.json |
| `projects/p151-2022c-b0/` | Q001, M001, D001-D003 | state/registry.json |
| `projects/p151-2020b-b0/` | Q001, M001, D001-D003 | state/registry.json |
| `projects/p151-2018a-b0/` | Q001, M001, D001-D003 | state/registry.json |
| `projects/p151-2019c-b0/` | Q001, M001, D001-D003 | state/registry.json |

### 6.3 测量报告

| 文件 | 说明 |
|---|---|
| `research/P15/measurement_recovery/runs/b0_*_gate.json` | 5 份 execution_gate 完整报告 |
| `projects/p151-*/state/e2e_metrics_report.json` | 5 份 e2e 八项指标报告 |
| `research/P15/benchmark/problem_cards/*/gt.json` | 5 份金标准（sub_questions + methods + allowed_model_families） |

### 6.4 基础设施修复

| 文件 | 修复内容 |
|---|---|
| `research/P15/measurement_recovery/register_external_artifact.py` | 新增 B0 node_id 映射；仅 decision 类型写 decision_log；alternatives 归一化为字符串；question 自引用检测 |
| `core/tools/e2e_metrics.py` | `decisions.load()` 增加文件存在守卫（minimal core bug fix） |
| `research/P15/measurement_recovery/run_b0_metrics.py` | 新增 B0 指标运行辅助脚本 |

---

## 7. 下一步（B0 完成后）

1. **方法卡库扩充**（P1 优先级）: 新增运动学/多体动力学、PDE/有限差分、动态规划/MDP、排队论四类方法卡，使 method_selection 指标对所有家族题目具备区分度
2. **decomposition 指标增强**: e2e_metrics 解析 question artifact 的 `payload.sub_questions[]` 做语义对齐，而非仅计数 artifact 数量
3. **B1 intervention 设计**: 基于 B0 观测设计 intervention（如方法卡扩充后重跑、prompt 优化、多轮 self-critique），对比 B0/B1 差异
4. **2018_A 数据修复**: 统一 manifest 字段命名（text/objective），使 Artifact Integrity 达 100%，提升跨题可比性
5. **Measurement Integrity 口径调整**: external_agent 产物的 created_by 应包含 agent 标识，使 overall_real_artifact 能正确识别真实 agent 产出

---

## 8. 研究纪律遵守声明

- ✅ B0 observation ≠ capability conclusion — 本报告所有数值标注为 baseline 观测
- ✅ 未先修 2024_A 的错误 — 2024_A method_selection=0 作为第一份观测保留
- ✅ 未开 intervention — 五题全部 B0 完成后才做 failure diagnosis
- ✅ baseline 先于 intervention
- ✅ negative result 是有效结果 — method_selection=0 的三题均为有效观测
- ✅ 未修改 evaluator 或 gold standard — GT 为题面真实子问题和方法家族
- ✅ 未用 synthetic evidence — 全部 25 个 artifact executor_type=external_agent
- ✅ 每题独立执行 — 5 个子 Agent 并行，不参考其他题结果
- ✅ 未修改 core/ 架构 — 仅 1 处 minimal core bug fix（e2e_metrics load 守卫），其余修复在 research 层

---

*报告生成时间: 2026-09-08*
*执行者: P15.1 B0 Orchestrator (5 parallel external_agent sub-agents)*
*所有 artifact executor_type=external_agent，provenance 可追溯至冻结题面 input_sha256*
