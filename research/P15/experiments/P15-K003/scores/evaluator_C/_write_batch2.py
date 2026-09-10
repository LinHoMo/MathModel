# -*- coding: utf-8 -*-
"""Write batch 2 scores (BUNDLE_012..022) and patch batch1 L2.6 revisions for 001/008/010."""
import json, os

OUT = r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\experiments\P15-K003\scores\evaluator_C"

def s(score, maxv, ev):
    return {"score": score, "max": maxv, "evidence": ev}

B = {}

B["BUNDLE_012"] = {
 "scores": {
  "L1.1": s(1,2,"Q1 参数全提取；Q2/Q3 具体值(65°C/5.5mm/80°C/30/60min)未入 parameters"),
  "L1.2": s(2,2,"A1 一维/A2 对流边界+体温37/A3 物性恒定，初始边界有依据"),
  "L1.3": s(1,2,"识别温度分布/皮肤温度输出；未识别 problem1.xlsx 与精度要求"),
  "L1.4": s(1,1,"无显著歧义，未标注→默认1"),
  "L1.5": s(2,2,"numerical_pde 判定正确"),
  "L2.1": s(2,2,"v_T/v_Ts/v_t/v_x 声明且区分类型含范围"),
  "L2.2": s(0,2,"EQ1 引用 ρ_i,c_i,k_i；EQ2 引用 h,k,T_body；仅 k1/k2/h 声明，缺失率>30%"),
  "L2.3": s(2,2,"A1-A3 显式分型合理"),
  "L2.4": s(1,2,"OBJ1 覆盖 Q1；Q2/Q3 优化目标未声明"),
  "L2.5": s(2,2,"C1/C2 形式化且方向正确"),
  "L2.6": s(2,3,"E1-E3 满足；E4 无候选对比"),
  "L2.7": s(1,2,"缺初始条件方程；ρ/c 未声明→符号不一致"),
  "L3.1": s(2,2,"显式 FDM 满足 CFL，与 PDE 匹配"),
  "L3.2": s(1,2,"success；fidelity 10/11；problem1.xlsx 未产出"),
  "L3.3": s(1,2,"输出有限收敛(42.5°C)；无网格收敛检验证据"),
  "L3.4": s(2,2,"code_hash 存在；代码确定性"),
  "L3.5": s(1,1,"42.5°C 在 [37,80] 合理区间"),
  "L4.1": s(0,2,"validation_plan 无对照基线"),
  "L4.2": s(1,2,"plan.sensitivity 扰动 II 厚度/环境温度（敏感参数）但未执行"),
  "L4.3": s(1,1,"plan.limit_tests 含 2 类极限检验"),
  "L4.4": s(2,2,"validation_targets=OBJ1 覆盖 CL1；residual/constraint check 开启"),
  "L4.5": s(2,2,"CL1 evidence_refs=[E1,V1] 可解析无 unresolved")
 },
 "notes": "与 002 同模型（2018A）；IR 参数声明不全致 L2 差 0.5 未达阈值",
 "layer_totals": {"L1":7,"L2":10,"L3":7,"L4":6},
 "layer_pass": {"L1":True,"L2":False,"L3":True,"L4":False},
 "overall_pass": False
}

B["BUNDLE_013"] = {
 "scores": {
  "L1.1": s(1,2,"problem_binding Q1-Q3 缺 Q4；有效数据范围 85-105% (A3) 提取；无 extracted_conditions 列表"),
  "L1.2": s(1,2,"A2 K+ 淋滤隐式条件有依据；缺 空白=未检测等隐式条件"),
  "L1.3": s(1,2,"E1/E2 expected_outputs 仅精度与3预测；未识别亚类划分/敏感性/关联交付"),
  "L1.4": s(1,1,"plan.ambiguity_handling 标注风化程度量化歧义并采纳 K2O 流失率"),
  "L1.5": s(2,2,"statistical_modeling 判定正确"),
  "L2.1": s(1,2,"V1-V8 声明含类型；BaO 未声明，代码 14 特征仅声明 3"),
  "L2.2": s(0,2,"E1/E2 引用 w,b 未在 parameters 声明"),
  "L2.3": s(2,2,"A1-A3 显式分型含 rationale"),
  "L2.4": s(1,2,"O1/O2 匹配 Q2/Q3；Q1 风化前成分预测与 Q4 无目标"),
  "L2.5": s(2,2,"C1/C2 方向正确覆盖题面关键约束"),
  "L2.6": s(3,3,"E1-E3 满足；E4 候选对比（统计 vs 仿真）维度与依据充分"),
  "L2.7": s(1,2,"E1/E2 引用 w,b 未声明→符号不一致"),
  "L3.1": s(2,2,"梯度下降匹配逻辑回归"),
  "L3.2": s(1,2,"success；fidelity 3/15 (0.2)，多数声明变量未进 outputs"),
  "L3.3": s(1,2,"输出有限（acc=1.0）；无收敛阈值/残差证据"),
  "L3.4": s(1,2,"code_hash 存在；seed=43 非 42"),
  "L3.5": s(1,1,"输出在合理范围；但基于合成数据非附件实测"),
  "L4.1": s(0,2,"无对照基线"),
  "L4.2": s(1,2,"plan.sensitivity lr/k_loss 扰动但 result=占位未执行"),
  "L4.3": s(1,1,"plan.limit_tests 纯SiO2/高PbO 2类极限检验（占位）"),
  "L4.4": s(1,2,"claim_evidence_map 覆盖 CL1/CL2；风化预测主张无执行验证"),
  "L4.5": s(1,2,"claims 有 evidence_refs 且 status=supported；但 E1 输出与声明变量失配（fidelity 0.2）")
 },
 "notes": "与 001 同模型 + 验证计划；seed=43；合成数据替代附件",
 "layer_totals": {"L1":6,"L2":10,"L3":6,"L4":4},
 "layer_pass": {"L1":False,"L2":False,"L3":False,"L4":False},
 "overall_pass": False
}

B["BUNDLE_014"] = {
 "scores": {
  "L1.1": s(1,2,"提取 20平台/13要道/3分钟/60km/h；缺增加2-5/全市六区/P点(32)"),
  "L1.2": s(1,2,"3km 半径有推导；'每节点均设平台'与题面 20 平台矛盾"),
  "L1.3": s(1,2,"识别管辖/封锁交付；缺增设/合理性/围堵交付"),
  "L1.4": s(1,1,"'尽量3分钟'未作歧义处理→默认1"),
  "L1.5": s(2,2,"graph_algorithm 判定正确"),
  "L2.1": s(2,2,"coverage/t_max/CV/allocation/blockade 变量定义清楚"),
  "L2.2": s(1,2,"参数(时速/3min/20/13/3km)列出；方程引用 w(e) 边权未列参数"),
  "L2.3": s(1,2,"A1/A2 合理；'每节点设平台'与题面矛盾"),
  "L2.4": s(1,2,"Q1 前两问目标；增设/合理性/围堵目标缺失"),
  "L2.5": s(1,2,"3分钟/一平台一路口/唯一管辖 正确；缺 2-5 平台数约束"),
  "L2.6": s(2,3,"E1 Dijkstra 机理正确；E2/E3 一致；E4 无候选对比"),
  "L2.7": s(1,2,"方程可求解；w(e) 符号未声明"),
  "L3.1": s(2,2,"Dijkstra+最近邻+贪心匹配"),
  "L3.2": s(2,2,"success；输出完整；fidelity unverifiable（叙述式）"),
  "L3.3": s(2,2,"精确算法输出有限无 NaN"),
  "L3.4": s(2,2,"code_hash 存在；代码确定性（random_seed=42 声明）"),
  "L3.5": s(0,1,"coverage=1.0/max_response=0/封锁距离全 0——合成网络退化，对真实城区不合理"),
  "L4.1": s(0,2,"doc 验证无基线"),
  "L4.2": s(0,2,"无灵敏度分析"),
  "L4.3": s(0,1,"无极限检验"),
  "L4.4": s(1,2,"验证覆盖 Q1 主张但无执行证据"),
  "L4.5": s(1,2,"叙述式无结构化 claim")
 },
 "notes": "与 003 同模型叙述版；合成 20 节点网络致结果全 0",
 "layer_totals": {"L1":6,"L2":9,"L3":8,"L4":2},
 "layer_pass": {"L1":False,"L2":False,"L3":True,"L4":False},
 "overall_pass": False
}

B["BUNDLE_015"] = {
 "scores": {
  "L1.1": s(1,2,"合成数据替代附件一；未提取附件真实参数"),
  "L1.2": s(1,2,"信誉归入密度；Q3/Q4 隐式条件缺失"),
  "L1.3": s(1,2,"Q1/Q2 交付识别；Q3/Q4 缺失"),
  "L1.4": s(1,1,"默认 1"),
  "L1.5": s(2,2,"statistical_modeling 判定正确"),
  "L2.1": s(2,2,"doc 变量节完整"),
  "L2.2": s(1,2,"doc 参数节含样本量/学习率/轮数/搜索范围；β 系数未列参数"),
  "L2.3": s(1,2,"合成数据假设（A2）不合理"),
  "L2.4": s(1,2,"OBJ1/OBJ2 正确；Q3/Q4 缺失"),
  "L2.5": s(1,2,"自拟定价范围+概率公理"),
  "L2.6": s(2,3,"E1-E3 满足；E4 无候选对比"),
  "L2.7": s(1,2,"β 未声明"),
  "L3.1": s(2,2,"梯度下降+网格搜索匹配"),
  "L3.2": s(2,2,"success；输出完整（系数/最优价/利润曲线）"),
  "L3.3": s(1,2,"loss_final=0.655 有限；无收敛阈值"),
  "L3.4": s(1,2,"code_hash 存在；seed=43 非 42"),
  "L3.5": s(1,1,"系数符号正确，值域合理；最优价 40 为网格端点"),
  "L4.1": s(0,2,"无基线"),
  "L4.2": s(0,2,"无灵敏度声明"),
  "L4.3": s(0,1,"无极限检验"),
  "L4.4": s(1,2,"验证节匹配 Q1/Q2 主张但无执行证据"),
  "L4.5": s(1,2,"叙述式无结构化 claim")
 },
 "notes": "2017B 叙述版，系数符号正确；合成数据是主要缺陷",
 "layer_totals": {"L1":6,"L2":9,"L3":7,"L4":2},
 "layer_pass": {"L1":False,"L2":False,"L3":True,"L4":False},
 "overall_pass": False
}

B["BUNDLE_016"] = {
 "scores": {
  "L1.1": s(1,2,"Q1 决策结构(A/B/蓄车池)提取；Q3 两车道/Q4 优先权条件未提取"),
  "L1.2": s(2,2,"Poisson/指数服务/M/M/1 稳定性 隐式条件识别有依据"),
  "L1.3": s(1,2,"识别 Q1 决策模型交付；Q2-Q4 交付(数据/上车点/优先方案)缺失"),
  "L1.4": s(1,1,"默认 1"),
  "L1.5": s(2,2,"queuing_theory+决策分析 判定正确"),
  "L2.1": s(2,2,"doc 变量节 λ/μ/W_q/profit_q/profit_c/decision 定义清楚"),
  "L2.2": s(2,2,"doc 参数节含全部成本/车费/λ/μ；方程符号均被覆盖"),
  "L2.3": s(2,2,"M/M/1 假设显式分型合理"),
  "L2.4": s(1,2,"Q1 目标正确；Q2-Q4 无目标"),
  "L2.5": s(2,2,"C1(ρ<1)/C2(W_q≥0) 形式化正确"),
  "L2.6": s(2,3,"M/M/1 机理正确；E2/E3 一致；E4 无候选对比"),
  "L2.7": s(2,2,"W_q 与收益公式完整可求解，符号覆盖"),
  "L3.1": s(2,2,"M/M/1 解析+λ 扫描匹配"),
  "L3.2": s(2,2,"success；输出完整（决策/收益/扫描）"),
  "L3.3": s(2,2,"解析精确结果，有限无 NaN，扫描单调"),
  "L3.4": s(2,2,"code_hash 存在；代码确定性"),
  "L3.5": s(1,1,"收益/等待时间在合理量级（ρ=0.75 稳定）"),
  "L4.1": s(0,2,"无对照基线"),
  "L4.2": s(2,2,"E2 已执行 λ 10→38 扫描（敏感参数），报告决策切换边界 λ_critical=39.98"),
  "L4.3": s(1,1,"doc 验证含 ρ≥1 队列发散极限行为"),
  "L4.4": s(1,2,"验证匹配 Q1 主张；Q2-Q4 未覆盖"),
  "L4.5": s(1,2,"叙述式无结构化 claim 映射")
 },
 "notes": "2019C M/M/1 模型正确且执行良好；L4 缺基线致 FAIL",
 "layer_totals": {"L1":7,"L2":13,"L3":9,"L4":5},
 "layer_pass": {"L1":True,"L2":True,"L3":True,"L4":False},
 "overall_pass": False
}

B["BUNDLE_017"] = {
 "scores": {
  "L1.1": s(1,2,"Q1 结构提取；Q3/Q4 条件未处理"),
  "L1.2": s(2,2,"A1 Poisson/指数、A3 确定值 隐式条件有依据"),
  "L1.3": s(1,2,"Q1 交付；Q2-Q4 缺失"),
  "L1.4": s(1,1,"默认 1"),
  "L1.5": s(2,2,"queuing_theory 判定正确"),
  "L2.1": s(2,2,"v_lambda/v_mu/v_Wq/v_pq/v_pc/v_dec 声明含类型与范围"),
  "L2.2": s(1,2,"p_lam/p_mu/p_fare_q/p_fare_c/p_wc/p_ec 有来源；EQ2 引用 c_f(怠速)/t_c(回市区)未声明"),
  "L2.3": s(2,2,"A1-A3 显式分型合理"),
  "L2.4": s(1,2,"OBJ1 覆盖 Q1；Q2-Q4 无目标"),
  "L2.5": s(2,2,"C1/C2 形式化正确"),
  "L2.6": s(2,3,"M/M/1 机理正确；E4 无候选对比"),
  "L2.7": s(1,2,"EQ1/EQ2 完整可求解；c_f/t_c 符号未声明"),
  "L3.1": s(2,2,"M/M/1 解析+扫描匹配"),
  "L3.2": s(2,2,"success；fidelity 14/14 (1.0) 全对齐"),
  "L3.3": s(2,2,"解析精确结果有限无 NaN"),
  "L3.4": s(2,2,"code_hash 存在；代码确定性"),
  "L3.5": s(1,1,"收益/等待量级合理"),
  "L4.1": s(0,2,"validations 无对照基线"),
  "L4.2": s(2,2,"E2 λ 扫描已执行，报告决策切换边界 λ_critical"),
  "L4.3": s(1,1,"V1 稳定性含 ρ≥1 极限行为"),
  "L4.4": s(2,2,"V1/V2 覆盖 CL1/O1 且 E1/E2 已执行"),
  "L4.5": s(2,2,"CL1 evidence_refs=[E1,E2,V1] 可解析，无 unresolved")
 },
 "notes": "2019C IR 版，fidelity 1.0；仅 L4.1 无基线致 L4 关键维度 FAIL",
 "layer_totals": {"L1":7,"L2":11,"L3":9,"L4":7},
 "layer_pass": {"L1":True,"L2":True,"L3":True,"L4":False},
 "overall_pass": False
}

B["BUNDLE_018"] = {
 "scores": {
  "L1.1": s(1,2,"第1组参数提取；缺第2/3组、两道工序、故障参数"),
  "L1.2": s(2,2,"RGV 单服务/CNC 完成才上下料 关键隐式约束识别"),
  "L1.3": s(1,2,"识别吞吐量交付；未识别附件2 EXCEL 3 工作表"),
  "L1.4": s(1,1,"默认 1"),
  "L1.5": s(2,2,"simulation/DES 判定正确"),
  "L2.1": s(2,2,"doc 变量节完整"),
  "L2.2": s(2,2,"doc 参数节含移动1/2/3、加工、上下料、清洗、班次；方程符号覆盖"),
  "L2.3": s(2,2,"贪心/忽略故障/物料充足 假设显式合理"),
  "L2.4": s(1,2,"Q1 一道工序目标；两道工序/故障/3组缺失"),
  "L2.5": s(1,2,"RGV 单服务/CNC 顺序/清洗约束；缺两道工序/故障约束"),
  "L2.6": s(2,3,"DES 机理正确；E4 无候选对比"),
  "L2.7": s(1,2,"N=Σn_i 中 n_i 未在变量节列出"),
  "L3.1": s(2,2,"贪心+DES 匹配调度问题"),
  "L3.2": s(1,2,"success；输出完整；但仅第1组，无 EXCEL 交付"),
  "L3.3": s(2,2,"DES 精确结果有限（248件/利用率0.996）"),
  "L3.4": s(2,2,"code_hash 存在；代码确定性"),
  "L3.5": s(1,1,"248 件/31件每小时 合理量级"),
  "L4.1": s(0,2,"无基线"),
  "L4.2": s(0,2,"无灵敏度分析"),
  "L4.3": s(0,1,"无极限检验"),
  "L4.4": s(1,2,"验证匹配 CL1 但无执行证据"),
  "L4.5": s(1,2,"叙述式无结构化 claim")
 },
 "notes": "2018B 叙述版；仅覆盖一道工序第1组",
 "layer_totals": {"L1":7,"L2":11,"L3":8,"L4":2},
 "layer_pass": {"L1":True,"L2":True,"L3":True,"L4":False},
 "overall_pass": False
}

B["BUNDLE_019"] = {
 "scores": {
  "L1.1": s(1,2,"Q1 参数全提取；Q2/Q3 具体值未入 parameters"),
  "L1.2": s(2,2,"A1-A3 隐式条件有依据"),
  "L1.3": s(1,2,"未识别 problem1.xlsx 交付"),
  "L1.4": s(1,1,"默认 1"),
  "L1.5": s(2,2,"numerical_pde 判定正确"),
  "L2.1": s(2,2,"v_T/v_Ts/v_t/v_x 完整声明"),
  "L2.2": s(0,2,"EQ1/EQ2 引用 ρ/c/k3/k4/T_body 未声明"),
  "L2.3": s(2,2,"A1-A3 合理"),
  "L2.4": s(1,2,"Q2/Q3 优化目标缺失"),
  "L2.5": s(2,2,"C1/C2 正确"),
  "L2.6": s(2,3,"E1-E3 满足；E4 无候选对比"),
  "L2.7": s(1,2,"缺初始条件；ρ/c 未声明"),
  "L3.1": s(2,2,"显式 FDM CFL 匹配"),
  "L3.2": s(1,2,"success；fidelity 10/11；problem1.xlsx 未产出"),
  "L3.3": s(1,2,"输出有限收敛；无网格收敛检验"),
  "L3.4": s(2,2,"code_hash 存在；确定性"),
  "L3.5": s(1,1,"42.5°C 合理"),
  "L4.1": s(0,2,"无基线"),
  "L4.2": s(1,2,"plan.sensitivity 占位未执行"),
  "L4.3": s(1,1,"plan.limit_tests 2类"),
  "L4.4": s(2,2,"validation_targets=OBJ1 覆盖 CL1"),
  "L4.5": s(2,2,"CL1 证据可解析")
 },
 "notes": "与 002/012 同模型（2018A）",
 "layer_totals": {"L1":7,"L2":10,"L3":7,"L4":6},
 "layer_pass": {"L1":True,"L2":False,"L3":True,"L4":False},
 "overall_pass": False
}

B["BUNDLE_020"] = {
 "scores": {
  "L1.1": s(1,2,"第1组参数；缺第2/3组、两道工序、故障参数；move2/3 仅入代码"),
  "L1.2": s(2,2,"C1/C2 关键隐式约束；A3 显式忽略故障"),
  "L1.3": s(1,2,"未识别附件2 EXCEL(3工作表)交付"),
  "L1.4": s(1,1,"默认 1"),
  "L1.5": s(2,2,"simulation/DES 判定正确"),
  "L2.1": s(2,2,"v_N/v_thr/v_cyc/v_util/v_cnc 声明含类型与范围"),
  "L2.2": s(1,2,"p_pt/p_m1/p_lo/p_le/p_ct/p_shift 有来源；EQ1 引用 n_i 未声明；move2/3 缺"),
  "L2.3": s(2,2,"A1-A3 显式分型合理"),
  "L2.4": s(1,2,"OBJ1 正确；两道工序/故障/3组缺失"),
  "L2.5": s(1,2,"C1/C2 正确；缺两道工序/故障约束"),
  "L2.6": s(2,3,"DES 机理正确；E4 无候选对比"),
  "L2.7": s(1,2,"EQ1 中 n_i 未声明"),
  "L3.1": s(2,2,"贪心+DES 匹配"),
  "L3.2": s(1,2,"success；fidelity 11/11；但仅第1组无 EXCEL 交付"),
  "L3.3": s(2,2,"DES 精确结果有限"),
  "L3.4": s(2,2,"code_hash 存在；确定性"),
  "L3.5": s(1,1,"248件/31件每小时 合理"),
  "L4.1": s(0,2,"无基线"),
  "L4.2": s(1,2,"plan.sensitivity 加工时间/CNC数量（敏感参数）占位未执行"),
  "L4.3": s(1,1,"plan.limit_tests 单CNC/零移动 2类"),
  "L4.4": s(1,2,"validation_targets=OBJ1 覆盖 CL1；Q2/Q3 主张缺失"),
  "L4.5": s(2,2,"CL1 evidence_refs=[E1,V1] 可解析且 E1 已执行")
 },
 "notes": "2018B IR 版含验证计划；仅一道工序第1组",
 "layer_totals": {"L1":7,"L2":10,"L3":8,"L4":5},
 "layer_pass": {"L1":True,"L2":False,"L3":True,"L4":False},
 "overall_pass": False
}

B["BUNDLE_021"] = {
 "scores": {
  "L1.1": s(2,2,"doc 显式条件列表覆盖 223节/341/220/30/27.5/55cm/1m/s/16圈/9m/1.7m/2m/s（仅缺孔径5.5）"),
  "L1.2": s(2,2,"刚体链间距守恒/非相邻节碰撞/角速度差异 隐式条件识别充分"),
  "L1.3": s(1,2,"目标列出 Q1/Q2/Q3/Q5 输出；未识别 result1/2/4.xlsx 文件与 6 位小数交付"),
  "L1.4": s(1,1,"歧义点：碰撞判定标准/后节速度递推，已标注并采纳方案"),
  "L1.5": s(2,2,"运动学仿真（螺线+刚体链）判定正确"),
  "L2.1": s(2,2,"theta/r/(x_i,y_i)/v_i/d_min 声明含类型"),
  "L2.2": s(1,2,"N/L_head/L_body/W/pitch/v0/R_turn 有题面来源；E1 引用 r0 值(0.5)与 0.85 系数未参数化"),
  "L2.3": s(2,2,"A1-A4 显式分型含 rationale"),
  "L2.4": s(1,2,"Q1/Q2/Q3/Q5 目标；Q4 调头路径优化缺失"),
  "L2.5": s(1,2,"刚体/无碰撞/速度约束；缺 Q4 相切约束，刚体递推与'各把手位于螺线'冲突"),
  "L2.6": s(3,3,"E1-E3 满足；E4 候选对比（排除PDE/纯优化）维度与依据充分"),
  "L2.7": s(1,2,"E1-E4 可求解；r0 符号值未声明"),
  "L3.1": s(2,2,"时间步进+弧长数值积分匹配"),
  "L3.2": s(1,2,"success；仅输出头尾+关键帧，Q1 需 223×301 帧未产出；Q4 未实现；xlsx 未生成"),
  "L3.3": s(1,2,"输出有限；无网格收敛检验执行证据"),
  "L3.4": s(1,2,"code_hash 存在；seed=43 非 42"),
  "L3.5": s(0,1,"tail 位置 ±350~415m 远超螺线半径(~56m)物理不合理；collision=false 由粗抽样(步长10)造成"),
  "L4.1": s(0,2,"无对照基线"),
  "L4.2": s(1,2,"doc 灵敏度（螺距±10%）声明但未执行"),
  "L4.3": s(1,1,"doc 极限检验 pitch→0 螺线退化验证声明"),
  "L4.4": s(1,2,"验证方案覆盖 Q1 主张但无执行证据"),
  "L4.5": s(1,2,"叙述式无结构化 claim")
 },
 "notes": "2024A 叙述版；Q4 未实现，龙尾脱离螺线物理错误",
 "layer_totals": {"L1":8,"L2":11,"L3":5,"L4":4},
 "layer_pass": {"L1":True,"L2":True,"L3":False,"L4":False},
 "overall_pass": False
}

B["BUNDLE_022"] = {
 "scores": {
  "L1.1": s(1,2,"合成数据替代附件一；真实参数未提取"),
  "L1.2": s(1,2,"信誉归入密度；Q3/Q4 隐式条件缺失"),
  "L1.3": s(1,2,"Q1/Q2 交付；Q3/Q4 缺失"),
  "L1.4": s(1,1,"默认 1"),
  "L1.5": s(2,2,"statistical_modeling 判定正确"),
  "L2.1": s(2,2,"v_p/v_d/v_m/v_c/v_popt/v_prof 声明含类型与范围"),
  "L2.2": s(0,2,"EQ1 引用 β0-β3 未在 parameters 声明"),
  "L2.3": s(1,2,"合成数据假设（A2）不合理"),
  "L2.4": s(1,2,"OBJ1/OBJ2 匹配 Q1/Q2；Q3/Q4 缺失"),
  "L2.5": s(1,2,"自拟定价范围+概率公理；关键约束缺失"),
  "L2.6": s(2,3,"Logistic 机理正确；E4 无候选对比"),
  "L2.7": s(1,2,"EQ1/EQ2 可求解；β 未声明"),
  "L3.1": s(2,2,"梯度下降+网格搜索匹配"),
  "L3.2": s(2,2,"success；fidelity 14/17 (0.82)；输出完整"),
  "L3.3": s(1,2,"loss_final=0.681 有限；无收敛阈值"),
  "L3.4": s(1,2,"code_hash 存在；seed=44 非 42"),
  "L3.5": s(1,1,"系数符号正确（price+/distance-/density+），值域合理；最优价 40 网格端点"),
  "L4.1": s(0,2,"无基线"),
  "L4.2": s(0,2,"无灵敏度执行证据"),
  "L4.3": s(0,1,"无极限检验"),
  "L4.4": s(1,2,"验证目标匹配 Q1/Q2 主张但无执行证据"),
  "L4.5": s(2,2,"CL1/CL2 evidence_refs 可解析到已执行 E1/E2")
 },
 "notes": "2017B IR 版 seed=44；系数符号正确；合成数据主要缺陷",
 "layer_totals": {"L1":6,"L2":8,"L3":7,"L4":3},
 "layer_pass": {"L1":False,"L2":False,"L3":True,"L4":False},
 "overall_pass": False
}

KEYMAP = {"L1": ["L1.1","L1.3","L1.5"], "L2": ["L2.1","L2.2","L2.4","L2.5","L2.6"],
          "L3": ["L3.1","L3.2","L3.4"], "L4": ["L4.1","L4.2","L4.4","L4.5"]}

def write_payload(bid, data):
    lt = {"L1":0,"L2":0,"L3":0,"L4":0}; lm = {"L1":0,"L2":0,"L3":0,"L4":0}
    for dim, sc in data["scores"].items():
        layer = dim.split(".")[0]
        lt[layer] += sc["score"]; lm[layer] += sc["max"]
    lp = {k: (lt[k] >= lm[k]*0.7) for k in lt}
    for layer, keys in KEYMAP.items():
        if any(data["scores"][k]["score"] == 0 for k in keys):
            lp[layer] = False
    overall = all(lp.values())
    payload = {"bundle_id": bid, "evaluator_id": "C", "rubric_version": "v1.1",
               "scores": data["scores"], "layer_totals": lt, "layer_max": lm,
               "layer_pass": lp, "overall_pass": overall, "notes": data["notes"]}
    with open(os.path.join(OUT, bid + ".json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(bid, "L1:%d/%d %s L2:%d/%d %s L3:%d/%d %s L4:%d/%d %s OVERALL:%s" % (
        lt["L1"], lm["L1"], lp["L1"], lt["L2"], lm["L2"], lp["L2"],
        lt["L3"], lm["L3"], lp["L3"], lt["L4"], lm["L4"], lp["L4"], overall))

for bid, data in B.items():
    write_payload(bid, data)

# ---- Patch batch1: L2.6 candidates rule -> 3 for 001/008/010 ----
patch = {
 "BUNDLE_001": {"dim": "L2.6", "score": 3, "max": 3,
   "evidence": "E1-E3 满足；E4 候选对比（statistical_modeling vs simulation）含维度与依据"},
 "BUNDLE_008": {"dim": "L2.6", "score": 3, "max": 3,
   "evidence": "E1-E3 满足；E4 候选对比（simulation vs numerical_pde）含维度与依据"},
 "BUNDLE_010": {"dim": "L2.6", "score": 3, "max": 3,
   "evidence": "E1-E3 满足；E4 候选对比（simulation vs numerical_pde）含维度与依据"},
}
for bid, p in patch.items():
    path = os.path.join(OUT, bid + ".json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["scores"][p["dim"]] = {"score": p["score"], "max": p["max"], "evidence": p["evidence"]}
    lt = {"L1":0,"L2":0,"L3":0,"L4":0}; lm = {"L1":0,"L2":0,"L3":0,"L4":0}
    for dim, sc in data["scores"].items():
        layer = dim.split(".")[0]; lt[layer] += sc["score"]; lm[layer] += sc["max"]
    lp = {k: (lt[k] >= lm[k]*0.7) for k in lt}
    for layer, keys in KEYMAP.items():
        if any(data["scores"][k]["score"] == 0 for k in keys):
            lp[layer] = False
    data["layer_totals"] = lt; data["layer_pass"] = lp
    data["overall_pass"] = all(lp.values())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("PATCHED", bid, "L2:%d/%d %s OVERALL:%s" % (lt["L2"], lm["L2"], lp["L2"], data["overall_pass"]))
