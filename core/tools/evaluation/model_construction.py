#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_construction.py — P13-3 Model Construction 三独立测量评分器。

三个维度（定义见 CAPABILITY_ROADMAP_P13_P17.md P13-3）:
    structural    结构完整性（任务类型感知的组件清单）× 一致性扣分
    mathematical  数学正确性（错误分类学扣分制：量纲/索引/符号/边界/
                  校准合理性/缺失约束/未陈述假设）
    alignment     题目对齐（题目要求 → 模型元素的强制映射命中率）
                  ——"数学上正确但解决了另一个问题"在此独立暴露。

确定性、零 LLM、零第三方依赖。agent 对照 rubric 填写 scorecard（带证据
指针），本工具做 fail-closed 校验与确定性重算：
    scorecard = {
      "problem_id": ...,
      "questions": {qid: {"present": [组件id...], "alignment_hit": [索引...]}},
      "consistency_issues": ["结构级不一致描述", ...],
      "math_deductions": [{"tag": 分类学id, "count": n, "evidence": "..."}]
    }

用法: python model_construction.py --rubric <f> --scorecard <f> [--json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"_error": f"无法解析 {path}: {exc}"}


def compute(rubric: dict, scorecard: dict) -> dict:
    if "_error" in rubric:
        return rubric
    if "_error" in scorecard:
        return scorecard
    errors: list[str] = []
    rq = rubric["questions"]
    sc = scorecard.get("questions", {})

    present_total = present_hit = 0
    align_total = align_hit = 0
    per_q: dict[str, dict] = {}
    for qid, spec in rq.items():
        req = set(spec["structural_required"])
        got = set(sc.get(qid, {}).get("present", []))
        unknown = got - req
        if unknown:
            errors.append(f"{qid}: 未知结构组件 {sorted(unknown)}")
        p_hit = len(req & got)
        present_total += len(req)
        present_hit += p_hit
        pts = spec["alignment_points"]
        hits = sc.get(qid, {}).get("alignment_hit", [])
        if any(not isinstance(i, int) or i < 0 or i >= len(pts) for i in hits):
            errors.append(f"{qid}: alignment_hit 索引越界")
            valid = []
        else:
            valid = hits
        align_total += len(pts)
        align_hit += len(set(valid))
        per_q[qid] = {"structural": f"{p_hit}/{len(req)}",
                      "alignment": f"{len(set(valid))}/{len(pts)}"}

    taxonomy: dict = rubric["math_error_taxonomy"]
    math_deduct = 0.0
    ded_detail = []
    for d in scorecard.get("math_deductions", []):
        tag = d.get("tag")
        if tag not in taxonomy:
            errors.append(f"未知数学错误分类: {tag!r}")
            continue
        sub = taxonomy[tag] * int(d.get("count", 1))
        math_deduct += sub
        ded_detail.append({"tag": tag, "count": int(d.get("count", 1)),
                           "subtotal": sub, "evidence": d.get("evidence", "")})

    structural = (100.0 * present_hit / present_total) if present_total else 0.0
    structural = max(0.0, structural - rubric["consistency_penalty_per_issue"]
                     * len(scorecard.get("consistency_issues", [])))
    mathematical = max(0.0, 100.0 - math_deduct)
    alignment = round(100.0 * align_hit / align_total, 1) if align_total else 0.0
    w = rubric["weights"]
    composite = round((structural * w["structural"] + mathematical * w["mathematical"]
                       + alignment * w["alignment"])
                      / (w["structural"] + w["mathematical"] + w["alignment"]), 1)

    return {
        "mode": "model_construction",
        "problem_id": scorecard.get("problem_id"),
        "dimensions": {
            "structural_correctness": {
                "value": round(structural, 1),
                "detail": {"components": f"{present_hit}/{present_total}",
                           "consistency_issues": scorecard.get(
                               "consistency_issues", [])}},
            "mathematical_correctness": {
                "value": round(mathematical, 1),
                "detail": {"deductions": ded_detail}},
            "problem_alignment": {
                "value": alignment,
                "detail": {"per_question": per_q}},
        },
        "composite": composite,
        "errors": errors,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Model Construction 三维评分（P13-3）")
    ap.add_argument("--rubric", required=True)
    ap.add_argument("--scorecard", required=True)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    rub = _load(Path(args.rubric) if Path(args.rubric).is_absolute()
                else root / args.rubric)
    scd = _load(Path(args.scorecard) if Path(args.scorecard).is_absolute()
                else root / args.scorecard)
    report = compute(rub, scd)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
