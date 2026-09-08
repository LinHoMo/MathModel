#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""benchmark.py — 引擎演练 / 题库健康检查 / 国赛复盘基准 / 端到端能力基线

借鉴 MM-Bench 理念，用脚本化方式回答四类问题：
1. `pipeline`: 引擎对某个竞赛包能否健康开工？（临时项目脚手架 → state init → doctor → 清理）
2. `library`:  赛题库索引是否完整？（年份覆盖、待补标记、已核实题名数）
3. `bench`:    国赛复盘基准（rubric 列表 / run 模板 / 打分重算 / 报告）
4. `e2e`:      端到端能力基线（P13.0：真题导入 → V3 管线 → 八项指标）

    e2e run --problem 2000_C --project <name> --questions "Q001,Q002,Q003"
    e2e metrics --project <name> [--gt f] [--response f]
    e2e report --project <name>

指标定义见 docs/architecture/CAPABILITY_ROADMAP_P13_P17.md §1；
实现 core/tools/evaluation/e2e_metrics.py（确定性，零 LLM）。

零第三方依赖。pipeline 模式的临时项目命名 `_bench-*`，结束后自动删除。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
for _cat in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
    sys.path.insert(0, str(ROOT / "core" / "tools" / _cat))

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


# ---------------------------------------------------------------------------
# e2e 子命令：端到端能力基线（P13.0）
# ---------------------------------------------------------------------------

_DEFAULT_MMBENCH = ROOT.parent / "_mm_analysis" / "LLM-MM-Agent" / "MMBench"
MMBENCH_ROOT = Path(os.environ.get("MMBENCH_ROOT", str(_DEFAULT_MMBENCH)))


def _load_mmbench_problem(problem_id: str) -> dict:
    p = MMBENCH_ROOT / "problem" / f"{problem_id}.json"
    if not p.exists():
        raise ValueError(f"MMBench 题目不存在: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def e2e_prepare(problem_id: str, project: str, competition: str = "mcm") -> dict:
    """真题导入：题面 + 数据文件 + 元信息写入项目脚手架。返回元信息。"""
    prob = _load_mmbench_problem(problem_id)
    proj_dir = new_project.scaffold(project, competition, [])
    inputs = proj_dir / "inputs"
    parts = [f"# {problem_id}\n"]
    for key in ("background", "problem_requirement", "addendum"):
        if prob.get(key):
            parts.append(f"## {key}\n\n{prob[key]}\n")
    (inputs / "problem.md").write_text("\n".join(parts), encoding="utf-8")

    data_files: list[str] = []
    for rel in prob.get("dataset_path") or []:
        src = MMBENCH_ROOT / "dataset" / problem_id.replace("_", "_") / rel
        if not src.exists():
            # dataset 目录名形如 2000_C（与 problem_id 一致）
            src = MMBENCH_ROOT / "dataset" / problem_id / rel
        if src.exists():
            ddir = inputs / "data"
            ddir.mkdir(exist_ok=True)
            shutil.copy2(src, ddir / rel)
            data_files.append(f"inputs/data/{rel}")
    meta = {
        "problem_id": problem_id,
        "title": prob.get("title", problem_id),
        "background_excerpt": str(prob.get("background", ""))[:300],
        "dataset_files": data_files,
        "source": str(MMBENCH_ROOT),
    }
    _save_json(proj_dir / "work" / "e2e_problem.json", meta)
    return meta


def e2e_run(problem_id: str, project: str, questions: list[str],
            competition: str = "mcm", profile: str | None = None) -> dict:
    """端到端基线一次跑：导入 → V3 认知管线 → 八项指标落盘。

    profile: Problem Profile DTO（能力接口，非本体）——
        {"problem_title": ..., "problem_types": [...], ..., "per_question":
         {qid: {六键特征, "note": 映射理由}}}
    传入时经 RuntimeSession(features=...) 进入选型（P13-1 接口），
    副本存 work/e2e_profile.json 作 provenance。
    本命令只完成确定性部分（脚手架/管线/指标）；真实建模与 rubric 评分
    由 agent 会话按 SKILL.md 执行后经 `e2e metrics --response` 重算。
    """
    report: dict = {"mode": "e2e_run", "project": project,
                    "problem": problem_id, "questions": questions,
                    "profile": profile or "", "steps": {}}
    features: dict = {}
    if profile:
        p_path = Path(profile) if Path(profile).is_absolute() else ROOT / profile
        prof = _load_json(p_path)
        if "_error" in prof:
            report["steps"]["profile"] = f"FAIL: {prof['_error']}"
            return report
        # 兼容两种输入：纯 profile DTO，或消融 case 文件（features 内嵌）
        features = prof.get("features", prof) if isinstance(prof, dict) else {}
        report["steps"]["profile"] = "PASS"
        report["profile_keys"] = sorted(k for k in features
                                        if k != "per_question")
    try:
        meta = e2e_prepare(problem_id, project, competition)
        report["steps"]["prepare"] = "PASS"
        report["meta"] = meta
    except Exception as exc:  # noqa: BLE001
        report["steps"]["prepare"] = f"FAIL: {exc}"
        return report

    proj_dir = _find_project(project)
    if features:
        _save_json(proj_dir / "work" / "e2e_profile.json", features)
    try:
        if str(ROOT / "core") not in sys.path:
            sys.path.insert(0, str(ROOT / "core"))
        from runtime.execution.session import RuntimeSession
        session = RuntimeSession(proj_dir, questions, max_workers=1,
                                 features=features or None)
        prog = session.run()["progress"]
        report["steps"]["pipeline"] = (
            f"PASS（完成 {len(prog['completed'])}/{prog['total']}，"
            f"阻塞 {len(prog['blocked'])}，失败 {len(prog['failures'])}）")
        if prog["blocked"] or prog["failures"]:
            report["steps"]["pipeline"] += f" — {prog['blocked']} {prog['failures']}"
    except Exception as exc:  # noqa: BLE001
        report["steps"]["pipeline"] = f"FAIL: {exc}"
        return report

    try:
        import e2e_metrics as em
        m = em.compute_e2e_metrics(proj_dir)
        _save_json(proj_dir / "work" / "e2e_metrics.json", m)
        report["steps"]["metrics"] = "PASS"
        report["summary"] = m["summary"]
    except Exception as exc:  # noqa: BLE001
        report["steps"]["metrics"] = f"FAIL: {exc}"
        return report

    report["next_steps"] = [
        f"1. agent 真实解题（题面 inputs/problem.md，数据 inputs/data/）："
        f"分解/方法/建模/实验/结果 → 按 V3 产物登记",
        f"2. 写金标准 work/e2e_gt.json（sub_questions/methods）+ 评分响应 "
        f"work/e2e_response.json",
        f"3. 重算: python core/tools/benchmark.py e2e metrics --project "
        f"{project} --gt work/e2e_gt.json --response work/e2e_response.json",
        f"4. 报告: python core/tools/benchmark.py e2e report --project {project}",
    ]
    return report


def e2e_metrics_cmd(project: str, gt_file: str | None = None,
                    response_file: str | None = None) -> dict:
    """重算八项指标（可携带金标准与评分响应）。"""
    proj_dir = ROOT / "projects" / project
    if not proj_dir.exists():
        return {"_error": f"项目不存在: {proj_dir}"}
    gt = _load_json(Path(gt_file)) if gt_file else None
    resp = _load_json(Path(response_file)) if response_file else None
    for d in (gt, resp):
        if isinstance(d, dict) and "_error" in d:
            return d
    import e2e_metrics as em
    m = em.compute_e2e_metrics(proj_dir, gt, resp)
    _save_json(proj_dir / "work" / "e2e_metrics.json", m)
    print(json.dumps(m, ensure_ascii=False, indent=2))
    return m


def e2e_report(project: str) -> dict:
    """渲染端到端基线的 markdown 报告到 work/E2E_REPORT.md。"""
    proj_dir = ROOT / "projects" / project
    m = _load_json(proj_dir / "work" / "e2e_metrics.json")
    if "_error" in m:
        return m
    meta = _load_json(proj_dir / "work" / "e2e_problem.json")
    import e2e_metrics as em
    text = em.render_report(m, meta if "_error" not in meta else None)
    out = proj_dir / "work" / "E2E_REPORT.md"
    out.write_text(text, encoding="utf-8")
    print(text)
    return {"mode": "e2e_report", "written": str(out)}


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

    p_e2e = sub.add_parser("e2e", help="端到端能力基线（run/metrics/report）")
    e2e_sub = p_e2e.add_subparsers(dest="e2e_cmd", required=True)
    p_er = e2e_sub.add_parser("run", help="导入真题 → V3 管线 → 指标落盘")
    p_er.add_argument("--problem", required=True, help="MMBench 题目 ID，如 2000_C")
    p_er.add_argument("--project", required=True, help="项目名（小写字母开头）")
    p_er.add_argument("--questions", required=True,
                      help="问题分解（逗号分隔，如 Q001,Q002,Q003）")
    p_er.add_argument("--competition", default="mcm")
    p_er.add_argument("--profile", help="Problem Profile DTO JSON（P13-1 能力接口）")
    p_em = e2e_sub.add_parser("metrics", help="重算八项指标")
    p_em.add_argument("--project", required=True)
    p_em.add_argument("--gt", help="金标准 JSON（sub_questions/methods）")
    p_em.add_argument("--response", help="评分响应 JSON（rubric 打分）")
    p_erep = e2e_sub.add_parser("report", help="渲染 markdown 报告")
    p_erep.add_argument("--project", required=True)

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
    if args.mode == "bench":
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

    # e2e 子命令
    if args.mode == "e2e":
        if args.e2e_cmd == "run":
            rep = e2e_run(args.problem, args.project,
                          [q.strip() for q in args.questions.split(",") if q.strip()],
                          args.competition, profile=args.profile)
            print(json.dumps(rep, ensure_ascii=False, indent=2))
            failed = [k for k, v in rep.get("steps", {}).items()
                      if not str(v).startswith("PASS")]
            return 1 if failed else 0
        if args.e2e_cmd == "metrics":
            res = e2e_metrics_cmd(args.project, args.gt, args.response)
            return 0 if "_error" not in res else 1
        if args.e2e_cmd == "report":
            res = e2e_report(args.project)
            return 0 if "_error" not in res else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
