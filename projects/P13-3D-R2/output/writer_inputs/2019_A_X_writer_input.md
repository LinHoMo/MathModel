你是一位数学建模论文撰写专家。请根据以下信息撰写一篇完整的数学建模竞赛论文。

**题目**：高压油管的压力控制

**问题描述**：
分析高压油管内燃油喷射的压力变化规律，确定喷油嘴流量系数和凸轮运动规律对压力的影响。

**模型产物（MODEL_ARTIFACT）**：
以下是建模阶段产出的结构化模型信息。请严格基于此模型撰写论文，**不得修改、补充或删除模型中的任何元素**。

```json
{
  "problem_id": "2019_A",
  "assumptions": [
    {
      "id": "A1",
      "statement": "燃油不可压缩，流动为准稳态",
      "justification": "简化流体力学"
    },
    {
      "id": "A2",
      "statement": "喷嘴流量与压力平方根成正比",
      "justification": "伯努利方程"
    },
    {
      "id": "A3",
      "statement": "燃油温度恒定，密度均匀",
      "justification": "准稳态假设"
    }
  ],
  "variables": [
    {
      "id": "P",
      "name": "油管内压力",
      "description": "管内燃油压力",
      "unit": "MPa",
      "role": "state",
      "domain": "P ≥ 0"
    },
    {
      "id": "Q",
      "name": "喷油流量",
      "description": "喷嘴出口流量",
      "unit": "mm³/s",
      "role": "derived",
      "domain": "Q ≥ 0"
    },
    {
      "id": "x",
      "name": "进油阀位移",
      "description": "凸轮驱动的阀门开度",
      "unit": "mm",
      "role": "decision",
      "domain": "x ≥ 0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "流量系数 Cd",
      "value_or_source": "待标定",
      "unit": "1",
      "source": "calibrated"
    },
    {
      "id": "p2",
      "name": "管路容积 V",
      "value_or_source": "题目给定",
      "unit": "mm³",
      "source": "data"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "0 ≤ x ≤ x_max",
      "rationale": "阀门行程有限"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "最小化压力波动幅值",
      "kind": "minimize",
      "rationale": "压力稳定是喷射质量的关键"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "压力动态",
      "equation": "dP/dt = (E/V)·(Q_in - Q_out)",
      "derivation_notes": "体积弹性模量 E，管路容积 V"
    },
    {
      "id": "M2",
      "name": "进油流量",
      "equation": "Q_in = Cd·A_in·√(2(P_in-P)/ρ)",
      "derivation_notes": "进油阀流量，P_in 为供油压力"
    },
    {
      "id": "M3",
      "name": "喷嘴流量",
      "equation": "Q_out = Cd·A_out·√(2P/ρ)",
      "derivation_notes": "伯努利方程"
    }
  ],
  "candidate_models": [
    {
      "model": "ODE + 伯努利",
      "pros": "物理可解释",
      "cons": "参数少"
    },
    {
      "model": "CFD 数值模拟",
      "pros": "精度高",
      "cons": "计算成本高"
    }
  ],
  "selected_model": "ODE + 伯努利方程",
  "selection_reason": "题目要求分析压力变化规律，ODE 模型足够且可解释",
  "uncertainties": [],
  "sensitivity_plan": [
    {
      "parameter": "流量系数 Cd",
      "range": "±20%",
      "metric": "压力波动幅值"
    },
    {
      "parameter": "凸轮转速",
      "range": "±10%",
      "metric": "压力稳定性"
    }
  ],
  "problem_interpretation": "高压油管内燃油喷射的压力控制问题。通过凸轮驱动进油阀控制喷射规律，需要建立压力-流量耦合模型，分析压力波动规律并优化凸轮运动使压力稳定。建模思路：油管内压力动态由体积弹性模量与流量差决定，喷嘴流量遵循伯努利方程，凸轮位移决定进油流量。"
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