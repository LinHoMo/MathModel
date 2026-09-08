#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k001_freeze.py — P15-K001 冻结与漂移校验

用法:
    py -3.12 research/P15/scripts/k001_freeze.py freeze     # 计算并写入 hashes.json
    py -3.12 research/P15/scripts/k001_freeze.py --check    # 校验是否漂移（默认）

冻结项：题面 / 金标准 / 题目卡 / 方法卡 / 案例 / prompt 模板 / 规格 / schema。
任一哈希漂移 → 退出码 1，实验作废重跑（FROZEN 后禁止原地修改）。

零第三方依赖（PyYAML 除外，用于解析规格）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k001_common as K  # noqa: E402

HASHES_PATH = K.FROZEN / "hashes.json"


def collect_targets() -> list:
    """返回需要冻结的全部文件路径（存在性不足会报错）。"""
    files = []

    # 规格与 schema
    for name in ["problem_set.yaml", "knowledge_set.yaml", "sham_set.yaml", "case_set.yaml"]:
        files.append(K.FROZEN / name)
    for p in sorted(K.SCHEMAS.glob("*.json")):
        files.append(p)

    # prompt 模板
    for arm in K.ARMS:
        files.append(K.TEMPLATES / f"{arm}.md")

    # 题面 / 金标准 / 题目卡
    for pid, p in K.problem_index().items():
        for key in ("statement_path", "gt_path", "card_path"):
            files.append(K.ROOT / p[key])

    # 方法卡（目标卡 + sham 卡）
    cards = set()
    for k in K.load_knowledge_set()["knowledge"]:
        cards.add(k["path"])
    for s in K.load_sham_set()["sham"]:
        cards.add(s["path"])
    for c in sorted(cards):
        files.append(K.ROOT / c)

    # 案例资产（structural + solution）
    for layer in ("structural", "solution"):
        for _, relp in K.case_index(layer).items():
            files.append(K.ROOT / relp)

    return files


def compute(files: list) -> dict:
    entries = {}
    missing = []
    for f in files:
        if not f.exists():
            missing.append(K.rel(f))
            continue
        entries[K.rel(f)] = K.sha256_file(f)
    return {
        "experiment_id": K.EXPERIMENT_ID,
        "protocol_version": K.PROTOCOL_VERSION,
        "frozen_at": K.utc_now_iso(),
        "file_count": len(entries),
        "missing": missing,
        "files": entries,
    }


def frozen_root(entries: dict) -> str:
    body = "\n".join(f"{k}  {v}" for k, v in sorted(entries.items()))
    return K.sha256_text(body)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    mode = argv[0] if argv else "--check"

    files = collect_targets()
    report = compute(files)
    report["frozen_root_sha256"] = frozen_root(report["files"])

    if mode == "freeze":
        if report["missing"]:
            print("[FAIL] 以下冻结目标缺失：")
            for m in report["missing"]:
                print("   -", m)
            return 1
        K.write_json(HASHES_PATH, report)
        print(f"[OK] 已冻结 {report['file_count']} 个文件 → {K.rel(HASHES_PATH)}")
        print(f"     frozen_root_sha256 = {report['frozen_root_sha256']}")
        return 0

    # --check
    if not HASHES_PATH.exists():
        print(f"[FAIL] 未找到 hashes.json，请先执行 freeze：{HASHES_PATH}")
        return 1
    old = K.read_json(HASHES_PATH)
    old_files = old.get("files", {})
    new_files = report["files"]

    drift = []
    for path, h in sorted(old_files.items()):
        if path not in new_files:
            drift.append(f"MISSING  {path}")
        elif new_files[path] != h:
            drift.append(f"CHANGED  {path}")
    for path in sorted(new_files):
        if path not in old_files:
            drift.append(f"ADDED    {path}")

    if report["missing"]:
        for m in report["missing"]:
            drift.append(f"MISSING  {m}")

    if drift:
        print(f"[FAIL] 冻结项漂移 {len(drift)} 处（FROZEN 后禁止原地修改）：")
        for d in drift:
            print("   -", d)
        print("\n处理：要么恢复原内容，要么 new revision（P15-K001 v1.1）并使 v1.0 数据作废。")
        return 1

    print(f"[PASS] 冻结校验通过：{report['file_count']} 个文件，无漂移")
    print(f"       frozen_root_sha256 = {report['frozen_root_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
