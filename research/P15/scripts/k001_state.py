#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k001_state.py — P15-K001 实验状态机

状态链（预注册 §5.1）：
    DESIGN → REVIEW → PREREGISTERED → FROZEN → PREFLIGHT → RUNNING
           → VALIDATION → ANALYSIS → CLOSED

铁律：
  * 状态只能沿链前进，不能回退（回退 = 数据可信度事故）。
  * FROZEN 之后修改任何冻结项 = new revision（v1.1），v1.0 数据作废或单独归档；
    本脚本只记录 revision 事件，不代为修改冻结内容。

用法:
    py -3.12 research/P15/scripts/k001_state.py show
    py -3.12 research/P15/scripts/k001_state.py advance FROZEN [--note "..."]
    py -3.12 research/P15/scripts/k001_state.py set-run <submission_id> REGISTERED
    py -3.12 research/P15/scripts/k001_state.py batch <batch_id> done
    py -3.12 research/P15/scripts/k001_state.py gate <gate_name> PASS|FAIL
    py -3.12 research/P15/scripts/k001_state.py revision v1.1 --note "..."

零第三方依赖。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k001_common as K  # noqa: E402

CHAIN = [
    "DESIGN", "REVIEW", "PREREGISTERED", "FROZEN",
    "PREFLIGHT", "RUNNING", "VALIDATION", "ANALYSIS", "CLOSED",
]

STATUS_PATH = K.STATE / "status.json"

DEFAULT = {
    "experiment_id": K.EXPERIMENT_ID,
    "protocol_version": K.PROTOCOL_VERSION,
    "phase": "DESIGN",
    "revisions": [],
    "history": [],
    "gates": {},
    "batches": {},
    "runs": {"total": 0, "by_status": {}},
    "notes": [],
}


def load() -> dict:
    if STATUS_PATH.exists():
        return K.read_json(STATUS_PATH)
    return dict(DEFAULT)


def save(state: dict) -> None:
    K.write_json(STATUS_PATH, state)


def recount(state: dict) -> None:
    """从 manifests 重算 run 计数（唯一真源，避免增量计数漂移）。"""
    by_status, total = {}, 0
    for p in sorted(K.RUNS.glob("*/manifest.json")):
        try:
            m = K.read_json(p)
        except Exception:
            continue
        total += 1
        s = m.get("status", "UNKNOWN")
        by_status[s] = by_status.get(s, 0) + 1
    state["runs"] = {"total": total, "by_status": by_status}


def log(state: dict, event: str, **kw) -> None:
    entry = {"event": event, "at": K.utc_now_iso()}
    entry.update(kw)
    state.setdefault("history", []).append(entry)


def advance(state: dict, target: str, note: str = "") -> int:
    target = target.upper()
    if target not in CHAIN:
        print(f"[FAIL] 未知状态：{target}（合法：{'/'.join(CHAIN)}）")
        return 1
    cur = state["phase"]
    if CHAIN.index(target) <= CHAIN.index(cur):
        print(f"[FAIL] 不能回退或停在原状态：{cur} → {target}")
        return 1
    if CHAIN.index(target) > CHAIN.index(cur) + 1:
        skipped = CHAIN[CHAIN.index(cur) + 1: CHAIN.index(target)]
        print(f"[FAIL] 不能跳级：{cur} → {target}（跳过了 {'/'.join(skipped)}）")
        return 1
    state["phase"] = target
    log(state, "advance", **{"from": cur, "to": target, "note": note})
    save(state)
    print(f"[OK] {cur} → {target}")
    return 0


def show(state: dict) -> int:
    print("=" * 72)
    print(f"{state['experiment_id']}  protocol_version={state['protocol_version']}")
    print("=" * 72)
    chain = " → ".join(
        (f"[{p}]" if p == state["phase"] else p) for p in CHAIN
    )
    print("phase :", chain)
    print("phase_now:", state["phase"])
    if state.get("revisions"):
        print("revisions:", ", ".join(r.get("version", "?") for r in state["revisions"]))
    if state.get("gates"):
        print("gates:")
        for k, v in state["gates"].items():
            print(f"    {k}: {v}")
    if state.get("batches"):
        print("batches:")
        for k, v in sorted(state["batches"].items()):
            print(f"    {k}: {v}")
    runs = state.get("runs", {})
    if runs:
        print("runs: total =", runs.get("total", 0), "| by_status =", runs.get("by_status", {}))
    hist = state.get("history", [])
    if hist:
        print(f"history (last {min(10, len(hist))}):")
        for h in hist[-10:]:
            print("   ", h.get("at"), h.get("event"), {k: v for k, v in h.items() if k not in ("at", "event")})
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        return show(load())

    state = load()
    cmd = argv[0]

    if cmd == "show":
        return show(state)

    if cmd == "advance":
        if len(argv) < 2:
            print("用法: advance <TARGET> [--note ...]")
            return 1
        note = argv[argv.index("--note") + 1] if "--note" in argv else ""
        return advance(state, argv[1], note)

    if cmd == "revision":
        if len(argv) < 2:
            print("用法: revision <version> --note ...")
            return 1
        note = argv[argv.index("--note") + 1] if "--note" in argv else ""
        state.setdefault("revisions", []).append(
            {"version": argv[1], "at": K.utc_now_iso(), "note": note,
             "from_phase": state["phase"]}
        )
        log(state, "revision", version=argv[1], note=note)
        save(state)
        print(f"[OK] 记录 revision {argv[1]}（v1.0 数据须作废或单独归档）")
        return 0

    if cmd == "gate":
        if len(argv) < 3:
            print("用法: gate <name> PASS|FAIL")
            return 1
        state.setdefault("gates", {})[argv[1]] = argv[2].upper()
        log(state, "gate", name=argv[1], result=argv[2].upper())
        save(state)
        print(f"[OK] gate {argv[1]} = {argv[2].upper()}")
        return 0

    if cmd == "batch":
        if len(argv) < 3:
            print("用法: batch <batch_id> <status>")
            return 1
        state.setdefault("batches", {})[argv[1]] = argv[2]
        log(state, "batch", batch=argv[1], status=argv[2])
        save(state)
        print(f"[OK] batch {argv[1]} = {argv[2]}")
        return 0

    if cmd == "set-run":
        if len(argv) < 3:
            print("用法: set-run <submission_id> <status>")
            return 1
        sid, st = argv[1], argv[2]
        p = K.RUNS / sid / "manifest.json"
        prev = None
        if p.exists():
            m = K.read_json(p)
            prev = m.get("status")
            m["status"] = st
            m["updated_at"] = K.utc_now_iso()
            K.write_json(p, m)
        recount(state)
        log(state, "set-run", submission_id=sid, **{"from": prev, "to": st})
        save(state)
        print(f"[OK] run {sid}: {prev} → {st}   （计数已按 manifests 重算）")
        return 0

    if cmd == "sync":
        recount(state)
        save(state)
        print(f"[OK] 已按 manifests 重算：total={state['runs']['total']} "
              f"by_status={state['runs']['by_status']}")
        return 0

    print(f"[FAIL] 未知命令：{cmd}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
