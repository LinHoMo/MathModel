# -*- coding: utf-8 -*-
"""P0-3（终审 ROADMAP）：ExecutionResult 来源鉴别——execution_token。

ExecutionResult 等事实字段只能由 execution substrate 产生（The Agent Is
Not The State）。本模块提供进程级 HMAC 签发/校验：

  issue_token(code_hash, adapter_id, timestamp) -> token
  verify_token(code_hash, adapter_id, timestamp, token) -> bool

secret 在进程启动时生成（每次运行唯一），Agent/Handler 拿不到 secret 就
无法伪造 token；registry.create("execution_result") 校验 token，伪造 EXEC
（无 token / token 无效）在登记时被拒绝。

历史 EXEC（无 token，磁盘已存在）不回溯重算；如需通过 create 登记历史
形态，必须显式标记 legacy_unverified=true（本模块提供 is_legacy 辅助）。
"""

from __future__ import annotations

import hashlib
import hmac
import os

# 进程级 secret：每次进程运行唯一。Adapter 签发与 registry 校验在同一
# 进程内完成（RuntimeSession 生命周期内）；跨进程不共享（不用于持久签名）。
_SECRET = os.urandom(32)


def issue_token(code_hash: str, adapter_id: str, timestamp: str) -> str:
    """adapter 签发 execution_token（HMAC-SHA256(code_hash|adapter|ts)）。"""
    payload = _payload(code_hash, adapter_id, timestamp)
    return hmac.new(_SECRET, payload.encode("utf-8"),
                    hashlib.sha256).hexdigest()


def verify_token(code_hash: str, adapter_id: str, timestamp: str,
                 token: str) -> bool:
    """校验 token（常数时间比较，防时序侧信道）。"""
    if not token:
        return False
    expected = issue_token(code_hash, adapter_id, timestamp)
    return hmac.compare_digest(expected, token)


def is_legacy(data: dict) -> bool:
    """历史 EXEC 豁免标记（不追溯重算，显式声明）。"""
    return bool(data.get("legacy_unverified")) is True


def _payload(code_hash: str, adapter_id: str, timestamp: str) -> str:
    return f"{code_hash}|{adapter_id}|{timestamp}"
