#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k001_gen_bundles.py — 生成 P15-K001 的 55 个输入 bundle + 执行顺序 + 盲评映射

产出：
    protocol/frozen_specs/run_order.json        执行顺序（seed=42 shuffle，禁止改序）
    experiments/P15-K001/key/condition_map.json 盲评映射（严禁出现在盲评包中）
    experiments/P15-K001/bundles/<sid>.md       生成侧唯一输入
    experiments/P15-K001/runs/<sid>/manifest.json  （status=PENDING）

随机化：对每个 (problem, rep) 内的 5 个条件做 shuffle，削弱顺序/漂移效应。
submission_id 用受控随机源生成的 UUID4（可重放，但对盲评者无信息）。

用法:
    py -3.12 research/P15/scripts/k001_gen_bundles.py
    py -3.12 research/P15/scripts/k001_gen_bundles.py --dry-run

退出码：0 = 正常；1 = 冻结/前置检查失败。
零第三方依赖（PyYAML 除外）。
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k001_common as K  # noqa: E402

SEED = 42


def batch_of(problem_id: str, rep: int, block_role: str) -> str:
    if block_role == "generalization":
        return "batch4"
    if rep == 1:
        return {"2020_B": "batch0", "2018_A": "batch1", "2019_C": "batch1"}[problem_id]
    return {2: "batch2", 3: "batch3"}[rep]


def build_rows() -> list:
    ps = K.load_problem_set()
    pidx = K.problem_index()
    kidx = K.knowledge_index()
    sidx = K.sham_index()
    cidx = K.case_index("structural")

    rng = random.Random(SEED)
    rows = []
    seq = 0

    for pid in ps["primary_blocks"] + ps["generalization_blocks"]:
        p = pidx[pid]
        role = p["block_role"]
        reps = ps["replicates_primary"] if role == "main" else ps["replicates_generalization"]
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
                    "knowledge": K.ARM_SPEC[arm]["knowledge"],
                    "case": K.ARM_SPEC[arm]["case"],
                    "rep": rep,
                    "seed": ps["seeds"][rep - 1],
                    "sequence_in_block": pos,
                    "batch": batch_of(pid, rep, role),
                    "_knowledge_card": kidx[pid]["card_ids"][0] if K.ARM_SPEC[arm]["knowledge"] == "relevant" else None,
                    "_sham_card": sidx[pid]["sham_card"] if K.ARM_SPEC[arm]["knowledge"] == "sham" else None,
                    "_case_path": cidx[pid] if K.ARM_SPEC[arm]["case"] == "structural" else None,
                })
    return rows


def render_bundle(row: dict, problem: dict) -> str:
    arm = row["arm"]
    tpl = (K.TEMPLATES / f"{arm}.md").read_text(encoding="utf-8")
    statement = (K.ROOT / problem["statement_path"]).read_text(encoding="utf-8").strip()
    problem_sha = K.sha256_file(K.ROOT / problem["statement_path"])

    knowledge_text = ""
    if row["_knowledge_card"]:
        card_path = K.ROOT / "src/modeling_harness/knowledge/methods/cards" / f"{row['_knowledge_card']}.yaml"
        knowledge_text = card_path.read_text(encoding="utf-8").strip()
    elif row["_sham_card"]:
        card_path = K.ROOT / "src/modeling_harness/knowledge/methods/cards" / f"{row['_sham_card']}.yaml"
        knowledge_text = card_path.read_text(encoding="utf-8").strip()

    case_text = ""
    if row["_case_path"]:
        case_text = (K.ROOT / row["_case_path"]).read_text(encoding="utf-8").strip()

    out = tpl
    out = out.replace("{{SUBMISSION_ID}}", row["submission_id"])
    out = out.replace("{{PROBLEM_ID}}", row["problem_id"])
    out = out.replace("{{SEED}}", str(row["seed"]))
    out = out.replace("{{PROBLEM_STATEMENT}}", statement)
    out = out.replace("{{PROBLEM_SHA256}}", problem_sha)
    out = out.replace("{{REFERENCE_CONTENT_KNOWLEDGE}}", knowledge_text)
    out = out.replace("{{REFERENCE_CONTENT_CASE}}", case_text)
    out = out.replace("{{REFERENCE_CONTENT}}", knowledge_text or case_text)
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    dry = "--dry-run" in argv

    hashes_path = K.FROZEN / "hashes.json"
    if not hashes_path.exists():
        print("[FAIL] 未找到 hashes.json，请先运行 k001_freeze.py freeze")
        return 1

    pidx = K.problem_index()
    rows = build_rows()

    print(f"[INFO] 生成 {len(rows)} 个 run：")
    by_batch = {}
    for r in rows:
        by_batch.setdefault(r["batch"], []).append(r)
    for b in sorted(by_batch):
        print(f"        {b}: {len(by_batch[b])} runs")

    if dry:
        print("\n[dry-run] 前 8 行执行顺序：")
        for r in rows[:8]:
            print(f"   {r['seq']:>3}  {r['batch']}  {r['problem_id']}  arm {r['arm']}  rep {r['rep']}  seed {r['seed']}")
        return 0

    order = {
        "experiment_id": K.EXPERIMENT_ID,
        "protocol_version": K.PROTOCOL_VERSION,
        "randomization_seed": SEED,
        "generated_at": K.utc_now_iso(),
        "note": "严格按 seq 顺序执行；禁止按 A→B→C→D→E 固定顺序跑。",
        "rows": [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows],
    }
    K.write_json(K.FROZEN / "run_order.json", order)

    cond_map = {
        "experiment_id": K.EXPERIMENT_ID,
        "protocol_version": K.PROTOCOL_VERSION,
        "warning": "本文件是盲评密钥。禁止以任何形式出现在盲评包、bundle 文件名或报告附录之外的地方；ANALYSIS 阶段才可解封。",
        "map": {
            r["submission_id"]: {
                "problem_id": r["problem_id"],
                "block_role": r["block_role"],
                "arm": r["arm"],
                "knowledge": r["knowledge"],
                "case": r["case"],
                "rep": r["rep"],
                "seed": r["seed"],
                "batch": r["batch"],
            }
            for r in rows
        },
    }
    K.write_json(K.KEY / "condition_map.json", cond_map)

    for r in rows:
        problem = pidx[r["problem_id"]]
        bundle = render_bundle(r, problem)
        bpath = K.BUNDLES / f"{r['submission_id']}.md"
        bpath.parent.mkdir(parents=True, exist_ok=True)
        bpath.write_text(bundle, encoding="utf-8")

        ref_chars = len(bundle.split("<!-- BEGIN REFERENCE")[1].split("<!-- END REFERENCE -->")[0]) \
            if "<!-- BEGIN REFERENCE" in bundle else 0

        manifest = {
            "experiment_id": K.EXPERIMENT_ID,
            "protocol_version": K.PROTOCOL_VERSION,
            "submission_id": r["submission_id"],
            "problem_id": r["problem_id"],
            "block_role": r["block_role"],
            "condition": {"arm": r["arm"], "knowledge": r["knowledge"], "case": r["case"]},
            "knowledge": {
                "card_ids": [r["_knowledge_card"] or r["_sham_card"]] if (r["_knowledge_card"] or r["_sham_card"]) else [],
                "role": r["knowledge"],
                "card_sha256": {},
            },
            "case": {
                "path": r["_case_path"],
                "case_type": r["case"],
                "sha256": K.sha256_file(K.ROOT / r["_case_path"]) if r["_case_path"] else None,
            },
            "rep": r["rep"],
            "seed": r["seed"],
            "generator": {"agent_identity": "claude", "model_version": "PENDING", "provider": "PENDING"},
            "hashes": {
                "problem_sha256": K.sha256_file(K.ROOT / problem["statement_path"]),
                "prompt_sha256": K.sha256_file(K.TEMPLATES / f"{r['arm']}.md"),
                "bundle_sha256": K.sha256_text(bundle),
                "run_order_sha256": None,   # 顺序表写完后回填
            },
            "artifact_schema_version": K.ARTIFACT_SCHEMA_VERSION,
            "knowledge_trace": {"retrieved": [], "considered": [], "used": [], "adapted": [], "rejected": []},
            "cost": {"prompt_tokens": None, "completion_tokens": None, "latency_seconds": None},
            "reference_chars": ref_chars,
            "bundle_chars": len(bundle),
            "batch": r["batch"],
            "sequence_in_block": r["sequence_in_block"],
            "created_at": None,
            "status": "PENDING",
        }
        K.write_json(K.RUNS / r["submission_id"] / "manifest.json", manifest)

    # run_order_sha256 回填（顺序表写完后再算）
    ro_sha = K.sha256_file(K.FROZEN / "run_order.json")
    for r in rows:
        mp = K.RUNS / r["submission_id"] / "manifest.json"
        m = K.read_json(mp)
        m["hashes"]["run_order_sha256"] = ro_sha
        K.write_json(mp, m)

    print(f"\n[OK] bundles  → {K.rel(K.BUNDLES)}  ({len(rows)} 份)")
    print(f"[OK] run_order → {K.rel(K.FROZEN / 'run_order.json')}")
    print(f"[OK] 盲评密钥 → {K.rel(K.KEY / 'condition_map.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
