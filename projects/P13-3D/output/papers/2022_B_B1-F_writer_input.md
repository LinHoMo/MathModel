# 数学建模论文撰写

## 题目原文

题目 2022_B

## 匿名建模产物（Identity: Y）

```json
{
  "problem_id": "2022_B",
  "problem_interpretation": "四问同源于一个两库随机滚动调度框架：Q1 的抽水决策/耗尽时间/补水量是框架在固定需求、零来水基线下的读数；Q2 的竞争利益准则必须显式（分层/加权）且可审计；Q3 的短缺政策是约束不可行时的规则化降级；Q4 的需求增长/可再生/节水是参数化情景在框架上的传播。成功标准：四问各自能指认到框架中的决策变量、约束或目标；所有工程边界（死水位、输水能力、蒸发）显式入模。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "Powell→Mead 单向输水，通过能力上限 Cap_pipe（工程参数，情景化）",
      "justification": "题面工程设定 + 干预②：能力上限显式入模"
    },
    {
      "id": "A2",
      "statement": "月步长；月内流量均匀；蒸发为水位与表面积的函数 E(t) = e_0·A_surf(M_t, P_t)（情景开关）",
      "justification": "离散化 + 干预②：蒸发不可静默省略"
    },
    {
      "id": "A3",
      "statement": "发电量 E_t = η·ρ·g·H(M_t)·q_t，水头 H 随水位下降而衰减；发电需水量 D_e 为保证电网基荷的过水需求",
      "justification": "水电工程常识 + 题面"
    },
    {
      "id": "A4",
      "statement": "Q1 基线：零来水、需求固定；不确定性经由来水/需求情景分支进入（见 uncertainties）",
      "justification": "题面 Q1 显式条件"
    }
  ],
  "variables": [
    {
      "id": "M_t",
      "name": "Mead 水位",
      "description": "状态",
      "unit": "ft",
      "role": "state",
      "domain": "[M_dead, M_max]"
    },
    {
      "id": "P_t",
      "name": "Powell 水位",
      "description": "状态",
      "unit": "ft",
      "role": "state",
      "domain": "[P_dead, P_max]"
    },
    {
      "id": "x_P,t",
      "name": "Powell 抽水量",
      "description": "决策",
      "unit": "acre-ft/月",
      "role": "decision",
      "domain": "[0, Cap_pipe]"
    },
    {
      "id": "x_M,t",
      "name": "Mead 抽水量",
      "description": "决策",
      "unit": "acre-ft/月",
      "role": "decision",
      "domain": "≥0"
    },
    {
      "id": "s_w,t",
      "name": "用水短缺",
      "description": "居民/工业/农业合计短缺",
      "unit": "acre-ft/月",
      "role": "derived",
      "domain": "≥0"
    },
    {
      "id": "s_e,t",
      "name": "发电短缺",
      "description": "发电过水缺口",
      "unit": "acre-ft/月",
      "role": "derived",
      "domain": "≥0"
    },
    {
      "id": "q_t",
      "name": "发电过流量",
      "description": "经过水轮机的流量",
      "unit": "acre-ft/月",
      "role": "decision",
      "domain": "≥0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "容量曲线 V_M(·), V_P(·)",
      "value_or_source": "题面附表分段线性插值",
      "unit": "acre-ft",
      "source": "data"
    },
    {
      "id": "p2",
      "name": "死水位 M_dead, P_dead 与上限 M_max, P_max",
      "value_or_source": "工程规范/题面附表",
      "unit": "ft",
      "source": "data"
    },
    {
      "id": "p3",
      "name": "需求基线 D_w0, D_e0 及增长率 g、节水率 c、可再生占比 η_ren(t)",
      "value_or_source": "题面 Q4 情景参数",
      "unit": "混合",
      "source": "assumed"
    },
    {
      "id": "p4",
      "name": "蒸发系数 e_0",
      "value_or_source": "湖泊蒸发文献典型值（情景开关）",
      "unit": "ft/月",
      "source": "literature"
    },
    {
      "id": "p5",
      "name": "输水能力 Cap_pipe",
      "value_or_source": "工程参数（情景）",
      "unit": "acre-ft/月",
      "source": "assumed"
    },
    {
      "id": "p6",
      "name": "发电效率 η 与水电转换系数",
      "value_or_source": "水电工程典型值",
      "unit": "1",
      "source": "literature"
    },
    {
      "id": "p7",
      "name": "短缺优先级序",
      "value_or_source": "水法惯例：residential > industrial > agricultural > hydropower",
      "unit": "1",
      "source": "literature"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "V_P(t+1) = V_P(t) − x_P,t − E_P(t)；V_M(t+1) = V_M(t) + x_P,t − x_M,t − E_M(t)",
      "rationale": "两库水量守恒（蒸发显式入模，可关）"
    },
    {
      "id": "C2",
      "expression": "M_dead ≤ M_t ≤ M_max；P_dead ≤ P_t ≤ P_max",
      "rationale": "死水位（不可再取）与防洪上限"
    },
    {
      "id": "C3",
      "expression": "x_M,t + s_w,t = D_w(t)；q_t + s_e,t = D_e(t)",
      "rationale": "需求平衡（短缺显式变量而非隐式缺额）"
    },
    {
      "id": "C4",
      "expression": "0 ≤ x_P,t ≤ min(Cap_pipe, V_P(t) − V_P(P_dead))",
      "rationale": "输水能力 + 不可抽取死水位以下水量（干预②：物理可行性）"
    },
    {
      "id": "C5",
      "expression": "q_t ≤ x_M,t + s_e,t 且 q_t 的水头 H(M_t) ≥ H_min_power",
      "rationale": "发电过水与最低发电水位"
    },
    {
      "id": "C6",
      "expression": "短缺分层：s_w,t 按优先级序从最低层开始累积（agricultural 先于 industrial 先于 residential），residential 短缺仅在前两层用尽后发生",
      "rationale": "Q3 政策的形式化（优先级字典序）"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "Q2 竞争利益准则（显式、可审计）：字典序 lexicographic——第一优先 residential 全满足，第二 industrial，第三 agricultural 缺口最小化，第四在剩余水中最大化发电 E_t；λ 加权作为字典序的连续化对照并给帕累托前沿",
      "kind": "lexicographic + weighted",
      "rationale": "Q2 要求 Explicitly state criteria——字典序声明即准则，帕累托前沿给权衡面"
    },
    {
      "id": "O2",
      "expression": "T_exhaust = min{t: M_t = M_dead 或 P_t = P_dead}（零来水基线）",
      "kind": "estimand",
      "rationale": "Q1 耗尽时间"
    },
    {
      "id": "O3",
      "expression": "ΔW(T) = Σ_{t≤T} (s_w,t + s_e,t) 的反解——维持零短缺所需的外部补水量",
      "kind": "estimand",
      "rationale": "Q1 补水量"
    },
    {
      "id": "O4",
      "expression": "Q4 读数：T_exhaust(g, c, η_ren) 曲面与短缺频率",
      "kind": "estimand",
      "rationale": "Q4 情景传播"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "水位-库容",
      "equation": "V_M(M_t), V_P(P_t)：附表分段线性插值",
      "derivation_notes": "p1"
    },
    {
      "id": "M2",
      "name": "两库守恒滚动（含蒸发）",
      "equation": "见 C1；E_M(t) = e_0·A_surf(M_t)",
      "derivation_notes": "蒸发与表面积（由容量曲线反推）耦合"
    },
    {
      "id": "M3",
      "name": "发电-水位耦合",
      "equation": "E_t = η·ρ·g·H(M_t)·q_t，H(M_t) = M_t − H_tail",
      "derivation_notes": "水头衰减使'多抽水'与'多发电'在低水位下冲突——Q2 竞争的数学根源"
    },
    {
      "id": "M4",
      "name": "短缺分层实现",
      "equation": "s_w,t = s_agr + s_ind + s_res，按 C6 字典序逐层累积",
      "derivation_notes": "LP 可线性化：分层短缺变量 + 优先级权重 M 大数法或分阶段 LP"
    },
    {
      "id": "M5",
      "name": "Q4 情景传播",
      "equation": "D_w(t) = D_w0(1+g)^t(1−c)；D_e(t) = D_e0(1+g_e)^t(1−η_ren(t))",
      "derivation_notes": "增长率、节水、可再生三参数独立扫描"
    }
  ],
  "candidate_models": [
    {
      "model": "分层字典序 LP + 情景滚动（本框架）",
      "pros": "准则可审计、短缺显式、工程边界全入模",
      "cons": "字典序需分阶段 LP"
    },
    {
      "model": "加权和单层 LP",
      "pros": "单次求解",
      "cons": "λ 无从取值时准则不可审计"
    },
    {
      "model": "随机动态规划（来水不确定）",
      "pros": "来水随机最优",
      "cons": "维数灾难；Q1 基线为零来水确定情景，本轮不需要"
    }
  ],
  "selected_model": "分层字典序 LP + 情景滚动（λ 加权对照）",
  "selection_reason": "Q2 明确要求显式准则——字典序比加权和更可审计；短缺必须作为显式变量才能承载 Q3；工程边界（C2/C4/C5）全入模后 Q1 的耗尽时间才是物理可达的读数",
  "uncertainties": [
    {
      "source": "蒸发 e_0",
      "handling": "scenario",
      "effect": "T_exhaust 下界修正（开关对照）"
    },
    {
      "source": "输水能力 Cap_pipe",
      "handling": "scenario",
      "effect": "抽水可行性边界"
    },
    {
      "source": "需求增长 g / 节水 c",
      "handling": "propagated",
      "effect": "T_exhaust 曲面（Q4）"
    },
    {
      "source": "可再生占比 η_ren(t)",
      "handling": "propagated",
      "effect": "发电需水下降 → T_exhaust 延长（Q4）"
    },
    {
      "source": "字典序 vs 加权和的准则选择",
      "handling": "scenario",
      "effect": "帕累托前沿对照（Q2 双准则稳健性）"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "需求增长率 g",
      "range": "−2% 至 +3%/yr",
      "metric": "T_exhaust 曲面（Q4）"
    },
    {
      "parameter": "节水率 c",
      "range": "0-30%",
      "metric": "T_exhaust 延长量"
    },
    {
      "parameter": "可再生占比 η_ren",
      "range": "初始值 → 50%",
      "metric": "D_e 下降与短缺频率"
    },
    {
      "parameter": "蒸发开关 e_0",
      "range": "0 vs 文献典型值",
      "metric": "T_exhaust 差（蒸发重要性定级）"
    },
    {
      "parameter": "输水能力 Cap_pipe",
      "range": "±50%",
      "metric": "可行域与短缺频率"
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

