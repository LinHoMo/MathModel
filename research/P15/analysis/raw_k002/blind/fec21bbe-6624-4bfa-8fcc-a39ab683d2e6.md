# 盲评样本 fec21bbe-6624-4bfa-8fcc-a39ab683d2e6

> 评估者须知：请只依据下面「题面」与「模型产物」评分。
> 本样本不含任何分组信息，也**不要**推测其分组。
> 评分标准：`research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md`（v1.1）

## 题面

2018年高教社杯全国大学生数学建模竞赛题目

（请先阅读“全国大学生数学建模竞赛论文格式规范”）

B题 智能RGV的动态调度策略

图1是一个智能加工系统的示意图，由8台计算机数控机床（Computer Number Controller，CNC）、1辆轨道式自动引导车（Rail Guide Vehicle，RGV）、1条RGV直线轨道、1条上料传送带、1条下料传送带等附属设备组成。RGV是一种无人驾驶、能在固定轨道上自由运行的智能车。它根据指令能自动控制移动方向和距离，并自带一个机械手臂、两只机械手爪和物料清洗槽，能够完成上下料及清洗物料等作业任务（参见附件1）。

图1：智能加工系统示意图

针对下面的三种具体情况：

1. 一道工序的物料加工作业情况，每台CNC安装同样的刀具，物料可以在任一台CNC上加工完成；

2. 两道工序的物料加工作业情况，每个物料的第一和第二道工序分别由两台不同的CNC依次加工完成；

3. CNC在加工过程中可能发生故障（据统计：故障的发生概率约为1%）的情况，每次故障排除（人工处理，未完成的物料报废）时间介于10~20分钟之间，故障排除后即刻加入作业序列。要求分别考虑一道工序和两道工序的物料加工作业情况。

请你们团队完成下列两项任务：

任务1：对一般问题进行研究，给出RGV动态调度模型和相应的求解算法；

任务2：利用表1中系统作业参数的3组数据分别检验模型的实用性和算法的有效性，给出RGV的调度策略和系统的作业效率，并将具体的结果分别填入附件2的EXCEL表中。

表1 智能加工系统作业参数的3组数据表（时间单位：秒）

| 系统作业参数 | 第1组 | 第2组 | 第3组 |
|---|---|---|---|
| RGV移动1个单位所需时间 | 20 | 23 | 18 |
| RGV移动2个单位所需时间 | 33 | 41 | 32 |
| RGV移动3个单位所需时间 | 46 | 59 | 46 |
| CNC加工完成一个一道工序的物料所需时间 | 560 | 580 | 545 |
| CNC加工完成一个两道工序物料的第一道工序所需时间 | 400 | 280 | 455 |
| CNC加工完成一个两道工序物料的第二道工序所需时间 | 378 | 500 | 182 |
| RGV为CNC1#，3#，5#，7#一次上下料所需时间 | 28 | 30 | 27 |
| RGV为CNC2#，4#，6#，8#一次上下料所需时间 | 31 | 35 | 32 |
| RGV完成一个物料的清洗作业所需时间 | 25 | 30 | 25 |

注：每班次连续作业8小时。

附件1：智能加工系统示意图
附件2：系统作业参数与要求填写的EXCEL结果表（3个工作表，分别对应3组数据）

## 模型产物（MODEL IR）

```json
{
  "ir_version": "1.0",
  "model_id": "m-dde3a4d4",
  "model_family": {
    "primary": "optimization",
    "secondary": [
      "simulation"
    ],
    "description": "以优先规则调度优化为核心，用离散事件仿真评估吞吐量，对一道/两道工序及故障情形给出可执行调度策略。",
    "candidates": [
      {
        "family": "optimization（优先规则调度优化）",
        "rationale": "单 RGV 多 CNC 的调度可用结构化优先规则表达，工程可执行且便于三组数据检验，选为最终模型。"
      },
      {
        "family": "simulation（纯离散事件仿真）",
        "rationale": "仅仿真不给出策略形式，作为评估工具而非决策内核，配合优化规则使用。"
      },
      {
        "family": "dynamic_programming（MDP 动态规划）",
        "rationale": "理论最优但状态空间随 8 台 CNC 与时间指数爆炸，实际不可解，排除为主求解器。"
      },
      {
        "family": "markov_decision_process",
        "rationale": "故障随机性可用 MDP 描述，但求解规模受限，仅作理论对照。"
      }
    ]
  },
  "problem_binding": {
    "problem_id": "2018_B",
    "sub_question_id": "Q1,Q2,Q3,Q4",
    "problem_sha256": "f00ef29490cc2ef0ca87d7bf17b598ecae98021e8049addfa222649bee410152"
  },
  "assumptions": [
    {
      "assumption_id": "A1",
      "text": "RGV 为单资源，任一时刻只服务一台 CNC。",
      "type": "mechanism",
      "rationale": "题面明确单台 RGV，是系统硬约束。"
    },
    {
      "assumption_id": "A2",
      "text": "上下料、清洗与移动时间恒定，取表 1 数值。",
      "type": "simplification",
      "rationale": "机械作业时间确定，秒级抖动可忽略。"
    },
    {
      "assumption_id": "A3",
      "text": "上料传送带供料无限。",
      "type": "simplification",
      "rationale": "避免缺料复杂化，高负载时高估产量约 1–2%。"
    },
    {
      "assumption_id": "A4",
      "text": "故障在每个加工周期独立同分布，概率 1%，修复时间 U(10,20) 分钟。",
      "type": "projection",
      "rationale": "按题面统计量建模随机故障。"
    },
    {
      "assumption_id": "A5",
      "text": "两道工序的 CNC 分组固定：1–4 号承担第一道，5–8 号承担第二道。",
      "type": "calibration",
      "rationale": "表 1 两道工序时间差异显著，固定分工便于排产，在 Q4 交叉检验。"
    }
  ],
  "variables": [
    {
      "variable_id": "V1",
      "name": "完成物料数",
      "symbol": "N",
      "definition": "班次内完成加工的物料总数",
      "unit": "件",
      "type": "derived",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3",
        "Q4"
      ]
    },
    {
      "variable_id": "V2",
      "name": "RGV 位置",
      "symbol": "p(t)",
      "definition": "t 时刻 RGV 所在位置（0 为传送带，1–8 为 CNC）",
      "unit": "",
      "type": "state",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "variable_id": "V3",
      "name": "调度动作",
      "symbol": "u(t)",
      "definition": "RGV 在 t 时刻的动作决策",
      "unit": "",
      "type": "decision",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "variable_id": "V4",
      "name": "CNC 状态",
      "symbol": "s_j(t)",
      "definition": "第 j 台 CNC 状态（空闲/加工/上下料/故障）",
      "unit": "",
      "type": "state",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "variable_id": "V5",
      "name": "班次产量",
      "symbol": "N_shift",
      "definition": "单班次完成的物料数",
      "unit": "件",
      "type": "derived",
      "sub_question_binding": "Q4"
    },
    {
      "variable_id": "V6",
      "name": "CNC 平均利用率",
      "symbol": "eta",
      "definition": "CNC 平均加工时间占班次比例",
      "unit": "%",
      "type": "derived",
      "sub_question_binding": "Q4"
    }
  ],
  "parameters": [
    {
      "parameter_id": "P1",
      "name": "移动 1 单位时间",
      "symbol": "t_m1",
      "value": "20/23/18",
      "source": "题目"
    },
    {
      "parameter_id": "P2",
      "name": "移动 2 单位时间",
      "symbol": "t_m2",
      "value": "33/41/32",
      "source": "题目"
    },
    {
      "parameter_id": "P3",
      "name": "移动 3 单位时间",
      "symbol": "t_m3",
      "value": "46/59/46",
      "source": "题目"
    },
    {
      "parameter_id": "P4",
      "name": "一道工序加工时间",
      "symbol": "t_p1",
      "value": "560/580/545",
      "source": "题目"
    },
    {
      "parameter_id": "P5",
      "name": "第一道工序加工时间",
      "symbol": "t_a1",
      "value": "400/280/455",
      "source": "题目"
    },
    {
      "parameter_id": "P6",
      "name": "第二道工序加工时间",
      "symbol": "t_a2",
      "value": "378/500/182",
      "source": "题目"
    },
    {
      "parameter_id": "P7",
      "name": "奇数位 CNC 上下料时间",
      "symbol": "t_lo",
      "value": "28/30/27",
      "source": "题目"
    },
    {
      "parameter_id": "P8",
      "name": "偶数位 CNC 上下料时间",
      "symbol": "t_le",
      "value": "31/35/32",
      "source": "题目"
    },
    {
      "parameter_id": "P9",
      "name": "清洗时间",
      "symbol": "t_w",
      "value": "25/30/25",
      "source": "题目"
    },
    {
      "parameter_id": "P10",
      "name": "班次时长",
      "symbol": "T_shift",
      "value": 28800,
      "source": "题目"
    },
    {
      "parameter_id": "P11",
      "name": "故障概率",
      "symbol": "p_f",
      "value": 0.01,
      "source": "题目"
    },
    {
      "parameter_id": "P12",
      "name": "修复时间",
      "symbol": "t_r",
      "value": "U(600,1200)",
      "source": "题目"
    }
  ],
  "objectives": [
    {
      "objective_id": "O1",
      "type": "maximize",
      "expression": "max N = sum_i 1[part_i completed by T_shift]",
      "variables_refs": [
        "V1"
      ],
      "sub_question_binding": "Q1"
    },
    {
      "objective_id": "O2",
      "type": "maximize",
      "expression": "max N over two-stage flow with fixed CNC groups",
      "variables_refs": [
        "V1"
      ],
      "sub_question_binding": "Q2"
    },
    {
      "objective_id": "O3",
      "type": "maximize",
      "expression": "max E[N] over failure randomness",
      "variables_refs": [
        "V1"
      ],
      "sub_question_binding": "Q3"
    },
    {
      "objective_id": "O4",
      "type": "estimate",
      "expression": "estimate N_shift and eta for 3 parameter sets via simulation",
      "variables_refs": [
        "V5",
        "V6"
      ],
      "sub_question_binding": "Q4"
    }
  ],
  "constraints": [
    {
      "constraint_id": "C1",
      "type": "single_server",
      "expression": "RGV serves exactly one CNC at any time",
      "variables_refs": [
        "V2",
        "V3"
      ],
      "source": "物理限制",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "constraint_id": "C2",
      "type": "machine_capacity",
      "expression": "each CNC processes at most one part at a time",
      "variables_refs": [
        "V4"
      ],
      "source": "物理限制",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "constraint_id": "C3",
      "type": "precedence",
      "expression": "second_op_start >= first_op_finish; ops on different CNCs",
      "variables_refs": [
        "V4"
      ],
      "source": "题面",
      "sub_question_binding": [
        "Q2",
        "Q3"
      ]
    },
    {
      "constraint_id": "C4",
      "type": "time_window",
      "expression": "all operations within [0, T_shift]",
      "variables_refs": [
        "V1"
      ],
      "source": "题面",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3",
        "Q4"
      ]
    },
    {
      "constraint_id": "C5",
      "type": "failure_downtime",
      "expression": "failed CNC unavailable for t_r, part scrapped",
      "variables_refs": [
        "V4"
      ],
      "source": "题面",
      "sub_question_binding": "Q3"
    }
  ],
  "mechanisms": [
    {
      "mechanism_id": "M1",
      "description": "单服务器多工作站排队调度：RGV 服务请求由 CNC 加工完成事件驱动，优先规则决定服务顺序。",
      "related_equations": [
        "E1"
      ],
      "sub_question_binding": [
        "Q1",
        "Q2"
      ]
    },
    {
      "mechanism_id": "M2",
      "description": "故障中断使 CNC 可用性随机化，调度需对停机鲁棒，期望产量由 Monte Carlo 估计。",
      "related_equations": [
        "E3"
      ],
      "sub_question_binding": "Q3"
    },
    {
      "mechanism_id": "M3",
      "description": "三组参数构成参考实验，验证策略在不同节拍下的普适性。",
      "related_equations": [
        "E4"
      ],
      "sub_question_binding": "Q4"
    }
  ],
  "equations": [
    {
      "equation_id": "E1",
      "latex": "t_{next} = \\min_j\\, t_j^{free} + t_{move}(|p-j|) + t_{load}(j) + t_w",
      "type": "递推",
      "variables_refs": [
        "V2",
        "V3",
        "V4"
      ],
      "derivation_trace": "事件调度：选择使 RGV 最早完成服务闭环的 CNC",
      "sub_question_binding": [
        "Q1",
        "Q2"
      ]
    },
    {
      "equation_id": "E2",
      "latex": "s_j(t+\\tau) = \\mathrm{idle} \\text{ when } \\tau = t_{p1} \\text{ (or } t_{a1}, t_{a2}) \\text{ elapses}",
      "type": "递推",
      "variables_refs": [
        "V4"
      ],
      "derivation_trace": "CNC 状态按加工时间确定性转移",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    {
      "equation_id": "E3",
      "latex": "F_j \\sim \\mathrm{Bernoulli}(0.01);\\quad t_r \\sim U(600,1200)",
      "type": "逻辑",
      "variables_refs": [
        "V4"
      ],
      "derivation_trace": "故障与修复时间的随机模型",
      "sub_question_binding": "Q3"
    },
    {
      "equation_id": "E4",
      "latex": "N = \\sum_{j=1}^{8}\\sum_{k=1}^{K_j} 1[\\text{part }(j,k) \\text{ completes by } T_{shift}]",
      "type": "代数",
      "variables_refs": [
        "V1"
      ],
      "derivation_trace": "班次产量计数",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3",
        "Q4"
      ]
    }
  ],
  "dependencies": [
    {
      "from": "E1",
      "to": "V3",
      "type": "selects_action"
    },
    {
      "from": "E2",
      "to": "E1",
      "type": "feeds_free_times"
    },
    {
      "from": "E3",
      "to": "E2",
      "type": "interrupts"
    },
    {
      "from": "E4",
      "to": "O1",
      "type": "evaluates"
    },
    {
      "from": "E4",
      "to": "O4",
      "type": "evaluates"
    }
  ],
  "solvers": [
    {
      "solver_id": "S1",
      "method": "事件驱动离散事件仿真（DES）",
      "implementation_ref": "事件队列 + 优先规则调度器，事件数 O(数百)",
      "sub_question_binding": [
        "Q1",
        "Q2",
        "Q3",
        "Q4"
      ]
    },
    {
      "solver_id": "S2",
      "method": "规则对比实验（FCFS/SPT/就近/轮询）",
      "implementation_ref": "对三组参数各跑多规则，选班产最高规则",
      "sub_question_binding": [
        "Q4"
      ]
    }
  ],
  "experiments": [
    {
      "experiment_id": "X1",
      "type": "deterministic_simulation",
      "inputs": {
        "mode": "single_op",
        "params": "group1",
        "t_end": 28800
      },
      "expected_outputs": {
        "N": "班产件数",
        "schedule": "RGV 动作时间表"
      },
      "sub_question_binding": "Q1"
    },
    {
      "experiment_id": "X2",
      "type": "deterministic_simulation",
      "inputs": {
        "mode": "two_op",
        "params": "group1",
        "t_end": 28800
      },
      "expected_outputs": {
        "N": "班产件数"
      },
      "sub_question_binding": "Q2"
    },
    {
      "experiment_id": "X3",
      "type": "monte_carlo",
      "inputs": {
        "p_f": 0.01,
        "t_r": "U(600,1200)",
        "n_seeds": 5
      },
      "expected_outputs": {
        "E[N]": "期望班产",
        "std": "标准差"
      },
      "sub_question_binding": "Q3"
    },
    {
      "experiment_id": "X4",
      "type": "cross_validation",
      "inputs": {
        "params": "3 groups",
        "modes": [
          "single_op",
          "two_op"
        ]
      },
      "expected_outputs": {
        "excel": "3 工作表结果"
      },
      "sub_question_binding": "Q4"
    }
  ],
  "validations": [
    {
      "validation_id": "V1",
      "type": "reproducibility",
      "method": "无故障理想节拍理论产量上限 vs 仿真产量",
      "targets_refs": [
        "O1",
        "O2"
      ],
      "sub_question_binding": [
        "Q1",
        "Q2"
      ]
    },
    {
      "validation_id": "V2",
      "type": "sensitivity",
      "method": "p_f 在 0–3%、t_w ±20% 变化对 N 的影响",
      "targets_refs": [
        "O3"
      ],
      "sub_question_binding": "Q3"
    },
    {
      "validation_id": "V3",
      "type": "limit",
      "method": "t_m→0 时产量趋近纯加工上限；p_f→0 与确定性一致",
      "targets_refs": [
        "O1",
        "O3"
      ],
      "sub_question_binding": [
        "Q1",
        "Q3"
      ]
    },
    {
      "validation_id": "V4",
      "type": "reproducibility",
      "method": "5 个随机种子重复 Monte Carlo，CV<3%",
      "targets_refs": [
        "O3"
      ],
      "sub_question_binding": "Q3"
    },
    {
      "validation_id": "V5",
      "type": "reproducibility",
      "method": "三组参数产量与加工时间负相关的单调性检验",
      "targets_refs": [
        "O4"
      ],
      "sub_question_binding": "Q4"
    }
  ],
  "claims": [
    {
      "claim_id": "C1",
      "text": "一道工序情形下就近优先规则可使班产接近理论上限。",
      "type": "performance_claim",
      "evidence_refs": [
        "X1",
        "V1"
      ],
      "model_refs": [
        "M1"
      ],
      "sub_question_binding": "Q1",
      "status": "hypothesis"
    },
    {
      "claim_id": "C2",
      "text": "两道工序固定分组下存在稳定高产的调度规则。",
      "type": "performance_claim",
      "evidence_refs": [
        "X2",
        "V1"
      ],
      "model_refs": [
        "M1"
      ],
      "sub_question_binding": "Q2",
      "status": "hypothesis"
    },
    {
      "claim_id": "C3",
      "text": "故障情形期望班产对 p_f 近似线性敏感，对修复时长弱敏感。",
      "type": "robustness_claim",
      "evidence_refs": [
        "X3",
        "V2",
        "V4"
      ],
      "model_refs": [
        "M2"
      ],
      "sub_question_binding": "Q3",
      "status": "hypothesis"
    },
    {
      "claim_id": "C4",
      "text": "三组参数下模型输出的产量与效率指标自洽可复现，可填入 Excel。",
      "type": "consistency_claim",
      "evidence_refs": [
        "X4",
        "V5"
      ],
      "model_refs": [
        "M3"
      ],
      "sub_question_binding": "Q4",
      "status": "hypothesis"
    }
  ],
  "model_graph": {
    "nodes": [
      {
        "id": "M1",
        "label": "优先规则调度机理"
      },
      {
        "id": "M2",
        "label": "故障随机机理"
      },
      {
        "id": "E1",
        "label": "事件调度方程"
      },
      {
        "id": "E3",
        "label": "故障模型"
      },
      {
        "id": "O1",
        "label": "Q1 产量目标"
      },
      {
        "id": "O4",
        "label": "Q4 三组检验"
      }
    ],
    "edges": [
      {
        "from": "M1",
        "to": "E1",
        "relation": "instantiates"
      },
      {
        "from": "M2",
        "to": "E3",
        "relation": "instantiates"
      },
      {
        "from": "E1",
        "to": "O1",
        "relation": "maximizes"
      },
      {
        "from": "E1",
        "to": "O4",
        "relation": "evaluates"
      }
    ]
  },
  "modeling_trace": "判定为单服务器多工作站调度问题；对比 MILP（规模爆炸）、MDP（状态爆炸）后选择优先规则 + 离散事件仿真；故障用 Bernoulli+均匀修复建模；Q1–Q3 分层建模，Q4 用三组参数交叉检验并输出 Excel 结果。"
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
