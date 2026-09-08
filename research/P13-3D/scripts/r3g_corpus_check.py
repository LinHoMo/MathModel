#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r3g_corpus_check.py — R3.2 语料完整性门禁 (R3-G2).

版本：v1.1（P13-3D-R3.1 instrument hardening, 2026-09-07）
      v1.0 单元级判定语义冻结不变；v1.1 additive 新增语料级配对唯一性检查。

检查 48 篇真实 Writer 论文：
  1. 存在性（24 单元 × 2 条件）
  2. 篇幅（>= MIN_CHARS）
  3. 10 个必需章节齐全
  4. 无元叙述泄漏
  5. 记录 sha256 / 字符数 / 章节命中
  6. [v1.1] 配对唯一性：非规范/多余文件、同单元 W0/W1 重复、跨单元内容重复

gate = cells_ok AND pairing_ok —— corpus gate 是实验完整性的最后一道门。

Usage:
  python r3g_corpus_check.py            # 检查并打印报告
  python r3g_corpus_check.py --json     # 输出 JSON
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]
R3 = ROOT / "research" / "P13-3D-R3"
PAPERS = R3 / "real_papers"
ARTIFACTS = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
MAPS = R3 / "output" / "maps"
PROMPTS = R3 / "prompts"

QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]
ARMS = ["B0", "MMA", "B1_F"]          # 文件名用下划线
ARM_LABEL = {"B0": "B0", "MMA": "MMA", "B1_F": "B1-F"}

MIN_CHARS = 5000
TARGET_MIN, TARGET_MAX = 6000, 11000

REQUIRED_SECTIONS = [
    ("摘要", [r"摘要"]),
    ("问题重述", [r"问题重述", r"问题重述与背景", r"问题背景"]),
    ("模型假设", [r"模型假设", r"假设"]),
    ("符号说明", [r"符号说明", r"符号表"]),
    ("模型建立与求解", [r"模型建立", r"模型建立与求解", r"模型构建"]),
    ("候选模型对比", [r"候选模型", r"候选模型对比", r"模型对比", r"模型比较"]),
    ("选定模型说明", [r"选定模型", r"选定模型说明", r"模型选择", r"最终模型"]),
    ("灵敏度分析", [r"灵敏度", r"敏感性"]),
    ("模型评价", [r"模型评价", r"模型评估", r"评价与改进"]),
    ("结论", [r"结论"]),
]

LEAK_PATTERNS = [
    r"MODEL_ARTIFACT", r"MODEL_PAPER_MAP", r"结构化映射", r"映射层", r"灵敏度映射",
    r"依据映射", r"按映射", r"映射要求", r"映射，", r"映射的",
    r"模型构件", r"本构件", r"该构件", r"sensitivity_plan",
    r"selected_model", r"candidate_models",
    r"W0", r"W1", r"本实验", r"实验条件", r"对照条件", r"两种条件",
]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_sections(text: str):
    heads = [ln.strip("# ").strip() for ln in text.splitlines() if ln.lstrip().startswith("#")]
    hit, miss = [], []
    for name, pats in REQUIRED_SECTIONS:
        ok = any(re.search(p, h) for h in heads for p in pats)
        (hit if ok else miss).append(name)
    return hit, miss


def check_leak(text: str):
    return [p for p in LEAK_PATTERNS if re.search(p, text)]


CANONICAL_PAPER_RE = re.compile(r"^(.+)_(B0|MMA|B1_F)\.md$")


def check_pairing_integrity():
    """P13-3D-R3.1 hardening（additive，v1.1）：语料级配对唯一性。

    阻断四类缺陷（不改变任何单元级判定语义）：
      A. 同一 (question, arm, writer) 出现多份 paper（非规范命名 / 冗余副本）
      B. 同一 paper 内容被配给多个单元（跨单元内容重复）
      C. 同一单元 W0/W1 字节级重复（配对失效）
      D. 任意不同单元共享完全相同内容 hash
    """
    known_questions = set(QUESTIONS)
    problems = {
        "unexpected_files": [], "missing_canonical": [],
        "same_cell_duplicates": [], "cross_cell_duplicates": [],
    }
    by_hash = {}
    files_scanned = 0
    for cond in ["W0", "W1"]:
        d = PAPERS / cond
        if not d.exists():
            problems["missing_canonical"].append(f"{cond}/<directory missing>")
            continue
        for f in sorted(d.glob("*.md")):
            m = CANONICAL_PAPER_RE.match(f.name)
            if not (m and m.group(1) in known_questions):
                problems["unexpected_files"].append(f"{cond}/{f.name}")
                continue
            files_scanned += 1
            by_hash.setdefault(sha256_file(f), []).append(f"{cond}/{f.name}")
    for qid in QUESTIONS:
        for arm in ARMS:
            for cond in ["W0", "W1"]:
                if not (PAPERS / cond / f"{qid}_{arm}.md").exists():
                    problems["missing_canonical"].append(f"{cond}/{qid}_{arm}.md")
    for h, paths in by_hash.items():
        if len(paths) < 2:
            continue
        conds_by_name = {}
        for p in paths:
            cond, fname = p.split("/", 1)
            conds_by_name.setdefault(fname, []).append(cond)
        for fname in sorted(conds_by_name):
            if len(conds_by_name[fname]) > 1:
                problems["same_cell_duplicates"].append(
                    f"{fname}: {','.join(conds_by_name[fname])}")
        if len(conds_by_name) > 1:
            problems["cross_cell_duplicates"].append(
                {"sha256": h[:16], "paths": sorted(paths)})
    ok = not any(problems.values())
    payload = {"stats": {"files_scanned": files_scanned,
                         "unique_hashes": len(by_hash)}, **problems}
    return ok, payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    report = {"checked_at": datetime.now().isoformat(), "cells": [], "summary": {}}
    n_ok = 0
    deficient = []

    for qid in QUESTIONS:
        for arm in ARMS:
            cell = {
                "problem_id": qid,
                "arm": ARM_LABEL[arm],
                "files": {},
            }
            for cond in ["W0", "W1"]:
                f = PAPERS / cond / f"{qid}_{arm}.md"
                if not f.exists():
                    cell["files"][cond] = {"exists": False}
                    continue
                text = f.read_text(encoding="utf-8")
                hit, miss = check_sections(text)
                leak = check_leak(text)
                entry = {
                    "exists": True,
                    "chars": len(text),
                    "sha256": sha256_file(f),
                    "sections_found": len(hit),
                    "sections_missing": miss,
                    "leak": leak,
                    "mtime": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    "ok": len(text) >= MIN_CHARS and not miss and not leak,
                }
                entry["reason"] = []
                if len(text) < MIN_CHARS:
                    entry["reason"].append(f"too_short({len(text)}<{MIN_CHARS})")
                if miss:
                    entry["reason"].append("missing:" + ",".join(miss))
                if leak:
                    entry["reason"].append("leak:" + ",".join(leak))
                cell["files"][cond] = entry

            both_ok = all(cell["files"].get(c, {}).get("ok") for c in ["W0", "W1"])
            cell["ok"] = both_ok
            if both_ok:
                n_ok += 1
            else:
                deficient.append(f"{qid}/{ARM_LABEL[arm]}")
            report["cells"].append(cell)

    total = len(QUESTIONS) * len(ARMS)
    pairing_ok, pairing = check_pairing_integrity()
    report["pairing_integrity"] = {"ok": pairing_ok, **pairing}
    report["summary"] = {
        "cells_total": total,
        "cells_ok": n_ok,
        "papers_total": total * 2,
        "papers_present": sum(
            1 for c in report["cells"] for k in ("W0", "W1") if c["files"].get(k, {}).get("exists")
        ),
        "deficient_cells": deficient,
        "pairing": "OK" if pairing_ok else "FAIL",
        "gate": "PASS" if (n_ok == total and pairing_ok) else "FAIL",
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print("=" * 72)
    print("R3.2 CORPUS GATE (R3-G2)")
    print("=" * 72)
    for c in report["cells"]:
        line = f"  {c['problem_id']:<8} {c['arm']:<5} "
        for cond in ["W0", "W1"]:
            e = c["files"].get(cond, {})
            if not e.get("exists"):
                line += f"{cond}: MISSING   "
            else:
                flag = "OK " if e["ok"] else "BAD"
                line += f"{cond}: {flag} {e['chars']:>6}c sec={e['sections_found']}/10  "
        print(line)
    print("-" * 72)
    s = report["summary"]
    print(f"  cells ok : {s['cells_ok']}/{s['cells_total']}")
    print(f"  papers   : {s['papers_present']}/{s['papers_total']}")
    p = report["pairing_integrity"]
    print(f"  pairing  : {s['pairing']} (files={p['stats']['files_scanned']}, "
          f"unique_hashes={p['stats']['unique_hashes']})")
    if not p["ok"]:
        for k, v in p.items():
            if k not in ("ok", "stats") and v:
                print(f"  ! {k}: {v}")
    print(f"  GATE     : {s['gate']}")
    if s["deficient_cells"]:
        print(f"  deficient: {', '.join(s['deficient_cells'])}")
    sys.exit(0 if s["gate"] == "PASS" else 1)


if __name__ == "__main__":
    main()
