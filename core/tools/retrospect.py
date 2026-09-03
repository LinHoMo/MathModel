#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""retrospect.py — 赛后回顾工具（Growth 阶段）

借鉴全流程建模工作流的「Growth 回顾」理念：比赛/项目收尾后，把过程数据
（失败记录、返修轮次、门禁警告、评审判定）汇总为结构化回顾报告，供把教训
沉淀回知识库（core/knowledge/_negative/ 与 pitfalls/）。

用法:
    python core/tools/retrospect.py <项目> [--out <work/RETROSPECTIVE.md>]

零第三方依赖。只读 state.json 与 output 产物，写出到 work/ 目录。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDS = ("modeler", "programmer", "writer", "reviewer")

# 仅取 PIPELINE 总步数（四手全流程 agent 数），避免硬编码
sys.path.insert(0, str(ROOT / "core" / "tools"))
import state as S  # noqa: E402


def _load_state(project_dir: Path) -> dict:
    state_path = project_dir / "work" / "state.json"
    if not state_path.exists():
        raise FileNotFoundError(f"未找到状态文件: {state_path}")
    with open(state_path, encoding="utf-8") as f:
        return json.load(f)


def build_report(state: dict) -> dict:
    """从 state.json 计算回顾统计。纯函数，便于单测。"""
    completed = state.get("completed") or []
    failed = state.get("failed") or []
    q_states = state.get("q_states") or {}
    review = state.get("review") or {}

    by_hand_done = {h: 0 for h in HANDS}
    by_hand_fail = {h: 0 for h in HANDS}
    for item in completed:
        hand = item.get("hand")
        if hand in by_hand_done:
            by_hand_done[hand] += 1
    for item in failed:
        hand = item.get("hand") if isinstance(item, dict) else None
        if hand in by_hand_fail:
            by_hand_fail[hand] += 1
        elif isinstance(item, str):
            for h in HANDS:
                if item.startswith(h):
                    by_hand_fail[h] += 1

    qfix_used = sum(1 for v in q_states.values()
                    if isinstance(v, dict) and v.get("status") in ("fixed", "qfixed"))

    return {
        "project": state.get("project", ""),
        "total_steps": len(getattr(S, "PIPELINE", [])),
        "completed_total": len(completed),
        "completed_by_hand": by_hand_done,
        "failed_total": len(failed),
        "failed_by_hand": by_hand_fail,
        "failure_records": failed,
        "qfix_used": qfix_used,
        "review": {
            "rounds_used": review.get("round", 0),
            "max_rounds": review.get("max_rounds"),
            "verdict": review.get("verdict", ""),
            "weighted_score": review.get("weighted"),
            "weak_dimensions": review.get("min_dimensions") or [],
        },
    }


def render_markdown(report: dict) -> str:
    lines = [
        f"# 赛后回顾报告 — {report['project']}",
        "",
        "> 由 `core/tools/retrospect.py` 自动生成；「经验沉淀」小节由撰写人手工补充后，",
        "> 把可复用条目归档到 `core/knowledge/_negative/` 或 `core/knowledge/pitfalls/`。",
        "",
        "## 1. 过程统计",
        "",
        f"- 完成步骤：{report['completed_total']} / {report.get('total_steps') or report['completed_total']}",
        f"- 失败记录：{report['failed_total']} 条；快速修复（qfix）使用：{report['qfix_used']} 次",
        "",
        "| 手 | 完成 | 失败 |",
        "|---|---|---|",
    ]
    for hand in HANDS:
        lines.append(
            f"| {hand} | {report['completed_by_hand'].get(hand, 0)} "
            f"| {report['failed_by_hand'].get(hand, 0)} |"
        )

    review = report["review"]
    lines += [
        "",
        "## 2. 评审与判定",
        "",
        f"- 评审轮次：{review['rounds_used']} / {review.get('max_rounds') or '?'}",
        f"- 判定：{review['verdict'] or '未评审'}；加权分：{review['weighted_score']}",
        f"- 薄弱维度：{'、'.join(review['weak_dimensions']) or '无'}",
        "",
        "## 3. 失败与返修清单",
        "",
    ]
    if report["failure_records"]:
        for rec in report["failure_records"]:
            lines.append(f"- {json.dumps(rec, ensure_ascii=False)}")
    else:
        lines.append("- 无失败记录。")

    lines += [
        "",
        "## 4. 经验沉淀（人工填写）",
        "",
        "- [ ] 最耗时的一步是哪一步？根因是什么？",
        "- [ ] 哪个门禁警告反复出现？应写成哪条规则/反模式？",
        "- [ ] 哪个候选方法被放弃？放弃理由是否值得进 `pitfalls/`？",
        "- [ ] 薄弱维度的提升动作（对应 review.weak_dimensions）：",
        "",
        "## 5. 知识库归档去向",
        "",
        "| 教训 | 归档位置 | 状态 |",
        "|---|---|---|",
        "| （示例）多起点检查遗漏导致局部最优 | `core/knowledge/pitfalls/` | 待归档 |",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="赛后回顾：汇总过程数据生成回顾报告")
    parser.add_argument("project", help="项目名（projects/ 下目录）")
    parser.add_argument("--out", help="输出路径（默认 projects/<项目>/work/RETROSPECTIVE.md）")
    args = parser.parse_args(argv)

    project_dir = ROOT / "projects" / args.project
    if not project_dir.is_dir():
        print(f"[FAIL] 项目不存在: {project_dir}", file=sys.stderr)
        return 2

    try:
        state = _load_state(project_dir)
    except FileNotFoundError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2

    report = build_report(state)
    out_path = Path(args.out) if args.out else project_dir / "work" / "RETROSPECTIVE.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown(report), encoding="utf-8")

    json_path = out_path.with_suffix(".json")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] 回顾报告: {out_path}")
    print(f"[OK] 结构化数据: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
