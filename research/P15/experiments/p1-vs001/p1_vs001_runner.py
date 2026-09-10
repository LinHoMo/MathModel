#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1-VS-001 Executable Model Construction Loop — Runner.

驱动 M0/M1/M2 闭环，使用 core 现有原语（registry/evidence_graph/codegen/
adapters/validation/replay），core 只做登记/执行/校验/谱系，不做 LLM 调用。

用法:
    py -3.12 p1_vs001_runner.py --stage m0
    py -3.12 p1_vs001_runner.py --stage m1
    py -3.12 p1_vs001_runner.py --stage m2
    py -3.12 p1_vs001_runner.py --stage replay --exec-id EXEC001
    py -3.12 p1_vs001_runner.py --stage all   (M0+M1+M2+replay)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from modeling_harness.runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402
from modeling_harness.runtime.execution.codegen import register_code, execute_code  # noqa: E402
from modeling_harness.runtime.execution.validation import validate_execution  # noqa: E402
from modeling_harness.runtime.execution.replay import replay_execution  # noqa: E402

EXP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = EXP_DIR / "project"


# ---------------------------------------------------------------- helpers

def _load_registry() -> ArtifactRegistry:
    reg = ArtifactRegistry(PROJECT_DIR / "state" / "registry.json")
    if reg.path.exists():
        reg.load()
    return reg


def _load_graph(reg: ArtifactRegistry) -> EvidenceGraph:
    g = EvidenceGraph(reg, PROJECT_DIR / "state" / "evidence_graph.json")
    return g


def _save(reg, g):
    reg.save()
    g.save()


def register_problem(reg, g, title, text):
    art = reg.create("problem", title=title,
                     data={"text": text}, activate=True,
                     created_by="p1-vs001")
    _save(reg, g)
    return art.artifact_id


def register_question(reg, g, problem_id, desc):
    art = reg.create("question", title=desc,
                     data={"description": desc}, activate=True,
                     created_by="p1-vs001")
    g.add_relation(problem_id, "motivates", art.artifact_id)
    _save(reg, g)
    return art.artifact_id


def register_model_ir(reg, g, question_id, mir_dict, version_label):
    """登记 MODEL_IR（MIR 类型）+ 关联 model artifact（M 类型）。"""
    family = (mir_dict.get("computational", {})
              .get("solver", {}).get("family", "unknown"))
    mir_art = reg.create(
        "model_ir", title=f"MODEL_IR {version_label}",
        question=question_id, data=mir_dict, activate=True,
        created_by="external_model_constructor",
        provenance={"stage": version_label, "source": "external_constructor"})
    model_art = reg.create(
        "model", title=f"Model {version_label}",
        question=question_id,
        data={"model_ir_id": mir_art.artifact_id,
              "model_family": family,
              "version": version_label},
        activate=True, created_by="external_model_constructor")
    g.add_relation(question_id, "solved_by", model_art.artifact_id)
    _save(reg, g)
    return mir_art.artifact_id, model_art.artifact_id


def register_code_and_execute(reg, g, model_id, code, inputs,
                              output_mapping=None, question_id=None):
    """登记 CODE → implemented_by 边 → 真实执行 → EXEC artifact。"""
    code_art = register_code(
        PROJECT_DIR, code, language="python",
        model_id=model_id, output_mapping=output_mapping or {},
        created_by="external_model_constructor", question=question_id)
    # register_code 已保存 registry；重新加载以保持同步
    reg = _load_registry()
    g = _load_graph(reg)
    g.add_relation(model_id, "implemented_by", code_art.artifact_id)
    _save(reg, g)

    exec_art = execute_code(
        PROJECT_DIR, code_art.artifact_id, inputs=inputs,
        question=question_id, created_by="p1-vs001")
    reg = _load_registry()
    g = _load_graph(reg)
    # code → execution_result 谱系边（derived_from 允许任意类型）
    g.add_relation(exec_art.artifact_id, "derived_from", code_art.artifact_id)
    _save(reg, g)
    return reg, g, code_art.artifact_id, exec_art.artifact_id


def run_validation(reg, g, exec_id, checks):
    """对 execution_result 跑确定性校验 → VR artifact + verified_by 边。"""
    vr = validate_execution(PROJECT_DIR, exec_id, checks,
                            provenance={"engine": "p1-vs001.validation",
                                        "check_count": len(checks)})
    reg = _load_registry()
    g = _load_graph(reg)
    return reg, g, vr


def register_revision(reg, g, old_mir_id, new_mir_id, old_model_id,
                      new_model_id, revision_request):
    """登记修订谱系：revision_of + supersedes 边 + registry supersede。"""
    g.add_relation(new_mir_id, "revision_of", old_mir_id)
    g.add_relation(new_mir_id, "supersedes", old_mir_id)
    reg.supersede(old_mir_id, reason="validation failed → revised",
                  replacement=new_mir_id, by="p1-vs001")
    reg.supersede(old_model_id, reason="validation failed → revised",
                  replacement=new_model_id, by="p1-vs001")
    # 保存 revision_request 为 provenance 记录
    rev_art = reg.create(
        "decision", title="Revision Request",
        data=revision_request, activate=True,
        created_by="p1-vs001",
        provenance={"revision_of": old_mir_id, "supersedes_to": new_mir_id})
    _save(reg, g)
    return rev_art.artifact_id


def do_replay(exec_id):
    """重放指定 execution_result，返回偏差报告。"""
    return replay_execution(PROJECT_DIR, exec_id)


# ---------------------------------------------------------------- stages

def stage_m0():
    """M0: 手写 LP 三层 MODEL_IR + 代码，跑通最小契约。"""
    print("=" * 60)
    print("M0 — Executable Model Contract (hand-written LP)")
    print("=" * 60)
    reg = _load_registry()
    g = _load_graph(reg)

    # 1. Problem
    problem_id = register_problem(
        reg, g, "M0 工厂生产计划 LP",
        "工厂生产A、B两种产品，受机器工时和人工工时约束，求利润最大化。")
    print(f"  Problem: {problem_id}")

    # 2. Question
    q_id = register_question(reg, g, problem_id, "求最优生产计划")
    print(f"  Question: {q_id}")

    # 3. MODEL_IR
    mir = json.loads((EXP_DIR / "m0" / "model_ir.json").read_text("utf-8"))
    mir_id, model_id = register_model_ir(reg, g, q_id, mir, "M0-v1")
    print(f"  MODEL_IR: {mir_id}, Model: {model_id}")

    # 4. Code + Execute
    code = (EXP_DIR / "m0" / "run_model.py").read_text("utf-8")
    inputs = {"parameters": mir["semantic"]["parameters"]}
    # 把 parameters 从 {name: {value,...}} 展平为 {name: value}
    flat_params = {k: v["value"] for k, v in inputs["parameters"].items()}
    inputs = {"parameters": flat_params}
    output_mapping = {
        "x_A": "x_A", "x_B": "x_B",
        "objective_value": "objective_value",
        "constraint_violation_max": "constraint_violation_max",
    }
    reg, g, code_id, exec_id = register_code_and_execute(
        reg, g, model_id, code, inputs, output_mapping, q_id)
    print(f"  Code: {code_id}, Execution: {exec_id}")

    # 5. Validation
    checks = [
        {"name": "x_A_exists", "kind": "output_field_exists", "path": "x_A"},
        {"name": "x_B_exists", "kind": "output_field_exists", "path": "x_B"},
        {"name": "obj_numeric", "kind": "output_numeric", "path": "objective_value"},
        {"name": "obj_positive", "kind": "output_range",
         "path": "objective_value", "min": 0},
        {"name": "constraint_violation_zero", "kind": "output_range",
         "path": "constraint_violation_max", "min": 0, "max": 1e-6},
        {"name": "solver_optimal", "kind": "output_equals",
         "path": "solver_status", "expect": "optimal"},
    ]
    reg, g, vr = run_validation(reg, g, exec_id, checks)
    print(f"  Validation: {vr.verification_id} status={vr.status}")

    # 打印执行结果数值
    exec_art = reg.get(exec_id)
    outputs = (exec_art.data or {}).get("outputs", {})
    print(f"  Outputs: objective={outputs.get('objective_value')}, "
          f"x_A={outputs.get('x_A')}, x_B={outputs.get('x_B')}, "
          f"max_violation={outputs.get('constraint_violation_max')}")

    result = {
        "stage": "m0",
        "problem_id": problem_id, "question_id": q_id,
        "model_ir_id": mir_id, "model_id": model_id,
        "code_id": code_id, "execution_id": exec_id,
        "validation_id": vr.verification_id,
        "validation_status": vr.status,
        "outputs": outputs,
    }
    (EXP_DIR / "m0" / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
    print(f"  M0 result saved to m0/result.json")
    return result


def stage_m1():
    """M1: 2019_C Q1 排队模型 v1（故意有错误约束），执行→Validation FAIL。"""
    print("=" * 60)
    print("M1 — One Real Problem: 2019_C Q1 (M/M/c queue, v1 = flawed)")
    print("=" * 60)
    reg = _load_registry()
    g = _load_graph(reg)

    # 1. Problem（2019_C）
    problem_text = (REPO / "research/P15/benchmark/problem_cards/2019_C"
                    / "problem_statement.txt").read_text("utf-8")
    problem_id = register_problem(reg, g, "2019_C 机场出租车问题", problem_text)
    print(f"  Problem: {problem_id}")

    # 2. Question Q1
    q_id = register_question(
        reg, g, problem_id,
        "建立机场出租车排队模型（M/M/c），分析平均等待时间与队列长度")
    print(f"  Question: {q_id}")

    # 3. MODEL_IR v1（由外部 Model Constructor 产出，故意错误）
    mir = json.loads((EXP_DIR / "m1" / "model_ir_v1.json").read_text("utf-8"))
    mir_id, model_id = register_model_ir(reg, g, q_id, mir, "M1-v1")
    print(f"  MODEL_IR v1: {mir_id}, Model: {model_id}")

    # 4. Code + Execute
    code = (EXP_DIR / "m1" / "run_model_v1.py").read_text("utf-8")
    inputs = {"parameters": mir["semantic"]["parameters"]}
    flat_params = {k: v["value"] for k, v in inputs["parameters"].items()}
    inputs = {"parameters": flat_params}
    output_mapping = {
        "avg_waiting_time": "avg_waiting_time",
        "avg_queue_length": "avg_queue_length",
        "server_utilization": "server_utilization",
        "probability_wait": "probability_wait",
        "constraint_violation_max": "constraint_violation_max",
    }
    reg, g, code_id, exec_id = register_code_and_execute(
        reg, g, model_id, code, inputs, output_mapping, q_id)
    print(f"  Code: {code_id}, Execution: {exec_id}")

    # 5. Validation（基于真实数值判 FAIL）
    checks = [
        {"name": "wait_time_exists", "kind": "output_field_exists",
         "path": "avg_waiting_time"},
        {"name": "wait_time_nonnegative", "kind": "output_range",
         "path": "avg_waiting_time", "min": 0},
        {"name": "utilization_le_1", "kind": "output_range",
         "path": "server_utilization", "min": 0, "max": 1.0},
        {"name": "queue_length_nonnegative", "kind": "output_range",
         "path": "avg_queue_length", "min": 0},
        # 关键：稳定性约束 rho = lambda/(c*mu) < 1
        {"name": "stability_constraint", "kind": "output_range",
         "path": "constraint_violation_max", "min": 0, "max": 1e-6},
    ]
    reg, g, vr = run_validation(reg, g, exec_id, checks)
    print(f"  Validation: {vr.verification_id} status={vr.status}")
    for c in vr.checks:
        print(f"    [{c['name']}] passed={c['passed']} — {c['detail']}")

    exec_art = reg.get(exec_id)
    outputs = (exec_art.data or {}).get("outputs", {})
    print(f"  Outputs: wait={outputs.get('avg_waiting_time')}, "
          f"queue={outputs.get('avg_queue_length')}, "
          f"rho={outputs.get('server_utilization')}, "
          f"max_violation={outputs.get('constraint_violation_max')}")

    result = {
        "stage": "m1",
        "problem_id": problem_id, "question_id": q_id,
        "model_ir_id": mir_id, "model_id": model_id,
        "code_id": code_id, "execution_id": exec_id,
        "validation_id": vr.verification_id,
        "validation_status": vr.status,
        "validation_checks": vr.checks,
        "outputs": outputs,
    }
    (EXP_DIR / "m1" / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
    print(f"  M1 result saved to m1/result.json")
    return result


def stage_m2():
    """M2: Revision → MODEL_IR v2（修正）→ 执行 → Validation PASS。"""
    print("=" * 60)
    print("M2 — Model Revision: v1 FAIL → v2 PASS")
    print("=" * 60)
    # 读取 M1 结果获取 IDs
    m1_result = json.loads((EXP_DIR / "m1" / "result.json").read_text("utf-8"))
    old_mir_id = m1_result["model_ir_id"]
    old_model_id = m1_result["model_id"]
    q_id = m1_result["question_id"]
    print(f"  Revising M1: {old_mir_id} → v2")

    reg = _load_registry()
    g = _load_graph(reg)

    # 1. RevisionRequest（基于 M1 validation FAIL）
    revision_request = {
        "revision_of": old_mir_id,
        "trigger": "validation_failed",
        "failed_checks": [c["name"] for c in m1_result["validation_checks"]
                          if not c["passed"]],
        "diagnosis": "M1 v1 的服务率参数错误（mu 过小），导致系统不稳定 "
                     "(rho >= 1)，排队论公式产生负值或无穷大等待时间。",
        "corrective_action": "修正服务率 mu 为正确值，确保 rho = lambda/(c*mu) < 1，"
                             "重新计算 M/M/c 排队指标。",
    }

    # 2. MODEL_IR v2（修正版）
    mir_v2 = json.loads((EXP_DIR / "m2" / "model_ir_v2.json").read_text("utf-8"))
    mir_id, model_id = register_model_ir(reg, g, q_id, mir_v2, "M1-v2")
    print(f"  MODEL_IR v2: {mir_id}, Model: {model_id}")

    # 3. 登记修订谱系
    rev_id = register_revision(reg, g, old_mir_id, mir_id,
                               old_model_id, model_id, revision_request)
    print(f"  RevisionRequest: {rev_id}")
    print(f"  Edges: {mir_id} -revision_of-> {old_mir_id}, "
          f"{mir_id} -supersedes-> {old_mir_id}")

    # 4. Code v2 + Execute
    code = (EXP_DIR / "m2" / "run_model_v2.py").read_text("utf-8")
    inputs = {"parameters": mir_v2["semantic"]["parameters"]}
    flat_params = {k: v["value"] for k, v in inputs["parameters"].items()}
    inputs = {"parameters": flat_params}
    output_mapping = {
        "avg_waiting_time": "avg_waiting_time",
        "avg_queue_length": "avg_queue_length",
        "server_utilization": "server_utilization",
        "probability_wait": "probability_wait",
        "constraint_violation_max": "constraint_violation_max",
    }
    reg, g, code_id, exec_id = register_code_and_execute(
        reg, g, model_id, code, inputs, output_mapping, q_id)
    print(f"  Code v2: {code_id}, Execution v2: {exec_id}")

    # 5. Validation v2（应 PASS）
    checks = [
        {"name": "wait_time_exists", "kind": "output_field_exists",
         "path": "avg_waiting_time"},
        {"name": "wait_time_nonnegative", "kind": "output_range",
         "path": "avg_waiting_time", "min": 0},
        {"name": "utilization_le_1", "kind": "output_range",
         "path": "server_utilization", "min": 0, "max": 1.0},
        {"name": "queue_length_nonnegative", "kind": "output_range",
         "path": "avg_queue_length", "min": 0},
        {"name": "stability_constraint", "kind": "output_range",
         "path": "constraint_violation_max", "min": 0, "max": 1e-6},
        {"name": "wait_time_finite", "kind": "output_range",
         "path": "avg_waiting_time", "min": 0, "max": 1e6},
    ]
    reg, g, vr = run_validation(reg, g, exec_id, checks)
    print(f"  Validation v2: {vr.verification_id} status={vr.status}")
    for c in vr.checks:
        print(f"    [{c['name']}] passed={c['passed']} — {c['detail']}")

    exec_art = reg.get(exec_id)
    outputs = (exec_art.data or {}).get("outputs", {})
    print(f"  Outputs v2: wait={outputs.get('avg_waiting_time')}, "
          f"queue={outputs.get('avg_queue_length')}, "
          f"rho={outputs.get('server_utilization')}, "
          f"max_violation={outputs.get('constraint_violation_max')}")

    result = {
        "stage": "m2",
        "old_model_ir_id": old_mir_id, "old_model_id": old_model_id,
        "new_model_ir_id": mir_id, "new_model_id": model_id,
        "revision_request_id": rev_id,
        "code_id": code_id, "execution_id": exec_id,
        "validation_id": vr.verification_id,
        "validation_status": vr.status,
        "validation_checks": vr.checks,
        "outputs": outputs,
        "revision_request": revision_request,
    }
    (EXP_DIR / "m2" / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
    print(f"  M2 result saved to m2/result.json")
    return result


def stage_replay(exec_id=None):
    """Replay RUN1 (M1 exec) 和 RUN2 (M2 exec)，输出偏差报告。"""
    print("=" * 60)
    print("Replay — 从 execution_result 重现 RUN1/RUN2")
    print("=" * 60)
    results = {}

    # 如果没指定 exec_id，从 result.json 读取
    if exec_id:
        ids_to_replay = [exec_id]
    else:
        m1 = json.loads((EXP_DIR / "m1" / "result.json").read_text("utf-8"))
        m2 = json.loads((EXP_DIR / "m2" / "result.json").read_text("utf-8"))
        ids_to_replay = [m1["execution_id"], m2["execution_id"]]

    for eid in ids_to_replay:
        print(f"\n  Replaying {eid}...")
        rep = do_replay(eid)
        print(f"    ok={rep.get('ok')}, status: recorded={rep.get('recorded_status')} "
              f"replayed={rep.get('replayed_status')}, "
              f"outputs_match={rep.get('outputs_match')}")
        if rep.get("deviation"):
            for d in rep["deviation"]:
                print(f"    deviation: {d['dim']} — {d['why']}")
        results[eid] = rep

    (EXP_DIR / "replay_report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), "utf-8")
    print(f"\n  Replay report saved to replay_report.json")
    return results


def stage_all():
    r0 = stage_m0()
    r1 = stage_m1()
    r2 = stage_m2()
    rp = stage_replay()
    return {"m0": r0, "m1": r1, "m2": r2, "replay": rp}


def main():
    ap = argparse.ArgumentParser(description="P1-VS-001 Runner")
    ap.add_argument("--stage", required=True,
                    choices=["m0", "m1", "m2", "replay", "all"])
    ap.add_argument("--exec-id", default=None,
                    help="replay 阶段指定 execution_id")
    args = ap.parse_args()

    if args.stage == "m0":
        stage_m0()
    elif args.stage == "m1":
        stage_m1()
    elif args.stage == "m2":
        stage_m2()
    elif args.stage == "replay":
        stage_replay(args.exec_id)
    elif args.stage == "all":
        stage_all()


if __name__ == "__main__":
    main()
