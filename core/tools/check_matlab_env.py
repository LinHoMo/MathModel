#!/usr/bin/env python3
"""MATLAB / 北太天元 / MWORKS Syslab 环境检测工具 — 零第三方依赖。

检测本机是否安装 MATLAB、北太天元（BDT）或 MWORKS Syslab，
输出可用工具箱列表与版本信息（Syslab 另报 M 命令行 mlang 与 Julia 运行时 julia-ty）。
供 template-selector / code-implementer 判断能否产出交付分支。

用法：
    python check_matlab_env.py              # JSON 报告到 stdout
    python check_matlab_env.py --summary    # 人类可读摘要到 stdout
    python check_matlab_env.py --platform matlab   # 只检测指定平台
    python check_matlab_env.py --platform syslab   # 只检测 MWORKS Syslab
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from typing import Optional


_COMMON_MATLAB_PATHS = {
    "win32": [
        r"C:\Program Files\MATLAB",
        r"C:\Program Files (x86)\MATLAB",
        os.path.expanduser(r"~\AppData\Local\Programs\MATLAB"),
    ],
    "darwin": [
        "/Applications/MATLAB_R2024a.app",
        "/Applications/MATLAB_R2024b.app",
        "/Applications/MATLAB_R2023b.app",
        "/Applications/MATLAB_R2023a.app",
        "/Applications/MATLAB_R2022b.app",
    ],
    "linux": [
        "/usr/local/MATLAB",
        "/opt/MATLAB",
    ],
}

_BDT_COMMON_PATHS = {
    "win32": [
        r"C:\Program Files\BeiTian\BDT",
        r"C:\Program Files (x86)\BeiTian\BDT",
        r"C:\Program Files\北太天元",
        os.path.expanduser(r"~\AppData\Local\Programs\BDT"),
    ],
    "darwin": [],
    "linux": [
        "/opt/bdt",
        "/usr/local/bdt",
    ],
}

_SYSLAB_COMMON_PATHS = {
    "win32": [
        r"C:\Program Files\MWORKS",
        r"C:\Program Files (x86)\MWORKS",
        r"D:\Program Files\MWORKS",
        os.path.expanduser(r"~\AppData\Local\Programs\MWORKS"),
    ],
    "darwin": ["/Applications/MWORKS"],
    "linux": ["/opt/MWORKS", "/usr/local/MWORKS"],
}

_KEY_TOOLBOXES = [
    "optim",
    "stats",
    "curvefit",
    "signal",
    "images",
    "control",
    "nnet",
    "global",
    "gads",
    "parallel",
]


def _find_executable(name: str) -> Optional[str]:
    return shutil.which(name)


def _run_cmd(cmd: list[str], timeout: int = 10) -> Optional[str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return None


def _detect_matlab() -> dict:
    info: dict = {
        "available": False,
        "executable": None,
        "version": None,
        "toolboxes": [],
        "license_valid": False,
    }

    exe = _find_executable("matlab")
    if not exe:
        sys_platform = sys.platform
        for base in _COMMON_MATLAB_PATHS.get(sys_platform, []):
            if sys_platform == "win32":
                candidate = os.path.join(base, "R2024b", "bin", "matlab.exe")
                if not os.path.isfile(candidate):
                    candidate = os.path.join(base, "R2024a", "bin", "matlab.exe")
                if os.path.isfile(candidate):
                    exe = candidate
                    break
            elif sys_platform == "darwin":
                candidate = os.path.join(base, "bin", "matlab")
                if os.path.isfile(candidate):
                    exe = candidate
                    break
            else:
                for entry in _list_dirs(base):
                    candidate = os.path.join(base, entry, "bin", "matlab")
                    if os.path.isfile(candidate):
                        exe = candidate
                        break
                if exe:
                    break

    if not exe:
        return info

    info["available"] = True
    info["executable"] = exe

    ver_out = _run_cmd([exe, "-batch", "disp(version); exit"])
    if ver_out:
        m = re.search(r"(\d+\.\d+[\.\d]*)", ver_out)
        if m:
            info["version"] = m.group(1)

    tb_out = _run_cmd([exe, "-batch", "disp(string(ver)); exit"])
    if tb_out:
        for tb in _KEY_TOOLBOXES:
            if tb.lower() in tb_out.lower():
                info["toolboxes"].append(tb)

    lic_out = _run_cmd([exe, "-batch", "disp(license('test','MATLAB')); exit"])
    if lic_out and "1" in lic_out:
        info["license_valid"] = True

    return info


def _detect_bdt() -> dict:
    info: dict = {
        "available": False,
        "executable": None,
        "version": None,
        "matlab_compatible": True,
    }

    exe = _find_executable("bdt") or _find_executable("beitian")
    if not exe:
        sys_platform = sys.platform
        for base in _BDT_COMMON_PATHS.get(sys_platform, []):
            if os.path.isdir(base):
                if sys_platform == "win32":
                    for name in ("bdt.exe", "beitian.exe", "BDT.exe"):
                        candidate = os.path.join(base, "bin", name)
                        if os.path.isfile(candidate):
                            exe = candidate
                            break
                else:
                    for name in ("bdt", "beitian"):
                        candidate = os.path.join(base, "bin", name)
                        if os.path.isfile(candidate):
                            exe = candidate
                            break
                if exe:
                    break

    if not exe:
        return info

    info["available"] = True
    info["executable"] = exe

    ver_out = _run_cmd([exe, "-batch", "disp(version); exit"])
    if ver_out:
        m = re.search(r"(\d+\.\d+[\.\d]*)", ver_out)
        if m:
            info["version"] = m.group(1)

    return info


def _list_dirs(path: str) -> list[str]:
    try:
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    except Exception:
        return []


def _read_syslab_ini() -> dict:
    """读取 ~/.syslab/syslab-env.ini 的键值（MWORKS Syslab 环境配置）。"""
    ini = os.path.join(os.path.expanduser("~"), ".syslab", "syslab-env.ini")
    vals: dict = {}
    try:
        with open(ini, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith(("#", ";", "[")):
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
    except OSError:
        pass
    return vals


def _syslab_home(ini: dict) -> Optional[str]:
    home = os.environ.get("SYSLAB_HOME") or ini.get("SYSLAB_HOME")
    if home and os.path.isdir(home):
        return home
    for base in _SYSLAB_COMMON_PATHS.get(sys.platform, []):
        if os.path.isdir(base):
            for d in _list_dirs(base):
                if d.lower().startswith("syslab"):
                    p = os.path.join(base, d)
                    if os.path.isdir(p):
                        return p
    return None


def _detect_syslab() -> dict:
    """检测 MWORKS Syslab（国产 MATLAB 兼容环境，M CLI + julia-ty 双运行时）。"""
    info: dict = {
        "available": False,
        "home": None,
        "executable": None,   # M 命令行（mlang）
        "julia": None,        # Syslab Julia（julia-ty）
        "version": None,
        "matlab_compatible": True,
    }
    ini = _read_syslab_ini()
    home = _syslab_home(ini)
    if not home:
        return info

    is_win = sys.platform == "win32"
    m_cli = os.path.join(home, "Tools", "TyMLangDist", "mlang.bat" if is_win else "mlang.sh")
    if not os.path.isfile(m_cli):
        m_cli = None

    julia_home = ini.get("JULIA_HOME")
    if not julia_home or not os.path.isdir(julia_home):
        julia_home = os.path.join(home, "Tools", "julia-1.10.10")
    julia = os.path.join(julia_home, "bin", "julia-ty.bat" if is_win else "julia-ty.sh")
    if not os.path.isfile(julia) and is_win:
        julia = r"C:\Users\Public\TongYuan\julia-1.10.10\bin\julia-ty.bat"
    if not os.path.isfile(julia):
        julia = None

    version = ini.get("SYSLAB_VERSION")
    if not version:
        m = re.search(r"(\d{4}[ab])", os.path.basename(home))
        if m:
            version = m.group(1)

    info["available"] = True
    info["home"] = home
    info["executable"] = m_cli
    info["julia"] = julia
    info["version"] = version
    return info


def check_all() -> dict:
    return {
        "platform": sys.platform,
        "os": platform.system(),
        "os_version": platform.version(),
        "matlab": _detect_matlab(),
        "beitian": _detect_bdt(),
        "syslab": _detect_syslab(),
        "recommendation": _recommend(),
    }


def _recommend() -> str:
    beitian = _detect_bdt()
    syslab = _detect_syslab()
    matlab = _detect_matlab()
    if beitian["available"]:
        return "beitian"
    if syslab["available"]:
        return "syslab"
    if matlab["available"]:
        return "matlab"
    return "python_only"


def format_summary(report: dict) -> str:
    lines = [
        "=" * 50,
        "MATLAB / 北太天元 / MWORKS Syslab 环境检测报告",
        "=" * 50,
        f"操作系统: {report.get('os', '')} {report.get('os_version', '')}",
        "",
    ]

    ml = report.get("matlab") or {}
    if ml.get("available"):
        lines.append(f"[OK] MATLAB: {ml.get('executable')}")
        if ml.get("version"):
            lines.append(f"     版本: {ml.get('version')}")
        if ml.get("toolboxes"):
            lines.append(f"     关键工具箱: {', '.join(ml.get('toolboxes'))}")
        lines.append(f"     License: {'有效' if ml.get('license_valid') else '未验证'}")
    else:
        lines.append("[--] MATLAB: 未检测到")

    lines.append("")

    bt = report.get("beitian") or {}
    if bt.get("available"):
        lines.append(f"[OK] 北太天元: {bt.get('executable')}")
        if bt.get("version"):
            lines.append(f"     版本: {bt.get('version')}")
        lines.append(f"     MATLAB 兼容: {'是' if bt.get('matlab_compatible') else '未知'}")
    else:
        lines.append("[--] 北太天元: 未检测到")

    lines.append("")

    sy = report.get("syslab") or {}
    if sy.get("available"):
        lines.append(f"[OK] MWORKS Syslab: {sy.get('home')}")
        if sy.get("version"):
            lines.append(f"     版本: {sy.get('version')}")
        lines.append(f"     M 命令行: {sy.get('executable') or '未找到'}")
        lines.append(f"     Julia 运行时: {sy.get('julia') or '未找到'}")
        lines.append(f"     MATLAB 兼容: {'是' if sy.get('matlab_compatible') else '未知'}")
    else:
        lines.append("[--] MWORKS Syslab: 未检测到")

    lines.append("")
    rec = report.get("recommendation") or "python_only"
    if rec == "beitian":
        lines.append("建议: 使用北太天元（国产平台，国赛主推）")
    elif rec == "syslab":
        lines.append("建议: 使用 MWORKS Syslab（国产 MATLAB 兼容，M/Julia 双运行时）")
    elif rec == "matlab":
        lines.append("建议: 使用 MATLAB")
    else:
        lines.append("建议: 仅 Python 主线，不产出交付分支")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MATLAB/北太天元环境检测")
    parser.add_argument("--summary", action="store_true", help="人类可读摘要")
    parser.add_argument("--platform", choices=["matlab", "beitian", "syslab"], help="只检测指定平台")
    args = parser.parse_args()

    report = check_all()

    if args.platform:
        report = {
            "platform": args.platform,
            args.platform: report[args.platform],
            "recommendation": report["recommendation"],
        }

    if args.summary:
        print(format_summary(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
