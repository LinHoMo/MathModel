#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_mmbench.py —— MMBench 数据集导入 + 复盘基准数据适配器

消费 LLM-MM-Agent 仓库的 ../_mm_analysis/LLM-MM-Agent/MMBench/problem/*.json，
导出为 MathModel 可直接消费的 rubric JSON 与 benchmark schema。

本库**不自带 LLM 调用**：`bench_mmbench` 只解决"题目从哪里来"与"格式对齐"，
实际评分仍由 agent runtime 读 SKILL.md 主观产出 bench_result.json，
再由 benchmark.py bench score 重算校验。

命令:
    python core/tools/bench_mmbench.py list                       列出 MMBench 全部题
    python core/tools/bench_mmbench.py export --year 2024 --topic A --out core/knowledge/bumch
    python core/tools/bench_mmbench.py path                        打印 MMBench 根路径

自动定位 MMBench: <PROJECT_ROOT>/../_mm_analysis/LLM-MM-Agent/MMBench
或通过环境变量 MMBENCH_ROOT 覆盖。

零第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_MMBENCH = ROOT.parent / "_mm_analysis" / "LLM-MM-Agent" / "MMBench"
MMBENCH_ROOT = Path(os.environ.get("MMBENCH_ROOT", str(_DEFAULT_MMBENCH)))

PROBLEM_DIR = MMBENCH_ROOT / "problem"
EVAL_DIR = MMBENCH_ROOT / "evaluation"
DATASET_DIR = MMBENCH_ROOT / "dataset"


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_mmbench_root() -> Path | None:
    if PROBLEM_DIR.is_dir() and any(PROBLEM_DIR.glob("*.json")):
        return MMBENCH_ROOT
    return None


def list_problems(as_json: bool = False) -> dict:
    """列出 MMBench 全部可用题目。"""
    root = find_mmbench_root()
    if not root:
        report = {"error": f"MMBench 未找到: {MMBENCH_ROOT}", "hint": "设置 MMBENCH_ROOT 环境变量"}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    jsons = sorted(PROBLEM_DIR.glob("*.json"))
    items = []
    for js in jsons:
        data = _load_json(js)
        items.append({
            "file": js.name,
            "year": int(js.stem.split("_")[0]) if "_" in js.stem else None,
            "topic": js.stem.split("_")[-1] if "_" in js.stem else None,
            "has_background": bool(data and data.get("background")),
            "has_requirement": bool(data and data.get("problem_requirement")),
            "datasets": data.get("dataset_path", []) if data else [],
        })
    report = {"mode": "mmbench_list", "root": str(root), "count": len(items), "problems": items}
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def _classify_topic(text: str) -> str:
    """基于题干关键词做粗粒度题型分类（A=连续/物理 B=离散/规划 C=数据/统计 D/E=交叉）。"""
    t = (text or "").lower()
    data_kw = ["data", "regression", "classification", "prediction", "statistical",
               "sampling", "clustering", "correlation", "optimization data"]
    phys_kw = ["physics", "motion", "heat", "fluid", "mechanics", "wave",
               "differential", "continuous", "trajectory"]
    discrp_kw = ["discrete", "network", "graph", "routing", "scheduling",
                 "integer", "combinatorial", "game"]
    score = {"C": 0, "A": 0, "B": 0}
    for k in data_kw:
        if k in t:
            score["C"] += 1
    for k in phys_kw:
        if k in t:
            score["A"] += 1
    for k in discrp_kw:
        if k in t:
            score["B"] += 1
    return max(score, key=score.get)


def export_problem(year: int, topic: str, out_dir: str | None = None,
                   as_json: bool = False) -> dict:
    """导出一题为 MathModel 通用 rubric JSON 骨架。

    注意：MMBench 不分 CUMCM/MCM 命名，需由调用方按本赛季对照判定。
    导出 rubric source="mmbench_import"，dimensions 由 assessment_points 平铺生成。
    """
    root = find_mmbench_root()
    if not root:
        return {"error": f"MMBench 未找到: {MMBENCH_ROOT}"}

    stem = f"{year}_{topic.upper()}"
    src = PROBLEM_DIR / f"{stem}.json"
    if not src.exists():
        return {"error": f"MMBench 中无此题: {src}"}

    data = _load_json(src)
    if not data:
        return {"error": f"无法解析: {src}"}

    background = data.get("background", "")
    requirement = data.get("problem_requirement", "")
    topic_class = _classify_topic(background + " " + requirement)

    rubric = {
        "competition": "mmbench_import",
        "year": year,
        "topic": topic.upper(),
        "title": "",
        "source": "mmbench_import",
        "source_note": f"从 LLM-MM-Agent MMBench {stem}.json 导入，待补 title 与官方 rubric",
        "total_score": 100,
        "dimensions": [
            {
                "id": "abstract",
                "name": "摘要与写作",
                "max_score": 10,
                "assessment_points": [
                    {"criterion": "摘要独立成页、结构完整", "score": 5},
                    {"criterion": "写作规范、条理清晰、排版美观", "score": 5}
                ],
                "reference_results": [],
                "common_pitfalls": []
            },
            {
                "id": "problem_solving",
                "name": "问题求解（模型/算法/结果三件套）",
                "max_score": 85,
                "assessment_points": [
                    {"criterion": "模型建立（公式清晰、假设合理）", "score": 30},
                    {"criterion": "算法设计（可编程、有步骤）", "score": 25},
                    {"criterion": "结果（具体数值、落在合理区间）", "score": 20},
                    {"criterion": "验证与灵敏度分析", "score": 10}
                ],
                "reference_results": [],
                "common_pitfalls": ["模型与算法割裂", "结果脱离现实区间"]
            },
            {
                "id": "bonus",
                "name": "特色加分",
                "max_score": 5,
                "assessment_points": [
                    {"criterion": "模型/算法/检验自主创新", "score": 5}
                ],
                "reference_results": [],
                "common_pitfalls": []
            }
        ],
        "meta": {
            "generated_by": "bench_mmbench.py export",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "version": "1",
            "anchor": f"mmbench/{stem}.json",
            "topic_class": topic_class,
            "dataset_hints": data.get("dataset_path", []),
            "raw_excerpt": {
                "background": background[:300],
                "requirement": requirement[:300]
            }
        }
    }

    if out_dir:
        out_path = Path(out_dir) / f"mmbench_{year}{topic.lower()}.json"
        _save_json(out_path, rubric)
        rubric["_saved_to"] = str(out_path)

    if as_json:
        print(json.dumps(rubric, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(rubric, ensure_ascii=False, indent=2))
    return rubric


def print_path() -> None:
    """打印 MMBench 根路径。"""
    root = find_mmbench_root()
    if root:
        print(f"MMBENCH_ROOT={root}")
        print(f"状态: 已定位，共 {len(list(PROBLEM_DIR.glob('*.json')))} 题")
    else:
        print(f"MMBENCH_ROOT={MMBENCH_ROOT}")
        print("状态: 未定位。设置 MMBENCH_ROOT 环境变量后重试。")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="MMBench 数据导出适配器")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="列出 MMBench 全部题").add_argument("--json", action="store_true")

    p_exp = sub.add_parser("export", help="导出题为 rubric 骨架")
    p_exp.add_argument("--year", type=int, required=True)
    p_exp.add_argument("--topic", required=True)
    p_exp.add_argument("--out", help="输出目录（默认仅打印）")
    p_exp.add_argument("--json", action="store_true")

    sub.add_parser("path", help="打印 MMBench 根路径")

    args = parser.parse_args(argv)

    if args.cmd == "list":
        res = list_problems(as_json=getattr(args, "json", False))
        return 0 if "error" not in res else 1
    if args.cmd == "export":
        res = export_problem(args.year, args.topic, args.out, as_json=getattr(args, "json", False))
        return 0 if "error" not in res else 1
    if args.cmd == "path":
        print_path()
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
