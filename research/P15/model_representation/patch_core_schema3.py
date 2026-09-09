#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_core_schema3.py — core MODEL_IR schema 补 BINDING（sub_question_binding anyOf string|string[]）
同时给 research 旧版同步标记（finalize 已做，跳过）。"""
import json
import io

p = "core/schemas/v3/model/model_ir.schema.json"
s = json.load(io.open(p, encoding="utf-8"))

BINDING = {
    "anyOf": [
        {"type": "string", "minLength": 1},
        {"type": "array", "items": {"type": "string"}},
    ]
}
n = 0
for sec in ["variables", "objectives", "constraints", "mechanisms", "equations",
            "solvers", "experiments", "validations", "claims"]:
    props = s["properties"][sec]["items"]["properties"]
    if "sub_question_binding" in props:
        old = props["sub_question_binding"]
        # 已是 anyOf 则跳过
        if old.get("anyOf"):
            continue
        props["sub_question_binding"] = BINDING
        n += 1
        print(f"{sec}: sub_question_binding -> anyOf")
print(f"patched {n} 处")
io.open(p, "w", encoding="utf-8").write(json.dumps(s, ensure_ascii=False, indent=2))
print("core schema 已写回")
