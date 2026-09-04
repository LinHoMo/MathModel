"""Stable ID System — V3 统一对象身份。

ID 格式: <TYPE><NNN>，项目内唯一、终身稳定、永不复用。
版本独立于 ID（contract.version 整数递增），ID 不编码语义与路径。

前缀表（与 docs/architecture/V3.1_ARCHITECTURE.md §1.11 一致）:
    P=problem Q=question M=model A=assumption DATA=dataset CODE=code
    E=experiment R=result F=figure T=table C=claim D=decision
    N=narrative S=paper_section DELIV=deliverable
"""

from __future__ import annotations

import re

# 类型 → ID 前缀（单一真源；新增类型必须在此登记）
ARTIFACT_TYPES: dict[str, str] = {
    "problem": "P",
    "question": "Q",
    "model": "M",
    "assumption": "A",
    "dataset": "DATA",
    "code": "CODE",
    "experiment": "E",
    "result": "R",
    "figure": "F",
    "table": "T",
    "claim": "C",
    "decision": "D",
    "narrative": "N",
    "paper_section": "S",
    "deliverable": "DELIV",
}

# 反查：前缀 → 类型
PREFIX_TO_TYPE: dict[str, str] = {v: k for k, v in ARTIFACT_TYPES.items()}

# ID 正则：前缀 + 1-6 位数字（三位零填充为规范形态，宽松接受 1-6 位）
_ID_RE = re.compile(r"^(P|Q|M|A|DATA|CODE|E|R|F|T|C|D|N|S|DELIV)(\d{1,6})$")


class IDFormatError(ValueError):
    """ID 格式非法。"""


def is_valid_id(artifact_id: str) -> bool:
    """判断字符串是否为合法 Stable ID（编号必须 ≥1）。"""
    if not isinstance(artifact_id, str):
        return False
    m = _ID_RE.match(artifact_id)
    return bool(m and int(m.group(2)) >= 1 and m.group(1) in PREFIX_TO_TYPE)


def parse_id(artifact_id: str) -> tuple[str, str, int]:
    """解析 ID → (type, prefix, number)。非法则抛 IDFormatError。"""
    m = _ID_RE.match(artifact_id or "")
    if not m:
        raise IDFormatError(f"非法 Artifact ID: {artifact_id!r}（期望如 M002 / Q001 / DATA003）")
    prefix, num = m.group(1), int(m.group(2))
    if prefix not in PREFIX_TO_TYPE:
        raise IDFormatError(f"未知 ID 前缀: {prefix!r}")
    return PREFIX_TO_TYPE[prefix], prefix, num


def id_type(artifact_id: str) -> str:
    """返回 ID 对应的 artifact 类型。"""
    return parse_id(artifact_id)[0]


def format_id(prefix: str, number: int) -> str:
    """规范形态：三位零填充（≥1000 不填充）。"""
    if prefix not in PREFIX_TO_TYPE:
        raise IDFormatError(f"未知 ID 前缀: {prefix!r}")
    if number < 1:
        raise IDFormatError(f"编号必须 ≥1: {number}")
    return f"{prefix}{number:03d}" if number < 1000 else f"{prefix}{number}"


def id_matches_type(artifact_id: str, artifact_type: str) -> bool:
    """校验 ID 前缀与声明类型一致（防止 M001 声明为 question）。"""
    if artifact_type not in ARTIFACT_TYPES:
        raise IDFormatError(f"未知 artifact 类型: {artifact_type!r}")
    try:
        return id_type(artifact_id) == artifact_type
    except IDFormatError:
        return False
