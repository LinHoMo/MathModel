# -*- coding: utf-8 -*-
"""P15-K004 Experiment Runner（P2-1b）。

执行 ref constructor × 2 RT conditions × 8 problems 的实验矩阵。
LLM-free：ref constructor 是确定性模板，无需 API。

用法：
    cd research/P15/k004
    py -3.12 run_k004.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "research" / "P15" / "vs001_run"))
sys.path.insert(0, str(REPO / "research" / "P15" / "k004"))

PROBLEMS = [
    "2011_B", "2017_B", "2018_A", "2018_B",
    "2019_C", "2020_B", "2022_C", "2024_A",
]

PROBLEM_CARDS_DIR = REPO / "research" / "P15" / "benchmark" / "problem_cards"
OUTPUT_DIR = Path(__file__).parent / "results"


def load_problem(qid: str) -> dict:
    """从 card.yaml 加载问题特征。"""
    import yaml
    card_path = PROBLEM_CARDS_DIR / qid / "card.yaml"
    if not card_path.exists():
        return {"question": qid, "statement": "", "features": {}}
    with open(card_path, encoding="utf-8") as f:
        card = yaml.safe_load(f)
    stmt_path = PROBLEM_CARDS_DIR / qid / "problem_statement.txt"
    statement = ""
    if stmt_path.exists():
        statement = stmt_path.read_text(encoding="utf-8")[:2000]
    return {
        "question": qid,
        "statement": statement or card.get("title", ""),
        "features": {
            "problem_types": card.get("family", []),
            "sub_questions": card.get("sub_questions", []),
            "allowed_structures": card.get("allowed_modeling_structures", []),
            "key_variables": card.get("key_variables", []),
            "key_constraints": card.get("key_constraints", []),
        },
    }


def run_ref_minus_rt(constructor, problem: dict, seed: int) -> dict:
    """ref constructor -RT：产出 bundle 即止，不执行。"""
    bundle = constructor.construct(problem, context=None)
    return {
        "constructor": "ref",
        "runtime": "-RT",
        "problem": problem["question"],
        "seed": seed,
        "model_id": bundle.model_ir.get("model_id", ""),
        "family": bundle.model_ir.get("model_family", {}).get("primary", ""),
        "fidelity_score": None,
        "exec_status": "not_executed",
        "validation_status": "not_validated",
        "bundle_json": bundle.to_json(),
    }


def run_ref_plus_rt(constructor, problem: dict, seed: int,
                    project_dir: Path) -> dict:
    """ref constructor +RT：注入 Runtime 并执行完整 DAG。"""
    from modeling_harness.runtime.execution.session import RuntimeSession
    from modeling_harness.runtime.execution.adapters import LocalPythonAdapter
    from modeling_harness.runtime.constructors.registry import apply_bundle

    bundle = constructor.construct(problem, context=None)
    # Registry assigns Q001, Q002... as artifact_ids. external_model_irs
    # must use the same key. Override bundle.question to match.
    qid = "Q001"
    bundle.question = qid

    adapter = LocalPythonAdapter()
    session = RuntimeSession(
        project_dir=project_dir,
        questions=[qid],
        execution_adapter=adapter,
    )
    apply_bundle(session, bundle, workdir=str(project_dir))

    t0 = time.time()
    report = session.run(save=True)
    elapsed = time.time() - t0

    session.checkpoint()

    # 提取结果
    exec_status = "not_found"
    val_status = "not_found"
    fidelity_score = None
    exec_id = None

    completed_nodes = report.get("progress", {}).get("completed", [])
    if isinstance(completed_nodes, list):
        # completed is a list of node IDs — check which nodes ran
        for nid in completed_nodes:
            if "model_execution" in nid:
                exec_status = "ran"
            if "model_validation" in nid:
                val_status = "ran"

    # 从 registry 提取执行结果
    execs = session.registry.list_by_type("execution_result")
    if execs:
        ex = execs[0]
        exec_status = (ex.data or {}).get("status", "unknown")
        exec_id = ex.artifact_id

    # 从 registry 提取验证结果
    vrs = session.registry.list_by_type("verification_result")
    if vrs:
        vr = vrs[0]
        val_status = (vr.data or {}).get("status", "unknown")

    # 从 registry 提取 fidelity 报告
    fids = [a for a in session.registry.list_by_type("fidelity_report")]
    if fids:
        fidelity_score = (fids[0].data or {}).get("fidelity_score")

    # 提取证据关系
    evidence = []
    for rel in session.graph.relations:
        evidence.append({"from": rel["from"], "relation": rel["relation"], "to": rel["to"]})

    return {
        "constructor": "ref",
        "runtime": "+RT",
        "problem": problem["question"],
        "seed": seed,
        "model_id": bundle.model_ir.get("model_id", ""),
        "family": bundle.model_ir.get("model_family", {}).get("primary", ""),
        "fidelity_score": fidelity_score,
        "exec_status": exec_status,
        "validation_status": val_status,
        "evidence_count": len(evidence),
        "elapsed_s": round(elapsed, 2),
        "report_summary": {
            "completed": len(completed_nodes),
            "failures": list(report.get("progress", {}).get("failures", {}).keys())
                if isinstance(report.get("progress", {}).get("failures", {}), dict)
                else report.get("progress", {}).get("failures", []),
        },
    }


def main():
    from reference_constructor import ReferenceConstructor

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    constructor = ReferenceConstructor()
    results = []

    for qid in PROBLEMS:
        problem = load_problem(qid)
        for seed in [42, 137]:
            # -RT
            r = run_ref_minus_rt(constructor, problem, seed)
            results.append(r)
            print(f"[ref/-RT] {qid} seed={seed} → model={r['model_id']}")

            # +RT
            proj = OUTPUT_DIR / f"ref_RT_{qid}_s{seed}"
            try:
                r = run_ref_plus_rt(constructor, problem, seed, proj)
                results.append(r)
                print(f"[ref/+RT] {qid} seed={seed} → exec={r['exec_status']} "
                      f"val={r['validation_status']} "
                      f"fid={r.get('fidelity_score', '?')} "
                      f"({r.get('elapsed_s', '?')}s)")
            except Exception as e:
                results.append({
                    "constructor": "ref", "runtime": "+RT",
                    "problem": qid, "seed": seed,
                    "exec_status": "error", "error": str(e),
                })
                print(f"[ref/+RT] {qid} seed={seed} → ERROR: {e}")

    # 保存结果
    out_file = OUTPUT_DIR / "k004_ref_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果保存到 {out_file}")
    print(f"总计 {len(results)} runs")

    # 汇总
    rt_results = [r for r in results if r.get("runtime") == "+RT"]
    exec_pass = sum(1 for r in rt_results if r.get("exec_status") == "success")
    val_pass = sum(1 for r in rt_results if r.get("validation_status") == "passed")
    fid_aligned = sum(1 for r in rt_results
                      if r.get("fidelity_score") is not None
                      and r["fidelity_score"] >= 0.8)
    print(f"\n=== ref constructor 汇总 ===")
    print(f"+RT runs: {len(rt_results)}")
    print(f"exec success: {exec_pass}/{len(rt_results)}")
    print(f"val pass: {val_pass}/{len(rt_results)}")
    print(f"fidelity aligned (≥0.8): {fid_aligned}/{len(rt_results)}")


if __name__ == "__main__":
    main()
