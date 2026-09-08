# -*- coding: utf-8 -*-
"""最终核验：10 个 run 的登记状态与主方法族。"""
import json
from pathlib import Path

plan = [
    ("6", "47378190-96da-4dac-b2ff-5d2a386ecbe0"),
    ("7", "c241330b-01a9-471f-9e8a-774bcf36d58b"),
    ("8", "6c307511-b2b9-437a-a8df-6ec4ce4a2bbd"),
    ("9", "371ecd7b-27cd-4130-8722-9389571aa876"),
    ("10", "1a2a73ed-562b-4f79-8374-59eef50bea63"),
    ("11", "43b7a3a6-9a8d-4a03-980d-7b71d8f56413"),
    ("12", "759cde66-bacf-43d0-8b1f-9163ce9ff57f"),
    ("13", "ec1b8ca1-f91e-4d4c-9ff4-9b7889463e85"),
    ("14", "4b0dbb41-8d52-48f1-942c-3fe860e7a113"),
    ("15", "e2acf72f-9e57-4f7a-a0ee-89aed453dd32"),
]
all_ok = True
for seq, sid in plan:
    m = json.loads((Path("runs") / sid / "manifest.json").read_text(encoding="utf-8"))
    ir = json.loads((Path("runs") / sid / "model_ir.json").read_text(encoding="utf-8"))
    ok = m["status"] == "REGISTERED" and m["generator"]["agent_identity"] == "doubao"
    all_ok &= ok
    print(f"seq {seq} | {sid[:8]} | arm={m['condition']['arm']} | {m['status']} | "
          f"gen={m['generator']['agent_identity']}/{m['generator']['model_version']} | "
          f"fam={ir['model_family']['primary']} | latency={m['cost']['latency_seconds']} | "
          f"pt={m['cost']['prompt_tokens']} ct={m['cost']['completion_tokens']}")
print("ALL_REGISTERED_OK" if all_ok else "SOME_NOT_OK")
