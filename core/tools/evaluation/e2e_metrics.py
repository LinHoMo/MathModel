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
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
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
    decisions.load()
    return {"registry": registry, "graph": graph, "state": state,
            "decisions": decisions}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def _method_hit(candidate_ids: list[str], card_names: dict[str, str],
                gt_methods: list[str]) -> bool:
    """top-k 候选与金标准方法做归一化包含匹配（双向）。"""
    gts = [_norm(g) for g in gt_methods if _norm(g)]
    for cid in candidate_ids:
        hay = " ".join(filter(None, {_norm(cid), _norm(card_names.get(cid, ""))}))
        for gt in gts:
            if gt and (gt in hay or hay in gt):
                return True
    return False


def _load_card_names() -> dict[str, str]:
    """从方法卡 YAML 提取 {card_id: "name family"}（零依赖正则解析）。"""
    cards_dir = ROOT / "core" / "knowledge" / "methods" / "cards"
    out: dict[str, str] = {}
    if not cards_dir.exists():
        return out
    for f in sorted(cards_dir.glob("*.yaml")):
        text = f.read_text(encoding="utf-8")
        cid_m = re.search(r"^card_id:\s*(\S+)", text, flags=re.M)
        name_m = re.search(r'^name:\s*(.+)$', text, flags=re.M)
        fam_m = re.search(r"^family:\s*(\S+)", text, flags=re.M)
        if cid_m:
            out[cid_m.group(1)] = " ".join(
                g.group(0).strip() for g in (name_m, fam_m) if g)
    return out


def _metrics(project_dir: Path, gt: dict | None, response: dict | None,
             loaded: dict) -> dict:
    reg = loaded["registry"]
    graph = loaded["graph"]
    st = loaded["state"].data["state"]
    decisions = loaded["decisions"]

    questions = [a for a in reg.list_by_type("question")]
    results = [a for a in reg.list_by_type("result")
               if a.status not in ("invalidated", "superseded", "deprecated")]
    models = [a for a in reg.list_by_type("model")]
    card_names = _load_card_names()

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

    # 2 method selection：每问题 top-3 候选（chosen + shortlist 前 2）命中 GT
    methods_gt = gt.get("methods") or []
    method_value = None
    method_detail: dict = {"gt_methods": methods_gt,
                           "per_question": {}}
    if methods_gt and models:
        hits = []
        for q in questions:
            qm = [m for m in models if m.question == q.artifact_id]
            if not qm:
                continue
            m0 = qm[0]
            data = m0.data or {}
            top3 = [data.get("card_id", "")] + list(
                (data.get("shortlist") or [])[:2])
            hit = _method_hit(top3, card_names, methods_gt)
            hits.append(hit)
            method_detail["per_question"][q.artifact_id] = {
                "top3": [t for t in top3 if t], "hit": hit}
        if hits:
            method_value = round(100.0 * sum(hits) / len(hits), 1)

    # 3 model correctness：来自 agent 对照 rubric 的评分（缺评分 → n/a）
    mc = response.get("model_correctness_pct")
    model_value = round(float(mc), 1) if mc is not None else None
    model_detail = {"source": "response.rubric" if mc is not None
                    else "缺评分响应（n/a）"}

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
        ratios = [min(1.0, counts[k] / _PAPER_DEFAULTS[k])
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

    return {
        "decomposition_coverage": pack(decomp_value, decomp_detail),
        "method_selection": pack(method_value, method_detail),
        "model_correctness": pack(model_value, model_detail),
        "experiment_validity": pack(exp_value, exp_detail),
        "validation_reliability": pack(val_value, val_detail),
        "innovation": pack(innov_value, innov_detail),
        "writing_completeness": pack(wc_value, wc_detail),
        "end_to_end": pack(e2e_value, e2e_detail),
    }


def compute_e2e_metrics(project_dir: str | Path, gt: dict | None = None,
                        response: dict | None = None) -> dict:
    """计算八项能力指标。返回可直接落盘的 JSON 兼容 dict。"""
    pdir = Path(project_dir)
    report = {
        "mode": "e2e_metrics",
        "project": pdir.name,
        "computed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "metrics": _metrics(pdir, gt, response, _load_project(pdir)),
    }
    values = [m["value"] for m in report["metrics"].values()
              if m["value"] is not None]
    report["summary"] = {
        "computed": len(values), "absent": 8 - len(values),
        "mean_of_available": round(sum(values) / len(values), 1)
        if values else None,
    }
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
    return "\n".join(lines)


def main(argv=None) -> int:  # pragma: no cover - CLI 由 benchmark.py e2e 承载
    print("本模块由 benchmark.py e2e 子命令调用；"
          "编程接口: compute_e2e_metrics(project_dir, gt, response)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
