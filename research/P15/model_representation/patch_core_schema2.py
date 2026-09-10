#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_core_schema2.py — 用 JSON 语义扩展 core MODEL_IR schema 词表"""
import json
import io

p = "src/modeling_harness/schemas/v3/model/model_ir.schema.json"
s = json.load(io.open(p, encoding="utf-8"))

P = s["properties"]
P["assumptions"]["items"]["properties"]["type"]["enum"].append("mechanism_assumption")
P["variables"]["items"]["properties"]["type"]["enum"].extend(["derived", "parameter"])
P["parameters"]["items"]["properties"]["source"]["enum"].append("推导")
P["objectives"]["items"]["properties"]["type"]["enum"].extend(["satisfy", "simulate", "find"])
P["validations"]["items"]["properties"]["type"]["enum"].extend(["convergence", "uncertainty"])

for sec in ["assumptions", "variables", "parameters", "objectives", "validations"]:
    e = P[sec]["items"]["properties"]["type" if sec != "parameters" else "source"]["enum"]
    print(sec, "->", e)

io.open(p, "w", encoding="utf-8").write(
    json.dumps(s, ensure_ascii=False, indent=2))
print("core schema 已写回（indent=2 统一格式）")
