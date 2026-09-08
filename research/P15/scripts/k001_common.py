#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k001_common.py — P15-K001 公共路径与哈希工具

所有 P15-K001 脚本共享的常量与工具函数。

运行要求：`py -3.12`（该解释器带 PyYAML 6.0.3 / jsonschema）。
零第三方依赖：本模块只用标准库。
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
FROZEN = PROTOCOL / "frozen_specs"
SCHEMAS = PROTOCOL / "schemas"
TEMPLATES = FROZEN / "prompt_templates"
EXP = P15 / "experiments" / "P15-K001"
BUNDLES = EXP / "bundles"
RUNS = EXP / "runs"
KEY = EXP / "key"
STATE = EXP / "state"
CASES = P15 / "cases"
ANALYSIS = P15 / "analysis"

EXPERIMENT_ID = "P15-K001"
PROTOCOL_VERSION = "1.0"
ARTIFACT_SCHEMA_VERSION = "model-ir-1.0"

ARMS = ["A", "B", "C", "D", "E"]
ARM_SPEC = {
    "A": {"knowledge": "none", "case": "none"},
    "B": {"knowledge": "relevant", "case": "none"},
    "C": {"knowledge": "none", "case": "structural"},
    "D": {"knowledge": "relevant", "case": "structural"},
    "E": {"knowledge": "sham", "case": "none"},
}


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


# ---- 规格加载 ------------------------------------------------------------
def _load_yaml():
    import yaml  # 仅在 py -3.12 环境提供
    return yaml


def load_spec(name: str) -> dict:
    path = FROZEN / name
    if not path.exists():
        raise FileNotFoundError(f"frozen spec not found: {path}")
    yaml = _load_yaml()
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_problem_set() -> dict:
    return load_spec("problem_set.yaml")


def load_knowledge_set() -> dict:
    return load_spec("knowledge_set.yaml")


def load_sham_set() -> dict:
    return load_spec("sham_set.yaml")


def load_case_set() -> dict:
    return load_spec("case_set.yaml")


def problem_index() -> dict:
    ps = load_problem_set()
    return {p["problem_id"]: p for p in ps["problems"]}


def knowledge_index() -> dict:
    return {k["problem_id"]: k for k in load_knowledge_set()["knowledge"]}


def sham_index() -> dict:
    return {s["problem_id"]: s for s in load_sham_set()["sham"]}


def case_index(layer: str = "structural") -> dict:
    cs = load_case_set()["case_layers"][layer]
    return {a["problem_id"]: a["path"] for a in cs["assets"]}


# ---- 工具 ----------------------------------------------------------------
def rel(path: Path) -> str:
    """仓库相对路径（POSIX 分隔），用于哈希与 manifest 记录。"""
    return path.resolve().relative_to(ROOT).as_posix()


def deterministic_uuid4(rng) -> str:
    """用受控随机源生成 UUID4 外观的 submission_id（保证可重放）。"""
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


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


def reference_markers() -> tuple:
    return ("<!-- BEGIN REFERENCE", "<!-- END REFERENCE -->")
