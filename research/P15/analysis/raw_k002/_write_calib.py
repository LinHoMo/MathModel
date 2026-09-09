# -*- coding: utf-8 -*-
import json, os
from datetime import datetime

OUT = "C:/Users/Lin/Desktop/Programs/MathModel/research/P15/analysis/raw_k002/scores/_calibration/eval_E06"
os.makedirs(OUT, exist_ok=True)

RUBRIC = "MODEL_CONSTRUCTION_RUBRIC-v1.1a"

# helper: build dimensions dict from list of (dim, score, evidence)
def dims(pairs):
    d = {}
    for k, s, e in pairs:
        d[k] = {"score": s, "evidence": e}
    return d

def vector(d):
    lv = {"L1_total":0,"L2_total":0,"L3_total":0,"L4_total":0}
    for k,v in d.items():
        if k.startswith("L1"): lv["L1_total"]+=v["score"]
        elif k.startswith("L2"): lv["L2_total"]+=v["score"]
        elif k.startswith("L3"): lv["L3_total"]+=v["score"]
        elif k.startswith("L4"): lv["L4_total"]+=v["score"]
    return lv

def write(uuid, d, notes=""):
    doc = {
        "submission_id": uuid,
        "evaluator": {"model":"E06","type":"independent_llm","version":"1.0",
                       "timestamp": datetime.now().isoformat()},
        "rubric_version": RUBRIC,
        "dimensions": d,
        "vector": vector(d),
        "failure_modes": [],
        "notes": notes
    }
    path = os.path.join(OUT, uuid + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return path

# ---------------- 04fc6d82 (2018_B, m-b16f192b) ----------------
u = "04fc6d82-7d15-4385-92fb-e43b99546eb4"
d = dims([
 ("L1.1",2,"题面表1共9组作业参数（RGV移动1/2/3单位、加工时间、上下料、清洗）全部由 P1-P12 提取，数值与题面逐条一致。"),
 ("L1.2",2,"隐式条件以 A1（单RGV串行不可抢占）、A3（两道工序须不同CNC）、A4（故障1%概率独立）识别，覆盖题面隐含约束。"),
 ("L1.3",1,"识别了调度策略与作业效率主交付物，但未显式标注题面 Q2『将结果填入附件2的EXCEL表（3个工作表）』这一具体表格/工作表交付规格。"),
 ("L1.4",0,"产物无歧义点标注字段或章节（无 ambiguity_handling），未标注如『两道工序能否同一CNC完成』等题面歧义点。"),
 ("L1.5",2,"model_family.primary=optimization + secondary simulation，问题类型为调度优化+仿真，与题面一致。"),
 ("L2.1",2,"V1-V10 覆盖位置/状态/决策/派生变量，sub_question_binding 完整绑定 Q1-Q4。"),
 ("L2.2",2,"P1-P12 完整提取题面表1全部参数（移动/加工/上下料/清洗/班次28800s/故障概率0.01），source 标注『题目』。"),
 ("L2.3",2,"A1-A6 含 mechanism/simplification/projection/calibration 类型与 rationale，如 A4 故障分布假设误差随班次统计平均减小。"),
 ("L2.4",2,"O1-O4 对应 Q1-Q4 最大化班次产量/期望产量，目标与题面任务1模型、任务2检验一致。"),
 ("L2.5",2,"C1-C6 覆盖单资源/时间窗/行程/先后序/容量/截止约束，source 标注题面或物理限制。"),
 ("L2.6",3,"M1-M4 机理对应排序/并行机/两阶段流水/随机故障题面，candidates 列4候选并说明排除理由，机理-方程 E1-E6 一致。"),
 ("L2.7",2,"E1-E6 结构完整（逻辑/代数/递推/差分），含 derivation_trace 与 sub_question_binding。"),
 ("L3.1",2,"S1 分支定界求解MIP、S2 轮询优先启发式、S3 蒙特卡洛样本均值，方法与 optimization/simulation 模型匹配。"),
 ("L3.2",2,"no-exec-artifact: S1-S3 均含 implementation_ref（0-1变量构造、轮询优先、固定随机数发生器抽样故障），输入-输出与依赖可查。"),
 ("L3.3",2,"no-exec-artifact: MIP 为精确算法收敛性由方法内在保证；V3 声明故障样本数 100→2000 期望产量波动收敛于1%以内。"),
 ("L3.4",1,"no-exec-artifact: S3 仅声明『固定随机数发生器』但无≥5固定种子列表与 cv<10% 稳定性判据，可复现设计不完整。"),
 ("L3.5",1,"no-exec-artifact: X1-X3 给出预期输出量级（班次产量整数件、RGV利用率0.7-0.95、故障下降5%-15%），与题面物理量级相符。"),
 ("L4.1",2,"no-exec-artifact: V1 以轮询贪心策略为基线对比MIP产量上界，报告对比判据『MIP最优解≥贪心解』。"),
 ("L4.2",2,"no-exec-artifact: V2 对移动/上下料时间±10%扰动，观察班次产量变化率。"),
 ("L4.3",1,"no-exec-artifact: V4 极限检验：清洗时间→0、移动时间→0 时产量趋近加工时间决定极限。"),
 ("L4.4",2,"no-exec-artifact: validations V1→O1/O2、V2→O2、V3→O4、V4→O3 覆盖全部4个目标，与题面 evaluation 对应。"),
 ("L4.5",2,"no-exec-artifact: claims C1-C4 均含 evidence_refs（X/V）且 status 为 supported/hypothesis，无 unresolved。"),
])
write(u, d)

# ---------------- 3ff350bf (2011_B, m-af221e77, +VP) ----------------
u = "3ff350bf-766e-4b15-874e-bc192ef91276"
d = dims([
 ("L1.1",2,"题面 Q1-Q5 全部约束（3分钟覆盖、13要道全封锁、新增2-5平台、六区评估、围堵）由 P1-P8、C1-C5 逐项提取，与题面一致。"),
 ("L1.2",2,"隐式条件以 A1（图加权无向）、A2（最近平台单归属）、A4（案发3分钟后调度）、A5（覆盖率/变异系数指标）识别。"),
 ("L1.3",1,"识别了管辖分配/封锁方案/新增平台/围堵方案等主交付物，但未显式标注题面附件2『5个工作表』的具体工作表交付规格。"),
 ("L1.4",1,"Validation Plan.ambiguity_handling 列出3处歧义（3分钟软约束、嫌疑车速未给定、围堵时间窗），并给出采纳与理由。"),
 ("L1.5",2,"model_family.primary=optimization + secondary graph_algorithm/decision_analysis，问题类型为离散指派/选址优化，判定正确。"),
 ("L2.1",2,"V1-V9 覆盖节点/时间/指派/封锁/响应/平台/工作量/覆盖率/可达域，绑定 Q1-Q5。"),
 ("L2.2",2,"P1-P8 提取车速60、覆盖阈值3、平台数20、要道13、新增区间[2,5]、案发延迟3等，source 标注题目/假设。"),
 ("L2.3",2,"A1-A5 含 mechanism/projection 类型与 rationale，如 A5 合理性指标直接度量工作量不均衡与出警时长。"),
 ("L2.4",2,"O1-O5 对应 Q1-Q5 min-max 指派/选址/评估/围堵目标，与题面一致。"),
 ("L2.5",2,"C1-C5 覆盖指派/覆盖/匹配/预算/截止约束，source 标注题面。"),
 ("L2.6",3,"M1-M4 机理对应指派/选址/min-max/时变可达，candidates 列4候选（含排除 multi_objective/simulation）并说明，机理-方程 E1-E6 一致。"),
 ("L2.7",2,"E1-E6 结构完整（最短时间矩阵/指派/可达域/出口封锁），含 derivation_trace。"),
 ("L3.1",2,"S1 Floyd-Warshall、S2 瓶颈指派/匈牙利、S3 分支定界、S4 动态可达+指派，方法与图优化模型匹配。"),
 ("L3.2",2,"no-exec-artifact: S1-S4 均含 implementation_ref（O(N³)矩阵、二分图瓶颈匹配、分支定界、时间步扩张），输入-输出可查。"),
 ("L3.3",2,"no-exec-artifact: 指派/选址为精确算法收敛性内在保证；VP 提供确定性算法终止条件固定，无发散风险。"),
 ("L3.4",2,"no-exec-artifact: VP.multi_seed 列5固定种子[42,123,456,789,1024]、aggregation mean_std，支持可复现设计。"),
 ("L3.5",1,"no-exec-artifact: X1-X5 给出预期输出（管辖表/最大响应/封锁匹配/覆盖率-CV/出口集），量级与题面物理量级相符。"),
 ("L4.1",2,"no-exec-artifact: V1 以单平台单节点与直线路网手工对照、完全图退化验证为基线；V4 报告确定性算法多次一致。"),
 ("L4.2",2,"no-exec-artifact: V2 车速±20%、道路±10%、嫌疑车速±20%扰动检验稳定性；VP.sensitivity 4项参数扰动。"),
 ("L4.3",1,"no-exec-artifact: V3 与 VP.LT1-LT4 极限检验（车速→∞、平台=节点数、新增上限放宽、嫌疑车速→0）。"),
 ("L4.4",2,"no-exec-artifact: validations V1→O1/O2、V2→O1-O3/O5、V3→O1/O3、V4→O1-O5 覆盖全部5目标。"),
 ("L4.5",2,"no-exec-artifact: claim_evidence_map 将 C1-C5 映射到 V1-V4 且 status 为 supported/hypothesis，无 unresolved。"),
])
write(u, d)

# ---------------- 7c69dee1 (2018_B, m-eead449b, +VP) ----------------
u = "7c69dee1-bb5e-4bcf-95ed-626914296c07"
d = dims([
 ("L1.1",2,"题面表1作业参数与两道工序/故障设定由 P1-P8、A1-A5 提取（加工/清洗/上下料/移动时间、班次28800s、故障0.01），一致。"),
 ("L1.2",2,"隐式条件以 A1（单机械手串行）、A2（加工后等待清洗）、A3（无故障确定/故障1%）、A4（移动线性）识别。"),
 ("L1.3",1,"识别了调度策略与产量主交付物，但未显式标注题面 Q2『将结果填入附件2的EXCEL表（3个工作表）』具体表格交付规格。"),
 ("L1.4",1,"Validation Plan.ambiguity_handling 列出4处歧义（服务优先级、故障修复时长、两道缓冲、班末统计），给出采纳与理由。"),
 ("L1.5",2,"model_family.primary=dynamic_programming + secondary optimization/mdp，问题类型为事件驱动DP，判定正确。"),
 ("L2.1",2,"V1-V7 覆盖位置/状态/剩余时间/动作/产量/空闲率/故障，绑定 Q1-Q4。"),
 ("L2.2",2,"P1-P8 提取加工/清洗/上下料/移动时间、CNC数8、班次28800s、故障0.01、刀具寿命，source 标注题目。"),
 ("L2.3",2,"A1-A5 含 mechanism/simplification/calibration 类型与 rationale，如 A5 修复时长未给作保守偏乐观处理。"),
 ("L2.4",2,"O1-O4 对应 Q1-Q4 最大化（期望）产量，目标与题面一致。"),
 ("L2.5",2,"C1-C5 覆盖单服务/工序/时间窗/故障/刀具约束，source 标注题面。"),
 ("L2.6",3,"M1-M4 机理对应事件驱动/服务资格/期望折现/产线串行，candidates 列4候选并说明，机理-方程 E1-E4 一致。"),
 ("L2.7",2,"E1-E4 结构完整（状态转移/事件DP/期望递推/节拍），含 derivation_trace。"),
 ("L3.1",2,"S1 事件驱动前向搜索、S2 滚动重调度、S3 蒙特卡洛策略评估、S4 节拍分析，方法与DP/MDP模型匹配。"),
 ("L3.2",2,"no-exec-artifact: S1-S4 含 implementation_ref（pseudocode 事件仿真/重调度/5×8h仿真/line balance），路径与输出可查。"),
 ("L3.3",2,"no-exec-artifact: DP/价值迭代为精确算法收敛性内在保证；V5 声明调度搜索深度/剪枝阈值收敛、产量对阈值不敏感。"),
 ("L3.4",2,"no-exec-artifact: VP.multi_seed 列5固定种子[42,43,44,45,46]、tolerance cv<10%、result cv≈4.2%。"),
 ("L3.5",1,"no-exec-artifact: X1-X4 给出预期输出（N_prod/调度序列/期望产量/瓶颈），量级与题面物理量级相符。"),
 ("L4.1",2,"no-exec-artifact: V1 以『固定轮询顺序』策略为基线比较DP策略产量提升。"),
 ("L4.2",2,"no-exec-artifact: V3 故障率0.5%~2%扫描、移动时间±20%、二道工序加工±20%扰动观察产量损失曲线。"),
 ("L4.3",1,"no-exec-artifact: V4 与 VP.LT1-LT4 极限检验（移动→0、故障率→0、加工→∞、班次→0）。"),
 ("L4.4",1,"no-exec-artifact: validations 仅覆盖 O1/O2（V1→O1、V2/V3/V4→O2、V5→O1），O3(Q3)/O4(Q4) 目标无对应验证，覆盖不全。"),
 ("L4.5",2,"no-exec-artifact: claims C1-C3 均含 evidence_refs（X/V）且 status 均为 supported，无 unresolved。"),
])
write(u, d)

# ---------------- c37459ee (2020_B, model_doc) ----------------
u = "c37459ee-f50b-4a63-b71e-cd7b27cd8130"
d = dims([
 ("L1.1",2,"题面显式规则（天单位/箱单位/负重/天气三态/沙暴停留/挖矿3倍/起终退半价/多人k倍）在『显式条件』段逐条提取，与题面一致。"),
 ("L1.2",2,"隐式条件段识别相邻区域移动、资源约束内可行、未到终点耗尽判负、多人信息结构两类，覆盖题面隐含。"),
 ("L1.3",2,"问题理解段显式复现 Q1『将相应结果分别填入Result.xlsx』交付规格，识别了 Result.xlsx 这一具体文件交付物。"),
 ("L1.4",1,"『歧义点』段列出三处歧义（天气转移未知、最优策略口径、多人均衡概念）并给出本文处理口径。"),
 ("L1.5",2,"问题类型判定为『多阶段随机序贯决策（资源-资金联合调度）』，Q1确定性DP/Q2随机DP/Q3多人博弈，判定正确。"),
 ("L2.1",2,"变量表含 t/l/w/f/m/s/a/qw/qf/k/g/b 共12项，覆盖状态/观测/决策/导出，绑定 Q1-Q3。"),
 ("L2.2",2,"参数表含 q0/αm/αg/Wmax/ρ/p0/βv/βr/g0/T/Π/n 共12项，source 标注题面/校准。"),
 ("L2.3",2,"A1-A6 含简化/机制/校准类型与合理性说明，如 A2 天气一阶马尔可夫为信息结构最小完备刻画。"),
 ("L2.4",2,"Q1-Q3 目标为 max m_T+1 / max E[m_T+1] / max Σm，与题面保留资金最大化一致。"),
 ("L2.5",2,"约束表含负重/存活/截止/沙暴/起点购买/矿山时序/多人规则，source 标注题面。"),
 ("L2.6",3,"§7 给出候选模型对比表（DP/MDP/MIP/RL）并说明选择依据，机理主线贯穿 Q1→Q2→Q3，机理-方程 E1-E6 一致。"),
 ("L2.7",2,"E1-E6 结构完整（消耗规则/资金转移/确定性递推/随机递推/多人关系/博弈递推），含初始与终止条件。"),
 ("L3.1",2,"求解策略：Q1后向价值迭代、Q2随机价值迭代、Q3对称策略迭代，方法与DP/MDP模型匹配。"),
 ("L3.2",1,"no-exec-artifact: 仅叙述『价值迭代网格化、复杂度O(T·|L|·网格³)』，无 implementation_ref/代码路径或明确输出约定。"),
 ("L3.3",2,"no-exec-artifact: 验证方案声明『收敛：价值迭代残差阈值、策略迭代策略变化量单调递减』，含收敛判据。"),
 ("L3.4",2,"no-exec-artifact: 可复现性段固定5组随机数初值抽样天气路径与均衡初值，报告均值标准差，多初值稳定性 std<10% 均值。"),
 ("L3.5",1,"no-exec-artifact: 结果合理性预期给出量级（全知比未知高5%-15%、挖矿窗口、多人略低），与题面物理量级相符。"),
 ("L4.1",1,"no-exec-artifact: 基线仅『全晴无补给点应直线直达』行为对照，未给出零模型/随机基线并报告对比结论。"),
 ("L4.2",2,"no-exec-artifact: 灵敏度扰动基础消耗/转移概率/基础收益 ±20% 观察关键输出变化。"),
 ("L4.3",1,"no-exec-artifact: 极限检验 W_max→∞ 一次购满、q0→0 全程挖矿、T→最短路径无挖矿。"),
 ("L4.4",2,"no-exec-artifact: 验证方案（基线/极限/灵敏度/多初值/收敛）覆盖 Q1-Q3 全部子问题核心目标。"),
 ("L4.5",1,"no-exec-artifact: 产物为叙述式文档，未枚举显式 claims 与 claim_evidence_map，主张-证据对应无结构化支撑。"),
])
write(u, d)

# ---------------- ff5e9ff0 (2019_C, model_doc) ----------------
u = "ff5e9ff0-ff50-4de4-b825-67b85cabcc97"
d = dims([
 ("L1.1",2,"题面 Q1-Q4（排队vs返回决策/排队乘客相互作用/分时段方案/短途优先）在问题理解段提取，与题面一致。"),
 ("L1.2",2,"假设 A1-A6 识别隐式条件（泊松到达/M/M/c、司机理性、空返成本、蓄车池容量、短途阈值、数据固定）。"),
 ("L1.3",2,"识别了 Q2『收集数据给出选择方案』交付要求；Q1-Q4 决策/方案/评价交付物均已覆盖。"),
 ("L1.4",0,"产物无歧义点标注字段或章节，未标注如『短途优先阈值如何标定』『司机风险偏好』等题面歧义点。"),
 ("L1.5",2,"问题类型判定为收益均衡+排队网络混合框架，Q1-Q4 为收益比较/排队/阈值/方案评价，判定正确。"),
 ("L2.1",2,"V1-V10 覆盖等待/收益/成本/决策/到达率/队长/短途占比/净收益，绑定 Q1-Q4。"),
 ("L2.2",2,"P1-P8 提取平均车费/里程/成本/容量/空返里程/短途阈值/优先比例/时段，source 标注题面/校准/假设。"),
 ("L2.3",2,"A1-A6 含 mechanism/simplification/calibration/projection 类型与合理性说明，如 A1 高峰自相关使估计偏乐观。"),
 ("L2.4",2,"Q1 比较净收益、Q2 排队指标、Q3 阈值策略、Q4 短途优先评价，目标与题面一致。"),
 ("L2.5",2,"C1-C5 覆盖容量/稳态/决策边界/短途比例/公平下限，source 标注题面/模型。"),
 ("L2.6",3,"§七 候选模型对比表（收益+M/M/c/博弈/统计回归）说明选择依据，机理主线 Q1→Q2→Q3→Q4，机理-方程一致。"),
 ("L2.7",2,"方程含收益比较/排队内核/阈值策略/短途优先/系统平均等待，结构完整且含推导。"),
 ("L3.1",2,"求解：Q1 估计参数给Wq*、Q2 M/M/c公式、Q3 二分法解阈值、Q4 注入规则重算，方法与排队模型匹配。"),
 ("L3.2",1,"no-exec-artifact: 叙述求解步骤但无 implementation_ref/代码路径或明确输入输出约定。"),
 ("L3.3",2,"no-exec-artifact: M/M/c 为精确解析公式，收敛性由方法内在保证；仿真交叉验证层为确定性公式对照。"),
 ("L3.4",2,"no-exec-artifact: 固定5组随机数初值[42,123,456,789,1024]运行仿真，多初值稳定性 std<5%，cv<10%。"),
 ("L3.5",1,"no-exec-artifact: 结果合理性预期给量级（Wq*几十分钟、高峰接近临界、短途节省30%+、整体吞吐提升），相符。"),
 ("L4.1",2,"no-exec-artifact: 基线以 M/M/c 解析结果与离散事件仿真对比，误差<10% 作为对照判据。"),
 ("L4.2",2,"no-exec-artifact: 灵敏度 λt,λp 各±20%、θ±20% 扰动，阈值策略方向不变。"),
 ("L4.3",1,"no-exec-artifact: 极限检验 λt→μ 时 Wq→∞（失稳）、θ→0 时短途优先退化为普通排队。"),
 ("L4.4",2,"no-exec-artifact: 验证（基线/灵敏度/极限/多初值/公平检验）覆盖 Q1-Q4 全部核心目标。"),
 ("L4.5",1,"no-exec-artifact: 叙述式文档未枚举显式 claims 与 evidence_refs，主张-证据对应无结构化映射。"),
])
write(u, d)

# ---------------- 88bd6407 (2018_A, m-322c95c9) ----------------
u = "88bd6407-2bcf-4e01-a28d-efe39bf00273"
d = dims([
 ("L1.1",2,"题面 Q1-Q3 参数（75/65/80℃、II层6mm/IV层5.5mm、工作90/60/30min、47℃/5min约束）由 P1-P8、O1-O3 提取，一致。"),
 ("L1.2",2,"隐式条件以 A1（一维传热）、A3（外对流/内恒温37）、A5（初始37℃）识别，覆盖题面隐含物理设定。"),
 ("L1.3",2,"O1 显式声明『生成 problem1.xlsx』，识别了 Q1 的具体 Excel 文件名交付规格。"),
 ("L1.4",0,"产物无歧义点标注字段或章节（无 ambiguity_handling），未标注如『对流系数如何获取』『IV层等效导热』等歧义。"),
 ("L1.5",2,"model_family.primary=heat_transfer + secondary pde/numerical_optimization，问题类型为多层传热+厚度优化，判定正确。"),
 ("L2.1",2,"V1-V8 覆盖温度场/坐标/时间/皮肤温度/II层厚/IV层厚/超温时间/峰值，绑定 Q1-Q3。"),
 ("L2.2",2,"P1-P8 提取环境/皮肤37/时长/各层导热/密度比热/厚度/对流系数/阈值(47,5min)，source 标注题目/校准。"),
 ("L2.3",2,"A1-A5 含 simplification/mechanism/mechanism_assumption/calibration 类型与 rationale，如 A4 空气层等效导热常用近似。"),
 ("L2.4",2,"O1 仿真温度分布、O2/O3 最小化厚度满足约束，目标与题面一致。"),
 ("L2.5",2,"C1-C4 覆盖温度上限/超温时长/厚度正/物理边界约束，source 标注题面/物理限制。"),
 ("L2.6",3,"M1-M5 机理对应导热/对流/层间连续/厚度热阻/空气层隔热，candidates 列5候选并说明排除理由，机理-方程 E1-E4 一致。"),
 ("L2.7",2,"E1-E4 结构完整（热传导PDE/对流边界/界面连续/热阻网络），含 derivation_trace。"),
 ("L3.1",2,"S1 Crank-Nicolson 隐式差分、S2 厚度扫描二分、S3 二维网格+帕累托、S4 参数反演，方法与PDE/优化模型匹配。"),
 ("L3.2",2,"no-exec-artifact: S1-S4 含 implementation_ref（pseudocode 三对角求解/二分/网格筛选/最小二乘），路径与输出可查。"),
 ("L3.3",2,"no-exec-artifact: 隐式差分+PDE为精确/稳定格式；V2 声明网格细化(Δx/2、Δt/2)检验温度场收敛误差<0.1℃。"),
 ("L3.4",1,"no-exec-artifact: V5 仅称『网格划分与初值扰动下结果稳定（多次重算）』，无≥5固定种子列表与 cv<10% 判据。"),
 ("L3.5",1,"no-exec-artifact: X1-X4 给出预期输出（皮肤温度曲线/最优厚度/厚度对/对流系数），量级与题面物理量级相符。"),
 ("L4.1",2,"no-exec-artifact: V1 以纯导热无对流(h→∞)与绝热(h→0)两极限为界，验证测量曲线落在预测区间内。"),
 ("L4.2",2,"no-exec-artifact: V3 对 h_conv 与 k_2 各±20%扰动，观察最优厚度与皮肤温度敏感度。"),
 ("L4.3",1,"no-exec-artifact: V4 极限检验 d2→∞ 皮肤趋37℃、d4→0 退化为三层。"),
 ("L4.4",2,"no-exec-artifact: validations V1→O1、V2→O1、V3→O2、V4→O2/O3、V5→O1 覆盖全部3目标。"),
 ("L4.5",2,"no-exec-artifact: claims C1-C3 均含 evidence_refs（X/V）且 status 均为 supported，无 unresolved。"),
])
write(u, d)

# ---------------- 30beb45f (2017_B, m-cc428b57, +VP) ----------------
u = "30beb45f-6835-44f2-8eb8-1f9d7914c120"
d = dims([
 ("L1.1",2,"题面 Q1-Q4（定价规律/新方案/打包/新项目）约束（位置/定价/完成、会员信誉、预算）由 P1-P8、O1-O4 提取，一致。"),
 ("L1.2",2,"隐式条件以 A1（会员行为加总为完成概率）、A3（核密度光滑）、A5（打包消除内耗）识别。"),
 ("L1.3",2,"识别了 Q1 规律分析/Q2 新方案/Q3 打包/Q4 新项目定价等主交付物，与题面四类任务对应。"),
 ("L1.4",1,"Validation Plan.ambiguity_handling 列出3处歧义（直线vs路网距离、打包领取方式、未完成原因口径），给出采纳与理由。"),
 ("L1.5",2,"model_family.primary=statistical_modeling + secondary optimization/clustering，问题类型为统计建模+定价优化，判定正确。"),
 ("L2.1",2,"V1-V14 覆盖定价/状态/概率/坐标/密度/距离/竞争/打包/新定价/完成率/供需比，绑定 Q1-Q4。"),
 ("L2.2",2,"P1-P8 提取价格上下限/总预算/竞争半径/打包半径/逻辑回归系数/带宽/信誉，source 标注校准/题目/假设。"),
 ("L2.3",2,"A1-A5 含 mechanism_assumption/simplification/projection/calibration/mechanism 类型与 rationale，如 A2 大样本相关性稀释。"),
 ("L2.4",2,"O1 估计完成概率、O2-O4 最大化完成率，目标与题面一致。"),
 ("L2.5",2,"C1-C5 覆盖区间/预算/空间邻近/分组完备/预算约束，source 标注模型假设/题面。"),
 ("L2.6",3,"M1-M5 机理对应供需比/效用/边际优化/打包去内耗/外推，candidates 列4候选并说明排除，机理-方程 E1-E6 一致。"),
 ("L2.7",2,"E1-E6 结构完整（供需比/逻辑回归/完成率/预算优化/打包概率/反解定价），含 derivation_trace。"),
 ("L3.1",2,"S1 IRLS逻辑回归、S2 边际排序+网格、S3 DBSCAN聚类、S4 自助重抽样，方法与统计/优化/聚类模型匹配。"),
 ("L3.2",2,"no-exec-artifact: S1-S4 含 implementation_ref（pseudocode IRLS/排序/DBSCAN/bootstrap），路径与输出可查。"),
 ("L3.3",2,"no-exec-artifact: S1 声明 IRLS until ||Δβ||<1e-6 收敛判据；逻辑回归/DBSCAN为精确/收敛算法。"),
 ("L3.4",2,"no-exec-artifact: VP.multi_seed 列5固定种子[42,43,44,45,46]、tolerance cv<10%、result cv≈2.3%。"),
 ("L3.5",1,"no-exec-artifact: X1-X4 给出预期输出（回归系数/R²-AUC/新价格表/打包组/建议定价），量级与题面相符。"),
 ("L4.1",2,"no-exec-artifact: V1 以常数概率模型与均值定价为基线，对比逻辑回归 R²与AUC 检验解释力。"),
 ("L4.2",2,"no-exec-artifact: V2 预算±20%、VP.sensitivity 3项参数扰动观察完成率/系数变化。"),
 ("L4.3",1,"no-exec-artifact: V3 与 VP.LT1-LT3 极限检验（价格→下限、打包半径→0退化、密度→∞价格封顶）。"),
 ("L4.4",2,"no-exec-artifact: validations V1→O1、V2→O2、V3→O3、V4→O4 覆盖全部4目标。"),
 ("L4.5",2,"no-exec-artifact: claim_evidence_map 将 C1-C4 映射到 V1/V2/V3/V4 且 status 均为 supported，无 unresolved。"),
])
write(u, d)

# ---------------- 286218b8 (2024_A, model_doc) ----------------
u = "286218b8-48f4-4f12-9e99-53d23e896c64"
d = dims([
 ("L1.1",2,"题面 223节/龙头341cm/龙身220cm/板宽30cm/孔径5.5cm/孔心27.5cm/螺距55cm/1m/s/第16圈/9m调头圆等显式几何参数在『显式条件』段逐条提取。"),
 ("L1.2",2,"隐式条件段识别等距螺线极径线性、相邻把手距=板长、调头圆边界限制、速度由曲率链式放大等。"),
 ("L1.3",2,"问题理解段显式复现 Q1『result1.xlsx（保留6位小数）』、Q2 result2.xlsx、Q4 result4.xlsx 文件交付规格与精度要求。"),
 ("L1.4",1,"『歧义点』段列出三处（A点极角取32π、碰撞判据取法向间隙<板宽、调头切点自由变量）。"),
 ("L1.5",2,"问题类型判定为『平面曲线几何与约束优化』，核心范式螺线/圆弧几何+相切约束最值，判定正确。"),
 ("L2.1",2,"变量表含 r(θ)/θ/ρ(θ)/P_i/v_i/g(θ)/s_T/(R1,R2)/κ_i，覆盖状态/派生/决策，绑定 Q1-Q5。"),
 ("L2.2",2,"参数表含 L0/L1/w/N/v0/n0/R_T/λ/p/v_max 共10项，取值与来源标注题面给定。"),
 ("L2.3",2,"B1-B5 含 mechanism/simplification/calibration 类型与合理性说明，如 B3 等距螺线法向间隙近似。"),
 ("L2.4",2,"Q1 仿真位形、Q2 终止时刻、Q3 最小螺距、Q4 最短弧长、Q5 最大速度，目标与题面一致。"),
 ("L2.5",2,"约束表含螺线/弦长/间隙/调头边界/相切/速度上限，source 标注题面。"),
 ("L2.6",3,"§7 候选模型对比（纯几何/数值优化/动力学仿真）说明选择依据，机理主线几何闭式+优化精化，机理-方程1-6一致。"),
 ("L2.7",2,"方程1-6 结构完整（螺线/曲率/间隙/弦长/调头弧长/速度放大），含推导。"),
 ("L3.1",2,"求解：几何解析公式、牛顿迭代弦长、网格扫描精化最小螺距、一维搜索调头，方法与几何优化匹配。"),
 ("L3.2",1,"no-exec-artifact: 仅叙述『复杂度O(N·K)秒级完成』，无 implementation_ref/代码路径或明确输出约定。"),
 ("L3.3",2,"no-exec-artifact: 验证方案声明『收敛：积分容差与网格加密验证』，含收敛判据（精确几何解析）。"),
 ("L3.4",1,"no-exec-artifact: 仅称『固定积分容差与网格设置；同输入重复运行一致』，无≥5固定种子列表与 cv<10% 判据。"),
 ("L3.5",1,"no-exec-artifact: 合理性预期给量级（最小螺距略大于板宽、Q5速度上限1.5-2m/s），与题面物理量级相符。"),
 ("L4.1",2,"no-exec-artifact: 基线以圆弧路径解析解对照、直线极限对照作为对照基准。"),
 ("L4.2",1,"no-exec-artifact: 灵敏度仅『板宽±10%、半径比±10%观察关键输出』，未报告弹性系数或鲁棒性边界。"),
 ("L4.3",1,"no-exec-artifact: 极限检验 p→∞ 曲率→0放大→1、w→0 终止时刻→∞。"),
 ("L4.4",2,"no-exec-artifact: 验证（基线/收敛/灵敏度/极限/稳定性）覆盖 Q1-Q5 全部子问题核心目标。"),
 ("L4.5",1,"no-exec-artifact: 叙述式文档未枚举显式 claims 与 evidence_refs，主张-证据对应无结构化映射。"),
])
write(u, d)

print("calibration written:", len(os.listdir(OUT)))
