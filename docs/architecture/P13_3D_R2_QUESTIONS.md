# P13-3D-R2 Transmission Benchmark — 选题锁定

**日期**：2026-09-07
**状态**：Locked（仅题目 + Profile，不生成 Artifact）

---

## 1. 选题标准

| 条件 | 说明 |
|---|---|
| **C1: 未进入 P13-3B/C/R5** | 不在 2024_A / 2021_C / 2022_B 之中 |
| **C2: 题面与数据完整可访问** | 公开赛题，可从 CUMCM 官方获取 |
| **C3: 可生成完整 MODEL_ARTIFACT v1** | 题目足够复杂，能产出 variables/objective/constraints/mechanism 等完整字段 |
| **C4: 题型异质性** | 不是同一种经典模型换皮 |

---

## 2. 选题结果：8 题 × 4 Regime

| # | 题目 | Regime | 难度 | 核心方法 |
|---|---|---|---|---|
| Q1 | 2019_A 高压油管的压力控制 | Mechanism | 难 | ODE + 数值求解 + 参数寻优 |
| Q2 | 2022_A 波浪能最大输出功率设计 | Mechanism | 难 | 振动力学 + 数值求解 + 参数优化 |
| Q3 | 2017_B "拍照赚钱"的任务定价 | Data | 中 | 回归 + 分类 + 定价优化 |
| Q4 | 2022_C 古代玻璃制品的成分分析与鉴别 | Data | 中 | 聚类 + 判别 + PCA |
| Q5 | 2020_B 穿越沙漠 | Optimization | 难 | 动态规划 / MDP + 博弈 + 蒙特卡洛 |
| Q6 | 2024_B 生产过程中的决策问题 | Optimization | 中 | 概率决策 + 优化 + 灵敏度 |
| Q7 | 2023_C 蔬菜类商品的自动定价与补货决策 | Hybrid | 中 | 预测 + 优化 + 灵敏度（Data→Opt） |
| Q8 | 2024_C 农作物的种植策略 | Hybrid | 中 | 线性/整数规划 + 多目标权衡 |

---

## 3. 各题 Difficulty Profile

### Q1: 2019_A 高压油管的压力控制（Mechanism）

```json
{
  "problem_id": "2019_A",
  "regime": "Mechanism",
  "difficulty": "hard",
  "subproblem_count": 4,
  "data_dependency": "provided_numerical",
  "model_family": "ODE_system",
  "mechanism_depth": 4,
  "optimization_depth": 3,
  "ambiguity_level": 2,
  "artifact_complexity_expected": {
    "variables": 8,
    "parameters": 6,
    "constraints": 4,
    "mechanism": 3,
    "assumptions": 5,
    "objective": 1,
    "total_elements": 27
  },
  "paper_conversion_complexity": {
    "equation_density": "high",
    "multi_stage_chain": false,
    "cross_question_dependency": false,
    "figure_demand": "medium",
    "formula_count_estimate": 12
  }
}
```

### Q2: 2022_A 波浪能最大输出功率设计（Mechanism）

```json
{
  "problem_id": "2022_A",
  "regime": "Mechanism",
  "difficulty": "hard",
  "subproblem_count": 3,
  "data_dependency": "provided_numerical",
  "model_family": "vibration_mechanics",
  "mechanism_depth": 5,
  "optimization_depth": 4,
  "ambiguity_level": 2,
  "artifact_complexity_expected": {
    "variables": 10,
    "parameters": 8,
    "constraints": 5,
    "mechanism": 4,
    "assumptions": 6,
    "objective": 1,
    "total_elements": 34
  },
  "paper_conversion_complexity": {
    "equation_density": "high",
    "multi_stage_chain": false,
    "cross_question_dependency": false,
    "figure_demand": "high",
    "formula_count_estimate": 15
  }
}
```

### Q3: 2017_B "拍照赚钱"的任务定价（Data）

```json
{
  "problem_id": "2017_B",
  "regime": "Data",
  "difficulty": "medium",
  "subproblem_count": 3,
  "data_dependency": "provided_dataset",
  "model_family": "regression_classification",
  "mechanism_depth": 2,
  "optimization_depth": 2,
  "ambiguity_level": 3,
  "artifact_complexity_expected": {
    "variables": 6,
    "parameters": 4,
    "constraints": 3,
    "mechanism": 2,
    "assumptions": 4,
    "objective": 1,
    "total_elements": 20
  },
  "paper_conversion_complexity": {
    "equation_density": "medium",
    "multi_stage_chain": false,
    "cross_question_dependency": false,
    "figure_demand": "high",
    "formula_count_estimate": 8
  }
}
```

### Q4: 2022_C 古代玻璃制品的成分分析与鉴别（Data）

```json
{
  "problem_id": "2022_C",
  "regime": "Data",
  "difficulty": "medium",
  "subproblem_count": 4,
  "data_dependency": "provided_dataset",
  "model_family": "clustering_discriminant_PCA",
  "mechanism_depth": 2,
  "optimization_depth": 1,
  "ambiguity_level": 2,
  "artifact_complexity_expected": {
    "variables": 7,
    "parameters": 3,
    "constraints": 2,
    "mechanism": 3,
    "assumptions": 4,
    "objective": 1,
    "total_elements": 20
  },
  "paper_conversion_complexity": {
    "equation_density": "medium",
    "multi_stage_chain": false,
    "cross_question_dependency": false,
    "figure_demand": "high",
    "formula_count_estimate": 10
  }
}
```

### Q5: 2020_B 穿越沙漠（Optimization）

```json
{
  "problem_id": "2020_B",
  "regime": "Optimization",
  "difficulty": "hard",
  "subproblem_count": 3,
  "data_dependency": "scenario_based",
  "model_family": "MDP_game_theory",
  "mechanism_depth": 3,
  "optimization_depth": 5,
  "ambiguity_level": 3,
  "artifact_complexity_expected": {
    "variables": 8,
    "parameters": 6,
    "constraints": 4,
    "mechanism": 3,
    "assumptions": 5,
    "objective": 1,
    "total_elements": 27
  },
  "paper_conversion_complexity": {
    "equation_density": "medium",
    "multi_stage_chain": true,
    "cross_question_dependency": true,
    "figure_demand": "medium",
    "formula_count_estimate": 12
  }
}
```

### Q6: 2024_B 生产过程中的决策问题（Optimization）

```json
{
  "problem_id": "2024_B",
  "regime": "Optimization",
  "difficulty": "medium",
  "subproblem_count": 3,
  "data_dependency": "provided_numerical",
  "model_family": "probability_decision",
  "mechanism_depth": 2,
  "optimization_depth": 3,
  "ambiguity_level": 2,
  "artifact_complexity_expected": {
    "variables": 5,
    "parameters": 4,
    "constraints": 3,
    "mechanism": 2,
    "assumptions": 4,
    "objective": 1,
    "total_elements": 19
  },
  "paper_conversion_complexity": {
    "equation_density": "medium",
    "multi_stage_chain": false,
    "cross_question_dependency": false,
    "figure_demand": "medium",
    "formula_count_estimate": 8
  }
}
```

### Q7: 2023_C 蔬菜类商品的自动定价与补货决策（Hybrid: Data→Opt）

```json
{
  "problem_id": "2023_C",
  "regime": "Hybrid",
  "difficulty": "medium",
  "subproblem_count": 4,
  "data_dependency": "provided_dataset",
  "model_family": "forecasting_optimization",
  "mechanism_depth": 3,
  "optimization_depth": 4,
  "ambiguity_level": 2,
  "artifact_complexity_expected": {
    "variables": 9,
    "parameters": 5,
    "constraints": 5,
    "mechanism": 3,
    "assumptions": 5,
    "objective": 2,
    "total_elements": 29
  },
  "paper_conversion_complexity": {
    "equation_density": "high",
    "multi_stage_chain": true,
    "cross_question_dependency": true,
    "figure_demand": "high",
    "formula_count_estimate": 14
  }
}
```

### Q8: 2024_C 农作物的种植策略（Hybrid: Planning+Multi-objective）

```json
{
  "problem_id": "2024_C",
  "regime": "Hybrid",
  "difficulty": "medium",
  "subproblem_count": 3,
  "data_dependency": "provided_numerical",
  "model_family": "integer_programming_multi_objective",
  "mechanism_depth": 2,
  "optimization_depth": 5,
  "ambiguity_level": 2,
  "artifact_complexity_expected": {
    "variables": 8,
    "parameters": 6,
    "constraints": 6,
    "mechanism": 2,
    "assumptions": 4,
    "objective": 2,
    "total_elements": 28
  },
  "paper_conversion_complexity": {
    "equation_density": "medium",
    "multi_stage_chain": true,
    "cross_question_dependency": true,
    "figure_demand": "medium",
    "formula_count_estimate": 10
  }
}
```

---

## 4. 复杂度分布

| 题目 | Regime | Artifact 元素 | 方程密度 | 多阶段 | 跨问依赖 |
|---|---|---|---|---|---|
| 2019_A | Mechanism | 27 | High | No | No |
| 2022_A | Mechanism | 34 | High | No | No |
| 2017_B | Data | 20 | Medium | No | No |
| 2022_C | Data | 20 | Medium | No | No |
| 2020_B | Optimization | 27 | Medium | Yes | Yes |
| 2024_B | Optimization | 19 | Medium | No | No |
| 2023_C | Hybrid | 29 | High | Yes | Yes |
| 2024_C | Hybrid | 28 | Medium | Yes | Yes |

**Artifact 复杂度范围**：19–34 元素（覆盖低/中/高）
**Hybrid 占比**：2/8 = 25%（满足压力测试需求）
**多阶段链条**：3/8 = 37.5%

---

## 5. 下一步（待启动）

1. **Phase 1**: 为每题 × arm（B0/MMA/B1-F）构建 MODEL_ARTIFACT v1 JSON
2. **Phase 2**: SHA256 哈希 + 冻结（G0 Input Freeze Gate）
3. **Phase 3**: 生成 8 × 3 = 24 份 Writer inputs（盲评映射）
4. **Phase 4**: 生成 24 份 papers
5. **Phase 5**: 运行 Fidelity Gate v2
6. **Phase 6**: Blind Paper Quality 评估
7. **Phase 7**: 配对分析（ΔModel/ΔPaper/TE）
8. **Phase 8**: 回答 H10/H11/H12
