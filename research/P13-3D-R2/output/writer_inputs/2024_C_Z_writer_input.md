你是一位数学建模论文撰写专家。请根据以下信息撰写一篇完整的数学建模竞赛论文。

**题目**：农作物的种植策略

**问题描述**：
在有限耕地资源下，建立多目标优化模型制定最优种植策略，考虑收益、风险和可持续性权衡。

**模型产物（MODEL_ARTIFACT）**：
以下是建模阶段产出的结构化模型信息。请严格基于此模型撰写论文，**不得修改、补充或删除模型中的任何元素**。

```json
{
  "problem_id": "2024_C",
  "assumptions": [
    {
      "id": "A1",
      "statement": "耕地面积固定，作物间可轮作",
      "justification": "题面设定"
    },
    {
      "id": "A2",
      "statement": "市场需求和价格可预测",
      "justification": "题面给定数据"
    }
  ],
  "variables": [
    {
      "id": "x_i",
      "name": "作物 i 种植面积",
      "description": "决策变量",
      "unit": "亩",
      "role": "decision",
      "domain": "x_i ≥ 0"
    },
    {
      "id": "R",
      "name": "总收益",
      "description": "销售收入减成本",
      "unit": "yuan",
      "role": "derived",
      "domain": "R ≥ 0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "各作物单位面积收益 r_i",
      "value_or_source": "题目给定",
      "unit": "yuan/亩",
      "source": "data"
    },
    {
      "id": "p2",
      "name": "总耕地面积 A",
      "value_or_source": "题目给定",
      "unit": "亩",
      "source": "data"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "Σx_i ≤ A",
      "rationale": "耕地面积约束"
    },
    {
      "id": "C2",
      "expression": "x_i ≥ 0",
      "rationale": "非负约束"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "max R = Σ r_i · x_i",
      "kind": "maximize",
      "rationale": "总收益最大"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "收益计算",
      "equation": "R = Σ r_i · x_i",
      "derivation_notes": "线性收益"
    }
  ],
  "candidate_models": [
    {
      "model": "线性规划",
      "pros": "简单高效",
      "cons": "忽略不确定性"
    },
    {
      "model": "随机规划",
      "pros": "考虑价格波动",
      "cons": "需要分布信息"
    }
  ],
  "selected_model": "线性规划",
  "selection_reason": "基础模型适用 LP",
  "uncertainties": [],
  "sensitivity_plan": [],
  "problem_interpretation": "在有限耕地资源下，建立多目标优化模型制定最优种植策略，考虑收益、风险和可持续性权衡。"
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