"""mh — Modeling-Harness（建模执行框架）统一 CLI 入口。

子命令聚合 modeling_harness/cli 下各工具；`mh <command> --help` 查看各工具细节。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

_PROJECT_ROOT = Path(__file__).resolve().parents[3]

_VERSION = "3.2.2"


def _run_validate(argv: list[str]) -> int:
    from modeling_harness.cli.validate import validate_project

    success = validate_project(str(_PROJECT_ROOT))
    return 0 if success else 1


def _run(argv: list[str], module: str) -> int:
    """以子命令视角替换 sys.argv 后调用模块 main()，保证 argparse 正确解析。"""
    import importlib

    mod = importlib.import_module(f"modeling_harness.cli.{module}")
    fn: Callable = getattr(mod, "main")
    old_argv = sys.argv
    sys.argv = [f"mh-{module}"] + list(argv)
    try:
        return int(fn())
    finally:
        sys.argv = old_argv


COMMANDS: dict[str, tuple[Callable, str]] = {
    "validate": (_run_validate, "项目级校验（四件套之一）"),
    "catalog-check": (lambda a: _run(a, "catalog_check"), "catalog 双视图三方一致"),
    "terminology": (lambda a: _run(a, "catalog_check"), "旧术语零残留检查（别名）"),
    "doctor": (lambda a: _run(a, "doctor"), "环境预检（工具链/目录/角色）"),
    "new-project": (lambda a: _run(a, "new_project"), "创建新建模项目实例"),
    "replay": (lambda a: _run(a, "replay"), "运行回放 / 校验 / diff"),
    "knowledge": (lambda a: _run(a, "knowledge"), "知识库查询工具"),
    "benchmark": (lambda a: _run(a, "benchmark"), "题库健康检查与开工演练"),
    "e2e-metrics": (lambda a: _run(a, "e2e_metrics"), "端到端指标统计"),
    "env-doctor": (lambda a: _run(a, "env_doctor"), "env 配置诊断"),
    "manifest": (lambda a: _run(a, "gen_runtime_manifest"), "生成 runtime 技能清单"),
    "cloud-sandbox": (lambda a: _run(a, "cloud_sandbox"), "云沙箱工具"),
    "diagram": (lambda a: _run(a, "diagram_gen"), "图生成工具"),
    "scholar": (lambda a: _run(a, "scholar_fetch"), "学术检索工具"),
}


def print_help() -> None:
    lines = [
        "usage: mh <command> [args...]",
        "",
        "Modeling-Harness — 面向数模竞赛与科研的可信建模执行与验证框架",
        "",
        "commands:",
    ]
    for name, (_, desc) in COMMANDS.items():
        lines.append(f"  {name:<14} {desc}")
    lines.append("")
    lines.append("run `mh <command> --help` for command details")
    print("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print_help()
        return 0
    if args[0] in ("-V", "--version"):
        print(f"mh {_VERSION} — Modeling-Harness 建模执行框架")
        return 0
    cmd, rest = args[0], args[1:]
    entry = COMMANDS.get(cmd)
    if entry is None:
        print(f"mh: unknown command {cmd!r}", file=sys.stderr)
        print_help()
        return 2
    try:
        return int(entry[0](rest))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
