#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e2e_metrics.py — 八项能力指标的可计算实现（Capability Baseline，P13.0）。

确定性、零 LLM、零第三方依赖。指标定义（唯一真源）:
    docs/architecture/CAPABILITY_ROADMAP_P13_P17.md §1

输入:
    project_dir   V3 项目目录（state/{registry,evidence_graph,status,decision_log}.json）
    gt            可选金标准 JSON: {"sub_questions": [...], "methods": [...]}
    response      可选评分响应 JSON（agent 对照 rubric 填写）:
                  {"decomposition_aligned": n, "model_correctness_pct": x,
                   "total": {"awarded": x, "max_score": 100}}

规则: 输入缺失的指标如实记 null（不臆造分数）；能从产物确定性计算的
尽量计算。所有指标值域 0-100。

construction_strategy_selection（模型构造策略选择评估）:
    检查 agent 构造模型时识别的问题结构是否对齐 benchmark allowed_modeling_structures。
    采用多解模型原则：allowed_modeling_structures 是唯一评分依据，
    catalog 外结构/模型标记 out_of_catalog 不自动判错，需人工审查数学合理性。
    historical_core_methods 仅用于 detail 展示，不参与评分。

Measurement Integrity（measurement metadata，不是第 9 项能力指标）:
    provenance-based realization（v1）——回答"这个分数有多少是 agent
    真实产物支撑的"。判据 v1 = created_by.startswith("agent")（本仓库
    基线实验约定，不冻结为通用语义）；分子/分母全保留可审计；不计算
    均值、不与 Capability 合并。
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
_CORE = str(ROOT / "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from runtime.decisions.log import DecisionLog  # noqa: E402
from runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402
from runtime.state.model import ProjectState  # noqa: E402

ROBUSTNESS_TAGS = {"sensitivity", "baseline", "multi_run"}

# env paper 组默认阈值（缺失回退；与 core/env/config.yaml 保持一致）
_PAPER_DEFAULTS = {"min_figures": 6, "min_tables": 4,
                   "min_equations": 15, "min_references": 10}


def _load_project(project_dir: Path) -> dict:
    sdir = project_dir / "state"
    registry = ArtifactRegistry(sdir / "registry.json")
    graph = EvidenceGraph(registry, sdir / "evidence_graph.json")
    state = ProjectState(sdir / "status.json")
    decisions = DecisionLog(sdir / "decision_log.json")
    if decisions.path.exists():
        decisions.load()
    return {"registry": registry, "graph": graph, "state": state,
            "decisions": decisions}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def _is_empty_artifact(a) -> bool:
    """P0-2: 判断 artifact 是否为空壳（无 payload 文件且无内联数据）。

    空壳判据：payload 为 None/[]，且 data 为 None/{}/或 data 内嵌 payload=[]。
    有意义的内联数据（如 model 的 card_id/objective）不算空。
    """
    payload = getattr(a, "payload", None)
    data = getattr(a, "data", None)
    payload_empty = payload is None or payload == []
    data_empty = data is None or data == {}
    if not data_empty and isinstance(data, dict):
        # data 中只有空 payload 也视为空
        if set(data.keys()) <= {"payload"} and data.get("payload") in (None, []):
            data_empty = True
    return payload_empty and data_empty


def _load_card_families() -> dict[str, str]:
    """P0-3: 从方法卡 YAML 提取 {card_id: family}（零依赖正则解析）。"""
    cards_dir = ROOT / "core" / "knowledge" / "methods" / "cards"
    out: dict[str, str] = {}
    if not cards_dir.exists():
        return out
    for f in sorted(cards_dir.glob("*.yaml")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        cid_m = re.search(r"^card_id:\s*(\S+)", text, flags=re.M)
        fam_m = re.search(r"^family:\s*(\S+)", text, flags=re.M)
        if cid_m and fam_m:
            out[cid_m.group(1)] = fam_m.group(1)
    return out


def _load_benchmark_reference(problem_id: str) -> dict:
    """从 CUMCM-Bench-v2.json 加载某题的参考方法家族。

    返回 {"historical_core_methods": [...], "allowed_modeling_structures": [...],
           "acceptable_solution_variants": [...], "family": [...]}。
    allowed_modeling_structures 是唯一评分依据；historical_core_methods 仅用于
    detail 展示，不参与评分；字段缺失时对应值为 None。
    """
    bench_path = ROOT / "research" / "P15" / "benchmark" / "CUMCM-Bench-v2.json"
    if not bench_path.exists() or not problem_id:
        return {}
    try:
        bench = json.loads(bench_path.read_text(encoding="utf-8"))
        for p in bench.get("problems", []):
            if p.get("question_id") == problem_id:
                return {
                    "historical_core_methods": p.get("historical_core_methods"),
                    "allowed_modeling_structures": p.get("allowed_modeling_structures"),
                    "acceptable_solution_variants": p.get("acceptable_solution_variants"),
                    "family": p.get("family"),
                }
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _infer_problem_id(project_dir: Path, gt: dict) -> str | None:
    """P0-3: 从 gt 或项目目录名推断 problem_id（如 2024_A）。"""
    if gt and gt.get("problem_id"):
        return gt["problem_id"]
    # 项目名形如 p151-2024a → 2024_A
    m = re.search(r"(\d{4})[_\-]?([a-e])", project_dir.name, re.I)
    if m:
        return f"{m.group(1)}_{m.group(2).upper()}"
    return None


def _structure_hit(card_id: str, card_families: dict[str, str],
                       allowed_families: list[str]) -> tuple[bool, bool]:
    """结构对齐检查：检查 card 的 modeling_structure 是否在 allowed_modeling_structures 中。

    Returns (hit, is_alternative):
      hit=True            → 结构在 allowed_modeling_structures 中
      hit=False, alt=True → 方法卡存在但家族不匹配（合理替代方法）
      hit=False, alt=False → 方法卡不存在或无家族信息
    """
    if not card_id or not allowed_families:
        return False, False
    family = card_families.get(card_id, "")
    if not family:
        return False, False
    ref_norm = {_norm(r) for r in allowed_families if _norm(r)}
    fam_norm = _norm(family)
    # 家族名直接匹配，或紧凑匹配（去空格后包含）
    fam_compact = fam_norm.replace(" ", "")
    for r in ref_norm:
        r_compact = r.replace(" ", "")
        if fam_norm == r or fam_norm in r or r in fam_norm:
            return True, False
        if fam_compact and (fam_compact in r_compact or r_compact in fam_compact):
            return True, False
    return False, True


def _model_structural_check(models: list) -> dict:
    """P0-4: 基于 artifact 内容的 minimal model_correctness 结构检查。

    检查每个 model artifact 是否包含 objective（优化目标）、constraints（约束）、
    variables（变量定义）。这只是 structural check，不是 semantic correctness。

    返回 {"structural_pass": bool, "per_model": {artifact_id: {field: bool}},
           "models_checked": int}
    """
    per_model: dict[str, dict] = {}
    all_pass = True
    checked = 0
    for m in models:
        data = getattr(m, "data", None) or {}
        payload = getattr(m, "payload", None) or []
        # 优先从 data 检查，也检查 payload 引用的文件（仅检查存在性）
        fields = {}
        for field in ("objective", "constraints", "variables"):
            val = data.get(field)
            if field == "objective":
                ok = isinstance(val, str) and len(val.strip()) > 0
            else:
                ok = isinstance(val, list) and len(val) > 0
            # 如果 data 中没有但 payload 有文件，视为可能有内容（不判 FAIL）
            if not ok and payload:
                ok = None  # 无法从内联数据判定
            fields[field] = ok
        per_model[m.artifact_id] = fields
        checked += 1
        # 只要有一个字段明确 FAIL 就整体 FAIL；None（payload有文件但无内联）不判 FAIL
        if any(v is False for v in fields.values()):
            all_pass = False
    return {
        "structural_pass": all_pass if checked > 0 else False,
        "per_model": per_model,
        "models_checked": checked,
        "note": "structural check only (objective/constraints/variables), not semantic correctness",
    }


def _metrics(project_dir: Path, gt: dict | None, response: dict | None,
             loaded: dict) -> dict:
    reg = loaded["registry"]
    graph = loaded["graph"]
    st = loaded["state"].data["state"]
    decisions = loaded["decisions"]

    questions_raw = [a for a in reg.list_by_type("question")]
    results_raw = [a for a in reg.list_by_type("result")
                   if a.status not in ("invalidated", "superseded", "deprecated")]
    models_raw = [a for a in reg.list_by_type("model")]

    # P0-2: 空壳 artifact 过滤（payload=[] 且 data={} 的不计入评分）
    questions = [a for a in questions_raw if not _is_empty_artifact(a)]
    results = [a for a in results_raw if not _is_empty_artifact(a)]
    models = [a for a in models_raw if not _is_empty_artifact(a)]
    empty_artifact_count = {
        "question": len(questions_raw) - len(questions),
        "result": len(results_raw) - len(results),
        "model": len(models_raw) - len(models),
    }
    # 统计全 registry 空壳（含 assumption/figure/problem 等不直接参与评分的类型）
    all_empty = sum(1 for a in reg.all() if _is_empty_artifact(a))
    empty_total = sum(empty_artifact_count.values())
    empty_artifact_count["_all_types_total"] = all_empty

    claims_total = int(st.get("evidence", {}).get("claims_total", 0) or 0)
    claims_supported = int(st.get("evidence", {}).get("claims_supported", 0) or 0)
    support_ratio = (claims_supported / claims_total) if claims_total else None

    gt = gt or {}
    response = response or {}

    # 1 decomposition：语义对齐数优先来自 response（agent 对照 GT 判定），
    #   否则退化为数量比（确定性代理，detail 中注明口径）
    sub_qs = gt.get("sub_questions") or []
    decomp_value = None
    decomp_detail: dict = {"gt_sub_questions": len(sub_qs),
                           "produced_questions": len(questions)}
    if sub_qs:
        aligned = response.get("decomposition_aligned")
        if aligned is None:
            aligned = min(len(questions), len(sub_qs))
            decomp_detail["mode"] = "count_ratio（无语义对齐评分，退化口径）"
        else:
            decomp_detail["mode"] = "aligned（agent 对照 GT 判定）"
        decomp_value = round(100.0 * min(int(aligned), len(sub_qs))
                             / len(sub_qs), 1)

    # 2 method selection（方法兼容性评估）。
    #   allowed_modeling_structures 是唯一评分依据；historical_core_methods 仅用于
    #   detail 展示，不参与评分，不做回退。catalog 外方法标记 out_of_catalog，
    #   不自动判 0，需人工审查数学合理性。
    methods_gt = gt.get("methods") or []
    card_families = _load_card_families()
    problem_id = _infer_problem_id(project_dir, gt)
    bench_ref = _load_benchmark_reference(problem_id) if problem_id else {}
    allowed_families = bench_ref.get("allowed_modeling_structures")
    historical_core_methods = bench_ref.get("historical_core_methods")
    acceptable_variants = bench_ref.get("acceptable_solution_variants")

    method_value = None
    method_detail: dict = {
        "gt_methods": methods_gt,
        "allowed_modeling_structures": allowed_families,
        "historical_core_methods": historical_core_methods,
        "acceptable_solution_variants": acceptable_variants,
        "problem_id": problem_id,
        "definition": (
            "方法兼容性评估：检查 agent 选择的方法族是否在 benchmark "
            "allowed_modeling_structures 中；catalog 外结构标记 out_of_catalog 不自动判错"
        ),
        "per_question": {},
    }
    if not allowed_families:
        method_detail["structure_alignment_basis"] = "unavailable"
        method_detail["note"] = "allowed_modeling_structures unavailable in benchmark"
    elif models:
        method_detail["structure_alignment_basis"] = "allowed_modeling_structures"
        t1_hits, t3_hits = [], []
        alt_count = 0
        out_of_catalog_count = 0
        for q in questions:
            qm = [m for m in models if m.question == q.artifact_id]
            if not qm:
                continue
            m0 = qm[0]
            data = m0.data or {}
            chosen = str(data.get("card_id", ""))
            shortlist = [c["card_id"] if isinstance(c, dict) else str(c)
                         for c in (data.get("shortlist") or [])]
            cands = [chosen] + [c for c in shortlist if c != chosen]
            top3 = [c for c in cands if c][:3]
            # 结构命中为唯一评分依据（allowed_modeling_structures 唯一评分依据，
            # 无字符串方法兜底；methods_gt 仅保留在 detail 展示）
            t1_fam, t1_alt = _structure_hit(chosen, card_families, allowed_families)
            t1 = t1_fam
            t3_fam = any(_structure_hit(c, card_families, allowed_families)[0]
                         for c in top3)
            t3 = t3_fam
            is_alt = (not t1_fam) and t1_alt and chosen
            # out_of_catalog 检测：card_id 不在方法卡目录中
            is_out_of_catalog = bool(chosen) and chosen not in card_families
            if is_alt:
                alt_count += 1
            if is_out_of_catalog:
                out_of_catalog_count += 1
            t1_hits.append(t1)
            t3_hits.append(t3)
            method_detail["per_question"][q.artifact_id] = {
                "top1_chosen": chosen,
                "top1_structure": card_families.get(chosen, ""),
                "top1_hit": t1, "top1_structure_hit": t1_fam,
                "top1_alternative": is_alt,
                "out_of_catalog": is_out_of_catalog,
                "top3": top3, "top3_hit": t3,
                "shortlist": shortlist}
        if t3_hits:
            method_value = round(100.0 * sum(t3_hits) / len(t3_hits), 1)
            method_detail["top1_hit_rate"] = round(
                100.0 * sum(t1_hits) / len(t1_hits), 1)
            method_detail["distinct_chosen"] = len(
                {(m.data or {}).get("card_id", "") for m in models})
            method_detail["alternative_method_count"] = alt_count
            method_detail["out_of_catalog_count"] = out_of_catalog_count
            if alt_count > 0:
                method_detail["alternative_method_note"] = (
                    f"{alt_count} 题选择了参考家族外的方法卡（alternative_method），"
                    "不自动判 wrong，需人工审查合理性")
            if out_of_catalog_count > 0:
                method_detail["out_of_catalog_note"] = (
                    f"{out_of_catalog_count} 题选择的方法不在 catalog 中"
                    "（out_of_catalog），需人工审查数学合理性，不自动判 0")

    # 3 model correctness。P0-4 修复：
    #   - 外部输入 model_correctness_pct 为 null/n/a/缺失 → UNAVAILABLE（不静默跳过）
    #   - 增加基于 artifact 内容的 structural check（objective/constraints/variables）
    #   - 缺失的题目不参与总分平均（value=None 已被 summary 过滤）
    mc_raw = response.get("model_correctness_pct")
    mc_unavailable = mc_raw is None or (isinstance(mc_raw, str)
                                        and mc_raw.strip().lower() in ("n/a", "na", "null", ""))
    structural = _model_structural_check(models) if models else {
        "structural_pass": False, "per_model": {}, "models_checked": 0,
        "note": "no non-empty model artifacts"}

    if mc_unavailable:
        model_value = None
        model_detail = {
            "model_correctness": "UNAVAILABLE",
            "source": "外部评分缺失（null/n/a），不参与总分计算",
            "model_correctness_structural": "PASS" if structural["structural_pass"] else "FAIL",
            "structural_check": structural,
            "note": "structural check only, not semantic correctness",
        }
    else:
        try:
            model_value = round(float(mc_raw), 1)
            model_detail = {
                "model_correctness": model_value,
                "source": "response.rubric",
                "model_correctness_structural": "PASS" if structural["structural_pass"] else "FAIL",
                "structural_check": structural,
                "note": "structural check only, not semantic correctness",
            }
        except (TypeError, ValueError):
            model_value = None
            model_detail = {
                "model_correctness": "UNAVAILABLE",
                "source": f"外部评分格式错误: {repr(mc_raw)}",
                "model_correctness_structural": "PASS" if structural["structural_pass"] else "FAIL",
                "structural_check": structural,
            }

    # 4 experiment validity：实验设计质量（稳健性证据覆盖 + 多次运行）
    robust = [r for r in results
              if ROBUSTNESS_TAGS & set(r.tags or [])]
    robust_ratio = (len(robust) / len(results)) if results else None
    multi_run = sum(1 for r in results
                    if (r.data or {}).get("runs", 1) >= 5)
    exp_components = [v for v in (robust_ratio,) if v is not None]
    exp_value = round(100.0 * sum(exp_components) / len(exp_components), 1) \
        if exp_components else None
    exp_detail = {"results": len(results), "with_robustness_tags": len(robust),
                  "multi_run_ge5": multi_run}

    # 5 validation reliability：证据质量（claim 支撑率 + 论文/引用侧如存在）
    val_components = [v for v in (support_ratio,) if v is not None]
    paper = project_dir / "paper" / "main.tex"
    if paper.exists():
        val_components.append(1.0)   # 存在论文占位；一致性由 consistency_checker 另行验证
    val_value = round(100.0 * sum(val_components) / len(val_components), 1) \
        if val_components else None
    val_detail = {"claims_supported": claims_supported,
                  "claims_total": claims_total,
                  "paper_present": paper.exists()}

    # 6 innovation：声明的创新（pattern 引用）中有实验支撑的比例
    pat_refs = [ref.get("id", "") for d in decisions.decisions.values()
                if d.active for ref in (d.knowledge_refs or [])
                if str(ref.get("id", "")).startswith("pat-")]
    if pat_refs:
        exp_qs = {e.question for e in reg.list_by_type("experiment")}
        backed = sum(1 for d in decisions.decisions.values()
                     if d.active and any(str(r.get("id", "")).startswith("pat-")
                                         for r in (d.knowledge_refs or []))
                     and d.question in exp_qs)
        innov_value = round(100.0 * backed / len(pat_refs), 1)
    else:
        innov_value = 0.0
    innov_detail = {"declared_patterns": len(pat_refs)}

    # 7 writing completeness：结构完整率（无 main.tex → n/a）
    wc_value = None
    wc_detail: dict = {"main_tex": paper.exists()}
    if paper.exists():
        tex = paper.read_text(encoding="utf-8", errors="ignore")
        bib = project_dir / "paper" / "references.bib"
        counts = {
            "figures": len(re.findall(r"\\includegraphics", tex)),
            "tables": len(re.findall(r"\\begin\{table", tex)),
            "equations": len(re.findall(r"\\begin\{equation", tex)),
            "references": len(re.findall(r"^@\w+", bib.read_text(encoding="utf-8"),
                                         flags=re.M)) if bib.exists() else 0,
        }
        ratios = [min(1.0, counts[k] / _PAPER_DEFAULTS["min_" + k])
                  for k in counts]
        wc_value = round(100.0 * sum(ratios) / len(ratios), 1)
        wc_detail.update(counts)

    # 8 end-to-end：rubric 总分（response 缺失 → n/a）
    total = response.get("total") or {}
    e2e_value = None
    if total.get("max_score"):
        e2e_value = round(100.0 * float(total.get("awarded", 0))
                          / float(total["max_score"]), 1)
    e2e_detail = {"rubric_total": total or None}

    def pack(value, detail):
        return {"value": value, "detail": detail}

    metrics = {
        "decomposition_coverage": pack(decomp_value, decomp_detail),
        "structure_alignment": pack(method_value, method_detail),  # 输出键=结构对齐（Model Construction Strategy Selection 语义，v1.2 统一）
        "model_correctness": pack(model_value, model_detail),
        "experiment_validity": pack(exp_value, exp_detail),
        "validation_reliability": pack(val_value, val_detail),
        "innovation": pack(innov_value, innov_detail),
        "writing_completeness": pack(wc_value, wc_detail),
        "end_to_end": pack(e2e_value, e2e_detail),
    }
    return {
        "metrics": metrics,
        "empty_artifact_filter": {
            "total_excluded": empty_total,
            "registry_empty_total": all_empty,
            "per_type": empty_artifact_count,
            "note": f"评分相关 {empty_total} 个空壳 artifact 已排除（全 registry 共 {all_empty} 个空壳），不参与评分" if empty_total > 0
            else f"无评分相关空壳 artifact（全 registry 共 {all_empty} 个空壳）",
        },
    }


def _measurement_integrity(registry) -> dict:
    """Provenance-based realization（v1，measurement metadata）。

    回答"分数有多少由 agent 真实登记的产物支撑"，不是能力分数：
    不求均值、不进能力总分。分子/分母全保留供审计。
    """
    agent = lambda a: str(getattr(a, "created_by", "") or "").startswith("agent")  # noqa: E731
    agent_created = sum(1 for a in registry.all() if agent(a))
    total = len(registry.all())

    def ratio(art_type: str) -> dict:
        arts = registry.list_by_type(art_type)
        num = sum(1 for a in arts if agent(a))
        den = len(arts)
        return {"numerator": num, "denominator": den,
                "value": round(100.0 * num / den, 1) if den else None}

    return {
        "criterion": "created_by startswith 'agent'（provenance-based, v1）",
        "experiment_realization": ratio("experiment"),
        "validation_realization": ratio("claim"),
        "writing_realization": ratio("paper_section"),
        "overall_real_artifact": {"numerator": agent_created,
                                  "denominator": total,
                                  "value": round(100.0 * agent_created / total, 1)
                                  if total else None},
    }


def compute_e2e_metrics(project_dir: str | Path, gt: dict | None = None,
                        response: dict | None = None) -> dict:
    """计算八项能力指标 + Measurement Integrity 仪表盘。"""
    pdir = Path(project_dir)
    loaded = _load_project(pdir)
    metrics_result = _metrics(pdir, gt, response, loaded)
    metrics = metrics_result["metrics"]
    report = {
        "mode": "e2e_metrics",
        "project": pdir.name,
        "computed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "metrics": metrics,
        "empty_artifact_filter": metrics_result["empty_artifact_filter"],
        "measurement_integrity": _measurement_integrity(loaded["registry"]),
    }
    values = [m["value"] for m in metrics.values()
              if m["value"] is not None]
    report["summary"] = {
        "computed": len(values), "absent": 8 - len(values),
        "mean_of_available": round(sum(values) / len(values), 1)
        if values else None,
    }   # summary 只覆盖 Capability；Measurement Integrity 不参与任何均值
    return report


def render_report(metrics_report: dict, problem_meta: dict | None = None) -> str:
    """渲染 markdown 报告（BASELINE_REPORT 的 per-problem 块）。"""
    lines = [f"## {metrics_report['project']}"]
    if problem_meta:
        lines.append(f"- 题目: {problem_meta.get('problem_id', '?')} — "
                     f"{problem_meta.get('title', '')}")
    lines.append(f"- 计算时间: {metrics_report['computed_at']}")
    lines.append("")
    lines.append("| 指标 | 值 (0-100) | 明细 |")
    lines.append("|---|---|---|")
    for name, m in metrics_report["metrics"].items():
        v = "n/a" if m["value"] is None else m["value"]
        d = json.dumps(m["detail"], ensure_ascii=False)
        d = d if len(d) <= 120 else d[:117] + "..."
        lines.append(f"| {name} | {v} | `{d}` |")
    s = metrics_report["summary"]
    lines.append("")
    lines.append(f"可计算指标 {s['computed']}/8，缺失 {s['absent']}（n/a 不计分），"
                 f"可得均值 **{s['mean_of_available']}**。")
    lines.append("")
    # P0-2: 空壳 artifact 过滤报告
    eaf = metrics_report.get("empty_artifact_filter")
    if eaf and eaf.get("total_excluded", 0) > 0:
        lines.append("### Artifact Non-Emptiness Filter")
        lines.append("")
        lines.append(f"**{eaf['total_excluded']} 个空壳 artifact 已排除**（不参与评分）：")
        for atype, cnt in eaf.get("per_type", {}).items():
            if cnt > 0:
                lines.append(f"- {atype}: {cnt} 个")
        lines.append("")
    mi = metrics_report.get("measurement_integrity")
    if mi:
        lines.append("### Measurement Integrity"
                     "（measurement metadata，非能力分数，不并入均值）")
        lines.append("")
        lines.append(f"判据: {mi['criterion']}")
        lines.append("")
        lines.append("| 量 | 值 | 分子 / 分母 |")
        lines.append("|---|---|---|")
        for k in ("experiment_realization", "validation_realization",
                  "writing_realization", "overall_real_artifact"):
            v = mi[k]
            val = "n/a" if v["value"] is None else f"{v['value']}%"
            lines.append(f"| {k} | {val} | {v['numerator']} / {v['denominator']} |")
        lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:  # pragma: no cover - CLI 由 benchmark.py e2e 承载
    print("本模块由 benchmark.py e2e 子命令调用；"
          "编程接口: compute_e2e_metrics(project_dir, gt, response)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
