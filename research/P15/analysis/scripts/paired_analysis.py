#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paired_analysis.py — P15-K001 配对/区组分析（先冻结，后看数据）

分析单位：problem(block) × condition(treatment) × rep。
**不做跨题裸均值相减**：先在每个 block 内算条件均值与差值，再跨 block 聚合。

估计量（预注册 §2.2 / §7.2）：
    Δ_K    = mean(B,D) − mean(A,C)
    Δ_C    = mean(C,D) − mean(A,B)
    Δ_I    = (D − B) − (C − A)
    Δ_Sham = B − E                    （robustness，非主检验）

区间估计：cluster bootstrap（对 problem 重采样，10 000 次，seed=42）→ 95% 百分位 CI。
显著性：符号置换检验（次要；block=3 时最小 p=0.25，见预注册 §7.3 功效声明）。

用法:
    py -3.12 research/P15/analysis/scripts/paired_analysis.py --freeze   # DATA FREEZE
    py -3.12 research/P15/analysis/scripts/paired_analysis.py            # 分析 + 报告
    py -3.12 research/P15/analysis/scripts/paired_analysis.py --selftest # 用合成数据自检

零第三方依赖（标准库）。
"""
from __future__ import annotations

import json
import random
import shutil
import sys
from pathlib import Path

P15 = Path(__file__).resolve().parents[2]      # research/P15
ROOT = P15.parent.parent                       # 仓库根
sys.path.insert(0, str(P15 / "scripts"))
import k001_common as K  # noqa: E402

RAW = K.ANALYSIS / "raw"
FROZEN = K.ANALYSIS / "frozen"
SCORES = RAW / "scores"
REPORT = K.ANALYSIS / "reports" / "P15-K001-REPORT.md"

SEED = 42
N_BOOT = 10000

L1 = ["L1.1", "L1.2", "L1.3", "L1.4", "L1.5"]
L2 = ["L2.1", "L2.2", "L2.3", "L2.4", "L2.5", "L2.6", "L2.7"]
L3 = ["L3.1", "L3.2", "L3.3", "L3.4", "L3.5"]
L4 = ["L4.1", "L4.2", "L4.3", "L4.4", "L4.5"]
L1_MAX, L2_MAX, L3_MAX, L4_MAX = 9, 15, 9, 9

PRIMARY_DIMS = ["L2.1", "L2.2", "L2.4", "L2.5", "L2.6", "L2.7"]   # 13 分
STRUCT_DIMS = ["L2.1", "L2.2", "L2.7"]                            # 6 分
MATH_DIMS = ["L2.4", "L2.5", "L2.6"]                              # 7 分


def _sum(dims: dict, keys: list) -> int:
    return int(sum(int(dims[k]["score"]) for k in keys))


def compute_vector(score: dict) -> dict:
    dims = score["dimensions"]
    det = score.get("deterministic", {}) or {}
    alignment = _sum(dims, L1) / L1_MAX * 100
    structure = _sum(dims, STRUCT_DIMS) / 6 * 100
    mathematics = _sum(dims, MATH_DIMS) / 7 * 100
    mcq = _sum(dims, PRIMARY_DIMS) / 13 * 100
    validation = _sum(dims, L4) / L4_MAX * 100
    ratio = float(det.get("undeclared_symbol_ratio") or 0.0)
    idx_flag = 1 if det.get("index_inconsistency") else 0
    consistency = max(0.0, min(100.0, 100 * (1 - ratio) - 20 * idx_flag))
    total = int(det.get("total_claims") or 0)
    sup = int(det.get("supported_claims") or 0)
    support = (sup / total * 100) if total else 0.0
    return {
        "alignment": round(alignment, 2), "structure": round(structure, 2),
        "mathematics": round(mathematics, 2), "consistency": round(consistency, 2),
        "validation": round(validation, 2), "support": round(support, 2),
        "mcq_primary": round(mcq, 2),
        "L1_total": _sum(dims, L1), "L2_total": _sum(dims, L2),
        "L3_total": _sum(dims, L3), "L4_total": _sum(dims, L4),
    }


def load_records() -> list:
    """合并盲评得分 + 确定性指标 + （解封的）condition。"""
    cmap = K.read_json(K.KEY / "condition_map.json")["map"]
    recs = []
    for p in sorted(SCORES.glob("*.json")):
        if p.name.endswith(".template.json"):
            continue
        s = K.read_json(p)
        sid = s["submission_id"]
        if sid not in cmap:
            continue
        cond = cmap[sid]
        vec = compute_vector(s)
        recs.append({
            "submission_id": sid, "problem_id": cond["problem_id"],
            "block_role": cond["block_role"], "arm": cond["arm"],
            "rep": cond["rep"], "batch": cond["batch"],
            "vector": vec,
            "method_family": (s.get("deterministic") or {}).get("method_family_identified"),
            "failure_modes": s.get("failure_modes", []),
            "evaluator_model": (s.get("evaluator") or {}).get("model", ""),
        })
    return recs


def condition_means(recs: list, metric: str) -> dict:
    """{problem: {arm: mean over reps}}"""
    acc = {}
    for r in recs:
        acc.setdefault(r["problem_id"], {}).setdefault(r["arm"], []).append(r["vector"][metric])
    return {p: {a: sum(v) / len(v) for a, v in arms.items()} for p, arms in acc.items()}


def deltas(means: dict) -> dict | None:
    m = means
    if not all(a in m for a in ("A", "B", "C", "D")):
        return None
    dk = ((m["B"] + m["D"]) / 2) - ((m["A"] + m["C"]) / 2)
    dc = ((m["C"] + m["D"]) / 2) - ((m["A"] + m["B"]) / 2)
    di = (m["D"] - m["B"]) - (m["C"] - m["A"])
    dsham = (m["B"] - m["E"]) if "E" in m else None
    return {"delta_K": dk, "delta_C": dc, "delta_I": di, "delta_Sham": dsham}


def bootstrap_ci(values: list, n: int = N_BOOT, seed: int = SEED) -> tuple:
    """cluster bootstrap：对 block 重采样，返回 95% 百分位 CI。"""
    if not values:
        return (None, None)
    rng = random.Random(seed)
    k = len(values)
    means = []
    for _ in range(n):
        sample = [values[rng.randrange(k)] for _ in range(k)]
        means.append(sum(sample) / k)
    means.sort()
    lo = means[int(0.025 * n)]
    hi = means[min(n - 1, int(0.975 * n))]
    return (lo, hi)


def sign_permutation_p(values: list) -> float | None:
    """双侧符号置换检验；返回 p 值（block 少时功效极低，仅作次要证据）。"""
    if not values:
        return None
    n = len(values)
    obs = abs(sum(values) / n)
    cnt = 0
    total = 2 ** n
    for mask in range(total):
        s = 0.0
        for i in range(n):
            s += values[i] if (mask >> i) & 1 else -values[i]
        if abs(s / n) >= obs - 1e-12:
            cnt += 1
    return cnt / total


def analyze(recs: list) -> dict:
    primary = [r for r in recs if r["block_role"] == "main"]
    gen = [r for r in recs if r["block_role"] == "generalization"]

    out = {"n_records": len(recs), "n_primary": len(primary), "n_generalization": len(gen),
           "metrics": {}}

    for metric in ["mcq_primary", "structure", "mathematics", "alignment",
                   "consistency", "validation", "support"]:
        cm = condition_means(primary, metric)
        per_problem = {p: deltas(m) for p, m in cm.items()}
        per_problem = {p: d for p, d in per_problem.items() if d}
        agg = {}
        for key in ["delta_K", "delta_C", "delta_I", "delta_Sham"]:
            vals = [d[key] for d in per_problem.values() if d.get(key) is not None]
            if not vals:
                continue
            lo, hi = bootstrap_ci(vals)
            agg[key] = {
                "point": round(sum(vals) / len(vals), 2),
                "ci95": [round(lo, 2), round(hi, 2)],
                "n_blocks": len(vals),
                "per_block": {p: round(d[key], 2) for p, d in per_problem.items() if d.get(key) is not None},
                "sign_perm_p": round(sign_permutation_p(vals), 4),
            }
        out["metrics"][metric] = {
            "condition_means": {p: {a: round(v, 2) for a, v in m.items()} for p, m in cm.items()},
            "effects": agg,
        }

    # RQ5：方法族识别 vs 构造质量
    fam = {}
    for r in primary:
        allowed = set(K.problem_index()[r["problem_id"]]["allowed_model_families"])
        ok = r["method_family"] in allowed
        fam.setdefault(r["arm"], []).append(1.0 if ok else 0.0)
    out["rq5_method_family_hit_rate"] = {
        a: round(sum(v) / len(v), 3) for a, v in sorted(fam.items())
    }

    # RQ4：failure mode 分布
    fm = {}
    for r in recs:
        for f in r["failure_modes"]:
            fm.setdefault(f, {}).setdefault(r["arm"], 0)
            fm[f][r["arm"]] += 1
    out["rq4_failure_modes"] = fm

    # 泛化观察（单列，不并入主检验）
    if gen:
        cmg = condition_means(gen, "mcq_primary")
        out["generalization_condition_means"] = {
            p: {a: round(v, 2) for a, v in m.items()} for p, m in cmg.items()}
        out["generalization_deltas"] = {p: d for p, d in
                                        ((p, deltas(m)) for p, m in cmg.items()) if d}

    # knowledge utilization 机制链
    kt = {"retrieved": 0, "used": 0, "adapted": 0, "rejected": 0, "runs": 0}
    for sid, c in K.read_json(K.KEY / "condition_map.json")["map"].items():
        if c["knowledge"] == "none":
            continue
        mp = K.RUNS / sid / "manifest.json"
        if not mp.exists():
            continue
        m = K.read_json(mp)
        t = m.get("knowledge_trace") or {}
        kt["runs"] += 1
        kt["retrieved"] += 1 if t.get("retrieved") else 0
        kt["used"] += 1 if t.get("used") else 0
        kt["adapted"] += 1 if t.get("adapted") else 0
        kt["rejected"] += 1 if t.get("rejected") else 0
    out["knowledge_utilization"] = kt

    out["evaluator_models"] = sorted({r["evaluator_model"] for r in recs if r["evaluator_model"]})
    return out


def do_freeze() -> int:
    if FROZEN.exists():
        shutil.rmtree(FROZEN)
    FROZEN.mkdir(parents=True)
    copied = 0
    for p in sorted(RAW.rglob("*")):
        if p.is_file():
            rel = p.relative_to(RAW)
            dst = FROZEN / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            copied += 1
    digest = {str(p.relative_to(FROZEN).as_posix()): K.sha256_file(p)
              for p in sorted(FROZEN.rglob("*")) if p.is_file()}
    K.write_json(FROZEN / "_FREEZE_MANIFEST.json", {
        "experiment_id": K.EXPERIMENT_ID,
        "protocol_version": K.PROTOCOL_VERSION,
        "frozen_at": K.utc_now_iso(),
        "file_count": copied,
        "files": digest,
        "frozen_root_sha256": K.sha256_obj(digest),
        "analysis_script_sha256": K.sha256_file(Path(__file__)),
    })
    print(f"[OK] DATA FREEZE：{copied} 个文件 → {K.rel(FROZEN)}")
    return 0


def render_report(res: dict) -> str:
    def fmt(key, e):
        if not e:
            return f"| {key} | — | — | — | — |"
        p = e["point"]
        lo, hi = e["ci95"]
        return f"| {key} | {p:+.2f} | [{lo:+.2f}, {hi:+.2f}] | {e['n_blocks']} | {e['sign_perm_p']} |"

    L = []
    L.append("# P15-K001 — Model Construction Knowledge Efficacy（2×2 + Sham）\n")
    L.append(f"- protocol_version: `{K.PROTOCOL_VERSION}`")
    L.append(f"- 样本：{res['n_records']} 条（主检验 {res['n_primary']} / 泛化观察 {res['n_generalization']}）")
    L.append(f"- 评估模型：{', '.join(res['evaluator_models']) or '（未记录）'}")
    L.append("")
    L.append("## 1. 主终点 MCQ（L2 composite: structure + mathematics）\n")
    L.append("| 效应 | 点估计 | 95% CI（cluster bootstrap） | blocks | 符号置换 p |")
    L.append("|---|---|---|---|---|")
    m = res["metrics"]["mcq_primary"]["effects"]
    for k in ["delta_K", "delta_C", "delta_I", "delta_Sham"]:
        L.append(fmt(k, m.get(k)))
    L.append("")
    L.append("### 各题条件均值（MCQ）\n")
    L.append("| problem | A | B | C | D | E(sham) |")
    L.append("|---|---|---|---|---|---|")
    for p, arms in res["metrics"]["mcq_primary"]["condition_means"].items():
        L.append(f"| {p} " + "".join(f"| {arms.get(a, '—')} " for a in "ABCDE") + "|")
    L.append("")
    L.append("## 2. 六维向量上的效应（分辨「更会建模」还是「更会说方法名」）\n")
    L.append("| 维度 | Δ_K | Δ_K 95%CI | Δ_C | Δ_C 95%CI | Δ_I | Δ_I 95%CI |")
    L.append("|---|---|---|---|---|---|---|")
    for dim in ["structure", "mathematics", "alignment", "consistency", "validation", "support"]:
        e = res["metrics"][dim]["effects"]
        row = [f"| {dim} "]
        for k in ["delta_K", "delta_C", "delta_I"]:
            if k in e:
                row.append(f"| {e[k]['point']:+.2f} | [{e[k]['ci95'][0]:+.2f}, {e[k]['ci95'][1]:+.2f}] ")
            else:
                row.append("| — | — ")
        L.append("".join(row) + "|")
    L.append("")
    L.append("## 3. RQ5 方法族识别命中率（对照 allowed_model_families）\n")
    L.append("| 臂 | 命中率 |")
    L.append("|---|---|")
    for a, v in res["rq5_method_family_hit_rate"].items():
        L.append(f"| {a} | {v} |")
    L.append("")
    L.append("> 与 §1 的 MCQ 效应对比：若方法族命中率提升明显而 MCQ 无提升，"
             "说明知识只让模型「更会说方法名」。\n")
    L.append("## 4. RQ4 失败模式分布（arm 计数）\n")
    if res["rq4_failure_modes"]:
        L.append("| FM | " + " | ".join("ABCDE") + " |")
        L.append("|---|" + "---|" * 5)
        for f, cnt in sorted(res["rq4_failure_modes"].items()):
            L.append(f"| {f} " + "".join(f"| {cnt.get(a, 0)} " for a in "ABCDE") + "|")
    else:
        L.append("（无 FM 标注）")
    L.append("")
    L.append("## 5. 知识使用机制链\n")
    ku = res["knowledge_utilization"]
    if ku["runs"]:
        L.append(f"- 有参考资料注入的 run 数：{ku['runs']}")
        L.append(f"- 采纳率 used/retrieved：{ku['used']}/{ku['retrieved']}")
        L.append(f"- 改造后使用 adapted：{ku['adapted']}")
        L.append(f"- 明确拒绝 rejected：{ku['rejected']}")
    else:
        L.append("（无 knowledge_trace 数据）")
    L.append("")
    L.append("## 6. 泛化观察（不并入主检验）\n")
    L.append("```json")
    L.append(json.dumps(res.get("generalization_condition_means", {}), ensure_ascii=False, indent=2))
    L.append("```")
    L.append("")
    L.append("## 7. 结论与决策门\n")
    mk = res["metrics"]["mcq_primary"]["effects"].get("delta_K")
    if mk:
        lo = mk["ci95"][0]
        if lo > 0:
            L.append(f"- Δ_K 点估计 {mk['point']:+.2f}，CI 下界 {lo:+.2f} > 0 → "
                     "进入 Phase C（知识组件消融）。")
        else:
            L.append(f"- Δ_K 点估计 {mk['point']:+.2f}，CI 下界 {lo:+.2f} ≤ 0 → "
                     "记录为 negative result，回头查知识质量，不进 P15.2。")
    sham = res["metrics"]["mcq_primary"]["effects"].get("delta_Sham")
    if sham:
        lo, hi = sham["ci95"]
        if lo <= 0 <= hi:
            L.append(f"- Δ_Sham 点估计 {sham['point']:+.2f}，CI 跨 0 → "
                     "无法排除「更多上下文」解释，Sham 控制力不足。")
        else:
            L.append(f"- Δ_Sham 点估计 {sham['point']:+.2f}，CI 不跨 0 → "
                     "效应可归因于知识内容本身而非文本长度。")
    L.append("")
    L.append("## 8. 功效声明\n")
    L.append("主检验 block 数 = 3，符号置换最小可达 p = 0.25（双侧 0.125）。")
    L.append("**本轮以效应量 + 95% CI 为主结论，p 值仅作辅助。**")
    L.append("跨题型强泛化结论留给第二轮（12–20 题）。")
    return "\n".join(L)


def selftest() -> int:
    rng = random.Random(7)
    fake = []
    for pid in ["2020_B", "2018_A", "2019_C"]:
        base = {"2020_B": 55, "2018_A": 48, "2019_C": 60}[pid]
        for arm in "ABCDE":
            bump = {"A": 0, "B": 9, "C": 4, "D": 14, "E": 1}[arm]
            for rep in (1, 2, 3):
                dims = {}
                for d in L1 + L2 + L3 + L4:
                    mx = 3 if d == "L2.6" else (1 if d in ("L1.4", "L3.5", "L4.3") else 2)
                    dims[d] = {"score": min(mx, max(0, round(mx * (base + bump) / 100) + rng.choice([-1, 0, 0, 1])))}
                fake.append({
                    "submission_id": f"selftest-{pid}-{arm}-{rep}",
                    "problem_id": pid, "block_role": "main", "arm": arm, "rep": rep,
                    "vector": compute_vector({"dimensions": dims, "deterministic": {}}),
                    "method_family": "dynamic_programming", "failure_modes": [],
                    "evaluator_model": "selftest",
                })
    res = analyze(fake)
    print("[selftest] 合成数据分析结果（仅验证脚本可运行，不具科学含义）：")
    print(json.dumps(res["metrics"]["mcq_primary"]["effects"], ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--freeze" in argv:
        return do_freeze()
    if "--selftest" in argv:
        return selftest()

    if not any(SCORES.glob("*.json")):
        print("[FAIL] analysis/raw/scores/ 下没有评分文件。")
        return 1

    recs = load_records()
    if not recs:
        print("[FAIL] 没有可分析的记录（检查 submission_id 是否匹配 condition_map）。")
        return 1
    res = analyze(recs)
    K.write_json(K.ANALYSIS / "raw" / "analysis_result.json", res)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(res), encoding="utf-8")
    print(f"[OK] 分析完成：{len(recs)} 条记录 → {K.rel(REPORT)}")
    mk = res["metrics"]["mcq_primary"]["effects"].get("delta_K")
    if mk:
        print(f"     Δ_K = {mk['point']:+.2f}  95%CI [{mk['ci95'][0]:+.2f}, {mk['ci95'][1]:+.2f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
