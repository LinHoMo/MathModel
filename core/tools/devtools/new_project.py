#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""new_project.py — 新项目脚手架

为多元化赛事快速开工：创建标准项目目录结构、导入赛题文件、提示下一步命令。
零第三方依赖。不覆盖已存在的项目。

用法:
    python core/tools/new_project.py <项目名> --competition <赛事>
                                     [--problem <赛题文件> ...] [--force]

--competition 的取值动态读取 core/env/profiles/*.yaml 的 meta.competition
（单一真源），覆盖所有已配置赛事包（cumcm / mcm / diangong / huashu / huawei /
apmcm / mathorcup / renzhengbei / shuweibei）。
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# 项目目录结构（单一事实源，供脚手架创建）。与 REFACTOR_PLAN §6.3 对齐：
# - 删除 tables/（表格直接写进 tex，无独立目录必要）
# - _debug/ → _scratch/（临时区，显式创建，可随时清空，不再污染 code/）
# - 新增 deliverables/（投稿交付物：论文PDF/支撑材料ZIP/AI工具使用详情PDF）
# - 新增 support_materials 不再单独建目录；披露材料统一落到 deliverables/
PROJECT_DIRS = (
    # --- V2 legacy 布局（29-agent 线性流水线，保持兼容不删除） ---
    "inputs",
    "inputs/external",
    "work",
    "output",
    "code",
    "figures",
    "paper",
    "paper/figures",
    "deliverables",
    "_scratch",
    # --- V3 workspace（Cognitive Workflow Runtime，P1+） ---
    # state/       多维状态（state/status.json + workflow 视图，state.py v3 子命令消费）
    # artifacts/   Artifact Layer 落盘区，按 kind 分目录存原文件（registry 索引在根）
    "state",
    "artifacts",
    "artifacts/data",
    "artifacts/code",
    "artifacts/figures",
    "artifacts/tables",
    "artifacts/results",
)
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")

NEXT_STEPS = """\
下一步（按 AGENTS.md 执行协议）:
  1. python core/tools/state.py {name} init
  2. python core/tools/doctor.py --project {name} --competition {comp}
  3. python core/tools/state.py {name} status   # 从 modeler/problem-parser 开始

V3 Runtime（可选，与 V2 并行）:
  python core/tools/state.py {name} v3          # V2→V3 自动转换 + 多维状态视图
"""


def known_competitions() -> list[str]:
    """动态读取 core/env/profiles/*.yaml 的 meta.competition（单一真源）。

    原实现读 core/templates/latex 目录名，只覆盖有 LaTeX 模板的 6 个赛事，
    遗漏了有 profile 但复用国赛模板的 diangong / huashu / huawei。
    现以 profile 为准，所有赛事包均可建；profile 目录缺失时回退到模板目录兜底。
    """
    prof_dir = ROOT / "core" / "env" / "profiles"
    if prof_dir.is_dir():
        comps: set[str] = set()
        for f in sorted(prof_dir.glob("*.yaml")):
            if f.name.startswith("_"):
                continue
            comp = _profile_meta_competition(f.read_text(encoding="utf-8"))
            if comp:
                comps.add(comp)
        if comps:
            return sorted(comps)
    # 回退：模板目录
    base = ROOT / "core" / "templates" / "latex"
    if base.is_dir():
        return sorted(p.name for p in base.iterdir() if p.is_dir())
    return []


def _profile_meta_competition(text: str) -> str | None:
    """零依赖提取 profile 中 meta.competition 的值。"""
    in_meta = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "meta:":
            in_meta = True
            continue
        if in_meta:
            if line and not line[0].isspace():
                in_meta = False
                continue
            m = re.match(r"competition:\s*(\S+)", stripped)
            if m:
                return m.group(1)
    return None


def _write_time_budget(proj_dir: Path, competition: str) -> None:
    """生成时间预算模板 work/time_budget.yaml（不覆盖已有文件）"""
    target = proj_dir / "work" / "time_budget.yaml"
    if target.exists():
        return
    total_hours = {"cumcm": 72, "mcm": 96, "diangong": 72, "huawei": 72, "huashu": 72,
                    "apmcm": 96, "mathorcup": 72, "renzhengbei": 72, "shuweibei": 72}.get(competition, 72)
    content = f"""\
# 时间预算 — {proj_dir.name}
# 竞赛: {competition} | 总时限: {total_hours}h
# 每阶段完成后更新 actual_hours 与 status

stages:
  modeler:
    allocated_hours: {int(total_hours * 0.25)}
    actual_hours: 0
    status: pending  # pending / in_progress / done
    notes: ""
  programmer:
    allocated_hours: {int(total_hours * 0.30)}
    actual_hours: 0
    status: pending
    notes: ""
  writer:
    allocated_hours: {int(total_hours * 0.35)}
    actual_hours: 0
    status: pending
    notes: ""
  reviewer:
    allocated_hours: {int(total_hours * 0.10)}
    actual_hours: 0
    status: pending
    notes: ""

total_allocated_hours: {total_hours}
total_actual_hours: 0
deadline: ""  # 填写提交截止时间 (ISO 8601)
"""
    target.write_text(content.lstrip(), encoding="utf-8")


def _write_handoff(proj_dir: Path, competition: str) -> None:
    """生成交接文档模板 work/handoff.md（不覆盖已有文件）

    用于跨 session / 跨 runtime 传递上下文。每次 session 结束时更新，
    新 session 启动时先读此文件恢复进度。
    """
    target = proj_dir / "work" / "handoff.md"
    if target.exists():
        return
    content = f"""\
# Handoff — {proj_dir.name}

> 每次 session 结束时更新此文件。新 session 启动时先读此文件。

## 当前进度

- **竞赛**: {competition}
- **当前手**: modeler
- **当前 agent**: problem-parser
- **已完成步骤**: （无）
- **下一步**: `python core/tools/state.py {proj_dir.name} status`

## 关键决策

（尚无决策记录。决策详情见 `work/decision_log.json`。）

## 阻塞与风险

（无）

## 上次 session 摘要

首次创建，尚无历史。

## 文件索引

| 产物 | 路径 | 状态 |
|------|------|------|
| 赛题 | `inputs/` | 已导入 |
| MODEL_SPEC | `output/MODEL_SPEC.md` | 待生成 |
| CODE_DELIVERABLES | `output/CODE_DELIVERABLES.md` | 待生成 |
| PAPER_SPEC | `output/PAPER_SPEC.md` | 待生成 |
| 主代码 | `code/main.py` | 待生成 |
| 论文 | `paper/main.tex` | 待生成 |
"""
    target.write_text(content.lstrip(), encoding="utf-8")


def scaffold(project: str, competition: str, problem_files: list[str],
             force: bool = False) -> Path:
    """创建项目目录并复制赛题文件。返回项目目录。失败抛 ValueError。"""
    if not NAME_RE.match(project):
        raise ValueError(
            f"项目名 '{project}' 不合法：须以小写字母开头，只含小写字母/数字/连字符，2-64 字符")
    comps = known_competitions()
    if competition not in comps:
        raise ValueError(f"未知竞赛包 '{competition}'，可选: {', '.join(comps) or '(未找到)'}")

    proj_dir = ROOT / "projects" / project
    if proj_dir.exists() and not force:
        raise ValueError(f"项目已存在: {proj_dir}（如需重建请用 --force，将先自行备份）")
    if proj_dir.exists() and force:
        # 不删除用户数据：只补缺失目录
        pass

    for sub in PROJECT_DIRS:
        (proj_dir / sub).mkdir(parents=True, exist_ok=True)

    _write_time_budget(proj_dir, competition)
    _write_handoff(proj_dir, competition)

    for src in problem_files:
        src_path = Path(src)
        if not src_path.is_file():
            raise ValueError(f"赛题文件不存在: {src}")
        shutil.copy2(src_path, proj_dir / "inputs" / src_path.name)

    return proj_dir


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="新项目脚手架：创建目录结构并导入赛题")
    parser.add_argument("project", help="项目名（如 cumcm2025c / mcm2026e）")
    parser.add_argument("--competition", required=True,
                        help="竞赛包（动态读取 core/env/profiles/*.yaml，如 cumcm / mcm / "
                             "diangong / huashu / huawei / apmcm / mathorcup / renzhengbei / shuweibei）")
    parser.add_argument("--problem", action="append", default=[],
                        help="赛题文件路径（可多次指定）")
    parser.add_argument("--force", action="store_true",
                        help="目录已存在时补齐缺失子目录（不删除已有文件）")
    args = parser.parse_args(argv)

    try:
        proj_dir = scaffold(args.project, args.competition, args.problem, args.force)
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2

    print(f"[OK] 项目已创建: {proj_dir}")
    for sub in PROJECT_DIRS:
        print(f"     - {proj_dir.name}/{sub}/")
    for src in args.problem:
        print(f"[OK] 赛题已导入: inputs/{Path(src).name}")
    print(f"[OK] 时间预算模板: work/time_budget.yaml")
    print(f"[OK] 交接文档模板: work/handoff.md")
    print()
    print(NEXT_STEPS.format(name=args.project, comp=args.competition))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
