# 数学建模论文撰写

## 题目原文

题目 2024_A

## 匿名建模产物（Identity: X）

```json
{
  "problem_id": "2024_A",
  "problem_interpretation": "研究七鳃鳗性别比随资源可变这一能力，通过种群动力学+蒙特卡洛框架，回答对生态系统、种群自身、稳定性与寄生者的四类影响。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "有效繁殖项与雌性占比 r 成正比",
      "justification": "有性繁殖常识（建模思路隐含）"
    },
    {
      "id": "A2",
      "statement": "资源波动为外生随机情景，通过 r 与 K 双通道传导",
      "justification": "蒙特卡洛情景设定"
    },
    {
      "id": "A3",
      "statement": "寄生者增长率与七鳃鳗密度成正比（功能反应）",
      "justification": "Q4 寄生-宿主耦合设定"
    }
  ],
  "variables": [
    {
      "id": "N",
      "name": "七鳃鳗种群规模",
      "description": "状态量",
      "unit": "ind",
      "role": "state",
      "domain": "N ≥ 0"
    },
    {
      "id": "r",
      "name": "雌性占比",
      "description": "性别比，资源函数",
      "unit": "1",
      "role": "input",
      "domain": "0 ≤ r ≤ 1"
    },
    {
      "id": "R",
      "name": "资源波动",
      "description": "外生随机情景",
      "unit": "1",
      "role": "input",
      "domain": "R ≥ 0"
    },
    {
      "id": "P",
      "name": "寄生者种群",
      "description": "Q4 耦合物种",
      "unit": "ind",
      "role": "state",
      "domain": "P ≥ 0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "r_max",
      "value_or_source": "文献典型值域",
      "unit": "1/yr",
      "source": "literature"
    },
    {
      "id": "p2",
      "name": "K",
      "value_or_source": "情景设定",
      "unit": "ind",
      "source": "assumed"
    },
    {
      "id": "p3",
      "name": "寄生耦合强度",
      "value_or_source": "情景设定",
      "unit": "1",
      "source": "assumed"
    }
  ],
  "constraints": [],
  "objective": [
    {
      "id": "O1",
      "expression": "固定性别比 vs 可变性别比两组情景的种群轨迹分布对比（灭绝概率、规模方差）",
      "kind": "simulate",
      "rationale": "按各子问题输出对比结论"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "Logistic + 性别比（思路级）",
      "equation": "dN/dt = r_max·r·N·(1−N/K)，r 随资源波动",
      "derivation_notes": "思路级方程，未给显式 r(R) 函数形式"
    },
    {
      "id": "M2",
      "name": "寄生耦合（思路级）",
      "equation": "dP/dt 与 N 成正比（功能反应项思路）",
      "derivation_notes": "未给显式系数"
    }
  ],
  "candidate_models": [
    {
      "model": "Logistic + 蒙特卡洛",
      "pros": "可解释、易实现",
      "cons": "性别比机制弱"
    },
    {
      "model": "Lotka-Volterra 耦合",
      "pros": "可加寄生者",
      "cons": "无数据标定难"
    },
    {
      "model": "寄生-宿主标准型",
      "pros": "Q4 适配",
      "cons": "参数多"
    }
  ],
  "selected_model": "Logistic 种群动力学 + 蒙特卡洛（Q4 加寄生耦合）",
  "selection_reason": "七鳃鳗-生态系统交互本质是资源约束下的种群演化；蒙特卡洛处理资源不确定性；按题面无数据，参数取文献典型值域",
  "uncertainties": [
    {
      "source": "资源波动",
      "handling": "propagated",
      "effect": "蒙特卡洛轨迹分布"
    },
    {
      "source": "参数（r_max/K/耦合强度）",
      "handling": "propagated",
      "effect": "敏感性采样"
    },
    {
      "source": "性别决定机制的具体函数形式",
      "handling": "qualitative",
      "effect": "未建模具体形式"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "r_max",
      "range": "±20%",
      "metric": "灭绝概率/均衡规模"
    },
    {
      "parameter": "K",
      "range": "±20%",
      "metric": "灭绝概率/均衡规模"
    },
    {
      "parameter": "Δr（性别比响应幅度）",
      "range": "±0.1",
      "metric": "种群轨迹方差"
    },
    {
      "parameter": "寄生耦合强度",
      "range": "±20%",
      "metric": "寄生者规模"
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

