#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate P15.1 B0 failure attribution table (diagnosis only, no fixes)."""
import json
from pathlib import Path

ROOT = Path(r"C:\Users\Lin\Desktop\Programs\MathModel")
OUT_DIR = ROOT / "research" / "P15" / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Shared evidence strings ──────────────────────────────────────────
EVAL_METHOD = (
    "e2e_metrics.py: method_selection 用 model artifact 的 data.card_id 查方法卡 family，"
    "与 benchmark allowed_model_families 做家族匹配；t3_str 回退用 _method_hit() 对 card_id/name 与 gt_methods 做字符串包含匹配"
)
EVAL_DECOMP = (
    "e2e_metrics.py L270-284: 无 response.decomposition_aligned 时退化为 "
    "min(produced_question_count, gt_sub_question_count)/gt_count（count_ratio）"
)
EVAL_INNOV = (
    "e2e_metrics.py L418-431: innovation 扫描 decision_log.decisions[].knowledge_refs 中 pat- 前缀条目；"
    "无 pat- 引用则 innov_value=0.0"
)
EVAL_MC = (
    "e2e_metrics.py L356-393: model_correctness 依赖外部 response.model_correctness_pct；"
    "缺失时 value=None，仅做 structural check（objective/constraints/variables 存在性）"
)
EVAL_EXP = (
    "e2e_metrics.py L395-405: experiment_validity 统计 result artifact 中 robustness tag 比例和 multi_run>=5；"
    "无 result artifact 时 exp_components 为空 → value=None"
)
EVAL_VAL = (
    "e2e_metrics.py L407-416: validation_reliability = claim 支撑率（status.json evidence 字段）+ paper 存在性；"
    "claims_total=0 且无 main.tex → val_components 为空 → value=None"
)
EVAL_WC = (
    "e2e_metrics.py L433-449: writing_completeness 检查 paper/main.tex 存在性并统计 figures/tables/equations/references；"
    "无 main.tex → value=None"
)
EVAL_E2E = (
    "e2e_metrics.py L451-457: end_to_end 依赖 response.total.awarded/max_score；缺失 → value=None"
)
EVAL_MI = (
    "e2e_metrics.py L484-510: measurement_integrity 判据 v1 = created_by.startswith('agent')；"
    "统计各类型 artifact 中 agent 创建的比例"
)
EVAL_EAF = (
    "e2e_metrics.py L65-79, L249-261: empty_artifact_filter 用 _is_empty_artifact() 判定 "
    "payload=None/[] 且 data=None/{}/仅含空 payload 的空壳 artifact"
)

CARD_COVER = (
    "方法卡库 src/modeling_harness/knowledge/methods/cards/ 共 16 张，family 覆盖：decision_analysis, classical_timeseries, "
    "composite_evaluation, metaheuristics, uncertainty_propagation, multi_objective_optimization, "
    "statistical_modeling, dimensionality_reduction, unsupervised, supervised_learning, timeseries_learning。"
    "无 kinematics/geometric_modeling/dynamic_programming/MDP/game_theory/PDE/finite_difference/queueing_theory 家族卡片"
)

B0_STAGE = (
    "B0 baseline 仅执行 DAG 前 5 节点（problem_understanding→model_construction→method_selection→"
    "solving_strategy→validation_plan），不执行代码运行、实验、论文写作和端到端评分"
)

# ── Per-problem data ─────────────────────────────────────────────────
problems = {
    "2024_A": {
        "project": "p151-2024a-b0",
        "gt_count": 5,
        "produced_q": 1,
        "decomp_score": 20.0,
        "method_score": 0.0,
        "method_chosen": "mc-monte-carlo",
        "method_family": "uncertainty_propagation",
        "method_ref": '["kinematics","geometric_modeling","numerical_solution"]',
        "method_top3": '["mc-monte-carlo","mc-ga","mc-pso"]',
        "method_top1_hit": False,
        "method_top3_hit": False,
        "actual_model_family": "multibody_dynamics（payload.model_family）",
        "method_decision_note": (
            "D001 decision 明确写道：'可用方法卡中无运动学/几何类，最接近的是mc-monte-carlo..."
            "这本身是方法卡覆盖度不足的观测'；实际核心方法为'多体刚体链运动学递推+阿基米德螺线参数化'"
        ),
        "q_subq_in_artifact": 5,
    },
    "2022_C": {
        "project": "p151-2022c-b0",
        "gt_count": 4,
        "produced_q": 1,
        "decomp_score": 25.0,
        "method_score": 100.0,
        "method_chosen": "mc-pca",
        "method_family": "dimensionality_reduction",
        "method_ref": '["clustering","discriminant_analysis","PCA","statistical_analysis"]',
        "method_top3": '["mc-pca","mc-kmeans","mc-xgboost"]',
        "method_top1_hit": True,
        "method_top3_hit": True,
        "method_top1_family_hit": False,
        "actual_model_family": "statistical_classification（payload.model_family）",
        "method_decision_note": (
            "D001 decision：'PCA降维 + K-Means聚类 + XGBoost分类 + OLS回归 + 相关性分析'；"
            "top1_hit=True 来自 _method_hit 字符串回退（card name 含'PCA'匹配 gt_methods'pca'），"
            "但 top1_family_hit=False（dimensionality_reduction 不在 ref 家族中）"
        ),
        "q_subq_in_artifact": 4,
    },
    "2020_B": {
        "project": "p151-2020b-b0",
        "gt_count": 3,
        "produced_q": 1,
        "decomp_score": 33.3,
        "method_score": 0.0,
        "method_chosen": "mc-ga",
        "method_family": "metaheuristics",
        "method_ref": '["dynamic_programming","MDP","game_theory","Monte_Carlo"]',
        "method_top3": '["mc-ga","mc-nsga2","mc-monte-carlo"]',
        "method_top1_hit": False,
        "method_top3_hit": False,
        "actual_model_family": "['dynamic_programming','optimization','markov_decision_process','game_theory']（payload.model_family）",
        "method_decision_note": (
            "D001 decision：'选择遗传算法(mc-ga)作为Q1确定性优化的主求解方法'，"
            "并明确指出'本题无专用动态规划卡'；D002 solving_strategy 实际使用 MDP值迭代+纳什均衡，"
            "但 card_id 标记为 mc-ga（metaheuristics），与 ref 家族无匹配"
        ),
        "q_subq_in_artifact": 3,
    },
    "2018_A": {
        "project": "p151-2018a-b0",
        "gt_count": 3,
        "produced_q": 1,
        "decomp_score": 33.3,
        "method_score": 0.0,
        "method_chosen": "mc-ga",
        "method_family": "metaheuristics",
        "method_ref": '["heat_equation_PDE","parameter_inversion","optimization"]',
        "method_top3": '["mc-ga","mc-monte-carlo","mc-pso"]',
        "method_top1_hit": False,
        "method_top3_hit": False,
        "actual_model_family": "pde（payload.model_family）",
        "method_decision_note": (
            "D001 decision：'采用隐式有限差分法（Crank-Nicolson格式）离散PDE，结合遗传算法/模式搜索进行层厚优化'；"
            "核心方法为 FDM/PDE，但方法卡库无 PDE/finite_difference 家族卡片，"
            "card_id 被迫标记为 mc-ga（仅用于优化子问题），与 ref 家族无匹配"
        ),
        "q_subq_in_artifact": 3,
    },
    "2019_C": {
        "project": "p151-2019c-b0",
        "gt_count": 4,
        "produced_q": 1,
        "decomp_score": 25.0,
        "method_score": 100.0,
        "method_chosen": "mc-monte-carlo",
        "method_family": "uncertainty_propagation",
        "method_ref": '["queuing_analysis","optimization","decision_modeling"]',
        "method_top3": '["mc-monte-carlo","mc-ahp","mc-ga"]',
        "method_top1_hit": False,
        "method_top3_hit": True,
        "method_top1_family_hit": False,
        "actual_model_family": "['queueing_theory','decision_analysis','optimization','simulation']（payload.model_family）",
        "method_decision_note": (
            "D001 decision：'排队论解析模型为骨架、蒙特卡洛仿真为验证、遗传算法处理Q3布局优化'；"
            "top1 chosen=mc-monte-carlo（family=uncertainty_propagation）与 ref 无匹配，top1_hit=False；"
            "top3_hit=True 来自 mc-ahp（card name 含'decision_analysis'）与 gt_methods'decision_analysis' 的字符串回退匹配；"
            "方法卡库无 queueing_theory 家族卡片"
        ),
        "q_subq_in_artifact": 4,
    },
}

attributions = []

def add(pid, metric, b0_score, observed_reason, failure_attr, evidence, confidence, action):
    attributions.append({
        "problem_id": pid,
        "metric": metric,
        "b0_score": b0_score,
        "observed_reason": observed_reason,
        "failure_attribution": failure_attr,
        "evidence": evidence,
        "confidence": confidence,
        "recommended_action": action,
    })

for pid, p in problems.items():
    proj = p["project"]

    # ── 1. method_selection ────────────────────────────────────────
    if p["method_score"] == 0.0:
        add(pid, "method_selection", 0.0,
            f"model artifact M001 的 data.card_id={p['method_chosen']}（family={p['method_family']}）"
            f"与 benchmark allowed_model_families {p['method_ref']} 无家族匹配；top3={p['method_top3']} 亦无匹配。"
            f"但 payload.model_family={p['actual_model_family']} 与 ref 高度相关，"
            f"说明 agent 实际选择了正确方法家族，仅因方法卡库无对应卡片而 card_id 错配。",
            "measurement_failure",
            f"{EVAL_METHOD}；{CARD_COVER}；{proj}/state/registry.json M001.data.card_id={p['method_chosen']}, "
            f"M001.payload.model_family={p['actual_model_family']}；{proj}/state/registry.json D001: {p['method_decision_note']}；"
            f"research/P15/benchmark/CUMCM-Bench-v2.json {pid}.allowed_model_families={p['method_ref']}",
            "high",
            "calibrate_instrument")
    else:  # 100.0
        family_hit = p.get("method_top1_family_hit", False)
        add(pid, "method_selection", 100.0,
            f"method_value=100% 基于 top3_hit_rate，但 top1 chosen={p['method_chosen']}"
            f"（family={p['method_family']}）的 top1_family_hit={family_hit}，top1_hit={p['method_top1_hit']}。"
            f"分数来自字符串回退匹配（_method_hit）而非主路径家族检查。"
            f"payload.model_family={p['actual_model_family']} 与 ref 相关，但 card_id 未反映主方法。",
            "measurement_failure",
            f"{EVAL_METHOD}；{proj}/state/e2e_metrics_report.json method_selection.detail.per_question.Q001: "
            f"top1_chosen={p['method_chosen']}, top1_family_hit={family_hit}, top3_hit={p['method_top3_hit']}；"
            f"{proj}/state/registry.json D001: {p['method_decision_note']}；"
            f"方法卡 family 命名（dimensionality_reduction/uncertainty_propagation）与 benchmark allowed_model_families 命名（PCA/queuing_analysis）存在 taxonomy 映射断层",
            "medium",
            "calibrate_instrument")

    # ── 2. decomposition_coverage ───────────────────────────────────
    add(pid, "decomposition_coverage", p["decomp_score"],
        f"evaluator 用 count_ratio 退化口径：produced_question_count={p['produced_q']} / gt_sub_questions={p['gt_count']} "
        f"= {p['decomp_score']}%。但 Q001 artifact 的 payload.sub_questions 实际包含 {p['q_subq_in_artifact']} 个子问题，"
        f"与 GT 完全对齐（逐条比对文本一致）。低分完全源于 artifact 粒度约定与 evaluator 假设不匹配："
        f"B0 将所有子问题打包进单个 Q001 artifact，而 evaluator 假设一个 question artifact = 一个子问题。",
        "measurement_failure",
        f"{EVAL_DECOMP}；{proj}/state/e2e_metrics_report.json decomposition_coverage.detail: "
        f"gt_sub_questions={p['gt_count']}, produced_questions={p['produced_q']}, mode='count_ratio（无语义对齐评分，退化口径）'；"
        f"{proj}/state/registry.json Q001.payload.sub_questions 含 {p['q_subq_in_artifact']} 条，"
        f"与 research/P15/benchmark/b0_manifests/{pid}/00_problem_understanding.json sub_questions 逐条对应",
        "high",
        "calibrate_instrument")

    # ── 3. innovation ───────────────────────────────────────────────
    add(pid, "innovation", 0.0,
        "decision_log.json 的 decisions 数组中无任何条目包含 knowledge_refs 字段，"
        "更无 pat- 前缀的 pattern 引用。innov_value=0.0 是因为 B0 artifact schema（model-ir-1.0 / b0-baseline-v1）"
        "不包含 knowledge_refs / pattern 引用机制，evaluator 无法检测到任何创新声明。"
        "这不是 agent 未产生创新思维，而是测量通道在 B0 阶段不存在。",
        "measurement_failure",
        f"{EVAL_INNOV}；{proj}/state/decision_log.json 全部 3 条 decision（D001-D003）均无 knowledge_refs 字段；"
        f"{proj}/state/registry.json D001-D003 payload 含 decision/alternatives/reasoning/criteria 但无 pattern 引用结构；"
        f"B0 prompt_or_skill_version='b0-baseline-v1' 未定义 pattern 引用输出 schema",
        "high",
        "calibrate_instrument")

    # ── 4. model_correctness ────────────────────────────────────────
    add(pid, "model_correctness", None,
        "response.model_correctness_pct 未提供（B0 阶段无外部语义评分输入），value=None。"
        "structural check 结果为 PASS：M001 的 data.objective（非空字符串）、data.constraints（非空列表）、"
        "data.variables（非空列表）均存在。模型 artifact 结构完整，但语义正确性无法在 B0 阶段评估。",
        "not_applicable",
        f"{EVAL_MC}；{proj}/state/e2e_metrics_report.json model_correctness.detail: "
        f"model_correctness='UNAVAILABLE', source='外部评分缺失（null/n/a）', model_correctness_structural='PASS'；"
        f"structural_check.per_model.M001: objective=True, constraints=True, variables=True；"
        f"{B0_STAGE}",
        "high",
        "no_action")

    # ── 5. experiment_validity ──────────────────────────────────────
    add(pid, "experiment_validity", None,
        "registry 中无 result 类型 artifact（results=0），exp_components 为空列表 → value=None。"
        "B0 阶段仅完成问题理解、模型构建、方法选择、求解策略和验证计划，不执行代码运行和实验，"
        "因此不产生 result artifact。无 robustness tag、无 multi_run 数据可统计。",
        "not_applicable",
        f"{EVAL_EXP}；{proj}/state/e2e_metrics_report.json experiment_validity.detail: "
        f"results=0, with_robustness_tags=0, multi_run_ge5=0；"
        f"{proj}/state/registry.json artifact_ids 仅含 Q001/M001/D001-D003，无 result/experiment 类型；"
        f"{B0_STAGE}",
        "high",
        "no_action")

    # ── 6. validation_reliability ───────────────────────────────────
    add(pid, "validation_reliability", None,
        "claims_total=0（status.json evidence 字段无 claim 记录）且 paper/main.tex 不存在，"
        "val_components 为空 → value=None。B0 阶段不产生 claim artifact 和论文，"
        "验证计划（D003）仅为规划文档，未执行验证，因此无 claim 支撑率可计算。",
        "not_applicable",
        f"{EVAL_VAL}；{proj}/state/e2e_metrics_report.json validation_reliability.detail: "
        f"claims_supported=0, claims_total=0, paper_present=False；"
        f"{proj}/state/registry.json 无 claim 类型 artifact；{proj}/paper/ 目录不存在；"
        f"{B0_STAGE}",
        "high",
        "no_action")

    # ── 7. writing_completeness ─────────────────────────────────────
    add(pid, "writing_completeness", None,
        "paper/main.tex 不存在 → value=None。B0 阶段不执行论文写作节点，无 LaTeX 源文件、"
        "无 references.bib、无图表和公式计数。writing_completeness 指标的所有输入前提在 B0 均不满足。",
        "not_applicable",
        f"{EVAL_WC}；{proj}/state/e2e_metrics_report.json writing_completeness.detail: main_tex=False；"
        f"{proj}/paper/ 目录不存在；{B0_STAGE}",
        "high",
        "no_action")

    # ── 8. end_to_end ───────────────────────────────────────────────
    add(pid, "end_to_end", None,
        "response.total 未提供（无 awarded/max_score）→ value=None。B0 阶段不执行端到端 rubric 评分，"
        "无总分输入。end_to_end 指标完全依赖外部评分响应，B0 不产生该数据。",
        "not_applicable",
        f"{EVAL_E2E}；{proj}/state/e2e_metrics_report.json end_to_end.detail: rubric_total=null；"
        f"B0 运行无 response JSON 传入 compute_e2e_metrics()；{B0_STAGE}",
        "high",
        "no_action")

    # ── 9. measurement_integrity ────────────────────────────────────
    add(pid, "measurement_integrity", 0.0,
        f"overall_real_artifact=0/5：判据 created_by.startswith('agent') 下，5 个 artifact 无一命中。"
        f"但所有 artifact 的 provenance 子文档均显示 executor_type='external_agent', agent_identity='doubao'，"
        f"证明这些确实是 agent 创建的产物。created_by 字段填充的是 DAG 节点名"
        f"（problem_understanding/model_construction/method_selection/solving_strategy/validation_plan），"
        f"而非 'agent...' 前缀。判据 v1 与 B0 注册约定不匹配，导致测量完整性被严重低估。"
        f"experiment/validation/writing realization 为 0/0（null），因 B0 无对应类型 artifact。",
        "measurement_failure",
        f"{EVAL_MI}；{proj}/state/e2e_metrics_report.json measurement_integrity: "
        f"overall_real_artifact={{numerator:0, denominator:5, value:0.0}}, "
        f"experiment/validation/writing_realization={{numerator:0, denominator:0, value:null}}；"
        f"{proj}/state/registry.json 各 artifact.created_by ∈ "
        f"['problem_understanding','model_construction','method_selection','solving_strategy','validation_plan']，"
        f"provenance.executor_type='external_agent', provenance.agent_identity='doubao'",
        "high",
        "calibrate_instrument")

    # ── 10. empty_artifact_filter ───────────────────────────────────
    add(pid, "empty_artifact_filter", 0,
        "total_excluded=0，registry_empty_total=0：所有 5 个 artifact（Q001/M001/D001-D003）"
        "均有非空 payload（含 sub_questions/model_spec/decision 等实质内容），无空壳 artifact。"
        "空壳过滤器正常工作，未误排除任何 artifact。此指标无失败。",
        "not_applicable",
        f"{EVAL_EAF}；{proj}/state/e2e_metrics_report.json empty_artifact_filter: "
        f"total_excluded=0, registry_empty_total=0, per_type={{question:0, result:0, model:0, _all_types_total:0}}；"
        f"{proj}/state/registry.json Q001.payload.sub_questions 非空，M001.payload.variables/constraints/equations 非空，"
        f"D001-D003.payload.decision/reasoning 非空",
        "high",
        "no_action")

# ── Summary ───────────────────────────────────────────────────────────
from collections import Counter
attr_counts = Counter(a["failure_attribution"] for a in attributions)
summary = {
    "total_records": len(attributions),
    "measurement_failure": attr_counts.get("measurement_failure", 0),
    "capability_failure": attr_counts.get("capability_failure", 0),
    "mixed": attr_counts.get("mixed", 0),
    "unresolved": attr_counts.get("unresolved", 0),
    "not_applicable": attr_counts.get("not_applicable", 0),
}

output = {"attributions": attributions, "summary": summary}

# Write JSON
json_path = OUT_DIR / "_attribution_table.json"
json_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"JSON written: {json_path} ({len(attributions)} records)")

# Write Markdown
md_lines = [
    "# P15.1 B0 Failure Attribution Table",
    "",
    f"**生成时间**: 2026-09-08 | **项目数**: 5 | **记录数**: {len(attributions)}",
    "",
    "## 归因分布汇总",
    "",
    "| failure_attribution | count |",
    "|---|---|",
]
for k in ["measurement_failure", "capability_failure", "mixed", "unresolved", "not_applicable"]:
    md_lines.append(f"| {k} | {summary[k]} |")
md_lines += ["", "---", "", "## 逐项归因明细", ""]

# Group by problem
for pid in ["2024_A", "2022_C", "2020_B", "2018_A", "2019_C"]:
    md_lines.append(f"### {pid}")
    md_lines.append("")
    md_lines.append("| metric | b0_score | attribution | confidence | recommended_action |")
    md_lines.append("|---|---|---|---|---|")
    for a in attributions:
        if a["problem_id"] == pid:
            score = "n/a" if a["b0_score"] is None else a["b0_score"]
            md_lines.append(
                f"| {a['metric']} | {score} | {a['failure_attribution']} | "
                f"{a['confidence']} | {a['recommended_action']} |"
            )
    md_lines.append("")
    # Detailed observations for this problem
    for a in attributions:
        if a["problem_id"] == pid:
            score = "n/a" if a["b0_score"] is None else a["b0_score"]
            md_lines.append(f"**{a['metric']}** ({score}) — {a['failure_attribution']} [{a['confidence']}]")
            md_lines.append("")
            md_lines.append(f"- **observed_reason**: {a['observed_reason']}")
            md_lines.append(f"- **evidence**: {a['evidence']}")
            md_lines.append(f"- **recommended_action**: {a['recommended_action']}")
            md_lines.append("")

md_path = OUT_DIR / "_attribution_table.md"
md_path.write_text("\n".join(md_lines), encoding="utf-8")
print(f"Markdown written: {md_path}")
print(f"Summary: {summary}")
