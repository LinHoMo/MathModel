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
      "statement": "蔬菜保鲜期有限，过期报废",
      "justification": "生鲜特性"
    },
    {
      "id": "A2",
      "statement": "需求受价格影响",
      "justification": "经济学常识"
    }
  ],
  "variables": [
    {
      "id": "p",
      "name": "销售价格",
      "description": "当日定价",
      "unit": "yuan/kg",
      "role": "decision",
      "domain": "p > 0"
    },
    {
      "id": "q",
      "name": "补货量",
      "description": "当日进货量",
      "unit": "kg",
      "role": "decision",
      "domain": "q ≥ 0"
    },
    {
      "id": "D",
      "name": "实际需求",
      "description": "随机需求",
      "unit": "kg",
      "role": "state",
      "domain": "D ≥ 0"
    },
    {
      "id": "w",
      "name": "剩余库存",
      "description": "日末库存",
      "unit": "kg",
      "role": "state",
      "domain": "w ≥ 0"
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
      "equation": "D = f(p) + ε",
      "derivation_notes": "价格-需求关系"
    },
    {
      "id": "M2",
      "name": "库存动态",
      "equation": "w(t+1) = max(q(t) - D(t), 0)",
      "derivation_notes": "库存更新"
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
  "problem_interpretation": "建立蔬菜销售预测模型和动态定价与补货联合优化模型，在保鲜约束下最小化损耗和缺货损失。"
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