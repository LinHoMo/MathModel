#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""env_doctor.py — 环境诊断与修复工具

对 env/config.yaml 进行全量校验，自动修复常见问题。

用法:
    python src/modeling_harness/cli/env_doctor.py
    python src/modeling_harness/cli/env_doctor.py --fix
    python src/modeling_harness/cli/env_doctor.py --json

零第三方依赖。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "src" / "modeling_harness" / "cli"))


from modeling_harness.env.loader import get as env_get, load_config  # noqa: E402
from pathlib import Path as _Path  # noqa: E402
CONFIG_PATH = _Path(__file__).resolve().parent.parent / "env" / "config.yaml"

_OK = "✅"
_WARN = "⚠️"
_FAIL = "❌"
_FIX = "🔧"

REQUIRED_SECTIONS = {
    "code": {"random_seed": int, "multi_run_count": int, "cv_threshold": float,
             "max_fix_rounds": int, "sensitivity_range": float},
    "modeling": {"min_candidate_models": int, "assumption_score_threshold": float},
    "review": {"max_rounds": int, "pass_score": int},
    "runtime": {"language": str, "template": str},
}


def _ok(msg: str) -> dict:
    return {"status": "ok", "icon": _OK, "message": msg}


def _warn(msg: str, **kw) -> dict:
    return {"status": "warn", "icon": _WARN, "message": msg, **kw}


def _fail(msg: str, **kw) -> dict:
    return {"status": "fail", "icon": _FAIL, "message": msg, **kw}


def check_config_exists() -> list[dict]:
    results = []
    if CONFIG_PATH.exists():
        results.append(_ok(f"config.yaml 存在: {CONFIG_PATH}"))
    else:
        results.append(_fail(f"config.yaml 不存在: {CONFIG_PATH}"))
    return results


def check_sections() -> list[dict]:
    results = []
    try:
        load_config()
    except Exception as exc:
        results.append(_fail(f"加载失败: {exc}"))
        return results

    for section, fields in REQUIRED_SECTIONS.items():
        try:
            env_get(f"{section}.{list(fields.keys())[0]}")
            results.append(_ok(f"配置节 [{section}] 存在"))
        except Exception:
            results.append(_warn(f"配置节 [{section}] 缺失或为空"))

    return results


def check_types() -> list[dict]:
    results = []
    try:
        load_config()
    except Exception:
        return results

    for section, fields in REQUIRED_SECTIONS.items():
        for field, expected_type in fields.items():
            try:
                val = env_get(f"{section}.{field}")
                if val is not None and not isinstance(val, expected_type):
                    results.append(_warn(f"{section}.{field}: 期望 {expected_type.__name__}, 实际 {type(val).__name__}"))
                else:
                    results.append(_ok(f"{section}.{field} 类型正确"))
            except Exception:
                pass

    return results


def check_values() -> list[dict]:
    results = []
    try:
        load_config()
    except Exception:
        return results

    validators = [
        ("code.random_seed", lambda v: v == 42, "应为 42"),
        ("code.cv_threshold", lambda v: 0.01 <= v <= 0.5, "应在 0.01-0.5"),
        ("modeling.assumption_score_threshold", lambda v: 1 <= v <= 10, "应在 1-10"),
        ("review.max_rounds", lambda v: 1 <= v <= 10, "应在 1-10"),
    ]

    for key, validator, desc in validators:
        try:
            val = env_get(key)
            if val is not None and not validator(val):
                results.append(_warn(f"{key}={val} 不合理 ({desc})"))
            elif val is not None:
                results.append(_ok(f"{key}={val} 合理"))
        except Exception:
            pass

    return results


def _suggest_fixes(results: list[dict]) -> list[dict]:
    fixes = []
    for r in results:
        if r["status"] == "warn" or r["status"] == "fail":
            msg = r["message"]
            if "缺失" in msg and "配置节" in msg:
                fixes.append(f"补充配置: {msg.split('配置节')[0]}")
            elif "不存在" in msg:
                fixes.append("运行 init 创建 config.yaml")
            elif "不合理" in msg:
                fixes.append(f"调整阈值: {msg}")
    return fixes


def format_text(results: list[dict]) -> str:
    lines = ["环境诊断结果:", ""]
    for r in results:
        lines.append(f"  {r['icon']} {r['message']}")

    fixes = _suggest_fixes(results)
    if fixes:
        lines.extend(["", "建议修复:"])
        for fix in fixes:
            lines.append(f"  {_FIX} {fix}")

    total = len(results)
    ok = sum(1 for r in results if r["status"] == "ok")
    warns = sum(1 for r in results if r["status"] == "warn")
    fails = sum(1 for r in results if r["status"] == "fail")
    lines.extend(["", f"总计: {total} 项, 通过: {ok}, 警告: {warns}, 失败: {fails}"])

    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="环境诊断与修复工具")
    parser.add_argument("--fix", action="store_true", help="自动修复")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args(argv)

    results = []
    results.extend(check_config_exists())
    results.extend(check_sections())
    results.extend(check_types())
    results.extend(check_values())

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(format_text(results))

    fails = sum(1 for r in results if r["status"] == "fail")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
