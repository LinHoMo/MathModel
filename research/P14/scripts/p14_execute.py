#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""p14_execute.py — P14.3 执行器：把 specs 的 21 个实验落成 Execution/Result 实体.

模式:
  execute <run_dir>   # 逐 spec 逐实验执行（seed=42，timeout 180s），写 Execution/Result/logs
  replay  <run_dir>   # 对全部 completed Execution 确定性重放，比对 result.data 规范 hash，
                      # 追加 manifest.replays 记录（不修改任何实体）

约定（RUNBOOK_P14_1.md §4）：code 位于 <run>/code/q<question>.py，
Execution.runner.code_sha256 = 该文件 sha256（覆盖场景基线常数的溯源）。
Result.data = 实验模块 stdout JSON 的 metrics 对象。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p14_integrity_gate import canonical_hash  # noqa: E402

QUESTION_FILE = {"2019_A": "q2019A.py", "2020_B": "q2020B.py",
                 "2024_B": "q2024B.py", "2022_C": "q2022C.py"}
PY = sys.executable
TIMEOUT = 300


def now():
    return datetime.now().isoformat(timespec="seconds")


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def write_entity(run: Path, sub: str, e: dict):
    p = run / sub / f"{e['entity_id']}.json"
    p.write_text(json.dumps(e, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def next_id(existing: list, prefix: str) -> str:
    n = len(existing) + 1
    return f"{prefix}{n:03d}"


def run_experiment(run: Path, q: str, exp_id: str, log_path: Path):
    code_file = (run / "code" / QUESTION_FILE[q]).resolve()
    try:
        proc = subprocess.run([PY, str(code_file), exp_id], cwd=str(code_file.parent),
                              capture_output=True, text=True, timeout=TIMEOUT,
                              encoding="utf-8")
    except subprocess.TimeoutExpired:
        log_path.write_text(f"TIMEOUT after {TIMEOUT}s", encoding="utf-8")
        return None, "timeout", code_file
    log_path.write_text(
        f"exit={proc.returncode}\n--stdout--\n{proc.stdout[-8000:]}\n--stderr--\n{proc.stderr[-4000:]}",
        encoding="utf-8")
    if proc.returncode != 0:
        return None, "failed", code_file
    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        return payload.get("metrics", {}), "completed", code_file
    except (json.JSONDecodeError, IndexError):
        return None, "failed", code_file


def mode_execute(run: Path):
    specs = sorted((run / "specs").glob("*.json"))
    exe_list = sorted((run / "executions").glob("*.json")) if (run / "executions").exists() else []
    n_exe = len(exe_list)
    n_res = len(sorted((run / "results").glob("*.json"))) if (run / "results").exists() else 0
    (run / "logs").mkdir(exist_ok=True)
    for sp in specs:
        spec = load_json(sp)
        q = spec["question_id"]
        for exp in spec["experiments"]:
            exp_id = exp["experiment_id"]
            eid = f"P14-EXE{n_exe + 1:03d}"
            rid = f"P14-RES{n_res + 1:03d}"
            log_path = run / "logs" / f"{eid}.log"
            metrics, status, code_file = run_experiment(run, q, exp_id, log_path)
            if metrics is None and status == "completed":
                status = "failed"
            exe = {
                "entity_type": "execution", "entity_id": eid,
                "schema_version": "p14.v1", "run_id": spec["run_id"],
                "created_at": now(),
                "spec_ref": {"entity_type": "experiment_spec",
                             "entity_id": spec["entity_id"],
                             "content_sha256": spec["content_sha256"]},
                "experiment_id": exp_id,
                "runner": {"backend": "python-sandbox",
                           "python_version": sys.version.split()[0],
                           "entrypoint": f"code/{QUESTION_FILE[q]}::{exp_id}",
                           "code_sha256": hashlib.sha256(code_file.read_bytes()).hexdigest()},
                "seed": 42, "runs": exp.get("runs", 1), "status": status,
                "log_path": f"logs/{eid}.log",
                "env_fingerprint": f"py{sys.version_info.major}.{sys.version_info.minor}-win64;numpy",
                "parent_ref": {"entity_type": "experiment_spec",
                               "entity_id": spec["entity_id"],
                               "content_sha256": spec["content_sha256"]},
                "content_sha256": None,
            }
            write_entity(run, "executions", exe)
            n_exe += 1
            res = {
                "entity_type": "result", "entity_id": rid,
                "schema_version": "p14.v1", "run_id": spec["run_id"],
                "created_at": now(),
                "execution_ref": {"entity_type": "execution", "entity_id": eid,
                                  "content_sha256": None},
                "data": {"metrics": metrics or {}, "experiment_id": exp_id},
                "status": "valid" if status == "completed" else "invalid",
                "parent_ref": {"entity_type": "execution", "entity_id": eid,
                               "content_sha256": None},
                "content_sha256": None,
            }
            write_entity(run, "results", res)
            n_res += 1
            print(f"  {eid} {rid} {exp_id:<18} {status}")
    # 先终化 execution 自身 hash，再回填 result 引用（顺序不可换）
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from p14_integrity_gate import canonical_hash as _ch
    for f in sorted((run / "executions").glob("*.json")):
        x = load_json(f)
        if x.get("content_sha256") is None:
            x["content_sha256"] = _ch(x)
            f.write_text(json.dumps(x, ensure_ascii=False, indent=2), encoding="utf-8")
    # 回填 execution/result 引用 hash（execution 已定稿；result 引用 execution）
    for f in sorted((run / "results").glob("*.json")):
        r = load_json(f)
        xref = r["execution_ref"]
        x = load_json(run / "executions" / f"{xref['entity_id']}.json")
        xref["content_sha256"] = x["content_sha256"]
        r["parent_ref"]["content_sha256"] = x["content_sha256"]
        f.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"execute done: {n_exe} executions, {n_res} results")


def data_hash(r: dict) -> str:
    blob = json.dumps(r["data"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def mode_replay(run: Path):
    man = load_json(run / "manifest.json")
    man.setdefault("replays", [])
    done = {rp.get("execution_id") for rp in man["replays"] if rp.get("match") is True}
    exes = sorted((run / "executions").glob("*.json"))
    for f in exes:
        x = load_json(f)
        if x["status"] != "completed" or x["entity_id"] in done:
            continue
        qmap = {"2020": "2020_B", "2024": "2024_B", "2022": "2022_C"}
        q = qmap[x["experiment_id"].split("-")[1][:4]]
        exp_id = x["experiment_id"]
        code_file = run / "code" / QUESTION_FILE[q]
        log_path = run / "logs" / f"{x['entity_id']}.replay.log"
        metrics, status, _ = run_experiment(run, q, exp_id, log_path)
        # 与原 Result.data 比对（规范化）
        res_files = sorted((run / "results").glob("*.json"))
        orig = None
        for rf in res_files:
            r = load_json(rf)
            if r["execution_ref"]["entity_id"] == x["entity_id"]:
                orig = r
                break
        orig_hash = data_hash(orig) if orig else None
        if status == "completed" and orig is not None:
            replay_hash = hashlib.sha256(json.dumps(
                {"metrics": metrics, "experiment_id": exp_id},
                ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            match = replay_hash == orig_hash
        else:
            replay_hash = None
            match = False
        man["replays"].append({"execution_id": x["entity_id"], "replayed_at": now(),
                               "result_sha256_original": orig_hash,
                               "result_sha256_replay": replay_hash,
                               "match": bool(match)})
        mark = "OK " if match else "MISMATCH"
        print(f"  replay {x['entity_id']} {exp_id:<18} {mark}")
    (run / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    n_ok = sum(1 for rp in man["replays"] if rp["match"])
    print(f"replay done: {n_ok}/{len(man['replays'])} match")


if __name__ == "__main__":
    mode = sys.argv[1]
    rd = Path(sys.argv[2])
    if mode == "execute":
        mode_execute(rd)
    elif mode == "replay":
        mode_replay(rd)
    else:
        print("usage: p14_execute.py execute|replay <run_dir>")
        sys.exit(2)
