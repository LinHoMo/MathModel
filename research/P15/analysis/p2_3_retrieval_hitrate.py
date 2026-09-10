# -*- coding: utf-8 -*-
"""P2-3 检索命中率分析：区分「检索失败」vs「知识无用」。

问题：K001 知识注入 negative——到底是检索没把对的卡拿出来，还是
知识本身无用？本分析机械回答前者：对 8 题（K003 同题集）构造问题
特征 → KnowledgeRetriever.recommend → 检查 ground-truth 方法卡
（由官方标准解法 family 指派）是否在 top-k 内。

判定口径：
- hit@k 高 → K001 negative 不是检索失败（指向知识本身无效/剂量/
  测量问题——与 K001 ATTRIBUTION 结论一致）
- hit@k 低 → 检索是瓶颈 → P2-3 实验（直接注入 vs 检索后注入）有意义
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "core"))

from runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402

# ground-truth 卡：由 CUMCM 官方/标准解法 family 指派（见报告附录）
PROBLEM_GT = {
    "2011_B": "mc-dp",            # 最短路/覆盖 → DP（shortest_path 类）
    "2017_B": "mc-ols",           # 定价回归 → OLS
    "2018_A": "mc-numerical-pde", # 热传导/参数反演 → 数值 PDE
    "2018_B": "mc-dp",            # RGV 调度 → DP（resource_allocation 类）
    "2019_C": "mc-queuing-theory",# 出租车调度 → 排队论
    "2020_B": "mc-dp",            # 穿越沙漠 → MDP/DP
    "2022_C": "mc-kmeans",        # 玻璃成分分类 → 聚类
    "2024_A": "mc-numerical-pde", # 板凳龙运动学 → 数值积分/ODE
}

# 题目 family → 检索特征（problem_types 是 recommend 主打分键）
PROBLEM_FEATURES = {
    "2011_B": {"problem_types": ["shortest_path", "resource_allocation"],
               "has_data": True, "objectives": 1},
    "2017_B": {"problem_types": ["regression", "pricing"],
               "has_data": True, "sample_size": "large", "objectives": 2},
    "2018_A": {"problem_types": ["heat_transfer", "diffusion"],
               "has_data": True, "sample_size": "medium", "objectives": 2},
    "2018_B": {"problem_types": ["scheduling", "resource_allocation"],
               "has_data": True, "time_series": True, "objectives": 2},
    "2019_C": {"problem_types": ["random_service_system", "taxi_dispatch"],
               "has_data": True, "time_series": True, "objectives": 2},
    "2020_B": {"problem_types": ["sequential_decision", "inventory_control"],
               "has_data": True, "time_series": True, "uncertainty": True,
               "objectives": 2},
    "2022_C": {"problem_types": ["clustering", "classification"],
               "has_data": True, "sample_size": "small", "objectives": 1},
    "2024_A": {"problem_types": ["kinematics", "optimization"],
               "has_data": True, "time_series": True, "objectives": 3},
}


def main() -> dict:
    r = KnowledgeRetriever(str(REPO / "core" / "knowledge"))
    rows = []
    for pid, gt in PROBLEM_GT.items():
        feats = PROBLEM_FEATURES[pid]
        recs = r.recommend(feats, top_k=10)
        top = [(rec.card.card_id, round(rec.score, 2)) for rec in recs]
        ids = [cid for cid, _ in top]
        rank = ids.index(gt) + 1 if gt in ids else None
        rows.append({
            "problem": pid,
            "ground_truth_card": gt,
            "top10": top,
            "gt_rank": rank,
            "hit@3": rank is not None and rank <= 3,
            "hit@5": rank is not None and rank <= 5,
            "hit@10": rank is not None,
        })

    n = len(rows)
    out = {
        "analysis": "P2-3 retrieval hit-rate（检索失败 vs 知识无用 判别）",
        "n_problems": n,
        "hit@3": sum(1 for r_ in rows if r_["hit@3"]),
        "hit@5": sum(1 for r_ in rows if r_["hit@5"]),
        "hit@10": sum(1 for r_ in rows if r_["hit@10"]),
        "rows": rows,
        "verdict": None,
    }
    h3 = out["hit@3"] / n
    if h3 >= 0.75:
        out["verdict"] = ("hit@3>=75%：检索基本可靠 → K001 negative 不是"
                          "「检索失败」→ 指向知识效用/剂量/测量维度"
                          "（与 K001 ATTRIBUTION 一致）")
    elif h3 >= 0.4:
        out["verdict"] = ("hit@3 中低：检索部分失效 → P2-3 直接注入 vs "
                          "检索后注入实验必要（可区分两类失败）")
    else:
        out["verdict"] = ("hit@3 低：检索是主要瓶颈 → 优先修检索/特征"
                          "工程，再谈知识效用")
    return out


if __name__ == "__main__":
    res = main()
    print(json.dumps(res, ensure_ascii=False, indent=1))
    out_p = REPO / "research" / "P15" / "analysis" / "p2_3_retrieval_hitrate.json"
    out_p.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    print("written:", out_p)
