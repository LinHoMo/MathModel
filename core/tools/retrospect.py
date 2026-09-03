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
from datetime import datetime
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


def _parse_ts(ts_str):
    """解析 ISO8601 时间戳字符串为 datetime。失败返回 None。"""
    if not ts_str or not isinstance(ts_str, str):
        return None
    try:
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def _calc_timing(completed: list[dict]) -> dict:
    """从 completed 的时间戳列表计算各阶段耗时统计。

    每个 completed 项含 hand/agent/stimestamp。按 pipeline 顺序相邻项的时间差
    即该 agent 的"主观耗时"（记录 agent runtime 完成间隔，非 CPU 时间）。
    """
    timed = []
    for item in completed:
        ts = _parse_ts(item.get("timestamp", ""))
        if ts:
            timed.append({**item, "_ts": ts})
    timed.sort(key=lambda x: x["_ts"])

    per_agent = []
    prev_ts = None
    prev_label = None
    for item in timed:
        cur_ts = item["_ts"]
        label = f"{item.get('hand','?')}/{item.get('agent','?')}"
        gap = round((cur_ts - prev_ts).total_seconds(), 1) if prev_ts else 0.0
        per_agent.append({
            "hand": item.get("hand"),
            "agent": item.get("agent"),
            "timestamp": item.get("timestamp"),
            "gap_seconds": gap,
        })
        prev_ts, prev_label = cur_ts, label

    total_wall = 0.0
    if len(timed) >= 2:
        total_wall = round((timed[-1]["_ts"] - timed[0]["_ts"]).total_seconds(), 1)
    elif timed:
        total_wall = 0.0

    # 按手聚合
    hand_gaps: dict[str, float] = {h: 0.0 for h in HANDS}
    for p in per_agent:
        h = p["hand"]
        if h in hand_gaps:
            hand_gaps[h] = round(hand_gaps[h] + p["gap_seconds"], 1)

    # 最慢的前 5 步
    top5 = sorted(per_agent, key=lambda x: x["gap_seconds"], reverse=True)[:5]

    return {
        "total_wall_seconds": total_wall,
        "timed_steps": len(timed),
        "hand_wall_seconds": hand_gaps,
        "slowest_steps": top5,
        "per_agent": per_agent,
    }


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

    timing = _calc_timing(completed)
    prev_ts_list = [c.get("timestamp") for c in completed if c.get("timestamp")]
    first_ts = prev_ts_list[0] if prev_ts_list else None
    last_ts = prev_ts_list[-1] if prev_ts_list else None

    return {
        "project": state.get("project", ""),
        "total_steps": len(getattr(S, "PIPELINE", [])),
        "completed_total": len(completed),
        "completed_by_hand": by_hand_done,
        "failed_total": len(failed),
        "failed_by_hand": by_hand_fail,
        "failure_records": failed,
        "qfix_used": qfix_used,
        "timing": timing,
        "first_completed_ts": first_ts,
        "last_completed_ts": last_ts,
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
    timing = report.get("timing") or {}
    lines += [
        "",
        "## 2. 时序与耗时",
        "",
    ]
    if timing.get("timed_steps", 0) >= 2:
        dur_min = round(timing.get("total_wall_seconds", 0) / 60, 1)
        lines += [
            f"- 全流程墙钟时间：**{timing['total_wall_seconds']} s** ({dur_min} min)",
            f"- 有记录步数：{timing['timed_steps']} / {len(report.get('per_agent',[]) or [])}",
            f"- 起点：{report.get('first_completed_ts', '')}",
            f"- 终点：{report.get('last_completed_ts', '')}",
            "",
            "| 手 | 累计耗时 (s) |",
            "|---|---|",
        ]
        hw = timing.get("hand_wall_seconds", {})
        for hand in HANDS:
            lines.append(f"| {hand} | {hw.get(hand, 0)} |")
        top5 = timing.get("slowest_steps", [])
        if top5:
            lines += ["", "### 最慢 5 步", ""]
            for i, p in enumerate(top5, 1):
                lines.append(f"{i}. `{p['hand']}/{p['agent']}` — {p['gap_seconds']} s")
    else:
        lines += ["- 尚未有足够时序记录（需 ≥ 2 个带时间戳的完成步骤）。"]

    lines += [
        "",
        "## 3. 评审与判定",
        "",
        f"- 评审轮次：{review['rounds_used']} / {review.get('max_rounds') or '?'}",
        f"- 判定：{review['verdict'] or '未评审'}；加权分：{review['weighted_score']}",
        f"- 薄弱维度：{'、'.join(review['weak_dimensions']) or '无'}",
        "",
        "## 4. 失败与返修清单",
        "",
    ]
    if report["failure_records"]:
        for rec in report["failure_records"]:
            lines.append(f"- {json.dumps(rec, ensure_ascii=False)}")
    else:
        lines.append("- 无失败记录。")

    lines += [
        "",
        "## 5. 经验沉淀（人工填写）",
        "",
        "- [ ] 最耗时的一步是哪一步？根因是什么？",
        "- [ ] 哪个门禁警告反复出现？应写成哪条规则/反模式？",
        "- [ ] 哪个候选方法被放弃？放弃理由是否值得进 `pitfalls/`？",
        "- [ ] 薄弱维度的提升动作（对应 review.weak_dimensions）：",
        "",
        "## 6. 知识库归档去向",
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
