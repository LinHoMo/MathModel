#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aggregate_scores.py —— 5 张评分卡 → work/score_card.json（聚合真源）

为什么必须由脚本聚合
--------------------
`work/score_card.json` 被三处消费：gate.py 的 scorer-adversarial 后置条件、
score_artifact.py 的 verdict 重算、revision-planner 的修改清单。但此前**没有任何
agent 声明产出它，也没有任何脚本生成它**——唯一的"生成者"是模型手写的 JSON。

手写卡在本项目里的实际后果（cumcm2024a，实测）：
  * weighted_score 写 7.07，而按同一批分数 7.5/7.2/6.9/7.5/5.5 与 A 题权重实算是 6.99；
  * blocking 只收了 weakness-hunter 的一条，对抗评分员的 fail 判定被整段丢掉。

职责边界：聚合由本脚本做，verdict 由 `score_artifact.decide()` 做。
不给 score_artifact 加 `--aggregate`——它的信任模型是"只读裁判、脚本重算"，
让裁判自己出卷子，重算就失去意义。

用法
----
    python core/tools/aggregate_scores.py <项目>            # 生成/覆盖 work/score_card.json
    python core/tools/aggregate_scores.py <项目> --verify   # 重算并与磁盘比对（门禁用）
    python core/tools/aggregate_scores.py <项目> --json     # 同时以 JSON 打印
    python core/tools/aggregate_scores.py <项目> --type C   # 覆盖题型

退出码
------
    0  已写入 / --verify 一致
    1  --verify 不一致（卡是手写的，或分卡更新后未重新聚合）
    2  输入缺失（分卡不全 / 项目不存在）
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import gatelib as G  # noqa: E402
import score_artifact as SA  # noqa: E402

try:
    import weight_profiles as WP  # 题型差异化评审权重（零依赖）
except Exception:  # pragma: no cover - 降级为固定权重
    WP = None

SCORERS = ("academic", "engineering", "judge", "reader", "adversarial")
CARD_FILES = {s: f"score_card_{s}.json" for s in SCORERS}
AGGREGATE = "score_card.json"
GENERATED_BY = "aggregate_scores.py"

# weight_profiles.DEFAULT_BASE 的同款固定权重，供题型解析不出时回退
FALLBACK_WEIGHTS = {
    "scorer-academic": 0.25,
    "scorer-engineering": 0.20,
    "scorer-judge": 0.25,
    "scorer-reader": 0.15,
    "scorer-adversarial": 0.15,
}

# 对抗卡 deductions 里哪些算"致命"：只有这些才升格为 blocking，
# 否则每条小扣分都变阻塞项，verdict 会永远 block。
FATAL_HINTS = ("blocking", "致命", "fatal")

_FIX_ACTION = "修正该项后重跑 scorer-adversarial 复核"


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[aggregate] 解析失败 {path}: {e}", file=sys.stderr)
        return None


def load_cards(work_dir):
    """读 5 张分卡，返回 (cards, missing)。"""
    cards, missing = {}, []
    for s in SCORERS:
        c = _load_json(work_dir / CARD_FILES[s])
        if c is None:
            missing.append(s)
        else:
            cards[s] = c
    return cards, missing


def extract_score(scorer, card):
    """取分：对抗卡没有 weighted_score，只有 base_score/final_score（实测字段名不同）。"""
    keys = ("final_score", "weighted_score") if scorer == "adversarial" \
        else ("weighted_score", "final_score")
    for key in keys:
        try:
            v = float(card.get(key))
        except (TypeError, ValueError):
            continue
        return round(v, 3)

    vals = []
    for sub in (card.get("sub_scores") or {}).values():
        try:
            vals.append(float((sub or {}).get("score")))
        except (TypeError, ValueError):
            continue
    return round(sum(vals) / len(vals), 3) if vals else None


def extract_evidence(card):
    """把 evidence_refs 拼成一段，避免 score_artifact.compute() 触发「无证据」告警。"""
    refs = card.get("evidence_refs") or []
    if isinstance(refs, str):
        refs = [refs]
    parts = [str(r).strip() for r in refs if str(r).strip()]
    if not parts:  # 分卡没填 refs 时退回各子项证据，总好过空字符串
        for name, sub in (card.get("sub_scores") or {}).items():
            ev = (sub or {}).get("evidence")
            if ev:
                parts.append(f"{name}: {ev}")
    return "；".join(parts)


def resolve_weights(base, type_override=None):
    """题型差异化权重，返回 (weights, topic_type)。解析不出题型时回退固定权重。"""
    topic = type_override or SA._resolve_topic_type(base)
    if topic and WP is not None:
        try:
            return WP.get_weights(topic), topic
        except Exception as e:
            print(f"[aggregate] 题型权重解析失败（回退固定权重）: {e}", file=sys.stderr)
    return dict(FALLBACK_WEIGHTS), topic


def adversarial_blocking(card):
    """blocking 路径①：对抗卡的 fail 判定 + 致命扣分项。"""
    if not card:
        return []
    out = []

    # 扣分项字段名在文档与实产物之间漂移过：SKILL.md 的 Output Schema 写
    # category/points/evidence，磁盘上真实的卡是 dimension/amount/finding。
    # 两套都认——只认一套的后果是 blocking 归零、该拦的论文被放行（fail-open）。
    for d in card.get("deductions") or []:
        d = d or {}
        text = " ".join(str(d.get(k, "")) for k in
                        ("dimension", "category", "finding", "evidence")).lower()
        if not any(h in text for h in FATAL_HINTS):
            continue
        issue = str(d.get("finding") or d.get("evidence") or "").strip()
        if issue:
            out.append({
                "source": "scorer-adversarial/deduction",
                "issue": issue,
                "severity": "blocking",
                "action_required": _FIX_ACTION,
            })

    for b in card.get("blocking_issues") or []:
        issue = (str(b.get("issue") or b.get("evidence") or "").strip()
                 if isinstance(b, dict) else str(b).strip())
        if issue:
            out.append({
                "source": "scorer-adversarial/blocking_issues",
                "issue": issue,
                "severity": "blocking",
                "action_required": _FIX_ACTION,
            })

    reason = str(card.get("fail_reason") or "").strip()
    if reason:
        out.append({
            "source": "scorer-adversarial/verdict",
            "issue": reason,
            "severity": "blocking",
            "action_required": _FIX_ACTION,
        })
    return out


def weakness_blocking(weakness):
    """blocking 路径②：weakness_report.hits[] 中 severity==blocking 的条目。"""
    out = []
    for hit in (weakness or {}).get("hits") or []:
        hit = hit or {}
        if str(hit.get("severity", "")).lower() != "blocking":
            continue
        issue = str(hit.get("evidence") or hit.get("suggestion") or "").strip()
        if not issue:
            continue
        out.append({
            "source": f"weakness-hunter/{hit.get('id', 'unknown')}",
            "issue": issue,
            "severity": "blocking",
            "action_required": str(hit.get("suggestion") or "").strip() or _FIX_ACTION,
        })
    return out


def dedupe(items):
    """按 (source, issue) 去重，保序。score_artifact.merge_blocking 复用同一函数，
    保证两处算出的是同一批条目。"""
    seen, out = set(), []
    for it in items:
        key = (it.get("source", ""), it.get("issue", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def collect_blocking(cards, weakness):
    return dedupe(adversarial_blocking(cards.get("adversarial"))
                  + weakness_blocking(weakness))


def build(base, type_override=None):
    """聚合出 score_card 结构，返回 (card, notes)；card 为 None 表示输入不全。"""
    work = base / "work"
    cards, missing = load_cards(work)
    if missing:
        return None, [f"缺分卡 work/{CARD_FILES[s]}" for s in missing]

    notes = []
    weakness = _load_json(work / "weakness_report.json")
    if weakness is None:
        notes.append("无 work/weakness_report.json，blocking 仅来自对抗评分员")

    weights, topic = resolve_weights(base, type_override)
    if not topic:
        notes.append("题型无法解析，使用固定权重")

    dims = []
    for s in SCORERS:
        name = f"scorer-{s}"
        score = extract_score(s, cards[s])
        if score is None:
            notes.append(f"{name} 无可用分数（weighted_score/final_score/sub_scores 均缺）")
            continue
        dims.append({
            "name": name,
            "score": score,
            "weight": weights.get(name, FALLBACK_WEIGHTS[name]),
            "evidence": extract_evidence(cards[s]),
        })

    total_w = sum(d["weight"] for d in dims)
    weighted = round(sum(d["score"] * d["weight"] for d in dims) / total_w, 3) if total_w else None

    card = {
        "dimensions": dims,
        "weighted_score": weighted,
        "blocking": collect_blocking(cards, weakness),
        "skeptic_additions_summary": (cards.get("adversarial") or {}).get("skeptic_additions") or {},
        "topic_type": topic,
        "generated_by": GENERATED_BY,
        "timestamp": _now(),
    }
    return card, notes


def _brief(v, limit=70):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    return s if len(s) <= limit else s[:limit] + "…"


def compare(disk, fresh):
    """忽略 timestamp，逐项比对磁盘卡与重算卡，返回差异说明列表。"""
    diffs = []
    if disk.get("generated_by") != GENERATED_BY:
        diffs.append(f"generated_by={disk.get('generated_by')!r}（应为 {GENERATED_BY!r}，疑似手写）")

    for key in ("weighted_score", "topic_type", "skeptic_additions_summary"):
        if disk.get(key) != fresh.get(key):
            diffs.append(f"{key} 不一致: 磁盘={_brief(disk.get(key))} 重算={_brief(fresh.get(key))}")

    dd, fd = disk.get("dimensions") or [], fresh.get("dimensions") or []
    if [d.get("name") for d in dd] != [d.get("name") for d in fd]:
        diffs.append(f"dimensions 名单不一致: 磁盘={[d.get('name') for d in dd]} "
                     f"重算={[d.get('name') for d in fd]}")
    else:
        for a, b in zip(dd, fd):
            for key in ("score", "weight", "evidence"):
                if a.get(key) != b.get(key):
                    diffs.append(f"dimensions[{a.get('name')}].{key} 不一致: "
                                 f"磁盘={_brief(a.get(key))} 重算={_brief(b.get(key))}")

    db, fb = disk.get("blocking") or [], fresh.get("blocking") or []
    if db != fb:
        dk = {(x.get("source"), x.get("issue")) for x in db}
        fk = {(x.get("source"), x.get("issue")) for x in fb}
        for src, issue in sorted(fk - dk):
            diffs.append(f"blocking 缺失: [{src}] {_brief(issue)}")
        for src, issue in sorted(dk - fk):
            diffs.append(f"blocking 多余: [{src}] {_brief(issue)}")
    return diffs


def main(argv=None):
    ap = argparse.ArgumentParser(description="聚合 5 张评分卡 → work/score_card.json")
    ap.add_argument("project")
    ap.add_argument("--verify", action="store_true",
                    help="重算并与磁盘卡比对（不写盘），不一致 EXIT 1")
    ap.add_argument("--json", action="store_true", help="以 JSON 打印聚合卡")
    ap.add_argument("--type", dest="type_override", default=None,
                    help="题型覆盖（A/B/C/D/E/MCM/ICM），默认从项目产物自动解析")
    args = ap.parse_args(argv)

    base = G.project_dir(args.project)
    if not base.exists():
        print(f"[aggregate] 项目不存在: {base}", file=sys.stderr)
        return 2

    if args.verify:
        # generated_by 字段可以伪造，重算结果不能。
        fresh, notes = build(base, args.type_override)
        if fresh is None:
            print("[aggregate] " + "；".join(notes), file=sys.stderr)
            return 2
        disk = _load_json(base / "work" / AGGREGATE)
        diffs = [f"work/{AGGREGATE} 不存在"] if disk is None else compare(disk, fresh)
        for d in diffs:
            print(f"  [FAIL] {d}")
        for n in notes:
            print(f"  [注意] {n}")
        if diffs:
            print(f"[aggregate] 重跑: python core/tools/aggregate_scores.py {args.project}")
            return 1
        print(f"  [PASS] work/{AGGREGATE} 与重算一致（{len(fresh['dimensions'])} 维，"
              f"weighted={fresh['weighted_score']}，blocking={len(fresh['blocking'])}）")
        return 0

    card, notes = build(base, args.type_override)
    if card is None:
        print("[aggregate] " + "；".join(notes), file=sys.stderr)
        return 2
    # --json 时 stdout 必须是纯 JSON，提示行改走 stderr，否则下游 json.loads 会被打断
    note_out = sys.stderr if args.json else sys.stdout
    for n in notes:
        print(f"  [注意] {n}", file=note_out)

    out = base / "work" / AGGREGATE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return 0

    print("=" * 60)
    print(f"聚合评分卡: {base.name}")
    print("=" * 60)
    print(f"  题型: {card['topic_type'] or '未知'}"
          + ("（固定权重）" if not card["topic_type"] else ""))
    print(f"  加权均分: {card['weighted_score']}")
    for d in card["dimensions"]:
        ev = "有证据" if d.get("evidence") else "无证据"
        print(f"    - {d['name']:20s} {d['score']:>5} 分  权重 {d['weight']:.4f}  [{ev}]")
    print("-" * 60)
    print(f"  blocking: {len(card['blocking'])} 条")
    for i, b in enumerate(card["blocking"], 1):
        print(f"    {i}. [{b['source']}] {_brief(b['issue'], 90)}")
    print("-" * 60)
    print(f"已写入 {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    print("下一步: python core/tools/score_artifact.py "
          f"{args.project}   # 由它判 verdict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
