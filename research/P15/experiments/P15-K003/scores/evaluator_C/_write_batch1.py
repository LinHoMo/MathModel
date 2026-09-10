# -*- coding: utf-8 -*-
"""Write batch 1 scores for evaluator C (BUNDLE_001..011)."""
import json, os

OUT = r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\experiments\P15-K003\scores\evaluator_C"

def s(score, maxv, ev):
    return {"score": score, "max": maxv, "evidence": ev}

BUNDLES = {}

BUNDLES["BUNDLE_001"] = {
  "scores": {
    "L1.1": s(1,2,"model_ir problem_binding 覆盖 Q1-Q3 但缺 Q4；extracted 条件 85%-105% (A3)、两类玻璃、风化机制，无 extracted_conditions 列表"),
    "L1.2": s(1,2,"implicit: K+ 优先淋滤 (A2) 有推导依据；缺空白=未检测/风化点采样等隐式条件"),
    "L1.3": s(1,2,"experiments expected_outputs 仅 train_accuracy>0.9 与 3 预测；未识别 亚类划分/敏感性/关联分析等交付"),
    "L1.4": s(1,1,"题面无显著歧义，未标注歧义→默认 1"),
    "L1.5": s(2,2,"statistical_modeling/逻辑回归 二分类，与数据驱动分类问题一致"),
    "L2.1": s(1,2,"V1-V8 声明且区分 observation/state/derived；但 A1 提及判别成分 BaO 未声明，代码 14 特征仅声明 3"),
    "L2.2": s(0,2,"方程 E1/E2 引用 w,b 未在 parameters 声明（仅 P1-P4），引用参数缺失率>30%"),
    "L2.3": s(2,2,"A1-A3 显式、分型、有 rationale，可检验"),
    "L2.4": s(1,2,"O1/O2 匹配 Q2/Q3；Q1 风化前成分预测与 Q4 关联无目标"),
    "L2.5": s(2,2,"C1(0≤p≤1) C2(85%≤Σ≤105%) 方向正确，覆盖题面关键约束"),
    "L2.6": s(2,3,"E1 统计分类机理正确；E2 方程-机理一致；E3 目标支撑；E4 候选对比仅 2 项且较表面"),
    "L2.7": s(1,2,"E1-E3 可求解；E1/E2 引用 w,b 未在声明集→符号不一致"),
    "L3.1": s(2,2,"梯度下降求解逻辑回归，与模型类型匹配"),
    "L3.2": s(1,2,"status=success/returncode=0；fidelity 3/15 (0.2)，多数声明变量未进 outputs（SiO2/K2O/PbO/y/p）"),
    "L3.3": s(1,2,"outputs 有限无 NaN（acc=1.0）；无残差阈值/收敛判据"),
    "L3.4": s(2,2,"code_hash 存在；random.seed(42) 固定且代码确定性"),
    "L3.5": s(1,1,"输出在合理范围（acc=1.0、概率 0/1、K2O 流失 0.3）；但基于合成数据非附件实测"),
    "L4.1": s(0,2,"validations 仅 convergence/sensitivity，无对照基线"),
    "L4.2": s(1,2,"V2 灵敏度扰动学习率（非敏感参数），未报告弹性系数；无执行证据"),
    "L4.3": s(0,1,"无极限/边界检验"),
    "L4.4": s(1,2,"验证覆盖 CL1(性能) 与 CL2(风化机制) 声明但 Q3/Q4 主张未验证"),
    "L4.5": s(1,2,"CL1/CL2 有 evidence_refs 且 status=supported；但风化主张证据 E2 为预测实验，与机制主张关联弱")
  },
  "notes": "合成数据替代附件数据；Q4 完全未建模；fidelity 0.2 显示输出-声明失配",
  "layer_totals": {"L1": 6, "L2": 9, "L3": 7, "L4": 3},
  "layer_pass": {"L1": False, "L2": False, "L3": True, "L4": False},
  "overall_pass": False
}

BUNDLES["BUNDLE_002"] = {
  "scores": {
    "L1.1": s(1,2,"Q1 参数全提取（75°C/6mm/5mm/5400s/37°C）；Q2/Q3 具体值(65°C/5.5mm/80°C/30/60min)未入 parameters"),
    "L1.2": s(2,2,"A1 一维简化、A2 对流边界+体温37°C、A3 物性恒定，初始/边界条件有推导依据"),
    "L1.3": s(1,2,"识别计算温度分布/皮肤温度，但未识别 Q1 交付 problem1.xlsx 与 6 位精度要求"),
    "L1.4": s(1,1,"题面无显著歧义，未标注→默认 1"),
    "L1.5": s(2,2,"numerical_pde/热传导 判定正确"),
    "L2.1": s(2,2,"v_T/v_Ts/v_t/v_x 声明且区分 field/output/independent，含 value_range"),
    "L2.2": s(0,2,"EQ1 引用 ρ_i,c_i,k_i，EQ2 引用 h,k,T_body；仅 k1/k2/h 声明，ρ/c/k3/k4/T_body 缺失>30%"),
    "L2.3": s(2,2,"A1-A3 显式、分型(projection/mechanism/simplification)、合理可检验"),
    "L2.4": s(1,2,"OBJ1 覆盖 Q1；Q2/Q3 厚度优化目标未声明（仅在约束中体现）"),
    "L2.5": s(2,2,"C1(T≤47°C) C2(>44°C≤5min) 形式化且方向正确"),
    "L2.6": s(2,3,"E1 热传导机理正确；E2 方程-机理一致；E3 目标/约束支撑；E4 无候选对比"),
    "L2.7": s(1,2,"EQ1+EQ2 完整但缺初始条件方程；EQ1 引用 ρ/c 未声明→符号不一致"),
    "L3.1": s(2,2,"显式 FDM 满足 CFL(dt=0.25dx²/α_max)，与 PDE 匹配"),
    "L3.2": s(1,2,"status=success；fidelity 10/11；但 Q1 要求的 problem1.xlsx 未产出"),
    "L3.3": s(1,2,"outputs 有限收敛（42.5°C 平滑曲线）；无网格收敛检验证据"),
    "L3.4": s(2,2,"code_hash 存在；代码完全确定性（无随机）"),
    "L3.5": s(1,1,"42.5°C 在 37-80 合理区间，量级正确"),
    "L4.1": s(0,2,"validation_plan 无对照基线（仅 limit_tests/sensitivity）"),
    "L4.2": s(1,2,"plan.sensitivity 扰动 II 厚度/环境温度（敏感参数）但无弹性系数/边界结果"),
    "L4.3": s(1,1,"plan.limit_tests 含 2 类极限检验（零厚度 II 层、环境=体温）"),
    "L4.4": s(2,2,"validation_targets=OBJ1 覆盖核心主张 CL1；constraint_violation_check/residual_check=true"),
    "L4.5": s(2,2,"CL1 evidence_refs=[E1,V1] 可解析，无 unresolved")
  },
  "notes": "模型物理正确但 IR 参数声明不完整；L2 总分 10/15 差 0.5 未达阈值",
  "layer_totals": {"L1": 7, "L2": 10, "L3": 7, "L4": 6},
  "layer_pass": {"L1": True, "L2": False, "L3": True, "L4": False},
  "overall_pass": False
}

BUNDLES["BUNDLE_003"] = {
  "scores": {
    "L1.1": s(1,2,"提取 20平台/13要道/3分钟/60km/h；缺 增加2-5平台、六区A-F、P点(32节点)"),
    "L1.2": s(1,2,"A2 推导 3km 覆盖半径；A3 每节点设平台与题面矛盾（平台为子集）"),
    "L1.3": s(1,2,"识别管辖/封锁输出；缺 平台增设方案/全市合理性/围堵方案交付"),
    "L1.4": s(1,1,"'尽量3分钟'软约束未作歧义处理→默认 1"),
    "L1.5": s(2,2,"graph_algorithm/优化 判定正确"),
    "L2.1": s(2,2,"v_cov/v_resp/v_cv/v_alloc/v_block 声明且区分类型"),
    "L2.2": s(1,2,"p_speed/p_resp/p_nplat/p_nexit 有来源；EQ1 引用 w(e) 边权未声明"),
    "L2.3": s(1,2,"A1/A2 合理；A3(每节点均设平台) 与题面 20 平台设置矛盾→部分不合理"),
    "L2.4": s(1,2,"OBJ1/OBJ2 匹配 Q1 前两问；增加平台/全市/围堵目标缺失"),
    "L2.5": s(1,2,"C1(3min)/C2(一平台一路口) 正确；缺 2-5 平台数约束、工作量均衡约束"),
    "L2.6": s(2,3,"E1 图论机理正确；E2 方程-机理一致；E3 目标支撑；E4 无候选对比"),
    "L2.7": s(1,2,"EQ1/EQ2 可求解；EQ1 引用 w(e) 未声明→符号不一致"),
    "L3.1": s(2,2,"Dijkstra+最近邻+贪心，与图模型匹配"),
    "L3.2": s(2,2,"status=success/returncode=0；fidelity 12/12 (1.0) 全对齐"),
    "L3.3": s(2,2,"精确算法（Dijkstra+贪心）输出有限无 NaN，收敛内在保证"),
    "L3.4": s(2,2,"code_hash 存在；代码确定性（random_seed=42 声明）"),
    "L3.5": s(0,1,"coverage=1.0/max_response=0/封锁距离全 0——合成网络每节点即平台致结果退化，对真实城区不合理"),
    "L4.1": s(0,2,"无对照基线"),
    "L4.2": s(1,2,"plan.sensitivity 扰动响应时间/平台数（敏感参数）但无执行结果/弹性系数"),
    "L4.3": s(1,1,"plan.limit_tests 含单平台系统/全连接图 2 类极限检验"),
    "L4.4": s(1,2,"validation_targets=OBJ1/OBJ2 覆盖 CL1/CL2；但题面 Q2 主张未覆盖"),
    "L4.5": s(2,2,"CL1/CL2 evidence_refs 可解析到 E1/E2/V1/V2，无 unresolved")
  },
  "notes": "合成 20 节点网络替代真实 92 节点 A 区数据，结果退化全 0；L2.6 无候选对比",
  "layer_totals": {"L1": 6, "L2": 9, "L3": 8, "L4": 5},
  "layer_pass": {"L1": False, "L2": False, "L3": True, "L4": False},
  "overall_pass": False
}

BUNDLES["BUNDLE_004"] = {
  "scores": {
    "L1.1": s(1,2,"提取规则约束(负重/消耗倍率/沙暴)；初始资金/挖矿收益用'假设'值替代附件数据，六关参数未提取"),
    "L1.2": s(2,2,"C1 负重/C2 非耗尽/C3 沙暴停留 为关键隐式条件且有来源"),
    "L1.3": s(1,2,"识别最大化收益目标；未识别 Result.xlsx 交付及六关结果填写"),
    "L1.4": s(1,1,"题面无显著歧义，未标注→默认 1"),
    "L1.5": s(2,2,"dynamic_programming/序贯决策 判定正确"),
    "L2.1": s(2,2,"v_profit/v_water/v_food/v_day/v_path 声明含 value_range 与类型"),
    "L2.2": s(0,2,"EQ1 引用 r(a)/c_w(a)/c_f(a) 未在 parameters 声明；附件实际参数(负重/资金/消耗)被假设替代"),
    "L2.3": s(2,2,"A1-A3 显式分型；5 节点简化与天气已知合理"),
    "L2.4": s(1,2,"OBJ1 最大化终资金正确；Q2/Q3(在线/多人) 未建模"),
    "L2.5": s(1,2,"C1/C2/C3 形式化正确；缺 挖矿消耗3倍/村庄购买/终点退回约束"),
    "L2.6": s(2,3,"E1 Bellman/DP 机理正确；E2 递推方程一致；E3 目标支撑；E4 无候选对比"),
    "L2.7": s(1,2,"EQ1 可求解；c_w/c_f/r 符号未声明→不一致"),
    "L3.1": s(2,2,"前向 DP 与确定性序贯决策匹配"),
    "L3.2": s(1,2,"status=success 但 outputs 退化：optimal_profit=0/arrival_day=-1/路径空，未产出任何有效策略"),
    "L3.3": s(0,2,"输出为空/退化（arrival_day=-1 超出 [0,10] 被 fidelity 标记），无收敛数值"),
    "L3.4": s(2,2,"code_hash 存在；random.seed(42) 固定，确定性"),
    "L3.5": s(0,1,"optimal_profit=0/arrival_day=-1 明显不合理（应给出有效到达策略）"),
    "L4.1": s(0,2,"validations 仅 feasibility/constraint，无基线"),
    "L4.2": s(0,2,"无灵敏度分析"),
    "L4.3": s(0,1,"无极限/边界检验"),
    "L4.4": s(1,2,"V1/V2 目标匹配 CL1（可行性/约束）但无执行证据"),
    "L4.5": s(1,2,"CL1 evidence_refs 存在但 E1 执行退化，证据不可信")
  },
  "notes": "DP 执行失败未找到可行解（n_states_explored=1），L3 关键输出缺失",
  "layer_totals": {"L1": 7, "L2": 9, "L3": 5, "L4": 2},
  "layer_pass": {"L1": True, "L2": False, "L3": False, "L4": False},
  "overall_pass": False
}

BUNDLES["BUNDLE_005"] = {
  "scores": {
    "L1.1": s(1,2,"识别附件一/二/三任务与会员信息；数据参数用合成数据替代（A2），未提取附件真实参数"),
    "L1.2": s(1,2,"A3 将信誉/预订限额归入密度（隐式条件）；缺 打包发布(Q3) 与 新项目(Q4) 隐式条件"),
    "L1.3": s(1,2,"识别 Q1/Q2 输出（概率/最优定价）；Q3/Q4 交付缺失"),
    "L1.4": s(1,1,"题面无显著歧义，未标注→默认 1"),
    "L1.5": s(2,2,"statistical_modeling/Logistic 判定正确"),
    "L2.1": s(2,2,"v_p/v_d/v_m/v_c/v_popt/v_prof 声明含类型与范围"),
    "L2.2": s(0,2,"EQ1 引用 β0-β3 回归系数未在 parameters 声明；仅 3 个训练超参数"),
    "L2.3": s(1,2,"A1 合理；A2 合成数据替代附件一（不解决真实数据问题）；A3 归并可接受"),
    "L2.4": s(1,2,"OBJ1/OBJ2 匹配 Q1/Q2；Q3/Q4 无目标"),
    "L2.5": s(1,2,"C1 定价[5,50]为自拟业务约束（题面未给）；C2 概率公理；关键约束缺失"),
    "L2.6": s(2,3,"E1 Logistic 机理正确；E2 方程一致；E3 目标支撑；E4 无候选对比"),
    "L2.7": s(1,2,"EQ1/EQ2 可求解；β 符号未声明→不一致"),
    "L3.1": s(2,2,"梯度下降+网格搜索，与模型匹配"),
    "L3.2": s(2,2,"status=success；fidelity 14/17 (0.82)；输出完整（系数/最优价/利润曲线）"),
    "L3.3": s(1,2,"loss_final=0.655 有限；无收敛阈值/曲线证据"),
    "L3.4": s(1,2,"code_hash 存在；random.seed(43) 固定但非 42"),
    "L3.5": s(1,1,"输出在合理范围；最优价 40 落在网格端点（边界伪最优）"),
    "L4.1": s(0,2,"validations 仅 accuracy/monotonicity，无基线"),
    "L4.2": s(1,2,"plan.sensitivity 扰动定价/距离（敏感参数）但结果占位未执行"),
    "L4.3": s(1,1,"plan.limit_tests 含零价格/极远任务 2 类极限检验"),
    "L4.4": s(1,2,"validation_targets=OBJ1/OBJ2 匹配 CL1/CL2；Q3/Q4 主张缺失"),
    "L4.5": s(2,2,"CL1/CL2 evidence_refs 可解析到 E1/E2（已执行）")
  },
  "notes": "合成数据替代真实附件数据是主要缺陷；L2.2 参数缺失",
  "layer_totals": {"L1": 6, "L2": 8, "L3": 7, "L4": 5},
  "layer_pass": {"L1": False, "L2": False, "L3": True, "L4": False},
  "overall_pass": False
}

BUNDLES["BUNDLE_006"] = {
  "scores": {
    "L1.1": s(1,2,"doc 覆盖规则与假设参数；六关附件参数未提取（用假设值）"),
    "L1.2": s(2,2,"约束(负重/非耗尽/沙暴) 为关键隐式条件且明确"),
    "L1.3": s(1,2,"识别最大化收益目标；未识别 Result.xlsx 交付"),
    "L1.4": s(1,1,"题面无显著歧义，未标注→默认 1"),
    "L1.5": s(2,2,"动态规划判定正确"),
    "L2.1": s(2,2,"doc 变量节完整列出 5 个变量及定义"),
    "L2.2": s(2,2,"doc 参数节含负重/资金/天数/消耗倍率/基准价格/挖矿收益/村庄倍率/退回半价，方程符号均被覆盖"),
    "L2.3": s(2,2,"假设显式分型，5 节点简化与参数取值合理声明"),
    "L2.4": s(1,2,"目标正确；仅覆盖 Q1"),
    "L2.5": s(1,2,"约束含负重/非耗尽/沙暴；缺村庄购买/挖矿倍率约束"),
    "L2.6": s(2,3,"E1-E3 满足；E4 无候选对比"),
    "L2.7": s(2,2,"递推方程+状态空间描述完整，符号在参数节可查"),
    "L3.1": s(2,2,"前向 DP 匹配"),
    "L3.2": s(1,2,"status=success 但 outputs 退化（profit=0/arrival_day=-1），未产出有效策略"),
    "L3.3": s(0,2,"输出退化空结果，无收敛数值"),
    "L3.4": s(1,2,"code_hash 存在；seed=43 非 42"),
    "L3.5": s(0,1,"profit=0/arrival_day=-1 不合理"),
    "L4.1": s(0,2,"doc 验证仅可行性/约束/收敛，无基线"),
    "L4.2": s(0,2,"无灵敏度分析"),
    "L4.3": s(0,1,"无极限检验"),
    "L4.4": s(1,2,"doc 验证目标匹配主张但无执行证据"),
    "L4.5": s(1,2,"叙述式无 claim 结构；执行失败使收敛主张不可信")
  },
  "notes": "叙述式 model_doc 参数声明完整使 L2 PASS；但执行退化致 L3 失败",
  "layer_totals": {"L1": 7, "L2": 12, "L3": 4, "L4": 2},
  "layer_pass": {"L1": True, "L2": True, "L3": False, "L4": False},
  "overall_pass": False
}

BUNDLES["BUNDLE_007"] = {
  "scores": {
    "L1.1": s(1,2,"doc 覆盖任务理解；合成数据替代附件一，未提取真实数据参数"),
    "L1.2": s(1,2,"信誉/预订限额归入密度；缺 Q3/Q4 隐式条件"),
    "L1.3": s(1,2,"识别 Q1/Q2 交付；Q3/Q4 缺失"),
    "L1.4": s(1,1,"默认 1"),
    "L1.5": s(2,2,"statistical_modeling 判定正确"),
    "L2.1": s(2,2,"doc 变量节完整列出 6 变量"),
    "L2.2": s(1,2,"doc 参数节有样本量/学习率/轮数/搜索范围；β 系数在方程中使用但未列入参数"),
    "L2.3": s(1,2,"合成数据假设（A2）不合理"),
    "L2.4": s(1,2,"OBJ1/OBJ2 正确；Q3/Q4 缺失"),
    "L2.5": s(1,2,"约束含自拟定价范围与概率公理"),
    "L2.6": s(2,3,"E1-E3 满足；E4 无候选对比"),
    "L2.7": s(1,2,"方程可求解；β 未声明"),
    "L3.1": s(2,2,"梯度下降+网格搜索匹配"),
    "L3.2": s(2,2,"status=success；输出完整（系数/最优价 40/利润曲线）"),
    "L3.3": s(1,2,"loss_final=0.681 有限；无收敛阈值证据"),
    "L3.4": s(1,2,"code_hash 存在；seed=44 非 42"),
    "L3.5": s(1,1,"输出范围合理；最优价 40 为网格端点"),
    "L4.1": s(0,2,"无基线"),
    "L4.2": s(0,2,"无灵敏度声明"),
    "L4.3": s(0,1,"无极限检验"),
    "L4.4": s(1,2,"验证节匹配 Q1/Q2 主张但无执行证据"),
    "L4.5": s(1,2,"叙述式无结构化 claim；证据为声明层")
  },
  "notes": "与 005 同模型叙述版；L4 无验证计划证据",
  "layer_totals": {"L1": 6, "L2": 9, "L3": 7, "L4": 2},
  "layer_pass": {"L1": False, "L2": False, "L3": True, "L4": False},
  "overall_pass": False
}

BUNDLES["BUNDLE_008"] = {
  "scores": {
    "L1.1": s(1,2,"P1-P7 题面参数全提取（223/3.41/2.2/0.3/0.55/1.0/4.5）；孔径5.5/孔距27.5 未提取（0.85 近似替代）"),
    "L1.2": s(2,2,"A1 刚体间距守恒、A4 碰撞判据等隐式条件识别且有依据"),
    "L1.3": s(1,2,"E1 期望 223×301 帧；未识别 result1/2/4.xlsx、6 位小数、关键时刻表格交付"),
    "L1.4": s(1,1,"validation_plan.ambiguity_handling 标注 2 处歧义（碰撞判据/速度递推）并给出采纳方案"),
    "L1.5": s(2,2,"simulation/运动学 判定正确"),
    "L2.1": s(2,2,"V1-V9 声明且区分 state/derived，覆盖 Q1-Q5 关键量"),
    "L2.2": s(1,2,"P1-P7 有来源；E1 引用 r0（初始半径）未声明；0.85 孔距折算参数未声明"),
    "L2.3": s(2,2,"A1-A4 显式分型含 rationale，可检验"),
    "L2.4": s(1,2,"O1/O2/O3/O4 覆盖 Q1/Q2/Q3/Q5；Q4 调头路径优化无目标"),
    "L2.5": s(1,2,"C1-C3 形式化正确；缺 Q4 相切约束；C1 刚体约束与'各把手位于螺线'题面几何约束冲突"),
    "L2.6": s(2,3,"E1 运动学仿真机理正确；E2/E3 一致；E4 候选对比存在但较表面"),
    "L2.7": s(1,2,"E1-E4 可求解；E1 引用 r0 未声明→符号不一致"),
    "L3.1": s(2,2,"时间步进+弧长数值积分，与仿真模型匹配"),
    "L3.2": s(1,2,"status=success；但仅输出头尾位置+关键帧，Q1 需 223×301 帧未产出；Q4 未实现；xlsx 未生成"),
    "L3.3": s(1,2,"outputs 有限无 NaN；无网格收敛检验执行证据"),
    "L3.4": s(1,2,"code_hash 存在；seed=43 非 42；plan.multi_seed 为占位未执行"),
    "L3.5": s(0,1,"tail 位置 ±350~415m 远超螺线半径(~56m)，物理不合理；collision=false 由粗糙抽样(步长10)造成"),
    "L4.1": s(0,2,"无对照基线"),
    "L4.2": s(1,2,"plan.sensitivity pitch±10%/v0±20%（敏感参数）但结果为占位"),
    "L4.3": s(1,1,"plan.limit_tests pitch→0/N=1 两类极限检验"),
    "L4.4": s(1,2,"validation_targets 覆盖 O1/O3（Q1/Q3）；Q2 碰撞/ Q4/Q5 主张未验证"),
    "L4.5": s(1,2,"CL1/CL2 evidence_refs=E1 可解析；但 E1 输出不含全 223 节数据，证据部分不可解析")
  },
  "notes": "Q4 完全未实现；刚体链递推使龙尾脱离螺线（物理错误）；碰撞抽样粗糙",
  "layer_totals": {"L1": 7, "L2": 10, "L3": 5, "L4": 4},
  "layer_pass": {"L1": True, "L2": False, "L3": False, "L4": False},
  "overall_pass": False
}

BUNDLES["BUNDLE_009"] = {
  "scores": {
    "L1.1": s(1,2,"提取第1组参数（560/20/28/31/25/28800）；缺第2/3组、两道工序参数、故障参数；move2/3 仅入代码未入 IR"),
    "L1.2": s(2,2,"C1 RGV 单服务/C2 CNC 完成才可上下料 为关键隐式约束，A3 显式忽略故障"),
    "L1.3": s(1,2,"识别吞吐量/利用率输出；未识别附件2 EXCEL(3工作表)交付"),
    "L1.4": s(1,1,"默认 1"),
    "L1.5": s(2,2,"simulation/DES 调度 判定正确"),
    "L2.1": s(2,2,"v_N/v_thr/v_cyc/v_util/v_cnc 声明含类型"),
    "L2.2": s(1,2,"p_pt/p_m1/p_lo/p_le/p_ct/p_shift 有来源；EQ1 引用 n_i 未声明；move2/3 缺"),
    "L2.3": s(2,2,"A1-A3 显式分型合理（贪心策略/忽略故障/同刀具）"),
    "L2.4": s(1,2,"OBJ1 最大化吞吐正确；两道工序/故障/3组数据目标未建模"),
    "L2.5": s(1,2,"C1/C2 正确；缺两道工序顺序/故障约束"),
    "L2.6": s(2,3,"E1 DES 机理正确；E2 一致；E3 目标支撑；E4 无候选对比"),
    "L2.7": s(1,2,"EQ1 可求解但仅为计数；n_i 符号未声明"),
    "L3.1": s(2,2,"贪心+DES 与调度问题匹配"),
    "L3.2": s(1,2,"status=success；fidelity 11/11；但任务2需 3 组数据仅第 1 组、无 EXCEL 产出"),
    "L3.3": s(2,2,"DES 精确仿真输出有限（248 件/利用率 0.996），确定性无发散"),
    "L3.4": s(2,2,"code_hash 存在；代码完全确定性无随机"),
    "L3.5": s(1,1,"248 件/31件每小时 在合理量级（RGV 近饱和 0.996）"),
    "L4.1": s(0,2,"V1/V2 仅守恒/利用率界，无基线"),
    "L4.2": s(0,2,"无灵敏度分析"),
    "L4.3": s(0,1,"无极限检验"),
    "L4.4": s(1,2,"V1/V2 匹配 CL1 但无执行验证证据"),
    "L4.5": s(2,2,"CL1 evidence_refs=[E1,V1] 可解析且 E1 已执行")
  },
  "notes": "仅覆盖一道工序第1组；任务2 三组数据与 EXCEL 交付未完成",
  "layer_totals": {"L1": 7, "L2": 10, "L3": 8, "L4": 3},
  "layer_pass": {"L1": True, "L2": False, "L3": True, "L4": False},
  "overall_pass": False
}

BUNDLES["BUNDLE_010"] = {
  "scores": {
    "L1.1": s(1,2,"P1-P7 提取；孔径/孔距未提取（0.85 近似）"),
    "L1.2": s(2,2,"A1/A4 隐式条件识别充分"),
    "L1.3": s(1,2,"未识别 xlsx 文件名/6 位小数交付"),
    "L1.4": s(1,1,"ambiguity_handling 标注 2 处歧义"),
    "L1.5": s(2,2,"simulation 判定正确"),
    "L2.1": s(2,2,"V1-V9 完整声明"),
    "L2.2": s(1,2,"r0 与 0.85 折算未声明"),
    "L2.3": s(2,2,"A1-A4 合理"),
    "L2.4": s(1,2,"Q4 无目标"),
    "L2.5": s(1,2,"C1-C3 正确；Q4 约束缺"),
    "L2.6": s(2,3,"E1-E3 满足；E4 对比表面"),
    "L2.7": s(1,2,"r0 未声明"),
    "L3.1": s(2,2,"时间步进+弧长积分匹配"),
    "L3.2": s(1,2,"223×301 帧未产出；Q4 未实现"),
    "L3.3": s(1,2,"输出有限；无网格收敛检验"),
    "L3.4": s(2,2,"code_hash 存在；random.seed(42) 固定"),
    "L3.5": s(0,1,"tail 位置 ±350~415m 物理不合理"),
    "L4.1": s(0,2,"无基线"),
    "L4.2": s(1,2,"plan.sensitivity 占位未执行"),
    "L4.3": s(1,1,"plan.limit_tests 2 类"),
    "L4.4": s(1,2,"部分主张覆盖"),
    "L4.5": s(1,2,"证据部分不可解析")
  },
  "notes": "与 008 同模型，seed=42；执行结果相同；物理不合理致 L3.5=0",
  "layer_totals": {"L1": 7, "L2": 10, "L3": 6, "L4": 4},
  "layer_pass": {"L1": True, "L2": False, "L3": False, "L4": False},
  "overall_pass": False
}

BUNDLES["BUNDLE_011"] = {
  "scores": {
    "L1.1": s(1,2,"合成数据替代附件一；真实数据参数未提取"),
    "L1.2": s(1,2,"信誉归入密度；Q3/Q4 缺失"),
    "L1.3": s(1,2,"Q1/Q2 交付；Q3/Q4 缺失"),
    "L1.4": s(1,1,"默认 1"),
    "L1.5": s(2,2,"statistical_modeling 判定正确"),
    "L2.1": s(2,2,"v_p/v_d/v_m/v_c/v_popt/v_prof 声明"),
    "L2.2": s(0,2,"EQ1 引用 β0-β3 未声明"),
    "L2.3": s(1,2,"合成数据假设不合理"),
    "L2.4": s(1,2,"Q3/Q4 缺失"),
    "L2.5": s(1,2,"自拟定价范围+概率公理"),
    "L2.6": s(2,3,"E1-E3 满足；E4 无对比"),
    "L2.7": s(1,2,"β 未声明"),
    "L3.1": s(2,2,"梯度下降+网格搜索匹配"),
    "L3.2": s(2,2,"status=success；fidelity 14/17；输出完整"),
    "L3.3": s(1,2,"loss_final=0.679 有限；无收敛阈值"),
    "L3.4": s(2,2,"code_hash 存在；seed=42 固定"),
    "L3.5": s(0,1,"拟合系数 price=-0.169/distance=+0.1366 与声明单调性(V2)及解释文本矛盾，逻辑不合理"),
    "L4.1": s(0,2,"无基线"),
    "L4.2": s(0,2,"无灵敏度声明"),
    "L4.3": s(0,1,"无极限检验"),
    "L4.4": s(1,2,"验证目标匹配 Q1/Q2 主张但无执行证据"),
    "L4.5": s(1,2,"CL1 证据含 V2 单调性，与执行系数符号矛盾→部分 unresolved")
  },
  "notes": "执行系数符号与模型声明解释相反（price 负、distance 正），结果逻辑自相矛盾",
  "layer_totals": {"L1": 6, "L2": 8, "L3": 7, "L4": 2},
  "layer_pass": {"L1": False, "L2": False, "L3": True, "L4": False},
  "overall_pass": False
}

for bid, data in BUNDLES.items():
    # rebuild layer totals from scores to guarantee consistency
    lt = {"L1": 0, "L2": 0, "L3": 0, "L4": 0}
    lm = {"L1": 0, "L2": 0, "L3": 0, "L4": 0}
    for dim, sc in data["scores"].items():
        layer = dim.split(".")[0]
        lt[layer] += sc["score"]
        lm[layer] += sc["max"]
    lp = {k: (lt[k] >= lm[k] * 0.7) for k in lt}
    # key dims per layer: L1(1,3,5), L2(1,2,4,5,6), L3(1,2,4), L4(1,2,4,5)
    keymap = {"L1": ["L1.1","L1.3","L1.5"], "L2": ["L2.1","L2.2","L2.4","L2.5","L2.6"],
              "L3": ["L3.1","L3.2","L3.4"], "L4": ["L4.1","L4.2","L4.4","L4.5"]}
    for layer, keys in keymap.items():
        if all(data["scores"][k]["score"] > 0 for k in keys):
            pass  # key dims ok
        else:
            lp[layer] = False
    overall = all(lp.values())
    payload = {
        "bundle_id": bid,
        "evaluator_id": "C",
        "rubric_version": "v1.1",
        "scores": data["scores"],
        "layer_totals": lt,
        "layer_max": lm,
        "layer_pass": lp,
        "overall_pass": overall,
        "notes": data["notes"]
    }
    with open(os.path.join(OUT, bid + ".json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(bid, "L1:%d/%d %s L2:%d/%d %s L3:%d/%d %s L4:%d/%d %s OVERALL:%s" % (
        lt["L1"], lm["L1"], lp["L1"], lt["L2"], lm["L2"], lp["L2"],
        lt["L3"], lm["L3"], lp["L3"], lt["L4"], lm["L4"], lp["L4"], overall))
