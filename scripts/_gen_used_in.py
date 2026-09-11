# -*- coding: utf-8 -*-
"""为三实例参数生成 used_in 显式引用（机器扫描真实命中，非编造）。

匹配规则（保守，宁可不声明也不误声明）：
  - component（equation/objective/.../claim）文本中命中以下任一：
      parameter_id / name(长度>=2) / symbol（词边界，单字母也安全）/
      归一化符号（长度>=3 才用，避免 R/K 噪声）/ 值信号（数字串长度>=2）
  - code 文件同规则逐文件扫描，命中即 code 引用（相对路径）。
dry-run：只打印审计，不写盘；加 --write 写盘并重算 registry sha256。
"""
import json
import re
import sys
import hashlib
import datetime
from pathlib import Path

sys.path.insert(0, "src")
from modeling_harness.cli.validate import (  # noqa: E402
    _normalize_symbol, _value_signals)

ROOT = Path(".")
COMPONENT_SPECS = [
    # 只匹配数学承载字段（不收 derivation_trace/type 散文，避免单字母噪声）
    ("equation", "equations", ("latex",)),
    ("objective", "objectives", ("expression",)),
    ("constraint", "constraints", ("expression",)),
    ("mechanism", "mechanisms",
     ("description", "governing_principle")),
    ("validation", "validations", ("method",)),
    ("claim", "claims", ("text",)),
]


def _symbol_hit(sym, text):
    if not sym:
        return False
    # 单字母/数字 ASCII：裸子串会命中 \theta 内部，只允许词边界匹配
    if re.fullmatch(r"[A-Za-z0-9]", sym):
        return re.search(r"(?<![A-Za-z0-9_])" + re.escape(sym)
                         + r"(?![A-Za-z0-9_])", text) is not None
    if sym in text:
        return True
    norm = _normalize_symbol(sym)
    if len(norm) >= 3 and norm in text.upper():
        return True
    return False


def _value_hit(val, text):
    for sig in _value_signals(val):
        if sig and len(str(sig)) >= 2 and str(sig) in text:
            return True
    return False


def param_hits(par, data, code_files):
    hits = []  # (type, ref)
    pid = str(par.get("parameter_id", ""))
    name = str(par.get("name", ""))
    sym = str(par.get("symbol", ""))
    val = par.get("value")
    for typ, key, fields in COMPONENT_SPECS:
        for item in data.get(key) or []:
            if not isinstance(item, dict):
                continue
            ref = item.get(f"{typ}_id")
            text = " ".join(str(item.get(f, "")) for f in fields)
            hit = (pid and pid in text) or (len(name) >= 2 and name in text) \
                or _symbol_hit(sym, text) or _value_hit(val, text)
            if hit and ref:
                hits.append((typ, str(ref)))
    for rel, text in code_files:
        hit = (pid and pid in text) or (len(name) >= 2 and name in text) \
            or _symbol_hit(sym, text) or _value_hit(val, text)
        if hit:
            hits.append(("code", rel))
    # 去重保序
    seen = set()
    out = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def main(write=False):
    for proj in ["cumcm2024a", "cumcm2026a", "cumcm2026b"]:
        pdir = ROOT / "projects" / proj
        data = json.loads((pdir / "model_ir.json").read_text(encoding="utf-8"))
        code_files = []
        cdir = pdir / "artifacts" / "code"
        if cdir.exists():
            for cf in sorted(cdir.glob("*.py")):
                code_files.append(
                    (f"artifacts/code/{cf.name}",
                     cf.read_text(encoding="utf-8", errors="ignore")))
        zero = []
        n_refs = []
        for par in data.get("parameters") or []:
            hits = param_hits(par, data, code_files)
            n_refs.append(len(hits))
            if not hits:
                zero.append(par.get("parameter_id"))
            par["used_in"] = [{"type": t, "ref": r} for t, r in hits]
        print(f"{proj}: params={len(n_refs)} refs/param "
              f"min={min(n_refs)} max={max(n_refs)} zero-hit={zero}")
        if write:
            mir = pdir / "model_ir.json"
            mir.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            h = hashlib.sha256(mir.read_bytes()).hexdigest()
            reg_p = pdir / "state" / "registry.json"
            reg = json.loads(reg_p.read_text(encoding="utf-8"))
            reg["artifacts"]["MH-MODEL_IR-0001"]["payload"]["sha256"] = h
            reg["artifacts"]["MH-MODEL_IR-0001"]["updated_at"] = \
                datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
            reg_p.write_text(json.dumps(reg, ensure_ascii=False, indent=2),
                             encoding="utf-8")
            print(f"  written; sha256={h[:12]}")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
