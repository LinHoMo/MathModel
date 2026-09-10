"""Stable ID System — V3 统一对象身份。

新生成格式（tech-rebuild）：MH-<TYPE>-<NNNN>，项目内唯一、终身稳定、永不复用。
    示例：MH-MODEL-0001 / MH-QUESTION-0001 / MH-EXECUTION_RESULT-0001
历史读取兼容：旧 V3 Stable ID（<PREFIX><NNN>，如 Q001 / M002 / DATA003）仍可解析，
    仅用于读取历史数据（projects/ 冻结 run 记录）；新生成一律使用 MH- 前缀。唯一例外：question 类型显式使用题面语义 ID（Q001/Q002，见 session.py registry.create artifact_id= 注入），属 V3 领域设计，非兼容层。
版本独立于 ID（contract.version 整数递增），ID 不编码语义与路径。

前缀表（与 docs/architecture/V3.1_ARCHITECTURE.md §1.11 一致）:
    P=problem Q=question M=model A=assumption DATA=dataset CODE=code
    E=experiment R=result F=figure T=table C=claim D=decision
    DELIV=deliverable
    EXEC=execution_result（P0-E：真实执行产物，一等 artifact）
    VR=verification_result（P0-E5：对执行结果的确定性验证产物）
    MIR=model_ir DIAG=diagnosis
"""

from __future__ import annotations

import re

# 类型 → 旧 ID 前缀（历史解析用；新生成使用 MH-<TYPE>- 格式）
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
    "deliverable": "DELIV",
    "execution_result": "EXEC",
    "verification_result": "VR",
    "model_ir": "MIR",
    "diagnosis": "DIAG",
}

# 反查：旧前缀 → 类型
PREFIX_TO_TYPE: dict[str, str] = {v: k for k, v in ARTIFACT_TYPES.items()}

# 新 ID 正则：MH-<TYPE>-<NNNN>（宽松接受 1-6 位数字）
_ID_RE_NEW = re.compile(r"^MH-([A-Z][A-Z_]*)-(\d{1,6})$")
# 旧 V3 Stable ID 正则：<PREFIX><1-6 位数字>（历史数据读取兼容）
_ID_RE_LEGACY = re.compile(
    r"^(P|Q|MIR|M|A|DATA|CODE|E|R|F|T|C|D|DELIV|EXEC|VR|DIAG)(\d{1,6})$")


class IDFormatError(ValueError):
    """ID 格式非法。"""


def _parse(artifact_id: str) -> tuple[str, str, int]:
    """解析 ID → (type, prefix, number)。非法则抛 IDFormatError。"""
    m = _ID_RE_NEW.match(artifact_id or "")
    if m:
        return m.group(1).lower(), "MH", int(m.group(2))
    m = _ID_RE_LEGACY.match(artifact_id or "")
    if m:
        prefix = m.group(1)
        if prefix not in PREFIX_TO_TYPE:
            raise IDFormatError(f"未知 ID 前缀: {prefix!r}")
        return PREFIX_TO_TYPE[prefix], prefix, int(m.group(2))
    raise IDFormatError(
        f"非法 Artifact ID: {artifact_id!r}（期望如 MH-MODEL-0001 / Q001）")


def is_valid_id(artifact_id: str) -> bool:
    """判断字符串是否为合法 Stable ID（MH- 或旧 V3 格式，编号必须 ≥1）。"""
    try:
        _, _, num = _parse(artifact_id)
        return num >= 1
    except IDFormatError:
        return False


def parse_id(artifact_id: str) -> tuple[str, str, int]:
    """解析 ID → (type, prefix, number)。非法则抛 IDFormatError。"""
    return _parse(artifact_id)


def id_type(artifact_id: str) -> str:
    """返回 ID 对应的 artifact 类型。"""
    return _parse(artifact_id)[0]


def format_id(artifact_type: str, number: int) -> str:
    """生成 MH- 规范形态：MH-<TYPE>-<NNNN>（四位零填充，≥10000 不填充）。"""
    if artifact_type not in ARTIFACT_TYPES:
        raise IDFormatError(f"未知 artifact 类型: {artifact_type!r}")
    if number < 1:
        raise IDFormatError(f"编号必须 ≥1: {number}")
    body = f"MH-{artifact_type.upper()}-"
    return f"{body}{number:04d}" if number < 10000 else f"{body}{number}"


def id_matches_type(artifact_id: str, artifact_type: str) -> bool:
    """校验 ID 前缀与声明类型一致（防止 MH-MODEL-0001 声明为 question）。"""
    if artifact_type not in ARTIFACT_TYPES:
        raise IDFormatError(f"未知 artifact 类型: {artifact_type!r}")
    try:
        return id_type(artifact_id) == artifact_type
    except IDFormatError:
        return False
