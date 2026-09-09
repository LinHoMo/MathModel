"""
P15-K003 预检主控脚本 — G4执行有效性dry-run + 18 runs题目区分度预检。

用法: py -3.12 k003_runner.py
产物: research/P15/experiments/P15-K003-precheck/
  runs/<run_id>/  (表示文件+代码+execution_result+fidelity_report+manifest)
  dryrun/         (G4 5场景fidelity报告)
  precheck_results.json  (18 runs汇总)
  g4_dryrun_report.json  (G4结论)
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
import hashlib
from pathlib import Path

# 路径设置
REPO_ROOT = Path(__file__).resolve().parents[4]  # MathModel/
PRECHECK_DIR = Path(__file__).resolve().parent
RUNS_DIR = PRECHECK_DIR / "runs"
DRYRUN_DIR = PRECHECK_DIR / "dryrun"
PROJECT_DIR = PRECHECK_DIR  # 用precheck目录作为harness project_dir

sys.path.insert(0, str(REPO_ROOT / "core"))
sys.path.insert(0, str(PRECHECK_DIR))

from runtime.execution.codegen import run_code_pipeline, register_code, execute_code
from runtime.execution.fidelity import check_fidelity
from k003_problems import PROBLEMS, MAIN_PROBLEMS

ARMS = ["F", "S", "SV"]
SEED = 42


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_run_id(problem_id: str, arm: str, rep: int) -> str:
    raw = f"{problem_id}_{arm}_rep{rep}_{SEED}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ============================================================
# G4 Dry-Run: 5场景fidelity校验
# ============================================================
def g4_dryrun() -> dict:
    """G4执行有效性dry-run：6题真实跑通 + 5场景fidelity校验。"""
    print("=" * 60)
    print("G4 DRY-RUN: 执行有效性预检")
    print("=" * 60)

    DRYRUN_DIR.mkdir(parents=True, exist_ok=True)
    results = {"scenarios": {}, "execution_tests": [], "conclusion": {}}

    # ---- Part 1: 6题真实执行测试 ----
    print("\n--- Part 1: 6题真实执行测试 ---")
    for pid in MAIN_PROBLEMS:
        p = PROBLEMS[pid]()
        model_ir = p["model_ir"]
        code = p["code"]
        output_mapping = p["output_mapping"]

        try:
            pipe_result = run_code_pipeline(
                PROJECT_DIR, model_ir, code,
                model_id=f"M-{pid}-dryrun",
                output_mapping=output_mapping,
            )
            exec_status = pipe_result["exec_status"]
            fid_status = pipe_result["fidelity_status"]
            fid_score = pipe_result["fidelity_score"]
            results["execution_tests"].append({
                "problem_id": pid,
                "exec_status": exec_status,
                "fidelity_status": fid_status,
                "fidelity_score": fid_score,
                "code_id": pipe_result["code_id"],
                "exec_id": pipe_result["exec_id"],
            })
            print(f"  {pid}: exec={exec_status}, fidelity={fid_status}({fid_score})")
        except Exception as e:
            results["execution_tests"].append({
                "problem_id": pid, "error": str(e),
            })
            print(f"  {pid}: ERROR {e}")

    exec_success = sum(1 for t in results["execution_tests"]
                       if t.get("exec_status") == "success")
    results["execution_success_rate"] = round(exec_success / len(MAIN_PROBLEMS), 4)

    # ---- Part 2: 5场景fidelity校验 ----
    print("\n--- Part 2: 5场景fidelity校验 ---")

    # 通用toy model_ir和code
    toy_code_aligned = '''
import json
def solve(inputs):
    return {"profit": 1500.5, "water": 8, "food": 5, "day": 7}
if __name__ == "__main__":
    print(json.dumps(solve({})))
'''

    toy_code_private_ns = '''
import json
def solve(inputs):
    return {"my_profit_val": 1500.5, "my_water_box": 8, "food_left": 5, "arrival": 7}
if __name__ == "__main__":
    print(json.dumps(solve({})))
'''

    toy_code_wrong_model = '''
import json
def solve(inputs):
    # 跑通但输出与声明的模型完全无关
    return {"unrelated_metric": 42, "random_value": 3.14}
if __name__ == "__main__":
    print(json.dumps(solve({})))
'''

    toy_ir = {
        "variables": [
            {"variable_id": "v1", "name": "profit", "symbol": "profit",
             "value_range": {"min": 0, "max": 10000}},
            {"variable_id": "v2", "name": "water", "symbol": "water",
             "value_range": {"min": 0, "max": 20}},
            {"variable_id": "v3", "name": "food", "symbol": "food",
             "value_range": {"min": 0, "max": 20}},
            {"variable_id": "v4", "name": "day", "symbol": "day",
             "value_range": {"min": 0, "max": 10}},
        ],
        "objectives": [
            {"objective_id": "o1", "type": "max", "expression": "max profit",
             "variables_refs": ["v1"]}
        ],
        "constraints": [
            {"constraint_id": "c1", "type": "capacity",
             "expression": "water+food<=20", "variables_refs": ["v2", "v3"]}
        ],
        "equations": [
            {"equation_id": "e1", "latex": "V=max[r+V']", "type": "dp",
             "variables_refs": ["v1", "v2", "v3"]}
        ],
    }

    # 场景1: 对齐 1.0 — 声明名与输出key完全一致
    print("  场景1: 对齐 (expected fidelity=1.0)")
    try:
        r1 = run_code_pipeline(PROJECT_DIR, toy_ir, toy_code_aligned,
                                model_id="G4-S1-aligned", output_mapping={})
        results["scenarios"]["S1_aligned"] = {
            "expected": 1.0, "actual": r1["fidelity_score"],
            "status": r1["fidelity_status"], "pass": r1["fidelity_score"] == 1.0,
        }
        print(f"    fidelity={r1['fidelity_score']} (expected 1.0) {'PASS' if r1['fidelity_score']==1.0 else 'FAIL'}")
    except Exception as e:
        results["scenarios"]["S1_aligned"] = {"error": str(e)}
        print(f"    ERROR: {e}")

    # 场景2: 私有命名空间无mapping 0.0 — 声明名与输出key不同，无output_mapping
    print("  场景2: 私有命名空间无mapping (expected fidelity=0.0)")
    try:
        r2 = run_code_pipeline(PROJECT_DIR, toy_ir, toy_code_private_ns,
                                model_id="G4-S2-private-no-mapping", output_mapping={})
        results["scenarios"]["S2_private_no_mapping"] = {
            "expected": 0.0, "actual": r2["fidelity_score"],
            "status": r2["fidelity_status"], "pass": r2["fidelity_score"] == 0.0,
        }
        print(f"    fidelity={r2['fidelity_score']} (expected 0.0) {'PASS' if r2['fidelity_score']==0.0 else 'FAIL'}")
    except Exception as e:
        results["scenarios"]["S2_private_no_mapping"] = {"error": str(e)}
        print(f"    ERROR: {e}")

    # 场景3: 私有+mapping 1.0 — 声明名与输出key不同，但output_mapping正确翻译
    print("  场景3: 私有+mapping (expected fidelity=1.0)")
    mapping_s3 = {
        "profit": "my_profit_val", "water": "my_water_box",
        "food": "food_left", "day": "arrival",
    }
    try:
        r3 = run_code_pipeline(PROJECT_DIR, toy_ir, toy_code_private_ns,
                                model_id="G4-S3-private-with-mapping",
                                output_mapping=mapping_s3)
        results["scenarios"]["S3_private_with_mapping"] = {
            "expected": 1.0, "actual": r3["fidelity_score"],
            "status": r3["fidelity_status"], "pass": r3["fidelity_score"] == 1.0,
        }
        print(f"    fidelity={r3['fidelity_score']} (expected 1.0) {'PASS' if r3['fidelity_score']==1.0 else 'FAIL'}")
    except Exception as e:
        results["scenarios"]["S3_private_with_mapping"] = {"error": str(e)}
        print(f"    ERROR: {e}")

    # 场景4: 跑通但模型错 0.0 — 代码执行成功但输出完全不包含声明的变量
    print("  场景4: 跑通但模型错 (expected fidelity=0.0)")
    try:
        r4 = run_code_pipeline(PROJECT_DIR, toy_ir, toy_code_wrong_model,
                                model_id="G4-S4-runs-wrong-model",
                                output_mapping={})
        results["scenarios"]["S4_runs_wrong_model"] = {
            "expected": 0.0, "actual": r4["fidelity_score"],
            "status": r4["fidelity_status"], "pass": r4["fidelity_score"] == 0.0,
        }
        print(f"    fidelity={r4['fidelity_score']} (expected 0.0) {'PASS' if r4['fidelity_score']==0.0 else 'FAIL'}")
    except Exception as e:
        results["scenarios"]["S4_runs_wrong_model"] = {"error": str(e)}
        print(f"    ERROR: {e}")

    # 场景5: mapping撒谎 — 用私有命名空间变量名（输出中完全不存在），
    # output_mapping只正确映射1个变量，其余撒谎→部分fidelity≈0.16
    print("  场景5: mapping撒谎 (expected fidelity≈0.16, partial)")
    toy_ir_s5 = {
        "variables": [
            {"variable_id": "v1", "name": "alpha", "symbol": "alpha",
             "value_range": {"min": 0, "max": 10000}},
            {"variable_id": "v2", "name": "beta", "symbol": "beta",
             "value_range": {"min": 0, "max": 20}},
            {"variable_id": "v3", "name": "gamma", "symbol": "gamma",
             "value_range": {"min": 0, "max": 20}},
            {"variable_id": "v4", "name": "delta", "symbol": "delta",
             "value_range": {"min": 0, "max": 10}},
        ],
        "objectives": [
            {"objective_id": "o1", "type": "max", "expression": "max alpha",
             "variables_refs": ["v1"]}
        ],
        "constraints": [
            {"constraint_id": "c1", "type": "capacity",
             "expression": "beta+gamma<=20", "variables_refs": ["v2", "v3"]}
        ],
        "equations": [
            {"equation_id": "e1", "latex": "V=max[r+V']", "type": "dp",
             "variables_refs": ["v1", "v2", "v3"]}
        ],
    }
    # 只正确映射alpha→profit，其余全部撒谎到不存在的key
    mapping_s5 = {
        "alpha": "profit",            # 唯一正确
        "beta": "nonexistent_beta",   # 撒谎
        "gamma": "nonexistent_gamma", # 撒谎
        "delta": "nonexistent_delta", # 撒谎
    }
    try:
        r5 = run_code_pipeline(PROJECT_DIR, toy_ir_s5, toy_code_aligned,
                                model_id="G4-S5-mapping-lies",
                                output_mapping=mapping_s5)
        results["scenarios"]["S5_mapping_lies"] = {
            "expected": "~0.16 (partial)", "actual": r5["fidelity_score"],
            "status": r5["fidelity_status"],
            "pass": r5["fidelity_score"] is not None and 0 < r5["fidelity_score"] < 1.0,
        }
        print(f"    fidelity={r5['fidelity_score']} (expected ~0.16 partial) {'PASS' if r5['fidelity_score'] is not None and 0<r5['fidelity_score']<1.0 else 'FAIL'}")
    except Exception as e:
        results["scenarios"]["S5_mapping_lies"] = {"error": str(e)}
        print(f"    ERROR: {e}")

    # G4结论
    all_pass = all(
        s.get("pass", False) for s in results["scenarios"].values()
        if "pass" in s
    )
    results["conclusion"] = {
        "execution_success_rate": results["execution_success_rate"],
        "execution_pass": results["execution_success_rate"] == 1.0,
        "fidelity_scenarios_pass": all_pass,
        "g4_pass": results["execution_success_rate"] == 1.0 and all_pass,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }

    # 落盘
    report_path = DRYRUN_DIR / "g4_dryrun_report.json"
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    print(f"\nG4报告已写入: {report_path}")
    print(f"G4结论: execution_rate={results['execution_success_rate']}, "
          f"fidelity_all_pass={all_pass}, G4_PASS={results['conclusion']['g4_pass']}")

    return results


# ============================================================
# 18 Runs 题目区分度预检
# ============================================================
def run_18_precheck() -> dict:
    """6题 × 3臂 × 1rep = 18 runs 全量执行。"""
    print("\n" + "=" * 60)
    print("18 RUNS 题目区分度预检")
    print("=" * 60)

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []

    for pid in MAIN_PROBLEMS:
        p = PROBLEMS[pid]()
        print(f"\n--- 题目 {pid}: {p['title']} ---")

        for arm in ARMS:
            run_id = make_run_id(pid, arm, 1)
            run_dir = RUNS_DIR / run_id
            run_dir.mkdir(parents=True, exist_ok=True)

            print(f"  臂 {arm} (run_id={run_id})...", end=" ", flush=True)

            # ---- 写表示文件 ----
            if arm == "F":
                # F臂: model_doc.md 自由文本九部分
                (run_dir / "model_doc.md").write_text(p["model_doc"], encoding="utf-8")
                model_ir_for_pipeline = {}  # F臂无结构化MODEL_IR
                artifact_type = "model_doc.md"
            elif arm == "S":
                # S臂: model_ir.json 18字段契约
                (run_dir / "model_ir.json").write_text(
                    json.dumps(p["model_ir"], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
                model_ir_for_pipeline = p["model_ir"]
                artifact_type = "model_ir.json"
            else:  # SV
                # SV臂: model_ir.json + validation_plan.json
                (run_dir / "model_ir.json").write_text(
                    json.dumps(p["model_ir"], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
                (run_dir / "validation_plan.json").write_text(
                    json.dumps(p["validation_plan"], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
                model_ir_for_pipeline = p["model_ir"]
                artifact_type = "model_ir.json+validation_plan.json"

            # ---- 写代码 ----
            (run_dir / "run_model.py").write_text(p["code"], encoding="utf-8")

            # ---- 写output_mapping ----
            (run_dir / "output_mapping.json").write_text(
                json.dumps(p["output_mapping"], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")

            # ---- 执行管线 ----
            try:
                pipe_result = run_code_pipeline(
                    PROJECT_DIR, model_ir_for_pipeline, p["code"],
                    model_id=f"M-{pid}-{arm}-precheck",
                    solver_id=f"S-{pid}-{arm}",
                    output_mapping=p["output_mapping"],
                )

                # 保存execution_result
                exec_id = pipe_result["exec_id"]
                # 从registry读取execution_result完整数据
                from runtime.artifacts.registry import ArtifactRegistry
                reg = ArtifactRegistry(PROJECT_DIR / "state" / "registry.json")
                reg.load()
                exec_art = reg.get(exec_id)
                exec_data = dict(exec_art.data or {}) if exec_art else {}

                (run_dir / "execution_result.json").write_text(
                    json.dumps(exec_data, ensure_ascii=False, indent=2, default=str) + "\n",
                    encoding="utf-8")

                # 保存fidelity_report
                fid_report_path = pipe_result.get("fidelity_report")
                if fid_report_path and Path(fid_report_path).exists():
                    fid_data = json.loads(Path(fid_report_path).read_text(encoding="utf-8"))
                    (run_dir / "fidelity_report.json").write_text(
                        json.dumps(fid_data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
                else:
                    fid_data = {}

                # 写manifest
                manifest = {
                    "run_id": run_id,
                    "problem_id": pid,
                    "arm": arm,
                    "rep": 1,
                    "seed": SEED,
                    "batch": "precheck",
                    "block_role": "main",
                    "status": "EXECUTED",
                    "model_family_primary": p["family_primary"],
                    "artifact_type": artifact_type,
                    "code_sha256": sha256_text(p["code"]),
                    "output_mapping": p["output_mapping"],
                    "execution": {
                        "code_id": pipe_result["code_id"],
                        "exec_id": pipe_result["exec_id"],
                        "exec_status": pipe_result["exec_status"],
                        "duration_ms": exec_data.get("duration_ms"),
                        "returncode": exec_data.get("returncode"),
                        "outputs_keys": list((exec_data.get("outputs") or {}).keys()),
                    },
                    "fidelity": {
                        "status": pipe_result["fidelity_status"],
                        "score": pipe_result["fidelity_score"],
                        "verification_id": pipe_result["verification_id"],
                    },
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "generator": {"agent_identity": "organizer_agent", "role": "external_constructor"},
                }
                (run_dir / "manifest.json").write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

                # 汇总
                result_entry = {
                    "run_id": run_id, "problem_id": pid, "arm": arm, "rep": 1,
                    "exec_status": pipe_result["exec_status"],
                    "fidelity_status": pipe_result["fidelity_status"],
                    "fidelity_score": pipe_result["fidelity_score"],
                    "duration_ms": exec_data.get("duration_ms"),
                    "outputs": exec_data.get("outputs") or {},
                    "model_family": p["family_primary"],
                }
                all_results.append(result_entry)
                print(f"exec={pipe_result['exec_status']}, "
                      f"fid={pipe_result['fidelity_status']}({pipe_result['fidelity_score']})")

            except Exception as e:
                print(f"ERROR: {e}")
                import traceback
                (run_dir / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
                all_results.append({
                    "run_id": run_id, "problem_id": pid, "arm": arm, "rep": 1,
                    "exec_status": "error", "error": str(e),
                })

    # 汇总落盘
    summary = {
        "total_runs": len(all_results),
        "execution_success": sum(1 for r in all_results if r.get("exec_status") == "success"),
        "runs": all_results,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    summary_path = PRECHECK_DIR / "precheck_results.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n",
                             encoding="utf-8")
    print(f"\n18 runs汇总已写入: {summary_path}")
    print(f"执行成功: {summary['execution_success']}/{summary['total_runs']}")

    return summary


# ============================================================
# 区分度统计分析
# ============================================================
def analyze_discrimination(results: dict) -> dict:
    """分析S-F方向与效应量。"""
    print("\n" + "=" * 60)
    print("区分度统计分析")
    print("=" * 60)

    runs = results["runs"]
    # 按题目分组
    by_problem = {}
    for r in runs:
        pid = r["problem_id"]
        if pid not in by_problem:
            by_problem[pid] = {}
        by_problem[pid][r["arm"]] = r

    # 构建代理评分（因为预检无盲评，用执行级指标构建MCQ代理）
    # 代理MCQ = execution_success(40) + fidelity_score*30 + coverage(30)
    # F臂fidelity=unverifiable→0分（如实记录格式不对称的延续）
    def proxy_mcq(r):
        exec_ok = 1.0 if r.get("exec_status") == "success" else 0.0
        fid = r.get("fidelity_score") or 0.0
        # coverage: 输出key数量（代理）
        out_keys = len(r.get("outputs") or {})
        coverage = min(1.0, out_keys / 8.0)
        return round(exec_ok * 40 + fid * 30 + coverage * 30, 2)

    per_problem = []
    s_f_diffs = []
    sv_s_diffs = []
    sv_f_diffs = []

    for pid in MAIN_PROBLEMS:
        if pid not in by_problem:
            continue
        arms = by_problem[pid]
        f_score = proxy_mcq(arms.get("F", {})) if "F" in arms else None
        s_score = proxy_mcq(arms.get("S", {})) if "S" in arms else None
        sv_score = proxy_mcq(arms.get("SV", {})) if "SV" in arms else None

        entry = {"problem_id": pid, "F_MCQ_proxy": f_score,
                 "S_MCQ_proxy": s_score, "SV_MCQ_proxy": sv_score}

        if f_score is not None and s_score is not None:
            entry["S_minus_F"] = round(s_score - f_score, 2)
            s_f_diffs.append(s_score - f_score)
        if s_score is not None and sv_score is not None:
            entry["SV_minus_S"] = round(sv_score - s_score, 2)
            sv_s_diffs.append(sv_score - s_score)
        if f_score is not None and sv_score is not None:
            entry["SV_minus_F"] = round(sv_score - f_score, 2)
            sv_f_diffs.append(sv_score - f_score)

        # fidelity详情
        for arm in ["F", "S", "SV"]:
            if arm in arms:
                entry[f"{arm}_fidelity"] = arms[arm].get("fidelity_status")
                entry[f"{arm}_fidelity_score"] = arms[arm].get("fidelity_score")
                entry[f"{arm}_exec"] = arms[arm].get("exec_status")

        per_problem.append(entry)

    # 总效应量（配对差均值 + bootstrap CI）
    import random
    random.seed(SEED)

    def bootstrap_ci(diffs, n_boot=100000):
        if not diffs:
            return {"mean": None, "ci_low": None, "ci_high": None, "n": 0}
        n = len(diffs)
        mean = sum(diffs) / n
        boot_means = []
        for _ in range(n_boot):
            sample = [diffs[random.randint(0, n - 1)] for _ in range(n)]
            boot_means.append(sum(sample) / n)
        boot_means.sort()
        ci_low = boot_means[int(0.025 * n_boot)]
        ci_high = boot_means[int(0.975 * n_boot)]
        # sd
        variance = sum((d - mean) ** 2 for d in diffs) / max(1, n - 1)
        sd = variance ** 0.5
        return {"mean": round(mean, 2), "ci_low": round(ci_low, 2),
                "ci_high": round(ci_high, 2), "sd": round(sd, 2),
                "n": n, "se": round(sd / (n ** 0.5), 2) if n > 0 else None}

    sf_stats = bootstrap_ci(s_f_diffs)
    svs_stats = bootstrap_ci(sv_s_diffs)
    svf_stats = bootstrap_ci(sv_f_diffs)

    # 决策
    def decision(stats):
        if stats["mean"] is None:
            return "insufficient_data"
        if stats["ci_low"] > 0:
            return "POSITIVE"
        elif stats["ci_high"] < 0:
            return "NEGATIVE"
        else:
            return "inclusive"

    analysis = {
        "per_problem": per_problem,
        "S_minus_F": {**sf_stats, "decision": decision(sf_stats)},
        "SV_minus_S": {**svs_stats, "decision": decision(svs_stats)},
        "SV_minus_F": {**svf_stats, "decision": decision(svf_stats)},
        "proxy_mcq_note": "预检无盲评，MCQ为执行级代理评分(exec_success*40+fidelity*30+coverage*30)，"
                           "正式实验以3 evaluator盲评rubric v1.2为准",
        "precheck_decision_rule": "DRAFT §5: 若Δ<3且CI含0→如实记录低功效观察，不做事后调参/提rep",
    }

    print(f"\n  S−F: Δ={sf_stats['mean']}, CI=[{sf_stats['ci_low']}, {sf_stats['ci_high']}], "
          f"decision={analysis['S_minus_F']['decision']}")
    print(f"  SV−S: Δ={svs_stats['mean']}, CI=[{svs_stats['ci_low']}, {svs_stats['ci_high']}], "
          f"decision={analysis['SV_minus_S']['decision']}")
    print(f"  SV−F: Δ={svf_stats['mean']}, CI=[{svf_stats['ci_low']}, {svf_stats['ci_high']}], "
          f"decision={analysis['SV_minus_F']['decision']}")

    return analysis


# ============================================================
# Main
# ============================================================
def main():
    t0 = time.time()
    print(f"P15-K003 预检启动 @ {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目目录: {PROJECT_DIR}")
    print(f"主检验题目: {MAIN_PROBLEMS}")

    # G4 Dry-Run
    g4_results = g4_dryrun()

    # 18 Runs
    precheck_results = run_18_precheck()

    # 区分度分析
    analysis = analyze_discrimination(precheck_results)

    # 最终汇总
    final = {
        "g4": g4_results["conclusion"],
        "precheck": {
            "total_runs": precheck_results["total_runs"],
            "execution_success": precheck_results["execution_success"],
            "execution_success_rate": round(
                precheck_results["execution_success"] / precheck_results["total_runs"], 4),
        },
        "discrimination": analysis,
        "duration_s": round(time.time() - t0, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }

    final_path = PRECHECK_DIR / "precheck_summary.json"
    final_path.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"预检完成! 耗时 {final['duration_s']}s")
    print(f"G4 PASS: {final['g4']['g4_pass']}")
    print(f"18 runs 执行成功率: {final['precheck']['execution_success_rate']}")
    print(f"汇总文件: {final_path}")
    print(f"{'=' * 60}")

    return final


if __name__ == "__main__":
    main()
