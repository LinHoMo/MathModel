#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run Record 记录器（System Hardening P3 —— Observability / Run Provenance）。

每次会话运行结束后落盘 state/runs/<run_id>.json：
  run_id 幂等派生 = sha1(project|questions|workflow_version|input_hash)[:12]
  （同配置同输入的重跑得到相同 run_id，天然支持确定性重放审计）。

全部哈希为 sha256（对称口径），确定性、零第三方依赖。
model_provider/model_version/token_cost 由外部 executor 通过 run_meta 注入，
runtime 零 LLM 调用时为 null（诚实缺省，不臆造）。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

PROMPT_DIRS = ["src/modeling_harness/roles", "src/modeling_harness/workflows"]
SKILL_DIRS = ["src/modeling_harness/skills"]


def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _hash_path(p: Path) -> str:
    try:
        return _hash_bytes(p.read_bytes())
    except Exception:
        return _hash_bytes(b"<missing>")


def hash_globs(patterns: list[str], base: Path) -> str:
    """按路径排序的目录文件组合哈希（工作流/角色/技能版本口径）。"""
    files: list[Path] = []
    for pat in patterns:
        for p in sorted((base / pat).rglob("*.yaml")):
            if p not in files:
                files.append(p)
    files = sorted(set(files), key=lambda f: str(f))
    h = hashlib.sha256()
    for f in files:
        h.update(str(f.relative_to(base)).encode("utf-8"))
        h.update(_hash_path(f).encode("utf-8"))
    return h.hexdigest()


def compute_input_hash(project_dir) -> str:
    """inputs/ 目录组合哈希；无输入时返回 <empty-inputs> 标记哈希。"""
    indir = Path(project_dir) / "inputs"
    if not indir.exists() or not any(indir.iterdir()):
        return _hash_bytes(b"<empty-inputs>")
    files = sorted(f for f in indir.rglob("*") if f.is_file())
    h = hashlib.sha256()
    for f in files:
        h.update(f.name.encode("utf-8"))
        h.update(_hash_path(f).encode("utf-8"))
    return h.hexdigest()


def workflow_version() -> str:
    """工作流定义版本 = roles/workflows YAML 组合哈希。"""
    return hash_globs(PROMPT_DIRS, REPO)


def skill_version() -> str:
    """技能指令包版本 = core/skills 组合哈希。"""
    return hash_globs(SKILL_DIRS, REPO)


def tool_version() -> str:
    """工具链版本 = catalog schema_version @ git HEAD 短哈希。"""
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO),
                           capture_output=True, text=True, timeout=15)
        head = r.stdout.strip()[:9] if r.returncode == 0 else "N/A"
    except Exception:
        head = "N/A"
    try:
        raw = Path(REPO / "catalog.yaml").read_text(encoding="utf-8")
        m = re.search(r"^schema_version:\s*(\d+)", raw, re.MULTILINE)
        ver = m.group(1) if m else "?"
    except Exception:
        ver = "?"
    return f"catalog-v{ver}@{head}"


def derive_run_id(project: str, questions: list[str],
                  wf_version: str, input_hash: str) -> str:
    seed = f"{project}|{','.join(sorted(questions))}|{wf_version}|{input_hash}"
    return _hash_bytes(seed.encode("utf-8"))[:12]


def iso_ts(epoch: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def emit_run_record(project_dir, questions: list[str], *,
                    status: str, started_at: float,
                    run_meta: dict | None = None,
                    parent_run_id: str | None = None,
                    engine_summary: dict | None = None) -> dict:
    """构建完整 Run Record——在 checkpoint 之后调用（读取落盘哈希）。"""
    project_dir = Path(project_dir)
    sdir = project_dir / "state"
    input_hash = compute_input_hash(project_dir)
    wf = workflow_version()
    meta = run_meta or {}
    eng = engine_summary or {}
    rec = {
        "schema_version": 1,
        "run_id": derive_run_id(str(project_dir), list(questions), wf, input_hash),
        "parent_run_id": parent_run_id,
        "project": str(project_dir),
        "questions": sorted(questions),
        "status": status,
        "workflow_version": wf,
        "skill_version": skill_version(),
        "tool_version": tool_version(),
        "model_provider": meta.get("model_provider"),
        "model_version": meta.get("model_version"),
        "prompt_hash": wf,          # prompt 口径 = roles/workflows 指令文件哈希
        "input_hash": input_hash,
        "artifact_hash": _hash_path(sdir / "registry.json"),
        "evidence_hash": _hash_path(sdir / "evidence_graph.json"),
        "decision_log_hash": _hash_path(sdir / "decision_log.json"),
        "latency": {
            "started_at": iso_ts(started_at),
            "finished_at": iso_ts(time.time()),
            "seconds": round(time.time() - started_at, 2),
        },
        "started_at": iso_ts(started_at),
        "token_cost": meta.get("token_cost"),
        "engine": {
            "completed_nodes": int(eng.get("completed", 0)),
            "retries": int(eng.get("retries", 0)),
            "failures": [str(f) for f in eng.get("failures", [])],
        },
        "decision": meta.get("decision"),
    }
    save_run_record(project_dir, rec)
    return rec


def save_run_record(project_dir, record: dict) -> Path:
    """原子落盘 state/runs/<run_id>.json。"""
    rdir = Path(project_dir) / "state" / "runs"
    rdir.mkdir(parents=True, exist_ok=True)
    dst = rdir / f"{record['run_id']}.json"
    fd, tmp = tempfile.mkstemp(dir=str(rdir), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return dst


def load_run_record(project_dir, run_id: str | None = None) -> dict:
    """读取 run record；run_id 缺省取目录内最新（按 mtime）。"""
    rdir = Path(project_dir) / "state" / "runs"
    if not rdir.exists():
        raise FileNotFoundError(f"无运行记录目录: {rdir}")
    if run_id is None:
        files = sorted(rdir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        if not files:
            raise FileNotFoundError(f"运行记录目录为空: {rdir}")
        run_id = files[-1].stem
    p = rdir / f"{run_id}.json"
    if not p.exists():
        raise FileNotFoundError(f"运行记录不存在: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def list_run_records(project_dir) -> list[dict]:
    rdir = Path(project_dir) / "state" / "runs"
    if not rdir.exists():
        return []
    out = []
    for p in sorted(rdir.glob("*.json"), key=lambda p: p.stat().st_mtime):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out