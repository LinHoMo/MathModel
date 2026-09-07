# 数学建模论文撰写

## 题目原文

题目 2024_A

## 匿名建模产物（Identity: Z）

```json
{
  "problem_id": "2024_A",
  "problem_interpretation": "七鳃鳗的性别决定是资源依赖型的（环境性别决定），这使种群具备一个固定性别比物种没有的自由度：资源冲击可以通过出生性比传导为种群结构变化。建模目标是把这条反馈链放进一个两性种群模型，并回答四问：生态系统冲击、种群自身得失、稳定性、寄生者能否获益。成功标准：四问各自能从同一模型的均衡/轨迹性质中读出，而非各自拼装独立说辞。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "出生性比 b(R) 是资源水平 R 的 sigmoid 函数：资源匮乏时雄性占比升高（资源依赖型性别决定），b ∈ [b_min, 1−b_min] 且 b_min > 0",
      "justification": "环境性别决定类的机制文献通例；有界化避免单性吸收态"
    },
    {
      "id": "A2",
      "statement": "繁殖瓶颈由 min(F, κM) 决定（一雄可配多雌，κ>1），而非简单 F×M",
      "justification": "七鳃鳗繁殖制度的近似；κ 使雄性稀缺的代价是渐进的"
    },
    {
      "id": "A3",
      "statement": "资源 R 服从均值回归的随机波动（自回归），并线性影响容纳量 K(R)",
      "justification": "无数据条件下取最简单随机过程，波动幅度作为情景参数"
    },
    {
      "id": "A4",
      "statement": "成年七鳃鳗是寄生者 P 的唯一宿主资源，寄生者增长率对七鳃鳗丰度有功能反应（Holling-II 型）",
      "justification": "题面 Q4 提示寄生者受益通道"
    }
  ],
  "variables": [
    {
      "id": "F",
      "name": "雌性七鳃鳗数量",
      "description": "雌性成体状态",
      "unit": "ind",
      "role": "state",
      "domain": "F ≥ 0"
    },
    {
      "id": "M",
      "name": "雄性七鳃鳗数量",
      "description": "雄性成体状态",
      "unit": "ind",
      "role": "state",
      "domain": "M ≥ 0"
    },
    {
      "id": "R",
      "name": "资源指数",
      "description": "自回归随机过程",
      "unit": "1",
      "role": "state",
      "domain": "R ≥ 0"
    },
    {
      "id": "P",
      "name": "寄生者丰度",
      "description": "以七鳃鳗为宿主的寄生种群",
      "unit": "ind",
      "role": "state",
      "domain": "P ≥ 0"
    },
    {
      "id": "b",
      "name": "出生性比（雌性比例）",
      "description": "b(R)，资源依赖",
      "unit": "1",
      "role": "derived",
      "domain": "[b_min, 1−b_min]"
    },
    {
      "id": "N",
      "name": "种群总规模",
      "description": "F + M",
      "unit": "ind",
      "role": "derived",
      "domain": "N ≥ 0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "内禀增长率 γ",
      "value_or_source": "文献典型值 0.5-1.5 /yr",
      "unit": "1/yr",
      "source": "literature"
    },
    {
      "id": "p2",
      "name": "基准容纳量 K0",
      "value_or_source": "情景设定",
      "unit": "ind",
      "source": "assumed"
    },
    {
      "id": "p3",
      "name": "性比-资源响应斜率 s",
      "value_or_source": "情景参数（机制强度）",
      "unit": "1",
      "source": "assumed"
    },
    {
      "id": "p4",
      "name": "配偶比 κ",
      "value_or_source": "文献常识 >1",
      "unit": "1",
      "source": "literature"
    },
    {
      "id": "p5",
      "name": "寄生功能反应半饱和常数 h",
      "value_or_source": "情景参数",
      "unit": "ind",
      "source": "assumed"
    },
    {
      "id": "p6",
      "name": "资源波动幅度 σ_R",
      "value_or_source": "情景参数",
      "unit": "1",
      "source": "assumed"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "b(R) ∈ [b_min, 1−b_min], b_min > 0",
      "rationale": "性比有界——排除单性吸收态（否则模型出现平凡灭绝/失控解）"
    },
    {
      "id": "C2",
      "expression": "F, M, P ≥ 0",
      "rationale": "种群量非负"
    },
    {
      "id": "C3",
      "expression": "有效繁殖瓶颈 min(F, κM) ≥ 1 才有正出生项",
      "rationale": "配偶约束：任何一侧趋零则出生趋零"
    },
    {
      "id": "C4",
      "expression": "0 < 1 − N/K(R) （密度因子）",
      "rationale": "容纳量随资源变化但密度因子为正"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "均衡 (F*, M*, P*) 及其局部稳定性（Jacobian 特征值）在「可变性比 vs 固定性比」两组下的对比",
      "kind": "simulate",
      "rationale": "Q1/Q3"
    },
    {
      "id": "O2",
      "expression": "资源波动下两性种群的灭绝概率与规模方差对比",
      "kind": "estimand",
      "rationale": "Q2 优劣势的可测表述"
    },
    {
      "id": "O3",
      "expression": "寄生者 P 的均衡丰度与方差对比（可变 vs 固定）",
      "kind": "estimand",
      "rationale": "Q4"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "出生性比的资源反馈",
      "equation": "b(R) = b_min + (1−2·b_min)·σ(s·(R−R0))，σ 为 logistic 函数",
      "derivation_notes": "资源低于基准 R0 时雄性占比升高（适应贫营养），高于时回落；s 控制机制强度"
    },
    {
      "id": "M2",
      "name": "两性状态转移",
      "equation": "dF/dt = γ·b(R)·min(F, κM)·(1−N/K(R)) − μF − ωP·F；dM/dt = γ·(1−b(R))·min(F, κM)·(1−N/K(R)) − μM − ωP·M",
      "derivation_notes": "出生按出生性比分流；ωP·F/M 为寄生导致的附加死亡（把 Q4 的耦合做进核心方程而非外挂）"
    },
    {
      "id": "M3",
      "name": "资源自回归",
      "equation": "R(t+1) = R0 + φ(R(t)−R0) + ε(t), ε~N(0, σ_R²)",
      "derivation_notes": "均值回归随机扰动，φ<1"
    },
    {
      "id": "M4",
      "name": "寄生者动态（Holling-II 功能反应）",
      "equation": "dP/dt = η·P·N/(h+N) − δP",
      "derivation_notes": "宿主丰度驱动的寄生者增长；h 为半饱和常数"
    },
    {
      "id": "M5",
      "name": "容纳量的资源调制",
      "equation": "K(R) = K0·(R/R0)",
      "derivation_notes": "资源直接影响容纳量，与 M1 的性比反馈并联构成双通道"
    }
  ],
  "candidate_models": [
    {
      "model": "单种群 Logistic + 外生性比情景",
      "pros": "最简",
      "cons": "性比无反馈、无配偶约束，Q1/Q4 只能外挂讨论"
    },
    {
      "model": "两性状态模型 + 资源反馈 + 寄生耦合（本模型）",
      "pros": "四问同源；性比有界且配偶约束保证非平凡动力学",
      "cons": "参数 6 个，无数据条件下只能情景化"
    },
    {
      "model": "进化博弈式性比适应",
      "pros": "机制更根本",
      "cons": "引入策略空间超出题目需要，无数据标定不可行"
    }
  ],
  "selected_model": "两性状态模型（M1-M5）+ 寄生耦合",
  "selection_reason": "四问共享同一组均衡/轨迹性质，避免拼装；性比有界与配偶约束排除平凡解；寄生耦合进核心方程使 Q4 可从模型内读出",
  "uncertainties": [
    {
      "source": "资源波动 σ_R、φ",
      "handling": "propagated",
      "effect": "蒙特卡洛轨迹 → 灭绝概率与方差（Q2）"
    },
    {
      "source": "性比响应强度 s",
      "handling": "scenario",
      "effect": "机制开/关与强度分档对比"
    },
    {
      "source": "寄生耦合强度 η/h",
      "handling": "scenario",
      "effect": "Q4 结论的稳健性"
    },
    {
      "source": "γ、K0 绝对水平",
      "handling": "propagated",
      "effect": "敏感性采样"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "性比响应斜率 s",
      "range": "0（机制关闭）至 2×基准",
      "metric": "灭绝概率、均衡性比与规模、寄生者方差"
    },
    {
      "parameter": "资源波动 σ_R",
      "range": "0.5×至 2×基准",
      "metric": "灭绝概率、规模方差"
    },
    {
      "parameter": "配偶比 κ",
      "range": "1 至 4",
      "metric": "雄性稀缺代价的敏感性"
    },
    {
      "parameter": "寄生耦合 η/h",
      "range": "±50%",
      "metric": "寄生者均衡与稳定性判据"
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

