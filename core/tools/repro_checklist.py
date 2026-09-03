#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复现清单 (reproducibility checklist)：依赖版本 + SHA-256 + 唯一复现命令 + 漂移校验。

对标 GitHub 同类项目（XiaoMaColtAI/math-modeling-skill）的复现清单实践，
把"换机器能不能复现"从口头承诺变成可校验的事实。

四要素：
1. **参数**：随机种子 / 多次运行次数 / CV 阈值 / 灵敏度范围（读 env，不硬编码）
2. **依赖**：扫描 code/*.py 的第三方 import（剔除仓库自有模块）+ requirements.txt，
   记录已装精确版本
3. **产物哈希**：code/*.py / figures/all_results.json / output 契约 / work/frozen_numbers.json / inputs/*
4. **唯一复现命令**

用法:
    python core/tools/repro_checklist.py <项目名> generate   # 生成（默认，向后兼容）
    python core/tools/repro_checklist.py <项目名> verify      # 校验产物哈希漂移
    python core/tools/repro_checklist.py <项目名> show        # 展示清单

产物:
    projects/<项目名>/output/reproducibility.json（符合 core/schemas/reproducibility.schema.json）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

MANIFEST_REL = "output/reproducibility.json"

_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([a-zA-Z_][\w.]*)\s+import|import\s+([a-zA-Z_][\w.]*))",
    re.MULTILINE,
)


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def project_dir(project):
    """解析项目目录：优先相对/绝对路径，否则回退 projects/<项目名>。"""
    p = Path(project)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        p = ROOT / "projects" / project
    return p


def sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (FileNotFoundError, OSError):
        return None


def get_python_version():
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_os_info():
    system = platform.system()
    if system == "Windows":
        return f"Windows {platform.release()}"
    if system == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    return f"{system} {platform.release()}"


def _env_get(key, default):
    """读 env 配置；加载失败回退默认值（与 freeze_numbers.py 同口径）。"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_env_loader_repro", ROOT / "core" / "env" / "loader.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.get(key, default)
    except Exception:
        return default


def _known_competitions() -> list[str]:
    base = ROOT / "core" / "templates" / "latex"
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir())


def _infer_competition(project_name: str) -> str:
    name = project_name.lower()
    for comp in _known_competitions():
        if name.startswith(comp):
            return comp
    return "unknown"


def _first_party_modules(base: Path) -> set[str]:
    """仓库自有模块名（code/*.py 与 core/**/*.py 的 stem），不应算第三方依赖。"""
    names = set()
    for py in list(base.glob("code/*.py")) + list(ROOT.glob("core/**/*.py")):
        names.add(py.stem)
    return names


def _installed_version(package: str) -> str:
    try:
        from importlib.metadata import version
        return version(package)
    except Exception:
        return "unknown (未安装或非 PyPI 包)"


def _scan_imports(base: Path) -> list[dict]:
    """扫描 code/*.py 的第三方 import，返回 [{name, version, used_by}]。"""
    stdlib = set(getattr(sys, "stdlib_module_names", set()))
    first_party = _first_party_modules(base)
    third_party: dict[str, set[str]] = {}
    for py in sorted(base.glob("code/*.py")):
        text = py.read_text(encoding="utf-8", errors="replace")
        for m in _IMPORT_RE.finditer(text):
            top = (m.group(1) or m.group(2)).split(".")[0]
            if not top or top in stdlib or top in first_party:
                continue
            third_party.setdefault(top, set()).add(py.name)
    return [
        {"name": name, "version": _installed_version(name),
         "used_by": sorted(third_party[name])}
        for name in sorted(third_party)
    ]


def _merge_requirements(base: Path, deps: list[dict]) -> list[dict]:
    """合并 code/requirements.txt 中显式声明的依赖（补齐未装包）。"""
    req_txt = base / "code" / "requirements.txt"
    if not req_txt.is_file():
        return deps
    have = {d["name"].lower() for d in deps}
    for line in req_txt.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([a-zA-Z0-9_.-]+)\s*==\s*(.+)$", line)
        if m and m.group(1).lower() not in have:
            deps.append({"name": m.group(1), "version": m.group(2), "used_by": ["requirements.txt"]})
    return sorted(deps, key=lambda d: d["name"].lower())


def scan_project_files(base: Path) -> dict[str, str]:
    """关键产物 + code/*.py + inputs/* + work/frozen_numbers.json 的 SHA-256。"""
    hashes = {}
    key_files = {
        "code/main.py": "main_py",
        "figures/all_results.json": "all_results_json",
        "output/MODEL_SPEC.md": "model_spec_md",
        "output/CODE_DELIVERABLES.md": "code_deliverables_md",
        "work/frozen_numbers.json": "frozen_numbers_json",
    }
    for rel, key in key_files.items():
        h = sha256_file(base / rel)
        if h:
            hashes[key] = h

    for g in ("code/*.py", "inputs/*"):
        for p in sorted(base.glob(g)):
            if p.is_file() and not p.name.startswith("."):
                h = sha256_file(p)
                if h:
                    hashes[p.relative_to(base).as_posix()] = h
    return hashes


def detect_main_command(base: Path, seed) -> str:
    main_py = base / "code" / "main.py"
    if main_py.is_file():
        content = main_py.read_text(encoding="utf-8", errors="replace")
        if "argparse" in content or "sys.argv" in content:
            return f"python code/main.py --seed {seed} --output figures/"
    return "python code/main.py"


def generate(project_name):
    base = project_dir(project_name)
    if not base.is_dir():
        print(f"Error: project directory not found: {base}", file=sys.stderr)
        return 1

    seed = _env_get("code.random_seed", 42)
    deps = _merge_requirements(base, _scan_imports(base))
    file_hashes = scan_project_files(base)
    main_cmd = detect_main_command(base, seed)

    checklist = {
        "reproduce_command": main_cmd,
        "python_version": get_python_version(),
        "dependencies": deps,
        "random_seed": seed,
        "multi_run_count": _env_get("code.multi_run_count", 5),
        "cv_threshold": _env_get("code.cv_threshold", 0.10),
        "sensitivity_range": _env_get("code.sensitivity_range", 0.20),
        "file_hashes": file_hashes,
        "hardware_env": {
            "os": get_os_info(),
            "cpu": platform.processor() or platform.machine(),
            "ram_gb": None,
            "gpu": None,
        },
        "data_sources": [],
        "competition": _infer_competition(base.name),
        "generated_at": _now(),
    }

    out_path = base / MANIFEST_REL
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(checklist, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")

    try:
        display = str(out_path.relative_to(ROOT))
    except ValueError:
        display = str(out_path)
    print(f"复现清单已生成: {display}")
    print(f"  依赖数: {len(deps)}  文件哈希: {len(file_hashes)} 个  种子: {seed}")
    print(f"  复现命令: {main_cmd}")
    return 0


def verify(project_name):
    base = project_dir(project_name)
    path = base / MANIFEST_REL
    if not path.is_file():
        print(f"无复现清单，先运行: python core/tools/repro_checklist.py {project_name} generate",
              file=sys.stderr)
        return 1

    manifest = json.loads(path.read_text(encoding="utf-8"))
    expected = manifest.get("file_hashes", {})
    # 当前磁盘按同一映射重建（key 命名与 generate 一致）
    current = scan_project_files(base)
    # 兼容旧清单：main_py 等语义 key 与 code/main.py 路径 key 可能并存
    drift = []
    for key, exp_h in expected.items():
        cur_h = current.get(key)
        if cur_h is None:
            drift.append((key, "MISSING"))
        elif cur_h != exp_h:
            drift.append((key, "CHANGED"))
    for key in current.keys() - expected.keys():
        drift.append((key, "NEW"))

    if drift:
        print(f"复现清单校验失败：{len(drift)} 项不一致")
        for key, kind in drift:
            print(f"  - [{kind}] {key}")
        return 1

    print(f"复现清单一致：{len(expected)} 项产物哈希全部匹配")
    print(f"  复现命令: {manifest.get('reproduce_command', '')}")
    return 0


def show(project_name):
    path = project_dir(project_name) / MANIFEST_REL
    if not path.is_file():
        print(f"无复现清单: {path}", file=sys.stderr)
        return 1
    m = json.loads(path.read_text(encoding="utf-8"))
    print(f"项目: {m.get('competition', '')}/{path.parent.parent.name}  "
          f"Python {m.get('python_version')}  生成: {m.get('generated_at')}")
    print(f"复现命令: {m.get('reproduce_command')}")
    print(f"参数: seed={m.get('random_seed')} multi_run={m.get('multi_run_count')} "
          f"cv={m.get('cv_threshold')} sens={m.get('sensitivity_range')}")
    deps = m.get("dependencies", [])
    print(f"依赖 ({len(deps)}):")
    for d in deps:
        used = ", ".join(d.get("used_by", []))
        print(f"  - {d['name']}=={d['version']}" + (f"  (used_by: {used})" if used else ""))
    fh = m.get("file_hashes", {})
    print(f"产物哈希 ({len(fh)}):")
    for k, v in fh.items():
        print(f"  - {k}  {v[:16]}…")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="复现清单：生成/校验论文交付的唯一复现命令")
    parser.add_argument("project", help="项目名或路径")
    parser.add_argument("action", nargs="?", default="generate",
                        choices=["generate", "verify", "show"],
                        help="generate=生成(默认) / verify=校验哈希漂移 / show=展示")
    args = parser.parse_args(argv)
    return {"generate": generate, "verify": verify, "show": show}[args.action](args.project)


if __name__ == "__main__":
    raise SystemExit(main())
