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
      "statement": "总耕地面积 A 固定，可分配给多种作物",
      "justification": "题面设定"
    },
    {
      "id": "A2",
      "statement": "各作物单位面积收益 r_i 已知或可估计",
      "justification": "题面给定数据"
    },
    {
      "id": "A3",
      "statement": "作物间存在轮作约束（同一种作物不能连续种植）",
      "justification": "农业常识"
    },
    {
      "id": "A4",
      "statement": "市场需求在计划期内稳定",
      "justification": "简化假设"
    },
    {
      "id": "A5",
      "statement": "考虑收益最大化和风险最小化两个目标",
      "justification": "多目标权衡"
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
      "id": "R_total",
      "name": "总收益",
      "description": "销售收入减成本",
      "unit": "yuan",
      "role": "derived",
      "domain": "R_total ≥ 0"
    },
    {
      "id": "risk",
      "name": "收益风险",
      "description": "收益方差",
      "unit": "yuan²",
      "role": "derived",
      "domain": "risk ≥ 0"
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
      "name": "收益模型",
      "equation": "R = Σ r_i · x_i",
      "derivation_notes": "线性收益"
    },
    {
      "id": "M2",
      "name": "面积约束",
      "equation": "Σ x_i ≤ A",
      "derivation_notes": "耕地约束"
    },
    {
      "id": "M3",
      "name": "轮作约束",
      "equation": "x_i(t) + x_i(t+1) ≤ A（简化）",
      "derivation_notes": "轮作约束"
    },
    {
      "id": "M4",
      "name": "风险模型",
      "equation": "Var(R) = Σ σ_i²·x_i² + 2·Σ_{i<j} ρ_ij·σ_i·σ_j·x_i·x_j",
      "derivation_notes": "方差-协方差"
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
  "problem_interpretation": "有限耕地资源下的多作物种植策略多目标优化问题。需要回答：(1)各作物收益-成本模型；(2)耕地面积约束下的种植优化；(3)轮作约束和多目标权衡（收益、风险、可持续性）；(4)不同市场情景下的策略。成功标准：帕累托前沿清晰，策略可执行。"
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