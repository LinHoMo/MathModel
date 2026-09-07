你是一位数学建模论文撰写专家。请根据以下信息撰写一篇完整的数学建模竞赛论文。

**题目**：波浪能最大输出功率设计

**问题描述**：
分析波浪能装置浮体在波浪激励下的振动特性，确定最优结构参数使输出功率最大。

**模型产物（MODEL_ARTIFACT）**：
以下是建模阶段产出的结构化模型信息。请严格基于此模型撰写论文，**不得修改、补充或删除模型中的任何元素**。

```json
{
  "problem_id": "2022_A",
  "assumptions": [
    {
      "id": "A1",
      "statement": "浮体做单自由度垂向振动",
      "justification": "简化力学模型"
    },
    {
      "id": "A2",
      "statement": "波浪激励为正弦函数",
      "justification": "规则波近似"
    }
  ],
  "variables": [
    {
      "id": "x",
      "name": "浮体位移",
      "description": "垂向振动位移",
      "unit": "m",
      "role": "state",
      "domain": "任意实数"
    },
    {
      "id": "v",
      "name": "浮体速度",
      "description": "振动速度",
      "unit": "m/s",
      "role": "derived",
      "domain": "任意实数"
    },
    {
      "id": "P_out",
      "name": "输出功率",
      "description": "瞬时电功率",
      "unit": "W",
      "role": "derived",
      "domain": "P_out ≥ 0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "浮体质量 m",
      "value_or_source": "题目给定",
      "unit": "kg",
      "source": "data"
    },
    {
      "id": "p2",
      "name": "弹簧刚度 k",
      "value_or_source": "待优化",
      "unit": "N/m",
      "source": "assumed"
    },
    {
      "id": "p3",
      "name": "阻尼系数 c",
      "value_or_source": "待优化",
      "unit": "N·s/m",
      "source": "assumed"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "k > 0, c > 0",
      "rationale": "物理可实现"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "max P_avg = (1/T)∫c·v² dt",
      "kind": "maximize",
      "rationale": "平均输出功率最大"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "振动方程",
      "equation": "m·ẍ + c·ẋ + k·x = F0·sin(ωt)",
      "derivation_notes": "牛顿第二定律"
    },
    {
      "id": "M2",
      "name": "功率输出",
      "equation": "P = c·ẋ²",
      "derivation_notes": "阻尼耗散功率"
    },
    {
      "id": "M3",
      "name": "稳态振幅",
      "equation": "A = F0 / √((k-mω²)² + (cω)²)",
      "derivation_notes": "受迫振动稳态解"
    }
  ],
  "candidate_models": [
    {
      "model": "单自由度受迫振动",
      "pros": "解析解可用",
      "cons": "忽略非线性"
    },
    {
      "model": "多自由度振动",
      "pros": "更精确",
      "cons": "参数多"
    }
  ],
  "selected_model": "单自由度受迫振动",
  "selection_reason": "波浪能装置可简化为单自由度振动系统",
  "uncertainties": [],
  "sensitivity_plan": [],
  "problem_interpretation": "波浪能装置通过浮体振动将波浪能转化为电能。建模思路：浮体受波浪激励做受迫振动，阻尼元件耗散的能量即为可提取的电能。优化目标是找到共振条件使振幅最大，同时考虑能量转换效率。"
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