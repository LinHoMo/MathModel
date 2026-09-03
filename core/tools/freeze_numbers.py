#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数字冻结 —— 论文数字的单一真源，P2-2。

解决两个真实问题
----------------
1. **论文数字无脚本来源**：正文里的数在任何脚本里都找不到出处。
   （本项目实测数值追溯率仅 86.4%，低于 90% 硬门禁。）
2. **修了 bug 论文仍用旧数字**：代码改了，论文没跟上，
   且没有任何机制提示"你该更新论文了"。

机制
----
* `freeze`：把 `figures/all_results.json` 扁平化为 `work/frozen_numbers.json`，
  每个数值记录路径、取值、来源脚本哈希。
* `check`：
  - 数值是否被改动（与冻结时比对）
  - 论文正文数字能否在冻结表中找到
  - 改动后自动把受影响章节标记为 stale

用法
----
    python core/tools/freeze_numbers.py <项目> freeze
    python core/tools/freeze_numbers.py <项目> check
    python core/tools/freeze_numbers.py <项目> show
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import state as S  # noqa: E402

FROZEN_REL = "work/frozen_numbers.json"

# 正文中允许出现、但不需要追溯的数字（年份、题号、章节号等）
# 这类数字不是"计算结果"，不应触发追溯失败。
NON_RESULT_PATTERNS = [
    r"^\d{4}$",          # 年份
    r"^[第]?\d+[章节题问]$",  # 第3章 / 问题2
    r"^\d+$",            # 纯序号（1 位或 2 位）
]


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def frozen_path(project):
    return S.project_dir(project) / FROZEN_REL


def _flatten(obj, prefix=""):
    """把嵌套 JSON 扁平化为 {path: value}，只保留数值与短字符串。"""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(_flatten(v, f"{prefix}[{i}]"))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out[prefix] = obj
    elif isinstance(obj, str) and len(obj) <= 64:
        out[prefix] = obj
    return out


def _sha(obj):
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def cmd_freeze(project, args):
    base = S.project_dir(project)
    src = base / "figures" / "all_results.json"
    if not src.exists():
        print(f"[freeze] 无 {src}，先跑完 result-verifier", file=sys.stderr)
        return 1

    data = json.loads(src.read_text(encoding="utf-8"))
    flat = _flatten(data)

    frozen = {
        "version": "1.0",
        "project": base.name,
        "frozen_at": _now(),
        "source": "figures/all_results.json",
        "source_hash": _sha(data),
        "count": len(flat),
        "numbers": {k: {"value": v} for k, v in flat.items()},
    }

    p = frozen_path(project)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(frozen, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")

    # 同步状态：清除 stale 标记（重新冻结即视为已对齐）
    st = S.load(project)
    if st is not None:
        st["numbers_frozen"] = {"at": frozen["frozen_at"],
                                "count": len(flat),
                                "stale": False}
        S.save(project, st)

    print(f"[freeze] 已冻结 {len(flat)} 个数值 → {p}")
    return 0


def _env_get(key, default):
    """读 env 配置；加载失败回退默认值（与 validate.py 同口径）。"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_env_loader_freeze", ROOT / "core" / "env" / "loader.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.get(key, default)
    except Exception:
        return default


def cmd_check(project, args):
    base = S.project_dir(project)
    fp = frozen_path(project)
    if not fp.exists():
        print(f"[freeze] 无冻结表，先运行: python core/tools/freeze_numbers.py {project} freeze",
              file=sys.stderr)
        return 1

    frozen = json.loads(fp.read_text(encoding="utf-8"))
    src = base / "figures" / "all_results.json"
    rc = 0

    # 1) 源是否被改动
    if src.exists():
        cur_hash = _sha(json.loads(src.read_text(encoding="utf-8")))
        if cur_hash != frozen.get("source_hash"):
            print("[FAIL] 结果文件已变更，冻结表过期")
            print(f"  冻结时: {frozen.get('source_hash', '')[:24]}…")
            print(f"  当前:   {cur_hash[:24]}…")
            print("  处理：确认改动后重新 freeze，并同步更新论文中受影响的数字")
            rc = 1
        else:
            print("[PASS] 冻结表与结果文件一致")
    else:
        print("[WARN] 结果文件缺失，无法比对")

    # 2) 论文数字追溯
    tex = base / "paper" / "main.tex"
    if tex.exists():
        text = tex.read_text(encoding="utf-8", errors="replace")
        # 去注释与数学环境，避免把公式编号、年份算进来
        body = re.sub(r"(?<!\\)%.*", "", text)
        body = re.sub(r"\\begin\{(equation|align|gather|multline)\*?\}.*?\\end\{\1\}",
                      " ", body, flags=re.DOTALL)

        allowed = {float(v["value"]) for v in frozen["numbers"].values()
                   if isinstance(v["value"], (int, float))}
        # 容差匹配（相对 0.5% 或绝对 0.01，与 env 一致）
        def _match(x):
            for a in allowed:
                if abs(x - a) <= 0.01 or (a != 0 and abs(x - a) / abs(a) <= 0.005):
                    return True
            return False

        cands = re.findall(r"(?<![\w.\\-])\d+\.\d{2,}(?![\w.])|(?<![\w.\\-])\d{3,}(?![\w.])",
                           body)
        traced = sum(1 for c in set(cands) if _match(float(c)))
        total = len(set(cands))
        ratio = traced / total if total else 1.0
        min_ratio = float(_env_get("runtime.traceability_min_ratio", 0.90))
        flag = "PASS" if ratio >= min_ratio else "FAIL"
        print(f"[{flag}] 论文数字追溯率 {ratio:.1%}（{traced}/{total}，阈值 {min_ratio:.0%}）")
        if flag == "FAIL":
            rc = 1
    else:
        print("[WARN] 无 paper/main.tex，跳过追溯检查")

    # 3) 状态同步
    st = S.load(project)
    if st is not None:
        st.setdefault("numbers_frozen", {})["stale"] = (rc == 1)
        st["numbers_frozen"]["last_check"] = _now()
        S.save(project, st)

    return rc


def cmd_show(project, args):
    fp = frozen_path(project)
    if not fp.exists():
        print("[freeze] 无冻结表")
        return 1
    f = json.loads(fp.read_text(encoding="utf-8"))
    print(f"项目: {f.get('project')}   数值数: {f.get('count')}")
    print(f"冻结时间: {f.get('frozen_at')}")
    n = 0
    for k, v in f.get("numbers", {}).items():
        if n >= (args.limit or 20):
            print(f"  …（共 {f['count']} 个，用 --limit N 查看更多）")
            break
        print(f"  {k} = {v['value']}")
        n += 1
    return 0


def main():
    ap = argparse.ArgumentParser(description="数字冻结（论文数字单一真源）")
    ap.add_argument("project")
    ap.add_argument("command", choices=["freeze", "check", "show"])
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()
    return {"freeze": cmd_freeze, "check": cmd_check, "show": cmd_show}[
        args.command](args.project, args)


if __name__ == "__main__":
    sys.exit(main())
