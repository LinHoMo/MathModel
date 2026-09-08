# Knowledge Calibration Handoff & Implementation Guide

> **日期**：2026-09-08
> **阶段**：Research-layer Calibration 完成，待实施
> **状态**：研究产出完整、自洽、经 Architecture Gate 审核；非回归验证通过；可临时放下，待后续实施

---

## 1. 本阶段做了什么

针对 P15.1 B0 归因发现的"方法卡库 L1/L2 骨架缺失"问题，完成了一次**受证据约束的知识架构考古与校准**：

- 4 份领域研究报告（连续物理 / 离散优化 / 网络博弈 / 分类学元验证），共 ~290KB / 3700+ 行
- 6-PART 最终报告（Taxonomy Audit / Knowledge Map / Knowledge Units / Method Card Candidates / Benchmark Mapping / Research Gaps）
- Architecture Gate 审核（5 条标准，28 项审核）
- **未修改 `core/knowledge/` 下任何现有文件**，全部产出在 `research/P15/knowledge_calibration/`

---

## 2. 核心结论（可冻结部分）

### 2.1 最终四层标签体系

| 层 | 原标签数 | 最终标签数 | 关键变更 |
|---|---|---|---|
| L1 Problem Structure | 8 | **9 + 1属性** | uncertainty 降级为跨层属性；data/evaluation 拆分为 data_analysis + decision_evaluation；新增 continuous_mechanics；diffusion → diffusion/heat_transfer |
| L2 Modeling Pattern | 8 | **11** | state_transition 拆分为 temporal_recurrence + decision_state_transition；新增 statistical_association、inverse_problem；distance/geometry → geometric_constraint |
| L3 Mathematical Formulation | 6 | **7** | differential equation 拆分为 ODE + PDE；graph 确认一级；probability → probability_and_stochastic；optimization 不拆分 |
| L4 Solver/Algorithm | 6 | **12** | GA → metaheuristic_optimization；新增 exact_optimizer、numerical_ODE、simulation、analytical_methods、dimensionality_reduction、graph_algorithm；DP → DP_and_MDP |

### 2.2 6 个跨研究冲突点已裁决

1. **optimization 不拆分**（子类型归入 L4 exact_optimizer）
2. **game-theoretic 不独立为 L3**（独特性在 L2 interaction_game，L3 用 optimization+probability+ODE 组合）
3. **stochastic_process 合并入 probability_and_stochastic**
4. **L4 采纳 12 标签方案**（经 36 题 benchmark 验证）
5. **graph 保持 L3**（三方一致）
6. **uncertainty 降级为跨层属性**（四方一致）

### 2.3 Benchmark 关键发现

- **三题 method_selection=0 完全可归因于 L1/L2 缺失**（非 Agent 能力失败）：
  - 2024_A：motion/geometry 零覆盖 → 现路径完整闭合
  - 2020_B：scheduling+competition/game 零覆盖 → 现路径完整闭合
  - 2018_A：diffusion+conservation_law+spatial_temporal_field 三层联动缺失 → 现路径完整闭合
- **2019_C 的 100 分确认为假阳性**：mc-monte-carlo 只是"用仿真近似排队"，正确核心卡应为 mc-queuing-theory
- 所有新增标签通过 non-overfitting 检查（36 题中 ≥2 题覆盖）

### 2.4 Architecture Gate 结果

| 结果 | 数量 | 说明 |
|---|---|---|
| GATE_PASS | 20 | 可立即进入正式知识库 |
| GATE_PASS_WITH_NOTES | 6 | 可进入但需标注边界 |
| CANDIDATE_PENDING_GATE | 2 | 暂不进入：supply_chain/operations（国赛仅2题）、graph_algorithm（benchmark仅1题且与exact_optimizer重叠） |

---

## 3. 候选方法卡清单

### 3.1 NEW 卡（7 张）

| 优先级 | ID | name | family | 解决什么 |
|---|---|---|---|---|
| **P0** | mc-dp | 动态规划与MDP | dynamic_programming | 2020_B method_selection=0 直接原因 |
| **P0** | mc-numerical-pde | PDE数值求解 | numerical_pde | 2018_A method_selection=0 直接原因 |
| **P0** | mc-queuing-theory | 排队论分析 | queuing_theory | 2019_C 假阳性根因 |
| P1 | mc-game-theory | 博弈论与均衡分析 | game_theory | 2020_B Q3 博弈部分 |
| P1 | mc-network-flow | 网络流与图优化 | network_flow | graph L3 零覆盖 |
| P1 | mc-milp | 混合整数线性规划 | exact_optimization | 调度/资源分配标准精确求解 |
| P1 | mc-ode-modeling | ODE建模与数值求解 | ode_modeling | 2024_A 运动学核心 |

### 3.2 RETRO-TAG / REVISE（4 张现有卡）

| 操作 | ID | 变更 |
|---|---|---|
| RETRO-TAG | mc-ga | family: metaheuristics → metaheuristic_optimization；补 L1/L2/L3/L4 标签 |
| RETRO-TAG | mc-pso | 同上 |
| RETRO-TAG | mc-sa | 同上 |
| REVISE | mc-monte-carlo | L1: uncertainty → [属性]stochastic；L4: [monte_carlo, simulation] |

### 3.3 其他现有卡 RETRO-TAG 摘要（P2）

mc-ols / mc-arima / mc-grey-gm11 / mc-lstm → regression_and_supervised + 对应 L2
mc-xgboost → regression_and_supervised + statistical_association
mc-kmeans → clustering + statistical_association
mc-pca → dimensionality_reduction + statistical_association
mc-ahp / mc-topsis / mc-entropy-weight / mc-fuzzy-evaluation → analytical_methods + 对应 L2
mc-nsga2 → metaheuristic_optimization + resource_constraint

详见 `04_METHOD_CARD_CANDIDATES.md` §2.3。

---

## 4. 候选卡 → 正式 YAML 转换规则

候选卡使用了研究格式，实施到 `core/knowledge/methods/cards/` 时需按以下规则转换：

### 4.1 字段映射

| 候选卡字段 | 正式 schema 字段 | 转换规则 |
|---|---|---|
| `id` | `card_id` | 直接映射 |
| `name` | `name` | 直接映射 |
| `family` | `family` | 直接映射（schema 无 enum 限制，新值可用） |
| `layer_coverage.l1_problem_structures` | `problem_structures` | 提取数组 |
| `layer_coverage.l2_modeling_patterns` | `modeling_patterns` | 提取数组 |
| `layer_coverage.l3_formulations` | `mathematical_forms` | 提取数组 |
| `layer_coverage.l4_solver_type` | （无对应字段） | 写入 `applicability` 或 `reference` 备注；schema 无 L4 字段，建议后续扩展 |
| `problem_types` | `problem_types` | 直接映射 |
| `modeling_patterns`（机理描述） | `modeling_patterns` | 合并（候选卡有两个 modeling_patterns：layer_coverage 中的标签 + 机理描述数组，需合并去重） |
| `formulations` | `mathematical_forms` | 合并 |
| `solvers` | （无对应字段） | 写入 `reference` 或 `applicability`；建议后续 schema 扩展 `solvers` 字段 |
| `requires` | `requires` | 直接映射 |
| `good_for` | `good_for` | 直接映射 |
| `bad_for` | `anti_patterns` | 映射（bad_for 描述的是不适用场景，anti_patterns 描述的是常见错误模式，需区分：bad_for → 写入 `applicability.not_for` 或 `reference`；真正的错误模式 → `anti_patterns`） |
| `risks` | `risks` | 直接映射 |
| `validation` | `validation` | 直接映射 |
| `evidence` | `source_refs` + `reference` | evidence 中的文献引用 → `source_refs`；内部研究引用 → `reference` 备注 |
| `status` | `status` | 直接映射 |

### 4.2 必须补充的 required 字段

现有 schema 的 required 字段：`card_id, name, family, version, problem_types, good_for, requires, risks, validation, often_combined_with, anti_patterns`

候选卡缺少以下字段，实施时必须补充：
- `version: 1`（新卡）或 `version: N+1`（RETRO-TAG 卡）
- `often_combined_with`：根据卡的内容推断兼容方法（如 mc-dp 常与 mc-monte-carlo 组合做策略评估）
- `anti_patterns`：从 `risks` 和 `bad_for` 中提取真正的错误模式

### 4.3 命名规范

- L1 标签：允许斜杠（`motion/geometry`, `diffusion/heat_transfer`），因为描述的是复合问题结构
- L2/L3/L4 标签：统一下划线（`conservation_law`, `spatial_temporal_field`, `probability_and_stochastic`, `metaheuristic_optimization`）
- L3 中 ODE/PDE 全大写（缩写），其余小写
- L4 中 `numerical_PDE`, `numerical_ODE`, `DP_and_MDP` 保留缩写大写，其余下划线小写

---

## 5. 实施清单（按优先级）

### P0 — 立即实施（解决三题 method_selection=0 + 假阳性）

1. **新增 3 张方法卡**：mc-dp, mc-numerical-pde, mc-queuing-theory
   - 按 §4 转换规则写入 `core/knowledge/methods/cards/`
   - 补充 required 字段
2. **RETRO-TAG 3 张卡**：mc-ga, mc-pso, mc-sa（family → metaheuristic_optimization，补四层标签）
3. **更新 method_card.schema.json**：
   - 考虑新增 `solvers` 字段（L4 求解器类型）
   - 考虑新增 `l4_solver_type` 字段或在 `applicability` 中增加
4. **验证**：用更新后的卡库重新运行 2024_A/2020_B/2018_A/2019_C 的 method_selection，检查三题是否 >0、2019_C 是否正确匹配 mc-queuing-theory

### P1 — 下一轮实施（补充知识覆盖）

5. **新增 4 张方法卡**：mc-game-theory, mc-network-flow, mc-milp, mc-ode-modeling
6. **REVISE mc-monte-carlo**：L1 → [属性]stochastic，L4 → [monte_carlo, simulation]
7. **其他 10 张卡 RETRO-TAG**：按 §3.3 摘要补四层标签
8. **建立 L1/L2 标签标注指南**：特别是 GATE_PASS_WITH_NOTES 的 6 项边界（continuous_mechanics vs motion/geometry、inverse_problem 可多标、geometric_constraint vs L1、simulation vs monte_carlo、mc-network-flow vs mc-milp、mc-monte-carlo vs simulation）

### P2 — 待验证后实施

9. **supply_chain/operations**：CANDIDATE_PENDING_GATE，待 benchmark 扩展至 50+ 题且 supply_chain 题数 ≥3 后重审
10. **graph_algorithm**：CANDIDATE_PENDING_GATE，图算法内容暂归入 mc-network-flow，待 benchmark 扩展后重审是否需要独立 L4 标签+卡
11. **REVISE mc-monte-carlo 的 simulation 标签**：需先明确 simulation/monte_carlo 边界

---

## 6. 不能现在冻结的 8 项决策

详见 `06_RESEARCH_GAPS.md` §4：

| # | 决策 | 当前状态 | 不能冻结的原因 | 下一轮验证计划 |
|---|---|---|---|---|
| 1 | L1 supply_chain/operations | ADD（MEDIUM） | 国赛仅2题，长期覆盖度不确定 | benchmark 扩展至50+题，检查题数≥3 |
| 2 | L2 inverse_problem | ADD | 通常与其他L2共存，排他性不确定 | 更多反问题题目上验证独立标注价值 |
| 3 | L4 graph_algorithm | ADD（MEDIUM） | 36题仅1题，与exact_optimizer重叠 | benchmark扩展后检查图算法题数≥3 |
| 4 | L4 simulation vs monte_carlo 边界 | 并列保留 | 边界模糊，实际标注可能不一致 | 制定标注指南，10+题双盲标注一致性检验 |
| 5 | L2 geometric_constraint vs L1 motion/geometry 边界 | 层间关系 | 实际标注可能语义重叠 | 5+运动学题目验证层间区分 |
| 6 | L3 optimization 子类型归属 | 不拆分（裁决） | discrete_optimization建议拆分，来源间有分歧 | 更多优化题目上验证L4 exact_optimizer子类型标注是否足够 |
| 7 | L3 game-theoretic 不独立 | 不独立（裁决） | network_game建议独立，来源间有分歧 | 更多博弈题目上验证optimization+probability组合标注是否足够 |
| 8 | 新增标签的长期 non-overfitting | 当前通过 | 36题有限样本 | benchmark扩展至50+题（含MCM/ICM）重新验证 |

---

## 7. 非回归验证结果

| 检查 | 结果 | 说明 |
|---|---|---|
| pytest | **774 passed, 11 skipped** (34.12s) | 与基线完全一致，零回归 |
| catalog_check --check | **OK** | v3 双视图与 roles/DAG/validators 三方一致 |
| validate.py | 53 passed, 4 failed | 4 个失败均为无活跃完整项目时的预期行为（B0 只有建模 IR，不执行论文/实验），非回归 |

本阶段未修改 `core/knowledge/`、`core/tools/`、`core/runtime/` 下任何文件，仅产出 `research/P15/knowledge_calibration/` 文档。

---

## 8. Git 状态说明

当前工作区有大量未提交改动，累积自以下阶段：
- 方向彻底改正（16张卡 + benchmark JSON + e2e_metrics.py + schema + 97处术语替换 + 治理规范）
- P15.1 B0 accumulation（5个项目 + b0_manifests + gt.json + gate/metrics runs）
- Measurement & Failure Attribution（归因报告 + failure_attribution.json）
- Knowledge Calibration（本轮产出）

**本阶段未执行 git commit**。建议用户审查后决定提交策略（可分阶段提交或一次性提交）。

已清理的临时文件：`_audit_old_direction.py`, `_b0_check.py`, `_inspect_cards.py`, `_inspect_families.py`, `migrate_benchmark.py`, `tests/tests/`（复现的嵌套目录）。

---

## 9. 下一步建议

### 可以临时放下的判断标准

本阶段已满足以下全部条件，可临时放下知识架构校准，转去项目其他部分：

1. ✅ 研究产出完整（6-PART + 4 evidence + Architecture Gate）
2. ✅ 自洽（6 个跨研究冲突点已裁决，标签体系无内部矛盾）
3. ✅ 经 Architecture Gate 审核（28 项审核，20 PASS + 6 PASS_WITH_NOTES + 2 PENDING）
4. ✅ 有明确的实施清单（P0/P1/P2，含转换规则）
5. ✅ 不阻塞其他工作（仅产出 research 文档，未改 core）
6. ✅ 临时文件已清理
7. ✅ 非回归验证通过（pytest 774/11 + catalog_check OK）
8. ✅ 有 handoff 文档（本文件）

### 恢复时的入口

- 实施 P0：从 `04_METHOD_CARD_CANDIDATES.md` 读取 3 张 P0 卡的完整 YAML，按 §4 转换规则写入 `core/knowledge/methods/cards/`
- 审查标签体系：从 `01_TAXONOMY_AUDIT.md` 和 `02_KNOWLEDGE_MAP.md` 开始
- 验证实施效果：用更新后的卡库重跑 2024_A/2020_B/2018_A/2019_C 的 method_selection

---

## 10. 文件索引

| 文件 | 大小 | 内容 |
|---|---|---|
| `01_TAXONOMY_AUDIT.md` | 24.7KB | PART A: 四层标签决策审计（KEEP/REVISE/SPLIT/MERGE/ADD/REMOVE） |
| `02_KNOWLEDGE_MAP.md` | 22.3KB | PART B: L1→L2→L3→L4 知识图谱（25条映射路径，断链检查） |
| `03_KNOWLEDGE_UNITS.md` | 61KB | PART C: 17个新增知识单元完整定义 |
| `04_METHOD_CARD_CANDIDATES.md` | 40.8KB | PART D: 7张NEW + 3张RETRO-TAG + 1张REVISE候选卡（完整YAML） |
| `05_BENCHMARK_MAPPING.md` | 21.6KB | PART E: 5题完整映射 + 36题分布统计 + 假阳性深度确认 |
| `06_RESEARCH_GAPS.md` | 20.6KB | PART F: 证据分级（9 Tier1 + 8 Tier2 + 6 UNCERTAIN）+ 8项不能冻结的决策 |
| `ARCHITECTURE_GATE_REPORT.md` | 17.2KB | 5条标准审核，28项结果 |
| `evidence/domain_continuous_physics.md` | 69KB | 连续物理域研究（970行，32条证据） |
| `evidence/domain_discrete_optimization.md` | 68.6KB | 离散优化域研究（879行，27条证据） |
| `evidence/domain_network_game.md` | 77.4KB | 网络博弈域研究（1127行，20+条Tier1证据） |
| `evidence/taxonomy_meta_validation.md` | 75KB | 分类学元验证（1031行，36题统计，8 UNCERTAIN） |

---

*本 handoff 文档固化了 Knowledge Calibration 阶段的完整状态、转换规则和实施清单。后续实施时以本文档为入口，配合 04_METHOD_CARD_CANDIDATES.md 的完整 YAML 使用。*
