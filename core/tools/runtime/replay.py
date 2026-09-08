#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""replay CLI —— 运行重放 / 差异归因（System Hardening P3）。

用法:
    python core/tools/replay.py <项目>                 # 校验最新一次运行（确定性重放）
    python core/tools/replay.py <项目> list            # 列出全部运行记录
    python core/tools/replay.py <项目> diff <A> <B>    # 两次运行逐字段差异 + 归因
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))

from runtime.execution.replay import diff as replay_diff  # noqa: E402
from runtime.execution.replay import list_runs, verify  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="运行重放校验 / 差异归因（Hardening P3）")
    ap.add_argument("project", help="项目目录名或路径")
    ap.add_argument("op", nargs="?", default="verify",
                    choices=["verify", "list", "diff"],
                    help="verify（默认）/ list / diff")
    ap.add_argument("rest", nargs="*", help="diff 模式的 run_a run_b")
    args = ap.parse_args()

    project = Path(args.project)
    if not project.exists():
        # 与 state.py 契约对齐： bare 项目名可在 projects/ 下解析（RC-S1 B×1）
        cand = ROOT / "projects" / args.project
        if cand.exists():
            project = cand
    if args.op == "list":
        for r in list_runs(project):
            print(f"{r['run_id']}  {r['status']:<10} {r['started_at']}  "
                  f"parent={r['parent_run_id']}")
        return 0
    if args.op == "diff":
        if len(args.rest) != 2:
            print("[replay] diff 需要两个 run_id", file=sys.stderr)
            return 2
        rep = replay_diff(project, args.rest[0], args.rest[1])
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0 if not rep["changed_fields"] else 1

    rep = verify(project)
    if not rep.get("ok"):
        print(f"[replay] FAIL（run {rep.get('run_id')}）:")
        for p_ in rep.get("problems", []):
            print(f"  - {p_}")
        for d in rep.get("drift", []):
            print(f"  * {d['field']}: 记录 {d['recorded']} ≠ 当前 {d['current']}（{d['why']}）")
        rec_ = rep.get("reconcile")
        if rec_ is not None and not rec_.get("ok"):
            for p_ in rec_.get("problems", []):
                print(f"  * 对账: {p_}")
        return 1
    print(f"[replay] OK（run {rep.get('run_id')}, status {rep.get('status')}）"
          f"—— 确定性口径全匹配 + 状态对账一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())