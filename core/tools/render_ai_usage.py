#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_ai_usage.py — AI 使用声明生成器

生成合规的 AI 使用声明段落，支持 CUMCM 和 MCM 格式。
从 artifact_registry 读取 AI 使用记录，自动生成声明文本。

用法:
    python core/tools/render_ai_usage.py <项目名>
    python core/tools/render_ai_usage.py <项目名> --format cumcm
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "tools"))
for _cat in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
    sys.path.insert(0, str(ROOT / "core" / "tools" / _cat))


CUMCM_TEMPLATE = (
    "本研究使用 AI 辅助工具（{tool_name} v{version}）完成了以下任务：\n"
    "{tasks}\n"
    "所有 AI 辅助生成的内容均经过作者人工审核与验证，确保结果的准确性与可靠性。"
)

MCM_TEMPLATE = (
    "This study utilized an AI-assisted tool ({tool_name} v{version}) "
    "for the following tasks:\n{tasks}\n"
    "All AI-generated content was manually reviewed and verified by the authors "
    "to ensure accuracy and reliability."
)

TASK_DESCRIPTIONS = {
    "problem-parser": "问题解析与特征提取",
    "type-classifier": "问题类型分类",
    "literature-searcher": "文献检索",
    "method-matcher": "方法匹配与推荐",
    "model-builder": "模型构建",
    "code-implementer": "代码实现",
    "test-runner": "测试执行",
    "section-writer": "论文章节撰写",
    "figure-generator": "图表生成",
    "reference-curator": "参考文献整理",
}


def _load_ai_records(project_dir: Path) -> dict:
    """加载 AI 使用记录。"""
    registry_path = project_dir / "work" / "artifact_registry.json"
    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
        return registry.get("ai_usage", {})

    state_path = project_dir / "work" / "state.json"
    if state_path.exists():
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
        return state.get("ai_usage", {})

    return {}


def generate_declaration(project_dir: Path, fmt: str = "cumcm") -> str:
    """生成 AI 使用声明。"""
    records = _load_ai_records(project_dir)

    tasks_used = []
    for agent, info in records.items():
        if isinstance(info, dict) and info.get("used", False):
            desc = TASK_DESCRIPTIONS.get(agent, agent)
            tasks_used.append(f"- {desc}")

    if not tasks_used:
        tasks_used = ["- 问题分析与方法选择", "- 代码实现与调试辅助"]

    tasks_text = "\n".join(tasks_used)

    template = CUMCM_TEMPLATE if fmt == "cumcm" else MCM_TEMPLATE
    return template.format(
        tool_name="MathModel",
        version="3.0",
        tasks=tasks_text,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="AI 使用声明生成器")
    parser.add_argument("project", help="项目名")
    parser.add_argument("--format", choices=["cumcm", "mcm"], default="cumcm",
                        help="声明格式")
    parser.add_argument("-o", "--output", help="输出文件路径")
    args = parser.parse_args(argv)

    project_dir = ROOT / "projects" / args.project
    if not project_dir.exists():
        print(f"[FAIL] 项目不存在: {project_dir}", file=sys.stderr)
        return 1

    declaration = generate_declaration(project_dir, fmt=args.format)

    if args.output:
        Path(args.output).write_text(declaration, encoding="utf-8")
        print(f"[OK] AI 使用声明已生成: {args.output}")
    else:
        print("\n--- AI 使用声明 ---\n")
        print(declaration)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
