#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境预检 —— 在开工前暴露问题，而不是等到最后一步才炸。

解决的问题
----------
此前 LaTeX 工具链、Python 依赖、竞赛模板是否齐备，
要一直跑到 writer/final-validator 才会暴露——
那时整条流水线的时间已经花掉了。

用法
----
    python core/tools/doctor.py                      # 检查仓库本体
    python core/tools/doctor.py --project cumcm2024a # 额外检查指定项目
    python core/tools/doctor.py --competition cumcm  # 按竞赛检查所需模板与引擎
    python core/tools/doctor.py --skip-tools         # 跳过外部工具链检查

退出码：0 = 全部就绪或仅有建议项；1 = 存在阻塞项。
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core" / "tools"))
for _cat in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
    sys.path.insert(0, str(ROOT / "core" / "tools" / _cat))

# 各竞赛所需的 LaTeX 引擎（沿用 handsomeZR 验证过的分配）
ENGINE_BY_COMPETITION = {
    "cumcm": "xelatex",
    "huawei": "xelatex",
    "diangong": "xelatex",
    "huashu": "xelatex",
    "mcm": "pdflatex",
    # 以下为 baseline 竞赛包（规则待官方核对，引擎按中文默认 xelatex）
    "apmcm": "xelatex",
    "mathorcup": "xelatex",
    "renzhengbei": "xelatex",
    "shuweibei": "xelatex",
}

REQUIRED_TOOLS = [
    ("state.py", "执行状态管理"),
    ("gate.py", "门禁判定"),
    ("gatelib.py", "门禁公共库"),
    ("render_ai_usage.py", "AI 使用披露生成器"),
    ("doctor.py", "环境预检（本文件）"),
]

REQUIRED_DIRS = [
    ("core/Modeler/agents", "建模手 8 个 agent"),
    ("core/Programmer/agents", "编程手 6 个 agent"),
    ("core/Writer/agents", "撰写手 7 个 agent"),
    ("core/Reviewer/agents", "评审手 8 个 agent"),
    ("core/knowledge/methodology", "方法论知识库"),
    ("core/knowledge/validation", "验证模块"),
    ("core/env", "配置层"),
    ("core/schemas", "结构化输出 Schema"),
]


class Result:
    def __init__(self):
        self.ok, self.warn, self.block = [], [], []

    def add(self, ok, name, detail=""):
        (self.ok if ok else self.warn).append((name, detail))

    def block_(self, name, detail=""):
        self.block.append((name, detail))


def check_python(r):
    v = sys.version_info
    ok = v >= (3, 8)
    r.add(ok, "Python 版本", f"{v.major}.{v.minor}.{v.micro}"
          + ("" if ok else "（需 >= 3.8）"))
    if not ok:
        r.block_("Python 版本", "需 >= 3.8")


def check_tools(r):
    for name, desc in REQUIRED_TOOLS:
        p = ROOT / "core" / "tools" / name
        ok = p.exists()
        r.add(ok, f"core/tools/{name}", desc if ok else "缺失")
        if not ok:
            r.block_(f"core/tools/{name}", "缺失")


def check_dirs(r):
    for d, desc in REQUIRED_DIRS:
        p = ROOT / d
        ok = p.is_dir()
        r.add(ok, d, desc if ok else "目录缺失")
        if not ok:
            r.block_(d, "目录缺失")


def check_agent_count(r):
    expect = {"Modeler": 8, "Programmer": 6, "Writer": 7, "Reviewer": 8}
    for hand, n in expect.items():
        d = ROOT / "core" / hand / "agents"
        if not d.is_dir():
            continue
        actual = len([x for x in d.iterdir() if x.is_dir()])
        ok = actual == n
        r.add(ok, f"{hand} agent 数", f"{actual}（期望 {n}）")
        if not ok:
            r.block_(f"{hand} agent 数", f"{actual} != {n}")


def check_catalog_v3(r):
    """catalog.yaml v5 双视图一致性（roles/DAG/validators 三方对齐）。"""
    import subprocess
    script = ROOT / "core" / "tools" / "catalog_check.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60)
    except Exception as e:
        r.add(False, "catalog v5 双视图", f"catalog_check 执行失败: {e}")
        return
    if proc.returncode == 0:
        r.add(True, "catalog v5 双视图", "v3 与 roles/DAG/validators 三方一致")
    else:
        out = (proc.stdout or proc.stderr).strip().splitlines()
        detail = out[0] if out else "不一致"
        r.add(False, "catalog v5 双视图", detail)
        r.block_("catalog v5 双视图", detail)


def check_latex(r, competition, skip):
    if skip:
        r.add(True, "LaTeX 工具链", "已跳过（--skip-tools）")
        return
    engine = ENGINE_BY_COMPETITION.get(competition, "xelatex")
    found = shutil.which(engine)
    if found:
        r.add(True, f"LaTeX 引擎 {engine}", found)
    else:
        r.add(False, f"LaTeX 引擎 {engine}",
              "未找到。论文将无法编译 PDF。"
              "env.runtime.compile_pdf=auto 时会降级为仅交付 .tex")
    # bibtex 用于参考文献
    bib = shutil.which("bibtex")
    r.add(bool(bib), "bibtex", bib or "未找到（参考文献将无法正常渲染）")
    # latexmk 可简化多次编译
    lmk = shutil.which("latexmk")
    r.add(bool(lmk), "latexmk", lmk or "未找到（可用 engine 手动跑多遍）")


def check_competition_pack(r, competition):
    if not competition:
        return
    pack = ROOT / "core" / "templates" / "latex" / competition
    if pack.is_dir():
        r.add(True, f"竞赛包 {competition}", str(pack))
    else:
        r.add(False, f"竞赛包 {competition}",
              f"templates/latex/{competition}/ 不存在，将回退到默认模板")


def check_project(r, project):
    import state as S
    base = S.project_dir(project)
    if not base.exists():
        r.block_(f"项目 {project}", "目录不存在")
        return
    r.add(True, f"项目 {project}", str(base))

    for sub, desc in [("inputs", "赛题与原始数据"),
                      ("work", "中间产物与状态"),
                      ("output", "三手产物契约")]:
        ok = (base / sub).is_dir()
        r.add(ok, f"{project}/{sub}", desc if ok else "缺失")

    st = S.load(project)
    if st is None:
        r.add(False, "执行状态",
              f"无 state.json，运行: python core/tools/state.py {project} init")
    else:
        done = len(st.get("completed", []))
        r.add(True, "执行状态", f"{done}/{len(S.PIPELINE)} 步已完成")

    # 原始数据只读检查（P2-12）
    inputs = base / "inputs"
    if inputs.is_dir():
        writable = [f.name for f in inputs.iterdir()
                    if f.is_file() and _is_writable(f)]
        if writable:
            r.add(False, "原始数据只读", f"可写文件（应设为只读）: {writable[:3]}")
        else:
            r.add(True, "原始数据只读", "inputs/ 未被标记为可写")


def _is_writable(p):
    import os
    return os.access(str(p), os.W_OK)


def main():
    ap = argparse.ArgumentParser(description="环境预检")
    ap.add_argument("--project", help="额外检查指定项目")
    ap.add_argument("--competition", choices=list(ENGINE_BY_COMPETITION),
                    help="按竞赛检查模板与引擎")
    ap.add_argument("--skip-tools", action="store_true",
                    help="跳过外部工具链检查")
    args = ap.parse_args()

    r = Result()
    check_python(r)
    check_tools(r)
    check_dirs(r)
    check_agent_count(r)
    check_catalog_v3(r)
    check_latex(r, args.competition, args.skip_tools)
    check_competition_pack(r, args.competition)
    if args.project:
        check_project(r, args.project)

    print("=" * 62)
    print("MathModelSkills 环境预检")
    print("=" * 62)
    for name, detail in r.ok:
        print(f"  [OK]   {name}" + (f" - {detail}" if detail else ""))
    for name, detail in r.warn:
        print(f"  [WARN] {name} - {detail}")
    print("-" * 62)
    print(f"就绪 {len(r.ok)} / 警告 {len(r.warn)} / 阻塞 {len(r.block)}")

    if r.block:
        print("\n阻塞项（必须修复后才能开工）:")
        for name, detail in r.block:
            print(f"  - {name}: {detail}")
        print("=" * 62)
        return 1

    if r.warn:
        print("\n建议项（不阻塞，但可能影响交付质量）:")
        for name, detail in r.warn:
            print(f"  - {name}: {detail}")

    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
