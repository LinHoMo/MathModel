"""
P15-K003 G2 — 构建校准集（8份匿名盲评包）+ condition_map（严禁外泄）。

选取标准：覆盖 3 臂 F/S/SV × 执行质量高低（fidelity 1.0/0.9/0.82/unverifiable）× 不同题目。
匿名化：包内只含 problem_statement.txt + 表示文件 + run_model.py + execution_result.json + fidelity_report.json。
去除：臂标记、题目标识（run_id/manifest中的problem_id/arm字段）、output_mapping中的题目关联。
condition_map 单独存 g2/_condition_map.json，严禁给 evaluator。
"""
import json
import shutil
from pathlib import Path

PRECHECK = Path(__file__).resolve().parent
G2_DIR = PRECHECK / "g2"
CALIB_DIR = G2_DIR / "calibration_packages"
RUNS_DIR = PRECHECK / "runs"
PROBLEM_CARDS = PRECHECK.parents[1] / "benchmark" / "problem_cards"

# 8份校准集选取（calib_id -> (problem_id, arm, run_id)）
CALIBRATION_SET = [
    ("CALIB_01", "2019_C", "F",  "2968df5edf16"),  # F, queuing, unverifiable
    ("CALIB_02", "2018_B", "F",  "704009dafe7d"),  # F, RGV sim, unverifiable
    ("CALIB_03", "2019_C", "S",  "931538e1b59d"),  # S, fidelity 1.0
    ("CALIB_04", "2020_B", "S",  "d77b53955292"),  # S, fidelity 0.9286
    ("CALIB_05", "2017_B", "S",  "d0f569ac0c2b"),  # S, fidelity 0.8235
    ("CALIB_06", "2018_B", "SV", "d732378e0f15"),  # SV, fidelity 1.0
    ("CALIB_07", "2018_A", "SV", "aa69ed329d67"),  # SV, fidelity 0.9091
    ("CALIB_08", "2017_B", "SV", "21225b715693"),  # SV, fidelity 0.8235
]

def build_calibration_set():
    G2_DIR.mkdir(parents=True, exist_ok=True)
    CALIB_DIR.mkdir(parents=True, exist_ok=True)

    condition_map = {}
    calib_manifest = []

    for calib_id, problem_id, arm, run_id in CALIBRATION_SET:
        src = RUNS_DIR / run_id
        dst = CALIB_DIR / calib_id
        dst.mkdir(parents=True, exist_ok=True)

        # 1. 题面（复制，不改内容——evaluator需要题面评L1）
        prob_card = PROBLEM_CARDS / problem_id
        stmt_src = prob_card / "problem_statement.txt"
        if stmt_src.exists():
            shutil.copy2(stmt_src, dst / "problem_statement.txt")

        # 2. 表示文件（按臂复制）
        if arm == "F":
            shutil.copy2(src / "model_doc.md", dst / "model_doc.md")
        elif arm == "S":
            shutil.copy2(src / "model_ir.json", dst / "model_ir.json")
        elif arm == "SV":
            shutil.copy2(src / "model_ir.json", dst / "model_ir.json")
            shutil.copy2(src / "validation_plan.json", dst / "validation_plan.json")

        # 3. 代码
        shutil.copy2(src / "run_model.py", dst / "run_model.py")

        # 4. 执行结果（匿名化：去除model_id中的题目/臂标记，去除provenance中的question）
        exec_data = json.loads((src / "execution_result.json").read_text(encoding="utf-8"))
        # 匿名化model_id
        if "model_id" in exec_data:
            exec_data["model_id"] = f"model_{calib_id}"
        # 匿名化provenance
        if "provenance" in exec_data and isinstance(exec_data["provenance"], dict):
            exec_data["provenance"].pop("question", None)
            exec_data["provenance"].pop("output_mapping", None)  # mapping可能泄露声明名
        (dst / "execution_result.json").write_text(
            json.dumps(exec_data, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8")

        # 5. fidelity报告（匿名化execution_id）
        fid_src = src / "fidelity_report.json"
        if fid_src.exists():
            fid_data = json.loads(fid_src.read_text(encoding="utf-8"))
            if "execution_id" in fid_data:
                fid_data["execution_id"] = f"exec_{calib_id}"
            if "verification_id" in fid_data:
                fid_data["verification_id"] = f"vr_{calib_id}"
            (dst / "fidelity_report.json").write_text(
                json.dumps(fid_data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")

        # 6. output_mapping（不放入盲评包——它属于CODE artifact元数据，fidelity已消费）
        # 实际上output_mapping对evaluator评L2/L3有参考价值，但可能泄露臂信息。
        # 决定：不放入盲评包，evaluator只能从表示文件和执行结果推断。

        # condition_map（严禁外泄）
        condition_map[calib_id] = {
            "original_run_id": run_id,
            "problem_id": problem_id,
            "arm": arm,
            "fidelity_score": exec_data.get("fidelity_score") or (
                json.loads(fid_src.read_text(encoding="utf-8")).get("fidelity_score")
                if fid_src.exists() else None),
        }

        calib_manifest.append({
            "calib_id": calib_id,
            "files": sorted([f.name for f in dst.iterdir() if f.is_file()]),
            "has_problem_statement": (dst / "problem_statement.txt").exists(),
            "has_execution_result": (dst / "execution_result.json").exists(),
            "has_fidelity_report": (dst / "fidelity_report.json").exists(),
        })

    # 保存condition_map（单独文件，严禁给evaluator）
    (G2_DIR / "_condition_map.json").write_text(
        json.dumps(condition_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    # 保存校准集清单（可给evaluator——只含calib_id和文件列表，不含臂/题目映射）
    (G2_DIR / "_calibration_set.json").write_text(
        json.dumps({"n_packages": len(calib_manifest),
                     "packages": calib_manifest}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    print(f"校准集构建完成：{len(calib_manifest)} 份")
    for m in calib_manifest:
        cm = condition_map[m["calib_id"]]
        print(f"  {m['calib_id']}: {cm['problem_id']} {cm['arm']:3s} "
              f"fid={cm['fidelity_score']} files={m['files']}")
    print(f"\ncondition_map 已保存到 g2/_condition_map.json（严禁外泄给 evaluator）")
    print(f"校准集清单已保存到 g2/_calibration_set.json（可给 evaluator）")

if __name__ == "__main__":
    build_calibration_set()
