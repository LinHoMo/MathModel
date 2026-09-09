#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k002_gen_bundles.py — 生成 P15-K002 输入 bundle + 执行顺序 + 盲评映射

三臂 F（free text）/ S（MODEL_IR 18 字段）/ SV（MODEL_IR + validation_plan）。
无知识/无 Sham 注入；指令长度对齐 <10%（F 臂追加等长引导句）。

产出：
    protocol/frozen_specs_k002/run_order.json     执行顺序（seed=42 shuffle，禁止改序）
    experiments/P15-K002/key/condition_map.json   盲评映射（严禁出现在盲评包中）
    experiments/P15-K002/bundles/<sid>.md         生成侧唯一输入
    experiments/P15-K002/runs/<sid>/manifest.json （status=PENDING）

规模：主检验 6 题 × 3 臂 × 5 rep = 90；泛化 2 题 × 3 臂 × 3 rep = 18；合计 108。

用法:
    py -3.12 research/P15/scripts/k002_gen_bundles.py [--dry-run]

零第三方依赖（PyYAML 除外）。
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k002_common as K  # noqa: E402

SEED = 42


def load_problem_spec() -> dict:
    """从 benchmark problem_cards 构建题集规格（不依赖未冻结的 frozen_specs）。"""
    problems = []
    for pid in K.PRIMARY_BLOCKS + K.GENERALIZATION_BLOCKS:
        card = K.PROBLEM_CARDS / pid / "card.yaml"
        if not card.exists():
            raise FileNotFoundError(f"problem card missing: {card}")
        gt_path = K.PROBLEM_CARDS / pid / "gt.json"
        if not gt_path.exists():
            raise FileNotFoundError(f"gt missing: {gt_path}")
        stmt = K.PROBLEM_CARDS / pid / "problem_statement.txt"
        if not stmt.exists():
            raise FileNotFoundError(f"statement missing: {stmt}")
        gt = K.read_json(gt_path)
        allowed = gt.get("allowed_modeling_structures") or []
        problems.append({
            "problem_id": pid,
            "block_role": "main" if pid in K.PRIMARY_BLOCKS else "generalization",
            "statement_path": K.rel(stmt),
            "statement_sha256": K.sha256_file(stmt),
            "sub_questions": gt["sub_questions"],
            "allowed_modeling_structures": allowed,
        })
    return {"problems": problems}


def build_rows() -> list:
    spec = load_problem_spec()
    pidx = {p["problem_id"]: p for p in spec["problems"]}
    rng = random.Random(SEED)
    rows = []
    seq = 0
    for pid in K.PRIMARY_BLOCKS + K.GENERALIZATION_BLOCKS:
        p = pidx[pid]
        role = p["block_role"]
        reps = K.REPLICATES_PRIMARY if role == "main" else K.REPLICATES_GENERALIZATION
        for rep in range(1, reps + 1):
            arms = list(K.ARMS)
            rng.shuffle(arms)                      # 每个 (problem, rep) 内随机化顺序
            for pos, arm in enumerate(arms):
                seq += 1
                rows.append({
                    "seq": seq,
                    "submission_id": K.deterministic_uuid4(rng),
                    "problem_id": pid,
                    "block_role": role,
                    "arm": arm,
                    "rep": rep,
                    "seed": K.SEEDS[rep - 1],
                    "sequence_in_block": pos,
                    "batch": batch_of(pid, rep, role),
                    "sub_questions": p["sub_questions"],
                    "allowed_modeling_structures": p["allowed_modeling_structures"],
                })
    return rows


def batch_of(problem_id: str, rep: int, block_role: str) -> str:
    if block_role == "generalization":
        return "batch6"
    if rep == 1:
        return {"2020_B": "batch0",
                "2018_A": "batch1", "2019_C": "batch1",
                "2018_B": "batch1", "2017_B": "batch1", "2011_B": "batch1"}[problem_id]
    return {2: "batch2", 3: "batch3", 4: "batch4", 5: "batch5"}[rep]


def render_bundle(row: dict, problem: dict) -> str:
    tpl = (K.TEMPLATES / f"{row['arm']}.md").read_text(encoding="utf-8")
    statement = (K.ROOT / problem["statement_path"]).read_text(encoding="utf-8").strip()
    out = tpl
    out = out.replace("{{SUBMISSION_ID}}", row["submission_id"])
    out = out.replace("{{PROBLEM_ID}}", row["problem_id"])
    out = out.replace("{{SUB_QUESTIONS}}", "、".join(problem["sub_questions"]))
    out = out.replace("{{ALLOWED_STRUCTURES}}",
                      "、".join(problem["allowed_modeling_structures"]))
    out = out.replace("{{PROBLEM_STATEMENT}}", statement)
    out = out.replace("{{SEED}}", str(row["seed"]))
    return out


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    precheck = "--precheck" in sys.argv
    spec = load_problem_spec()
    pidx = {p["problem_id"]: p for p in spec["problems"]}

    for arm in K.ARMS:
        tpl = K.TEMPLATES / f"{arm}.md"
        if not tpl.exists():
            print(f"[FAIL] prompt 模板缺失：{tpl}")
            return 1

    if precheck:
        return precheck_main(pidx)

    rows = build_rows()
    if dry_run:
        from collections import Counter
        print(f"[dry-run] {len(rows)} runs 将生成")
        print("  臂分布:", dict(Counter(r["arm"] for r in rows)))
        print("  题分布:", dict(Counter(r["problem_id"] for r in rows)))
        return 0

    K.EXP.mkdir(parents=True, exist_ok=True)
    K.KEY.mkdir(parents=True, exist_ok=True)
    K.BUNDLES.mkdir(parents=True, exist_ok=True)
    K.RUNS.mkdir(parents=True, exist_ok=True)
    K.FROZEN.mkdir(parents=True, exist_ok=True)

    condition_map = {"experiment_id": K.EXPERIMENT_ID,
                     "protocol_version": K.PROTOCOL_VERSION,
                     "warning": "分组明细严禁进入盲评包/报告附录",
                     "map": {}}
    run_order = {"seed": SEED, "runs": []}

    for row in rows:
        problem = pidx[row["problem_id"]]
        bundle = render_bundle(row, problem)
        sid = row["submission_id"]
        (K.BUNDLES / f"{sid}.md").write_text(bundle, encoding="utf-8")
        manifest = {
            "submission_id": sid, "problem_id": row["problem_id"],
            "arm": row["arm"], "rep": row["rep"], "seed": row["seed"],
            "batch": row["batch"], "block_role": row["block_role"],
            "status": "PENDING", "created_at": K.utc_now_iso(),
            "bundle_sha256": K.sha256_text(bundle),
            "statement_sha256": problem["statement_sha256"],
        }
        run_dir = K.RUNS / sid
        run_dir.mkdir(parents=True, exist_ok=True)
        K.write_json(run_dir / "manifest.json", manifest)
        condition_map["map"][sid] = {"problem_id": row["problem_id"],
                                     "arm": row["arm"], "rep": row["rep"]}
        run_order["runs"].append({"seq": row["seq"], "submission_id": sid})

    K.write_json(K.KEY / "condition_map.json", condition_map)
    K.write_json(K.FROZEN / "run_order.json", run_order)

    # 状态机：PENDING 计数
    from collections import Counter
    print(f"[OK] {len(rows)} bundles + manifests 生成")
    print("  臂分布:", dict(Counter(r["arm"] for r in rows)))
    print("  condition_map 已写入 key/（严禁外泄）")
    print("  run_order 已写入 frozen_specs_k002/")
    return 0


def precheck_main(pidx: dict) -> int:
    """题目区分度预检：主检验 6 题 × F/S 臂 × 1 rep = 12 runs。

    产出到 research/P15/experiments/P15-K002-precheck/（不污染正式实验目录）。
    """
    from collections import Counter
    pre = K.EXP.parent / "P15-K002-precheck"
    bundles_dir = pre / "bundles"
    runs_dir = pre / "runs"
    bundles_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)
    rows = []
    seq = 0
    for pid in K.PRIMARY_BLOCKS:
        problem = pidx[pid]
        arms = ["F", "S"]
        rng.shuffle(arms)
        for pos, arm in enumerate(arms):
            seq += 1
            rows.append({
                "seq": seq, "problem_id": pid, "arm": arm, "rep": 1,
                "seed": K.SEEDS[0], "sequence_in_block": pos,
                "submission_id": K.deterministic_uuid4(rng),
                "sub_questions": problem["sub_questions"],
                "allowed_modeling_structures": problem["allowed_modeling_structures"],
            })

    condition_map = {"experiment_id": K.EXPERIMENT_ID, "phase": "PRECHECK",
                     "warning": "分组明细严禁外泄", "map": {}}
    for row in rows:
        problem = pidx[row["problem_id"]]
        bundle = render_bundle(row, problem)
        sid = row["submission_id"]
        (bundles_dir / f"{sid}.md").write_text(bundle, encoding="utf-8")
        K.write_json(runs_dir / sid / "manifest.json", {
            "submission_id": sid, "problem_id": row["problem_id"],
            "arm": row["arm"], "rep": 1, "seed": row["seed"], "batch": "precheck",
            "block_role": "main", "status": "PENDING",
            "statement_sha256": problem["statement_sha256"],
            "bundle_sha256": K.sha256_text(bundle),
        })
        condition_map["map"][sid] = {"problem_id": row["problem_id"], "arm": row["arm"]}

    K.write_json(pre / "key" / "condition_map.json", condition_map)
    print(f"[OK] precheck {len(rows)} bundles → {K.rel(bundles_dir)}")
    print("  分布:", dict(Counter(r["arm"] for r in rows)),
          dict(Counter(r["problem_id"] for r in rows)))
    print("  注意：区分度判定依据 = 条件内方差与条件间差异（见 DRAFT §3.5）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
