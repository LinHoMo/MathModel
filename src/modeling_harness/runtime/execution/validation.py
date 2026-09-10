"""P0-E5 Validation Primitive — 三状态铁律的机械落地。

铁律（THREE_LAYER_ARCHITECTURE v3 §2.6）：execution_status=success 绝不推出
model_status=correct。本模块提供第一扇门（Execution → Validation）的确定性原语：

    ExecutionResult(EXEC)
        → 一组确定性检查（output 字段/数值范围/等式）
        → VerificationResult(VR, 一等 artifact)
        → verified_by 边绑定溯源

状态语义（与用户裁决一致）：
    * VR.status = passed  ⟺  execution success 且全部检查通过
    * VR.status = failed  ⟺  execution success 但至少一项检查失败（可归因到具体 check）
    * VR.status = invalid ⟺  execution 非 success（无输出可验证，不得 passed）

检查全部确定性执行（无 LLM、无随机）：verification 不是评价，是校验。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VERIFICATION_FIELDS = (
    "verification_id", "execution_id", "status", "checks",
    "evidence_refs", "started_at", "finished_at", "provenance",
)


@dataclass
class VerificationResultData:
    verification_id: str = ""
    execution_id: str = ""
    status: str = "invalid"          # passed / failed / invalid
    checks: list[dict] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in VERIFICATION_FIELDS}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "VerificationResultData":
        return cls(**{k: d.get(k) for k in VERIFICATION_FIELDS})


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _num(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _get_path(outputs: dict, path: str) -> Any:
    """'a.b.0' 形式取嵌套值；空路径返回整体。"""
    cur: Any = outputs
    for part in path.split(".") if path else []:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return None
    return cur


def _norm_key(key: str) -> str:
    """小写 + 去下划线/空格：'total_cost' == 'TotalCost' == 'total cost'。"""
    return "".join(ch for ch in key.lower() if ch.isalnum())


def resolve_output_key(outputs: dict, *names: str) -> str | None:
    """按候选名（name/symbol/别名）解析执行输出中的字段 key。

    精确匹配优先；其次小写归一匹配。返回命中的 key 或 None。
    """
    for n in names:
        if not n:
            continue
        if n in outputs:
            return n
    normed = {_norm_key(k): k for k in outputs}
    for n in names:
        if not n:
            continue
        hit = normed.get(_norm_key(n))
        if hit is not None:
            return hit
    return None


# ---------------------------------------------------------------- checks

def run_check(kind: str, outputs: dict, spec: dict) -> dict:
    """执行单条确定性检查，返回 {name, kind, passed, detail}。"""
    name = spec.get("name") or kind
    path = spec.get("path", "")
    detail = spec.get("expect", "")
    value = _get_path(outputs, path)

    if kind == "output_field_exists":
        ok = value is not None
        return {"name": name, "kind": kind, "passed": ok,
                "detail": (f"存在 {path}={value!r}" if ok
                           else f"缺失字段 {path!r}")}

    if kind == "output_numeric":
        num = _num(value)
        ok = num is not None
        return {"name": name, "kind": kind, "passed": ok,
                "detail": (f"{path}={num!r} 为数值" if ok
                           else f"{path}={value!r} 非数值")}

    if kind == "output_range":
        num = _num(value)
        lo, hi = spec.get("min"), spec.get("max")
        ok = num is not None and (lo is None or num >= lo) \
            and (hi is None or num <= hi)
        return {"name": name, "kind": kind, "passed": ok,
                "detail": (f"{path}={num!r} 在 [{lo}, {hi}]"
                           if ok else f"{path}={num!r} 超出 [{lo}, {hi}]")}

    if kind == "output_equals":
        ok = value == spec.get("expect")
        return {"name": name, "kind": kind, "passed": ok,
                "detail": (f"{path}={value!r} 等于期望 {spec.get('expect')!r}"
                           if ok else f"{path}={value!r} != {spec.get('expect')!r}")}

    if kind == "output_key_exists":
        # Fidelity 专用：按候选名（name/symbol/别名）解析输出字段
        hit = resolve_output_key(outputs, *(spec.get("names") or []))
        detail = (f"输出字段 {hit!r} 存在（声明 {spec.get('declared')!r}）"
                  if hit else
                  f"缺失声明 {spec.get('declared')!r}（候选 "
                  f"{spec.get('names') or []} 均未命中输出 key）")
        return {"name": name, "kind": kind, "passed": hit is not None,
                "detail": detail, "resolved_key": hit}

    if kind == "objective_finite":
        # P2-1 F7：目标值有限（递归扫描输出数值，发现 NaN/Inf → fail）。
        # 无数值输出 → 如实 unverifiable 语义：pass=False（有声明就该有
        # 数值，不能以"没输出"冒充"有限"）。
        bad = []
        for p, v in _iter_numeric(outputs):
            if v != v or v in (float("inf"), float("-inf")):
                bad.append((p, v))
        return {"name": name, "kind": kind, "passed": not bad,
                "detail": (f"输出数值全部有限（{len(list(_iter_numeric(outputs)))} 个）"
                           if not bad else
                           f"发现非有限值: {', '.join(f'{p}={v!r}' for p, v in bad[:3])}")}

    if kind == "constraint_satisfaction":
        # P2-1 F6：约束数值满足——对 MODEL_IR 中带显式可执行断言
        # （constraint.check = {path, op, value}）的约束做真值校验；
        # 无显式断言的约束如实跳过（复杂表达式不强行机械解析，不误判）。
        constraints = spec.get("constraints") or []
        judged = 0
        failed = []
        for c in constraints:
            ck = (c or {}).get("check")
            if not isinstance(ck, dict):
                continue
            cpath = ck.get("path")
            cval = _get_path(outputs, cpath)
            cnum = _num(cval)
            if cnum is None:
                failed.append(f"{cpath} 非数值")
                judged += 1
                continue
            op = ck.get("op", "<=")
            rhs = ck.get("value")
            try:
                rhs = float(rhs)
            except (TypeError, ValueError):
                failed.append(f"{cpath} 断言 rhs 非数值")
                judged += 1
                continue
            ok = {"<=": cnum <= rhs, ">=": cnum >= rhs,
                  "==": abs(cnum - rhs) < 1e-12,
                  "<": cnum < rhs, ">": cnum > rhs}.get(op)
            judged += 1
            if ok is not True:
                failed.append(f"{cpath}={cnum:g} 不满足 {op}{rhs:g}")
        if judged == 0:
            return {"name": name, "kind": kind, "passed": True,
                    "detail": "无带显式 check 断言的约束（可机械判定项 0，不误判）"}
        return {"name": name, "kind": kind, "passed": not failed,
                "detail": (f"可机械判定约束 {judged} 条全部满足"
                           if not failed else
                           f"{judged} 条中 {len(failed)} 条不满足: "
                           + "; ".join(failed[:4]))}

    return {"name": name, "kind": kind, "passed": False,
            "detail": f"未知检查类型 {kind!r}"}


def run_checks(execution_data: dict, checks: list[dict]) -> tuple[str, list[dict]]:
    """对执行结果跑检查集，返回 (status, checks)。

    铁律：execution 非 success → invalid，不执行任何检查。
    """
    if execution_data.get("status") != "success":
        return "invalid", [{
            "name": "__execution_status__", "kind": "precondition",
            "passed": False,
            "detail": (f"execution status={execution_data.get('status')}，"
                       "无输出可验证（铁律：不得 passed）"),
        }]
    results = [run_check(c.get("kind"), execution_data.get("outputs") or {},
                         c) for c in checks]
    status = "passed" if all(r["passed"] for r in results) else "failed"
    return status, results


# ---------------------------------------------------------------- P1-VS-001 数值验证（C8）

NUMERIC_VALIDATION_FIELDS = (
    "execution_valid", "mathematical_valid", "empirical_valid", "robustness",
    "constraint_violation_max", "objective_value", "objective_sane",
    "variable_domain_violation", "checks", "detail",
)


def derive_checks_from_mir(mir_data: dict) -> list[dict]:
    """audit FIX-5.2：从 MODEL_IR 动态派生验证检查（消除硬编码字段依赖）。

    无外部 validation_spec 时，从 variables[].symbol / objectives 的 target
    派生 output_field_exists 检查——验证"执行输出必须包含模型声明的变量与
    目标"，作为最小真实验证兜底。只做确定性结构检查，不推断数值正确性；
    具体数值规格仍由外部 validation_spec 提供（VS-001 等注入路径不受影响）。
    """
    checks: list[dict] = []
    for v in mir_data.get("variables") or []:
        sym = v.get("symbol") or v.get("variable_id")
        if sym:
            checks.append({
                "name": f"output_has_variable_{sym}",
                "kind": "output_field_exists",
                "path": sym,
                "expect": f"MODEL_IR 声明变量 {sym} 必须出现在执行输出",
            })
    for o in mir_data.get("objectives") or []:
        t = o.get("target") or o.get("symbol")
        if t:
            checks.append({
                "name": f"output_has_objective_{t}",
                "kind": "output_field_exists",
                "path": t,
                "expect": f"MODEL_IR 声明目标 {t} 必须出现在执行输出",
            })
    return checks


def run_numeric_validation(outputs: dict, spec: dict,
                           execution_status: str = "success") -> dict:
    """基于真实数值判 FAIL（P1-VS-001 C8，ValidationResult 四字段）。

    通用路径（audit FIX-5.2 前置）：spec 提供 "checks"（run_check 支持的类型：
    output_field_exists / output_numeric / output_range / output_equals /
    output_key_exists）时，走通用确定性检查集——不绑定任何特定题目。
    其余保持 2024_A 硬编码路径（P1-VS-001 向后兼容）。

    检查（全部确定性，零 LLM）：
      1. constraint_violation_max —— outputs["pair_distances"][t][i] 与
         spec.constraints[].reference 之差的绝对最大值（pair_index 0=头板，
         "1+"=全部体板）；> tolerance → mathematical_valid=False
      2. objective_sanity —— outputs["head_speeds"] 均值 vs spec.objective
         .expected ± tolerance → empirical_valid
      3. variable_domain_violation —— outputs["positions"] 全部坐标落在
         spec.domain [min,max] 内
      4. robustness —— 约束余量归一（1 − violation/最坏参考，clip [0,1]）
    判 FAIL 独立于 evidence_gate（evidence_gate 只查边不查数值）。
    """
    if execution_status != "success":
        return {
            "execution_valid": False, "mathematical_valid": False,
            "empirical_valid": False, "robustness": 0.0,
            "constraint_violation_max": None, "objective_value": None,
            "objective_sane": False, "variable_domain_violation": True,
            "status": "invalid", "detail": f"execution status={execution_status}",
            "checks": [{"name": "__execution_status__", "kind": "precondition",
                        "passed": False,
                        "detail": f"execution status={execution_status}，"
                                  "无输出可验证（铁律：不得 passed）"}],
        }

    # FIX-1.2/audit D-010：通用检查集路径（docstring 承诺但此前未实现）。
    # spec["checks"]（run_check 支持类型）存在时优先走确定性通用检查集，
    # 不再硬编码 2024_A 的 pair_distances/head_speeds 字段。
    checks_spec = spec.get("checks") or []
    if checks_spec:
        cstatus, results = run_checks(
            {"status": execution_status, "outputs": outputs}, checks_spec)
        n_pass = sum(1 for r in results if r.get("passed"))
        return {
            "execution_valid": True, "mathematical_valid": cstatus == "passed",
            "empirical_valid": cstatus == "passed",
            "robustness": 1.0 if cstatus == "passed" else 0.0,
            "constraint_violation_max": 0.0,
            "objective_value": None,
            "objective_sane": cstatus == "passed",
            "variable_domain_violation": False,
            "status": cstatus, "checks": results,
            "detail": f"通用检查集: {n_pass}/{len(results)} 通过",
        }

    checks: list[dict] = []
    pair_distances = outputs.get("pair_distances") or {}
    constraints = spec.get("constraints") or []
    constraint_violation_max = 0.0
    for c in constraints:
        ref = float(c.get("reference"))
        tol = float(c.get("tolerance", 1e-6))
        pi = c.get("pair_index")
        viol = 0.0
        n_checked = 0
        for t, ds in pair_distances.items():
            for i, d in enumerate(ds):
                if pi == "1+" and i < 1:
                    continue
                if pi != "1+" and i != pi:
                    continue
                n_checked += 1
                viol = max(viol, abs(float(d) - ref))
        ok = viol <= tol
        constraint_violation_max = max(constraint_violation_max, viol)
        checks.append({"name": c.get("name"), "kind": "constraint",
                       "passed": ok, "reference": ref, "max_violation": viol,
                       "checked_pairs": n_checked,
                       "detail": (f"max|d-ref|={viol:.6g}（≤{tol}）"
                                  if ok else
                                  f"max|d-ref|={viol:.6g} > tol={tol}")})

    obj = spec.get("objective") or {}
    exp = obj.get("expected")
    otol = float(obj.get("tolerance", 0.05))
    speeds = [float(v) for v in (outputs.get("head_speeds") or {}).values()
              if v is not None]
    objective_value = (sum(speeds) / len(speeds)) if speeds else None
    objective_sane = (objective_value is not None and exp is not None
                      and abs(objective_value - exp) <= otol)
    # FIX-1.2：执行失败/无输出时 objective_value=None，detail 不得格式化 None
    measured_desc = (f"{objective_value:.6g} m/s" if objective_value is not None
                     else "N/A（无输出）")
    exp_desc = (f"{exp}" if exp is not None else "N/A")
    checks.append({"name": obj.get("name", "objective_sanity"),
                   "kind": "objective", "passed": objective_sane,
                   "expected": exp, "measured": objective_value,
                   "detail": (f"mean head speed={measured_desc}"
                              f"（期望 {exp_desc}±{otol}）")})

    dom = spec.get("domain") or {}
    dmin, dmax = dom.get("min"), dom.get("max")
    domain_ok = True
    if dmin is not None and dmax is not None:
        for frame in outputs.get("positions") or []:
            for pt in frame.get("points") or []:
                for coord in pt:
                    if not (dmin <= coord <= dmax):
                        domain_ok = False
                        break
                if not domain_ok:
                    break
            if not domain_ok:
                break
    variable_domain_violation = not domain_ok
    if not domain_ok:
        checks.append({"name": "variable_domain", "kind": "domain",
                       "passed": False, "range": [dmin, dmax],
                       "detail": f"存在坐标超出 [{dmin}, {dmax}]"})

    constraint_tolerance = float(spec.get("constraint_tolerance", 1e-6))
    mathematical_valid = (constraint_violation_max <= constraint_tolerance
                          and domain_ok)
    empirical_valid = objective_sane
    if constraint_violation_max <= 1e-12:
        robustness = 1.0
    else:
        worst_ref = max((float(c.get("reference") or 1.0)) for c in constraints)
        robustness = max(0.0, 1.0 - constraint_violation_max / worst_ref)
    status = "passed" if (mathematical_valid and empirical_valid) else "failed"

    return {
        "execution_valid": True, "mathematical_valid": mathematical_valid,
        "empirical_valid": empirical_valid, "robustness": round(robustness, 6),
        "constraint_violation_max": round(constraint_violation_max, 9),
        "objective_value": objective_value,
        "objective_sane": objective_sane,
        "variable_domain_violation": variable_domain_violation,
        "status": status, "checks": checks,
        "detail": (f"constraint_violation_max={constraint_violation_max:.6g}，"
                   f"objective="
                   + (f"{objective_value:.6g}" if objective_value is not None else "N/A")
                   + f"，domain_ok={domain_ok}"),
    }


# ------------------------------------------------------------ P2-1 L6：Ground-Truth 断言判定

def _iter_numeric(outputs, path: str = ""):
    """递归产出 (path, value)：数值叶子（int/float，非 bool）。"""
    if isinstance(outputs, dict):
        for k, v in outputs.items():
            yield from _iter_numeric(v, f"{path}.{k}" if path else str(k))
    elif isinstance(outputs, (list, tuple)):
        for i, v in enumerate(outputs):
            yield from _iter_numeric(v, f"{path}[{i}]")
    elif isinstance(outputs, (int, float)) and not isinstance(outputs, bool):
        yield path, float(outputs)


def validate_against_gt(execution_result: dict,
                        gt_assertions: dict | None) -> dict:
    """P2-1 L6：可执行 ground-truth 断言判定（机械、LLM-free）。

    execution_result 应为合并了数值验证字段的真实执行产物：
      {status, outputs, constraint_violation_max, objective_value,
       objective_sane, ...}（arena 由 run_numeric_validation 产物合并）。

    gt_assertions = {"version", "source", "checks": [{
        "name", "kind", "source", 以及 kind 专属参数}]}
      kind:
        constraint_violation_max —— execution_result.constraint_violation_max
                                      vs {"op": "<=", "value": 0}
        objective_sane           —— objective_value 有限非 NaN（或
                                      execution_result.objective_sane is True）；
                                      模型无标量目标输出 → skipped（不计入分母，
                                      不误伤无目标输出的合法模型）
        output_nonnegative       —— 递归扫描 outputs 数值全部 ≥ 0；带
                                      {"paths": [候选名列表]} 时只查这些路径
                                      （由 MODEL_IR 声明的非负变量派生）
        output_range             —— {"path": "a.b" 或 "*" 全量,
                                      "min": .., "max": ..} 数值落入区间

    铁律：无断言 → unverifiable（l6_score=None，不编造分数）；
    判定失败必须来自真实数值，禁止硬编码 PASS；无法判定的断言
    如实 skipped（不计入分母，不误伤）。
    """
    checks = (gt_assertions or {}).get("checks") or []
    if not checks:
        return {
            "status": "unverifiable", "l6_score": None,
            "passed": 0, "total": 0,
            "checks": [{"name": "__no_gt_assertions__", "passed": False,
                        "detail": "无 ground-truth 断言（不编造分数）"}],
            "assertion_version": (gt_assertions or {}).get("version"),
        }
    if execution_result.get("status") != "success":
        return {
            "status": "invalid", "l6_score": None,
            "passed": 0, "total": len(checks),
            "checks": [{"name": c.get("name", "?"), "passed": False,
                        "detail": "execution 非 success，无输出可做 L6 判定",
                        "source": c.get("source")} for c in checks],
            "assertion_version": (gt_assertions or {}).get("version"),
        }
    outputs = execution_result.get("outputs") or {}
    results: list[dict] = []
    for c in checks:
        kind = c.get("kind")
        name = c.get("name") or kind
        src = c.get("source") or ""
        if kind == "constraint_violation_max":
            cvm = execution_result.get("constraint_violation_max")
            if cvm is None:
                results.append({"name": name, "passed": False,
                                "detail": "执行产物缺 constraint_violation_max",
                                "source": src})
                continue
            value = float(c.get("value", 0.0))
            passed = cvm <= value if c.get("op", "<=") == "<=" else cvm >= value
            results.append({"name": name, "passed": bool(passed),
                            "detail": f"cvm={cvm:.6g} vs {c.get('op', '<=')}{value:g}",
                            "source": src})
        elif kind == "objective_sane":
            obj = execution_result.get("objective_value")
            sane = execution_result.get("objective_sane")
            if sane is True:
                results.append({"name": name, "passed": True,
                                "detail": "objective_value 有限且合理",
                                "source": src})
            elif obj is None:
                # 模型无标量目标输出：不可判定 → skipped（不计入分母，
                # 不误伤无目标输出的合法模型，如实披露）
                results.append({"name": name, "passed": None,
                                "skipped": True,
                                "detail": "无 objective_value，该断言不可判定（skipped）",
                                "source": src})
            else:
                passed = isinstance(obj, (int, float)) and obj == obj \
                    and abs(obj) != float("inf")
                results.append({"name": name, "passed": bool(passed),
                                "detail": f"objective_value={obj!r}",
                                "source": src})
        elif kind == "output_nonnegative":
            paths = c.get("paths")
            if paths:
                # 只检查指定路径（MODEL_IR 声明的非负变量输出）
                neg = []
                scanned = 0
                for cand in paths:
                    hit = resolve_output_key(outputs, cand)
                    if hit is None:
                        continue
                    for p, v in _iter_numeric(_get_path(outputs, hit)):
                        scanned += 1
                        if v < 0:
                            neg.append((f"{hit}.{p}", v))
                if scanned == 0:
                    results.append({"name": name, "passed": None,
                                    "skipped": True,
                                    "detail": f"指定路径 {paths} 无可判定数值输出（skipped）",
                                    "source": src})
                    continue
                results.append({"name": name, "passed": not neg,
                                "detail": (f"非负输出（扫描 {scanned} 个数值，"
                                           "发现负值: "
                                           + ", ".join(f"{p}={v:g}" for p, v in neg[:3])
                                           + ("…" if len(neg) > 3 else ""))
                                           if neg else f"扫描 {scanned} 个数值全部 ≥ 0",
                                "source": src})
            else:
                neg = [(p, v) for p, v in _iter_numeric(outputs) if v < 0]
                results.append({"name": name, "passed": not neg,
                                "detail": (f"非负输出（发现 {len(neg)} 个负值: "
                                           + ", ".join(f"{p}={v:g}" for p, v in neg[:3])
                                           + ("…" if len(neg) > 3 else ""))
                                           if neg else "全部输出数值 ≥ 0",
                                "source": src})
        elif kind == "output_range":
            lo, hi = c.get("min"), c.get("max")
            path = c.get("path") or "*"
            if path == "*":
                vals = list(_iter_numeric(outputs))
            else:
                vals = [v for p, v in _iter_numeric(outputs) if p == path]
            bad = [(p, v) for p, v in vals
                   if (lo is not None and v < lo) or (hi is not None and v > hi)]
            results.append({"name": name, "passed": not bad,
                            "detail": (f"{path} ∈ [{lo}, {hi}]："
                                       + ("全部落入区间"
                                          if not bad else
                                          "越界: " + ", ".join(
                                              f"{p}={v:g}" for p, v in bad[:3])))
                            if vals else f"{path} 无数值输出可判定",
                            "source": src})
        else:
            results.append({"name": name, "passed": False,
                            "detail": f"未知断言类型: {kind}",
                            "source": src})
    judged = [r for r in results if r.get("passed") is not None]
    n_pass = sum(1 for r in judged if r["passed"])
    total = len(judged)
    score = round(n_pass / total, 4) if total else None
    status = "passed" if total and n_pass == total else "failed"
    return {"status": status, "l6_score": score,
            "passed": n_pass, "total": total,
            "skipped": sum(1 for r in results if r.get("skipped")),
            "checks": results,
            "assertion_version": (gt_assertions or {}).get("version")}


# ------------------------------------------------------------ registration

def validate_execution(project_dir: str | Path, exec_id: str,
                       checks: list[dict],
                       provenance: dict | None = None) -> VerificationResultData:
    """从 registry 取 execution_result，跑检查，注册 VR artifact + verified_by 边。

    返回 VerificationResultData；调用方可通过 data.verification_id 引用。
    """
    from runtime.artifacts.registry import ArtifactRegistry, ArtifactNotFound
    from runtime.graph.evidence_graph import EvidenceGraph

    project_dir = Path(project_dir)
    reg_path = project_dir / "state" / "registry.json"
    if not reg_path.exists():
        raise FileNotFoundError(f"Registry 不存在: {reg_path}")
    reg = ArtifactRegistry(reg_path)
    reg.load()

    try:
        art = reg.get(exec_id)
    except ArtifactNotFound:
        raise ValueError(f"execution_result 不存在: {exec_id}") from None
    exec_data = dict(art.data or {})

    started = _now()
    status, check_results = run_checks(exec_data, checks)
    finished = _now()

    vdata = VerificationResultData(
        verification_id="", execution_id=exec_id, status=status,
        checks=check_results,
        evidence_refs=[exec_id],
        started_at=started, finished_at=finished,
        provenance=provenance or {"engine": "execution.validation",
                                  "check_count": len(checks)},
    )
    created = reg.create("verification_result",
                         title=f"验证 {exec_id}（{status}）",
                         created_by="execution.validation",
                         data=vdata.to_dict(), activate=True)
    vdata.verification_id = created.artifact_id
    reg.save()

    g = EvidenceGraph(reg, project_dir / "state" / "evidence_graph.json")
    g.load()
    g.add_relation(exec_id, "verified_by", vdata.verification_id)
    g.save()

    return vdata


def main(argv: list[str] | None = None) -> int:
    """CLI：python -m runtime.execution.validation <项目> <exec_id> <checks.json>"""
    import argparse
    ap = argparse.ArgumentParser(description="对 execution_result 跑确定性验证")
    ap.add_argument("project")
    ap.add_argument("exec_id")
    ap.add_argument("checks", help="检查清单 JSON 文件路径")
    args = ap.parse_args(argv)

    checks = json.loads(Path(args.checks).read_text(encoding="utf-8"))
    vr = validate_execution(args.project, args.exec_id, checks)
    print(json.dumps(vr.to_dict(), ensure_ascii=False, indent=2))
    print(f"[validation] {vr.verification_id} status={vr.status} "
          f"checks={len(vr.checks)}")
    return 0 if vr.status == "passed" else 1
