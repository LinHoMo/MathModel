#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_core_schema.py — core MODEL_IR schema 词表完备化（多行 enum 块替换）"""
import io

p = "core/schemas/v3/model/model_ir.schema.json"
t = io.open(p, encoding="utf-8").read()

blocks = [
    (
        '"enum": [\n                "projection",\n                "calibration",\n                "mechanism",\n                "simplification"\n              ]',
        '"enum": [\n                "projection",\n                "calibration",\n                "mechanism",\n                "simplification",\n                "mechanism_assumption"\n              ]',
    ),
    (
        '"enum": [\n                "state",\n                "decision",\n                "observation",\n                "constant"\n              ]',
        '"enum": [\n                "state",\n                "decision",\n                "observation",\n                "constant",\n                "derived",\n                "parameter"\n              ]',
    ),
    (
        '"enum": [\n                "\u9898\u76ee",\n                "\u6821\u51c6",\n                "\u6587\u732e",\n                "\u5047\u8bbe"\n              ]',
        '"enum": [\n                "\u9898\u76ee",\n                "\u6821\u51c6",\n                "\u6587\u732e",\n                "\u5047\u8bbe",\n                "\u63a8\u5bfc"\n              ]',
    ),
    (
        '"enum": [\n                "minimize",\n                "maximize",\n                "estimate"\n              ]',
        '"enum": [\n                "minimize",\n                "maximize",\n                "estimate",\n                "satisfy",\n                "simulate",\n                "find"\n              ]',
    ),
    (
        '"enum": [\n                "baseline",\n                "sensitivity",\n                "limit",\n                "reproducibility"\n              ]',
        '"enum": [\n                "baseline",\n                "sensitivity",\n                "limit",\n                "reproducibility",\n                "convergence",\n                "uncertainty"\n              ]',
    ),
]
for old, new in blocks:
    n = t.count(old)
    if n:
        t = t.replace(old, new)
        print(f"replaced x{n}: {old.splitlines()[1].strip()}...")
    else:
        print(f"NOT FOUND: {old.splitlines()[1].strip()}")
io.open(p, "w", encoding="utf-8").write(t)
print("done")
