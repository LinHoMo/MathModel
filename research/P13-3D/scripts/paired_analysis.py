#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paired_analysis.py — P13-3D-R2 配对分析工具。

计算每题的 ΔModel / ΔPaper / TE（Transmission Efficiency），
以及 Spearman ρ 检验传导一致性。

用法:
  python paired_analysis.py --questions 2024_A,2021_C,2022_B
  python paired_analysis.py --questions 2024_A,2021_C,2022_B --json
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Warning: scipy not installed, Spearman ρ will not be computed", file=sys.stderr)


ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "tools"))


def load_model_scores(project_dir: Path, questions: list[str]) -> dict[str, dict[str, float]]:
    """Load model quality scores from P13-3C results.

    P13-3C model quality scores (from P13_3C_REPORT.md):
    - B0: 37.1
    - MMA: 69.5
    - B1-F: 86.2
    """
    # P13-3C reported model quality scores (same for all questions in R1)
    P13C_MODEL_SCORES = {
        "B0": 37.1,
        "MMA": 69.5,
        "B1-F": 86.2,
    }

    scores = {}
    for q in questions:
        scores[q] = {}
        for arm in ["B0", "MMA", "B1-F"]:
            scores[q][arm] = P13C_MODEL_SCORES.get(arm, 0.0)
    return scores


def load_paper_scores(project_dir: Path, questions: list[str]) -> dict[str, dict[str, float]]:
    """Load paper quality scores from evaluation results."""
    eval_dir = project_dir / "output" / "evaluation"
    scores = {}
    for q in questions:
        scores[q] = {}

        # Load arm mapping (X/Y/Z -> arm)
        mapping_file = eval_dir / f"{q}_arm_mapping.json"
        if not mapping_file.exists():
            continue
        mapping = json.loads(mapping_file.read_text(encoding="utf-8"))
        # Invert: X/Y/Z -> arm
        id_to_arm = {v: k for k, v in mapping.items()}

        # Load paper quality
        ef = eval_dir / f"{q}_paper_quality.json"
        if not ef.exists():
            continue
        data = json.loads(ef.read_text(encoding="utf-8"))

        for paper in data.get("papers", []):
            paper_id = paper.get("id", "")
            arm = id_to_arm.get(paper_id)
            if arm:
                scores_data = paper.get("scores", {})
                mean_score = sum(scores_data.values()) / len(scores_data) if scores_data else 0.0
                scores[q][arm] = mean_score
    return scores


def load_fidelity_scores(project_dir: Path, questions: list[str]) -> dict[str, dict[str, Any]]:
    """Load fidelity v2 scores."""
    fidelity_dir = project_dir / "output" / "fidelity"
    scores = {}
    for q in questions:
        scores[q] = {}
        for arm in ["B0", "MMA", "B1-F"]:
            ff = fidelity_dir / f"{q}_{arm}_fidelity_v2.json"
            if ff.exists():
                data = json.loads(ff.read_text(encoding="utf-8"))
                scores[q][arm] = {
                    "coverage": data.get("coverage_fidelity", 0.0),
                    "semantic": data.get("semantic_fidelity", 0.0),
                    "additions": len(data.get("mutation_audit", {}).get("additions", [])),
                    "deletions": len(data.get("mutation_audit", {}).get("deletions", [])),
                    "failures": [f["code"] for f in data.get("writer_failures", [])],
                }
    return scores


def compute_paired_analysis(
    model_scores: dict[str, dict[str, float]],
    paper_scores: dict[str, dict[str, float]],
    fidelity_scores: dict[str, dict[str, Any]],
) -> dict:
    """Compute paired ΔModel/ΔPaper/TE analysis."""
    questions = list(model_scores.keys())
    paired = []

    for q in questions:
        for arm in ["B0", "MMA", "B1-F"]:
            if arm == "B1-F" and "B0" in model_scores[q]:
                delta_model = model_scores[q][arm] - model_scores[q]["B0"]
                delta_paper = paper_scores[q][arm] - paper_scores[q]["B0"]

                te = delta_paper / delta_model if delta_model != 0 else float("inf")

                paired.append({
                    "question": q,
                    "delta_model": delta_model,
                    "delta_paper": delta_paper,
                    "transmission_efficiency": te,
                    "coverage": fidelity_scores[q][arm]["coverage"],
                    "semantic": fidelity_scores[q][arm]["semantic"],
                    "additions": fidelity_scores[q][arm]["additions"],
                    "deletions": fidelity_scores[q][arm]["deletions"],
                    "failures": fidelity_scores[q][arm]["failures"],
                })

    # Compute Spearman ρ if scipy available
    spearman_rho = None
    spearman_p = None
    if HAS_SCIPY and len(paired) > 2:
        delta_models = [p["delta_model"] for p in paired]
        delta_papers = [p["delta_paper"] for p in paired]
        rho, p_val = stats.spearmanr(delta_models, delta_papers)
        spearman_rho = round(rho, 3)
        spearman_p = round(p_val, 4)

    # Compute TE statistics
    te_values = [p["transmission_efficiency"] for p in paired if p["transmission_efficiency"] != float("inf")]
    mean_te = sum(te_values) / len(te_values) if te_values else 0.0
    te_variance = sum((te - mean_te) ** 2 for te in te_values) / len(te_values) if te_values else 0.0

    return {
        "paired_data": paired,
        "spearman_rho": spearman_rho,
        "spearman_p": spearman_p,
        "mean_te": round(mean_te, 3),
        "te_variance": round(te_variance, 4),
        "te_min": round(min(te_values), 3) if te_values else None,
        "te_max": round(max(te_values), 3) if te_values else None,
        "summary": {
            "n_questions": len(questions),
            "h8_support": spearman_rho is not None and spearman_rho > 0.6 and mean_te > 0.4,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="P13-3D-R2 Paired Analysis")
    parser.add_argument("--questions", required=True, help="Comma-separated question IDs")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    questions = [q.strip() for q in args.questions.split(",")]
    project_dir = ROOT / "research" / "P13-3D"

    model_scores = load_model_scores(project_dir, questions)
    paper_scores = load_paper_scores(project_dir, questions)
    fidelity_scores = load_fidelity_scores(project_dir, questions)

    result = compute_paired_analysis(model_scores, paper_scores, fidelity_scores)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("P13-3D-R2 Paired Analysis")
        print("=" * 60)
        print(f"{'Q':<12} {'ΔModel':>8} {'ΔPaper':>8} {'TE':>6} {'Cov':>6} {'Sem':>6} {'Add':>4} {'P1-P8'}")
        print("-" * 60)
        for p in result["paired_data"]:
            failures_str = ",".join(sorted(set(p["failures"])))
            print(f"{p['question']:<12} {p['delta_model']:>+7.1f} {p['delta_paper']:>+7.1f} "
                  f"{p['transmission_efficiency']:>5.2f} {p['coverage']:>5.1%} "
                  f"{p['semantic']:>5.1%} {p['additions']:>4} {failures_str}")
        print("-" * 60)
        print(f"Mean TE: {result['mean_te']:.3f} (var: {result['te_variance']:.4f})")
        if result["spearman_rho"] is not None:
            print(f"Spearman ρ: {result['spearman_rho']} (p={result['spearman_p']})")
        print(f"H8 Support: {result['summary']['h8_support']}")


if __name__ == "__main__":
    main()
