# -*- coding: utf-8 -*-
"""治理修复：validate.py iter_repo 统一排除研究实验路径（research/ + projects/ 下 P15 实验项目）。"""
import re

p = "src/modeling_harness/cli/validate.py"
t = open(p, encoding="utf-8").read()

# 1. 增加研究实验路径识别
anchor = 'REPO_SCAN_EXCLUDE_DIRS = {"_scratch", "_debug", "node_modules", "__pycache__"}'
assert anchor in t, "anchor REPO_SCAN_EXCLUDE_DIRS not found"
t = t.replace(
    anchor,
    'REPO_SCAN_EXCLUDE_DIRS = {"_scratch", "_debug", "node_modules", "__pycache__"}\n'
    'RESEARCH_PROJECT_PREFIXES = ("p151-", "rcs1-", "v3-real-", "bench-")\n'
    '\n'
    '\n'
    'def _is_research_scan_path(p: Path) -> bool:\n'
    '    """路径是否属于研究实验（research/ 或 projects/ 下的 P15/历史实验项目）。\n'
    '\n'
    '    研究实验不属于论文交付校验范围（validate.py 文档声明）；projects/ 内\n'
    '    滞留的历史研究实验项目（p151-*/rcs1-*/v3-real-*/bench-*）同样排除。\n'
    '    """\n'
    '    parts = p.parts\n'
    '    for idx, part in enumerate(parts):\n'
    '        if part == "research":\n'
    '            return True\n'
    '        if part == "projects" and idx + 1 < len(parts):\n'
    '            nxt = parts[idx + 1]\n'
    '            if nxt.startswith(RESEARCH_PROJECT_PREFIXES):\n'
    '                return True\n'
    '    return False',
)

# 2. iter_repo 使用统一排除
old_iter = (
    'def iter_repo(root, pattern):\n'
    '    """遍历 root 下匹配 pattern 的文件，跳过归档/临时目录。"""\n'
    '    root = Path(root)\n'
    '    for p in root.rglob(pattern):\n'
    '        if any(part in REPO_SCAN_EXCLUDE_DIRS for part in p.parts):\n'
    '            continue\n'
    '        yield p'
)
new_iter = (
    'def iter_repo(root, pattern):\n'
    '    """遍历 root 下匹配 pattern 的文件，跳过归档/临时/研究实验路径。"""\n'
    '    root = Path(root)\n'
    '    for p in root.rglob(pattern):\n'
    '        if any(part in REPO_SCAN_EXCLUDE_DIRS for part in p.parts):\n'
    '            continue\n'
    '        if _is_research_scan_path(p):\n'
    '            continue\n'
    '        yield p'
)
assert old_iter in t, "iter_repo pattern not found"
t = t.replace(old_iter, new_iter)

# 3. _live_project_dirs 复用统一前缀常量
old_live = '            and not d.name.startswith(("p151-", "rcs1-", "v3-real-", "bench-"))]'
new_live = '            and not d.name.startswith(RESEARCH_PROJECT_PREFIXES)]'
assert old_live in t, "live_project_dirs pattern not found"
t = t.replace(old_live, new_live)

open(p, "w", encoding="utf-8").write(t)
print("[OK] validate.py unified research exclusion")
