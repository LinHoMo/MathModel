# -*- coding: utf-8 -*-
"""P15-K001 2020_B 10 run model_ir 产前自检。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("../../scripts").resolve()))
import k001_register as R  # noqa: E402

RUNS = Path("runs")
sids = [
    "47378190-96da-4dac-b2ff-5d2a386ecbe0",
    "c241330b-01a9-471f-9e8a-774bcf36d58b",
    "6c307511-b2b9-437a-a8df-6ec4ce4a2bbd",
    "371ecd7b-27cd-4130-8722-9389571aa876",
    "1a2a73ed-562b-4f79-8374-59eef50bea63",
    "43b7a3a6-9a8d-4a03-980d-7b71d8f56413",
    "759cde66-bacf-43d0-8b1f-9163ce9ff57f",
    "ec1b8ca1-f91e-4d4c-9ff4-9b7889463e85",
    "4b0dbb41-8d52-48f1-942c-3fe860e7a113",
    "e2acf72f-9e57-4f7a-a0ee-89aed453dd32",
]
LEAK = ["armA", "armB", "armC", "armD", "armE", "sham", "knowledge", "mc-dp",
        "mc-queuing", "结构案例", "方法卡", "知识卡", "参考资料", "case-structural",
        "card_id", "case"]

all_ok = True
for sid in sids:
    p = RUNS / sid / "model_ir.json"
    try:
        ir = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(sid, "JSON ERROR", e)
        all_ok = False
        continue
    mf = json.loads((RUNS / sid / "manifest.json").read_text(encoding="utf-8"))
    ok_sha = ir["problem_binding"]["problem_sha256"] == mf["hashes"]["problem_sha256"]
    missing = [k for k in R.REQUIRED_TOP if k not in ir]
    # 排除契约强制字段 problem_card_ref（含仓库路径 P15/card.yaml，与已登记样例一致）
    scan = {k: v for k, v in ir.items() if k != "problem_binding"}
    text = json.dumps(scan, ensure_ascii=False)
    hits = [w for w in LEAK if w.lower() in text.lower()]
    det = R.compute_deterministic(ir)
    status = "OK" if (ok_sha and not missing and not hits) else "CHECK"
    if status != "OK":
        all_ok = False
    print(f"[{status}] {sid} sha={ok_sha} missing={missing or 'none'} "
          f"leak={hits or 'none'} ratio={det['undeclared_symbol_ratio']} "
          f"undeclared={det['undeclared_symbols'][:12]} "
          f"claims={det['supported_claims']}/{det['total_claims']} "
          f"sq={det['sub_question_binding_count']} fam={det['method_family_identified']}")

print("ALL_OK" if all_ok else "HAS_ISSUES")
