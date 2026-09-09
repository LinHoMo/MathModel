# -*- coding: utf-8 -*-
"""Write phase-2 (formal shard) evaluation score files for evaluator E06.
Independent blind scoring; no contact with generation side.
rubric_version: MODEL_CONSTRUCTION_RUBRIC-v1.1a (anchor K002).
"""
import json
import os
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def d(*pairs):
    """pairs: (dim_key, score, evidence)"""
    out = {}
    for k, s, e in pairs:
        out[k] = {"score": s, "evidence": e}
    return out

def vec(dims):
    order = [("L1.1","L1.2","L1.3","L1.4","L1.5"),
             ("L2.1","L2.2","L2.3","L2.4","L2.5","L2.6","L2.7"),
             ("L3.1","L3.2","L3.3","L3.4","L3.5"),
             ("L4.1","L4.2","L4.3","L4.4","L4.5")]
    sums = []
    for layer in order:
        sums.append(sum(dims[k]["score"] for k in layer))
    return {"L1": sums[0], "L2": sums[1], "L3": sums[2], "L4": sums[3]}

def write(uuid, dims, notes):
    rec = {
        "submission_id": uuid,
        "evaluator": {
            "model": "E06",
            "type": "independent_llm",
            "version": "1.0",
            "timestamp": TS
        },
        "rubric_version": "MODEL_CONSTRUCTION_RUBRIC-v1.1a",
        "dimensions": dims,
        "vector": vec(dims),
        "failure_modes": [],
        "notes": notes
    }
    path = os.path.join(BASE, "scores", uuid + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    return path

# ---------------------------------------------------------------------------
# 98ae4334 - 2019_C 机场出租车, m-ab8fb45c, MODEL IR, NO Validation Plan
# ---------------------------------------------------------------------------
write("98ae4334-6c12-4ce8-ae34-0454cac5b68c", d(
    ("L1.1", 2, "题面 Q1-Q4 显式提取：Q1 司机选择策略、Q2 收集机场数据给方案、Q3 上车点设置（双车道）、Q4 短途优先权均衡；problem_binding.sub_question_id='Q1,Q2,Q3,Q4' 与题面四问对应。"),
    ("L1.2", 2, "隐式条件识别：A2 将'航班与蓄车池车辆数可观测'投影为等待时间点估计；A3 到达近似泊松；P2/P3 参数'按机场-市区距离校准'体现数据缺失的隐式处理。"),
    ("L1.3", 1, "交付要求识别仅到'收集数据给出选择方案'层级，题面 Q2 未要求具体文件名，产物未给出具体表格/文件规格，判 1。"),
    ("L1.4", 0, "产物无 ambiguity_handling 章节，亦无歧义点标注字段，判 0。"),
    ("L1.5", 2, "model_family.primary='decision_analysis' 且 candidates 含 queueing_theory/game_theory；类型判定为决策分析+排队+博弈，与题面落点一致，判 2。"),
    ("L2.1", 2, "variables V1-V12 覆盖 W,R_q,R_e,a,γ,λ_p,λ_t,c,E_load,φ_i,G_i,G 等，类型/单位/子问题绑定齐全，判 2。"),
    ("L2.2", 2, "parameters P1-P7 含 c_w=30、l_s=6、μ、γ_0=0.6、Φ 等，source 标注文献/校准/假设，判 2。"),
    ("L2.3", 2, "assumptions A1-A5 均有 type 与 rationale，如 A1 期望效用者、A4 优先权不改变里程分布，合理，判 2。"),
    ("L2.4", 2, "objectives O1-O4 正确：O1 max U(a)、O3 max E_load、O4 min Gini，与题面四问目标对应，判 2。"),
    ("L2.5", 2, "constraints C1-C5：选择集、稳定性 λ_t<μ、安全车道≤2、等待 W_p≤W_max、优先权档位，覆盖题面约束，判 2。"),
    ("L2.6", 3, "candidates 含 5 个对比（decision_analysis/queueing/game/optimization/simulation）且各自 rationale 与弃用理由明确，E1-E4 与 M1-M4 机理-方程一致，判 3。"),
    ("L2.7", 2, "equations E1-E4：均值-方差效用、M/M/1 等待、Erlang-C、优先权收益递推，结构完整且 variables_refs 齐全，判 2。"),
    ("L3.1", 2, "solvers S1-S4：效用比较解析、分段扫描、Erlang-C 枚举 c∈{1,2}、优先权网格搜索，与 O1-O4 匹配，判 2 [no-exec-artifact]。"),
    ("L3.2", 2, "solvers 含 implementation_ref 'pseudocode: compare U_q vs U_e per hour' 等可执行伪代码，设计完备，判 2 [no-exec-artifact]。"),
    ("L3.3", 2, "S1 效用比较为解析解、S3 Erlang-C 枚举为精确算法，无迭代收敛风险；默认精确算法 2 分，判 2 [no-exec-artifact]。"),
    ("L3.4", 1, "无 Validation Plan / multi_seed；V4 仅叙述'多种子重抽样模拟'未列固定种子值与 cv 判据，可复现性设计仅叙述级，判 1 [no-exec-artifact]。"),
    ("L3.5", 1, "claims C1-C4 含'存在临界等待时间''双车道提升约30%''基尼降低约25%'等可检验合理性预期，判 1 [no-exec-artifact]。"),
    ("L4.1", 2, "V1 以'全部排队''全部空驶'两个极端基线比较验证混合策略不劣于任一极端，基线对照明确，判 2 [no-exec-artifact]。"),
    ("L4.2", 2, "V2 风险厌恶 γ 与等待成本 c_w 各 ±20% 观察决策边界移动；覆盖 O1，判 2 [no-exec-artifact]。"),
    ("L4.3", 1, "V3 极限 λ_p→0 时 E_load→0、λ_p→∞ 双车道仍优于单车道，边界行为正确，判 1 [no-exec-artifact]。"),
    ("L4.4", 2, "V1→O1/O2、V2→O1、V3→O3、V4→O4，覆盖 Q1-Q4 全部子问题目标，判 2 [no-exec-artifact]。"),
    ("L4.5", 2, "claims C1-C4 各含 evidence_refs（X1-X4,V1-V4）与 status:'supported'，构成结构化主张-证据映射，判 2。"),
), "2019_C 机场出租车；MODEL IR m-ab8fb45c；无 Validation Plan/ambiguity_handling；L4.5 因内嵌 claims 数组(含 evidence_refs+status)判 2。")

# ---------------------------------------------------------------------------
# 610461e3 - 2011_B 交巡警, m-da0260a6, MODEL IR + Validation Plan
# ---------------------------------------------------------------------------
write("610461e3-2a25-4888-8f02-bad0e7067ef4", d(
    ("L1.1", 2, "题面 Q1-Q5 显式提取：管辖分配、13要道封锁、增2-5平台、六区合理性、P点围堵；problem_binding.sub_question_id='Q1,Q2,Q3,Q4,Q5'。"),
    ("L1.2", 2, "隐式条件：A1 边权=长度/速度折算时间、A4 嫌疑犯沿最短路逃逸速度与警车相同、P7 W=附件2各表，识别题面隐含的路网图结构。"),
    ("L1.3", 1, "交付为方案类（管辖/调度/选址/围堵），题面未指定具体 Excel 文件名；产物 X4 提及'六区路网:5张表'但非交付文件名，判 1。"),
    ("L1.4", 1, "VP.ambiguity_handling 含 3 项：'3分钟内到达'软硬、工作量度量、围堵成功判据，各列 interpretations/adopted/justification，判 1。"),
    ("L1.5", 2, "primary='graph_algorithm' + secondary optimization；类型判定与题面路网图问题一致，判 2。"),
    ("L2.1", 2, "variables V1-V10：d_ij,x_ij,l_i,m_ik,T_B,Z,R(t),C,t_e,κ，覆盖 Q1-Q5，判 2。"),
    ("L2.2", 2, "parameters P1-P7：v=60,t_0=3,n_p=20,n_k=13,[n_-,n_+]=[2,5],Δ=3,W=附件2，source 题面，判 2。"),
    ("L2.3", 2, "assumptions A1-A5 含 type+rationale（如 A2 一对一匹配为硬约束），合理，判 2。"),
    ("L2.4", 2, "objectives O1-O5：最小化最大响应、瓶颈封锁时间、增补选址、覆盖率估计、围堵封口数，判 2。"),
    ("L2.5", 2, "constraints C1-C5：划分、时限、匹配、数量、围堵时序，覆盖题面，判 2。"),
    ("L2.6", 3, "candidates 4 个对比且 rationale 明确；M1-M4 与 E1-E4 机理-题面-方程一致，判 3。"),
    ("L2.7", 2, "equations E1-E4：Dijkstra、瓶颈匹配、覆盖增补、可达集扩张，结构完整，判 2。"),
    ("L3.1", 2, "solvers S1-S4：全源Dijkstra、瓶颈匹配(二分+匈牙利)、组合枚举+贪心、可达集扩张，与 O1-O5 匹配，判 2 [no-exec-artifact]。"),
    ("L3.2", 2, "solvers 含 implementation_ref 'pseudocode: heap-Dijkstra per source' 等可执行伪代码，判 2 [no-exec-artifact]。"),
    ("L3.3", 2, "Dijkstra、匈牙利为精确算法，默认 2 分；无迭代收敛风险，判 2 [no-exec-artifact]。"),
    ("L3.4", 2, "VP.multi_seed：n_runs=5，seeds=[42,43,44,45,46] 固定，tolerance cv<10%（实测 κ cv≈0.5%、|C| cv≈8.5%），可复现性机械支撑充分，判 2 [no-exec-artifact]。"),
    ("L3.5", 1, "claims C1-C5 含'覆盖率约92%''最晚封锁约8分钟''新增3-4平台消除超时'等可检验预期，判 1 [no-exec-artifact]。"),
    ("L4.1", 2, "V1 以'就近贪心管辖'为基线比较瓶颈指派 τ_max 与负荷方差，判 2 [no-exec-artifact]。"),
    ("L4.2", 2, "VP.sensitivity 3 项：v 50~70、Δ 1~5、t_0 2~4，one_at_a_time 覆盖 O1/O2/O5，判 2 [no-exec-artifact]。"),
    ("L4.3", 1, "VP.limit_tests LT1-LT3：v→∞ 出警归零、|Z|=2/5 单调、Δ→0 保守上界，边界行为正确，判 1 [no-exec-artifact]。"),
    ("L4.4", 2, "V1→O1、V2→O2/O1、V3→O3、V4→O5、V5→O3/O4，覆盖 Q1-Q5 全部目标，判 2 [no-exec-artifact]。"),
    ("L4.5", 2, "VP.claim_evidence_map C1-C5 各含 evidence_ref 与 status:'supported'，结构化映射完整，判 2。"),
), "2011_B 交巡警；MODEL IR m-da0260a6 + Validation Plan；SV臂5固定种子+cv<10%→L3.4=2；claim_evidence_map 全 supported→L4.5=2。")

# ---------------------------------------------------------------------------
# 9e8fc965 - 2022_C 古代玻璃, model_doc, NO Validation Plan
# ---------------------------------------------------------------------------
write("9e8fc965-0a2c-427e-9832-685694340a03", d(
    ("L1.1", 2, "题面 Q1-Q4 显式提取：风化关系与风化前成分预测、分类规律与亚类划分、未知鉴别、关联比较；§1 显式条件列出有效区间85-105%、两类标签、表单1-3。"),
    ("L1.2", 2, "隐式条件识别：§1 隐式条件含成分闭包性质(和=100%)、风化元素交换、未风化点保留配方、空白非0，识别充分，判 2。"),
    ("L1.3", 1, "交付为分析报告/划分结果，题面未指定具体文件名；产物未给出表格/文件规格，判 1。"),
    ("L1.4", 1, "§1 歧义点 ①②③ 明确标注：风化前成分无观测用未风化点代理、'合适成分'未指定用主成分自动识别、未知鉴别无真值用交叉验证，判 1。"),
    ("L1.5", 2, "§1 判定为'成分数据统计模式识别，含回归复原/降维聚类/判别分类/相关比较'，类型准确，判 2。"),
    ("L2.1", 2, "§3 变量 W_i,T_i,(D_i,C_i),x_ij,S_i,t_ik,p_jk,x̂_ij,Z_i,D_Mi 覆盖 Q1-Q4，判 2。"),
    ("L2.2", 2, "§4 参数 [L_lo,L_hi]=[85,105]、η=0.85、K、χ²_0.95、|p|*=0.4、e_tol=3% 含取值与来源，判 2。"),
    ("L2.3", 2, "§2 假设 B1-B5 含类型与'误差影响'列，合理（如 B3 线性偏移残差约2个百分点），判 2。"),
    ("L2.4", 2, "§5 目标 Q1估计风化前、Q2最小化聚类、Q3最小化错分、Q4估计谱结构，与题面对应，判 2。"),
    ("L2.5", 2, "§6 约束 数据有效性/载荷正交/方差占比/亚类互斥/归属唯一，覆盖，判 2。"),
    ("L2.6", 3, "§7 候选对比 候选1主成分+马氏(选)、候选2全成分LDA(弃,病态)、候选3逻辑回归(对照)，机理-题面一致，判 3。"),
    ("L2.7", 2, "§8 方程 1-5：主成分分解、得分复原、得分聚类、马氏判别、谱分解，结构完整，判 2。"),
    ("L3.1", 2, "§9 求解策略：SVD求主成分、低维最小二乘复原、马氏距离判别、两次特征分解，与 Q1-Q4 匹配，判 2 [no-exec-artifact]。"),
    ("L3.2", 2, "§9 给出算法与复杂度(O(p²n)等)但无 implementation_ref/伪代码文件；设计可理解，判 2 [no-exec-artifact]。"),
    ("L3.3", 2, "SVD/特征分解为精确算法，聚类迭代注明'终止条件:聚类迭代收敛'，收敛判据明确，默认 2 分，判 2 [no-exec-artifact]。"),
    ("L3.4", 1, "§9 仅叙述'聚类多起点固定、Bootstrap重采样固定流程'，未列固定种子值、未给 cv 判据，可复现性仅叙述级，判 1 [no-exec-artifact]。"),
    ("L3.5", 1, "§9 合理性预期：第一主成分解释>40%、PbO/BaO载荷显著、复原误差2-3%、错分率<10%，可检验，判 1 [no-exec-artifact]。"),
    ("L4.1", 2, "§9 基线：得分空间复原 vs 原始空间回归、马氏判别 vs 多数类基线，对照明确，判 2 [no-exec-artifact]。"),
    ("L4.2", 2, "§9 灵敏度：保留方差比 η 0.75~0.90 扰动观察亚类成员变化率，覆盖 Q2，判 2 [no-exec-artifact]。"),
    ("L4.3", 1, "§9 极限：η→1 复原收敛全空间、d→0 收敛未风化均值，边界行为正确，判 1 [no-exec-artifact]。"),
    ("L4.4", 2, "§9 基线/灵敏度/极限/稳定性(Bootstrap100次)覆盖 Q1-Q4 全部子问题，判 2 [no-exec-artifact]。"),
    ("L4.5", 1, "无结构化 claim_evidence_map；仅叙述式'合理性预期'，主张-证据对应为叙述级，判 1。"),
), "2022_C 古代玻璃；model_doc（PCA+马氏距离）；有歧义点章节(§1)→L1.4=1；无 VP/claim map→L3.4=1,L4.5=1。")

# ---------------------------------------------------------------------------
# 8ce21ea3 - 2011_B 交巡警, model_doc, NO Validation Plan
# ---------------------------------------------------------------------------
write("8ce21ea3-db20-456e-9c81-5fe7ceda8bbb", d(
    ("L1.1", 2, "§1 子问题分解 Q1-Q5 显式：管辖分配、封锁13要道、增2-5平台、六区评估、P点围堵；显式条件列出路口/速度60/平台20/要道13/P=32。"),
    ("L1.2", 2, "隐式条件识别：§1 列'警车沿最短路、3分钟覆盖阈值、封锁一对一、嫌疑车速未给定'，识别题面隐含，判 2。"),
    ("L1.3", 1, "交付为方案类，题面未指定具体文件名；产物未给出文件规格，判 1。"),
    ("L1.4", 1, "§1 歧义点：'尽量3分钟'软硬、嫌疑车速、围堵时间原点 三项标注并给出采纳方案，判 1。"),
    ("L1.5", 2, "§1 判定'图算法(最短路径+指派/选址)+组合优化+多指标统计'，与题面一致，判 2。"),
    ("L2.1", 2, "§3 变量 v_i,t_ij,x_kj,y_kl,T_max,z_j,w_k,θ,R(t) 覆盖 Q1-Q5，判 2。"),
    ("L2.2", 2, "§4 参数 v_p=60,T_3=3,m_A=20,n_g=13,Δ=[2,5],l_ij,τ_d=3,v_s=60 含取值来源，判 2。"),
    ("L2.3", 2, "§2 假设 A1-A5 含类型与合理性（如 A4 嫌疑车速灵敏度），判 2。"),
    ("L2.4", 2, "§5 目标 Q1最小化T_max、Q2最小化封锁时间、Q3最小化最大响应、Q4估计、Q5封锁出口，判 2。"),
    ("L2.5", 2, "§6 约束 全覆盖、响应时限、一对一、新增预算、封锁时限，覆盖，判 2。"),
    ("L2.6", 3, "§7 候选对比 4 项（最短路+指派(选)、连续几何选址(弃)、空间聚类(弃)、纯仿真(弃)）且弃用理由明确，判 3。"),
    ("L2.7", 2, "§8 方程 最短时间/管辖min-max/封锁指派/选址/可达域/出口封锁 6 式结构完整，判 2。"),
    ("L3.1", 2, "§9 求解策略：全源最短路+最近分配、匈牙利/瓶颈指派、枚举选址、可达域扩张，与 Q1-Q5 匹配，判 2 [no-exec-artifact]。"),
    ("L3.2", 2, "§9 给出算法与复杂度(O(N³)等)及求解器终止条件描述，但无伪代码文件/implementation_ref，判 2 [no-exec-artifact]。"),
    ("L3.3", 2, "匈牙利/瓶颈指派为精确算法，枚举选址为组合精确，默认 2 分，判 2 [no-exec-artifact]。"),
    ("L3.4", 1, "§9 仅叙述'整数规划固定求解器终止条件与随机数初始化方案，5组初始化报告一致性与均值±标准差'，未列固定种子值、无 cv 判据，判 1 [no-exec-artifact]。"),
    ("L3.5", 1, "§9 合理性预期：多数路口3分钟可达、13要道可全封锁、新增3-4平台改善、P点围堵时限内，可检验，判 1 [no-exec-artifact]。"),
    ("L4.1", 2, "§9 退化对照：单平台单节点、直线路网、完全图退化，作基线校正，判 2 [no-exec-artifact]。"),
    ("L4.2", 2, "§9 灵敏度：车速±20%、路长±10%、嫌疑车速±20%，覆盖 Q1-Q5，判 2 [no-exec-artifact]。"),
    ("L4.3", 1, "§9 极限：v_p→∞ 响应→0、平台数→节点数 覆盖完备、Δ→∞ 最大响应单调不增，边界正确，判 1 [no-exec-artifact]。"),
    ("L4.4", 2, "§9 退化对照+灵敏度+极限覆盖 Q1-Q5 全部子问题，判 2 [no-exec-artifact]。"),
    ("L4.5", 1, "无结构化 claim_evidence_map；仅叙述式合理性预期，判 1。"),
), "2011_B 交巡警；model_doc（图算法+组合优化）；有歧义点章节(§1)→L1.4=1；无 VP/claim map→L3.4=1,L4.5=1。")

# ---------------------------------------------------------------------------
# 580d7b71 - 2020_B 穿越沙漠, m-75e2d454, MODEL IR, NO Validation Plan
# ---------------------------------------------------------------------------
write("580d7b71-d8f5-4413-9be6-128e18c26797", d(
    ("L1.1", 2, "题面 Q1-Q3 显式提取（全知最优/在线策略/多人）；problem_binding.sub_question_id='Q1,Q2,Q3'；Q1 明确'填入Result.xlsx'。"),
    ("L1.2", 2, "隐式条件：A2 天气马尔可夫一阶、A4 起点仅购一次/终点退回半价、P11 天气转移概率，识别题面规则(3)(4)(6)(7)等隐式约束。"),
    ("L1.3", 2, "Q1 明确交付'将结果分别填入Result.xlsx'，产物识别该文件名，判 2。"),
    ("L1.4", 0, "产物无 ambiguity_handling 章节/歧义点字段，判 0。"),
    ("L1.5", 2, "primary='dynamic_programming'+secondary optimization/game_theory；类型判定与多阶段序贯决策一致，判 2。"),
    ("L2.1", 2, "variables V1-V12：t,l_t,w_t,f_t,m_t,s_t,a_t,q_w,q_f,k,g_t,b_t 覆盖 Q1-Q3，判 2。"),
    ("L2.2", 2, "parameters P1-P12：q_0,α_m=2,α_g=3,W_max,ρ_w,ρ_f,p_0,β_v=2,β_r=0.5,g_0,T,Π 含取值来源题面，判 2。"),
    ("L2.3", 2, "assumptions A1-A6 含 type+rationale（如 A3 失败惩罚、A6 到达当天不挖矿），合理，判 2。"),
    ("L2.4", 2, "objectives O1-O3：max m_{T+1}(已知)、max E[m_{T+1}](在线)、max E[Σ](多人)，与 Q1-Q3 对应，判 2。"),
    ("L2.5", 2, "constraints CT1-CT7：负重、非负、期限、沙暴、购一次、矿到达、多人耦合，覆盖题面全部规则，判 2。"),
    ("L2.6", 3, "candidates 4 个对比(DP选/IP弃/MDP弃/game辅助)且 rationale 明确；M1-M3 与 E1-E6 一致，判 3。"),
    ("L2.7", 2, "equations E1-E6：消耗规则、资金转移、确定性递推、期望递推、多人消耗收益、村庄价格，结构完整，判 2。"),
    ("L3.1", 2, "solvers S1-S3：确定性后向DP、期望DP、对称策略迭代，与 O1-O3 匹配，判 2 [no-exec-artifact]。"),
    ("L3.2", 2, "solvers 含 implementation_ref 'desert_dp.py'/'desert_expected_dp.py'/'desert_coord.py'，可执行代码指向明确，判 2 [no-exec-artifact]。"),
    ("L3.3", 2, "S1 确定性后向DP为精确递推、S2 期望DP精确，默认 2 分，判 2 [no-exec-artifact]。"),
    ("L3.4", 1, "无 multi_seed；V4 仅叙述'天气模拟以多组随机数初值重复，期望资金标准差应远小于均值'，未列固定种子与 cv 判据，判 1 [no-exec-artifact]。"),
    ("L3.5", 1, "claims CL1-CL3 含'存在明确挖矿窗口''在线更保守''避免扎堆'等可检验策略性预期，判 1 [no-exec-artifact]。"),
    ("L4.1", 2, "V1 退化基线：'天气全晴且无矿山村庄时最优应为最短路径直达'，对照正确，判 2 [no-exec-artifact]。"),
    ("L4.2", 2, "V2 基础消耗量±20% 扰动观察策略与资金；覆盖 O1/O2，判 2 [no-exec-artifact]。"),
    ("L4.3", 1, "V3 极限 初始资金→0 退化为不购买直接赶路，边界行为正确，判 1 [no-exec-artifact]。"),
    ("L4.4", 1, "validations V1→O1、V2→O1/O2、V3→O1、V4→O2、V5→O1/O2；O3(多人Q3) 无对应验证，缺失子问题验证，判 1 [no-exec-artifact]。"),
    ("L4.5", 2, "claims CL1-CL3 各含 evidence_refs(X1-X3,V1-V4) 与 status:'hypothesis'，结构化主张-证据映射，判 2。"),
), "2020_B 穿越沙漠；MODEL IR m-75e2d454；识别Result.xlsx→L1.3=2；无VP→L3.4=1；验证未覆盖Q3→L4.4=1；内嵌claims→L4.5=2。")

# ---------------------------------------------------------------------------
# 3ceddf2d - 2017_B 拍照赚钱, m-698b123d, MODEL IR + Validation Plan
# ---------------------------------------------------------------------------
write("3ceddf2d-839f-4c50-9223-b5135496f63c", d(
    ("L1.1", 2, "题面 Q1-Q4 显式提取：定价规律/未完成原因、新定价方案、打包修改、新项目方案；problem_binding.sub_question_id='Q1,Q2,Q3,Q4'。"),
    ("L1.2", 2, "隐式条件：A2 平台总预算固定(题面未给)、A3 会员密度代理、A5 新项目可迁移，识别题面未明信息。"),
    ("L1.3", 1, "交付为定价方案类，题面未指定具体文件名；产物未给表格规格，判 1。"),
    ("L1.4", 1, "VP.ambiguity_handling 含 2 项：预算约束是否存在、打包折扣承担方，各列 interpretations/adopted/justification，判 1。"),
    ("L1.5", 2, "primary='optimization'+secondary statistical_modeling/clustering；类型判定与定价优化一致，判 2。"),
    ("L2.1", 2, "variables V1-V9：p_j,π_j,y_j,(x_j,y_j),ρ_j,g_j,η_g,N_c,B_use 覆盖 Q1-Q4，判 2。"),
    ("L2.2", 2, "parameters P1-P7：θ(校准)、B、p_min/p_max、r_c=2km、η∈[0.85,1]、ȳ*=0.85 含来源，判 2。"),
    ("L2.3", 2, "assumptions A1-A6 含 type+rationale（如 A1 逻辑形式概率、A4 打包聚类），合理，判 2。"),
    ("L2.4", 2, "objectives O1-O4：反演规律、max N_c s.t.预算、打包联合max、新项目估计，与 Q1-Q4 对应，判 2。"),
    ("L2.5", 2, "constraints C1-C5：预算、价格盒、分区、折扣、容量，覆盖题面，判 2。"),
    ("L2.6", 3, "candidates 4 个对比(optimization选/statistical/clustering辅助/decision_analysis弃) rationale 明确；M1-M4 与 E1-E7 一致，判 3。"),
    ("L2.7", 2, "equations E1-E7：逻辑概率、正则化最小二乘、预算优化、一阶条件、聚类、组级概率、聚合，结构完整，判 2。"),
    ("L3.1", 2, "solvers S1-S3：投影梯度上升、K-means+坐标下降、牛顿-拉弗森回归，与 O1-O4 匹配，判 2 [no-exec-artifact]。"),
    ("L3.2", 2, "solvers 含 implementation_ref（投影步/交替优化/K收敛阈值1e-6），可执行设计完备，判 2 [no-exec-artifact]。"),
    ("L3.3", 2, "S3 牛顿法注明'收敛阈值1e-6'，K-means注明K由轮廓系数定，收敛判据明确；默认 2 分，判 2 [no-exec-artifact]。"),
    ("L3.4", 2, "VP.multi_seed：n_runs=5，seeds=[42,123,456,789,1024] 固定，多种子报告完成率均值标准差，可复现性机械支撑，判 2 [no-exec-artifact]。"),
    ("L3.5", 1, "claims C1-C4 含'未完成集中价格不足''唯一最优价格结构''打包提升完成率''达85%目标'等可检验预期，判 1 [no-exec-artifact]。"),
    ("L4.1", 2, "V1 以'统一价方案与差异化方案对比完成率'为基线，判 2 [no-exec-artifact]。"),
    ("L4.2", 2, "VP.sensitivity 3 项：P1±20%、P2±20%、P5±30%，one_at_a_time 覆盖 O2/O3，判 2 [no-exec-artifact]。"),
    ("L4.3", 1, "VP.limit_tests LT1-LT3：p_max→∞完成率→1、B→0退化最低价、ρ_j→0受密度主导，边界正确，判 1 [no-exec-artifact]。"),
    ("L4.4", 1, "V1→O2、V2→O2、V3→O2、V4→O3、V5→O4；O1(规律反演Q1) 无对应验证，缺失子问题验证，判 1 [no-exec-artifact]。"),
    ("L4.5", 2, "VP.claim_evidence_map C1(supported)/C2-C4(hypothesis) 各含 evidence_ref 与 status，结构化映射，判 2。"),
), "2017_B 拍照赚钱；MODEL IR m-698b123d + Validation Plan；SV臂5固定种子→L3.4=2；验证未覆盖Q1→L4.4=1；claim_evidence_map→L4.5=2。")

# ---------------------------------------------------------------------------
# a65ed389 - 2020_B 穿越沙漠, model_doc, NO Validation Plan
# ---------------------------------------------------------------------------
write("a65ed389-b74d-4fb1-b2e7-06298fadc1a6", d(
    ("L1.1", 2, "§一 子问题分解 Q1-Q3 显式：全知最优策略、在线策略、多人策略；§三/五/六 对应描写。"),
    ("L1.2", 2, "隐式条件识别：§二 A2 全知退化为单一路径、A4 多人仅经消耗倍数/收益分成/价格耦合、A6 矿山首日不挖矿，识别题面规则。"),
    ("L1.3", 2, "Q1 明确'将结果分别填入Result.xlsx'，文档识别该交付文件名，判 2。"),
    ("L1.4", 0, "文档无 ambiguity_handling/歧义点标注章节（§一仅列核心矛盾/关键实体/子问题），判 0。"),
    ("L1.5", 2, "§一 判定为'情景树随机优化+信息结构(非预期约束)'，类型与多阶段随机决策一致，判 2。"),
    ("L2.1", 2, "§三 变量 V1-V9：s_t,r_t,w_t,f_t,M_t,c_t,π_t,V_t,π_t,s_t^(i),k_t,M_T 覆盖 Q1-Q3，判 2。"),
    ("L2.2", 2, "§四 参数 P1-P11：λ_w=2,λ_m=3,ρ=0.5,κ_v=2,λ_k=2k,κ_k=4,γ_k=1/k,(q_w,q_f),(W_max),(d_w,d_f,g),P(c'|c)，含来源，判 2。"),
    ("L2.3", 2, "§二 假设 A1-A6 含类型与合理性（A1 mechanism、A3 simplification），判 2。"),
    ("L2.4", 2, "§五 目标 Q1 max M_T、Q2 max E[M_T]、Q3 max E[M_T^(i)]，与题面对应，判 2。"),
    ("L2.5", 2, "§六 约束 C1-C6：负重、生存、期限、行动过滤、耦合、购买一次，覆盖题面，判 2。"),
    ("L2.6", 3, "§七 候选对比表：情景树+多阶段随机规划(选)、MDP/值迭代(对照)、确定性DP(仅Q1)、启发式贪心(弃)，机理-题面一致，判 3。"),
    ("L2.7", 2, "§八 方程 资源资金转移、情景树递推、非预期约束、多人耦合、终点结算，结构完整，判 2。"),
    ("L3.1", 2, "§九 求解策略：Q1全知DP逆推、Q2情景树随机规划(随机对偶/情景分解)、Q3外层固定k_t迭代，与 Q1-Q3 匹配，判 2 [no-exec-artifact]。"),
    ("L3.2", 2, "§九 描述算法框架(分层抽样/情景分解/策略迭代)但无伪代码/implementation_ref，设计可理解，判 2 [no-exec-artifact]。"),
    ("L3.3", 2, "Q1确定性DP为精确算法；数值迭代未显式给收敛阈值但属精确递推，默认 2 分，判 2 [no-exec-artifact]。"),
    ("L3.4", 2, "§九 明确'固定 5 组随机数初值（42、123、456、789、1024）生成情景集，报告期望资金与5%-95%分位均值与标准差'，列出固定种子并报告离散度，可复现性机械支撑充分，判 2 [no-exec-artifact]。"),
    ("L3.5", 1, "§九 结果合理性预期：全知>在线、在线介于保守与全知上界、多人错峰均衡、沙暴停留价值显著，可检验，判 1 [no-exec-artifact]。"),
    ("L4.1", 2, "§九 基线：'全知结果与逐状态枚举最优对比'，对照明确，判 2 [no-exec-artifact]。"),
    ("L4.2", 2, "§九 灵敏度：天气转移概率±20%、消耗倍数±10% 扰动策略资金变化率<10%，判 2 [no-exec-artifact]。"),
    ("L4.3", 1, "§九 极限：天气转移趋确定时在线收敛全知策略，边界行为正确，判 1 [no-exec-artifact]。"),
    ("L4.4", 2, "§九 基线/灵敏度/极限/多初值稳定性/博弈收敛 覆盖 Q1-Q3 全部子问题，判 2 [no-exec-artifact]。"),
    ("L4.5", 1, "无结构化 claim_evidence_map；仅叙述式合理性预期，主张-证据对应为叙述级，判 1。"),
), "2020_B 穿越沙漠；model_doc（情景树随机规划）；识别Result.xlsx→L1.3=2；列出5固定种子→L3.4=2；无claim map→L4.5=1。")

# ---------------------------------------------------------------------------
# ece66fa2 - 2018_A 高温服装, m-21922946, MODEL IR + Validation Plan
# ---------------------------------------------------------------------------
write("ece66fa2-fd51-46e6-851b-4cf36123fdf7", d(
    ("L1.1", 2, "题面 Q1-Q3 显式提取：温度分布(problem1.xlsx)、II层最优厚度、II+IV层最优厚度；problem_binding.sub_question_id='Q1,Q2,Q3'。"),
    ("L1.2", 2, "隐式条件：A2 外表面对流/皮肤恒温37℃、A4 IV空气层等效导热、P8 网格0.1mm/1s，识别题面实验装置隐式。"),
    ("L1.3", 2, "Q1 明确'生成温度分布的Excel文件（文件名为problem1.xlsx）'，文档识别具体文件名，判 2。"),
    ("L1.4", 1, "VP.ambiguity_handling 含 4 项：皮肤边界条件、IV传热方式、h_conv取值、Q2约束严格性，各列 interpretations/adopted/justification，判 1。"),
    ("L1.5", 2, "primary='finite_difference'+secondary heat_transfer/numerical_optimization；类型判定与多层热传导数值离散一致，判 2。"),
    ("L2.1", 2, "variables V1-V8：T_i^n,Δx_i,Δt,T_s^n,d_2,d_4,τ_>44,T_max 覆盖 Q1-Q3，判 2。"),
    ("L2.2", 2, "parameters P1-P8：T_amb,T_skin,T_work,(k,ρ,c),层厚度,h_conv,(T_max^lim,τ),网格，含来源，判 2。"),
    ("L2.3", 2, "assumptions A1-A5 含 type+rationale（A3 稳定性CFL、A5 初始均匀37℃），合理，判 2。"),
    ("L2.4", 2, "objectives O1 simulate、O2/O3 minimize 厚度 s.t. 温度约束，与 Q1-Q3 对应，判 2。"),
    ("L2.5", 2, "constraints C1-C4：稳定性、温度上限、超温时长、正厚度，覆盖题面，判 2。"),
    ("L2.6", 3, "candidates 5 个对比(finite_difference选/heat_transfer/pde支撑/inverse辅助)；M1-M5 与 E1-E5 一致，判 3。"),
    ("L2.7", 2, "equations E1-E5：热传导PDE、显式FTCS、Crank-Nicolson、界面调和平均、稳态近似，结构完整，判 2。"),
    ("L3.1", 2, "solvers S1-S4：Thomas算法、网格收敛检验、二分厚度、双变量网格搜索，与 O1-O3 匹配，判 2 [no-exec-artifact]。"),
    ("L3.2", 2, "solvers 含 implementation_ref 'pseudocode: tridiagonal LU'/'bisection on d_2' 等可执行伪代码，判 2 [no-exec-artifact]。"),
    ("L3.3", 2, "S1 Thomas为精确求解、S3二分/S4网格为精确搜索，默认 2 分，判 2 [no-exec-artifact]。"),
    ("L3.4", 2, "VP.multi_seed：n_runs=5，seeds=[42,43,44,45,46] 固定，tolerance cv<5%（实测 h_conv cv≈1.5%），可复现性充分，判 2 [no-exec-artifact]。"),
    ("L3.5", 1, "claims C1-C3 含'Crank-Nicolson收敛稳定、误差<0.5℃''II层唯一最小可行值''可行域单调包络'等可检验预期，判 1 [no-exec-artifact]。"),
    ("L4.1", 2, "V2 显式与隐式格式交叉验证同一算例结果一致，基线对照明确，判 2 [no-exec-artifact]。"),
    ("L4.2", 2, "VP.sensitivity 3 项：h_conv±20%、k_2±20%、k_4±20%，one_at_a_time 覆盖 O1/O2/O3，判 2 [no-exec-artifact]。"),
    ("L4.3", 1, "VP.limit_tests LT1-LT4：T_amb→37℃恒温、d_2→∞趋37℃、d_4→0退化三层、Δt→0收敛PDE，边界正确，判 1 [no-exec-artifact]。"),
    ("L4.4", 2, "V1→O1、V2/V3→O1、V4→O2/O3、V5→O2/O3，覆盖 Q1-Q3 全部目标，判 2 [no-exec-artifact]。"),
    ("L4.5", 2, "VP.claim_evidence_map C1-C3 各含 evidence_ref 与 status:'supported'，结构化映射完整，判 2。"),
), "2018_A 高温服装；MODEL IR m-21922946 + Validation Plan；识别problem1.xlsx→L1.3=2；SV臂5固定种子+cv<5%→L3.4=2；claim_evidence_map 全 supported→L4.5=2。")

# ---------------------------------------------------------------------------
# 14822f53 - 2022_C 古代玻璃, m-599458c1, MODEL IR, NO Validation Plan
# ---------------------------------------------------------------------------
write("14822f53-8201-4c62-b5f5-9b220e8fa8e0", d(
    ("L1.1", 2, "题面 Q1-Q4 显式提取：风化关系/风化前成分、亚类划分、未知鉴别、关联比较；problem_binding.sub_question_id='Q1,Q2,Q3,Q4'。"),
    ("L1.2", 2, "隐式条件：A1 有效区间85-105%、A5 空白按缺失非0、V6 S_i 累加和，识别题面成分性隐式约束。"),
    ("L1.3", 1, "交付为分析/鉴别结果，题面未指定具体文件名；产物未给表格规格，判 1。"),
    ("L1.4", 0, "产物无 ambiguity_handling 章节/歧义点字段，判 0。"),
    ("L1.5", 2, "primary='statistical_classification'+secondary regression_analysis；类型判定与类别统计比较一致，判 2。"),
    ("L2.1", 2, "variables V1-V12：W_i,T_i,D_i,C_i,x_ij,S_i,x̂_ij,Z_i,g(x_i),ρ_ab,δ_i,d_i 覆盖 Q1-Q4，判 2。"),
    ("L2.2", 2, "parameters P1-P8：L_lo=85,L_hi=105,α=0.05,λ岭回归,PbO阈值,τ_sub,n_min=3 含来源，判 2。"),
    ("L2.3", 2, "assumptions A1-A5 含 type+rationale（A2 未风化点无偏近似、A4 判别边界可分），合理，判 2。"),
    ("L2.4", 2, "objectives O1-O4：复原回归、亚类最小化、判别最小化错分、相关系数估计，与 Q1-Q4 对应，判 2。"),
    ("L2.5", 2, "constraints C1-C6：有效性、非负、类别归属、判别输出、亚类规模、相关矩阵正定，覆盖，判 2。"),
    ("L2.6", 3, "candidates 3 个对比(statistical_classification选/clustering辅助/decision_tree弃) rationale 明确；M1-M3 与 E1-E6 一致，判 3。"),
    ("L2.7", 2, "equations E1-E6：S_i、δ_i、复原回归、PCA、LDA、相关系数，结构完整，判 2。"),
    ("L3.1", 2, "solvers S1-S4：岭回归闭式、KMeans+轮廓系数、LDA闭式、相关系数+Fisher z，与 O1-O4 匹配，判 2 [no-exec-artifact]。"),
    ("L3.2", 2, "solvers 含 implementation_ref '数值线性代数库'/'迭代Lloyd算法'/'特征分解' 等可执行指向，判 2 [no-exec-artifact]。"),
    ("L3.3", 2, "岭回归/LDA为闭式精确解，KMeans注明'10次随机初始化取最优'，收敛明确；默认 2 分，判 2 [no-exec-artifact]。"),
    ("L3.4", 1, "无 multi_seed；V3 仅叙述'多次随机重采样训练判别模型，统计错分率均值与波动'，未列固定种子与 cv 判据，判 1 [no-exec-artifact]。"),
    ("L3.5", 1, "claims C1-C4 含'风化与类型显著相关''亚类阈值±20%稳定''低错分率''PbO-BaO强正相关'等可检验预期，判 1 [no-exec-artifact]。"),
    ("L4.1", 2, "V1 以'风化点成分均值作为朴素基线'与复原模型比较误差，对照明确，判 2 [no-exec-artifact]。"),
    ("L4.2", 2, "V2 亚类阈值±20% 观察成员变化；覆盖 O2，判 2 [no-exec-artifact]。"),
    ("L4.3", 1, "V4 极限 显著性水平取0.01/0.10 重跑关联检验确认结论方向不变，边界行为正确，判 1 [no-exec-artifact]。"),
    ("L4.4", 2, "V1→O1、V2→O2、V3→O3、V4→O4、V5→O1，覆盖 Q1-Q4 全部目标，判 2 [no-exec-artifact]。"),
    ("L4.5", 2, "claims C1-C4 各含 evidence_refs(X1-X4,V1-V4) 与 status:'hypothesis'，结构化主张-证据映射，判 2。"),
), "2022_C 古代玻璃；MODEL IR m-599458c1；无VP/ambiguity→L1.4=0,L3.4=1；内嵌claims数组→L4.5=2。")

print("phase-2 shard files written OK")
