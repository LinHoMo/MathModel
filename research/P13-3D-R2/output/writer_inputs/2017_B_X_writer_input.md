你是一位数学建模论文撰写专家。请根据以下信息撰写一篇完整的数学建模竞赛论文。

**题目**："拍照赚钱"的任务定价

**问题描述**：
分析'拍照赚钱'众包任务定价的影响因素，建立定价模型优化任务完成率和总收益。

**模型产物（MODEL_ARTIFACT）**：
以下是建模阶段产出的结构化模型信息。请严格基于此模型撰写论文，**不得修改、补充或删除模型中的任何元素**。

```json
{
  "problem_id": "2017_B",
  "assumptions": [
    {
      "id": "A1",
      "statement": "用户选择任务基于报酬与距离的权衡",
      "justification": "众包平台通例"
    },
    {
      "id": "A2",
      "statement": "任务完成率与价格正相关",
      "justification": "经济学常识"
    }
  ],
  "variables": [
    {
      "id": "price",
      "name": "任务价格",
      "description": "单任务报酬",
      "unit": "yuan",
      "role": "decision",
      "domain": "price > 0"
    },
    {
      "id": "completion_rate",
      "name": "任务完成率",
      "description": "完成比例",
      "unit": "1",
      "role": "derived",
      "domain": "[0,1]"
    },
    {
      "id": "distance",
      "name": "用户到任务距离",
      "description": "地理距离",
      "unit": "km",
      "role": "input",
      "domain": "distance ≥ 0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "价格敏感系数 β",
      "value_or_source": "回归估计",
      "unit": "1",
      "source": "calibrated"
    },
    {
      "id": "p2",
      "name": "距离衰减系数 α",
      "value_or_source": "回归估计",
      "unit": "1",
      "source": "calibrated"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "0 ≤ completion_rate ≤ 1",
      "rationale": "概率有界"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "max E[收益] = Σ price_i · completion_rate_i",
      "kind": "maximize",
      "rationale": "总期望收益最大"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "完成率模型",
      "equation": "P(complete) = σ(β·price - α·distance + γ·region + b)",
      "derivation_notes": "多因素 logistic 回归"
    }
  ],
  "candidate_models": [
    {
      "model": "Logistic 回归",
      "pros": "简单可解释",
      "cons": "线性决策边界"
    },
    {
      "model": "随机森林",
      "pros": "非线性",
      "cons": "黑箱"
    }
  ],
  "selected_model": "Logistic 回归",
  "selection_reason": "定价问题需要可解释模型",
  "uncertainties": [],
  "sensitivity_plan": [],
  "problem_interpretation": "众包平台'拍照赚钱'任务定价问题。建模思路：用户选择任务基于报酬-距离权衡，完成率服从 logistic 函数。优化目标是找到使总期望收益最大的定价策略，考虑区域差异和时段效应。"
}
```

**论文要求**：
1. 按照标准数学建模论文格式撰写（摘要、问题重述、模型假设、符号说明、模型建立与求解、模型评价、参考文献）
2. 所有数学公式使用 LaTeX 格式
3. 论文中的所有变量、参数、约束、机制必须与 MODEL_ARTIFACT 完全一致
4. 不得引入 MODEL_ARTIFACT 中未定义的新变量、新约束或新机制
5. 不得修改 MODEL_ARTIFACT 中已有元素的含义或表达式
6. 摘要需概括问题、模型、主要结论
7. 模型假设需列出 MODEL_ARTIFACT 中的所有假设
8. 符号说明需列出 MODEL_ARTIFACT 中的所有变量和参数
9. 模型建立需详细展开 MODEL_ARTIFACT 中的所有机制方程
10. 模型评价需讨论局限性和改进方向

**输出格式**：LaTeX 格式的完整论文