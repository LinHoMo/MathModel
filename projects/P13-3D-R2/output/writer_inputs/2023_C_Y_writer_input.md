你是一位数学建模论文撰写专家。请根据以下信息撰写一篇完整的数学建模竞赛论文。

**题目**：蔬菜类商品的自动定价与补货决策

**问题描述**：
建立蔬菜销售预测模型和动态定价与补货联合优化模型，在保鲜约束下最小化损耗和缺货损失。

**模型产物（MODEL_ARTIFACT）**：
以下是建模阶段产出的结构化模型信息。请严格基于此模型撰写论文，**不得修改、补充或删除模型中的任何元素**。

```json
{
  "problem_id": "2023_C",
  "assumptions": [
    {
      "id": "A1",
      "statement": "蔬菜保鲜期为 T_max 天，超过则完全损耗",
      "justification": "生鲜特性"
    },
    {
      "id": "A2",
      "statement": "需求受价格影响，线性近似 D = a - b·p",
      "justification": "短期价格弹性稳定"
    },
    {
      "id": "A3",
      "statement": "每日补货一次，日末处理剩余库存",
      "justification": "实际操作"
    },
    {
      "id": "A4",
      "statement": "历史销售数据可用于需求分布估计",
      "justification": "数据驱动"
    },
    {
      "id": "A5",
      "statement": "缺货损失 = 毛利率 × 期望缺货量",
      "justification": "机会成本"
    }
  ],
  "variables": [
    {
      "id": "p_t",
      "name": "第 t 日定价",
      "description": "销售价格",
      "unit": "yuan/kg",
      "role": "decision",
      "domain": "p_t > 0"
    },
    {
      "id": "q_t",
      "name": "第 t 日补货量",
      "description": "进货量",
      "unit": "kg",
      "role": "decision",
      "domain": "q_t ≥ 0"
    },
    {
      "id": "D_t",
      "name": "第 t 日需求",
      "description": "随机需求",
      "unit": "kg",
      "role": "state",
      "domain": "D_t ≥ 0"
    },
    {
      "id": "w_t",
      "name": "第 t 日末库存",
      "description": "剩余量",
      "unit": "kg",
      "role": "state",
      "domain": "w_t ≥ 0"
    },
    {
      "id": "L_t",
      "name": "第 t 日损耗",
      "description": "过期报废量",
      "unit": "kg",
      "role": "derived",
      "domain": "L_t ≥ 0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "进货成本 c",
      "value_or_source": "题目给定",
      "unit": "yuan/kg",
      "source": "data"
    },
    {
      "id": "p2",
      "name": "需求分布参数",
      "value_or_source": "历史数据估计",
      "unit": "1",
      "source": "data"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "w ≤ 保鲜期限制",
      "rationale": "过期报废"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "max E[日利润] = p·min(q,D) - c·q - 损耗成本",
      "kind": "maximize",
      "rationale": "期望利润最大"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "需求模型",
      "equation": "D_t = max(0, a - b·p_t + ε_t), ε_t ~ N(0, σ²)",
      "derivation_notes": "带噪声的线性需求"
    },
    {
      "id": "M2",
      "name": "库存动态",
      "equation": "w_t = max(w_{t-1} + q_t - D_t, 0)",
      "derivation_notes": "库存更新"
    },
    {
      "id": "M3",
      "name": "损耗",
      "equation": "L_t = max(w_{t-1} + q_t - D_t - W_max, 0)",
      "derivation_notes": "超过保鲜容量的部分"
    },
    {
      "id": "M4",
      "name": "利润函数",
      "equation": "π_t = p_t·min(q_t + w_{t-1}, D_t) - c·q_t - h·L_t",
      "derivation_notes": "销售收益-进货成本-损耗成本"
    }
  ],
  "candidate_models": [
    {
      "model": "报童模型 + 价格优化",
      "pros": "经典框架",
      "cons": "单期"
    },
    {
      "model": "动态规划多期",
      "pros": "考虑库存积累",
      "cons": "计算复杂"
    }
  ],
  "selected_model": "报童模型 + 价格优化",
  "selection_reason": "蔬菜单日决策适用报童框架",
  "uncertainties": [],
  "sensitivity_plan": [],
  "problem_interpretation": "蔬菜类商品的动态定价与补货联合优化问题。需要回答：(1)销售量预测模型；(2)损耗率、定价和需求的关系；(3)动态定价与补货的联合优化；(4)灵敏度分析。成功标准：优化策略相比固定定价显著降低损耗率并提高利润。"
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