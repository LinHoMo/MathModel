#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 使用台账与披露生成器 —— 合规刚需，P2-1 最高优先级。

为什么必须有
------------
* CUMCM（全国大学生数学建模竞赛）要求提交 AI 使用支撑材料
* MCM/ICM（美赛）要求 AI Use Report 随论文一起提交
* 电工杯等赛事同样有披露要求

没有这个，作品可能因"未披露 AI 使用"被直接判违规——
这不属于体验问题，是能不能参赛的问题。

用法
----
    # 记录一条使用
    python core/tools/render_ai_usage.py <项目> add \
        --stage modeler/model-builder --tool "Claude Opus" \
        --purpose "推导螺线弧长公式" \
        --adopted "式(3)-(7)，已手工复核" \
        --reviewed yes

    # 生成披露材料
    python core/tools/render_ai_usage.py <项目> render --competition cumcm
    python core/tools/render_ai_usage.py <项目> render --competition mcm

    # 查看台账
    python core/tools/render_ai_usage.py <项目> show

产出
----
* cumcm  → projects/<项目>/support_materials/ai_usage_disclosure.md
* mcm    → projects/<项目>/paper/ai_usage_report.md（自动接入主模板）
* 其他   → projects/<项目>/support_materials/ai_usage_disclosure.md

台账存于 projects/<项目>/work/ai_usage_ledger.json，
并同步到 state.json 的 ai_usage_ledger 字段（单一事实源）。
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core" / "tools"))
for _cat in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
    sys.path.insert(0, str(ROOT / "core" / "tools" / _cat))

import state as S  # noqa: E402

LEDGER_REL = "work/ai_usage_ledger.json"

COMPETITIONS = {
    "cumcm": {
        "name": "全国大学生数学建模竞赛（CUMCM）",
        "lang": "zh",
        "out": "deliverables/ai_usage_disclosure.md",
        "note": "按当届通知要求，将本材料（编译后的「AI工具使用详情.pdf」）"
                "作为支撑材料随论文提交；若明确未使用 AI，则按通知要求提交正文声明。",
    },
    "mcm": {
        "name": "MCM/ICM（美赛）",
        "lang": "en",
        "out": "paper/ai_usage_report.md",
        "note": "COMAP 要求 AI Use Report 随论文提交，本文件需接入主模板。",
    },
    "diangong": {
        "name": "电工杯数学建模竞赛",
        "lang": "zh",
        "out": "deliverables/ai_usage_disclosure.md",
        "note": "官网暂无专门 AI 格式要求，仍建议随支撑材料一并提交。",
    },
    "huawei": {
        "name": "华为杯研究生数学建模竞赛",
        "lang": "zh",
        "out": "deliverables/ai_usage_disclosure.md",
        "note": "按当届通知核对披露要求。",
    },
}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ledger_path(project):
    return S.project_dir(project) / LEDGER_REL


def load_ledger(project):
    p = ledger_path(project)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": "1.0", "project": str(S.project_dir(project).name),
            "created": _now(), "entries": []}


def save_ledger(project, ledger):
    p = ledger_path(project)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")
    # 同步到 state.json（单一事实源）
    st = S.load(project)
    if st is not None:
        st["ai_usage_ledger"] = {
            "count": len(ledger["entries"]),
            "updated": _now(),
        }
        S.save(project, st)
    return p


def cmd_add(project, args):
    lg = load_ledger(project)
    lg["entries"].append({
        "timestamp": _now(),
        "stage": args.stage,
        "tool": args.tool,
        "purpose": args.purpose,
        "adopted": args.adopted or "",
        "reviewed": args.reviewed,
        "reviewer": args.reviewer or "",
    })
    save_ledger(project, lg)
    print(f"[ai-usage] 已记录 {args.stage}（共 {len(lg['entries'])} 条）")
    return 0


def cmd_show(project, args):
    lg = load_ledger(project)
    if not lg["entries"]:
        print("[ai-usage] 台账为空")
        return 0
    print(f"项目: {lg.get('project')}   记录数: {len(lg['entries'])}\n")
    for i, e in enumerate(lg["entries"], 1):
        print(f"{i}. [{e['stage']}] {e['tool']}")
        print(f"   用途: {e['purpose']}")
        if e["adopted"]:
            print(f"   采用: {e['adopted']}")
        print(f"   人工复核: {e['reviewed']}{' / ' + e['reviewer'] if e['reviewer'] else ''}")
    return 0


def _render_zh(project, lg, comp):
    entries = lg["entries"]
    L = [
        "# AI 使用情况说明",
        "",
        f"- **竞赛**：{comp['name']}",
        f"- **参赛项目**：{lg.get('project')}",
        f"- **生成时间**：{_now()}",
        f"- **记录条数**：{len(entries)}",
        "",
        "> 本材料由 `core/tools/render_ai_usage.py` 自动生成，",
        "> 内容源自 `work/ai_usage_ledger.json` 台账。",
        "> 提交前请逐条核对，并对 AI 生成内容承担全部责任。",
        "",
    ]

    if not entries:
        L += [
            "## 声明",
            "",
            "本队在本次竞赛的建模、求解与撰写过程中**未使用**人工智能工具。",
            "",
            "（若实际有使用，请先运行 `python core/tools/render_ai_usage.py <项目> add ...` 登记后再重新生成本材料。）",
            "",
        ]
        return "\n".join(L)

    reviewed = sum(1 for e in entries if str(e.get("reviewed", "")).lower()
                   in ("yes", "y", "是", "true"))
    L += [
        "## 一、总体情况",
        "",
        f"本队在本次竞赛中使用人工智能工具辅助完成部分工作，共记录 {len(entries)} 项，"
        f"其中 {reviewed} 项已经人工复核确认。",
        "",
        "**责任声明**：论文中的全部公式、代码、数据、事实与引用，"
        "均由本队成员逐一复核并负责。AI 生成内容仅作为辅助参考，"
        "未经复核不得作为结论依据。",
        "",
        "## 二、逐项说明",
        "",
        "| # | 使用环节 | 工具 | 用途 | 采用内容 | 人工复核 |",
        "|---|---|---|---|---|---|",
    ]
    for i, e in enumerate(entries, 1):
        rv = e.get("reviewed", "")
        rv = "是" if str(rv).lower() in ("yes", "y", "是", "true") else "否"
        if e.get("reviewer"):
            rv += f"（{e['reviewer']}）"
        L.append(
            f"| {i} | {e.get('stage','')} | {e.get('tool','')} | "
            f"{e.get('purpose','')} | {e.get('adopted','') or '—'} | {rv} |"
        )

    L += [
        "",
        "## 三、使用边界",
        "",
        "本队在以下环节**未**使用 AI 替代人工判断：",
        "",
        "1. 赛题理解与方法选择——由队员讨论确定；",
        "2. 模型假设的合理性判断——由队员依据物理与数学依据确定；",
        "3. 结论的可靠性评估——由队员结合灵敏度分析与误差分析给出；",
        "4. 最终署名与提交——由队员本人完成。",
        "",
        "## 四、备注",
        "",
        comp["note"],
        "",
        "> 提醒：竞赛规则每年可能变化，提交前必须以当届官方通知为准。",
    ]
    return "\n".join(L)


def _render_en(project, lg, comp):
    entries = lg["entries"]
    L = [
        "# AI Use Report",
        "",
        f"- **Contest**: {comp['name']}",
        f"- **Team project**: {lg.get('project')}",
        f"- **Generated**: {_now()}",
        f"- **Entries**: {len(entries)}",
        "",
        "> Generated by `core/tools/render_ai_usage.py` from `work/ai_usage_ledger.json`.",
        "> Review every entry before submission; the team remains fully "
        "responsible for all formulas, code, data, facts, and citations.",
        "",
    ]

    if not entries:
        L += [
            "## Statement",
            "",
            "No AI tools were used in the modeling, solution, or writing "
            "of this submission.",
            "",
        ]
        return "\n".join(L)

    L += [
        "## Usage log",
        "",
        "| # | Stage | Tool | Purpose | Adopted content | Human review |",
        "|---|---|---|---|---|---|",
    ]
    for i, e in enumerate(entries, 1):
        rv = str(e.get("reviewed", "")).lower()
        rv = "Yes" if rv in ("yes", "y", "是", "true") else "No"
        L.append(
            f"| {i} | {e.get('stage','')} | {e.get('tool','')} | "
            f"{e.get('purpose','')} | {e.get('adopted','') or '—'} | {rv} |"
        )

    L += [
        "",
        "## Boundaries",
        "",
        "AI tools were **not** used to replace human judgment in:",
        "",
        "1. Problem interpretation and method selection;",
        "2. Assessment of modeling assumptions;",
        "3. Evaluation of result reliability (sensitivity and error analysis);",
        "4. Final authorship and submission.",
        "",
        "## Note",
        "",
        comp["note"],
        "",
        "> Contest rules change yearly — always verify against the "
        "current official instructions before submitting.",
    ]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# 国赛支撑材料 LaTeX 源生成（编译后即为「AI工具使用详情.pdf」）
# ---------------------------------------------------------------------------
def _ai_report_name():
    """支撑材料文件名，取自 env: deliverables.ai_report_name（可插拔）。"""
    try:
        import sys as _s
        _s.path.insert(0, str(ROOT / "core"))
        from env.loader import get
        return str(get("deliverables.ai_report_name", default="AI工具使用详情")
                   or "AI工具使用详情")
    except Exception:
        return "AI工具使用详情"


def _escape_tex(s):
    """转义 LaTeX 特殊字符，避免披露文档编译失败。"""
    if not isinstance(s, str):
        s = str(s)
    return (s.replace("\\", r"\textbackslash ")
             .replace("&", r"\&").replace("%", r"\%").replace("$", r"\$")
             .replace("#", r"\#").replace("_", r"\_").replace("{", r"\{")
             .replace("}", r"\}").replace("^", r"\^{}").replace("~", r"\~{}"))


def _render_disclosure_tex(project, lg, comp):
    """生成支撑材料 LaTeX 源（与 _render_zh 内容对齐）。"""
    name = _ai_report_name()
    entries = lg["entries"]
    L = [
        r"\documentclass[UTF8, 11pt]{ctexart}",
        r"\usepackage[margin=2.5cm]{geometry}",
        r"\begin{document}",
        r"\section*{AI 使用情况说明}",
        "",
        f"竞赛：{_escape_tex(comp['name'])}",
        "",
        f"参赛项目：{_escape_tex(str(lg.get('project')))}",
        "",
        f"记录条数：{len(entries)}",
        "",
    ]
    if not entries:
        L += [
            "本队在本次竞赛的建模、求解与撰写过程中未使用人工智能工具。",
            "",
        ]
    else:
        reviewed = sum(1 for e in entries
                       if str(e.get("reviewed", "")).lower() in ("yes", "y", "是", "true"))
        L += [
            f"本队在本次竞赛中使用人工智能工具辅助完成部分工作，共记录 "
            f"{len(entries)} 项，其中 {reviewed} 项已人工复核确认。",
            "",
            "责任声明：论文中的全部公式、代码、数据、事实与引用，"
            "均由本队成员逐一复核并负责。AI 生成内容仅作辅助参考，未经复核不得作为结论依据。",
            "",
            r"\begin{tabular}{c|c|c|c|c|c}",
            "序号 & 环节 & 工具 & 用途 & 采用内容 & 人工复核 \\\\",
            r"\hline",
        ]
        for i, e in enumerate(entries, 1):
            rv = e.get("reviewed", "")
            rv = "是" if str(rv).lower() in ("yes", "y", "是", "true") else "否"
            if e.get("reviewer"):
                rv += f"（{e['reviewer']}）"
            L.append(" & ".join([
                str(i),
                _escape_tex(str(e.get("stage", ""))),
                _escape_tex(str(e.get("tool", ""))),
                _escape_tex(str(e.get("purpose", ""))),
                _escape_tex(str(e.get("adopted", "") or "—")),
                rv,
            ]) + r" \\")
        L.append(r"\hline")
        L.append(r"\end{tabular}")
        L.append("")
        L.append("使用边界：本队在赛题理解与方法选择、假设合理性判断、"
                 "结论可靠性评估、最终署名与提交环节，未使用 AI 替代人工判断。")
        L.append("")
    L.append(_escape_tex(comp.get("note", "")))
    L.append("")
    L.append(r"\end{document}")
    return "\n".join(L)


def _emit_disclosure_pdf(project, lg, comp):
    """写出支撑材料 .tex 并尽力编译为「AI工具使用详情.pdf」到 deliverables/。"""
    name = _ai_report_name()
    tex = S.project_dir(project) / "deliverables" / f"{name}.tex"
    tex.parent.mkdir(parents=True, exist_ok=True)
    tex.write_text(_render_disclosure_tex(project, lg, comp) + "\n", encoding="utf-8")
    print(f"[ai-usage] 已生成支撑材料源 {tex}")
    xelatex = shutil.which("xelatex")
    if not xelatex:
        print("[ai-usage] 环境无 xelatex：未生成 PDF（.tex 已生成，可在有 TeX 环境处编译）")
        return
    try:
        r = subprocess.run(
            [xelatex, "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
            cwd=str(tex.parent), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120)
        pdf = tex.with_suffix(".pdf")
        if r.returncode == 0 and pdf.exists():
            print(f"[ai-usage] 已编译支撑材料 PDF {pdf}")
        else:
            print("[ai-usage] xelatex 编译支撑材料失败（.tex 已生成，请检查后手动编译）")
    except subprocess.TimeoutExpired:
        print("[ai-usage] 支撑材料编译超时（.tex 已生成）")


def cmd_render(project, args):
    comp = COMPETITIONS.get(args.competition)
    if not comp:
        print(f"[ai-usage] 未知竞赛: {args.competition}", file=sys.stderr)
        print(f"  可选: {', '.join(COMPETITIONS)}", file=sys.stderr)
        return 2

    lg = load_ledger(project)
    text = (_render_en if comp["lang"] == "en" else _render_zh)(project, lg, comp)

    out = S.project_dir(project) / comp["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")

    print(f"[ai-usage] 已生成 {out}")
    print(f"[ai-usage] 竞赛: {comp['name']}   记录数: {len(lg['entries'])}")
    if args.competition == "mcm":
        print("[ai-usage] 请将本文件接入 paper/main.tex 主模板")
    elif args.competition == "cumcm":
        # 国赛要求支撑材料 PDF 命名为「AI工具使用详情」，随论文提交
        _emit_disclosure_pdf(project, lg, comp)
    return 0


def main():
    ap = argparse.ArgumentParser(description="AI 使用台账与披露生成器")
    ap.add_argument("project")
    ap.add_argument("command", choices=["add", "show", "render"])
    ap.add_argument("--stage", help="使用环节，如 modeler/model-builder")
    ap.add_argument("--tool", help="工具名与版本，如 Claude Opus")
    ap.add_argument("--purpose", help="用途")
    ap.add_argument("--adopted", help="实际采用的内容")
    ap.add_argument("--reviewed", default="no", help="是否人工复核：yes/no")
    ap.add_argument("--reviewer", help="复核人")
    ap.add_argument("--competition", default="cumcm",
                    choices=list(COMPETITIONS))
    args = ap.parse_args()

    fn = {"add": cmd_add, "show": cmd_show, "render": cmd_render}[args.command]
    return fn(args.project, args)


if __name__ == "__main__":
    sys.exit(main())
