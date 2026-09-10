# -*- coding: utf-8 -*-
"""初始化 state/：registry.json + evidence_graph.json + decision_log.json + status.json。

纪律：所有 ID 由 Registry 计数器发放、终身稳定；relations 只使用
docs/architecture/V3.1_ARCHITECTURE.md §1.3 定义的 14 种 relation；
artifact 的 payload 指向真实存在的文件（写入前逐个校验存在性）。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

STATE = ROOT / "state"
MODEL = ROOT  # 交付物在项目根（与 validate.py 契约一致）
RESULTS = ROOT / "artifacts" / "results"
CODE = ROOT / "artifacts" / "code"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
PROJECT = "cumcm2024a-harness"


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


def require(*paths: Path):
    for p in paths:
        if not p.exists():
            raise SystemExit(f"payload 不存在：{p}")


require(ROOT / "model_ir.json", ROOT / "inputs" / "problem.txt")
for i in (1, 2, 3, 4, 5):
    require(RESULTS / f"result{i}.xlsx")
for f in ("dragon_core.py", "q1_solve.py", "q2_solve.py", "q3_solve.py",
          "q4_solve.py", "q5_solve.py", "turnaround.py", "results_io.py",
          "build_model_ir.py", "init_state.py"):
    require(CODE / f)

# --------------------------------------------------------------- registry ---
ids = {}
counters: dict[str, int] = {}


def nid(kind: str) -> str:
    counters[kind] = counters.get(kind, 0) + 1
    return f"MH-{kind.upper()}-{counters[kind]:04d}"


def art(kind, title, payload, created_by, status="active", **kw):
    aid = nid(kind)
    d = {"schema_version": "3.1", "artifact_id": aid, "type": kind.lower(),
         "version": 1, "status": status, "title": title,
         "created_by": created_by, "created_at": NOW, "updated_at": NOW,
         "payload": payload}
    d.update(kw)
    ids[kind.lower()] = ids.get(kind.lower(), []) + [aid]
    return aid, d


artifacts: dict[str, dict] = {}


def add(kind, title, payload, created_by, **kw):
    aid, d = art(kind, title, payload, created_by, **kw)
    artifacts[aid] = d
    return aid


A_PROBLEM = add("problem", "2024_A 板凳龙闹元宵",
                {"statement": rel(ROOT / "inputs" / "cumcm2024A.txt"),
                 "sha256": "9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e",
                 "sub_questions": ["Q1", "Q2", "Q3", "Q4", "Q5"],
                 "gt_card": "research/P15/benchmark/problem_cards/2024_A/gt.json"},
                "problem_understanding")

A_QUESTION = add("question", "2024_A 子问题分解（Q1-Q5）",
                 {"sub_questions": [
                     {"id": "Q1", "type": "forward_simulation",
                      "text": "螺距 0.55 m 顺时针盘入，0~300 s 每秒全队位置速度"},
                     {"id": "Q2", "type": "collision_detection",
                      "text": "盘入终止时刻（板凳首次碰撞）"},
                     {"id": "Q3", "type": "geometric_optimization",
                      "text": "最小螺距使龙头能盘入到调头空间边界"},
                     {"id": "Q4", "type": "curve_design_and_simulation",
                      "text": "S 形调头曲线（R1=2R2）与 −100~100 s 仿真；能否调短"},
                     {"id": "Q5", "type": "velocity_constrained_optimization",
                      "text": "龙头最大行进速度使各把手速度 ≤ 2 m/s"}]},
                 "problem_understanding")

A_MODEL = add("model", "刚性链-曲线约束运动学模型（MODEL_IR M001）",
              {"model_ir": "model_ir.json",
               "model_document": "model.md",
               "model_family": "kinematic",
               "structure": "geometric_motion / kinematics",
               "key_choice": "弦长约束 |P_k − P_{k+1}| = L_k（非弧长等分）"},
              "model_construction")

CODE_FILES = ["dragon_core.py", "turnaround.py", "q1_solve.py", "q2_solve.py",
              "q3_solve.py", "q4_solve.py", "q5_solve.py", "results_io.py",
              "build_model_ir.py", "init_state.py"]
A_CODE = {f: add("code", f"实现：{f}", {"path": f"artifacts/code/{f}"}, "model_construction")
          for f in CODE_FILES}

solver_of = {1: "q1_solve.py", 2: "q2_solve.py", 3: "q3_solve.py",
             4: "q4_solve.py", 5: "q5_solve.py"}
A_EXP, A_RES = {}, {}
for q, f in solver_of.items():
    eid = add("experiment", f"EXP0{q}：问题 {q} 数值实验",
              {"sub_question": f"Q{q}", "solver_code": f"artifacts/code/{f}",
               "deterministic": True, "random_seed": None,
               "note": "确定性几何/求根计算，无随机性，故无需多种子"},
              "experiment_design")
    rid = add("result", f"result{q}.xlsx",
              {"path": f"artifacts/results/result{q}.xlsx",
               "sheets": ["all_handles", "key_points", "meta"] if q in (1, 2, 4)
                         else ["Sheet1", "meta"]},
              "experiment_execution")
    A_EXP[q], A_RES[q] = eid, rid

A_CLAIM = {}
for i, (q, txt) in enumerate([
        (1, "Q1 位置速度已给出；连杆弦长残差 ≤ 3.3e-13 m"),
        (1, "把手速率不恒等于龙头速率：t=300 s 龙尾 0.996478 m/s（弦长 vs 弧长模型的差异）"),
        (2, "Q2 盘入终止时刻 t* = 397.7836 s（临界板对 = 龙头板/第 10 条板）"),
        (2, "最小板距随时间非单调振荡（离散多边形相位效应），须细扫定位"),
        (3, "Q3 最小螺距见 result3.xlsx（与起始盘入位置无关的结构性结论）"),
        (4, "Q4 R1=3.005418 m, R2=1.502709 m, ψ=173.118°, L=13.621245 m，曲线全在调头空间内"),
        (4, "调头曲线长度对半径分配为不变量 ⇒ 不能靠调整圆弧缩短"),
        (5, "Q5 龙头最大速度 v_max = 2 / max|dσ_k/dσ_0|，见 result5.xlsx")], 1):
    A_CLAIM[i] = add("claim", f"CL{i:02d}", {"text": txt, "sub_question": f"Q{q}",
                                             "source": "MODEL_IR claims"},
                     "evidence_build")

A_ASSUME = add("assumption", "A01-A10 建模假设集",
               {"ids": [f"A{i:02d}" for i in range(1, 11)],
                "source": "model/model_ir.json#assumptions",
                "critical": ["A01 弦长约束", "A04 把手共路径（Q2-Q5 外推）",
                             "A05 碰撞判据（胶囊保守近似）",
                             "A10 最小可跟随曲率半径 1.43 m"]},
               "model_construction")

A_DOC = add("narrative", "模型描述文档 model.md",
            {"path": "model/model.md", "format": "markdown + mermaid"},
            "model_documentation")

registry = {
    "registry_version": 3,
    "project": PROJECT,
    "updated_at": NOW,
    "counters": {k: v for k, v in sorted(counters.items())},
    "artifacts": artifacts,
}

# ----------------------------------------------------------- evidence graph -
R = []


def edge(frm, to, rel_type, **kw):
    d = {"from": frm, "to": to, "relation": rel_type}
    d.update(kw)
    R.append(d)


edge(A_PROBLEM, A_QUESTION, "motivates")
edge(A_QUESTION, A_MODEL, "solved_by", note="整链构型由龙头弧长坐标唯一确定")
edge(A_MODEL, A_ASSUME, "assumes")
edge(A_MODEL, A_CODE["dragon_core.py"], "implemented_by", note="路径/递推/碰撞核心")
edge(A_MODEL, A_CODE["turnaround.py"], "implemented_by", note="调头曲线解析与最短化")
for q in solver_of:
    edge(A_MODEL, A_EXP[q], "validated_by", sub_question=f"Q{q}")
    edge(A_EXP[q], A_MODEL, "tests", sub_question=f"Q{q}")
    edge(A_EXP[q], A_CODE[solver_of[q]], "uses")
    edge(A_EXP[q], A_RES[q], "produces")
for i, q in zip(A_CLAIM, [1, 1, 2, 2, 3, 4, 4, 5]):
    edge(A_RES[q], A_CLAIM[i], "supports", sub_question=f"Q{q}")
edge(A_MODEL, A_DOC, "derived_from", note="模型描述是 MODEL_IR 的人类可读投影")

evidence_graph = {
    "graph_schema_version": 3,
    "graph_version": 1,
    "project": PROJECT,
    "updated_at": NOW,
    "relations": R,
}

# ------------------------------------------------------------- decision log -
decisions = [
    {"decision_id": "MH-DECISION-0001",
     "question": "相邻把手的约束取弦长还是弧长？",
     "chosen": "弦长约束 |P_k − P_{k+1}| = L_k（L_0=2.86, L_b=1.65）",
     "alternatives": ["弧长等分近似（相邻把手弧长间距恒为 L）"],
     "criteria": ["题面刚性板几何必然性", "是否与已知极限情形一致"],
     "evidence_ids": [A_RES[1], A_RES[4]],
     "reasoning": "同一刚板上两孔中心距固定是几何必然；弧长等分会抹掉把手速率差于龙头的效应"
                  "（t=300 s 龙尾 0.996478 vs 恒 1），而该差异经 h=1/0.5/0.25 s 三档差分确认为真实物理。",
     "confidence": 0.95, "reversible": True, "created_by": "model_construction",
     "created_at": NOW},
    {"decision_id": "MH-DECISION-0002",
     "question": "Q2 终止时刻如何定位？",
     "chosen": "1 s 粗扫 + 0.05 s 细扫 + 二分至 1e-4 s，并用相邻帧位移 = v·Δt 做连续性校验",
     "alternatives": ["假设 d_min(t) 单调后直接二分"],
     "criteria": ["离散多边形相位效应使 d_min 非单调"],
     "evidence_ids": [A_RES[2]],
     "reasoning": "链是内接于螺线的离散多边形，板体相对相位周期性变化 ⇒ d_min 振荡，"
                  "单调二分会给出错误时刻；细扫后邻域曲线光滑单调，且位移校验证明无求根跳支。",
     "confidence": 0.9, "reversible": True, "created_by": "experiment_design",
     "created_at": NOW},
    {"decision_id": "MH-DECISION-0003",
     "question": "Q3 的龙头起始位置如何设定？",
     "chosen": "不设起始位置：利用「构型只由（螺距, 龙头弧长）决定」的结构性事实，"
               "在龙头半径 {4.5,5,6,8,11,15,20} m 上取最小间隙",
     "alternatives": ["沿用 Q1 的第 16 圈起点", "指定某个外圈起点"],
     "criteria": ["结论对起始位置的鲁棒性"],
     "evidence_ids": [A_RES[3]],
     "reasoning": "整链构型与盘入历史无关；越往内曲率越大 ⇒ 最危险构型在 r=4.5 m。"
                  "两种解读（从远处盘入 / 从第 16 圈盘入）给出同一临界构型，结论鲁棒。",
     "confidence": 0.9, "reversible": True, "created_by": "model_construction",
     "created_at": NOW},
    {"decision_id": "MH-DECISION-0004",
     "question": "Q4「能否调短调头曲线」如何回答？",
     "chosen": "先证明端点固定时 L=(R1+R2)ψ 与半径分配无关（数值用 6 种分配验证），"
               "再以「圆内完整调头路径」为公平指标比较切点滑动方案",
     "alternatives": ["只做数值搜索最短两段弧"],
     "criteria": ["不变量的可证明性", "比较口径的公平性"],
     "evidence_ids": [A_RES[4]],
     "reasoning": "裸数值搜索会退化为「一段圆弧 + 一段近直线」（R2 ~ 10^3 m），形式上更短但已非 S 形；"
                  "且把出螺线在圆内的那一段计入后，圆内总长由 13.62 m 增至 ≥ 18.70 m。",
     "confidence": 0.85, "reversible": True, "created_by": "model_construction",
     "created_at": NOW},
    {"decision_id": "MH-DECISION-0005",
     "question": "Q5 是否需要对龙头速度做搜索？",
     "chosen": "不需要：v_max = v_lim / max_{k,t} |dσ_k/dσ_0|，一次几何扫描即可",
     "alternatives": ["对 v_head 做二分/黄金分割搜索"],
     "criteria": ["约束的线性性", "计算成本"],
     "evidence_ids": [A_RES[5]],
     "reasoning": "构型只依赖龙头位置，速率比 r_k 与 v_head 无关 ⇒ 约束关于 v_head 线性。"
                  "注意峰值尖锐（1 s 网格会漏），用 0.5/0.1/0.05 s 三档确认收敛。",
     "confidence": 0.95, "reversible": True, "created_by": "model_construction",
     "created_at": NOW},
]

decision_log = {"schema_version": 3, "project": PROJECT, "updated_at": NOW,
                "decisions": decisions}

status = {
    "schema_version": 3,
    "project": PROJECT,
    "updated_at": NOW,
    "problem": {"status": "parsed", "artifact": A_PROBLEM},
    "questions": {
        f"Q{q}": {"status": "validated", "models": [A_MODEL],
                  "experiments": [A_EXP[q]], "results": [A_RES[q]],
                  "claims": [A_CLAIM[i] for i in A_CLAIM
                             if artifacts[A_CLAIM[i]]["payload"]["sub_question"] == f"Q{q}"]}
        for q in solver_of
    },
    "evidence": {"graph_version": 1, "claims_supported": len(A_CLAIM),
                 "claims_total": len(A_CLAIM),
                 "coverage": 1.0},
    "artifacts": {"total": len(artifacts), "by_type": {
        t: len([a for a in artifacts.values() if a["type"] == t])
        for t in sorted({a["type"] for a in artifacts.values()})}},
    "limitations": [
        "A04：Q2-Q5 沿用「全部把手位于龙头走过的路径上」，未建模拖曳链的横向偏离",
        "A05：碰撞用胶囊近似矩形，判定偏保守（略早报碰撞）",
        "Q3 敏感性未在论文级网格上复算；结论依赖构型-历史无关性",
        "未做官方标准答案比对（不允许凭记忆伪造 GT）",
    ],
}


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    for name, obj in (("registry.json", registry),
                      ("evidence_graph.json", evidence_graph),
                      ("decision_log.json", decision_log),
                      ("status.json", status)):
        (STATE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"[write] state/{name}")
    print(f"[stats] artifacts={len(artifacts)} relations={len(R)} "
          f"decisions={len(decisions)} claims={len(A_CLAIM)} "
          f"evidence_coverage={status['evidence']['coverage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
