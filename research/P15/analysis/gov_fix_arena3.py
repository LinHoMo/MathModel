# -*- coding: utf-8 -*-
"""arena_runner load_pool skipped 原因化。"""
from pathlib import Path

p = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\benchmark\arena\arena_runner.py")
s = p.read_text(encoding="utf-8")

old = '''    pool: dict[str, list[dict]] = {}
    skipped: list[str] = []
    for run_dir in sorted(pool_root.iterdir()):
        if not run_dir.is_dir():
            continue
        mir_f, code_f, om_f, man_f = (run_dir / "model_ir.json",
                                      run_dir / "run_model.py",
                                      run_dir / "output_mapping.json",
                                      run_dir / "manifest.json")
        if not all(f.exists() for f in (mir_f, code_f, om_f, man_f)):
            skipped.append(run_dir.name)
            continue
        manifest = json.loads(man_f.read_text(encoding="utf-8"))
        pid = manifest.get("problem_id")
        if not pid:
            skipped.append(run_dir.name)
            continue
        cand = {
            "run_id": run_dir.name,
            "arm": manifest.get("arm"),
            "problem_id": pid,
            "model_ir": json.loads(mir_f.read_text(encoding="utf-8")),
            "code": code_f.read_text(encoding="utf-8"),
            "output_mapping": json.loads(om_f.read_text(encoding="utf-8")),
        }
        pool.setdefault(pid, []).append(cand)
    return pool, skipped'''

new = '''    pool: dict[str, list[dict]] = {}
    skipped: list[dict] = []
    for run_dir in sorted(pool_root.iterdir()):
        if not run_dir.is_dir():
            continue
        mir_f, code_f, om_f, man_f = (run_dir / "model_ir.json",
                                      run_dir / "run_model.py",
                                      run_dir / "output_mapping.json",
                                      run_dir / "manifest.json")
        if not man_f.exists():
            skipped.append({"run_id": run_dir.name, "reason": "缺 manifest.json"})
            continue
        manifest = json.loads(man_f.read_text(encoding="utf-8"))
        pid = manifest.get("problem_id")
        if not pid:
            skipped.append({"run_id": run_dir.name, "reason": "manifest 无 problem_id"})
            continue
        if not mir_f.exists():
            # K003 设计：F 臂（自由文本输入）不产生 MODEL_IR，不入 arena 池
            skipped.append({"run_id": run_dir.name, "reason": "F 臂无 model_ir"
                           if manifest.get("arm") == "F" else "缺 model_ir.json"})
            continue
        if not all(f.exists() for f in (code_f, om_f)):
            skipped.append({"run_id": run_dir.name,
                            "reason": "缺 run_model.py 或 output_mapping.json"})
            continue
        cand = {
            "run_id": run_dir.name,
            "arm": manifest.get("arm"),
            "problem_id": pid,
            "model_ir": json.loads(mir_f.read_text(encoding="utf-8")),
            "code": code_f.read_text(encoding="utf-8"),
            "output_mapping": json.loads(om_f.read_text(encoding="utf-8")),
        }
        pool.setdefault(pid, []).append(cand)
    return pool, skipped'''

assert old in s, "pattern not found"
p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("load_pool skipped reasons OK")
