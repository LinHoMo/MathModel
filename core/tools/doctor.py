#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境预检 —— 在开工前暴露问题，而不是等到最后一步才炸。

解决的问题
----------
V3 是 LLM-free harness：工具链、schema、知识库、运行时组件是否齐备，
在开工前一次性暴露，而不是等到执行中途才炸。

用法
----
    python core/tools/doctor.py                      # 检查仓库本体
    python core/tools/doctor.py --project cumcm2024a # 额外检查指定项目
    python core/tools/doctor.py --skip-tools         # 跳过外部工具链检查

退出码：0 = 全部就绪或仅有建议项；1 = 存在阻塞项。
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "tools"))

REQUIRED_TOOLS = [
    ("validate.py", "项目级校验"),
    ("catalog_check.py", "catalog 一致性检查"),
    ("new_project.py", "新项目脚手架"),
    ("doctor.py", "环境预检（本文件）"),
]

REQUIRED_DIRS = [
    ("core/knowledge/methodology", "方法论知识库"),
    ("core/validators/modules", "验证模块"),
    ("core/env", "配置层"),
    ("core/schemas", "结构化输出 Schema"),
    ("core/workflows/stages", "DAG stage 模板"),
    ("core/roles", "角色定义"),
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
    """V3：core/roles 4 角色定义齐全（analyst/modeler/experimenter/critic）。"""
    roles_dir = ROOT / "core" / "roles"
    if not roles_dir.is_dir():
        r.block_("core/roles", "目录缺失")
        return
    files = sorted(roles_dir.glob("*.yaml"))
    names = {f.stem for f in files}
    expected = {"analyst", "modeler", "experimenter", "critic"}
    missing = sorted(expected - names)
    ok = not missing
    r.add(ok, "V3 角色定义", "齐全" if ok else f"缺失 {missing}")
    if not ok:
        r.block_("V3 角色定义", f"缺失 {missing}")


def check_catalog_v3(r):
    """catalog.yaml v5 双视图一致性（roles/DAG/validators 三方对齐）。"""
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


def check_project(r, project):
    from pathlib import Path
    base = Path("projects") / project
    if not base.exists():
        r.block_(f"项目 {project}", "目录不存在")
        return
    r.add(True, f"项目 {project}", str(base))

    for sub, desc in [("inputs", "赛题与原始数据"),
                      ("state", "Registry + Evidence Graph"),
                      ("output", "模型产出")]:
        ok = (base / sub).is_dir()
        r.add(ok, f"{project}/{sub}", desc if ok else "缺失")

    # 检查 state 目录下的关键文件
    state_dir = base / "state"
    if state_dir.is_dir():
        for fname in ["registry.json", "evidence_graph.json"]:
            ok = (state_dir / fname).exists()
            r.add(ok, f"{project}/state/{fname}", "存在" if ok else "缺失")

    # 原始数据只读检查
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
    ap.add_argument("--skip-tools", action="store_true",
                    help="跳过外部工具链检查")
    args = ap.parse_args()

    r = Result()
    check_python(r)
    check_tools(r)
    check_dirs(r)
    check_agent_count(r)
    check_catalog_v3(r)
    if args.project:
        check_project(r, args.project)

    print("=" * 62)
    print("Modeling-Harness 环境预检")
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
