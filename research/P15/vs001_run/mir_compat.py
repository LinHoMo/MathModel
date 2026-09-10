# -*- coding: utf-8 -*-
"""MODEL_IR 旧格式 → 新规范（src/modeling_harness/schemas/v3/model/model_ir.schema.json v1.0）迁移。

背景：schema 于 2026-09-10 全面重建为 Model IR v1.0（唯一真源）：
- 顶层 required 17 字段（modeling_trace 不再是 required，但 $defs 约束其结构）
- 各 $defs 引入新词表（objectives.type / validations.type / variables.type /
  assumptions.source / parameters.source / constraints.type / claims.type/status）
- minItems：assumptions/variables/objectives/constraints/mechanisms/
  equations/claims ≥ 1
- modeling_trace 必须为 object（trace_version/generated_at/agent_identity/
  input_sha256）

本模块把 legacy fixture 数据迁移到新规范（幂等、不修改输入、语义保留）。
迁移是**一次性数据适配**，不是兼容层：迁移后必须通过 jsonschema 全量校验
（tests 会断言）。
"""
from __future__ import annotations

import copy

_OBJ_TYPE = {
    "compute": "find", "descriptive": "find", "simulate": "simulate",
    "minimize": "minimize", "maximize": "maximize", "find": "find",
    "satisfy": "satisfy", "estimand": "estimand",
}
_VAL_TYPE = {
    "constraint": "failure_case", "constraint_check": "failure_case",
    "consistency": "failure_case", "baseline": "baseline",
    "sensitivity": "sensitivity", "robustness": "robustness",
    "uncertainty": "uncertainty", "counterfactual": "counterfactual",
    "failure_case": "failure_case", "convergence": "convergence",
}
_VAR_TYPE = {
    "input": "input", "output": "derived", "observation": "input",
    "state": "state", "derived": "derived", "constant": "constant",
    "decision": "decision", "continuous": "continuous",
    "discrete": "discrete", "index": "index", "parameter": "constant",
}
_ASSUME_SOURCE = {
    "problem_explicit": "problem_explicit",
    "reasonable_simplification": "reasonable_simplification",
    "domain_knowledge": "domain_knowledge", "derived": "derived",
    "test_fixture": "domain_knowledge", "template_default": "assumed",
}
_ASSUME_TYPE = {
    "simplification": "simplification",
    "mechanism": "mechanism_assumption",
    "mechanism_assumption": "mechanism_assumption",
    "projection": "projection",
    "calibration": "calibration_anchor",
    "calibration_anchor": "calibration_anchor",
}
_PARAM_SOURCE = {
    "problem_given": "problem_given", "experimental": "experimental",
    "assumed": "assumed", "fitted": "fitted", "derived": "derived",
    "test_fixture": "assumed", "template_default": "assumed",
}
_CONSTRAINT_TYPE = {
    "equality": "equality", "inequality": "inequality",
    "boundary": "boundary", "initial": "initial", "logical": "logical",
    "range": "boundary", "domain": "boundary",
}
_CONSTRAINT_SOURCE = {
    "problem": "problem", "physical_law": "physical_law",
    "assumption_derived": "assumption_derived", "geometric": "geometric",
    "test_fixture": "assumption_derived", "template_default": "assumption_derived",
}
_MECH_TYPE = {
    "physical": "physical", "geometric": "geometric",
    "statistical": "statistical", "optimization": "optimization",
    "dynamical": "dynamical", "other": "other",
    "algebraic": "other", "deterministic_mapping": "other",
    "linear_mapping": "other",
}
_CLAIM_TYPE = {
    "result": "result", "interpretation": "interpretation",
    "recommendation": "recommendation", "descriptive": "interpretation",
}
_CLAIM_STATUS = {
    "supported": "supported", "refuted": "refuted",
    "unresolved": "unresolved", "candidate": "unresolved",
}
_SOLVER_TYPE = {
    "analytical": "analytical", "numerical": "numerical",
    "optimization": "optimization", "simulation": "simulation",
    "other": "other", "direct": "analytical",
}


def _map(items, fn):
    if not isinstance(items, list):
        return items
    return [fn(dict(x)) if isinstance(x, dict) else x for x in items]


def _migrate_derivation_trace(eq: dict) -> None:
    """equation.derivation_trace：旧 list['mechanism X'] → 新 object。"""
    dt = eq.get("derivation_trace")
    if dt is None:
        eq["derivation_trace"] = {
            "from_assumptions": [], "from_mechanisms": [],
            "from_equations": [], "steps": [],
        }
        return
    if isinstance(dt, list):
        mechanisms = [s for s in dt if str(s).startswith("mechanism ")]
        steps = [s for s in dt if not str(s).startswith("mechanism ")]
        eq["derivation_trace"] = {
            "from_assumptions": [],
            "from_mechanisms": [m.replace("mechanism ", "") for m in mechanisms],
            "from_equations": [],
            "steps": steps,
        }


def _migrate_dependency(dep: dict) -> dict:
    """dependency：旧 kind/source/target → 新 from_type/from_id/to_type/to_id/relation。"""
    if all(k in dep for k in ("from_type", "from_id", "to_type", "to_id",
                              "relation")):
        return dep
    kind = dep.get("kind") or "uses"
    src = str(dep.get("source") or "")
    tgt = str(dep.get("target") or "")
    _PREFIX = {
        "PARM": ("parameter", "parameter_id"),
        "VAR": ("variable", "variable_id"),
        "ASSUMPTION": ("assumption", "assumption_id"),
        "MECH": ("mechanism", "mechanism_id"),
        "EQ": ("equation", "equation_id"),
        "E": ("equation", "equation_id"),
        "CONSTRAINT": ("constraint", "constraint_id"),
        "OBJ": ("objective", "objective_id"),
    }
    def _split(s: str):
        for pre, (typ, _) in _PREFIX.items():
            if s.startswith(pre):
                return typ, s
        return "variable", s
    from_type, from_id = _split(src.split("/")[0])
    to_type, to_id = _split(tgt.split("/")[0])
    rel = {"parameter_binding": "feeds", "data_binding": "uses",
           "mechanism": "governs", "derivation": "derives"}.get(kind, "uses")
    return {
        "dependency_id": dep.get("dependency_id") or f"DEP-{src}-{tgt}",
        "from_type": from_type, "from_id": from_id,
        "to_type": to_type, "to_id": to_id,
        "relation": rel,
        "kind": kind,
    }


def _map1(item: dict, key: str, table: dict, fallback: str) -> None:
    v = item.get(key)
    if isinstance(v, str):
        item[key] = table.get(v, fallback)


def migrate_model_ir(legacy: dict) -> dict:
    """旧 MODEL_IR → 新规范（幂等；不修改输入）。"""
    out = copy.deepcopy(legacy or {})
    out.setdefault("code_mapping", {})
    out.setdefault("model_id", "MIGRATED")  # _BASE 模板无 model_id（派生时覆盖）

    # objectives
    out["objectives"] = _map(out.get("objectives"), lambda o: (
        _map1(o, "type", _OBJ_TYPE, "find"),
        o.setdefault("sub_question_binding", ["Q1"]), o)[2])
    # validations
    out["validations"] = _map(out.get("validations"), lambda v: (
        _map1(v, "type", _VAL_TYPE, "failure_case"),
        _map1(v, "pass_fail", {"pending": "inconclusive"}, "inconclusive")
        if v.get("pass_fail") == "pending" else None,
        v.setdefault("sub_question_binding", ["Q1"]), v)[3])
    # variables
    out["variables"] = _map(out.get("variables"), lambda v: (
        _map1(v, "type", _VAR_TYPE, "input"),
        v.setdefault("sub_question_binding", ["Q1"]), v)[2])
    # assumptions
    out["assumptions"] = _map(out.get("assumptions"), lambda a: (
        _map1(a, "source", _ASSUME_SOURCE, "domain_knowledge"),
        _map1(a, "type", _ASSUME_TYPE, "simplification"),
        a.setdefault("sub_question_binding", ["Q1"]), a)[3])
    # parameters
    out["parameters"] = _map(out.get("parameters"), lambda p: (
        _map1(p, "source", _PARAM_SOURCE, "assumed"), p)[1])
    # constraints
    out["constraints"] = _map(out.get("constraints"), lambda c: (
        _map1(c, "type", _CONSTRAINT_TYPE, "boundary"),
        _map1(c, "source", _CONSTRAINT_SOURCE, "assumption_derived"), c)[2])
    # equations：derivation_trace list（旧）→ object（新：from_assumptions/
    # from_mechanisms/from_equations/steps）
    out["equations"] = _map(out.get("equations"), lambda eq: (
        eq.setdefault("sub_question_binding", ["Q1"]),
        eq.setdefault("variables_refs", []),
        _migrate_derivation_trace(eq), eq)[3])

    # dependencies：旧 kind/source/target → 新 from_type/from_id/to_type/
    # to_id/relation
    out["dependencies"] = _map(out.get("dependencies"),
                               _migrate_dependency)

    # solvers
    out["solvers"] = _map(out.get("solvers"), lambda sv: (
        _map1(sv, "type", _SOLVER_TYPE, "other"), sv)[1])
    # claims
    out["claims"] = _map(out.get("claims"), lambda cl: (
        _map1(cl, "type", _CLAIM_TYPE, "interpretation"),
        _map1(cl, "status", _CLAIM_STATUS, "unresolved"),
        cl.setdefault("sub_question_binding", ["Q1"]), cl)[3])

    # modeling_trace：list（旧）→ object（新）
    mt = out.get("modeling_trace")
    if isinstance(mt, list):
        out["modeling_trace"] = {
            "trace_version": "1.0",
            "generated_at": "2026-09-10T00:00:00",
            "agent_identity": "fixture-migrated",
            "input_sha256": "b" * 64,
            "steps": mt,
        }
    elif isinstance(mt, dict):
        mt.setdefault("generated_at", "2026-09-10T00:00:00")
        mt.setdefault("agent_identity", "fixture-migrated")
        mt.setdefault("input_sha256", "b" * 64)
    else:
        out["modeling_trace"] = {
            "trace_version": "1.0",
            "generated_at": "2026-09-10T00:00:00",
            "agent_identity": "fixture-migrated",
            "input_sha256": "b" * 64,
        }

    # 顶层数组：None → []
    for k in ("assumptions", "variables", "parameters", "objectives",
              "constraints", "mechanisms", "equations", "dependencies",
              "solvers", "experiments", "validations", "claims"):
        if out.get(k) is None:
            out[k] = []

    # model_graph：nodes/edges 字符串（旧）→ 对象（新）
    mg = out.get("model_graph")
    if isinstance(mg, dict):
        nodes = mg.get("nodes")
        if nodes and all(isinstance(n, str) for n in nodes):
            mg["nodes"] = [{"node_id": n, "node_type": "variable"}
                           for n in nodes]
        edges = mg.get("edges")
        if edges and all(isinstance(e, list) and len(e) == 2 for e in edges):
            mg["edges"] = [{"source_node": e[0], "target_node": e[1],
                            "edge_type": "references_variable"}
                           for e in edges]
    return out
