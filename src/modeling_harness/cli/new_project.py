#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""new_project.py — 新项目脚手架（V3）

创建标准项目目录结构、导入赛题文件、提示下一步命令。
零第三方依赖。不覆盖已存在的项目。

产出定位（AGENTS.md）：问题输入 → 数学建模产出（MODEL_IR JSON +
模型描述文档 MD/Mermaid）。不含论文生成（LaTeX/PDF），不兼容 V2 布局。

用法:
    python src/modeling_harness/cli/new_project.py <项目名> [--competition <赛事>]
                                     [--problem <赛题文件> ...] [--force]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent

# V3 项目目录结构（单一事实源，供脚手架创建）：
# - inputs/     赛题原文（唯一输入）
# - state/      runtime 状态（status.json + runs/）
# - artifacts/  Artifact Registry 落盘区（registry 索引在 state/）
# - model/      建模产出：MODEL_IR JSON + 模型描述文档（MD/Mermaid）
PROJECT_DIRS = (
    "inputs",
    "state",
    "state/runs",
    "artifacts",
    "artifacts/data",
    "artifacts/code",
    "artifacts/results",
    "artifacts/figures",
    "model",
)
NAME_RE = __import__("re").compile(r"^[a-z][a-z0-9-]{1,63}$")

# 已知竞赛标识（V3 仅作元信息；不再绑定论文规格 / LaTeX 模板）
KNOWN_COMPETITIONS = (
    "cumcm", "mcm", "diangong", "huashu", "huawei",
    "apmcm", "mathorcup", "renzhengbei", "shuweibei",
)

NEXT_STEPS = """\
下一步（按 AGENTS.md 执行协议）:
  1. 将赛题原文保存为 inputs/problem.txt（或 inputs/question_spec.json）
  2. python src/modeling_harness/cli/validate.py {name}
  3. python src/modeling_harness/cli/catalog_check.py --check
  4. 沿 src/modeling_harness/roles/*.yaml 与 src/modeling_harness/skills/ 指令建模，产出写入项目根：
     - MODEL_IR: model_ir.json（顶层，与 validate.py/e2e_metrics.py 契约一致）
     - 描述文档: model.md（顶层，可含 Mermaid 图）
     - 数值结果: all_results.json（顶层，供数值追溯校验）
"""


def known_competitions() -> list[str]:
    """已知竞赛标识列表（V3 元信息用；论文规格已随 V2 移除）。"""
    return list(KNOWN_COMPETITIONS)


def _write_handoff(proj_dir: Path, competition: str) -> None:
    """生成交接文档模板 model/README.md（不覆盖已有文件）

    记录项目元信息与产出物索引；每次 session 结束时更新。
    """
    target = proj_dir / "model" / "README.md"
    if target.exists():
        return
    content = f"""\
# {proj_dir.name}

> 建模产出目录。Source of truth = Artifact Registry + Evidence Graph。

## 元信息

- **竞赛**: {competition if competition else "（未指定）"}
- **状态**: 待建模

## 产出物索引（均位于项目根目录）

| 产物 | 位置 | 状态 |
|------|------|------|
| 赛题原文 | `inputs/problem.txt` | 待导入 |
| 模型表示（MODEL_IR） | `model_ir.json` | 待生成 |
| 模型描述文档 | `model.md`（含 Mermaid） | 待生成 |
| 数值结果台账 | 结果 JSON（项目根） | 待生成 |
| 执行证据 | `artifacts/results/` | 待生成 |
| **模型图表（人看）** | `artifacts/figures/model-map.html` | 待生成（`mh diagram project <name>`） |
| 运行状态 | `state/` | 待初始化 |

## 目录索引（V3）

| 目录 | 说明 |
|------|------|
| `inputs/` | 赛题原文（唯一输入） |
| `state/` | runtime 状态 |
| `artifacts/` | Artifact Registry 落盘区（code/results/figures） |
| `model/` | 交接文档与附加说明 |

> 交付物统一位于**项目根目录**，与 V3 校验契约一致（不在 `model/` 子目录）。
"""
    target.write_text(content.lstrip(), encoding="utf-8")


def scaffold(project: str, competition: str, problem_files: list[str],
             force: bool = False) -> Path:
    """创建项目目录并复制赛题文件。返回项目目录。失败抛 ValueError。"""
    if not NAME_RE.match(project):
        raise ValueError(
            f"项目名 '{project}' 不合法：须以小写字母开头，只含小写字母/数字/连字符，2-64 字符")
    if competition and competition not in KNOWN_COMPETITIONS:
        raise ValueError(f"未知竞赛标识 '{competition}'，可选: {', '.join(KNOWN_COMPETITIONS)}")

    proj_dir = ROOT / "projects" / project
    if proj_dir.exists() and not force:
        raise ValueError(f"项目已存在: {proj_dir}（如需重建请用 --force）")

    for sub in PROJECT_DIRS:
        (proj_dir / sub).mkdir(parents=True, exist_ok=True)

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
    parser.add_argument("--competition", default="",
                        help="竞赛标识（可选，仅元信息；可选值见 known_competitions）")
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
    print("[OK] 交接文档模板: model/README.md")
    print()
    print(NEXT_STEPS.format(name=args.project))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
