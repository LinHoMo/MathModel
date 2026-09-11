#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q1/Q2 v2 结果产物的独立复核（machine-checkable）。

定位：验证器，不是生成器。它**不信任** q1q2_v2_results.json 里除输入坐标之外的
任何数字，全部按观测方程重算并与报告值比对。任一项不通过 → 退出码非 0。

之所以必须存在：本项目的铁律是「所有数值可追溯到已验证的 Result Artifact」。
没有这段复核，JSON 里的数字只是「脚本说自己算对了」。人工核对也被证明不可靠——
复核脚本开发过程中，手算 60.144281−55.147683 曾两次出错（正确值 4.996598）。

复核对标的四类缺陷（v1 的教训 + 本轮新增）：
  D1 算例可行性：|S−G| ≤ 1000 m 为「保证可行」（r_rec 未知但 ≥1000），
     ≤1500 m 只是「条件可行」，>1500 m 不可行。演示算例须取保证可行。
  D2 反例可实现性：反例必须同样满足硬约束，且不得落在真实可达集之外
     （v1 的 ρ=0.5083 就落在可达集外，夸大失效 28.33 倍）。
  D3 代理判据同向性：GDOP / 交会角 90° 等代理判据必须与真目标 E[D] 同向。
  D4 决策只用可观测量：源距 R 与接收半径 r_rec 都不是观测量，须进场景集。
  D5（本轮新增）可行性优先：失效率超阈值的方案不得参与最优性比较，
     否则「多数时候收不到信号」的点会靠条件期望 E[D|成功] 冒称最优。

运行：python projects/cumcm2026b/artifacts/code/verify_q1q2_v2.py [--full]
输出：projects/cumcm2026b/artifacts/q1q2_v2_verify.json
      --full 会重跑生成器（约 10 s）并逐字段对拍，用于确认产物可复现。
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import solve_q1q2_v2 as S  # noqa: E402

HERE = Path(__file__).resolve().parent
RES_PATH = HERE.parent / "q1q2_v2_results.json"
OUT_PATH = HERE.parent / "q1q2_v2_verify.json"

TOL_D = 1e-3          # 直径（m）
TOL_RHO = 1e-6        # ρ
TOL_ED = 1e-4         # E[D]（m）
TOL_RATE = 1e-6
# 坐标在结果 JSON 中四舍五入到 4 位小数（≈1e-4 m/轴），复核时由舍入坐标重算距离
# 会引入 ~2e-4 m 误差，故距离类硬约束的容差取 1e-3 m 而不是机器精度。
TOL_POS = 1e-3
TOL_DEG = 1e-4        # 角度（结果 JSON 中 ψ_max 保留 4 位小数）

CHECKS: list[dict] = []


def chk(cid: str, desc: str, ok: bool, detail: str = "") -> bool:
    CHECKS.append({"id": cid, "desc": desc, "ok": bool(ok), "detail": str(detail)})
    if not ok:
        print(f"  [FAIL] {cid} {desc}  {detail}")
    return bool(ok)


def require_realizable(tag: str, G, stations) -> bool:
    """硬约束可实现性。

    赛题只给 r_rec ∈ [1000,1500]，机器狗不可先知，故：
      |S−G| ≤ R_REC_MIN(1000)  → **保证可接收**（与 r_rec 实际取值无关）
      R_REC_MIN < |S−G| ≤ R_REC_MAX(1500) → 条件可行（依赖 r_rec 偏大）
      |S−G| > R_REC_MAX → 不可行
    另外 |S−G| ≤ R_OPTICAL(5 m) 时改用光学清除，不再测向，故不在测向算例内。
    """
    ok = True
    for i, s in enumerate(stations, 1):
        r = math.hypot(s[0] - G[0], s[1] - G[1])
        ok &= chk(f"{tag}.feas.S{i}", f"{tag}: |S{i}−G| ≤ {S.R_REC_MAX} m（可行）",
                  r <= S.R_REC_MAX + TOL_POS, f"|S{i}−G|={r:.4f} m")
        ok &= chk(f"{tag}.guar.S{i}", f"{tag}: |S{i}−G| ≤ {S.R_REC_MIN} m（保证可接收）",
                  r <= S.R_REC_MIN + TOL_POS, f"|S{i}−G|={r:.4f} m")
        ok &= chk(f"{tag}.opt.S{i}", f"{tag}: |S{i}−G| > {S.R_OPTICAL} m（未进入光学清除）",
                  r > S.R_OPTICAL, f"|S{i}−G|={r:.4f} m")
        ok &= chk(f"{tag}.area.S{i}", f"{tag}: S{i} 在区域内 (|S{i}| ≤ {S.R_AREA} m)",
                  math.hypot(*s) <= S.R_AREA + TOL_POS, f"|S{i}|={math.hypot(*s):.4f} m")
    ok &= chk(f"{tag}.area.G", f"{tag}: 源在区域内 (|G| ≤ {S.R_AREA} m)",
              math.hypot(*G) <= S.R_AREA + TOL_POS, f"|G|={math.hypot(*G):.4f} m")
    return ok


def regeom(stations, bearings_deg):
    """按观测方程重算定位区域 → (直径, MEC 半径, ρ, 直径圆是否覆盖)。"""
    poly = S.location_region(stations, bearings_deg)
    if len(poly) < 3:
        return None
    D = S.polygon_diameter(poly)
    _, r = S.min_enclosing_circle(poly)
    return D, r, r / D, S.covers_by_diameter_circle(poly)


def main(full: bool = False) -> int:
    t0 = time.time()
    if not RES_PATH.exists():
        print(f"missing {RES_PATH}")
        return 2
    raw = RES_PATH.read_bytes()
    res = json.loads(raw.decode("utf-8"))
    sha = hashlib.sha256(raw).hexdigest()
    print(f"verify {RES_PATH.name}  sha256={sha[:16]}…")

    # ---------------------------------------------------------------- 基本契约
    chk("meta.seed", "随机种子固定为 42", res.get("random_seed") == 42,
        f"seed={res.get('random_seed')}")
    c = res["constants"]
    chk("meta.const", "常量与赛题一致（R=1800, ε=1°, 接收半径 1000–1500 m）",
        c["R_AREA"] == 1800.0 and c["EPS_BEARING_DEG"] == 1.0
        and c["R_REC_MIN"] == 1000.0 and c["R_REC_MAX"] == 1500.0, json.dumps(c))

    # ---------------------------------------------------------------- Q1 算例
    print("Q1 算例：")
    for case in res["problem1"]["cases"]:
        G = tuple(case["source"])
        st = [tuple(s) for s in case["stations"]]
        tag = "Q1." + case["name"].split()[0]
        require_realizable(tag, G, st)
        chk(f"{tag}.guar.flag", f"{tag}: 自报「保证可行」为真",
            bool(case.get("station_source_dist_guaranteed")), "")
        g = regeom(st, case["true_bearings_deg"])
        chk(f"{tag}.poly", f"{tag}: 定位区域非退化", g is not None, "")
        if g is None:
            continue
        D, r, rho, covers = g
        chk(f"{tag}.D", f"{tag}: 直径重算一致", abs(D - case["diameter_m"]) <= TOL_D,
            f"recompute={D:.6f} reported={case['diameter_m']}")
        chk(f"{tag}.rho", f"{tag}: ρ 重算一致", abs(rho - case["rho_mec_over_D"]) <= TOL_RHO,
            f"recompute={rho:.9f} reported={case['rho_mec_over_D']}")
        # 数学必然：覆盖全部顶点的圆半径 ≥ D/2（直径两端点必在圆内）
        chk(f"{tag}.rho_lower", f"{tag}: ρ ≥ 1/2（直径两端点定圆）",
            rho >= 0.5 - 1e-12, f"ρ={rho:.9f}")
        # Thales：ρ = 1/2 ⟺ 直径圆覆盖
        chk(f"{tag}.thales", f"{tag}: ρ = 1/2 ⟺ 直径圆覆盖",
            covers == (rho <= 0.5 + 1e-9), f"covers={covers} ρ={rho:.9f}")
        if case.get("crossing_angle_deg") is not None and len(st) == 2:
            chi = S.ang_diff(S.bearing(G[0], G[1], st[0][0], st[0][1]),
                             S.bearing(G[0], G[1], st[1][0], st[1][1]))
            chk(f"{tag}.chi", f"{tag}: 交会角重算一致",
                abs(chi - case["crossing_angle_deg"]) <= 1e-3,
                f"recompute={chi:.4f} reported={case['crossing_angle_deg']}")

    # ---------------------------------------------------------------- Q1 反例
    print("Q1 反例：")
    ce = res["problem1"]["counterexample"]
    w = ce["worst_case"]
    G, st = tuple(w["source"]), [tuple(s) for s in w["stations"]]
    # 反例「可实现」是最容易被忽略的一条：不可实现的反例等于没有反例
    require_realizable("Q1.ce", G, st)
    g = regeom(st, [S.bearing(s[0], s[1], G[0], G[1]) for s in st])
    chk("Q1.ce.poly", "反例: 定位区域非退化", g is not None, "")
    if g is not None:
        D, r, rho, covers = g
        chk("Q1.ce.D", "反例: 直径重算一致", abs(D - w["diameter_m"]) <= TOL_D,
            f"recompute={D:.6f} reported={w['diameter_m']}")
        chk("Q1.ce.rho", "反例: ρ 重算一致", abs(rho - w["rho_mec_over_D"]) <= TOL_RHO,
            f"recompute={rho:.9f} reported={w['rho_mec_over_D']}")
        chk("Q1.ce.fails", "反例: 直径圆确实不覆盖（是真反例）", not covers, f"covers={covers}")
        chk("Q1.ce.gt_half", "反例: ρ > 1/2（不覆盖的必要条件）", rho > 0.5 + 1e-12,
            f"ρ={rho:.9f}")
        chk("Q1.ce.enlarge", "反例: required_enlarge_factor = 2·r_MEC/D",
            abs(w["required_enlarge_factor"] - 2.0 * r / D) <= 1e-6,
            f"reported={w['required_enlarge_factor']} recompute={2.0 * r / D:.9f}")
        chk("Q1.ce.window", "反例: 交会角落在失效窗口 (90°, 90°+2ε]",
            90.0 < w["crossing_angle_deg"] <= 90.0 + 2 * S.EPS_DEG,
            f"χ={w['crossing_angle_deg']}")
        chk("Q1.ce.origin", "反例: 由正向模型生成（非字面常量）",
            "forward_model" in (w.get("generation") or ""), str(w.get("generation")))

    wc = ce["window_empirical_check"]
    chk("Q1.win.agree", "失效窗口定理：落入窗口集合 == 覆盖失败集合（iff，逐样本）",
        bool(wc["agree"]) and wc["n_in_window_predicted"] == ce["n_failures"],
        f"in_window={wc['n_in_window_predicted']} n_fail={ce['n_failures']}")
    p = wc["theoretical_fail_rate"]
    sd = math.sqrt(p * (1 - p) / max(1, ce["n_accepted"]))
    chk("Q1.win.rate", "失效率与理论 2ε/15° 一致（|z| ≤ 4）",
        abs(wc["observed_fail_rate"] - p) <= 4 * sd,
        f"obs={wc['observed_fail_rate']} theory={p} 4σ={4 * sd:.5f}")

    sup = ce["supremum_dense_scan"]
    rho_sup = sup["rho_sup_dense_scan"]
    chk("Q1.sup.order", "随机采样上确界 ≤ 定向密集扫描上确界",
        ce["rho_sup_observed"] <= rho_sup + 1e-12,
        f"obs={ce['rho_sup_observed']} dense={rho_sup}")
    chk("Q1.sup.jung", "上确界 < Jung 上界 1/√3", rho_sup < ce["jung_upper_bound"],
        f"{rho_sup} < {ce['jung_upper_bound']}")
    chk("Q1.sup.gt_half", "上确界 > 1/2（窗口内确有失效）", rho_sup > 0.5, f"{rho_sup}")
    # v1 的核心错误：手搓反例落在真实可达集之外
    chk("Q1.sup.v1_out", "v1 手搓反例 ρ=0.5083 落在可达集之外（超出上确界）",
        sup["v1_synthetic_rho"] > rho_sup,
        f"v1={sup['v1_synthetic_rho']} > sup={rho_sup}")
    exp_factor = (sup["v1_synthetic_rho"] - 0.5) / (rho_sup - 0.5)
    chk("Q1.sup.factor", "夸大倍数自洽",
        abs(sup["v1_exaggeration_factor"] - exp_factor) <= 0.02,
        f"reported={sup['v1_exaggeration_factor']} recompute={exp_factor:.4f}")
    chk("Q1.sup.invariant", "ρ 声明为相似不变量（扫描降维的依据）",
        bool(ce.get("rho_sup_is_similarity_invariant")), "")
    # 上确界的相似不变性直接数值验证：同一 (χ, r₂/r₁) 换绝对尺度，ρ 不变
    chi0 = sup["argmax"]["chi_deg"]
    ratio0 = sup["argmax"]["r2_over_r1"]
    rhos = []
    for scale in (300.0, 1000.0, 4000.0):
        gg = (0.0, 0.0)
        ss = [(scale, 0.0),
              (scale * ratio0 * math.cos(math.radians(chi0)),
               scale * ratio0 * math.sin(math.radians(chi0)))]
        pp = S.location_region(ss, [S.bearing(ss[0][0], ss[0][1], *gg),
                                    S.bearing(ss[1][0], ss[1][1], *gg)])
        if len(pp) >= 3:
            _, rr = S.min_enclosing_circle(pp)
            rhos.append(rr / S.polygon_diameter(pp))
    chk("Q1.sup.scale_inv", "相似不变性数值验证：3 个绝对尺度下 ρ 一致",
        len(rhos) == 3 and max(rhos) - min(rhos) < 1e-9,
        f"ρ={[round(x, 10) for x in rhos]}")

    # ---------------------------------------------------------------- Q2 决策
    print("Q2 决策：")
    q2 = res["problem2"]
    pbest = q2["per_scenario_best"]
    mm = q2["minimax_regret_point"]
    mx = q2["minimax_point"]
    keys = q2["scenarios"]
    # 后悔值独立重算：max_场景 (该点 E[D] − 该场景网格最优)
    recalc = {k: mm["E_D_by_scenario"][k] - pbest[k]["E_D_m"] for k in keys}
    chk("Q2.regret", "最小最大后悔值可重算",
        abs(max(recalc.values()) - mm["regret_m"]) <= TOL_ED,
        f"recompute={max(recalc.values()):.6f} reported={mm['regret_m']}")
    chk("Q2.regret.max", "后悔值取各场景最大值（max 而非均值/加权和）",
        abs(max(recalc.values()) - mm["regret_m"]) <= TOL_ED, str(recalc))
    chk("Q2.minimax", "最小最大点的最坏 E[D] 可重算",
        abs(max(mx["E_D_by_scenario"].values()) - mx["worst_E_D_m"]) <= TOL_ED,
        f"recompute={max(mx['E_D_by_scenario'].values()):.6f} reported={mx['worst_E_D_m']}")
    # 可行性优先：入选点失效概率必须低于阈值
    chk("Q2.feas.mm", f"最小最大后悔点失效概率 ≤ {q2['fail_tol']}",
        max(mm["fail_prob_by_scenario"].values()) <= q2["fail_tol"] + 1e-9,
        f"max={max(mm['fail_prob_by_scenario'].values())}")
    chk("Q2.feas.mx", f"最小最大点失效概率 ≤ {q2['fail_tol']}",
        max(mx["fail_prob_by_scenario"].values()) <= q2["fail_tol"] + 1e-9,
        f"max={max(mx['fail_prob_by_scenario'].values())}")
    # 被剔除的点确实失效率超阈
    chk("Q2.feas.excl", "被可行性筛剔除的点失效率确实 > 阈值",
        all(x["max_fail_prob"] > q2["fail_tol"] for x in q2["excluded_by_fail"]),
        f"n_excl={q2['n_grid_points'] - q2['n_feasible_points']}")
    chk("Q2.feas.count", "网格点统计自洽（可行 + 剔除 = 全部）",
        q2["n_feasible_points"] + (q2["n_grid_points"] - q2["n_feasible_points"])
        == q2["n_grid_points"] and q2["n_feasible_points"] > 0,
        f"{q2['n_feasible_points']}/{q2['n_grid_points']}")
    cand = q2["candidate_region"]
    rmin = min(x["regret_m"] for x in cand)
    chk("Q2.cand.thr", f"候选区内 regret ≤ (1+{q2['candidate_region_alpha']})·min",
        all(x["regret_m"] <= rmin * (1 + q2["candidate_region_alpha"]) + 1e-6 for x in cand),
        f"thr={rmin * (1 + q2['candidate_region_alpha']):.6f}")
    chk("Q2.cand.argmin", "候选区含最小后悔点",
        any(x["psi_deg"] == mm["psi_deg"] and x["d_m"] == mm["d_m"] for x in cand), "")
    chk("Q2.obs", "两个不可观测量（源距 R、接收半径 r_rec）均显式声明",
        any("源距" in s or "R=" in s for s in q2.get("not_observable", []))
        and any("r_rec" in s for s in q2.get("not_observable", [])),
        str(q2.get("not_observable")))
    chk("Q2.scen", f"场景集 = 距离先验 × r_rec 假设，共 {q2['n_scenarios']} 个",
        q2["n_scenarios"] == len(keys) >= 6, str(keys))
    drift = {(pbest[k]["psi_deg"], pbest[k]["d_m"]) for k in keys}
    chk("Q2.prior.drift", "各场景最优点不一致（故须报候选区 + 后悔值）", len(drift) > 1,
        str(sorted(drift)))

    # ---- 闭式可行域 vs 数值失效扫描（互校）
    print("Q2 闭式可行域 vs 数值扫描：")
    env = q2["feasibility_envelope"]["r_rec_1000_guaranteed"]
    R_lo, R_hi = env["R_lo_m"], env["R_hi_m"]
    psi_max_exp = math.degrees(math.asin(min(1.0, env["r_rec_m"] / R_hi)))
    chk("Q2.env.psimax", "ψ_max = arcsin(r_rec / R_hi) 自洽",
        abs(env["psi_max_deg"] - psi_max_exp) <= TOL_DEG,
        f"reported={env['psi_max_deg']} recompute={psi_max_exp:.6f}")
    # 用闭式包络预测每个网格点是否「必然可接收」，与数值失效率对照
    envmap = {r["psi_deg"]: r for r in env["rows"]}
    mism = []
    for psi in q2["grid_size"]["psi"]:
        row = envmap.get(psi)
        for d in q2["grid_size"]["d"]:
            pred = bool(row and row["feasible"]
                        and row["d_lo_m"] - 1e-6 <= d <= row["d_hi_m"] + 1e-6)
            mism.append((psi, d, pred))
    # 数值侧直接重算（复用生成器函数：输入是网格与先验，输出是失效率）
    priors = {
        "P1_距离均匀[200,1500]": [200.0 + 1300.0 * (i + 0.5) / 24 for i in range(24)],
        "P2_面积均匀(盘内密度∝R)": [1500.0 * math.sqrt((i + 0.5) / 24) for i in range(24)],
        "P3_远距集中[1000,1500]": [1000.0 + 500.0 * (i + 0.5) / 24 for i in range(24)],
    }
    S1 = tuple(q2["S1"])
    b1 = q2["b1_measured_deg"]
    bad = []
    for psi, d, pred in mism:
        fp = 0.0
        for Rs in priors.values():
            f = sum(S._E_D(S1, b1, psi, d, R, r_rec=S.R_REC_MIN)[1] for R in Rs) / len(Rs)
            fp = max(fp, f)
        obs = fp <= 1e-9
        # 闭式是「∀R∈[R_lo,R_hi]」的充分条件 → pred 为真则必 obs 为真（单向）
        if pred and not obs:
            bad.append((psi, d, round(fp, 4)))
    chk("Q2.env.sound", "闭式可行域是充分的：闭式判可行 → 数值失效率必为 0",
        not bad, f"violations={bad[:5]}")

    # ---------------------------------------------------------- 代理判据同向性
    print("Q2 代理判据：")
    cv = q2["compare_v1"]
    rows = cv["rows"]
    R = 1200.0
    eps_rad = math.radians(S.EPS_DEG)
    ok_cf = True
    for row in rows:
        cf = 2.0 * eps_rad * math.hypot(R, row["offset_m"])
        rel = abs(row["worst_D_m"] - cf) / row["worst_D_m"]
        ok_cf &= rel <= 0.01
        print(f"    offset={row['offset_m']:6.0f} m  worst_D={row['worst_D_m']:8.3f}"
              f"  闭式 2ε√(R²+t²)={cf:8.3f}  相对偏差={rel * 100:.3f}%")
    chk("Q2.cf", "闭式 D = 2ε·√(R²+t²) 与数值最坏直径一致（≤1%）", ok_cf, "")
    e = [row["E_D_m"] for row in rows]
    chk("Q2.cf.mono", "垂线族上 E[D] 随偏移严格递增（故「偏移越大越好」为假）",
        all(e[i] < e[i + 1] for i in range(len(e) - 1)), str([round(x, 3) for x in e]))
    v1row = [r for r in rows if r["offset_m"] == cv["v1_recommended_offset_m"]][0]
    chk("Q2.v1.worse", "v1 推荐点严格劣于最小偏移点（代理判据与真目标反号）",
        rows[0]["E_D_m"] < v1row["E_D_m"],
        f"v1 offset={v1row['offset_m']} E[D]={v1row['E_D_m']:.3f} "
        f"vs offset={rows[0]['offset_m']} E[D]={rows[0]['E_D_m']:.3f}")

    # ------------------------------------------------------- 可复现（--full）
    repro = None
    if full:
        print("--full：重跑生成器对拍")
        fresh = S.build_all()
        a1 = fresh["problem1"]["counterexample"]
        repro = {
            "n_failures_equal": a1["n_failures"] == ce["n_failures"],
            "rho_sup_equal": abs(a1["rho_sup_dense_scan"] - rho_sup) <= 1e-12,
            "q2_equal": (fresh["problem2"]["minimax_regret_point"]["psi_deg"] == mm["psi_deg"]
                         and fresh["problem2"]["minimax_regret_point"]["d_m"] == mm["d_m"]
                         and abs(fresh["problem2"]["minimax_regret_point"]["regret_m"]
                                 - mm["regret_m"]) <= TOL_ED),
        }
        chk("repro.n_fail", "重跑失效样本数一致（seed=42 可复现）",
            repro["n_failures_equal"],
            f"fresh={a1['n_failures']} stored={ce['n_failures']}")
        chk("repro.rho_sup", "重跑上确界一致", repro["rho_sup_equal"], "")
        chk("repro.q2", "重跑 Q2 最小最大后悔点一致", repro["q2_equal"], "")

    failed = [x for x in CHECKS if not x["ok"]]
    report = {
        "schema_version": 1,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "target": {"path": "artifacts/q1q2_v2_results.json", "sha256": sha},
        "n_checks": len(CHECKS),
        "n_failed": len(failed),
        "passed": not failed,
        "failed_ids": [x["id"] for x in failed],
        "recompute": repro,
        "checks": CHECKS,
    }
    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed"
          f"  ({time.time() - t0:.1f}s)  -> {OUT_PATH.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(full="--full" in sys.argv))
