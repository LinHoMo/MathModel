#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 condition_map 和匿名盲评 bundles（66 runs）。"""
import json
import shutil
from pathlib import Path

FORMAL_DIR = Path(__file__).resolve().parent
RUNS_DIR = FORMAL_DIR / "runs"
BUNDLES_DIR = FORMAL_DIR / "bundles"
KEY_DIR = FORMAL_DIR / "key"
PROBLEM_CARDS = FORMAL_DIR.parents[2] / "benchmark" / "problem_cards"

BUNDLES_DIR.mkdir(parents=True, exist_ok=True)
KEY_DIR.mkdir(parents=True, exist_ok=True)

# 收集所有 runs
manifests = []
for run_dir in sorted(RUNS_DIR.iterdir()):
    mp = run_dir / "manifest.json"
    if mp.exists():
        m = json.loads(mp.read_text(encoding="utf-8"))
        manifests.append(m)

print(f"收集到 {len(manifests)} runs")

# 生成 condition_map（严禁外泄给 evaluator）
condition_map = {}
for i, m in enumerate(manifests):
    bundle_id = f"BUNDLE_{i+1:03d}"
    sid = m["submission_id"]
    condition_map[bundle_id] = {
        "submission_id": sid,
        "problem_id": m["problem_id"],
        "arm": m["arm"],
        "seed": m["seed"],
        "model_family": m.get("model_family", ""),
        "exec_status": m.get("exec_status", ""),
        "fidelity_score": m.get("fidelity_score"),
    }

(KEY_DIR / "condition_map.json").write_text(
    json.dumps(condition_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"condition_map: {len(condition_map)} entries -> key/condition_map.json")

# 生成匿名 bundles
for bundle_id, info in condition_map.items():
    sid = info["submission_id"]
    src = RUNS_DIR / sid
    dst = BUNDLES_DIR / bundle_id
    dst.mkdir(parents=True, exist_ok=True)

    # 1. 题面（从 problem_cards 复制，不改内容）
    prob_card = PROBLEM_CARDS / info["problem_id"]
    stmt = prob_card / "problem_statement.txt"
    if stmt.exists():
        shutil.copy2(stmt, dst / "problem_statement.txt")

    # 2. 表示文件（按臂复制）
    arm = info["arm"]
    if arm == "F":
        if (src / "model_doc.md").exists():
            shutil.copy2(src / "model_doc.md", dst / "model_doc.md")
    elif arm == "S":
        if (src / "model_ir.json").exists():
            shutil.copy2(src / "model_ir.json", dst / "model_ir.json")
    elif arm == "SV":
        if (src / "model_ir.json").exists():
            shutil.copy2(src / "model_ir.json", dst / "model_ir.json")
        if (src / "validation_plan.json").exists():
            shutil.copy2(src / "validation_plan.json", dst / "validation_plan.json")

    # 3. 代码
    if (src / "run_model.py").exists():
        shutil.copy2(src / "run_model.py", dst / "run_model.py")

    # 4. 执行结果（匿名化 model_id）
    er_src = src / "execution_result.json"
    if er_src.exists():
        er = json.loads(er_src.read_text(encoding="utf-8"))
        er["model_id"] = f"model_{bundle_id}"
        if "provenance" in er and isinstance(er["provenance"], dict):
            er["provenance"].pop("question", None)
            er["provenance"].pop("output_mapping", None)
        (dst / "execution_result.json").write_text(
            json.dumps(er, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

    # 5. fidelity 报告（匿名化）
    fr_src = src / "fidelity_report.json"
    if fr_src.exists():
        fr = json.loads(fr_src.read_text(encoding="utf-8"))
        if "execution_id" in fr:
            fr["execution_id"] = f"exec_{bundle_id}"
        if "verification_id" in fr:
            fr["verification_id"] = f"vr_{bundle_id}"
        (dst / "fidelity_report.json").write_text(
            json.dumps(fr, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 统计
by_arm = {}
by_problem = {}
by_fidelity = {"aligned": 0, "misaligned": 0, "unverifiable": 0, "other": 0}
exec_success = 0
for m in manifests:
    a = m["arm"]
    p = m["problem_id"]
    by_arm[a] = by_arm.get(a, 0) + 1
    by_problem[p] = by_problem.get(p, 0) + 1
    if m.get("exec_status") == "success":
        exec_success += 1
    fs = m.get("fidelity_status", "other")
    if fs in by_fidelity:
        by_fidelity[fs] += 1
    else:
        by_fidelity["other"] += 1

summary = {
    "total_runs": len(manifests),
    "exec_success_rate": round(exec_success / len(manifests), 4) if manifests else 0,
    "by_arm": by_arm,
    "by_problem": by_problem,
    "by_fidelity_status": by_fidelity,
    "bundles_generated": len(list(BUNDLES_DIR.glob("BUNDLE_*"))),
}

(FORMAL_DIR / "run_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(f"\n=== 汇总 ===")
print(f"总 runs: {summary['total_runs']}")
print(f"exec_success_rate: {summary['exec_success_rate']}")
print(f"by_arm: {by_arm}")
print(f"by_problem: {by_problem}")
print(f"by_fidelity_status: {by_fidelity}")
print(f"bundles: {summary['bundles_generated']}")
print(f"\ncondition_map -> key/condition_map.json (严禁外泄)")
print(f"anonymous bundles -> bundles/BUNDLE_001/ ~ BUNDLE_{len(manifests):03d}/")
