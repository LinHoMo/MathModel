#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""评审判定 —— 脚本重算 verdict，消费长期闲置的 review.* 参数。

为什么必须由脚本重算
--------------------
模型自评分数不可信：撰写手刚写完的东西，让同一个模型的上下文去打分，
本质上是在给自己批改作业。分数必须由脚本依据可核验的输入重新计算。

两条硬规则
----------
1. **最低分不被均分掩盖**：加权均分用于排序，但任一关键维度低于
   `review.pass_score` 都必须单独处理，不能靠其他维度的高分拉平。
2. **权重限制在 [0.7, 1.5]**：避免题型偏好被过度放大。

用法
----
    python core/tools/score_artifact.py <项目>
    python core/tools/score_artifact.py <项目> --json
    python core/tools/score_artifact.py <项目> --round 2   # 记录当前评审轮次

退出码
------
    0  pass / pass_with_review
    1  refine / refine_partial
    2  block 或输入缺失
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core" / "tools"))
for _cat in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
    sys.path.insert(0, str(ROOT / "core" / "tools" / _cat))

import state as S  # noqa: E402

try:
    import weight_profiles as WP  # 题型差异化评审权重（零依赖）
except Exception:  # pragma: no cover - 降级为固定权重
    WP = None

WEIGHT_MIN, WEIGHT_MAX = 0.7, 1.5

# 维度名 → 5 评分员 hint（用于把题型权重套到 score_card 维度上）
_SCORER_KEY_HINTS = [
    ("academic", "scorer-academic"),
    ("engineering", "scorer-engineering"),
    ("judge", "scorer-judge"),
    ("reader", "scorer-reader"),
    ("adversarial", "scorer-adversarial"),
]


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _env(key, default=None):
    """读 env 参数（复用 gatelib 的加载逻辑，避免重复实现）。"""
    try:
        sys.path.insert(0, str(ROOT / "core"))
        from env.loader import get
        return get(key, default=default)
    except Exception:
        return default


def _load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[score] 解析失败 {path}: {e}", file=sys.stderr)
        return None


def _scorer_key(name):
    """把维度名映射到 5 评分员之一；无法映射返回 None（旧 8 维命名回退自带权重）。"""
    n = (name or "").lower()
    for hint, key in _SCORER_KEY_HINTS:
        if hint in n:
            return key
    return None


def _resolve_topic_type(base):
    """从 question_spec + type_classification 解析题型（A-E / MCM / ICM），失败返回 None。"""
    contest = None
    qs = _load_json(base / "work" / "question_spec.json")
    if qs:
        meta = qs.get("metadata") or {}
        contest = str(meta.get("contest", "") or "").strip().upper()
    if contest in ("MCM", "ICM"):
        return contest
    tc = _load_json(base / "work" / "type_classification.json")
    if tc:
        pt = tc.get("problem_type") or tc.get("topic_type")
        if pt:
            letter = str(pt).strip().split("-")[0].upper()
            if letter in ("A", "B", "C", "D", "E"):
                return letter
    return None


def compute(dims, pass_score, weakness, type_weights=None):
    """重算加权分与最低分，返回 (weighted, min_score, min_names, issues)。

    type_weights: 题型差异化权重（已归一化，sum=1.0）。提供时，凡能映射到
    5 评分员之一的维度改用题型权重；无法映射的维度仍用自带权重（旧 8 维兼容）。
    """
    issues = []
    total_w = 0.0
    total_s = 0.0
    scores = []

    for d in dims:
        name = d.get("name", "?")
        try:
            score = float(d.get("score"))
        except (TypeError, ValueError):
            issues.append(f"维度「{name}」分数缺失或非法，判为无效评分")
            continue
        if not 0 <= score <= 10:
            issues.append(f"维度「{name}」分数 {score} 超出 [0,10]")
            continue

        # 权重解析：题型差异化权重优先；否则维度自带权重（并做 [0.7,1.5] 夹紧）
        scorer = _scorer_key(name) if type_weights else None
        if scorer and scorer in type_weights:
            w = float(type_weights[scorer])
        else:
            try:
                w = float(d.get("weight", 1.0))
            except (TypeError, ValueError):
                w = 1.0
            if not WEIGHT_MIN <= w <= WEIGHT_MAX:
                issues.append(
                    f"维度「{name}」权重 {w} 超出 [{WEIGHT_MIN},{WEIGHT_MAX}]，已夹紧"
                )
                w = max(WEIGHT_MIN, min(WEIGHT_MAX, w))

        if not d.get("evidence"):
            issues.append(f"维度「{name}」无证据，分数可信度存疑")

        total_w += w
        total_s += score * w
        scores.append((name, score))

    if total_w == 0:
        return None, None, [], issues or ["无有效评分维度"]

    weighted = total_s / total_w
    min_score = min(s for _, s in scores) if scores else None
    min_names = [n for n, s in scores if s == min_score]
    return weighted, min_score, min_names, issues


def merge_blocking(weakness, card_blocking):
    """把聚合卡的 blocking[] 折回 weakness counts，让 decide() 真的看得见它。

    decide() 只读 weakness["counts"]["blocking"]；聚合卡的 blocking[] 此前是死数据，
    对抗评分员的 fail 判定根本到不了 verdict。这里单向合并（不改 decide），
    条数按合并去重后的实际条数写回。

    返回 (weakness_with_merged_counts, merged_blocking)。
    """
    import aggregate_scores as AG  # 延迟 import：AG 在模块级 import 了本模块

    merged = AG.dedupe(list(card_blocking or []) + AG.weakness_blocking(weakness))
    w = dict(weakness) if isinstance(weakness, dict) else {}
    counts = dict(w.get("counts") or {})
    counts["blocking"] = len(merged)
    w["counts"] = counts
    return w, merged


def decide(weighted, min_score, min_names, weakness, pass_score, max_rounds, round_no):
    """依据分数与阻塞项给出 verdict。"""
    blocking = (weakness or {}).get("counts", {}).get("blocking", 0)
    if isinstance(blocking, list):
        blocking = len(blocking)

    if blocking > 0:
        return "block", f"存在 {blocking} 个阻塞项，禁止提交"

    if weighted is None:
        return "block", "无有效评分"

    # 最低分不被均分掩盖
    if min_score is not None and min_score < pass_score:
        if round_no >= max_rounds:
            return "pass_with_review", (
                f"最低分维度 {min_names} 为 {min_score:.1f} < {pass_score}，"
                f"但已达评审轮次上限 {max_rounds}，需在提交前人工确认"
            )
        return "refine", (
            f"最低分维度 {min_names} 为 {min_score:.1f} < {pass_score}；"
            f"加权均分 {weighted:.2f} 不足以掩盖短板"
        )

    if weighted < pass_score:
        return "refine", f"加权均分 {weighted:.2f} < {pass_score}"

    # 达标：看是否还有遗留建议
    counts = (weakness or {}).get("counts", {})
    if counts.get("major", 0) > 0:
        # 若仅个别子问受影响 → 局部回修
        scopes = {
            (t or {}).get("scope", "")
            for t in (weakness or {}).get("hits", [])
            if (t or {}).get("severity") == "major"
        }
        partial = scopes and scopes != {"全文"} and scopes != {""}
        return ("refine_partial" if partial else "pass_with_review"), (
            f"加权均分 {weighted:.2f}，仍有 {counts.get('major')} 项 major 建议"
            + ("（集中在特定子问，可局部回修）" if partial else "")
        )

    if counts.get("minor", 0) > 0:
        return "pass_with_review", f"加权均分 {weighted:.2f}，{counts.get('minor')} 项 minor 建议"

    return "pass", f"加权均分 {weighted:.2f}，无遗留问题"


def main():
    ap = argparse.ArgumentParser(description="评审判定（脚本重算 verdict）")
    ap.add_argument("project")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--round", type=int, default=1, help="当前评审轮次")
    ap.add_argument("--type", dest="type_override", default=None,
                    help="题型覆盖（A/B/C/D/E/MCM/ICM），默认从项目产物自动解析")
    args = ap.parse_args()

    base = S.project_dir(project := args.project)
    if not base.exists():
        print(f"[score] 项目不存在: {base}", file=sys.stderr)
        return 2

    pass_score = float(_env("review.pass_score", 6) or 6)
    max_rounds = int(_env("review.max_rounds", 4) or 4)

    card = _load_json(base / "work" / "score_card.json")
    weakness = _load_json(base / "work" / "weakness_report.json")

    if card is None:
        print("[score] 无 work/score_card.json，先跑 "
              "python core/tools/aggregate_scores.py <项目>", file=sys.stderr)
        return 2

    dims = card.get("dimensions", [])

    # 聚合卡的 blocking[] 此前到不了 decide()，这里折回 counts
    weakness, merged_blocking = merge_blocking(weakness, card.get("blocking") or [])

    # 题型差异化权重：优先 --type 覆盖，其次从项目产物解析
    topic_type = args.type_override or _resolve_topic_type(base)
    type_weights = None
    if topic_type and WP is not None:
        try:
            type_weights = WP.get_weights(topic_type)
        except Exception as e:
            print(f"[score] 题型权重解析失败（回退自带权重）: {e}", file=sys.stderr)
            type_weights = None

    weighted, min_score, min_names, issues = compute(
        dims, pass_score, weakness, type_weights=type_weights)
    verdict, reason = decide(weighted, min_score, min_names, weakness,
                             pass_score, max_rounds, args.round)

    result = {
        "project": base.name,
        "round": args.round,
        "max_rounds": max_rounds,
        "pass_score": pass_score,
        "topic_type": topic_type,
        "weight_profile": type_weights,
        "weighted": round(weighted, 3) if weighted is not None else None,
        "min_score": min_score,
        "min_dimensions": min_names,
        "verdict": verdict,
        "reason": reason,
        "issues": issues,
        "timestamp": _now(),
    }

    # 写入状态
    st = S.load(project)
    if st is not None:
        st["review"] = result
        S.save(project, st)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print(f"评审判定: {base.name}   第 {args.round}/{max_rounds} 轮")
        print("=" * 60)
        if topic_type:
            print(f"  题型权重: {topic_type}" + ("（已应用）" if type_weights else "（回退自带权重）"))
        if weighted is not None:
            print(f"  加权均分: {weighted:.2f}  (通过线 {pass_score})")
            print(f"  最低维度: {min_score} — {', '.join(min_names)}")
        for d in dims:
            ev = "有证据" if d.get("evidence") else "无证据"
            print(f"    - {d.get('name','?'):20s} {d.get('score')} 分  "
                  f"权重 {d.get('weight',1.0)}  [{ev}]")
        print("-" * 60)
        for i in issues:
            print(f"  [注意] {i}")
        if merged_blocking:
            print(f"  阻塞项（{len(merged_blocking)}）:")
            for b in merged_blocking:
                issue = str(b.get("issue", ""))
                print(f"    - [{b.get('source','?')}] "
                      f"{issue if len(issue) <= 90 else issue[:90] + '…'}")
        print(f"\n  verdict: {verdict}")
        print(f"  理由:   {reason}")
        print("=" * 60)

    return {"block": 2, "refine": 1, "refine_partial": 1}.get(verdict, 0)


if __name__ == "__main__":
    sys.exit(main())
