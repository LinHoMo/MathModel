#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""benchmark.py — 引擎演练 / 题库健康检查 / 国赛复盘基准

借鉴 MM-Bench 理念，用脚本化方式回答三类问题：
1. `pipeline`: 引擎对某个竞赛包能否健康开工？（临时项目脚手架 → state init → doctor → 清理）
2. `library`:  赛题库索引是否完整？（年份覆盖、待补标记、已核实题名数）
3. `bench`:    国赛复盘基准（rubric 列表 / run 模板 / 打分重算 / 报告）

    bench list                列出所有 rubric 文件
    bench run --rubrict 打印 agent 调用模板（不调用 LLM）
    bench score --rubric <f> --response <f>   重算校验响应 JSON
    bench report --rubric <f> --response <f>  生成人类可读报告

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


# ---------------------------------------------------------------------------
# bench 子命令：国赛复盘基准
# ---------------------------------------------------------------------------

BENCH_DIR = ROOT / "core" / "knowledge" / "bench" / "cumcm"
RUBRIC_GLOB = "rubric_*.json"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"_error": f"无法解析 {path}: {exc}"}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def bench_list(as_json: bool = False) -> dict:
    """列出所有可用 rubric 文件。"""
    rubrics = sorted(BENCH_DIR.glob(RUBRIC_GLOB)) if BENCH_DIR.exists() else []
    items = []
    for r in rubrics:
        d = _load_json(r)
        items.append({
            "file": f"core/knowledge/bench/cumcm/{r.name}",
            "year": d.get("year"),
            "topic": d.get("topic"),
            "title": d.get("title", ""),
            "source": d.get("source", ""),
            "total_score": d.get("total_score"),
            "dimensions": len(d.get("dimensions", [])),
        })
    report = {"mode": "bench_list", "count": len(items), "rubrics": items}
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def bench_run(rubric_file: str) -> dict:
    """打印 agent 调用模板（本库不自带 LLM，仅给 prompt 骨架）。"""
    rubric_path = Path(rubric_file)
    if not rubric_path.is_absolute():
        rubric_path = ROOT / rubric_file
    if not rubric_path.exists():
        return {"_error": f"rubric 不存在: {rubric_file}"}

    rubric = _load_json(rubric_path)
    if "_error" in rubric:
        return rubric

    # 生成 response 模板，供 agent runtime 按 SKILL.md 主观填写
    template = {
        "competition": "cumcm",
        "year": rubric.get("year"),
        "topic": rubric.get("topic"),
        "rubric_ref": f"core/knowledge/bench/cumcm/{rubric_path.name}",
        "response_summary": {
            "modeled_problems": [],
            "claimed_results_count": 0,
            "approach_summary": ""
        },
        "dimension_scores": [
            {
                "dimension_id": d.get("id"),
                "awarded": 0,
                "max_score": d.get("max_score", 0),
                "rationale": "",
                "ground_truth_hits": 0,
                "ground_truth_misses": 0
            }
            for d in rubric.get("dimensions", [])
        ],
        "total": {"awarded": 0, "max_score": rubric.get("total_score", 100), "pct": 0},
        "flags": [],
        "generated_by": "bench_run_template",
        "generated_at": "",
    }

    year = rubric.get("year")
    topic = rubric.get("topic")
    out_path = ROOT / "projects" / f"_bench_{year}{topic}" / "bench_response_template.json"
    _save_json(out_path, template)

    print(f"# Rubric: {year} {topic} — {rubric.get('title', '')}")
    print(f"# 维度数: {len(rubric.get('dimensions', []))}")
    print(f"# 满分:   {rubric.get('total_score', 100)}")
    print()
    print("## Agent 调用步骤")
    print(f"1. 读取本 rubric 文件: core/knowledge/bench/cumcm/{rubric_path.name}")
    print("2. 根据其 dimensions[].assessment_points 对回答逐项评分")
    print("3. 对比 reference_results 标注 ground_truth_hits/misses")
    print("4. 写出 bench_response.json，字段对齐 bench_result.schema.json")
    print()
    print(f"## 模板已写入: {out_path}")
    print("## 下一步: python core/tools/benchmark.py bench score --rubric <f> --response <f>")

    return template


def bench_score(rubric_file: str, response_file: str, as_json: bool = False) -> dict:
    """重算校验：对齐 rubric 与 agent 响应，校验维度分不超过 max_score，汇总总分。"""
    r_path = Path(rubric_file) if Path(rubric_file).is_absolute() else ROOT / rubric_file
    p_path = Path(response_file) if Path(response_file).is_absolute() else ROOT / response_file

    rubric = _load_json(r_path)
    response = _load_json(p_path)

    errors: list[str] = []
    if "_error" in rubric:
        return rubric
    if "_error" in response:
        return response

    max_map = {d["id"]: d.get("max_score", 0) for d in rubric.get("dimensions", [])}
    ref_map: dict[str, list] = {}
    for d in rubric.get("dimensions", []):
        ref_map[d["id"]] = d.get("reference_results", [])

    total_awarded = 0.0
    total_max = rubric.get("total_score", 100)
    dim_reports = []

    for ds in response.get("dimension_scores", []):
        did = ds.get("dimension_id", "?")
        awarded = float(ds.get("awarded", 0))
        max_s = max_map.get(did, float(ds.get("max_score", 0)))

        issues: list[str] = []
        if awarded > max_s + 1e-9:
            issues.append(f"维度 {did} 得分 {awarded} 超过满分 {max_s}，按 {max_s} 截断")
            awarded = max_s
        if awarded < 0:
            issues.append(f"维度 {did} 得分为负 {awarded}，按 0 截断")
            awarded = 0

        # ground-truth 命中率统计
        hits = int(ds.get("ground_truth_hits", 0))
        refs = ref_map.get(did, [])
        expected = len(refs)
        if expected > 0 and hits > expected:
            issues.append(f"维度 {did} hits {hits} > 参考结果数 {expected}")

        total_awarded += awarded
        dim_reports.append({
            "dimension_id": did,
            "awarded": awarded,
            "max_score": max_s,
            "ground_truth_hits": hits,
            "ground_truth_expected": expected,
            "issues": issues,
        })

    # 检查 total 一致性
    declared_total = float(response.get("total", {}).get("awarded", 0))
    if abs(declared_total - total_awarded) > 0.5:
        errors.append(f"声明总分 {declared_total} 与重算合计 {total_awarded} 不一致（差 {abs(declared_total - total_awarded):.2f}）")

    pct = round(total_awarded / total_max * 100, 2) if total_max > 0 else 0.0
    passed = len(errors) == 0

    report = {
        "mode": "bench_score",
        "rubric": str(rubric_file),
        "response": str(response_file),
        "summary": {
            "total_awarded": round(total_awarded, 2),
            "total_max": total_max,
            "pct": pct,
            "dimensions_scored": len(dim_reports),
            "checks_passed": passed,
        },
        "dimensions": dim_reports,
        "errors": errors,
        "flags": response.get("flags", []),
    }
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def bench_report(rubric_file: str, response_file: str) -> str:
    """生成人类可读的复盘报告文本。"""
    r_path = Path(rubric_file) if Path(rubric_file).is_absolute() else ROOT / rubric_file
    rubric = _load_json(r_path)
    score = bench_score(rubric_file, response_file, as_json=True)

    if "_error" in score:
        return f"# 错误\n{score['_error']}"

    lines: list[str] = []
    lines.append(f"# 国赛复盘报告：{rubric.get('year', '?')} 年 {rubric.get('topic', '?')} 题")
    lines.append(f"**题目**: {rubric.get('title', '')}")
    lines.append(f"**Rubric 来源**: {rubric.get('source', '')}  ")
    snote = rubric.get("source_note", "")
    if snote:
        lines.append(f"**来源备注**: {snote}")
    s = score["summary"]
    lines.append(f"**总分**: {s['total_awarded']} / {s['total_max']}  ({s['pct']}%)")
    lines.append(f"**维度数**: {s['dimensions_scored']}")
    lines.append(f"**校验**: {'通过' if s['checks_passed'] else '未通过'}")
    lines.append("")
    lines.append("## 维度明细")
    lines.append("")
    lines.append("| 维度 | 得分 / 满分 | GT 命中 / 预期 | 问题 |")
    lines.append("|---|---|---|---|")
    for d in score["dimensions"]:
        iss = "; ".join(d["issues"]) if d["issues"] else "—"
        lines.append(f"| {d['dimension_id']} | {d['awarded']} / {d['max_score']} | "
                     f"{d['ground_truth_hits']} / {d['ground_truth_expected']} | {iss} |")
    if score["flags"]:
        lines.append("")
        lines.append("## 缺陷旗标")
        for f in score["flags"]:
            lines.append(f"- {f}")
    if score["errors"]:
        lines.append("")
        lines.append("## 校验错误")
        for e in score["errors"]:
            lines.append(f"- ⚠ {e}")
    lines.append("")

    text = "\n".join(lines)
    print(text)
    return text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="引擎演练 / 题库健康 / 国赛复盘基准")
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

    p_bench = sub.add_parser("bench", help="国赛复盘基准（list/run/score/report）")
    bench_sub = p_bench.add_subparsers(dest="bench_cmd", required=True)

    p_bl = bench_sub.add_parser("list", help="列出所有 rubric")
    p_bl.add_argument("--json", action="store_true", dest="as_json")

    p_br = bench_sub.add_parser("run", help="打印 agent 调用模板（不调用 LLM）")
    p_br.add_argument("--rubric", required=True, help="相对根目录的 rubric 路径")

    p_bs = bench_sub.add_parser("score", help="重算校验响应 JSON")
    p_bs.add_argument("--rubric", required=True)
    p_bs.add_argument("--response", required=True)
    p_bs.add_argument("--json", action="store_true", dest="as_json")

    p_brep = bench_sub.add_parser("report", help="生成可读报告")
    p_brep.add_argument("--rubric", required=True)
    p_brep.add_argument("--response", required=True)

    args = parser.parse_args(argv)

    if args.mode == "pipeline":
        report = pipeline_report(args.competition, args.problem, args.keep)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        steps = report["steps"]
        failed = [k for k, v in steps.items()
                  if not k.endswith("_detail") and not str(v).startswith("PASS")]
        return 1 if failed else 0

    if args.mode == "library":
        report = library_report()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if "error" not in report.get("cumcm", {}) else 1

    # bench 子命令
    if args.bench_cmd == "list":
        bench_list(as_json=getattr(args, "as_json", False))
        return 0
    if args.bench_cmd == "run":
        res = bench_run(args.rubric)
        return 0 if "_error" not in res else 1
    if args.bench_cmd == "score":
        res = bench_score(args.rubric, args.response, as_json=getattr(args, "as_json", False))
        return 0 if "_error" not in res and res.get("summary", {}).get("checks_passed") else 1
    if args.bench_cmd == "report":
        bench_report(args.rubric, args.response)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
