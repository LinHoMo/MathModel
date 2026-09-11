#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 Q1/Q2 v2 结果与 v1 缺陷审计并入 all_results.json（数值追溯真源）。

为什么需要：L4「数值追溯」门禁要求模型描述文档（*.md）中的每个数字都能在
all_results.json 或题面 inputs/problem.txt 中找到出处。v2 重做后新增的数字
（46.916 / 99.493 / 38.918 m、ρ 上确界 0.5002942、最小最大后悔点 (20°,1200) …
）以及论证「v1 哪里错了」所用的数字（2121.3 m、0.5083 …）都还不是机器产出，
必须各自落盘后才能写进文档——否则文档里的数字就是无源之水。

本脚本只**追加**顶层键，不动既有键（尤其 calibration_sensitivity），
v1 的 problem1/problem2 保留在 v1 命名空间下以维持可追溯。

运行：python projects/cumcm2026b/artifacts/code/build_all_results_v2.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent.parent
ALL = PROJ / "all_results.json"
V2 = HERE.parent / "q1q2_v2_results.json"
VER = HERE.parent / "q1q2_v2_verify.json"
AUD = HERE.parent / "q1q2_v1_audit.json"


def main() -> int:
    for p in (ALL, V2, VER, AUD):
        if not p.exists():
            raise SystemExit(f"missing {p}（请先运行对应脚本）")
    allr = json.loads(ALL.read_text(encoding="utf-8"))
    v2 = json.loads(V2.read_text(encoding="utf-8"))
    ver = json.loads(VER.read_text(encoding="utf-8"))
    aud = json.loads(AUD.read_text(encoding="utf-8"))

    # v1 结果移入 v1 命名空间（保留可追溯，不再充当 Q1/Q2 的当前答案）
    if "problem1" in allr and "problem1_v1" not in allr:
        allr["problem1_v1"] = allr.pop("problem1")
    if "problem2" in allr and "problem2_v1" not in allr:
        allr["problem2_v1"] = allr.pop("problem2")

    allr["problem1_v2"] = {
        "cases": v2["problem1"]["cases"],
        "counterexample": v2["problem1"]["counterexample"],
    }
    allr["problem2_v2"] = v2["problem2"]
    allr["v1_defect_audit"] = aud
    allr["v2_selfcheck"] = {
        "n_checks": ver["n_checks"],
        "n_failed": ver["n_failed"],
        "passed": ver["passed"],
        "target_sha256": ver["target"]["sha256"],
        "failed_ids": ver["failed_ids"],
    }
    allr["revision_note"] = (
        "problem1_v2/problem2_v2 为重建结果（算例保证可行、反例正向生成、"
        "目标 E[D]、场景集含 r_rec 假设）；problem1_v1/problem2_v1 保留备查。"
    )
    ALL.write_text(json.dumps(allr, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"updated -> {ALL}")
    print("  top-level keys:", list(allr.keys()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
