#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r32_eval.py — P13-3D-R3.2 真实 Writer 对照实验评测器（G3–G6）.

严格按 docs/architecture/R3_2_REAL_WRITER_PREREG.md（FROZEN）执行：
  G3  STC v2        —— 逐论文调用 research/P13-3D/scripts/stc_evaluator.py::compute_stc_v2
                       （校准仪器，Golden F1=1.000，禁止修改）
  G4  Fidelity v2   —— 逐论文调用 research/P13-3D/scripts/fidelity_gate.py::compute_fidelity
  G5  Blind PQ      —— 每题 6 篇（3 arm × W0/W1）匿名随机编号（seed 42），
                       评审 standalone 评分（4 维 0–100），盲态由 key 文件隔离保证
  G6  Paired analysis —— H13–H18（24 单元配对，W1 − W0）

用法:
  python r32_eval.py manifest         # G2 冻结清单：48 篇 sha256/mtime/batch
  python r32_eval.py stc              # G3
  python r32_eval.py fidelity         # G4
  python r32_eval.py blind-prep       # G5 准备（生成匿名包 + key，key 不进评审上下文）
  python r32_eval.py blind-collect    # G5 收集（读取 blind/{qid}_scores_raw.json）
  python r32_eval.py analyze          # G6（H13–H18）
  python r32_eval.py all              # manifest+stc+fidelity+blind-prep（blind-collect/analyze 除外）

输出目录: research/P13-3D-R3/real_evaluation/
统计: numpy 手写（配对 t 单侧 p 经不完全 beta；Wilcoxon 符号秩正态近似；Spearman 秩相关）
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import random
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

# --- 路径（P4 迁移后约定：repo 根 = parents[3]） ---
ROOT = Path(__file__).resolve().parents[3]  # MathModel repo root
SCRIPTS = ROOT / "research" / "P13-3D" / "scripts"
R2_ARTIFACTS = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
R3 = ROOT / "research" / "P13-3D-R3"
PAPERS = R3 / "real_papers"
EVAL = R3 / "real_evaluation"
BLIND = EVAL / "blind"

PREREG = ROOT / "docs" / "architecture" / "R3_2_REAL_WRITER_PREREG.md"

QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]
ARMS = ["B0", "MMA", "B1-F"]           # 语义 arm 名
CONDITIONS = ["W0", "W1"]

TITLES = {
    "2019_A": "高压油管的压力控制",
    "2022_A": "波浪能最大输出功率设计",
    "2017_B": "拍照赚钱的任务定价",
    "2022_C": "古代玻璃制品的成分分析与鉴别",
    "2020_B": "穿越沙漠",
    "2024_B": "生产过程中的决策问题",
    "2023_C": "蔬菜类商品的自动定价与补货决策",
    "2024_C": "农作物的种植策略",
}

# 冻结仪器（不得修改，只加载）
def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

stc_mod = _load_module("stc_evaluator_v2", SCRIPTS / "stc_evaluator.py")
fid_mod = _load_module("fidelity_gate_v2", SCRIPTS / "fidelity_gate.py")


# ---------------------------------------------------------------- 基础工具
def arm_token(arm: str) -> str:
    """语义 arm 名 → 文件名 token（B1-F → B1_F）。"""
    return arm.replace("-", "_")


def paper_path(cond: str, q: str, arm: str) -> Path:
    return PAPERS / cond / f"{q}_{arm_token(arm)}.md"


def artifact_path(q: str, arm: str) -> Path:
    return R2_ARTIFACTS / f"{q}_{arm_token(arm)}.json"


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def batch_of(mtime: datetime) -> str:
    """prereg 附录 A2：batch_id 记录。主批次 = 2026-09-07 13:37–15:21 生成波次；
    2020_B/B0 于 20:25–20:27 由本会话按冻结 prompt 重生成（配对重复缺陷修复）。"""
    return "G2-20260907-repair" if mtime.hour >= 16 else "G2-20260907-main"


def iter_units():
    """yield (question, arm, condition, path, text, mtime, sha, batch)."""
    for q in QUESTIONS:
        for arm in ARMS:
            for cond in CONDITIONS:
                p = paper_path(cond, q, arm)
                text = p.read_text(encoding="utf-8")
                mt = datetime.fromtimestamp(p.stat().st_mtime)
                yield q, arm, cond, p, text, mt, sha256_text(text), batch_of(mt)


def _mutation_count(mutation_audit: dict) -> int:
    """H16 口径：mutation_audit 中全部列表字段的事件总数（addition/deletion/
    modification/renaming/semantic_drift 等）。"""
    return sum(len(v) for v in mutation_audit.values() if isinstance(v, list))


# ---------------------------------------------------------------- 统计（numpy 手写）
def _betacf(a: float, b: float, x: float) -> float:
    MAXIT, EPS, FPMIN = 200, 3e-12, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_bt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1.0 - x))
    bt = math.exp(ln_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_sf_one_sided(t: float, df: float) -> float:
    """P(T > t)，单侧上尾。"""
    if df <= 0:
        return float("nan")
    x = df / (df + t * t)
    two_sided = _betainc(df / 2.0, 0.5, x)
    return two_sided / 2.0 if t > 0 else 1.0 - two_sided / 2.0


def paired_t_one_sided(d: np.ndarray) -> dict:
    """H: mean(d) > 0 的单侧配对 t 检验。"""
    d = np.asarray(d, dtype=float)
    n = len(d)
    mean = float(d.mean())
    sd = float(d.std(ddof=1)) if n > 1 else float("nan")
    if n < 2 or sd == 0:
        return {"n": n, "mean": mean, "t": float("inf") if mean > 0 else 0.0,
                "df": n - 1, "p_one_sided": 0.0 if mean > 0 else 1.0}
    t = mean / (sd / math.sqrt(n))
    return {"n": n, "mean": mean, "t": t, "df": n - 1,
            "p_one_sided": t_sf_one_sided(t, n - 1)}


def wilcoxon_one_sided(x1: np.ndarray, x0: np.ndarray) -> dict:
    """Wilcoxon 符号秩检验，H: x1 > x0（正态近似 + 连续性校正 + 结校正）。"""
    d = np.asarray(x1, dtype=float) - np.asarray(x0, dtype=float)
    d = d[d != 0]
    n = len(d)
    if n == 0:
        return {"n": 0, "w_plus": 0.0, "z": float("nan"), "p_one_sided": float("nan")}
    ad = np.abs(d)
    order = np.argsort(ad, kind="mergesort")
    ranks = np.empty(n, dtype=float)
    i = 0
    tie_sum = 0.0
    sorted_ad = ad[order]
    while i < n:
        j = i
        while j + 1 < n and sorted_ad[j + 1] == sorted_ad[i]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        ranks[order[i:j + 1]] = avg_rank
        t = j - i + 1
        tie_sum += (t ** 3 - t)
        i = j + 1
    w_plus = float(ranks[d > 0].sum())
    expected = n * (n + 1) / 4.0
    var = n * (n + 1) * (2 * n + 1) / 24.0 - tie_sum / 48.0
    z = (w_plus - expected - 0.5) / math.sqrt(var) if var > 0 else float("nan")
    p = 1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))) if not math.isnan(z) else float("nan")
    return {"n": n, "w_plus": w_plus, "z": z, "p_one_sided": p}


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    def ranks(a: np.ndarray) -> np.ndarray:
        order = np.argsort(a, kind="mergesort")
        r = np.empty(len(a), dtype=float)
        sa = a[order]
        i = 0
        while i < len(a):
            j = i
            while j + 1 < len(a) and sa[j + 1] == sa[i]:
                j += 1
            r[order[i:j + 1]] = (i + j) / 2.0 + 1.0
            i = j + 1
        return r
    rx, ry = ranks(np.asarray(x, dtype=float)), ranks(np.asarray(y, dtype=float))
    rx, ry = rx - rx.mean(), ry - ry.mean()
    denom = math.sqrt(float((rx ** 2).sum()) * float((ry ** 2).sum()))
    return float((rx * ry).sum() / denom) if denom > 0 else float("nan")


# ---------------------------------------------------------------- 子命令
def cmd_manifest() -> dict:
    entries = []
    for q, arm, cond, p, text, mt, sha, batch in iter_units():
        entries.append({
            "question": q, "arm": arm, "condition": cond,
            "file": str(p.relative_to(ROOT)),
            "chars": len(text), "sha256": sha,
            "mtime": mt.isoformat(timespec="seconds"), "batch_id": batch,
        })
    out = {"frozen_at": datetime.now().isoformat(timespec="seconds"),
           "n_papers": len(entries),
           "prereg": str(PREREG.relative_to(ROOT)),
           "papers": entries}
    EVAL.mkdir(parents=True, exist_ok=True)
    (EVAL / "corpus_manifest.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest: {len(entries)} papers -> {EVAL / 'corpus_manifest.json'}")
    return out


def cmd_stc() -> dict:
    results = []
    for q, arm, cond, p, text, mt, sha, batch in iter_units():
        artifact = json.loads(artifact_path(q, arm).read_text(encoding="utf-8"))
        stc = stc_mod.compute_stc_v2(text, artifact)
        results.append({
            "question": q, "arm": arm, "condition": cond,
            "chars": len(text), "sha256": sha, "mtime": mt.isoformat(timespec="seconds"),
            "batch_id": batch,
            "stc_core": stc["stc_core"], "stc_meta": stc["stc_meta"],
            "stc_overall": stc["stc_overall"],
            "elements": stc["elements"],
        })
    out = {"ran_at": datetime.now().isoformat(timespec="seconds"),
           "instrument": "stc_evaluator.py::compute_stc_v2 (STC v2, Golden F1=1.000, 冻结不改)",
           "prereg": str(PREREG.relative_to(ROOT)),
           "n": len(results), "results": results}
    EVAL.mkdir(parents=True, exist_ok=True)
    (EVAL / "r32_stc.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    # 摘要表
    print(f"{'unit':<16} {'STC_core W0/W1':>16} {'STC_meta W0/W1':>16} {'Δmeta':>8}")
    idx = {(r["question"], r["arm"], r["condition"]): r for r in results}
    for q in QUESTIONS:
        for arm in ARMS:
            w0, w1 = idx[(q, arm, "W0")], idx[(q, arm, "W1")]
            dm = w1["stc_meta"] - w0["stc_meta"]
            print(f"{q}/{arm:<5} {w0['stc_core']:>7.3f}/{w1['stc_core']:<7.3f} "
                  f"{w0['stc_meta']:>7.3f}/{w1['stc_meta']:<7.3f} {dm:>+8.3f}")
    print(f"stc: {len(results)} papers -> {EVAL / 'r32_stc.json'}")
    return out


def cmd_fidelity() -> dict:
    results = []
    for q, arm, cond, p, text, mt, sha, batch in iter_units():
        artifact = json.loads(artifact_path(q, arm).read_text(encoding="utf-8"))
        r = fid_mod.compute_fidelity(artifact, text)
        ma = r.get("mutation_audit", {})
        results.append({
            "question": q, "arm": arm, "condition": cond,
            "chars": len(text), "sha256": sha,
            "mtime": mt.isoformat(timespec="seconds"), "batch_id": batch,
            "coverage_fidelity": r.get("coverage_fidelity"),
            "semantic_fidelity": r.get("semantic_fidelity"),
            "mutations_total": _mutation_count(ma),
            "mutation_audit": ma,
            "writer_failures": r.get("writer_failures", []),
        })
    out = {"ran_at": datetime.now().isoformat(timespec="seconds"),
           "instrument": "fidelity_gate.py::compute_fidelity (v2: coverage/mutation/semantic, 冻结不改)",
           "prereg": str(PREREG.relative_to(ROOT)),
           "n": len(results), "results": results}
    EVAL.mkdir(parents=True, exist_ok=True)
    (EVAL / "r32_fidelity.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{'unit':<16} {'cond':<4} {'cover':>7} {'semantic':>9} {'mut':>4} failures")
    for r in results:
        fails = ",".join(sorted({f.get("code", "?") for f in r["writer_failures"]})) or "-"
        print(f"{r['question']}/{r['arm']:<5} {r['condition']:<4} "
              f"{r['coverage_fidelity']:>7.1%} {r['semantic_fidelity']:>9.1%} "
              f"{r['mutations_total']:>4} {fails}")
    print(f"fidelity: {len(results)} papers -> {EVAL / 'r32_fidelity.json'}")
    return out


RUBRIC = """对以下 6 篇同一数学建模赛题的匿名论文逐一独立评分。评分只依据论文文本本身（论文自带的问题重述即为其问题定义）。

## 评分维度（每项 0–100 整数）
1. math_correctness（数学正确性）：公式、推导、量纲是否正确自洽
2. problem_alignment（问题对齐）：论文是否清晰定义要解决的问题，并围绕它完整作答
3. completeness（完整性）：模型组件覆盖度（变量/参数/约束/目标/机制/假设/候选模型/选定模型/灵敏度）
4. communication（表达质量）：结构清晰度、可读性、逻辑连贯

## 输出格式（严格 JSON，不要输出任何其他文字、不要使用代码块围栏）
{"papers":[{"id":"X1","scores":{"math_correctness":<0-100>,"problem_alignment":<0-100>,"completeness":<0-100>,"communication":<0-100>},"brief":"<一句话依据>"}, ...]}
必须覆盖全部 6 篇，id 使用给定的编号。"""


def cmd_blind_prep() -> dict:
    BLIND.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)  # prereg：随机化编号 seed 42
    key = {}
    for q in QUESTIONS:
        items = []
        for arm in ARMS:
            for cond in CONDITIONS:
                p = paper_path(cond, q, arm)
                items.append({"arm": arm, "condition": cond, "file": p.name,
                              "text": p.read_text(encoding="utf-8")})
        rng.shuffle(items)
        labeled = [{"label": f"X{i+1}", "text": it["text"]} for i, it in enumerate(items)]
        key[q] = [{**{k: it[k] for k in ("arm", "condition", "file")}, "label": f"X{i+1}"}
                  for i, it in enumerate(items)]
        pack = {"question_id": q, "title": TITLES[q], "n_papers": 6,
                "rubric": RUBRIC, "papers": labeled}
        (BLIND / f"{q}_pack.json").write_text(
            json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    (BLIND / "blind_key.json").write_text(
        json.dumps({"note": "盲评密钥：仅供分析阶段去匿名，禁止进入任何评审上下文",
                    "random_seed": 42, "key": key}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"blind-prep: {len(QUESTIONS)} packs + blind_key.json -> {BLIND}")
    print("评审提示词模板 = RUBRIC（内嵌于各 pack.json.rubric）；评审不得接触 key。")
    return key


def cmd_blind_collect() -> dict:
    # key 存放在 blind/ 上一级，避免进入任何评审 agent 的可见目录
    key = json.loads((EVAL / "blind_key.json").read_text(encoding="utf-8"))["key"]
    out_results = []
    for q in QUESTIONS:
        raw_p = BLIND / f"{q}_scores_raw.json"
        if not raw_p.exists():
            print(f"MISSING {q}_scores_raw.json —— 跳过（评审未完成）")
            continue
        raw = raw_p.read_text(encoding="utf-8").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw[raw.find("{"):]
        data = json.loads(raw)
        label2meta = {e["label"]: e for e in key[q]}
        papers = []
        for pe in data["papers"]:
            meta = label2meta[pe["id"]]
            s = pe["scores"]
            pq = (s["math_correctness"] + s["problem_alignment"]
                  + s["completeness"] + s["communication"]) / 4.0
            papers.append({**meta, "scores": s, "brief": pe.get("brief", ""),
                           "PQ": pq})
        out_results.append({"question": q, "papers": papers})
        print(f"{q}: " + " ".join(
            f"{p['label']}({p['condition']}/{p['arm']})={p['PQ']:.1f}" for p in papers))
    out = {"collected_at": datetime.now().isoformat(timespec="seconds"),
           "scale": "每维 0–100，PQ = 4 维均值",
           "n_questions": len(out_results), "results": out_results}
    (EVAL / "r32_blind_pq.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"blind-collect: {len(out_results)}/8 questions -> {EVAL / 'r32_blind_pq.json'}")
    return out


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def cmd_analyze() -> dict:
    stc = _load_json(EVAL / "r32_stc.json")["results"]
    fid = _load_json(EVAL / "r32_fidelity.json")["results"]
    pq = _load_json(EVAL / "r32_blind_pq.json")["results"]
    idx_s = {(r["question"], r["arm"], r["condition"]): r for r in stc}
    idx_f = {(r["question"], r["arm"], r["condition"]): r for r in fid}
    idx_p = {}
    for r in pq:
        for pe in r["papers"]:
            idx_p[(r["question"], pe["arm"], pe["condition"])] = pe

    units = []
    for q in QUESTIONS:
        for arm in ARMS:
            w0s, w1s = idx_s[(q, arm, "W0")], idx_s[(q, arm, "W1")]
            w0f, w1f = idx_f[(q, arm, "W0")], idx_f[(q, arm, "W1")]
            w0p, w1p = idx_p[(q, arm, "W0")], idx_p[(q, arm, "W1")]
            units.append({
                "question": q, "arm": arm,
                "batch_w0": w0s["batch_id"], "batch_w1": w1s["batch_id"],
                "chars_w0": w0s["chars"], "chars_w1": w1s["chars"],
                "stc_core_w0": w0s["stc_core"], "stc_core_w1": w1s["stc_core"],
                "stc_meta_w0": w0s["stc_meta"], "stc_meta_w1": w1s["stc_meta"],
                "stc_overall_w0": w0s["stc_overall"], "stc_overall_w1": w1s["stc_overall"],
                "pq_w0": w0p["PQ"], "pq_w1": w1p["PQ"],
                "mut_w0": w0f["mutations_total"], "mut_w1": w1f["mutations_total"],
                "cover_w0": w0f["coverage_fidelity"], "cover_w1": w1f["coverage_fidelity"],
                "sem_w0": w0f["semantic_fidelity"], "sem_w1": w1f["semantic_fidelity"],
            })
            u = units[-1]
            u["d_stc_meta"] = u["stc_meta_w1"] - u["stc_meta_w0"]
            u["d_stc_core"] = u["stc_core_w1"] - u["stc_core_w0"]
            u["d_pq"] = u["pq_w1"] - u["pq_w0"]

    d_meta = np.array([u["d_stc_meta"] for u in units])
    d_core = np.array([u["d_stc_core"] for u in units])
    d_pq = np.array([u["d_pq"] for u in units])
    pq_w0 = np.array([u["pq_w0"] for u in units])
    pq_w1 = np.array([u["pq_w1"] for u in units])
    mut_w0 = np.array([u["mut_w0"] for u in units], dtype=float)
    mut_w1 = np.array([u["mut_w1"] for u in units], dtype=float)

    t_meta = paired_t_one_sided(d_meta)
    w_meta = wilcoxon_one_sided(pq_w1 * 0 + np.array([u["stc_meta_w1"] for u in units]),
                                np.array([u["stc_meta_w0"] for u in units]))
    t_pq = paired_t_one_sided(d_pq)
    w_pq = wilcoxon_one_sided(pq_w1, pq_w0)

    # H15: (PQ(B1F,W1)-PQ(B0,W1)) > (PQ(B1F,W0)-PQ(B0,W0)), 差值 >= +10
    per_q = {}
    for q in QUESTIONS:
        def pq_of(arm, cond):
            return idx_p[(q, arm, cond)]["PQ"]
        per_q[q] = {"d_w1": pq_of("B1-F", "W1") - pq_of("B0", "W1"),
                    "d_w0": pq_of("B1-F", "W0") - pq_of("B0", "W0")}
    h15_d1 = float(np.mean([v["d_w1"] for v in per_q.values()]))
    h15_d0 = float(np.mean([v["d_w0"] for v in per_q.values()]))

    mut_total_w0, mut_total_w1 = float(mut_w0.sum()), float(mut_w1.sum())
    worsening = [u["question"] + "/" + u["arm"] for u in units if u["mut_w1"] > u["mut_w0"]]
    rho = spearman(d_meta, d_pq)

    chars_w0 = np.array([u["chars_w0"] for u in units], dtype=float)
    chars_w1 = np.array([u["chars_w1"] for u in units], dtype=float)
    len_ratio = chars_w1 / chars_w0
    len_flagged = [f"{u['question']}/{u['arm']}({r:.2f})"
                   for u, r in zip(units, len_ratio) if abs(r - 1) > 0.15]

    def verdict(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    hypotheses = {
        "H13_structural_transmission": {
            "criterion": "mean(ΔSTC_meta) >= +0.15 且配对单侧 p<0.05",
            "mean_d_stc_meta": t_meta["mean"], "paired_t": t_meta,
            "wilcoxon": w_meta,
            "verdict": verdict(t_meta["mean"] >= 0.15 and t_meta["p_one_sided"] < 0.05),
        },
        "H14_paper_quality": {
            "criterion": "mean(ΔPQ) >= +5（100 分制）且配对单侧 p<0.05",
            "mean_d_pq": t_pq["mean"], "paired_t": t_pq, "wilcoxon": w_pq,
            "verdict": verdict(t_pq["mean"] >= 5.0 and t_pq["p_one_sided"] < 0.05),
        },
        "H15_capability_recovery": {
            "criterion": "(PQ(B1F,W1)-PQ(B0,W1)) > (PQ(B1F,W0)-PQ(B0,W0)) 且差值 >= +10",
            "d_w1_mean": h15_d1, "d_w0_mean": h15_d0, "diff": h15_d1 - h15_d0,
            "per_question": per_q,
            "verdict": verdict(h15_d1 > h15_d0 and (h15_d1 - h15_d0) >= 10.0),
        },
        "H16_no_unauthorized_mutation": {
            "criterion": "Mutations(W1) <= Mutations(W0)+2（24 单元合计），且逐单元不劣化",
            "mutations_w0_total": mut_total_w0, "mutations_w1_total": mut_total_w1,
            "worsening_units": worsening,
            "verdict": verdict(mut_total_w1 <= mut_total_w0 + 2 and not worsening),
        },
        "H17_mechanism_evidence": {
            "criterion": "Spearman(ΔSTC_meta, ΔPQ) > 0.5",
            "spearman_rho": rho,
            "verdict": verdict(rho > 0.5),
        },
        "H18_core_preservation": {
            "criterion": "mean(ΔSTC_core) >= -0.05，且无单元 ΔSTC_core < -0.15",
            "mean_d_stc_core": float(d_core.mean()),
            "min_d_stc_core": float(d_core.min()),
            "violating_units": [f"{u['question']}/{u['arm']}({u['d_stc_core']:+.3f})"
                                for u in units if u["d_stc_core"] < -0.15],
            "verdict": verdict(d_core.mean() >= -0.05 and d_core.min() >= -0.15),
        },
    }
    repaired = [u["question"] + "/" + u["arm"] for u in units
                if any("repair" in b for b in (u["batch_w0"], u["batch_w1"]))]
    out = {
        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        "prereg": str(PREREG.relative_to(ROOT)),
        "n_units": len(units),
        "unit_table": units,
        "length_covariate": {"mean_chars_w0": float(chars_w0.mean()),
                             "mean_chars_w1": float(chars_w1.mean()),
                             "mean_ratio": float(len_ratio.mean()),
                             "units_ratio_dev_gt_15pct": len_flagged},
        "batch_sensitivity": {"repaired_units": repaired,
                              "note": "2020_B/B0 于 G2 修复批次重生成（配对重复缺陷）；"
                                      "主结论同时报告含/不含该单元的 H13 敏感性"},
        "hypotheses": hypotheses,
    }
    # 敏感性：剔除修复单元后的 H13
    mask = np.array([all("repair" not in b for b in (u["batch_w0"], u["batch_w1"]))
                     for u in units])
    if mask.sum() < len(units) and mask.sum() > 1:
        out["batch_sensitivity"]["h13_without_repaired"] = paired_t_one_sided(d_meta[mask])
    (EVAL / "r32_paired_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("=" * 72)
    print("R3.2 PAIRED ANALYSIS — H13–H18 (n=24 units, W1 − W0)")
    print("=" * 72)
    for k, v in hypotheses.items():
        print(f"{k:<32} {v['verdict']}")
    print(f"\nmean ΔSTC_meta={t_meta['mean']:+.3f} (p_t={t_meta['p_one_sided']:.4f}, "
          f"p_w={w_meta['p_one_sided']:.4f})")
    print(f"mean ΔPQ={t_pq['mean']:+.2f} (p_t={t_pq['p_one_sided']:.4f}, "
          f"p_w={w_pq['p_one_sided']:.4f})")
    print(f"ΔSTC_core mean={d_core.mean():+.3f} min={d_core.min():+.3f}")
    print(f"Spearman(ΔSTC_meta,ΔPQ)={rho:+.3f}; mutations W0={mut_total_w0:.0f} "
          f"W1={mut_total_w1:.0f}; worsening={worsening or 'none'}")
    print(f"length ratio mean={len_ratio.mean():.3f}; flagged={len_flagged or 'none'}")
    print(f"analysis -> {EVAL / 'r32_paired_analysis.json'}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="R3.2 evaluation runner (G3–G6)")
    ap.add_argument("command", choices=[
        "manifest", "stc", "fidelity", "blind-prep", "blind-collect", "analyze", "all"])
    args = ap.parse_args()
    if args.command in ("manifest", "all"):
        cmd_manifest()
    if args.command in ("stc", "all"):
        cmd_stc()
    if args.command in ("fidelity", "all"):
        cmd_fidelity()
    if args.command in ("blind-prep", "all"):
        cmd_blind_prep()
    if args.command == "blind-collect":
        cmd_blind_collect()
    if args.command == "analyze":
        cmd_analyze()


if __name__ == "__main__":
    main()
