#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k002_common.py — P15-K002 公共路径与哈希工具

P15-K002 是 Model Representation Efficacy 实验：三臂 F/S/S+V（无知识/Sham 注入）。
复用 k001_common 的模式，但 EXP 路径与臂定义不同。

运行要求：`py -3.12`。零第三方依赖（PyYAML 除外）。
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---- 路径 ----------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
P15 = SCRIPTS_DIR.parent                       # research/P15
ROOT = P15.parent.parent                       # 仓库根

PROTOCOL = P15 / "protocol"
FROZEN = PROTOCOL / "frozen_specs_k002"
SCHEMAS = PROTOCOL / "schemas"
TEMPLATES = FROZEN / "prompt_templates"
EXP = P15 / "experiments" / "P15-K002"
BUNDLES = EXP / "bundles"
RUNS = EXP / "runs"
KEY = EXP / "key"
STATE = EXP / "state"
CASES = P15 / "cases"
ANALYSIS = P15 / "analysis"
DRYRUN = P15 / "dryrun"
BENCH = P15 / "benchmark"
PROBLEM_CARDS = BENCH / "problem_cards"

EXPERIMENT_ID = "P15-K002"
PROTOCOL_VERSION = "0.8"
ARTIFACT_SCHEMA_VERSION = "model-ir-1.0"

ARMS = ["F", "S", "SV"]
ARM_SPEC = {
    "F": {"representation": "free", "validation_plan": False},
    "S": {"representation": "model_ir", "validation_plan": False},
    "SV": {"representation": "model_ir", "validation_plan": True},
}

# K002 主检验 6 题（K001 既有 3 + 新增 3，Input Authenticity 全部 verified）
PRIMARY_BLOCKS = ["2020_B", "2018_A", "2019_C", "2018_B", "2017_B", "2011_B"]
GENERALIZATION_BLOCKS = ["2022_C", "2024_A"]
REPLICATES_PRIMARY = 5
REPLICATES_GENERALIZATION = 3
SEEDS = [42, 43, 44, 45, 46]


# ---- 哈希 ----------------------------------------------------------------
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_obj(obj: Any) -> str:
    return sha256_text(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def deterministic_uuid4(rng) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def reference_markers() -> tuple:
    return ("<!-- BEGIN REFERENCE", "<!-- END REFERENCE -->")
