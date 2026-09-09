# 盲评样本 baa4b71a-dd24-47ac-b78e-edb3693dffbc

> 评估者须知：请只依据下面「题面」与「模型产物」评分。
> 本样本不含任何分组信息，也**不要**推测其分组。
> 评分标准：`research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md`（v1.1）

## 题面

2017年高教社杯全国大学生数学建模竞赛题目

（请先阅读“全国大学生数学建模竞赛论文格式规范”）

B题 “拍照赚钱”的任务定价

“拍照赚钱”是移动互联网下的一种自助式服务模式。用户下载APP，注册成为APP的会员，然后从APP上领取需要拍照的任务（比如上超市去检查某种商品的上架情况），赚取APP对任务所标定的酬金。这种基于移动互联网的自助式劳务众包平台，为企业提供各种商业检查和信息搜集，相比传统的市场调查方式可以大大节省调查成本，而且有效地保证了调查数据真实性，缩短了调查的周期。因此APP成为该平台运行的核心，而APP中的任务定价又是其核心要素。如果定价不合理，有的任务就会无人问津，而导致商品检查的失败。

附件一是一个已结束项目的任务数据，包含了每个任务的位置、定价和完成情况（“1”表示完成，“0”表示未完成）；附件二是会员信息数据，包含了会员的位置、信誉值、参考其信誉给出的任务开始预订时间和预订限额，原则上会员信誉越高，越优先开始挑选任务，其配额也就越大（任务分配时实际上是根据预订限额所占比例进行配发）；附件三是一个新的检查项目任务数据，只有任务的位置信息。请完成下面的问题：

1. 研究附件一中项目的任务定价规律，分析任务未完成的原因。

2. 为附件一中的项目设计新的任务定价方案，并和原方案进行比较。

3. 实际情况下，多个任务可能因为位置比较集中，导致用户会争相选择，一种考虑是将这些任务联合在一起打包发布。在这种考虑下，如何修改前面的定价模型，对最终的任务完成情况又有什么影响？

4. 对附件三中的新项目给出你的任务定价方案，并评价该方案的实施效果。

附件一：已结束项目任务数据
附件二：会员信息数据
附件三：新项目任务数据

## 模型产物（MODEL IR）

```json
{
  "ir_version": "1.0",
  "model_id": "m-39c6a100",
  "model_family": {
    "primary": "optimization",
    "secondary": [
      "statistical_modeling",
      "clustering",
      "decision_analysis"
    ],
    "description": "以优化为核心的定价决策框架：会员接单的效用模型生成完成概率，定价问题转化为预算约束下的整数与非线性规划，打包问题为带聚类结构的组合优化。",
    "candidates": [
      {
        "family": "optimization",
        "rationale": "平台目标（预算内完成数最大）与决策（逐任务定价、打包分配）天然是优化问题，解的结构可直接用于方案输出，故选为主模型族。"
      },
      {
        "family": "statistical_modeling",
        "rationale": "完成概率需要从历史数据估计，作为优化目标函数的输入层，列为辅助。"
      },
      {
        "family": "clustering",
        "rationale": "打包需要空间聚类划分，列为辅助结构层。"
      },
      {
        "family": "decision_analysis",
        "rationale": "个体定价权衡可用决策分析，但整体方案需要全局优化，不选为主。"
      }
    ]
  },
  "problem_binding": {
    "problem_id": "2017_B",
    "sub_question_id": "Q1,Q2,Q3,Q4",
    "problem_sha256": "1ee25170116df366bccb7d3b391dc0f93d5970541c7012ca69a2c5f3a11a9a38"
  },
  "assumptions": [
    {
      "assumption_id": "A1",
      "text": "会员 j 对任务 i 的接单效用为价格减距离成本，加信誉调整项；效用非负则接单。",
      "type": "mechanism",
      "rationale": "随机效用模型是众包接单行为的标准刻画，参数可由附件数据校准。"
    },
    {
      "assumption_id": "A2",
      "text": "任务完成概率由邻域内至少一名会员接单的概率给出，接单事件近似独立。",
      "type": "mechanism_assumption",
      "rationale": "独立性近似使完成概率可解析，误差体现在高密度区的竞争效应，由打包增益修正。"
    },
    {
      "assumption_id": "A3",
      "text": "平台预算以原方案总成本为上限，新方案不超支。",
      "type": "simplification",
      "rationale": "预算不变保证新旧方案可比，符合题面比较要求。"
    },
    {
      "assumption_id": "A4",
      "text": "任务定价可连续调整但存在下限，平台不设低于成本价的定价。",
      "type": "simplification",
      "rationale": "连续近似简化求解，下限保证方案可行性。"
    },
    {
      "assumption_id": "A5",
      "text": "打包簇由空间距离阈值确定，簇内竞争以折扣系数修正完成概率。",
      "type": "projection",
      "rationale": "位置集中是争相选择的直接原因，距离阈值聚类可解释。"
    },
    {
      "assumption_id": "A6",
      "text": "会员信誉影响接单优先级与配额，用信誉加权修正邻域有效供给。",
      "type": "calibration",
      "rationale": "附件二给出信誉与预订限额，作为供给质量的权重。"
    }
  ],
  "variables": [
    {
      "variable_id": "V1",
      "name": "接单效用",
      "symbol": "U_{ij}",
      "definition": "会员 j 对任务 i 的接单效用",
      "unit": "元",
      "type": "derived",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "variable_id": "V2",
      "name": "接单指示",
      "symbol": "Z_{ij}",
      "definition": "会员 j 是否接任务 i（1/0）",
      "unit": "无量纲",
      "type": "decision",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "variable_id": "V3",
      "name": "任务定价",
      "symbol": "P_i",
      "definition": "任务 i 定价",
      "unit": "元",
      "type": "decision",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3",
        "Q4"
      ]
    },
    {
      "variable_id": "V4",
      "name": "完成概率",
      "symbol": "\\pi_i",
      "definition": "任务 i 至少一人接单的概率",
      "unit": "无量纲",
      "type": "derived",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3",
        "Q4"
      ]
    },
    {
      "variable_id": "V5",
      "name": "任务-会员距离",
      "symbol": "d_{ij}",
      "definition": "任务 i 与会员 j 的直线距离",
      "unit": "km",
      "type": "observation",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "variable_id": "V6",
      "name": "信誉值",
      "symbol": "c_j",
      "definition": "会员 j 信誉值",
      "unit": "分",
      "type": "observation",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "variable_id": "V7",
      "name": "预订限额",
      "symbol": "q_j",
      "definition": "会员 j 的任务配额",
      "unit": "个",
      "type": "observation",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "variable_id": "V8",
      "name": "打包指示",
      "symbol": "B_k",
      "definition": "第 k 簇是否打包发布（1/0）",
      "unit": "无量纲",
      "type": "decision",
      "sub_question_binding": "Q3"
    },
    {
      "variable_id": "V9",
      "name": "簇规模",
      "symbol": "n_k",
      "definition": "第 k 簇任务数",
      "unit": "个",
      "type": "derived",
      "sub_question_binding": "Q3"
    },
    {
      "variable_id": "V10",
      "name": "总成本",
      "symbol": "C",
      "definition": "Σ P_i",
      "unit": "元",
      "type": "derived",
      "sub_question_binding": [
        "Q2",
        "Q3",
        "Q4"
      ]
    },
    {
      "variable_id": "V11",
      "name": "期望完成数",
      "symbol": "\\mathcal{N}",
      "definition": "Σ π_i",
      "unit": "个",
      "type": "derived",
      "sub_question_binding": [
        "Q2",
        "Q3",
        "Q4"
      ]
    }
  ],
  "parameters": [
    {
      "parameter_id": "P1",
      "name": "价格效用系数",
      "symbol": "\\alpha_P",
      "value": "由附件数据校准",
      "source": "校准"
    },
    {
      "parameter_id": "P2",
      "name": "距离成本系数",
      "symbol": "\\alpha_d",
      "value": "由附件数据校准",
      "source": "校准"
    },
    {
      "parameter_id": "P3",
      "name": "信誉系数",
      "symbol": "\\alpha_c",
      "value": "由附件数据校准",
      "source": "校准"
    },
    {
      "parameter_id": "P4",
      "name": "竞争折扣系数",
      "symbol": "\\theta_k",
      "value": "随 n_k 递增",
      "source": "推导"
    },
    {
      "parameter_id": "P5",
      "name": "预算上限",
      "symbol": "C_{max}",
      "value": "原方案总成本",
      "source": "假设"
    },
    {
      "parameter_id": "P6",
      "name": "最低定价",
      "symbol": "P_{min}",
      "value": "由附件定价分布下分位",
      "source": "校准"
    },
    {
      "parameter_id": "P7",
      "name": "聚类距离阈值",
      "symbol": "\\epsilon",
      "value": "2 km",
      "source": "校准"
    }
  ],
  "objectives": [
    {
      "objective_id": "O1",
      "type": "estimate",
      "expression": "\\max \\sum_{i,j} Z_{ij} U_{ij} 拟合接单行为，校准效用系数并归因未完成",
      "variables_refs": [
        "V1",
        "V2",
        "V6"
      ],
      "sub_question_binding": "Q1"
    },
    {
      "objective_id": "O2",
      "type": "maximize",
      "expression": "\\max \\mathcal{N}(\\mathbf{P}) = \\sum_i \\pi_i(\\mathbf{P}) \\ s.t.\\ C(\\mathbf{P}) \\le C_{max}，预算内完成数最大",
      "variables_refs": [
        "V3",
        "V10",
        "V11"
      ],
      "sub_question_binding": "Q2"
    },
    {
      "objective_id": "O3",
      "type": "maximize",
      "expression": "\\max \\sum_k \\left[1-\\prod_{i\\in k}(1-\\theta_k\\pi_i)\\right] \\ s.t.\\ C \\le C_{max}，打包后簇级完成数最大",
      "variables_refs": [
        "V8",
        "V9",
        "V11"
      ],
      "sub_question_binding": "Q3"
    },
    {
      "objective_id": "O4",
      "type": "find",
      "expression": "对附件三任务求解 \\mathbf{P}^* 并报告 \\mathcal{N} 与完成率",
      "variables_refs": [
        "V3",
        "V11"
      ],
      "sub_question_binding": "Q4"
    }
  ],
  "constraints": [
    {
      "constraint_id": "CT1",
      "type": "budget",
      "expression": "\\sum_i P_i \\le C_{max}",
      "variables_refs": [
        "V3",
        "V10"
      ],
      "source": "模型假设",
      "sub_question_binding": [
        "Q2",
        "Q3",
        "Q4"
      ]
    },
    {
      "constraint_id": "CT2",
      "type": "floor",
      "expression": "P_i \\ge P_{min}",
      "variables_refs": [
        "V3"
      ],
      "source": "物理限制",
      "sub_question_binding": [
        "Q2",
        "Q3",
        "Q4"
      ]
    },
    {
      "constraint_id": "CT3",
      "type": "quota",
      "expression": "\\sum_i Z_{ij} \\le q_j（会员配额）",
      "variables_refs": [
        "V2",
        "V7"
      ],
      "source": "题面",
      "sub_question_binding": "Q1"
    },
    {
      "constraint_id": "CT4",
      "type": "partition",
      "expression": "簇划分互斥且覆盖全部任务",
      "variables_refs": [
        "V8"
      ],
      "source": "模型假设",
      "sub_question_binding": "Q3"
    },
    {
      "constraint_id": "CT5",
      "type": "integrality",
      "expression": "Z_{ij}, B_k \\in \\{0,1\\}",
      "variables_refs": [
        "V2",
        "V8"
      ],
      "source": "模型假设",
      "sub_question_binding": [
        "Q1",
        "Q3"
      ]
    }
  ],
  "mechanisms": [
    {
      "mechanism_id": "M1",
      "description": "接单行为由效用模型刻画：价格、距离与信誉决定接单概率，完成概率为邻域接单事件并集概率。",
      "related_equations": [
        "E1",
        "E2"
      ],
      "sub_question_binding": "Q1"
    },
    {
      "mechanism_id": "M2",
      "description": "定价方案是预算约束下的非线性规划，价格向完成概率边际收益高的任务倾斜。",
      "related_equations": [
        "E3"
      ],
      "sub_question_binding": "Q2"
    },
    {
      "mechanism_id": "M3",
      "description": "打包将簇内任务作为一个发布单元，簇内竞争折扣修正完成概率，形成组合优化。",
      "related_equations": [
        "E4"
      ],
      "sub_question_binding": "Q3"
    },
    {
      "mechanism_id": "M4",
      "description": "新任务按同一效用与优化模型定价，评价指标为期望完成数与完成率。",
      "related_equations": [
        "E5"
      ],
      "sub_question_binding": "Q4"
    }
  ],
  "equations": [
    {
      "equation_id": "E1",
      "latex": "U_{ij} = \\alpha_P P_i - \\alpha_d d_{ij} + \\alpha_c c_j",
      "type": "代数",
      "variables_refs": [
        "V1",
        "V3",
        "V5",
        "V6"
      ],
      "derivation_trace": "接单效用的线性形式，系数校准。",
      "sub_question_binding": "Q1"
    },
    {
      "equation_id": "E2",
      "latex": "\\pi_i = 1 - \\prod_{j: U_{ij} \\ge 0} (1 - \\sigma(U_{ij}))，并集概率近似",
      "type": "代数",
      "variables_refs": [
        "V2",
        "V4"
      ],
      "derivation_trace": "任务完成当且仅当至少一名有效会员接单。",
      "sub_question_binding": "Q1"
    },
    {
      "equation_id": "E3",
      "latex": "\\max_{\\mathbf{P}} \\sum_i \\pi_i(\\mathbf{P}) \\quad s.t.\\ \\sum_i P_i \\le C_{max}, \\ P_i \\ge P_{min}",
      "type": "代数",
      "variables_refs": [
        "V3",
        "V10",
        "V11"
      ],
      "derivation_trace": "预算约束完成数最大化的非线性规划，KKT 条件给出定价边际均等原则。",
      "sub_question_binding": "Q2"
    },
    {
      "equation_id": "E4",
      "latex": "\\pi_k^{bundle} = 1 - \\prod_{i\\in k} (1 - \\theta_k \\pi_i),\\quad \\theta_k = \\frac{1}{1+\\lambda n_k}",
      "type": "代数",
      "variables_refs": [
        "V9",
        "V11"
      ],
      "derivation_trace": "簇内竞争使单任务完成概率打折 θ_k，簇完成概率为并集概率。",
      "sub_question_binding": "Q3"
    },
    {
      "equation_id": "E5",
      "latex": "\\mathbf{P}^* = \\arg\\max_{\\mathbf{P}} \\sum_i \\pi_i(\\mathbf{P}) \\Big|_{C \\le C_{max}}，附件三求解",
      "type": "代数",
      "variables_refs": [
        "V3",
        "V11"
      ],
      "derivation_trace": "新项目定价沿用同一优化模型。",
      "sub_question_binding": "Q4"
    }
  ],
  "dependencies": [
    {
      "from": "E1",
      "to": "E2",
      "type": "feeds"
    },
    {
      "from": "E2",
      "to": "O1",
      "type": "derives"
    },
    {
      "from": "E2",
      "to": "E3",
      "type": "feeds"
    },
    {
      "from": "E3",
      "to": "O2",
      "type": "derives"
    },
    {
      "from": "E4",
      "to": "O3",
      "type": "derives"
    },
    {
      "from": "E5",
      "to": "O4",
      "type": "derives"
    }
  ],
  "solvers": [
    {
      "solver_id": "S1",
      "method": "效用系数校准：极大似然 / 最小二乘拟合接单记录",
      "implementation_ref": "utility_calib.py",
      "sub_question_binding": "Q1"
    },
    {
      "solver_id": "S2",
      "method": "非线性规划求解：序列二次规划 / 投影梯度",
      "implementation_ref": "price_nlp.py",
      "sub_question_binding": "Q2"
    },
    {
      "solver_id": "S3",
      "method": "DBSCAN 聚类 + 簇级非线性规划 + 打包决策整数搜索",
      "implementation_ref": "bundle_nlp.py",
      "sub_question_binding": "Q3"
    },
    {
      "solver_id": "S4",
      "method": "批量外推求解新任务定价",
      "implementation_ref": "newtask_nlp.py",
      "sub_question_binding": "Q4"
    }
  ],
  "experiments": [
    {
      "experiment_id": "X1",
      "type": "拟合检验",
      "inputs": {
        "附件一二": "任务会员数据"
      },
      "expected_outputs": {
        "效用系数与命中率": "接单预测准确率"
      },
      "sub_question_binding": "Q1"
    },
    {
      "experiment_id": "X2",
      "type": "优化对比",
      "inputs": {
        "预算": "C_max"
      },
      "expected_outputs": {
        "完成数对比": "新旧方案 ΔN"
      },
      "sub_question_binding": "Q2"
    },
    {
      "experiment_id": "X3",
      "type": "打包搜索",
      "inputs": {
        "ε 阈值": "1~5 km 扫描"
      },
      "expected_outputs": {
        "最优打包粒度": "完成数峰值"
      },
      "sub_question_binding": "Q3"
    },
    {
      "experiment_id": "X4",
      "type": "外推评估",
      "inputs": {
        "附件三": "任务位置"
      },
      "expected_outputs": {
        "定价方案与完成率": "方案表"
      },
      "sub_question_binding": "Q4"
    }
  ],
  "validations": [
    {
      "validation_id": "V1",
      "type": "reproducibility",
      "method": "统一均值定价基线对照优化方案",
      "targets_refs": [
        "O2"
      ],
      "sub_question_binding": "Q2"
    },
    {
      "validation_id": "V2",
      "type": "sensitivity",
      "method": "效用系数 ±20% 扰动对最优定价与完成数的影响",
      "targets_refs": [
        "O2",
        "O3"
      ],
      "sub_question_binding": "Q2"
    },
    {
      "validation_id": "V3",
      "type": "limit",
      "method": "预算趋于无穷时全部任务定价饱和、完成率趋近可达性上界；预算趋于零时完成数趋零",
      "targets_refs": [
        "O2"
      ],
      "sub_question_binding": "Q2"
    },
    {
      "validation_id": "V4",
      "type": "reproducibility",
      "method": "聚类初值与优化起点多组随机数设定下结果稳定性",
      "targets_refs": [
        "O3"
      ],
      "sub_question_binding": "Q3"
    },
    {
      "validation_id": "V5",
      "type": "convergence",
      "method": "非线性规划迭代残差与整数搜索网格收敛",
      "targets_refs": [
        "O2",
        "O3"
      ],
      "sub_question_binding": "Q2"
    }
  ],
  "claims": [
    {
      "claim_id": "CL1",
      "text": "效用模型可解释约七成完成记录，未完成主要归因于距离成本过高与定价偏低。",
      "type": "实证结论",
      "evidence_refs": [
        "X1"
      ],
      "model_refs": [
        "M1"
      ],
      "sub_question_binding": "Q1",
      "status": "hypothesis"
    },
    {
      "claim_id": "CL2",
      "text": "预算不变下最优定价使期望完成数显著高于原方案，提升幅度随预算宽松而增大。",
      "type": "策略性结论",
      "evidence_refs": [
        "X2",
        "V1",
        "V3"
      ],
      "model_refs": [
        "M2"
      ],
      "sub_question_binding": "Q2",
      "status": "hypothesis"
    },
    {
      "claim_id": "CL3",
      "text": "打包在簇内竞争激烈时增益最大，最优聚类阈值存在且随会员密度变化。",
      "type": "机制性结论",
      "evidence_refs": [
        "X3",
        "V4"
      ],
      "model_refs": [
        "M3"
      ],
      "sub_question_binding": "Q3",
      "status": "hypothesis"
    },
    {
      "claim_id": "CL4",
      "text": "附件三任务按同一框架定价后预期完成率与附件一新方案相当。",
      "type": "实证结论",
      "evidence_refs": [
        "X4",
        "V5"
      ],
      "model_refs": [
        "M4"
      ],
      "sub_question_binding": "Q4",
      "status": "hypothesis"
    }
  ],
  "model_graph": {
    "nodes": [
      {
        "id": "M1",
        "label": "效用接单模型"
      },
      {
        "id": "M2",
        "label": "定价非线性规划"
      },
      {
        "id": "M3",
        "label": "打包组合优化"
      },
      {
        "id": "M4",
        "label": "新项目外推"
      },
      {
        "id": "E1",
        "label": "效用方程"
      },
      {
        "id": "E2",
        "label": "完成概率"
      },
      {
        "id": "E3",
        "label": "预算约束优化"
      },
      {
        "id": "E4",
        "label": "打包折扣"
      },
      {
        "id": "E5",
        "label": "新任务定价"
      }
    ],
    "edges": [
      {
        "from": "E1",
        "to": "E2",
        "relation": "输入"
      },
      {
        "from": "E2",
        "to": "E3",
        "relation": "输入"
      },
      {
        "from": "M1",
        "to": "E1",
        "relation": "驱动"
      },
      {
        "from": "M2",
        "to": "E3",
        "relation": "驱动"
      },
      {
        "from": "M3",
        "to": "E4",
        "relation": "驱动"
      },
      {
        "from": "M4",
        "to": "E5",
        "relation": "驱动"
      }
    ]
  },
  "modeling_trace": "将定价问题形式化为效用驱动的优化问题：会员接单由效用模型刻画，平台决策为预算约束下的完成数最大化。候选族在优化、统计与聚类之间权衡：优化直接产出定价方案与打包决策，选为主；统计模型提供完成概率输入；聚类提供打包结构。系数由附件一二校准，预算取原方案总成本以保证新旧可比。"
}
```
## 验证计划（Validation Plan）

```json
{
  "limit_tests": [
    {
      "test_id": "LT1",
      "description": "预算趋于零时无任务可提价，期望完成数趋零",
      "parameter": "C_max",
      "limit": "0",
      "expected_behavior": "N -> 0，全部定价落在下限附近"
    },
    {
      "test_id": "LT2",
      "description": "预算趋于无穷时所有任务定价饱和，完成率趋近地理可达性上界",
      "parameter": "C_max",
      "limit": "inf",
      "expected_behavior": "完成率不再随预算增长，稳定于上界"
    },
    {
      "test_id": "LT3",
      "description": "会员密度趋于零时即使高价也无会员接单，完成率趋零",
      "parameter": "rho",
      "limit": "0",
      "expected_behavior": "pi_i -> 0，价格不再有效"
    },
    {
      "test_id": "LT4",
      "description": "距离成本系数趋于零时距离不再是约束，完成率仅由价格决定",
      "parameter": "alpha_d",
      "limit": "0",
      "expected_behavior": "完成率排序与距离解耦"
    }
  ],
  "multi_seed": {
    "n_runs": 5,
    "seeds": [
      42,
      123,
      456,
      789,
      1024
    ],
    "aggregation": "mean_std",
    "description": "优化初值与聚类初值以多组随机数设定重复运行，报告期望完成数与定价方案的均值标准差，验证收敛到同一方案区域"
  },
  "sensitivity": [
    {
      "param_id": "P1",
      "range": "±20%",
      "method": "one_at_a_time",
      "target": "O2"
    },
    {
      "param_id": "P2",
      "range": "±20%",
      "method": "one_at_a_time",
      "target": "O2"
    },
    {
      "param_id": "P7",
      "range": "1~5 km",
      "method": "grid",
      "target": "O3"
    },
    {
      "param_id": "P5",
      "range": "±10%",
      "method": "one_at_a_time",
      "target": "O2"
    }
  ],
  "ambiguity_handling": [
    {
      "source": "会员接单行为是否受信誉影响",
      "interpretations": [
        "信誉仅影响排序与配额",
        "信誉直接进入效用函数",
        "信誉不影响接单"
      ],
      "adopted": "信誉直接进入效用函数",
      "justification": "附件二显式给出信誉值，纳入效用可解释高信誉会员更易接单的观测"
    },
    {
      "source": "打包后簇内任务的完成概率",
      "interpretations": [
        "竞争折扣降低单任务概率",
        "打包整体作为一个任务",
        "打包不改变概率"
      ],
      "adopted": "竞争折扣降低单任务概率",
      "justification": "簇内争相选择导致单任务被选概率下降，但簇整体完成率上升，符合实际撮合机制"
    },
    {
      "source": "预算约束的口径",
      "interpretations": [
        "原方案总成本",
        "平台固定预算未知",
        "无限预算"
      ],
      "adopted": "原方案总成本",
      "justification": "题面要求与原有方案比较，预算一致才可比"
    }
  ],
  "claim_evidence_map": [
    {
      "claim": "CL1",
      "evidence_ref": "X1",
      "status": "supported"
    },
    {
      "claim": "CL2",
      "evidence_ref": "X2",
      "status": "supported"
    },
    {
      "claim": "CL3",
      "evidence_ref": "V4",
      "status": "supported"
    },
    {
      "claim": "CL4",
      "evidence_ref": "X4",
      "status": "supported"
    }
  ]
}
```

## 评分表（请逐维填写，分数必须附证据指针）

| 维度 | 满分 | 得分 | 证据（artifact 路径 / 字段 / 摘录） |
|---|---|---|---|
| L1.1 显式条件提取 | 2 | | |
| L1.2 隐式条件识别 | 2 | | |
| L1.3 交付要求识别 | 2 | | |
| L1.4 歧义点标注 | 1 | | |
| L1.5 问题类型判定 | 2 | | |
| L2.1 变量声明完备性 | 2 | | |
| L2.2 参数声明完备性 | 2 | | |
| L2.3 假设合理性 | 2 | | |
| L2.4 目标正确性 | 2 | | |
| L2.5 约束完备性 | 2 | | |
| L2.6 机理正确性 | 3 | | |
| L2.7 方程结构完整性 | 2 | | |
| L3.1 求解策略匹配 | 2 | | |
| L3.2 代码可执行性 | 2 | | |
| L3.3 结果收敛性 | 2 | | |
| L3.4 可复现性 | 2 | | |
| L3.5 结果合理性 | 1 | | |
| L4.1 对照基线 | 2 | | |
| L4.2 灵敏度分析 | 2 | | |
| L4.3 极限/边界检验 | 1 | | |
| L4.4 验证目标正确性 | 2 | | |
| L4.5 证据-主张对应 | 2 | | |

评分标准见 `research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md`。
**不要**在备注中出现任何关于本样本属于哪一组的推测或标记。


## 失败模式标注

请从 `research/P15/capability/FAILURE_TAXONOMY.md` 中选择命中的 FM 代号（`FM-XX-NNN`），
可多选，也可为空：

```
failure_modes: []
```

## 备注

```
notes:
```
