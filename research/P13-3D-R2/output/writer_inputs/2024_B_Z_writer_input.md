你是一位数学建模论文撰写专家。请根据以下信息撰写一篇完整的数学建模竞赛论文。

**题目**：生产过程中的决策问题

**问题描述**：
建立生产过程中的质量检验概率模型，分析检验成本与不合格品损失的权衡，确定最优检验策略。

**模型产物（MODEL_ARTIFACT）**：
以下是建模阶段产出的结构化模型信息。请严格基于此模型撰写论文，**不得修改、补充或删除模型中的任何元素**。

```json
{
  "problem_id": "2024_B",
  "assumptions": [
    {
      "id": "A1",
      "statement": "产品不合格率 p 已知或可通过历史数据估计",
      "justification": "题面设定"
    },
    {
      "id": "A2",
      "statement": "检验为破坏性或非破坏性均可，但有单位成本",
      "justification": "题面设定"
    },
    {
      "id": "A3",
      "statement": "不合格品流出造成客户损失 c_def >> c_ins",
      "justification": "质量惩罚"
    },
    {
      "id": "A4",
      "statement": "批次内产品独立同分布",
      "justification": "随机抽样假设"
    }
  ],
  "variables": [
    {
      "id": "n",
      "name": "抽样量",
      "description": "每批检验数量",
      "unit": "件",
      "role": "decision",
      "domain": "n ≥ 0"
    },
    {
      "id": "p",
      "name": "不合格品率",
      "description": "批次不合格率",
      "unit": "1",
      "role": "input",
      "domain": "[0,1]"
    },
    {
      "id": "C_total",
      "name": "总成本",
      "description": "检验成本+不合格损失",
      "unit": "yuan",
      "role": "derived",
      "domain": "C_total ≥ 0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "单件检验成本 c_ins",
      "value_or_source": "题目给定",
      "unit": "yuan/件",
      "source": "data"
    },
    {
      "id": "p2",
      "name": "不合格品流出损失 c_def",
      "value_or_source": "题目给定",
      "unit": "yuan/件",
      "source": "data"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "0 ≤ n ≤ N（批次总量）",
      "rationale": "检验量不超过批次"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "min E[C_total] = c_ins·n + c_def·P(漏检)·(N-n)",
      "kind": "minimize",
      "rationale": "总期望成本最小"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "漏检概率",
      "equation": "P(miss) = (1-p)^n ≈ e^{-np}（大批次）",
      "derivation_notes": "二项分布/泊松近似"
    },
    {
      "id": "M2",
      "name": "总期望成本",
      "equation": "E[C] = c_ins·n + c_def·P(miss)·(N-n)",
      "derivation_notes": "检验成本+期望损失"
    },
    {
      "id": "M3",
      "name": "最优检验量",
      "equation": "n* = argmin E[C]，一阶条件: c_ins = c_def·(N-n)·(-∂P(miss)/∂n)",
      "derivation_notes": "边际成本=边际收益"
    }
  ],
  "candidate_models": [
    {
      "model": "二项抽样模型",
      "pros": "简单",
      "cons": "假设放回抽样"
    },
    {
      "model": "超几何抽样模型",
      "pros": "精确",
      "cons": "计算复杂"
    }
  ],
  "selected_model": "二项抽样模型",
  "selection_reason": "批次大时二项近似足够",
  "uncertainties": [],
  "sensitivity_plan": [],
  "problem_interpretation": "生产质量检验的成本-风险权衡优化问题。需要回答：(1)质量检验的概率模型；(2)检验成本与不合格品损失的权衡；(3)最优检验频率和抽样方案；(4)不同质量水平下的最优策略。成功标准：最优策略显著降低总期望成本。"
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