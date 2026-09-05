#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score_compute.py -- 从产物直接抽取证据、自动计算 5 张评分卡。

替代模型手写 score_card_*.json，改为脚本依据可验证的输入重算：
- academic:    推导完整性/假设合理性/验证充分性/数学正确性
- engineering: 可复现性/计算性能/鲁棒性/工程规范
- judge:       创新性/完整性/规范性/亮点度
- reader:      结构清晰度/语言质量/图表叙事/逻辑流畅度
- adversarial: 逻辑自洽性/边界极限/造假风险/可攻击面 (扣分制)

用法：
    python core/tools/score_compute.py <项目>           # 生成/覆盖 5 张评分卡
    python core/tools/score_compute.py <项目> --json    # 同时输出汇总 JSON
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core" / "tools"))
for _cat in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
    sys.path.insert(0, str(ROOT / "core" / "tools" / _cat))

from core.env.loader import get as env_get


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# =============================================================================
# 通用工具函数
# =============================================================================

def _find_sections(tex: str) -> dict[str, str]:
    """提取 LaTeX 章节内容。返回 {section_name: content}。"""
    sections = {}
    pattern = r"\\\\(?:section|subsection)\\{([^}]+)\\}(.*?)(?=\\\\(?:section|subsection)\\{|\\\\end\\{document\\}|\\Z)"
    for match in re.finditer(pattern, tex, re.DOTALL | re.IGNORECASE):
        name = match.group(1).strip()
        content = match.group(2).strip()
        sections[name] = content
    return sections


def _count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, re.IGNORECASE))


def _has_keywords(text: str, keywords: list[str]) -> bool:
    return any(kw.lower() in text.lower() for kw in keywords)


def _score_clamp(v: float) -> float:
    return max(0.0, min(10.0, v))


# =============================================================================
# 1. Academic Scorer (学术严谨性) - 权重 25%
# 维度：推导完整性(30%)、假设合理性(25%)、验证充分性(25%)、数学正确性(20%)
# =============================================================================

def compute_academic(base: Path) -> dict:
    tex = _read_text(base / "paper" / "main.tex") or ""
    results = _load_json(base / "figures" / "all_results.json")
    weakness = _load_json(base / "work" / "weakness_report.json")

    sections = _find_sections(tex)

    # 推导完整性 (30%)
    derivation_kw = ["推导", "derivation", "从.*得到", "由.*可得", "根据.*定律", "由.*定理"]
    derivation_score = 5.0
    if _has_keywords(tex, derivation_kw):
        derivation_score += 2.0
    if any("symbol" in s.lower() or "\u7b26\u53f7" in s for s in sections):
        derivation_score += 1.5
    if any("\u5047\u8bbe" in s or "assumption" in s.lower() for s in sections):
        derivation_score += 1.5
    derivation_score = _score_clamp(derivation_score)

    # 假设合理性 (25%) - 检查四维评分
    assumption_score = 4.0
    if any("\u5047\u8bbe" in s or "assumption" in s.lower() for s in sections):
        assumption_score += 2.0
    if weakness:
        hits = weakness.get("hits", [])
        assumption_issues = [h for h in hits if h.get("type") == "assumption"]
        assumption_score -= len(assumption_issues) * 0.5
    assumption_score = _score_clamp(assumption_score)

    # 验证充分性 (25%)
    validation_score = 4.0
    val_kw = ["灵敏度", "sensitivity", "交叉验证", "cross.valid", "鲁棒性", "robust"]
    if _has_keywords(tex, val_kw):
        validation_score += 2.5
    if results and "sensitivity" in str(results).lower():
        validation_score += 2.0
    if "cross.valid" in tex.lower() or "cross_valid" in tex.lower():
        validation_score += 1.5
    validation_score = _score_clamp(validation_score)

    # 数学正确性 (20%)
    math_score = 5.0
    if any("symbol" in s.lower() or "\u7b26\u53f7" in s for s in sections):
        math_score += 1.5
    if _has_keywords(tex, ["边界条件", "boundary condition", "单位", "unit", "量纲", "dimension"]):
        math_score += 1.5
    if _count_pattern(tex, r"\\\\begin\\{(?:equation|align|gather)\\*?\\}") >= 5:
        math_score += 2.0
    math_score = _score_clamp(math_score)

    weighted = round(
        derivation_score * 0.30 +
        assumption_score * 0.25 +
        validation_score * 0.25 +
        math_score * 0.20,
        3
    )

    return {
        "scorer": "scorer-academic",
        "dimension": "academic_rigor",
        "weight": 0.25,
        "sub_scores": {
            "derivation_completeness": {"score": derivation_score, "evidence": "章节包含推导关键词，符号表{}".format("存在" if any("symbol" in s.lower() or "\u7b26\u53f7" in s for s in sections) else "缺失")},
            "assumption_validity": {"score": assumption_score, "evidence": "假设章节{}，weakness假设类问题{}个".format("存在" if any("\u5047\u8bbe" in s or "assumption" in s.lower() for s in sections) else "缺失", len([h for h in (weakness or {}).get("hits", []) if h.get("type") == "assumption"]))},
            "validation_thoroughness": {"score": validation_score, "evidence": "灵敏度/交叉验证关键词{}".format("存在" if _has_keywords(tex, val_kw) else "缺失")},
            "mathematical_correctness": {"score": math_score, "evidence": "符号表{}，公式数{}".format("存在" if any("symbol" in s.lower() or "\u7b26\u53f7" in s for s in sections) else "缺失", _count_pattern(tex, r"\\\\begin\\{(?:equation|align|gather)\\*?\\}"))}
        },
        "weighted_score": weighted,
        "evidence_refs": ["paper/main.tex"],
        "verdict_contribution": "pass" if weighted >= 6 else "refine"
    }


# =============================================================================
# 2. Engineering Scorer (工程落地) - 权重 20%
# 维度：可复现性(30%)、计算性能(20%)、鲁棒性(30%)、工程规范(20%)
# =============================================================================

def compute_engineering(base: Path) -> dict:
    tex = _read_text(base / "paper" / "main.tex") or ""
    code_main = _read_text(base / "code" / "main.py") or ""
    test_report = _load_json(base / "work" / "test_report.json")
    deliverables = _read_text(base / "output" / "CODE_DELIVERABLES.md") or ""

    # 可复现性 (30%)
    seed = int(env_get("code.random_seed", 42) or 42)
    repro_score = 3.0
    if "seed({})".format(seed) in code_main or "seed = {}".format(seed) in code_main or "random_state={}".format(seed) in code_main:
        repro_score += 3.0
    if "np.random.seed" in code_main or "random.seed" in code_main:
        repro_score += 2.0
    if test_report and test_report.get("multi_run_cv", 1.0) < 0.1:
        repro_score += 2.0
    repro_score = _score_clamp(repro_score)

    # 计算性能 (20%)
    perf_score = 5.0
    if "timeout" in code_main.lower() or "time_limit" in code_main.lower():
        perf_score += 2.0
    if "memory" in code_main.lower() or "\u5185\u5b58" in code_main:
        perf_score += 1.5
    if "solver" in code_main.lower() and ("scipy" in code_main or "cvxopt" in code_main or "ortools" in code_main):
        perf_score += 1.5
    perf_score = _score_clamp(perf_score)

    # 鲁棒性 (30%)
    robust_score = 4.0
    if "constraint" in code_main.lower() and ("penalty" in code_main.lower() or "\u60ef\u7f6e" in code_main or "soft" in code_main.lower()):
        robust_score += 2.0
    if "try:" in code_main and "except" in code_main:
        robust_score += 1.5
    if "assert" in code_main:
        robust_score += 1.5
    if _has_keywords(deliverables, ["鲁棒", "robust", "约束重验证", "constraint verification"]):
        robust_score += 1.0
    robust_score = _score_clamp(robust_score)

    # 工程规范 (20%)
    quality_score = 4.0
    if (base / "code").exists() and (base / "figures").exists():
        quality_score += 1.5
    if '"""' in code_main or "'''" in code_main or "def " in code_main:
        quality_score += 1.5
    if "data" in code_main.lower() and ("valid" in code_main.lower() or "check" in code_main.lower()):
        quality_score += 1.5
    if deliverables and ("运行" in deliverables or "run" in deliverables.lower()):
        quality_score += 1.5
    quality_score = _score_clamp(quality_score)

    weighted = round(
        repro_score * 0.30 +
        perf_score * 0.20 +
        robust_score * 0.30 +
        quality_score * 0.20,
        3
    )

    return {
        "scorer": "scorer-engineering",
        "dimension": "engineering_quality",
        "weight": 0.20,
        "sub_scores": {
            "reproducibility": {"score": repro_score, "evidence": "种子设置{}".format("存在" if "seed({})".format(seed) in code_main or "seed = {}".format(seed) in code_main else "缺失")},
            "performance": {"score": perf_score, "evidence": "超时/内存配置{}".format("存在" if "timeout" in code_main.lower() else "缺失")},
            "robustness": {"score": robust_score, "evidence": "约束重验证/软惩罚{}".format("存在" if "penalty" in code_main.lower() or "\u60ef\u7f6e" in code_main else "缺失")},
            "code_quality": {"score": quality_score, "evidence": "目录规范{}，docstring{}".format("是" if (base/"code").exists() else "否", "存在" if '"""' in code_main else "缺失")}
        },
        "weighted_score": weighted,
        "evidence_refs": ["code/main.py", "work/test_report.json", "output/CODE_DELIVERABLES.md"],
        "verdict_contribution": "pass" if weighted >= 6 else "refine"
    }


# =============================================================================
# 3. Judge Scorer (评委视角) - 权重 25%
# 维度：创新性(30%)、完整性(25%)、规范性(25%)、亮点度(20%)
# =============================================================================

def compute_judge(base: Path) -> dict:
    tex = _read_text(base / "paper" / "main.tex") or ""
    model_spec = _read_text(base / "output" / "MODEL_SPEC.md") or ""
    code_deliv = _read_text(base / "output" / "CODE_DELIVERABLES.md") or ""
    results = _load_json(base / "figures" / "all_results.json")

    # 创新性 (30%) - 对照 INNOVATION-TAGS.md
    innovation_score = 4.0
    innov_tags = _read_text(ROOT / "core" / "knowledge" / "methodology" / "INNOVATION-TAGS.md") or ""
    if innov_tags:
        tags = [line.strip() for line in innov_tags.splitlines() if line.strip() and not line.startswith("#")]
        hits = sum(1 for t in tags if t.lower() in tex.lower())
        innovation_score += min(hits * 1.5, 4.0)
    if _has_keywords(tex, ["新", "novel", "创新", "improved", "改进", "首次", "first"]):
        innovation_score += 1.5
    innovation_score = _score_clamp(innovation_score)

    # 完整性 (25%)
    complete_score = 5.0
    required = ["MODEL_SPEC.md", "CODE_DELIVERABLES.md", "PAPER_SPEC.md"]
    have = sum(1 for f in required if (base / "output" / f).exists())
    complete_score += have * 1.5
    if _has_keywords(tex, ["子问题", "sub.problem", "子问"]):
        complete_score += 1.0
    complete_score = _score_clamp(complete_score)

    # 规范性 (25%) - 格式/页数/字数/图表/公式/引用/匿名/AI披露
    compliance_score = 4.0
    if "page" in tex.lower() or "\u9875" in tex:
        compliance_score += 1.0
    if _count_pattern(tex, r"\\\\begin\\{(?:equation|align|gather)\\*?\\}") >= 15:
        compliance_score += 1.5
    if _has_keywords(tex, ["参考文献", "references", "bib"]):
        compliance_score += 1.0
    if _has_keywords(tex, ["AI", "人工智能", "ChatGPT", "GPT"]):
        compliance_score += 1.5
    compliance_score = _score_clamp(compliance_score)

    # 亮点度 (20%)
    highlight_score = 5.0
    abs_match = re.search(r"\\\\begin\\{abstract\\}(.*?)\\\\end\\{abstract\\}", tex, re.DOTALL)
    if abs_match and _count_pattern(abs_match.group(1), r"\\d+\\.?\\d*") >= 2:
        highlight_score += 2.0
    if _has_keywords(tex, ["假设", "必要性", "necessary", "简化", "justify"]):
        highlight_score += 1.5
    if _has_keywords(tex, ["局限", "limitation", "不足", "weakness", "改进", "future"]):
        highlight_score += 1.5
    highlight_score = _score_clamp(highlight_score)

    weighted = round(
        innovation_score * 0.30 +
        complete_score * 0.25 +
        compliance_score * 0.25 +
        highlight_score * 0.20,
        3
    )

    return {
        "scorer": "scorer-judge",
        "dimension": "judge_perspective",
        "weight": 0.25,
        "sub_scores": {
            "innovation": {"score": innovation_score, "evidence": "INNOVATION-TAGS 命中{}".format("是" if innov_tags and any(t.lower() in tex.lower() for t in [l.strip() for l in (_read_text(ROOT/"core"/"knowledge"/"methodology"/"INNOVATION-TAGS.md") or "").splitlines() if l.strip() and not l.startswith("#")]) else "否")},
            "completeness": {"score": complete_score, "evidence": "三手契约齐全 {}/3".format(sum(1 for f in required if (base/"output"/f).exists()))},
            "compliance": {"score": compliance_score, "evidence": "格式/引用/AI披露检查"},
            "highlight": {"score": highlight_score, "evidence": "摘要含数值{}".format("是" if abs_match and _count_pattern(abs_match.group(1), r"\\d+\\.?\\d*")>=2 else "否")}
        },
        "weighted_score": weighted,
        "evidence_refs": ["paper/main.tex", "output/MODEL_SPEC.md", "output/CODE_DELIVERABLES.md"],
        "verdict_contribution": "pass" if weighted >= 6 else "refine"
    }


# =============================================================================
# 4. Reader Scorer (可读性) - 权重 15%
# 维度：结构清晰度(30%)、语言质量(25%)、图表叙事(25%)、逻辑流畅度(20%)
# =============================================================================

def compute_reader(base: Path) -> dict:
    tex = _read_text(base / "paper" / "main.tex") or ""
    bib = _read_text(base / "paper" / "references.bib") or ""

    # 结构清晰度 (30%)
    struct_score = 5.0
    required_order = ["摘要", "问题重述", "假设", "符号", "模型", "建模", "求解", "验证", "灵敏度", "评价", "结论"]
    found_order = [s for s in required_order if s in tex]
    if len(found_order) >= 8:
        struct_score += 3.0
    elif len(found_order) >= 6:
        struct_score += 2.0
    elif len(found_order) >= 4:
        struct_score += 1.0
    struct_score = _score_clamp(struct_score)

    # 语言质量 (25%) - 无AI痕迹/禁用词/内部路径/占位符/列表
    lang_score = 7.0
    forbidden = _read_text(ROOT / "core" / "knowledge" / "validation" / "forbidden-words.md") or ""
    forbid_list = [line.strip() for line in forbidden.splitlines() if line.strip() and not line.startswith("#")]
    forbid_hits = [w for w in forbid_list if w in tex]
    lang_score -= len(forbid_hits) * 0.5
    if _count_pattern(tex, r"\\\\begin\\{(?:itemize|enumerate)\\}") > 0:
        lang_score -= 1.5
    internal = ["MODEL_SPEC", "CODE_DELIVERABLES", "all_results", "work/", "figures/", ".py"]
    internal_hits = sum(1 for p in internal if p in tex)
    lang_score -= internal_hits * 0.5
    lang_score = _score_clamp(lang_score)

    # 图表叙事 (25%) - 前引导后分析、非主语
    fig_score = 6.0
    fig_refs = _count_pattern(tex, r"如图\\d+|图\\d+所示|由图\\d+|从图\\d+")
    figs = _count_pattern(tex, r"\\\\includegraphics")
    if figs > 0 and fig_refs >= figs:
        fig_score += 2.0
    if fig_refs <= 3:  # 主语句式少
        fig_score += 1.0
    fig_score = _score_clamp(fig_score)

    # 逻辑流畅度 (20%)
    flow_score = 6.0
    transitions = ["因此", "所以", "进而", "由此", "此外", "另外", "另一方面", "综上"]
    if _has_keywords(tex, transitions):
        flow_score += 1.5
    # 引用闭合
    cite_keys = set(re.findall(r"\\\\cite[tp]?\\{([^}]+)\\}", tex))
    bib_keys = set(re.findall(r"@\\w+\\{(\\w[\\w-]*)", bib))
    if cite_keys and cite_keys.issubset(bib_keys):
        flow_score += 1.5
    flow_score = _score_clamp(flow_score)

    weighted = round(
        struct_score * 0.30 +
        lang_score * 0.25 +
        fig_score * 0.25 +
        flow_score * 0.20,
        3
    )

    return {
        "scorer": "scorer-reader",
        "dimension": "readability",
        "weight": 0.15,
        "sub_scores": {
            "structure_clarity": {"score": struct_score, "evidence": "章节覆盖 {}/{}".format(len(found_order), len(required_order))},
            "language_quality": {"score": lang_score, "evidence": "禁用词命中 {}，内部路径 {}，列表环境 {}".format(len(forbid_hits), internal_hits, _count_pattern(tex, r"\\\\begin\\{(?:itemize|enumerate)\\}"))},
            "figure_narrative": {"score": fig_score, "evidence": "图表引用 {} 次，主语句式 {}".format(fig_refs, min(fig_refs, 3))},
            "logic_flow": {"score": flow_score, "evidence": "过渡词存在，引用闭合 {}".format(cite_keys.issubset(bib_keys) if cite_keys else "N/A")}
        },
        "weighted_score": weighted,
        "evidence_refs": ["paper/main.tex", "paper/references.bib"],
        "verdict_contribution": "pass" if weighted >= 6 else "refine"
    }


# =============================================================================
# 5. Adversarial Scorer (对抗视角) - 权重 15% (扣分制，基准 10)
# 维度：逻辑自洽性(30%)、边界极限(25%)、造假风险(25%)、可攻击面(20%)
# =============================================================================

def compute_adversarial(base: Path) -> dict:
    tex = _read_text(base / "paper" / "main.tex") or ""
    results = _load_json(base / "figures" / "all_results.json")
    model_spec = _read_text(base / "output" / "MODEL_SPEC.md") or ""
    code_deliv = _read_text(base / "output" / "CODE_DELIVERABLES.md") or ""
    weakness = _load_json(base / "work" / "weakness_report.json")
    antipatterns = _read_text(ROOT / "core" / "knowledge" / "pitfalls" / "antipatterns.md") or ""

    base_score = 10.0
    deductions = []

    # 1. 逻辑自洽性 (30%) - 摘要/正文/图表/表格/代码数值一致
    consistency_penalty = 0.0
    if results:
        abs_match = re.search(r"\\\\begin\\{abstract\\}(.*?)\\\\end\\{abstract\\}", tex, re.DOTALL)
        if abs_match:
            abs_nums = set(re.findall(r"\\b\\d+\\.?\\d*\\b", abs_match.group(1)))
            body_nums = set(re.findall(r"\\b\\d+\\.?\\d*\\b", tex))
            missing = abs_nums - body_nums
            if missing:
                consistency_penalty += 1.5
                deductions.append({
                    "amount": 1.5, "dimension": "numeric_consistency",
                    "finding": "摘要数值 {} 未在正文出现".format(missing),
                    "evidence": "abstract vs body"
                })
    if _has_keywords(tex, ["矛盾", "contradict", "不一致", "inconsistent"]):
        consistency_penalty += 1.0
        deductions.append({"amount": 1.0, "dimension": "internal_contradiction", "finding": "文中存在自相矛盾表述"})

    # 2. 边界/极限情况 (25%)
    boundary_penalty = 0.0
    if not _has_keywords(tex, ["边界", "boundary", "极限", "limit", "退化", "degenerate", "极值", "extreme"]):
        boundary_penalty += 1.5
        deductions.append({"amount": 1.5, "dimension": "boundary_edge_cases", "finding": "未讨论退化/极限边界条件"})
    if results and "scenario" not in str(results).lower():
        boundary_penalty += 1.0
        deductions.append({"amount": 1.0, "dimension": "boundary_edge_cases", "finding": "缺多场景/极端参数验证"})

    # 3. 造假/夸大风险 (25%)
    fabrication_penalty = 0.0
    bib = _read_text(base / "paper" / "references.bib") or ""
    years = [int(y) for y in re.findall(r"year\\s*=\\s*['\"]?\\{?\\s*(\\d{4})", bib, re.IGNORECASE)]
    current_year = 2026
    future = [y for y in years if y > current_year]
    if future:
        fabrication_penalty += 2.0
        deductions.append({"amount": 2.0, "dimension": "fabrication_risk", "finding": "存在未来年份文献: {}".format(future)})
    if results:
        all_nums = []
        def walk(o):
            if isinstance(o, dict):
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for i in o: walk(i)
            elif isinstance(o, (int, float)) and not isinstance(o, bool):
                all_nums.append(o)
        walk(results)
        first_digits = [int(str(abs(n))[0]) for n in all_nums if n != 0]
        if first_digits:
            benford_exp = [0.301, 0.176, 0.125, 0.097, 0.079, 0.067, 0.058, 0.051, 0.046]
            benford_obs = [first_digits.count(d)/len(first_digits) for d in range(1,10)]
            chi2 = sum((o-e)**2/e for o,e in zip(benford_obs, benford_exp) if e>0)
            if chi2 > 15:
                fabrication_penalty += 1.5
                deductions.append({"amount": 1.5, "dimension": "fabrication_risk", "finding": "数值分布偏离 Benford 律 (chi2={:.1f})".format(chi2)})

    # 4. 可攻击面 (20%) - 反模式命中
    attack_penalty = 0.0
    anti_lines = [l.strip() for l in antipatterns.splitlines() if l.strip() and not l.startswith("#")]
    anti_hits = [l for l in anti_lines if any(w.lower() in tex.lower() for w in l.split() if len(w)>2)]
    if anti_hits:
        attack_penalty += min(len(anti_hits) * 0.5, 3.0)
        deductions.append({"amount": min(len(anti_hits) * 0.5, 3.0), "dimension": "antipatterns", "finding": "命中 {} 条反模式".format(len(anti_hits))})

    final_score = _score_clamp(base_score - consistency_penalty - boundary_penalty - fabrication_penalty - attack_penalty)

    # Skeptic 引用审查 (简化)
    skeptic_additions = {"citation_padding_count": 0, "citation_padding_examples": [], "reviewer_prediction": []}
    skeptic_additions["reviewer_prediction"] = [
        {"likelihood": "high", "question": "方法选型依据是什么？有无基线对比？", "rationale": "评委首要核对方法选型合理性"},
        {"likelihood": "medium", "question": "关键假设在真实场景下是否成立？", "rationale": "假设有效性常被追问"}
    ]

    return {
        "scorer": "scorer-adversarial",
        "dimension": "adversarial_review",
        "weight": 0.15,
        "base_score": 10,
        "deductions": deductions,
        "final_score": round(final_score, 3),
        "evidence_refs": ["paper/main.tex", "figures/all_results.json", "antipatterns.md"],
        "verdict_contribution": "fail" if final_score < 6 else "pass",
        "fail_reason": "、".join([d["finding"] for d in deductions if d["amount"] >= 1.0]) if any(d["amount"] >= 1.0 for d in deductions) else "",
        "skeptic_additions": skeptic_additions
    }


# =============================================================================
# 主流程
# =============================================================================

SCORERS = {
    "academic": compute_academic,
    "engineering": compute_engineering,
    "judge": compute_judge,
    "reader": compute_reader,
    "adversarial": compute_adversarial,
}


def main():
    ap = argparse.ArgumentParser(description="从产物自动计算 5 张评分卡")
    ap.add_argument("project", help="项目路径")
    ap.add_argument("--json", action="store_true", help="输出汇总 JSON")
    ap.add_argument("--skip-aggregate", action="store_true", help="跳过后续 aggregate_scores 调用")
    args = ap.parse_args()

    base = Path(args.project)
    if not base.exists():
        print("[score_compute] 项目不存在: {}".format(base), file=sys.stderr)
        return 2

    print("=" * 60)
    print("自动评分卡计算: {}".format(base.name))
    print("=" * 60)

    all_cards = {}
    for name, fn in SCORERS.items():
        print("\n[{}] 计算中...".format(name))
        try:
            card = fn(base)
            out_path = base / "work" / "score_card_{}.json".format(name)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            all_cards[name] = card
            print("  写入: {}".format(out_path))
            print("  得分: {}".format(card.get("weighted_score", card.get("final_score", "N/A"))))
        except Exception as e:
            print("  [ERROR] {}: {}".format(name, e), file=sys.stderr)
            return 1

    # 自动调用 aggregate_scores
    print("\n[aggregate_scores] 聚合中...")
    import subprocess
    r = subprocess.run(
        [sys.executable, str(ROOT / "core" / "tools" / "aggregate_scores.py"), str(base)],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if r.returncode != 0:
        print("  [WARN] aggregate_scores EXIT {}: {}".format(r.returncode, r.stderr), file=sys.stderr)
    else:
        print("  聚合完成")

    if args.json:
        summary = {k: {"score": v.get("weighted_score", v.get("final_score")), "verdict": v.get("verdict_contribution")} for k, v in all_cards.items()}
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("完成。后续运行：")
    print("  python core/tools/score_artifact.py <项目>  # 判定 verdict")
    return 0


if __name__ == "__main__":
    sys.exit(main())