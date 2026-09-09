#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k002_freeze.py — P15-K002 冻结与漂移校验

用法:
    py -3.12 research/P15/scripts/k002_freeze.py freeze     # 计算并写入 hashes.json
    py -3.12 research/P15/scripts/k002_freeze.py --check    # 校验是否漂移（默认）

冻结项（PREREGISTERED/FROZEN 后锁定，任一漂移 → 实验作废重跑）：
  * prompt 模板 F/S/SV
  * 8 道题题面 / gt.json / card.yaml（Input Authenticity 已 verified）
  * catalog/model_families.yaml 词表（G3）
  * P15-K002-DRAFT.md / P15-K002-GATES.md（预注册与 Gate 证据）
  * run_order.json（FROZEN 阶段生成后锁定）
  * schemas（experiment_manifest / score_vector / case_asset，若有）

零第三方依赖（PyYAML 除外）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k002_common as K  # noqa: E402

HASHES_PATH = K.FROZEN / "hashes.json"

# 追加冻结项（相对仓库根）
EXTRA_FILES = [
    "research/P15/protocol/preregistration/P15-K002-DRAFT.md",
    "research/P15/protocol/preregistration/P15-K002-GATES.md",
    "research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md",  # v1.1 评分标准（K002 全程使用）
    "core/schemas/v3/model/model_ir.schema.json",  # MODEL_IR 契约真源（P1 C1 迁移，K002 模板对齐版）
    "catalog/model_families.yaml",
    "core/knowledge/methods/cards/mc-dp.yaml",
    "core/knowledge/methods/cards/mc-numerical-pde.yaml",
    "core/knowledge/methods/cards/mc-queuing-theory.yaml",
    "core/schemas/v3/knowledge/method_card.schema.json",
]


def collect_targets() -> list:
    files = []

    # prompt 模板（F/S/SV 三臂）
    for arm in K.ARMS:
        files.append(K.TEMPLATES / f"{arm}.md")

    # 8 道题题面 / gt / card
    for pid in K.PRIMARY_BLOCKS + K.GENERALIZATION_BLOCKS:
        for key in ("problem_statement.txt", "gt.json", "card.yaml"):
            files.append(K.PROBLEM_CARDS / pid / key)

    # run_order（FROZEN 阶段生成后存在；未生成时跳过，不报错）
    ro = K.FROZEN / "run_order.json"
    if ro.exists():
        files.append(ro)

    # schemas（若存在）
    for p in sorted(K.SCHEMAS.glob("*.json")):
        files.append(p)

    # 追加冻结项
    for relp in EXTRA_FILES:
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
        print("\n处理：要么恢复原内容，要么 new revision（P15-K002 v1.1）并使 v1.0 数据作废。")
        return 1

    print(f"[PASS] 冻结校验通过：{report['file_count']} 个文件，无漂移")
    print(f"       frozen_root_sha256 = {report['frozen_root_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
