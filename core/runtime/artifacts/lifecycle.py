"""Artifact Lifecycle — 生命周期状态机（fail-closed）。

状态集:
    正向: draft → active → validated → published
    终态/旁路: invalidated / superseded / deprecated / blocked

转换规则（未列出的转换一律拒绝）:
    draft → active                    产出完成
    active → validated                通过 validator/critic
    validated → published             进入 deliverable
    active|validated → blocked        依赖阻塞（可恢复）
    blocked → active                  依赖恢复
    任意(非终态) → invalidated        失效传播命中（终态）
    任意(非终态) → superseded         被新版本替代（终态）
    任意(非终态) → deprecated         人工/流程废弃（终态）
    draft → draft / active → active   幂等 no-op（重放安全）
"""

from __future__ import annotations

STATES = ("draft", "active", "validated", "published",
          "blocked", "invalidated", "superseded", "deprecated")

_TERMINAL = ("invalidated", "superseded", "deprecated")

# 允许的转换表：from → {to}
_TRANSITIONS: dict[str, set[str]] = {
    "draft":      {"active", "invalidated", "superseded", "deprecated", "draft"},
    "active":     {"validated", "blocked", "invalidated", "superseded", "deprecated", "active"},
    "validated":  {"published", "blocked", "invalidated", "superseded", "deprecated", "validated"},
    "published":  {"invalidated", "superseded", "deprecated", "published"},
    "blocked":    {"active", "invalidated", "superseded", "deprecated", "blocked"},
    # 终态不可转出
    "invalidated": set(),
    "superseded":  set(),
    "deprecated":  set(),
}


class LifecycleError(ValueError):
    """非法状态转换。"""


def is_terminal(state: str) -> bool:
    return state in _TERMINAL


def can_transition(current: str, target: str) -> bool:
    if current not in STATES or target not in STATES:
        return False
    return target in _TRANSITIONS[current]


def assert_transition(current: str, target: str) -> None:
    """断言转换合法，非法则抛 LifecycleError（fail-closed）。"""
    if current not in STATES:
        raise LifecycleError(f"未知状态: {current!r}")
    if target not in STATES:
        raise LifecycleError(f"未知状态: {target!r}")
    if not can_transition(current, target):
        hint = ""
        if is_terminal(current):
            hint = f"（{current} 是终态，不可转出；如需继续请创建新 Artifact 或新版本）"
        raise LifecycleError(f"非法生命周期转换: {current} → {target}{hint}")


def next_forward(state: str) -> str | None:
    """正向主线的下一站（draft→active→validated→published），终态/旁路返回 None。"""
    return {"draft": "active", "active": "validated", "validated": "published"}.get(state)
