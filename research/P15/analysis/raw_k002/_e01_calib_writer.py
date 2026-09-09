# -*- coding: utf-8 -*-
import json, os, datetime

BASE = r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\analysis\raw_k002"
OUT = os.path.join(BASE, "scores", "_calibration", "eval_E01")
os.makedirs(OUT, exist_ok=True)

RV = "MODEL_CONSTRUCTION_RUBRIC-v1.1a"
TS = datetime.datetime.now().astimezone().isoformat()

def mk(sub, dims, fail, notes):
    vec = {
        "L1_total": sum(dims[d]["score"] for d in ["L1.1","L1.2","L1.3","L1.4","L1.5"]),
        "L2_total": sum(dims[d]["score"] for d in ["L2.1","L2.2","L2.3","L2.4","L2.5","L2.6","L2.7"]),
        "L3_total": sum(dims[d]["score"] for d in ["L3.1","L3.2","L3.3","L3.4","L3.5"]),
        "L4_total": sum(dims[d]["score"] for d in ["L4.1","L4.2","L4.3","L4.4","L4.5"]),
    }
    return {
        "submission_id": sub,
        "evaluator": {"model": "E01", "type": "independent_llm", "version": "1.0", "timestamp": TS},
        "rubric_version": RV,
        "dimensions": dims,
        "vector": vec,
        "failure_modes": fail,
        "notes": notes,
    }

# ---------------- 04fc6d82 ----------------
d = {
 "L1.1": {"score":2, "evidence":"P1-P12 完整覆盖题面表1：RGV移动1/2/3单位[20,23,18]/[33,41,32]/[46,59,46]、一道工序加工[560,580,545]、一二工序[400,280,455]/[378,500,182]、奇偶上下料[28,30,27]/[31,35,32]、清洗[25,30,25]、班次28800s、故障概率0.01、排除[600,1200]s，与题面逐条一致。"},
 "L1.2": {"score":2, "evidence":"A1(单RGV串行)、A3(两道工序不同CNC)、A5(初始全空闲)、A6(移动按单位数)识别题面隐含物理/边界条件并给推导依据。"},
 "L1.3": {"score":1, "evidence":"objectives O1-O4 覆盖任务1模型+算法、任务2三组检验与效率；但未显式列出‘填入附件2 EXCEL表(3工作表)’这一具体交付物规格（锚定C：主要交付物已识别，附件表格/格式规格遗漏）。"},
 "L1.4": {"score":1, "evidence":"题面较明确，无必须标注的关键歧义；按默认给满分（problem_binding+assumptions 已对故障处理作A4合理假设，无未处理歧义）。"},
 "L1.5": {"score":2, "evidence":"model_family.primary=optimization/secondary=simulation，调度问题判定为0-1规划+离散事件仿真，与gold family一致。"},
 "L2.1": {"score":2, "evidence":"V1-V10 区分 state/decision/derived/observation 类型（p_t、s_{i,t}、x_{i,t}、N、T_{i,k}、I_RGV、z_{i,k}、R_{i,k}、W_t、C_j），关键变量齐全。"},
 "L2.2": {"score":2, "evidence":"P1-P12 每个参数有 source=题目 与取值；方程符号 m/g/u/w/H/q/a,b 均能在 parameters 声明集中解析。"},
 "L2.3": {"score":2, "evidence":"A1-A6 显式区分 mechanism/simplification/mechanism_assumption/projection/calibration 类型，每条带 rationale 且可检验。"},
 "L2.4": {"score":2, "evidence":"O1-O4 max N 覆盖任务1/2/3/4；机制M1-M4支撑目标量产生，约束C1-C6不与目标冲突（目标-机制-约束三角一致）。"},
 "L2.5": {"score":2, "evidence":"C1(单RGV)≤1、C2(加工不重叠)、C3(移动时间)、C4(工序顺序)、C5(N2≤N1)、C6(截止≤28800)方向正确无符号错误。"},
 "L2.6": {"score":3, "evidence":"E1机理-题面：调度用0-1规划正确；E2机理-方程：E1-E6由机理导出；E3机理-目标/约束：机制支撑目标且隐含约束入C；E4候选对比4个(optimization/simulation/DP/MDP)含选择依据，四要素全满足。"},
 "L2.7": {"score":2, "evidence":"E1-E6 含递推/代数方程与 derivation_trace，符号集⊆variables/parameters（T,u,w,g,z,R 均声明），可求解。"},
 "L3.1": {"score":2, "evidence":"S1分支定界(MIP滚动)、S2轮询启发式、S3蒙特卡洛样本均值，与0-1规划/随机故障模型口径匹配。"},
 "L3.2": {"score":2, "evidence":"no-exec-artifact: S1-S3 均带 implementation_ref(时间轴离散化+0-1变量/轮询规则/固定RNG抽样)，experiments X1-X3 声明 inputs/expected_outputs 输入-输出约定，可执行性有据可查。"},
 "L3.3": {"score":2, "evidence":"no-exec-artifact: MIP分支定界+上界加速为精确算法(收敛内在保证)；V3显式声明收敛判据‘样本100→2000，波动收敛于1%以内’。"},
 "L3.4": {"score":1, "evidence":"no-exec-artifact: S3蒙特卡洛‘固定随机数发生器’但仅声明样本500，未固定 seed=42 也未给 seeds≥5 与 cv 判据，缺一项。"},
 "L3.5": {"score":1, "evidence":"no-exec-artifact: X1 expected_outputs 给‘RGV利用率0.7-0.95’、X3‘期望产量较无故障降5%-15%’量级与题面物理量级相符。"},
 "L4.1": {"score":2, "evidence":"V1 以‘轮询贪心策略’为基线对比产量上界，并报告判据‘MIP最优解应不小于贪心解’。"},
 "L4.2": {"score":2, "evidence":"V2 对移动时间与上下料时间±10%扰动，报告班次产量变化率(弹性系数)。"},
 "L4.3": {"score":1, "evidence":"no-exec-artifact: V4 仅1类极限检验(清洗时间→0与移动时间→0，产量趋加工时间极限)，满足≥1类但未达2类。"},
 "L4.4": {"score":2, "evidence":"V1-V4 覆盖 O1-O4 全部核心主张(产量上界/一道接近最优/两道瓶颈/故障下降)，验证指标对应子问题目标。"},
 "L4.5": {"score":2, "evidence":"claims C1-C4 均有 evidence_refs 指向 X/V 且可解析；C1=supported、C2-C4=hypothesis 但均带可解析证据，无 unresolved/unsupported。"},
}
json.dump(mk("04fc6d82-7d15-4385-92fb-e43b99546eb4", d, [], "结构化MODEL_IR(S臂风格)，要素齐全。L1.3漏附件2 EXCEL规格；L3.4未固定seed≥5；L4.3仅1类极限。"), open(os.path.join(OUT,"04fc6d82-7d15-4385-92fb-e43b99546eb4.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- 3ff350bf ----------------
d = {
 "L1.1": {"score":2, "evidence":"P1-P8 覆盖题面显式数字：车速60km/h(P1)、覆盖阈值3min(P2)、A区平台20(P3)、要道13(P4)、新增平台[2,5](P5)、案发延迟3min(P7)、嫌疑车速60(P8)及道路长度附件(P6)，关键参数完整提取。"},
 "L1.2": {"score":2, "evidence":"A1(带权无向图/匀速)、A2(最近平台单归属+3min阈值)、A3(平台-要道一对一)、A4(围堵时间窗口)、A5(合理性指标)识别题面隐含图结构与覆盖约束并给依据。"},
 "L1.3": {"score":2, "evidence":"objectives O1-O5 对应题面5项交付要求(管辖分配/封锁调度/新增平台选址/六区合理性/围堵方案)，全部子问题交付物已识别。"},
 "L1.4": {"score":1, "evidence":"validation_plan.ambiguity_handling 标注3处歧义(3min软约束口径/嫌疑车速未给定/围堵时间窗)，并给出采纳方案与理由，歧义已处理。"},
 "L1.5": {"score":2, "evidence":"model_family.primary=optimization/secondary=graph_algorithm/decision_analysis，交巡警指派/选址/围堵判定为组合优化，与问题类型一致。"},
 "L2.1": {"score":2, "evidence":"V1-V9 区分 constant/derived/decision/observation 类型(节点/行驶时间/管辖指派/封锁指派/最大响应/新增平台/工作量/覆盖率/可达域)，关键变量齐全。"},
 "L2.2": {"score":2, "evidence":"P1-P8 每个参数有 source 与取值；方程符号 v_p/T_3/t_ij/m_A/n_g/Δ/τ_d/v_s 均在 parameters 声明集内。"},
 "L2.3": {"score":2, "evidence":"A1-A5 显式分类(mechanism/projection)且每条带 rationale 可检验。"},
 "L2.4": {"score":2, "evidence":"O1-O5 均为 min T_max/覆盖/瓶颈，与题面‘尽量3min到达/全封锁/新增平台/合理性/围堵’目标一致；目标被机制M1-M4支撑，约束不冲突。"},
 "L2.5": {"score":2, "evidence":"C1(指派∑=1)、C2(覆盖3min)、C3(匹配)、C4(预算2-5)、C5(封锁时限)方向正确。"},
 "L2.6": {"score":3, "evidence":"E1机理-题面：指派优化正确；E2机理-方程：E1-E6由机制导出；E3机理-目标/约束：机制支撑目标且约束入C；E4候选对比4个(optimization/graph/multi_objective排除/simulation排除)含依据，四要素全满足。"},
 "L2.7": {"score":2, "evidence":"E1-E6 含最短时间矩阵/指派/选址/可达域方程与 derivation_trace，符号集⊆variables/parameters，可求解。"},
 "L3.1": {"score":2, "evidence":"S1 Floyd-Warshall、S2 瓶颈指派(匈牙利)、S3 分支定界、S4 动态可达+指派，与图/优化模型口径匹配。"},
 "L3.2": {"score":2, "evidence":"no-exec-artifact: S1-S4 带 implementation_ref(Floyd-Warshall O(N³)/二分图瓶颈匹配/分支定界/动态可达)且 experiments X1-X5 声明 inputs/expected_outputs，可执行性有据可查。"},
 "L3.3": {"score":2, "evidence":"no-exec-artifact: 指派/选址为整数规划精确算法，收敛由方法内在保证(默认2)。"},
 "L3.4": {"score":1, "evidence":"no-exec-artifact: validation_plan.multi_seed n_runs=5、seeds=[42,123,456,789,1024] 固定，但仅述‘确定性算法逐位一致’，未给 cv<10% 等稳定性判据，缺一项。"},
 "L3.5": {"score":1, "evidence":"no-exec-artifact: experiments X1-X5 expected_outputs 命名关键输出量(最大响应/覆盖缺口/全封锁时间/改善后响应/围堵完成时间)，与题面物理量级相符。"},
 "L4.1": {"score":0, "evidence":"validations V1-V4 为退化/极限/灵敏度/可复现性校验，无任何零模型/随机基线/文献基准/贪婪启发式等对照基线，亦无 baseline 对比结论。"},
 "L4.2": {"score":2, "evidence":"V2 与 validation_plan.sensitivity 对车速±20%、道路长度±10%、嫌疑车速±20%扰动，报告方案稳定性与围堵余量(弹性)。"},
 "L4.3": {"score":1, "evidence":"no-exec-artifact: validation_plan.limit_tests LT1-LT4 及 V3 提供≥2类极限/退化检验(车速→∞、平台数→节点数、Δ→∞、嫌疑车速→0)，满足≥1类(满分1)。"},
 "L4.4": {"score":2, "evidence":"V1-V4 覆盖 O1-O5 全部核心主张(管辖最优/全封锁可行/新增平台/六区不均衡/围堵完成)，验证指标对应子问题。"},
 "L4.5": {"score":2, "evidence":"claims C1-C5 均有 evidence_refs 指向 X/V 可解析；claim_evidence_map 状态 supported/hypothesis，无 unsupported/未解析引用。"},
}
json.dump(mk("3ff350bf-766e-4b15-874e-bc192ef91276", d, [], "SV臂结构化+验证计划。L4.1缺对照基线(仅退化/极限校验)；L3.4固定seed但无cv判据；L4.3仅按二档记1。"), open(os.path.join(OUT,"3ff350bf-766e-4b15-874e-bc192ef91276.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- 7c69dee1 ----------------
d = {
 "L1.1": {"score":1, "evidence":"P1-P8 提取了多数显式条件，但存在明显错误：P2清洗时间写成‘一道35s/二道30s’应为25/30/25；P3上下料时间写20应为奇偶28-32/31-35/32；P1加工时间‘一道560s；二道560s/280s’混淆一二工序(应为一560/580/545、一二道400/280/455与378/500/182)；且未提取题面明示的故障排除10-20min(600-1200s)作为显式参数。错误率>30%。"},
 "L1.2": {"score":2, "evidence":"A1(单RGV串行)、A2(CNC状态机)、A3(故障1%独立)、A4(移动线性)、A5(修复忽略)识别题面隐含状态机与随机故障条件，并给推导依据。"},
 "L1.3": {"score":1, "evidence":"objectives O1-O4 覆盖任务1模型+算法、任务2三组检验及效率；但同04fc未显式列出‘填入附件2 EXCEL表(3工作表)’交付规格。"},
 "L1.4": {"score":1, "evidence":"validation_plan.ambiguity_handling 标注4处歧义(RGV优先级/修复时长/两道缓冲/班末统计)并给采纳方案，歧义已处理。"},
 "L1.5": {"score":2, "evidence":"model_family.primary=dynamic_programming/secondary=optimization/MDP，RGV调度判为事件驱动DP+随机MDP，与调度/序贯决策范式一致。"},
 "L2.1": {"score":2, "evidence":"V1-V7 区分 state/decision/derived/observation(位置/状态/剩余时间/动作/产量/空闲率/故障事件)，关键变量齐全。"},
 "L2.2": {"score":1, "evidence":"P1-P8 均声明 source 与取值，符号在方程中可解析；但多处取值错误(清洗35/30、上下料20、加工时间混淆)，内容不正确(格式中立下字段齐全但值错)。"},
 "L2.3": {"score":2, "evidence":"A1-A5 显式分类(mechanism/simplification/calibration/mechanism_assumption)且带 rationale；A5修复忽略偏乐观已说明。"},
 "L2.4": {"score":2, "evidence":"O1-O4 max N_prod 覆盖无故障/故障/一道/两道，与题面目标一致；目标被机制M1-M4支撑，约束不冲突。"},
 "L2.5": {"score":2, "evidence":"C1(单服务)、C2(工序)、C3(时间窗)、C4(故障状态)、C5(刀具)方向正确。"},
 "L2.6": {"score":3, "evidence":"E1机理-题面：事件驱动DP正确刻画调度；E2机理-方程：E1-E4由机制导出；E3机理-目标/约束：机制支撑产量目标且故障约束入C；E4候选对比4个(DP/optimization/MDP/simulation)含依据，四要素全满足。"},
 "L2.7": {"score":2, "evidence":"E1-E4 含状态转移/价值递推/期望递推/节拍方程与 derivation_trace，符号集⊆variables/parameters，可求解。"},
 "L3.1": {"score":2, "evidence":"S1事件驱动前向搜索、S2滚动重调度、S3蒙特卡洛、S4节拍分析，与DP/MDP模型口径匹配。"},
 "L3.2": {"score":2, "evidence":"no-exec-artifact: S1-S4 带 implementation_ref(pseudocode: event simulation/greedy pruning/replan at fault/line balance)，算法步骤可查，可执行性有据。"},
 "L3.3": {"score":2, "evidence":"no-exec-artifact: V5 声明‘调度搜索深度/剪枝阈值收敛：产量对阈值不敏感’收敛判据；DP为精确递推，收敛内在保证。"},
 "L3.4": {"score":2, "evidence":"no-exec-artifact: validation_plan.multi_seed n_runs=5、seeds=[42,43,44,45,46] 固定、tolerance cv<10%、result cv≈4.2%，多种子+固定seed+判据齐全。"},
 "L3.5": {"score":1, "evidence":"no-exec-artifact: claim C2‘期望产量损失约1~3件/班’、X1-X2 expected_outputs 给产量量级，与题面物理量级相符。"},
 "L4.1": {"score":2, "evidence":"V1 以‘固定轮询顺序策略’为基线对比DP策略产量提升，并报告对比结论。"},
 "L4.2": {"score":2, "evidence":"V3 故障率0.5%~2%扫描 + validation_plan.sensitivity(P7/P4/P1 ±20%)扰动，报告产量损失曲线与弹性。"},
 "L4.3": {"score":1, "evidence":"no-exec-artifact: V4 与 validation_plan.limit_tests LT1-LT4 提供≥2类极限(移动→0/故障率→0/加工→∞/班次→0)，满足≥1类(满分1)。"},
 "L4.4": {"score":2, "evidence":"V1-V5 覆盖 O1-O4 核心主张(无故障产量/故障损失/一般模型/两道瓶颈)，验证指标对应子问题。"},
 "L4.5": {"score":2, "evidence":"claims C1-C3 均 supported，evidence_refs 指向 X/V 可解析，claim_evidence_map 全部 supported，无 unresolved。"},
}
json.dump(mk("7c69dee1-bb5e-4bcf-95ed-626914296c07", d, ["FM-PA-003"], "DP版RGV模型。L1.1/L2.2参数值明显错误(清洗/上下料/加工时间混淆且漏故障排除时长)；L4.1有轮询基线。"), open(os.path.join(OUT,"7c69dee1-bb5e-4bcf-95ed-626914296c07.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- c37459ee ----------------
d = {
 "L1.1": {"score":2, "evidence":"§1显式条件列出：天为基、第0天起点、截止前到达、水/食物箱单位、负重上限、耗尽判负、天气三态、停留1/行走2/挖矿3倍、起点购一次、终点半价退、矿山收益、村庄2倍、多人2k/3k/4k，覆盖题面全部显式规则。"},
 "L1.2": {"score":2, "evidence":"§隐式条件：相邻区域(公共边)才移动、行动需资源可行、未到终点耗尽判负、多人信息结构，识别题面隐含约束并给依据。"},
 "L1.3": {"score":1, "evidence":"§子问题分解识别Q1-Q3及六关(第一/二/三/四/五/六关)交付，但题面‘将结果分别填入Result.xlsx’的具体文件交付规格未在产物中显式列出(锚定C：主要交付物已识别，Result.xlsx格式规格遗漏)。"},
 "L1.4": {"score":1, "evidence":"§歧义点显式标注3处(天气转移未知/最优策略口径取期望资金/多人均衡概念)并各给处理方案。"},
 "L1.5": {"score":2, "evidence":"判定为‘多阶段随机序贯决策(资源-资金联合调度)’，Q1确定DP、Q2随机DP/MDP、Q3多人随机博弈，与问题类型一致。"},
 "L2.1": {"score":2, "evidence":"§3 变量表 V1-V12(t/l_t/w_t/f_t/m_t/s_t/a_t/q_w/q_f/k/g_t/b_t)区分状态/决策/观测/导出类型，关键变量齐全。"},
 "L2.2": {"score":2, "evidence":"§4 参数表 P(基础消耗/行走倍数2/挖矿倍数3/负重/单箱重/基准价/村庄倍数2(4)/退回0.5/基础收益/截止T/转移矩阵/玩家数n)均标 source(题面/校准)。"},
 "L2.3": {"score":2, "evidence":"§2 A1-A6 显式分类(simplification/mechanism/calibration)且每条带合理性说明与误差影响。"},
 "L2.4": {"score":2, "evidence":"§5 Q1-Q3 max m_{T+1}/E[m]/Σm，与题面‘保留尽可能多资金’目标一致；目标被DP机制支撑，约束不冲突。"},
 "L2.5": {"score":2, "evidence":"§6 约束表：负重≤/存活≥/截止≤/沙暴停留/起点购一次/矿山时序/多人规则，方向正确。"},
 "L2.6": {"score":3, "evidence":"E1机理-题面：多阶段DP正确；E2机理-方程：E1-E6由递推结构导出；E3机理-目标/约束：机制支撑资金目标且多人规则入约束；E4候选对比4个(DP价值迭代/MDP/混合整数规划对照/强化学习不采用)含依据，四要素全满足。"},
 "L2.7": {"score":2, "evidence":"§8 E1-E6(消耗/资金转移/Q1递推/Q2期望递推/Q3倍数/博弈递推)含初始与终止条件，符号集⊆变量/参数，可求解。"},
 "L3.1": {"score":2, "evidence":"§9 Q1后向价值迭代、Q2随机价值迭代、Q3对称策略迭代，与DP/MDP模型口径匹配。"},
 "L3.2": {"score":2, "evidence":"no-exec-artifact: §9 给出算法步骤(状态5维网格化、复杂度O(T·|L|·网格³)、消耗步长压缩网格)与输出约定(逐日策略表)，可执行性有据可查。"},
 "L3.3": {"score":2, "evidence":"no-exec-artifact: §验证方案5‘价值迭代残差阈值、策略迭代策略变化量单调递减’声明收敛判据；价值迭代为精确算法。"},
 "L3.4": {"score":2, "evidence":"no-exec-artifact: §可复现性‘固定5组随机数初值抽样天气路径与均衡初值’+§验证‘期望资金标准差<10%均值’，seeds=5固定且cv<10%判据齐全。"},
 "L3.5": {"score":1, "evidence":"no-exec-artifact: §结果合理性预期‘全知比未知高5%~15%、挖矿窗口在资源宽裕时段、多人错峰单玩家略低于单人基准’给出量级范围，与题面物理量级相符。"},
 "L4.1": {"score":1, "evidence":"§验证方案1‘基线：全晴无补给点时应直线直达’为退化/简化情景基线，对比判据已述但属极限式基线而非零模型/随机/贪婪基准，基线较弱。"},
 "L4.2": {"score":2, "evidence":"§验证方案3 对基础消耗、转移概率、基础收益±20%扰动，报告灵敏度。"},
 "L4.3": {"score":1, "evidence":"no-exec-artifact: §验证方案2 提供≥2类极限(W_max→∞购满直达/q_0→0全程挖矿/T→最短路径无挖矿)，满足≥1类(满分1)。"},
 "L4.4": {"score":2, "evidence":"§验证方案(基线/极限/灵敏度/收敛/多初值)覆盖Q1-Q3核心主张(各关策略与合理性)，验证设计对应子问题目标。"},
 "L4.5": {"score":1, "evidence":"叙述式产物无独立claims/evidence_refs结构；结论(全知>未知5-15%等)由模型与验证设计支撑，但无显式claim-evidence图谱，部分预期为假设无计算证据(无执行产物)。"},
}
json.dump(mk("c37459ee-f50b-4a63-b71e-cd7b27cd8130", d, [], "F臂叙述式model_doc。要素齐全；L1.3漏Result.xlsx规格；L4.1仅退化基线；L4.5无显式claim-evidence结构。"), open(os.path.join(OUT,"c37459ee-f50b-4a63-b71e-cd7b27cd8130.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- ff5e9ff0 ----------------
d = {
 "L1.1": {"score":2, "evidence":"§一/三/四 提取题面显式规则与数字：两条并行车道(乘车区)、先来后到排队、分批定量放行、不能拒载、多次往返、优先权；参数(平均车费/里程/单位成本/排队容量/空返里程/短途阈值/航班时段)均标 source，关键显式条件完整。"},
 "L1.2": {"score":2, "evidence":"A1(乘客到达近似泊松/服务指数)、A2(期望收益理性决策)识别题面隐含随机到达与理性人假设，并给推导依据。"},
 "L1.3": {"score":2, "evidence":"§子问题分解 Q1-Q4 对应题面四项交付(决策模型+策略/方案+合理性+依赖性/上车点设置/优先方案)，交付要求已识别。"},
 "L1.4": {"score":1, "evidence":"题面‘优先权’定义模糊，产物经 A5(短途判定按里程阈值)+Q4设计予以识别与处理(未单列歧义节，但实质处理了含糊点)。"},
 "L1.5": {"score":2, "evidence":"判定为‘收益均衡+排队网络(M/M/c)混合框架’，微观经济学+排队论，与出租车司机决策问题类型一致。"},
 "L2.1": {"score":2, "evidence":"V1-V10(W_q/R/C_0/δ/λ_p/λ_t/μ/L/θ/Π)区分 derived/decision/parameter/state/observation 类型，关键变量齐全。"},
 "L2.2": {"score":2, "evidence":"P1-P8(平均车费/里程/单位成本/容量/空返里程/短途阈值/优先比例/航班时段)均标 source(题面/校准/假设)。"},
 "L2.3": {"score":2, "evidence":"A1-A6 显式分类(mechanism/mechanism_assumption/simplification/calibration/projection)且带合理性说明。"},
 "L2.4": {"score":2, "evidence":"Q1估计临界等待、Q2刻画排队、Q3阈值策略、Q4短途优先评价，与题面四项要求一致；目标被收益+排队机制支撑，约束不冲突。"},
 "L2.5": {"score":2, "evidence":"C1(容量L≤K)、C2(稳态λ_t<μ)、C3(决策边界W_q≤W_q*)、C4(0≤θ≤1)、C5(公平下限)方向正确。"},
 "L2.6": {"score":3, "evidence":"E1机理-题面：收益比较+排队联立正确；E2机理-方程：§八公式由机制导出；E3机理-目标/约束：机制支撑收益目标且约束入C；E4候选对比4个(收益+M/M/c/离散事件仿真/博弈论/纯统计回归不采用)含依据，四要素全满足。"},
 "L2.7": {"score":2, "evidence":"§八 E1-E5(收益比较/排队内核L_q,W_q/阈值/短途优先/平均等待)符号集⊆变量/参数，含稳态边界条件，可求解。"},
 "L3.1": {"score":2, "evidence":"§九 Q1附件数据估计、Q2 M/M/c公式、Q3二分法解阈值、Q4注入规则重算+仿真交叉验证，与排队/优化模型匹配。"},
 "L3.2": {"score":2, "evidence":"no-exec-artifact: §九给出算法步骤(由数据估计W_q*、M/M/c公式计算、二分法解阈值、重算)与输出约定，可执行性有据可查。"},
 "L3.3": {"score":2, "evidence":"no-exec-artifact: M/M/c为闭式精确算法，收敛由公式内在保证(默认2)；二分法收敛。"},
 "L3.4": {"score":2, "evidence":"no-exec-artifact: §可复现性‘仿真层固定5组随机数初值(42,123,456,789,1024)运行，报告均值标准差’+§多初值‘标准差<5%’，seeds=5固定且cv判据齐全。"},
 "L3.5": {"score":1, "evidence":"no-exec-artifact: §结果合理性预期‘W_q*在几十分钟量级、短途优先节省30%以上’给出量级范围，与题面物理量级相符。"},
 "L4.1": {"score":2, "evidence":"§验证方案基线‘M/M/c解析结果与离散事件仿真对比，W_q误差<10%’，以离散事件仿真为对照基线并报告对比判据。"},
 "L4.2": {"score":2, "evidence":"§灵敏度 对λ_t,λ_p各±20%、θ±20%扰动，报告W_q*与阈值策略方向不变。"},
 "L4.3": {"score":1, "evidence":"no-exec-artifact: §极限 提供≥2类(λ_t→μ时W_q→∞失稳/θ→0退化为普通排队)，满足≥1类(满分1)。"},
 "L4.4": {"score":2, "evidence":"§验证方案(基线/灵敏度/极限/多初值/公平)覆盖Q1-Q4核心主张(决策边界/排队指标/时段策略/短途优先)，验证设计对应子问题。"},
 "L4.5": {"score":1, "evidence":"叙述式产物无独立claims/evidence_refs结构；结论由模型与验证设计支撑，但无显式claim-evidence图谱(无执行产物，部分结论为预期无计算证据)。"},
}
json.dump(mk("ff5e9ff0-ff50-4de4-b825-67b85cabcc97", d, [], "F臂叙述式model_doc。要素齐全；L4.5无显式claim-evidence结构。"), open(os.path.join(OUT,"ff5e9ff0-ff50-4de4-b825-67b85cabcc97.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- 88bd6407 ----------------
d = {
 "L1.1": {"score":2, "evidence":"P1-P8 覆盖题面显式数字：环境温度(75/65/80)、皮肤37、工作时长(90/60/30min)、各层导热/密度比热(附件1)、各层厚度(0.6,6,3.6,5)mm、对流系数校准、温度约束(47℃,5min)，关键参数完整提取。"},
 "L1.2": {"score":2, "evidence":"A1(一维传热)、A2(各向同性)、A3(对流边界/皮肤37)、A4(空气层等效)、A5(初始37℃)识别题面隐含传热边界与初始条件并给依据。"},
 "L1.3": {"score":2, "evidence":"O1 显式‘生成problem1.xlsx’、O2/O3 确定II层及II+IV最优厚度，题面Q1-Q3交付物(温度分布Excel/最优厚度)均已识别且含具体文件名。"},
 "L1.4": {"score":1, "evidence":"题面传热问题定义明确，无必须标注的关键歧义；MODEL_IR未单列歧义节，按默认给满分(对流系数缺失已由A3/校准处理)。"},
 "L1.5": {"score":2, "evidence":"model_family.primary=heat_transfer/secondary=pde/numerical_optimization，多层一维热传导判定正确，与问题类型一致。"},
 "L2.1": {"score":2, "evidence":"V1-V8(T(x,t)/x/t/T_s/d_2/d_4/τ_>44/T_max)区分state/observation/derived/decision类型，关键变量齐全。"},
 "L2.2": {"score":2, "evidence":"P1-P8 每个参数有 source 与取值(附件1/题面/校准)；方程符号 k_i,ρ_i,c_i,h_conv,d_i,T_amb 均在 parameters 声明集内。"},
 "L2.3": {"score":2, "evidence":"A1-A5 显式分类(simplification/mechanism/mechanism_assumption/calibration)且带 rationale 可检验。"},
 "L2.4": {"score":2, "evidence":"O1 simulate+生成xlsx、O2 min d2 s.t. T_max≤47,τ≤5、O3 min联合 s.t.同约束，与题面Q2/Q3要求一致；目标被热阻机制支撑，约束不冲突。"},
 "L2.5": {"score":2, "evidence":"C1(温度≤47)、C2(超温≤5min)、C3(厚度>0)、C4(0≤T≤T_amb)方向正确无符号错误。"},
 "L2.6": {"score":3, "evidence":"E1机理-题面：傅里叶导热正确；E2机理-方程：E1-E4由机制导出；E3机理-目标/约束：机制支撑温度目标且约束入C；E4候选对比5个(heat_transfer/pde/numerical_optimization/inverse_problem/finite_difference)含依据，四要素全满足。"},
 "L2.7": {"score":2, "evidence":"E1-E4(PDE+对流边界E2+界面连续E3+热阻网络E4)含初始/边界条件，符号集⊆variables/parameters，可求解。"},
 "L3.1": {"score":2, "evidence":"S1 Crank-Nicolson隐式有限差分、S2二分搜索、S3网格+帕累托、S4参数反演，与PDE/优化模型口径匹配。"},
 "L3.2": {"score":2, "evidence":"no-exec-artifact: S1-S4 带 implementation_ref(pseudocode: tridiagonal solve Δx=0.1mm Δt=1s / bisection / grid / least-squares fit)，可执行性有据可查。"},
 "L3.3": {"score":2, "evidence":"no-exec-artifact: V2‘网格细化(Δx/2、Δt/2)检验温度场收敛，误差<0.1℃’声明收敛判据；隐式格式收敛内在保证。"},
 "L3.4": {"score":1, "evidence":"no-exec-artifact: V5‘网格划分与初值扰动下结果稳定(多次重算)’提及多次重算但未固定 seed 也未给 cv 判据(模型确定性，缺显式多种子设计)，缺一项。"},
 "L3.5": {"score":1, "evidence":"no-exec-artifact: X1 expected_outputs‘与附件2误差MAE<0.5℃’、X2/X3‘约束余量T_max,τ’给出量级范围，与题面物理量级相符。"},
 "L4.1": {"score":0, "evidence":"V1 以‘纯导热无对流(h→∞)与绝热(h→0)’为极限边界校验，属极限检验而非对照基线模型(无零模型/随机/文献/贪婪基线对比)。"},
 "L4.2": {"score":2, "evidence":"V3 对 h_conv 与 k_2 各±20%扰动，观察最优厚度与皮肤温度敏感度(弹性系数)。"},
 "L4.3": {"score":1, "evidence":"no-exec-artifact: V4(d_2→∞皮肤→37℃且超温→0、d_4→0退化为三层)及V1极限边界，提供≥1类极限/退化检验(满分1)。"},
 "L4.4": {"score":2, "evidence":"V1-V5 覆盖 O1-O3 核心主张(复现附件2曲线/最小II厚度/II+IV帕累托)，验证指标对应子问题。"},
 "L4.5": {"score":2, "evidence":"claims C1-C3 均 supported，evidence_refs 指向 X/V 可解析，无 unresolved/unsupported。"},
}
json.dump(mk("88bd6407-2bcf-4e01-a28d-efe39bf00273", d, [], "S臂结构化MODEL_IR(无验证计划)。L4.1仅极限边界无对照基线；L3.4未固定seed/cv；L4.3仅二档1。"), open(os.path.join(OUT,"88bd6407-2bcf-4e01-a28d-efe39bf00273.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- 30beb45f ----------------
d = {
 "L1.1": {"score":2, "evidence":"提取题面显式条件：任务位置/定价/完成(附件一)、会员位置/信誉/预订限额(附件二)、新任务位置(附件三)；变量p_i/y_i/x_i/z_i、参数P1/P2(65-90)/P8(信誉s_m)覆盖题面明示数字与结构(预订限额为附件数据，以密度抽象处理)。"},
 "L1.2": {"score":2, "evidence":"A1(完成概率仅由定价/距离/竞争决定)、A2(独立伯努利)、A3(核密度投影)、A4(预算锚定)、A5(打包去内耗)识别题面隐含供需机制并给依据。"},
 "L1.3": {"score":2, "evidence":"objectives O1-O4 对应题面四项交付(规律+原因/新方案+比较/打包修改+影响/新项目方案+评价)，交付要求已识别。"},
 "L1.4": {"score":1, "evidence":"validation_plan.ambiguity_handling 标注3处歧义(距离直线vs路网/打包一组一单/未完成原因口径)并给采纳方案，歧义已处理。"},
 "L1.5": {"score":2, "evidence":"model_family.primary=statistical_modeling/secondary=optimization/clustering，定价-完成判为逻辑回归+预算优化+空间聚类，与问题类型一致。"},
 "L2.1": {"score":2, "evidence":"V1-V14(p_i/y_i/π_i/x_i/z_i/ρ_m/ρ_t/d_i/n_cmp/g_k/q_k/w_j/R/r_i)区分 observation/derived/decision 类型，关键变量齐全。"},
 "L2.2": {"score":2, "evidence":"P1-P8 每个参数有 source(校准/题目/假设)与取值；方程符号 p_i,d_i,n_cmp,β,B,r_pack 均在 parameters 声明集内。"},
 "L2.3": {"score":2, "evidence":"A1-A5 显式分类(mechanism_assumption/simplification/projection/calibration/mechanism)且带 rationale 可检验。"},
 "L2.4": {"score":2, "evidence":"O1估计规律、O2 max完成率预算约束、O3打包、O4新项目外推，与题面一致；目标被效用机制支撑，约束不冲突。"},
 "L2.5": {"score":2, "evidence":"C1(价格区间)、C2(预算∑≤B)、C3(空间邻近)、C4(分组完备)、C5(新预算)方向正确。"},
 "L2.6": {"score":3, "evidence":"E1机理-题面：统计建模+逻辑回归正确；E2机理-方程：E1-E6由效用机制导出；E3机理-目标/约束：机制支撑完成率目标且约束入C；E4候选对比4个(statistical_modeling/optimization/clustering/decision_analysis排除)含依据，四要素全满足。"},
 "L2.7": {"score":2, "evidence":"E1-E6(供需比/逻辑回归/完成率/优化/打包/外推)符号集⊆variables/parameters，可求解。"},
 "L3.1": {"score":2, "evidence":"S1 IRLS逻辑回归、S2边际排序+网格、S3 DBSCAN聚类、S4 bootstrap重抽样，与统计/优化/聚类模型匹配。"},
 "L3.2": {"score":2, "evidence":"no-exec-artifact: S1-S4 带 implementation_ref(pseudocode: IRLS ‖Δβ‖<1e-6 / sort ∂π/∂p / DBSCAN(eps,minPts) / bootstrap 500)，可执行性有据可查。"},
 "L3.3": {"score":2, "evidence":"no-exec-artifact: S1 IRLS 声明收敛判据‘‖Δβ‖<1e-6’；逻辑回归迭代收敛内在保证。"},
 "L3.4": {"score":2, "evidence":"no-exec-artifact: validation_plan.multi_seed n_runs=5、seeds=[42,43,44,45,46]、tolerance cv<10%、result cv≈2.3%，多种子+固定seed+判据齐全。"},
 "L3.5": {"score":1, "evidence":"no-exec-artifact: X2‘完成率提升ΔR’、claim C2‘提升约10%量级’给出量级范围，与题面物理量级相符。"},
 "L4.1": {"score":2, "evidence":"V1 以‘常数概率模型与均值定价’为基线对比逻辑回归R²与AUC，并报告对比判据。"},
 "L4.2": {"score":2, "evidence":"V2 预算±20% + validation_plan.sensitivity(P1/P4/P5)扰动，报告完成率变化率与弹性。"},
 "L4.3": {"score":1, "evidence":"no-exec-artifact: V3(r_pack→0退化)与 validation_plan.limit_tests LT1-LT3(价格→下限/打包半径→0/密度→∞)提供≥2类极限，满足≥1类(满分1)。"},
 "L4.4": {"score":2, "evidence":"V1-V4 覆盖 O1-O4 核心主张(定价规律/新方案提升/打包优于单独/新项目可实施)，验证指标对应子问题。"},
 "L4.5": {"score":2, "evidence":"claims C1-C4 均 supported，evidence_refs 指向 X/V 可解析，claim_evidence_map 全部 supported，无 unresolved。"},
}
json.dump(mk("30beb45f-6835-44f2-8eb8-1f9d7914c120", d, [], "SV臂结构化+验证计划。要素齐全，各维度高分。"), open(os.path.join(OUT,"30beb45f-6835-44f2-8eb8-1f9d7914c120.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- 286218b8 ----------------
d = {
 "L1.1": {"score":2, "evidence":"§1显式条件列出：223节、龙头板长341cm/龙身220cm/板宽30cm/孔径5.5cm/孔心距27.5cm、Q1螺距55cm等距螺线/1m/s/第16圈A点/0-300s每秒、Q2终止时刻、Q3调头直径9m、Q4螺距1.7m/中心对称/两段相切(前半径=后2倍)/-100~100s、Q5速度≤2m/s，全部数字与约束完整提取。"},
 "L1.2": {"score":2, "evidence":"§隐式条件：等距螺线极径随极角线性、相邻把手距离=板长、把手沿螺线落位、调头圆边界限制最内半径、速度由曲率链式放大，识别题面隐含几何约束并给依据。"},
 "L1.3": {"score":2, "evidence":"§1 显式识别 Q1 result1.xlsx(模板,保留6位小数)、Q2 result2.xlsx、Q4 result4.xlsx 及特定时刻(0,60,...,300s；-100~100s)交付规格，文件格式/精度/时间范围/附件均覆盖(锚定C满分)。"},
 "L1.4": {"score":1, "evidence":"§歧义点显式标注3处(A点极角取32π/碰撞判据取法向间隙<板宽/调头切点作自由变量)并各给处理方案。"},
 "L1.5": {"score":2, "evidence":"判定为‘平面曲线几何与约束优化(螺线/圆弧几何关系+相切约束最值)’，与板凳龙问题类型一致。"},
 "L2.1": {"score":2, "evidence":"§3 变量表(极径r/极角θ/曲率半径ρ/把手点P_i/把手速度v_i/圈间隙g/调头弧长s_T/圆弧半径(R1,R2)/速度比κ_i)区分状态/派生/决策类型，关键变量齐全。"},
 "L2.2": {"score":2, "evidence":"§4 参数表(龙头板长3.41/龙身2.20/板宽0.30/节数223/龙头速度1/初始圈16/调头圆半径4.5/半径比2.0/螺距/速度上限2)均标 source=题面给定。"},
 "L2.3": {"score":2, "evidence":"§2 B1-B5 显式分类(mechanism/simplification/calibration)且带合理性说明与误差影响。"},
 "L2.4": {"score":2, "evidence":"§5 Q1仿真/Q2终止时刻/Q3最小螺距/Q4最短弧长/Q5最大龙头速度，与题面五项要求一致；目标被几何机制支撑，约束不冲突。"},
 "L2.5": {"score":2, "evidence":"§6 约束：螺线=、弦长=L_i、间隙≥w、调头边界=4.5、相切R1=2R2、速度≤2，方向正确。"},
 "L2.6": {"score":3, "evidence":"E1机理-题面：螺线/圆弧几何正确；E2机理-方程：§8六式由几何导出；E3机理-目标/约束：机制支撑最值目标且约束入C；E4候选对比3个(纯几何/数值优化/动力学仿真弃用)含依据，≥2候选满足四要素。"},
 "L2.7": {"score":2, "evidence":"§8 E1-E6(螺线/曲率/间隙/弦长/调头弧长/速度放大)含解析形式，符号集⊆变量/参数，可求解。"},
 "L3.1": {"score":2, "evidence":"§9 几何量解析公式、弦长牛顿迭代、最小螺距网格扫描后精化、调头一维搜索，与几何/优化模型口径匹配。"},
 "L3.2": {"score":2, "evidence":"no-exec-artifact: §9 给出算法步骤(解析公式/牛顿迭代弦长/网格扫描/一维搜索 R_2)与输出约定，可执行性有据可查。"},
 "L3.3": {"score":2, "evidence":"no-exec-artifact: §验证‘积分容差与网格加密验证’声明收敛判据；牛顿迭代收敛内在保证。"},
 "L3.4": {"score":2, "evidence":"no-exec-artifact: §可复现性‘固定积分容差与网格设置；同输入重复运行一致’+§验证‘稳定性：重复运行逐位一致’，确定性几何模型等价声明可复现(无随机无需seed)。"},
 "L3.5": {"score":1, "evidence":"no-exec-artifact: §合理性预期‘最小螺距略大于板宽、调头弧长小于原始、Q5速度上限1.5~2m/s’给出量级范围，与题面物理量级相符。"},
 "L4.1": {"score":2, "evidence":"§验证基线‘圆弧路径解析解对照；直线极限对照’，以解析解/直线极限为对照基线并报告对比判据。"},
 "L4.2": {"score":2, "evidence":"§灵敏度 对板宽±10%、半径比±10%扰动，观察关键输出。"},
 "L4.3": {"score":1, "evidence":"no-exec-artifact: §极限 提供≥2类(p→∞曲率→0放大→1 / w→0终止→∞)，满足≥1类(满分1)。"},
 "L4.4": {"score":2, "evidence":"§验证方案(基线/收敛/灵敏度/极限/稳定性)覆盖Q1-Q5核心主张(位形仿真/终止时刻/最小螺距/最短调头/最大速度)，验证设计对应子问题。"},
 "L4.5": {"score":1, "evidence":"叙述式产物无独立claims/evidence_refs结构；结论由几何与验证设计支撑，但无显式claim-evidence图谱(无执行产物，部分结论为预期无计算证据)。"},
}
json.dump(mk("286218b8-48f4-4f12-9e99-53d23e896c64", d, [], "F臂叙述式model_doc。L1.3满分(识别xlsx/6位小数/时刻)；L4.5无显式claim-evidence结构。"), open(os.path.join(OUT,"286218b8-48f4-4f12-9e99-53d23e896c64.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

print("calibration written:", 8)
