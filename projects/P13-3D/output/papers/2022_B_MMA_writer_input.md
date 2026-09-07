# 数学建模论文撰写

## 题目原文

题目 2022_B

## 匿名建模产物（Identity: X）

```json
{
  "problem_id": "2022_B",
  "problem_interpretation": "两库系统的逐期 LP 调度框架：决策变量为逐期抽水量，约束为水量守恒+水位安全边界+需求满足，多目标（缺水率/发电量）以加权和+帕累托前沿呈现，短缺按优先级分层削减，四问同源于滚动 LP。",
  "assumptions": [
    {
      "id": "A1",
      "statement": " Powell→Maid 单向输水，无逆向",
      "justification": "工程设定"
    },
    {
      "id": "A2",
      "statement": "月步长滚动，期内流量均匀",
      "justification": "离散化近似"
    },
    {
      "id": "A3",
      "statement": "发电量 ∝ 过水流量 × 水头（水头由水位决定）",
      "justification": "水电常识"
    }
  ],
  "variables": [
    {
      "id": "M_t",
      "name": "Mead 水位（第 t 期）",
      "description": "状态",
      "unit": "ft",
      "role": "state",
      "domain": "[死水位, 防洪上限]"
    },
    {
      "id": "P_t",
      "name": "Powell 水位（第 t 期）",
      "description": "状态",
      "unit": "ft",
      "role": "state",
      "domain": "[死水位, 防洪上限]"
    },
    {
      "id": "x_P,t",
      "name": "Powell 期抽水量",
      "description": "决策",
      "unit": "acre-ft",
      "role": "decision",
      "domain": "≥0"
    },
    {
      "id": "x_M,t",
      "name": "Mead 期抽水量",
      "description": "决策",
      "unit": "acre-ft",
      "role": "decision",
      "domain": "≥0"
    },
    {
      "id": "short_t",
      "name": "第 t 期短缺量",
      "description": "需求未满足部分",
      "unit": "acre-ft",
      "role": "derived",
      "domain": "≥0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "容量曲线 V(·)",
      "value_or_source": "题目附表插值",
      "unit": "acre-ft",
      "source": "data"
    },
    {
      "id": "p2",
      "name": "死水位/发电最低水位",
      "value_or_source": "工程规范（题面附表）",
      "unit": "ft",
      "source": "data"
    },
    {
      "id": "p3",
      "name": "需求 D_w, D_e",
      "value_or_source": "题面给定（Q1 固定；Q4 情景缩放）",
      "unit": "acre-ft/yr",
      "source": "data"
    },
    {
      "id": "p4",
      "name": "发电效率系数",
      "value_or_source": "水电常识值",
      "unit": "1",
      "source": "literature"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "V_P(t+1) = V_P(t) − x_P,t（含蒸发修正可选项）；V_M(t+1) = V_M(t) − x_M,t + x_P,t",
      "rationale": "两库水量守恒"
    },
    {
      "id": "C2",
      "expression": "死水位 ≤ M_t, P_t ≤ 防洪上限",
      "rationale": "水位安全边界"
    },
    {
      "id": "C3",
      "expression": "x_M,t + x_P,t + short_t = D_w + D_e（Q3 短缺放开前取 short=0）",
      "rationale": "需求平衡"
    },
    {
      "id": "C4",
      "expression": "x_P,t ≤ 输水管道通过能力",
      "rationale": "工程能力约束"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "min Σ_t short_t（缺水率）与 max Σ_t 发电量 的加权和 λ 扫描",
      "kind": "minimize",
      "rationale": "Q2 显式准则：λ 公开且做帕累托前沿"
    },
    {
      "id": "O2",
      "expression": "T_exhaust = min{t: M_t 或 P_t 触及死水位}",
      "kind": "estimand",
      "rationale": "Q1 耗尽时间"
    },
    {
      "id": "O3",
      "expression": "ΔW = Σ_t 需求缺口（无来水情景下维持需求的累积补水量）",
      "kind": "estimand",
      "rationale": "Q1 补水量"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "水位-库容",
      "equation": "V(M_t), V(P_t) 由容量曲线线性插值",
      "derivation_notes": "附表插值"
    },
    {
      "id": "M2",
      "name": "守恒滚动",
      "equation": "见 C1",
      "derivation_notes": "逐期 LP"
    },
    {
      "id": "M3",
      "name": "发电量",
      "equation": "E_t = η·ρ·g·H(M_t)·x_M,t（水头 H 由水位定）",
      "derivation_notes": "水头随水位下降而衰减——发电与水位耦合"
    },
    {
      "id": "M4",
      "name": "需求演化（Q4）",
      "equation": "D_w(t) = D_w0·(1+g)^t·(1−c)；D_e(t) = D_e0·(1−η_ren(t))·(1+g_e)^t",
      "derivation_notes": "增长率 g、节水 c、可再生占比 η_ren 为情景参数"
    }
  ],
  "candidate_models": [
    {
      "model": "逐期 LP（本模型）",
      "pros": "全局最优+帕累托前沿可参数化",
      "cons": "线性近似蒸发/水头"
    },
    {
      "model": "动态规划",
      "pros": "非线性水头处理",
      "cons": "维数灾难"
    },
    {
      "model": "NSGA-II",
      "pros": "非凸前沿",
      "cons": "无全局最优保证"
    }
  ],
  "selected_model": "逐期 LP + 加权和帕累托扫描 + 分层短缺政策",
  "selection_reason": "约束线性；加权和法透明且满足 Q2 'Explicitly state criteria' 的可审计要求；帕累托前沿给决策者完整权衡面",
  "uncertainties": [
    {
      "source": "蒸发与渗漏",
      "handling": "scenario",
      "effect": "耗尽时间下界修正"
    },
    {
      "source": "来水（降水）",
      "handling": "scenario",
      "effect": "Q1 基线为零来水、扩展情景补来水"
    },
    {
      "source": "需求增长率 g",
      "handling": "propagated",
      "effect": "Q4 等高线"
    },
    {
      "source": "可再生占比 η_ren(t)",
      "handling": "propagated",
      "effect": "Q4 发电需水下降"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "需求 D_w/D_e",
      "range": "±20%",
      "metric": "T_exhaust / ΔW"
    },
    {
      "parameter": "初始水位 M0/P0",
      "range": "±10%",
      "metric": "T_exhaust"
    },
    {
      "parameter": "λ（用水-发电权重）",
      "range": "0-1 扫描",
      "metric": "帕累托前沿"
    },
    {
      "parameter": "可再生占比 η_ren",
      "range": "初始值至 50%",
      "metric": "D_e 下降与 T_exhaust 延长"
    }
  ]
}
```

---

# 数学建模论文撰写

请根据提供的建模产物，撰写完整的数学建模论文。

## 撰写要求

1. **问题重述**：用自己的语言重新描述题目要求，明确要回答的子问题。
2. **假设**：列出建模产物中明确声明的假设，说明每个假设的合理性。
3. **符号说明**：整理建模产物中的变量和参数，用表格呈现。
4. **模型建立**：
   - 目标函数/估计量：完整写出数学表达式。
   - 约束条件：逐条列出，附物理/工程解释。
   - 机理方程：写出状态转移方程或核心方程组。
   - 模型选择理由：为什么选这个模型而非其他候选。
5. **求解方法**：描述求解思路（数值/解析/仿真），给出算法步骤。

## 格式要求

- 公式用 LaTeX（$$...$$ 或 \[...\]）
- 无实验数据处以"待实验验证"或占位符标注
- 不要编造数据或实验结果
- 中文撰写
- 标题用 `# 建模论文`

## 重要提醒

- 严格基于提供的建模产物撰写，不要自行添加产物中没有的变量、约束或假设。
- 如果产物中缺少某个子问题的模型，如实说明"该子问题的模型待补充"。
- 保持学术论文的客观、严谨风格。

