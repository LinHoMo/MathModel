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
      "statement": "燃油近似不可压缩（体积弹性模量 E ≈ 常数）",
      "justification": "柴油/汽油 E ≈ 1.5 GPa，压力变化 <5% 时近似成立"
    },
    {
      "id": "A2",
      "statement": "管内流动为准稳态（压力波传播时间 << 喷射周期）",
      "justification": "高压油管长度短，声速 ~1400 m/s"
    },
    {
      "id": "A3",
      "statement": "喷嘴流量遵循伯努利方程，流量系数 Cd 在工作范围内近似常数",
      "justification": "喷嘴几何固定，雷诺数足够高"
    },
    {
      "id": "A4",
      "statement": "进油阀位移由凸轮型线决定，忽略阀弹簧动力学",
      "justification": "凸轮驱动 >> 弹簧力"
    },
    {
      "id": "A5",
      "statement": "温度变化可忽略（短时喷射过程）",
      "justification": "单次喷射 ms 级"
    }
  ],
  "variables": [
    {
      "id": "P",
      "name": "油管内压力",
      "description": "管内燃油压力（状态变量）",
      "unit": "MPa",
      "role": "state",
      "domain": "0 ≤ P ≤ P_max"
    },
    {
      "id": "Q_in",
      "name": "进油流量",
      "description": "通过进油阀的流量",
      "unit": "mm³/s",
      "role": "derived",
      "domain": "Q_in ≥ 0"
    },
    {
      "id": "Q_out",
      "name": "喷油流量",
      "description": "通过喷嘴的流量",
      "unit": "mm³/s",
      "role": "derived",
      "domain": "Q_out ≥ 0"
    },
    {
      "id": "x_valve",
      "name": "进油阀位移",
      "description": "凸轮驱动的阀门开度",
      "unit": "mm",
      "role": "decision",
      "domain": "0 ≤ x_valve ≤ x_max"
    },
    {
      "id": "cam_angle",
      "name": "凸轮转角",
      "description": "凸轮角度位置",
      "unit": "deg",
      "role": "input",
      "domain": "0 ≤ cam_angle ≤ 360"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "流量系数 Cd",
      "value_or_source": "待标定（Q1 目标）",
      "unit": "1",
      "source": "calibrated"
    },
    {
      "id": "p2",
      "name": "管路容积 V",
      "value_or_source": "几何给定",
      "unit": "mm³",
      "source": "data"
    },
    {
      "id": "p3",
      "name": "体积弹性模量 E",
      "value_or_source": "燃油物性 ~1.5 GPa",
      "unit": "MPa",
      "source": "literature"
    },
    {
      "id": "p4",
      "name": "供油压力 P_in",
      "value_or_source": "高压油泵输出",
      "unit": "MPa",
      "source": "data"
    },
    {
      "id": "p5",
      "name": "喷嘴面积 A_out",
      "value_or_source": "喷嘴几何",
      "unit": "mm²",
      "source": "data"
    },
    {
      "id": "p6",
      "name": "燃油密度 ρ",
      "value_or_source": "~850 kg/m³",
      "unit": "kg/m³",
      "source": "literature"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "0 ≤ x_valve ≤ x_max",
      "rationale": "阀门行程有限"
    },
    {
      "id": "C2",
      "expression": "P ≥ 0（物理非负）",
      "rationale": "压力非负"
    },
    {
      "id": "C3",
      "expression": "Q_in ≥ 0, Q_out ≥ 0",
      "rationale": "流量方向约束"
    },
    {
      "id": "C4",
      "expression": "一个喷射周期内 ∫Q_out dt = V_inject（喷油量）",
      "rationale": "喷油量约束"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "min max|P(t) - P_target|（压力波动最小化）",
      "kind": "minimize",
      "rationale": "Q3 凸轮优化目标"
    },
    {
      "id": "O2",
      "expression": "标定 Cd 使模型压力曲线与实测匹配",
      "kind": "estimand",
      "rationale": "Q1 参数标定"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "压力动态（体积弹性）",
      "equation": "dP/dt = (E/V)·(Q_in - Q_out)",
      "derivation_notes": "质量守恒+体积弹性模量定义"
    },
    {
      "id": "M2",
      "name": "进油流量",
      "equation": "Q_in = Cd·A_in(x_valve)·√(2(P_in - P)/ρ)",
      "derivation_notes": "伯努利方程，A_in 为阀门有效通流面积"
    },
    {
      "id": "M3",
      "name": "喷嘴流量",
      "equation": "Q_out = Cd·A_out·√(2P/ρ)",
      "derivation_notes": "伯努利方程"
    },
    {
      "id": "M4",
      "name": "凸轮型线",
      "equation": "x_valve = f(cam_angle)",
      "derivation_notes": "凸轮升程曲线，Q3 设计对象"
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
      "metric": "压力波动幅值、峰值压力"
    },
    {
      "parameter": "凸轮转速",
      "range": "±10%",
      "metric": "压力稳定性、喷油量一致性"
    },
    {
      "parameter": "喷嘴面积 A_out",
      "range": "±15%",
      "metric": "压力响应、喷油速率"
    }
  ],
  "problem_interpretation": "高压油管燃油喷射系统的压力控制问题。需要回答：(1)喷油嘴流量系数如何确定；(2)凸轮驱动的进油阀运动如何影响管内压力；(3)如何设计凸轮运动规律使压力波动最小；(4)不同工况下的压力稳定性。成功标准：四问均能从同一压力动态模型中读出，而非各自拼装独立说辞。"
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