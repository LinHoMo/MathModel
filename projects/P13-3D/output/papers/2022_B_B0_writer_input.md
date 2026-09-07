# 数学建模论文撰写

## 题目原文

题目 2022_B

## 匿名建模产物（Identity: Z）

```json
{
  "problem_id": "2022_B",
  "problem_interpretation": "Mead（M）与 Powell（P）两库在固定供水/供电需求下的抽水决策：抽多少、多久耗尽、需补多少水，以及竞争利益（用水 vs 发电）的解决准则与短缺政策。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "两库水量仅通过抽水管道交换（Powell→Mead），无其他联通",
      "justification": "题面设定"
    },
    {
      "id": "A2",
      "statement": "需求（农业/工业/居民用水 + 发电用水）为固定常量",
      "justification": "题面 Q1 固定需求设定"
    },
    {
      "id": "A3",
      "statement": "无额外来水（降雨等）作为 Q1 基线情景",
      "justification": "题面 Q1 显式条件"
    }
  ],
  "variables": [
    {
      "id": "M",
      "name": "Mead 水位",
      "description": "水库水位高度",
      "unit": "ft",
      "role": "state",
      "domain": "≥0"
    },
    {
      "id": "P",
      "name": "Powell 水位",
      "description": "水库水位高度",
      "unit": "ft",
      "role": "state",
      "domain": "≥0"
    },
    {
      "id": "x_P",
      "name": "从 Powell 抽水量",
      "description": "决策变量",
      "unit": "acre-ft/yr",
      "role": "decision",
      "domain": "≥0"
    },
    {
      "id": "x_M",
      "name": "从 Mead 抽水量",
      "description": "决策变量",
      "unit": "acre-ft/yr",
      "role": "decision",
      "domain": "≥0"
    },
    {
      "id": "D_w",
      "name": "用水总需求",
      "description": "农业+工业+居民",
      "unit": "acre-ft/yr",
      "role": "input",
      "domain": ">0"
    },
    {
      "id": "D_e",
      "name": "发电需水量",
      "description": "发电所需过水量",
      "unit": "acre-ft/yr",
      "role": "input",
      "domain": ">0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "库容-水位转换系数",
      "value_or_source": "题目附表（容量曲线）",
      "unit": "acre-ft/ft",
      "source": "data"
    },
    {
      "id": "p2",
      "name": "初始水位 M0, P0",
      "value_or_source": "题面条件",
      "unit": "ft",
      "source": "data"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "x_P + x_M ≥ D_w + D_e",
      "rationale": "需求满足"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "求最小抽水代价下满足需求，并推算两库耗尽时间",
      "kind": "simulate",
      "rationale": "Q1"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "库容折算",
      "equation": "水量 V(M) 由容量曲线查得",
      "derivation_notes": "水位↔水量"
    },
    {
      "id": "M2",
      "name": "水量守恒",
      "equation": "V_P(t+1) = V_P(t) − x_P；V_M(t+1) = V_M(t) − x_M + x_P",
      "derivation_notes": "Powell 抽水入 Mead"
    }
  ],
  "candidate_models": [
    {
      "model": "线性规划 + 水量守恒",
      "pros": "简单",
      "cons": "未考虑发电水位约束"
    },
    {
      "model": "动态规划",
      "pros": "可处理时序",
      "cons": "状态维数高"
    }
  ],
  "selected_model": "线性规划 + 水量守恒",
  "selection_reason": "约束线性、目标明确，LP 足够",
  "uncertainties": [
    {
      "source": "需求变化",
      "handling": "qualitative",
      "effect": "Q4 讨论"
    },
    {
      "source": "蒸发损失",
      "handling": "ignored",
      "effect": "未建模"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "需求 D",
      "range": "±20%",
      "metric": "耗尽时间"
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

