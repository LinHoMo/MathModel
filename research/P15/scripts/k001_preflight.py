#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k001_preflight.py — P15-K001 运行前门禁

在 RUNNING 之前必须全绿。门禁项：

    G1  冻结项无漂移（调用 k001_freeze.py --check）
    G2  结构案例泄漏扫描通过（调用 k001_leak_scan.py）
    G3  prompt 模板：剥离参考资料段后 A–E 逐字节一致（保证 condition 是唯一变量）
    G4  bundle 完整性：数量匹配、无残留占位符、题面非空
    G5  盲评密钥完备且臂分布正确
    G6  bundle 无分组标签泄漏（不得出现 arm / sham / 负控制等字样）
    G7  参考资料长度协变量（B vs E 长度差超过容差 → WARN）

用法:
    py -3.12 research/P15/scripts/k001_preflight.py

退出码：0 = 全部通过；1 = 存在 FAIL。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k001_common as K  # noqa: E402

PY = sys.executable
BEGIN, END = K.reference_markers()

LABEL_LEAK = ["sham", "负控制", "对照实验", "实验分组", "arm ", "臂 A", "臂 B", "臂 C", "臂 D", "臂 E"]


def run(cmd: list) -> tuple:
    p = subprocess.run([PY] + cmd, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def strip_reference(text: str) -> str:
    if BEGIN in text and END in text:
        head, rest = text.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        return (head + "<!--REF-->" + tail).strip()
    return text.strip()


def g1() -> tuple:
    rc, out = run([str(K.SCRIPTS_DIR / "k001_freeze.py"), "--check"])
    return rc == 0, out.strip().splitlines()[-1] if out.strip() else ""


def g2() -> tuple:
    rc, out = run([str(K.SCRIPTS_DIR / "k001_leak_scan.py")])
    return rc == 0, "结构案例泄漏扫描"


def g3() -> tuple:
    bases = {}
    for arm in K.ARMS:
        p = K.TEMPLATES / f"{arm}.md"
        if not p.exists():
            return False, f"模板缺失: {p.name}"
        bases[arm] = strip_reference(p.read_text(encoding="utf-8"))
    ref = bases["A"]
    bad = [a for a in K.ARMS if bases[a] != ref]
    if bad:
        return False, f"剥离参考资料段后与 A 不一致: {bad}"
    return True, "A–E 模板非参考资料段逐字节一致"


def g4() -> tuple:
    order = K.read_json(K.FROZEN / "run_order.json")
    rows = order["rows"]
    bundles = sorted(p.name for p in K.BUNDLES.glob("*.md"))
    expect = sorted(f"{r['submission_id']}.md" for r in rows)
    if bundles != expect:
        return False, f"bundle 与 run_order 不匹配（bundle={len(bundles)} rows={len(rows)}）"
    for r in rows:
        t = (K.BUNDLES / f"{r['submission_id']}.md").read_text(encoding="utf-8")
        if "{{" in t:
            return False, f"残留占位符: {r['submission_id']}"
        if "{{PROBLEM_STATEMENT}}" in t:
            return False, f"题面未替换: {r['submission_id']}"
    return True, f"{len(rows)} 份 bundle 完整，无残留占位符"


def g5() -> tuple:
    cmap = K.read_json(K.KEY / "condition_map.json")["map"]
    order = K.read_json(K.FROZEN / "run_order.json")["rows"]
    sids = {r["submission_id"] for r in order}
    if set(cmap) != sids:
        return False, "condition_map 与 run_order 的 submission_id 集合不一致"
    dist = {}
    for v in cmap.values():
        dist[v["arm"]] = dist.get(v["arm"], 0) + 1
    if len(set(dist.values())) != 1:
        return False, f"臂分布不均: {dist}"
    return True, f"盲评密钥完备，臂分布 {dist}"


def g6() -> tuple:
    bad = []
    for p in sorted(K.BUNDLES.glob("*.md")):
        t = p.read_text(encoding="utf-8").lower()
        for w in LABEL_LEAK:
            if w.lower() in t:
                bad.append(f"{p.name}:{w}")
                break
    if bad:
        return False, f"bundle 含分组标签泄漏 {len(bad)} 处，例: {bad[:3]}"
    return True, "bundle 无分组标签泄漏"


def g7() -> tuple:
    """参考资料长度协变量：比较 B 与 E 的 reference_chars（按题）。"""
    cmap = K.read_json(K.KEY / "condition_map.json")["map"]
    by = {}
    for sid, v in cmap.items():
        m = K.read_json(K.RUNS / sid / "manifest.json")
        by.setdefault((v["problem_id"], v["arm"]), []).append(m["reference_chars"])
    lines, warn = [], []
    for pid in sorted({k[0] for k in by}):
        b = sum(by.get((pid, "B"), [0])) / max(1, len(by.get((pid, "B"), [1])))
        e = sum(by.get((pid, "E"), [0])) / max(1, len(by.get((pid, "E"), [1])))
        ratio = abs(b - e) / b if b else 0.0
        lines.append(f"    {pid}: B={b:.0f} E={e:.0f} 差比={ratio:.1%}")
        if ratio > 0.15:
            warn.append(f"{pid} 差比 {ratio:.1%} > 15%")
    ok = True
    msg = "参考资料长度协变量:\n" + "\n".join(lines)
    if warn:
        msg += "\n    [WARN] " + "; ".join(warn) + "（Sham 控制力下降，需在报告声明）"
    return ok, msg


def main() -> int:
    gates = [("G1", "冻结无漂移", g1), ("G2", "案例无泄漏", g2), ("G3", "模板一致", g3),
             ("G4", "bundle 完整", g4), ("G5", "盲评密钥", g5), ("G6", "无标签泄漏", g6),
             ("G7", "长度协变量", g7)]
    print("=" * 72)
    print(f"P15-K001 PREFLIGHT  （protocol v{K.PROTOCOL_VERSION}）")
    print("=" * 72)
    failed = []
    for gid, name, fn in gates:
        ok, msg = fn()
        print(f"[{'PASS' if ok else 'FAIL'}] {gid} {name}: {msg}")
        if not ok:
            failed.append(gid)
    print("-" * 72)
    if failed:
        print(f"[FAIL] PREFLIGHT 未通过：{', '.join(failed)}。禁止进入 RUNNING。")
        return 1
    print("[PASS] PREFLIGHT 全绿，可进入 RUNNING。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
