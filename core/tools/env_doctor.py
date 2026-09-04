"""core/tools/env_doctor.py —— 参数生效体检。

回答一个问题：**我改的参数到底生效了没有？**

用法：
    python core/tools/env_doctor.py                  # 打印当前生效参数
    python core/tools/env_doctor.py --official       # 只看官方硬约束
    python core/tools/env_doctor.py --path paper     # 只看某个组
    python core/tools/env_doctor.py --json           # 机器可读输出
    python core/tools/env_doctor.py --check          # 只做体检，有问题返回非 0

退出码：
    0  无矛盾、无被拒覆盖
    1  存在参数矛盾或被拒绝的 OFFICIAL 覆盖
    2  配置层本身不可用（schema.yaml 缺失等）
"""

import argparse
import json
import os
import sys

# core/env 在上层目录，需要把 core/ 加入模块搜索路径
_CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from env.loader import doctor_report, EnvConfigError  # noqa: E402


def _fmt_value(v):
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    return str(v)


def render(rep, only_prefix=None, official_only=False):
    lines = []
    lines.append("=" * 72)
    lines.append("MathModelSkills 参数生效体检")
    lines.append("=" * 72)

    pm = rep["profile_meta"] or {}
    lines.append("当前 profile : %s" % rep["profile"])
    if pm:
        lines.append("赛事         : %s" % pm.get("name", "?"))
        lines.append("官方核验     : verified=%s  核对日期 %s" % (
            pm.get("verified", "?"), pm.get("verified_date", "?")))
        lines.append("规则来源     : %s" % pm.get("rules_source", "?"))
        if pm.get("note"):
            lines.append("备注         : %s" % pm["note"])
    lines.append("可用 profile : %s" % ", ".join(rep["available_profiles"]))
    lines.append("")

    rows = rep["rows"]
    if only_prefix:
        rows = [r for r in rows if r["path"].startswith(only_prefix)]
    if official_only:
        rows = [r for r in rows if r["layer"] == "OFFICIAL"]

    if rows:
        lines.append("%-40s %-22s %-9s %s" % ("参数", "生效值", "层级", "来源"))
        lines.append("-" * 72)
        for r in rows:
            lines.append("%-40s %-22s %-9s %s" % (
                r["path"], _fmt_value(r["value"]), r["layer"], r["source"]))
        lines.append("")

    if rep["issues"]:
        lines.append("[参数矛盾] %d 项" % len(rep["issues"]))
        for i in rep["issues"]:
            lines.append("  ! %s" % i)
        lines.append("")

    if rep["rejected"]:
        lines.append("[被拒绝的覆盖] %d 项 —— OFFICIAL 层参数不允许用户覆盖" % len(rep["rejected"]))
        for path, want, keep in rep["rejected"]:
            lines.append("  x %s 想改成 %r，已拒绝" % (path, want))
        lines.append("")

    if not rep["issues"] and not rep["rejected"]:
        lines.append("[体检结论] 参数自洽，无被拒绝的覆盖。")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="参数生效体检")
    ap.add_argument("--official", action="store_true", help="只显示 OFFICIAL 层参数")
    ap.add_argument("--path", default=None, help="只显示指定前缀，如 paper / official")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--check", action="store_true", help="只体检不打印详情")
    args = ap.parse_args()

    try:
        rep = doctor_report()
    except EnvConfigError as e:
        sys.stderr.write("[env_doctor] 配置层不可用：%s\n" % e)
        return 2

    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    elif not args.check:
        print(render(rep, only_prefix=args.path, official_only=args.official))

    return 1 if (rep["issues"] or rep["rejected"]) else 0


if __name__ == "__main__":
    sys.exit(main())
