"""profiles/base.py — Profile 注册契约（competition / research 两套场景）。

本模块是 profiles 包的真源实现：
- `PROFILES_ROOT`：profiles 数据目录（仓库根 /profiles）
- `profile_path(kind, name)`：返回 profiles/<kind>/<name>.yaml 的路径（不存在则抛错）
- `AVAILABLE_PROFILES`：按 kind 列出可用 profile 名

依赖方向：仅标准库；不依赖 runtime / roles / validators（可被任何层安全 import）。
yaml 内容解析由消费方（runtime/execution/composer.py）负责，本层只做注册与寻址。
"""

from __future__ import annotations

from pathlib import Path

PROFILES_ROOT = Path(__file__).resolve().parent
PROFILE_KINDS = ("competition", "research")


class ProfileError(ValueError):
    """Profile 寻址 / 注册非法。"""


def profile_path(kind: str, name: str) -> Path:
    """返回 profiles/<kind>/<name>.yaml 的路径。

    kind 必须是 PROFILE_KINDS 之一（competition / research）；
    文件不存在时抛 ProfileError。
    """
    if kind not in PROFILE_KINDS:
        raise ProfileError(f"未知 profile kind: {kind!r}（可用: {', '.join(PROFILE_KINDS)}）")
    path = PROFILES_ROOT / kind / f"{name}.yaml"
    if not path.exists():
        raise ProfileError(f"{kind} profile 不存在: {path}")
    return path


def _discover(kind: str) -> list[str]:
    d = PROFILES_ROOT / kind
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.yaml"))


AVAILABLE_PROFILES: dict[str, list[str]] = {
    kind: _discover(kind) for kind in PROFILE_KINDS
}
