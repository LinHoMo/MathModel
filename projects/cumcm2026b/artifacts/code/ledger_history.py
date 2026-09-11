#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ledger_history.py —— 把历史轮次的产物数字收进当前台账，供正文的「历史值」追溯。

问题（结构性的）：`all_results.json` 只保存**最新一轮**的产物，而模型描述文档的正文会
累积历次实验的数字（改前/改后、被替代的候选、早期版本的指标…）。任一次重跑都会把旧值
覆盖掉，于是正文里的历史数字成了孤儿——不是伪造，但**无法从工作区台账追溯**。

修法：把 `projects/cumcm2026b/all_results.json` 在 git 历史里的**每一个版本**都读出来，
收割其全部数值，写进当前台账的 `historical_values` 段。每个历史数字因此都能指到
"某次提交里的某个产物"——这才是真实的 provenance（机器抽取，不手敲）。

运行：``py -3.12 -X utf8 -m ledger_history``
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent          # …/projects/cumcm2026b/artifacts/code
REPO = HERE.parents[3]                          # 仓库根
REL = "projects/cumcm2026b/all_results.json"


def _collect(obj, out: set) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            _collect(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect(v, out)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.add(float(obj))


def harvest() -> dict:
    """遍历该文件在 git 历史中的所有版本，收割全部数值。"""
    revs = subprocess.run(
        ["git", "log", "--format=%H", "--", REL],
        cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    values: set = set()
    versions = 0
    for rev in revs:
        blob = subprocess.run(
            ["git", "show", f"{rev}:{REL}"],
            cwd=REPO, capture_output=True, text=True
        )
        if blob.returncode != 0:
            continue
        try:
            _collect(json.loads(blob.stdout), values)
        except Exception:
            continue
        versions += 1
    # 当前工作区版本也要在（可能尚未提交）
    try:
        _collect(json.loads((REPO / REL).read_text(encoding="utf-8")), values)
    except Exception:
        pass
    return {"source": REL, "versions_scanned": versions,
            "n_values": len(values),
            "note": "历史轮次的产物数字（含被后续重跑覆盖的值），供正文历史值追溯",
            "values": sorted(values)}


def main() -> int:
    rep = harvest()
    allres = REPO / REL
    data = json.loads(allres.read_text(encoding="utf-8"))
    data["historical_values"] = rep
    allres.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"[OK] 扫描 {rep['versions_scanned']} 个历史版本，"
          f"收割 {rep['n_values']} 个数值 → 并入 {allres.name} 的 historical_values 段")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
