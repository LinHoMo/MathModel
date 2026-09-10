# -*- coding: utf-8 -*-
"""治理修复：validate.py _live_project_dirs 排除 P15 研究实验项目（正则替换，鲁棒）。"""
import re

p = "src/modeling_harness/cli/validate.py"
t = open(p, encoding="utf-8").read()

old_fn = re.compile(
    r'def _live_project_dirs\(project_path\):.*?'
    r'return \[d for d in pdir\.iterdir\(\)\n'
    r'\s+if d\.is_dir\(\) and not d\.name\.startswith\("\."\)\n'
    r'\s+and not \(d / "work" / "e2e_problem\.json"\)\.exists\(\)\]',
    re.S,
)

new_fn = (
    'def _live_project_dirs(project_path):\n'
    '    """返回 projects/ 下的活跃项目实例目录（样例已迁移至 tests/fixtures/）。\n'
    '\n'
    '    本仓库是技能库，projects/ 可能为空（无活跃实例）。项目级存在性检查\n'
    '    （all_results.json / 随机种子 / 论文 .tex）仅在存在活跃实例时才应报失败，\n'
    '    否则库模式下的空 projects/ 会持续产生假失败。\n'
    '\n'
    '    研究实验（P13-3D 系列 / bench 运行 / P15 实验项目 p151-*/rcs1-*/v3-real-*）\n'
    '    不属于论文交付校验范围（research/ 不在本函数扫描内；projects/ 内滞留的\n'
    '    P15 历史研究实验项目同样排除——它们没有论文交付契约）。\n'
    '    """\n'
    '    pdir = project_path / "projects"\n'
    '    if not pdir.is_dir():\n'
    '        return []\n'
    '    return [d for d in pdir.iterdir()\n'
    '            if d.is_dir() and not d.name.startswith(".")\n'
    '            and not (d / "work" / "e2e_problem.json").exists()\n'
    '            and not d.name.startswith(("p151-", "rcs1-", "v3-real-", "bench-"))]'
)

t2, n = old_fn.subn(new_fn, t)
assert n == 1, f"expected 1 replacement, got {n}"
open(p, "w", encoding="utf-8").write(t2)
print("[OK] validate.py _live_project_dirs replaced")
