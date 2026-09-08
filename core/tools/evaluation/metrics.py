#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABOUTME: 项目度量数字单一真源 —— 实测扫描所有数值，写入 docs/METRICS.md
ABOUTME: --inject 模式把数字注入 README/AGENTS/ARCHITECTURE/STATUS 的标记块

用法：
    python core/tools/metrics.py              # 输出实测度量到 stdout
    python core/tools/metrics.py --write      # 写 docs/METRICS.md
    python core/tools/metrics.py --inject     # 注入标记块 + 写 METRICS.md
    python core/tools/metrics.py --check      # 注入后 git diff 应为空（幂等检测）
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# 实测扫描
# ---------------------------------------------------------------------------

def _scan_catalog():
    """从 catalog.yaml / 文件系统扫描 agent 与 hand 数量。"""
    try:
        for _c in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
            sys.path.insert(0, str(ROOT / "core" / "tools" / _c))
        from gen_runtime_manifest import load_catalog
        cat = load_catalog()
        hands = cat.get("hands", [])
        total_agents = sum(len(h.get("agents", [])) for h in hands)
        return {
            "hands": len(hands),
            "agents": total_agents,
            "hand_names": [h["name"] for h in hands],
        }
    except Exception as e:
        return {"error": str(e)}


def _scan_tools():
    """扫描 core/tools/ 下 .py 文件数量与行数。"""
    tools_dir = ROOT / "core" / "tools"
    py_files = sorted(tools_dir.glob("*.py"))
    total_lines = 0
    for f in py_files:
        try:
            total_lines += len(f.read_text(encoding="utf-8", errors="replace").splitlines())
        except Exception:
            pass
    return {"count": len(py_files), "total_lines": total_lines, "files": [f.name for f in py_files]}


def _scan_known_competitions():
    """从 new_project.py 的 known_competitions() 扫描竞赛数。"""
    try:
        for _c in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
            sys.path.insert(0, str(ROOT / "core" / "tools" / _c))
        import new_project as np_mod
        comps = np_mod.known_competitions()
        if isinstance(comps, dict):
            return {"count": len(comps), "competitions": list(comps.keys())}
        elif isinstance(comps, (list, tuple)):
            return {"count": len(comps), "competitions": list(comps)}
        else:
            return {"count": 0, "raw": str(comps)}
    except Exception as e:
        return {"error": str(e)}


def _scan_methodology():
    """扫描 methodology 目录 .md 数量。"""
    meth_dir = ROOT / "core" / "knowledge" / "methodology"
    if not meth_dir.exists():
        return {"count": 0}
    return {"count": len(list(meth_dir.glob("*.md")))}


def _run(cmd, timeout=120):
    """运行命令，返回 (returncode, stdout+stderr)。"""
    try:
        r = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:
        return -2, str(e)


def _scan_tests():
    """运行 pytest -q 并汇总（解析末行汇总行）。"""
    rc, out = _run([sys.executable, "-m", "pytest", "-q", "--tb=no"])
    lines = [l for l in out.strip().splitlines() if l.strip()]
    tail = lines[-1] if lines else ""
    p = re.search(r"(\d+) passed", tail)
    s = re.search(r"(\d+) skipped", tail)
    f = re.search(r"(\d+) failed", tail)
    return {
        "exit": rc,
        "passed": int(p.group(1)) if p else 0,
        "failed": int(f.group(1)) if f else 0,
        "skipped": int(s.group(1)) if s else 0,
        "raw_tail": tail,
    }


def _scan_gate():
    """对测试 fixture 跑 gate.py --level all，统计 [PASS]/[FAIL]/[SKIP] 与 EXIT。"""
    rc, out = _run([sys.executable, "core/tools/gate.py", "tests/fixtures/sample_incomplete_project", "--level", "all"], timeout=180)
    return {
        "exit": rc,
        "pass": out.count("[PASS]"),
        "fail": out.count("[FAIL]"),
        "skip": out.count("[SKIP]"),
    }


def _scan_validate():
    """对测试 fixture 跑 validate_project.py，统计 HARD/WARN/PASS 标记与 EXIT。"""
    rc, out = _run([sys.executable, "core/tools/validate_project.py", "--project", "tests/fixtures/sample_incomplete_project"], timeout=180)
    return {
        "exit": rc,
        "hard_fail": len(re.findall(r"^\s*HARD\s", out, re.MULTILINE)),
        "warn": len(re.findall(r"^\s*WARN\s", out, re.MULTILINE)),
        "passed": len(re.findall(r"^\s*(?:PASS|OK)\s", out, re.MULTILINE)),
    }


def _scan_validate_lib():
    """跑 validate.py（无参数，库级校验），解析汇总行。"""
    rc, out = _run([sys.executable, "core/tools/validate.py"], timeout=120)
    m = re.search(r"验证完成:\s*(\d+)\s*通过,\s*(\d+)\s*失败,\s*(\d+)\s*警告", out)
    if not m:
        return {"exit": rc, "passed": 0, "warn": 0, "fail": 0, "note": "无汇总行，需人工确认"}
    return {
        "exit": rc,
        "passed": int(m.group(1)),
        "fail": int(m.group(2)),
        "warn": int(m.group(3)),
    }


def _scan_git():
    """当前 HEAD 短 hash（数字与提交绑定）。"""
    rc, out = _run(["git", "rev-parse", "HEAD"], timeout=15)
    return {"exit": rc, "head": out.strip()[:9] if rc == 0 else "N/A"}


def _scan_traceability():
    """追溯率四口径（不在 P0 合并，仅公示）。"""
    # 1. documents.ts 口径
    # 2. validate.py 口径
    # 3. freeze_numbers.py 口径
    # 4. validate_project.py 口径
    # 简单实测部分
    code_dir = ROOT / "tests" / "fixtures" / "sample_incomplete_project" / "code"
    figures_dir = ROOT / "tests" / "fixtures" / "sample_incomplete_project" / "figures"
    return {
        "note": "追溯率四口径不在 P0 合并，需独立实测；仅公示以下脚本可计算",
        "scripts": [
            "core/tools/freeze_numbers.py tests/fixtures/sample_incomplete_project check (数字冻结口径)",
            "core/tools/validate_project.py --project tests/fixtures/sample_incomplete_project (综合校验口径)",
        ]
    }


def scan_all():
    """执行全部扫描并返回 metrics dict。"""
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds") + "Z"
    return {
        "generated_at": ts,
        "generated_by": "core/tools/metrics.py",
        "commit": _scan_git(),
        "catalog": _scan_catalog(),
        "tools": _scan_tools(),
        "known_competitions": _scan_known_competitions(),
        "methodology_docs": _scan_methodology(),
        "tests": _scan_tests(),
        "gate_cumcm2024anew": _scan_gate(),
        "validate_project_cumcm2024anew": _scan_validate(),
        "validate_library": _scan_validate_lib(),
        "traceability": _scan_traceability(),
    }


# ---------------------------------------------------------------------------
# 渲染 METRICS.md
# ---------------------------------------------------------------------------

def render_markdown(m):
    """从 metrics dict 生成 docs/METRICS.md 内容。"""
    lines = [
        "# 项目度量（单一真源 · 脚本自动生成）",
        "",
        "> **本文件由 `core/tools/metrics.py --write` 自动生成，禁止手改。**",
        f"> 最近扫描时间: `{m['generated_at']}`",
        f"> 生成脚本: `{m['generated_by']}`",
        f"> commit: `{m.get('commit', {}).get('head', 'N/A')}`",
        "",
        "---",
        "",
        "## 概览",
        "",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| 手（hands）数 | {m['catalog']['hands']} |",
        f"| agent 数 | {m['catalog']['agents']} |",
        f"| tools 脚本数 | {m['tools']['count']} |",
        f"| tools 总行数 | {m['tools']['total_lines']} |",
        f"| `known_competitions()` | {m['known_competitions'].get('count', 'N/A')} |",
        f"| methodology .md 数 | {m['methodology_docs']['count']} |",
        "",
        "## 测试（全量 pytest）",
        "",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| pytest 通过 | {m['tests']['passed']} |",
        f"| pytest 失败 | {m['tests']['failed']} |",
        f"| pytest 跳过 | {m['tests']['skipped']} |",
        f"| pytest EXIT | {m['tests']['exit']} |",
        "",
        "## 全链路门禁（测试 fixture sample_incomplete_project）",
        "",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| gate.py [PASS] | {m['gate_cumcm2024anew']['pass']} |",
        f"| gate.py [FAIL] | {m['gate_cumcm2024anew']['fail']} |",
        f"| gate.py [SKIP] | {m['gate_cumcm2024anew']['skip']} |",
        f"| gate.py EXIT | {m['gate_cumcm2024anew']['exit']} |",
        "",
        "## 项目校验（测试 fixture sample_incomplete_project）",
        "",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| validate_project HARD | {m['validate_project_cumcm2024anew']['hard_fail']} |",
        f"| validate_project WARN | {m['validate_project_cumcm2024anew']['warn']} |",
        f"| validate_project PASS | {m['validate_project_cumcm2024anew']['passed']} |",
        f"| validate_project EXIT | {m['validate_project_cumcm2024anew']['exit']} |",
        "",
        "> 口径说明：归档样例是部分样例，不承诺全绿；以上数字是命令真实输出的计数。",
        "",
        "## 库级校验",
        "",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| validate.py 通过 | {m['validate_library']['passed']} |",
        f"| validate.py 警告 | {m['validate_library']['warn']} |",
        f"| validate.py 失败 | {m['validate_library']['fail']} |",
        f"| validate.py EXIT | {m['validate_library']['exit']} |",
        "",
        "## 追溯率（四口径，待实测对比）",
        "",
        m['traceability']['note'],
        "",
        "准绳: `freeze_numbers.py`。其他口径需独立实测后补全对比表。",
        "",
        "---",
        "",
        "## agent 详单",
        "",
        "| 手 | agents |",
        "|-----|--------|",
    ]
    for h_name in m["catalog"]["hand_names"]:
        # find agents for this hand
        try:
            for _c in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
                sys.path.insert(0, str(ROOT / "core" / "tools" / _c))
            from gen_runtime_manifest import load_catalog
            cat = load_catalog()
            hand = next((x for x in cat["hands"] if x["name"] == h_name), {})
            agents = hand.get("agents", [])
            names = ", ".join(a["name"] for a in agents)
            lines.append(f"| {h_name} | {names} |")
        except Exception:
            lines.append(f"| {h_name} | (扫描失败) |")

    lines += [
        "",
        "---",
        "",
        "*文件末尾*",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# --inject: 标记块回填
# ---------------------------------------------------------------------------

METRIC_TAG = "<!-- METRICS:INSERT -->"

METRIC_SNIPPETS = {
    "README.md": {
        "tag": "<!-- METRICS:README -->",
        "content": (
            "项目度量详见 [docs/METRICS.md](docs/METRICS.md)（单一真源，脚本自动生成）。\n"
        ),
    },
    "AGENTS.md": {
        "tag": "<!-- METRICS:AGENTS -->",
        "content": (
            "项目度量详见 [docs/METRICS.md](docs/METRICS.md)（单一真源，脚本自动生成）。\n"
        ),
    },
    "docs/ARCHITECTURE.md": {
        "tag": "<!-- METRICS:ARCH -->",
        "content": (
            "项目度量详见 [docs/METRICS.md](docs/METRICS.md)（单一真源，脚本自动生成）。\n"
        ),
    },
    "docs/STATUS.md": {
        "tag": "<!-- METRICS:STATUS -->",
        "content": (
            "项目度量详见 [docs/METRICS.md](docs/METRICS.md)（单一真源，脚本自动生成）。\n"
        ),
    },
}


def inject_metrics(metrics_text):
    """把标记块写进各文档，替换过期数字散文。"""
    # 先把 metrics 摘要词也写进 METRICS.md
    metrics_path = ROOT / "docs" / "METRICS.md"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(metrics_text, encoding="utf-8")

    replaced = []
    for rel_path, cfg in METRIC_SNIPPETS.items():
        f = ROOT / rel_path
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        tag = cfg["tag"]
        if tag in text:
            # replace whole tagged block
            text = re.sub(
                re.escape(tag) + r".*?" + re.escape(tag),
                tag + "\n" + cfg["content"] + tag,
                text, flags=re.DOTALL
            )
            f.write_text(text, encoding="utf-8")
            replaced.append(rel_path)
    return replaced


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="项目度量单一真源（实测扫描 → docs/METRICS.md）")
    ap.add_argument("--write", action="store_true", help="写 docs/METRICS.md")
    ap.add_argument("--inject", action="store_true", help="注入标记块 + 写 METRICS.md")
    ap.add_argument("--check", action="store_true", help="注入后 git diff --exit-code 幂等检测")
    args = ap.parse_args()

    if not any([args.write, args.inject, args.check]):
        m = scan_all()
        print(json.dumps(m, ensure_ascii=False, indent=2))
        return 0

    if args.write or args.inject:
        m = scan_all()
        md = render_markdown(m)
        mp = ROOT / "docs" / "METRICS.md"
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text(md, encoding="utf-8")
        print(f"[metrics] docs/METRICS.md 已生成（{m['generated_at']}）")
        if args.inject:
            replaced = inject_metrics(md)
            print(f"[metrics] 已注入标记块到: {replaced}")

    if args.check:
        # 幂等检测：注入后再次运行，diff 应为空
        import subprocess
        r = subprocess.run(
            ["git", "diff", "--exit-code"],
            cwd=str(ROOT), capture_output=True, text=True)
        if r.returncode == 0:
            print("[metrics] --check 幂等通过：无 diff")
            return 0
        print("[metrics] --check 失败：存在 diff")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
