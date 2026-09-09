#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_templates.py — 同步 S/SV 模板：description + 词表扩展（与 core schema 一致）"""
import io

for name in ["S.md", "SV.md"]:
    p = f"research/P15/protocol/frozen_specs_k002/prompt_templates/{name}"
    t = io.open(p, encoding="utf-8").read()
    repl = [
        # model_family 加 description（schema required）
        ('`{"primary": "...", "secondary": [...], "candidates": [{"family": "...", "rationale": "选择/排除依据"}]}`',
         '`{"primary": "...", "secondary": [...], "description": "<一句话说明该模型族选择>", "candidates": [{"family": "...", "rationale": "选择/排除依据"}]}`'),
        # assumptions.type 词表
        ("（projection/calibration/mechanism/simplification）",
         "（projection/calibration/mechanism/simplification/mechanism_assumption）"),
        # variables.type 词表 + binding 说明
        ("`type`（state/decision/observation/constant）、`sub_question_binding`",
         "`type`（state/decision/observation/constant/derived/parameter）、`sub_question_binding`（字符串或字符串数组）"),
        # parameters.source 词表
        ("（题目/校准/文献/假设）", "（题目/校准/文献/假设/推导）"),
        # objectives.type 词表
        ("（minimize/maximize/estimate）", "（minimize/maximize/estimate/satisfy/simulate/find）"),
        # validations.type 词表
        ("（baseline/sensitivity/limit/reproducibility）", "（baseline/sensitivity/limit/reproducibility/convergence/uncertainty）"),
    ]
    for old, new in repl:
        n = t.count(old)
        if n:
            t = t.replace(old, new)
            print(f"{name}: replaced x{n}: {old[:40]}...")
        else:
            print(f"{name}: NOT FOUND: {old[:40]}")
    io.open(p, "w", encoding="utf-8").write(t)
print("templates done")
