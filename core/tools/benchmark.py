#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""benchmark.py — 引擎演练与题库健康检查

借鉴 MM-Bench 理念，用脚本化方式回答两个问题：
1. `pipeline`: 引擎对某个竞赛包能否健康开工？（临时项目脚手架 → state init → doctor → 清理）
2. `library`:  赛题库索引是否完整？（年份覆盖、待补标记、已核实题名数）

用法:
    python core/tools/benchmark.py pipeline --competition cumcm [--problem <文件>] [--keep]
    python core/tools/benchmark.py library
    （任一模式加 --json 输出机器可读结果）

零第三方依赖。pipeline 模式的临时项目命名 `_bench-*`，结束后自动删除。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import new_project  # noqa: E402


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def pipeline_report(competition: str, problem: str | None = None,
                    keep: bool = False) -> dict:
    """开工演练：脚手架 → state init → doctor → 清理。返回每步结果。"""
    proj = f"bench-{competition}-{int(time.time())}"
    report: dict = {
        "mode": "pipeline", "competition": competition,
        "project": proj, "steps": {}, "cleaned": False,
    }
    problem_files = [problem] if problem else []
    try:
        try:
            new_project.scaffold(proj, competition, problem_files)
            report["steps"]["scaffold"] = "PASS"
        except ValueError as exc:
            report["steps"]["scaffold"] = f"FAIL: {exc}"
            return report

        py = sys.executable
        for step, cmd in (
            ("state_init", [py, "core/tools/state.py", proj, "init"]),
            ("state_status", [py, "core/tools/state.py", proj, "status"]),
            ("doctor", [py, "core/tools/doctor.py",
                        "--project", proj, "--competition", competition]),
        ):
            try:
                rc, out = _run(cmd, ROOT)
                report["steps"][step] = "PASS" if rc == 0 else f"FAIL(rc={rc})"
                if rc != 0:
                    report["steps"][f"{step}_detail"] = out[-800:]
            except Exception as exc:  # noqa: BLE001 - 演练要汇总所有失败
                report["steps"][step] = f"ERROR: {exc}"
        return report
    finally:
        bench_dir = ROOT / "projects" / proj
        if keep:
            report["cleaned"] = False
            report["kept_at"] = str(bench_dir)
        elif bench_dir.exists():
            shutil.rmtree(bench_dir, ignore_errors=True)
            report["cleaned"] = not bench_dir.exists()


def library_report() -> dict:
    """赛题库健康检查：INDEX.md 年份覆盖 + 待补标记 + MCM 已核实题名。"""
    report: dict = {"mode": "library", "cumcm": {}, "mcm": {}}
    index = ROOT / "core" / "knowledge" / "problems" / "INDEX.md"
    if index.exists():
        text = index.read_text(encoding="utf-8")
        years = re.findall(r"^## (\d{4}) 年", text, flags=re.M)
        rows = [ln for ln in text.splitlines()
                if re.match(r"^\|\s*\d{4}\s*\|", ln)]
        report["cumcm"] = {
            "years_covered": sorted(set(years)),
            "entries": len(rows),
            "pending_marks": text.count("（待补）"),
        }
    else:
        report["cumcm"] = {"error": f"缺失: {index}"}

    mcm = ROOT / "core" / "knowledge" / "problems" / "MCM-ICM.md"
    if mcm.exists():
        text = mcm.read_text(encoding="utf-8")
        verified = [ln for ln in text.splitlines()
                    if re.match(r"^\|\s*\d{4}\s*\|\s*(MCM|ICM)", ln)]
        report["mcm"] = {
            "verified_titles": len(verified),
            "pending_marks": text.count("（待核实后补充）") + text.count("待补"),
        }
    else:
        report["mcm"] = {"error": f"缺失: {mcm}"}
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="引擎演练与题库健康检查")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_pipe = sub.add_parser("pipeline", help="竞赛开工演练（临时项目，自动清理）")
    p_pipe.add_argument("--competition", required=True)
    p_pipe.add_argument("--problem", help="可选赛题文件")
    p_pipe.add_argument("--keep", action="store_true", help="保留临时项目不清理")
    p_pipe.add_argument("--json", action="store_true", dest="as_json",
                        help="输出机器可读 JSON")

    p_lib = sub.add_parser("library", help="赛题库健康检查")
    p_lib.add_argument("--json", action="store_true", dest="as_json",
                       help="输出机器可读 JSON")

    args = parser.parse_args(argv)

    if args.mode == "pipeline":
        report = pipeline_report(args.competition, args.problem, args.keep)
    else:
        report = library_report()

    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.mode == "pipeline":
        steps = report["steps"]
        failed = [k for k, v in steps.items()
                  if not k.endswith("_detail") and not str(v).startswith("PASS")]
        return 1 if failed else 0
    return 0 if "error" not in report.get("cumcm", {}) else 1


if __name__ == "__main__":
    raise SystemExit(main())
