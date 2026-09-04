#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""knowledge.py — Knowledge 检索 CLI（V3 P2）

跨 runtime 的知识检索入口：任意 agent 用一条命令拿到方法建议包
（候选方法 + 适用条件 + 风险 + 验证方式 + 历史失败案例 + 创新模式）。

用法:
    python core/tools/knowledge.py recommend --types evaluation,ranking [--no-data]
                                         [--sample small|medium|large]
                                         [--timeseries] [--objectives N] [--uncertain]
    python core/tools/knowledge.py show mc-topsis
    python core/tools/knowledge.py failures mc-ga
    python core/tools/knowledge.py patterns [evaluation,...]
    python core/tools/knowledge.py stats

零第三方依赖。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core"))

from runtime.knowledge.cards import CardError           # noqa: E402
from runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402

KNOWLEDGE_ROOT = ROOT / "core" / "knowledge"


def _retriever() -> KnowledgeRetriever:
    return KnowledgeRetriever(KNOWLEDGE_ROOT)


def cmd_recommend(args) -> int:
    r = _retriever()
    features = {"problem_types": [t.strip() for t in args.types.split(",") if t.strip()]}
    if args.no_data:
        features["has_data"] = False
    if args.sample:
        features["sample_size"] = args.sample
    if args.timeseries:
        features["time_series"] = True
    if args.objectives is not None:
        features["objectives"] = args.objectives
    if args.uncertain:
        features["uncertainty"] = True

    recs = r.recommend(features, top_k=args.top)
    if not recs:
        print("[knowledge] 无匹配方法卡（检查问题类型标签: "
              f"{sorted({t for c in r.cards.values() for t in c.problem_types})}）")
        return 1
    for i, rec in enumerate(recs, 1):
        c = rec.card
        print(f"{i}. [{c.card_id}] {c.name}  (score={rec.score}, family={c.family})")
        for m in rec.matched:
            print(f"   + {m}")
        for g in c.good_for[:3]:
            print(f"   适用: {g}")
        for v in c.validation:
            print(f"   必做验证: {v}")
        for w in (rec.warnings or c.risks)[:2]:
            print(f"   风险: {w}")
        for f in rec.related_failures:
            print(f"   失败案例: [{f.failure_id}] {f.title} → 避免: {f.avoidance}")
        for p in rec.related_patterns:
            print(f"   创新模式: [{p.pattern_id}] {p.title}")
        if c.often_combined_with:
            print(f"   常组合: {', '.join(c.often_combined_with)}")
    return 0


def cmd_show(args) -> int:
    r = _retriever()
    c = r.card(args.card_id)
    print(f"[{c.card_id}] {c.name}  (family={c.family}, v{c.version})")
    print(f"问题类型: {', '.join(c.problem_types)}")
    print("适用:")
    for g in c.good_for:
        print(f"  + {g}")
    if c.requires:
        print("前提:")
        for q in c.requires:
            print(f"  - {q}")
    if c.risks:
        print("风险:")
        for w in c.risks:
            print(f"  ! {w}")
    if c.validation:
        print("必做验证:")
        for v in c.validation:
            print(f"  * {v}")
    if c.often_combined_with:
        print(f"常组合: {', '.join(c.often_combined_with)}")
    if c.reference:
        print(f"详档: core/knowledge/{c.reference}")
    return 0


def cmd_failures(args) -> int:
    r = _retriever()
    for f in r.failures_for(args.card_id):
        print(f"[{f.failure_id}] {f.title}  (mode={f.failure_mode})")
        print(f"  症状: {f.symptom}")
        print(f"  检测: {f.detection}")
        print(f"  避免: {f.avoidance}")
    return 0


def cmd_patterns(args) -> int:
    r = _retriever()
    types = [t.strip() for t in (args.types or "").split(",") if t.strip()]
    pats = r.patterns_for(types) if types else list(r.patterns.values())
    for p in pats:
        print(f"[{p.pattern_id}] {p.title}")
        print(f"  基线: {p.baseline_method}")
        print(f"  创新: {p.innovation}")
        for e in p.required_evidence:
            print(f"  必需证据: {e}")
    return 0


def cmd_stats(_args) -> int:
    r = _retriever()
    families = sorted({c.family for c in r.cards.values()})
    modes = sorted({f.failure_mode for f in r.failures.values()})
    print(f"方法卡: {len(r.cards)} 张  方法族: {', '.join(families)}")
    print(f"失败记忆: {len(r.failures)} 条  失败模式: {', '.join(modes)}")
    print(f"创新模式: {len(r.patterns)} 个")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Knowledge 检索 CLI（V3）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("recommend", help="按问题特征检索方法建议包")
    p.add_argument("--types", required=True, help="问题类型标签，逗号分隔（evaluation,ranking...）")
    p.add_argument("--no-data", action="store_true", help="无题给数据")
    p.add_argument("--sample", choices=["small", "medium", "large"], help="样本量档")
    p.add_argument("--timeseries", action="store_true", help="问题含时间演化")
    p.add_argument("--objectives", type=int, help="目标数")
    p.add_argument("--uncertain", action="store_true", help="含不确定性")
    p.add_argument("--top", type=int, default=5)
    p.set_defaults(fn=cmd_recommend)

    p = sub.add_parser("show", help="查看方法卡详情")
    p.add_argument("card_id")
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("failures", help="方法卡的关联失败记忆")
    p.add_argument("card_id")
    p.set_defaults(fn=cmd_failures)

    p = sub.add_parser("patterns", help="创新模式（可按问题类型过滤）")
    p.add_argument("types", nargs="?", default="")
    p.set_defaults(fn=cmd_patterns)

    p = sub.add_parser("stats", help="知识库统计")
    p.set_defaults(fn=cmd_stats)

    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except CardError as exc:
        print(f"[knowledge] 契约错误: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        print(f"[knowledge] 不存在: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
