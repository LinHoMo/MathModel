#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""finalize_k002.py — 一次性完成 v0.8 revision 收尾：
1) research 旧版 schema 标 SUPERSEDED（x-superseded_by 指向 core 真源）
2) k002_freeze.py EXTRA_FILES 加入 core MODEL_IR schema
3) k002_common.py PROTOCOL_VERSION -> 0.8
4) k002_state.py revision v0.8（若未记录）
"""
import io
import json
import subprocess
import sys

ROOT = "."

# 1) research 旧版标 SUPERSEDED
p = "research/P15/model_representation/model_ir.schema.json"
s = json.load(io.open(p, encoding="utf-8"))
s["x_superseded_by"] = "core/schemas/v3/model/model_ir.schema.json"
s["x_superseded_note"] = (
    "2026-09-09 治理：MODEL_IR 契约唯一真源已迁移至 core/schemas/v3/model/"
    "（P1 C1）。本文件保留仅作历史参考与向后引用；K002 register/freeze 均以 core 版为准。"
)
io.open(p, "w", encoding="utf-8").write(json.dumps(s, ensure_ascii=False, indent=2))
print("1) research 旧版已标 SUPERSEDED")

# 2) k002_freeze.py EXTRA_FILES 加 core schema
p = "research/P15/scripts/k002_freeze.py"
t = io.open(p, encoding="utf-8").read()
if "core/schemas/v3/model/model_ir.schema.json" not in t:
    t = t.replace(
        '    "research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md",  # v1.1 评分标准（K002 全程使用）',
        '    "research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md",  # v1.1 评分标准（K002 全程使用）\n'
        '    "core/schemas/v3/model/model_ir.schema.json",  # MODEL_IR 契约真源（P1 C1 迁移，K002 模板对齐版）',
    )
    io.open(p, "w", encoding="utf-8").write(t)
    print("2) k002_freeze.py 已加入 core MODEL_IR schema 冻结项")
else:
    print("2) k002_freeze.py 已包含 core schema（跳过）")

# 3) k002_common.py 版本
p = "research/P15/scripts/k002_common.py"
t = io.open(p, encoding="utf-8").read()
old = 'PROTOCOL_VERSION = "0.7"'
if old in t:
    t = t.replace(old, 'PROTOCOL_VERSION = "0.8"')
    io.open(p, "w", encoding="utf-8").write(t)
    print("3) k002_common PROTOCOL_VERSION -> 0.8")
else:
    print("3) PROTOCOL_VERSION 已是 0.8 或非预期（当前含 0.8:", "0.8" in t, "）")

# 4) revision v0.8
r = subprocess.run(
    [sys.executable, "research/P15/scripts/k002_state.py", "revision", "v0.8",
     "--note", "MODEL_IR 契约真源迁移 core（P1 C1）+ 词表完备化 + register 真 jsonschema + 模板同步 description/词表"],
    capture_output=True, text=True, encoding="utf-8")
print("4)", r.stdout.strip())
