"""profiles/ — 场景 Profile 包（competition / research 两套）。

Profile = 在 base workflow（workflows/base.yaml + stages/）之上的**场景覆盖层**：
赛事 profile（competition/*.yaml）与科研 profile（research/*.yaml）以
schema_version: 3 的 yaml 声明对 stage 列表 / 节点的调整（remove_stages /
insert_after / add_nodes / remove_nodes）与场景描述。

定位与分层（依赖方向）：
    profiles 只依赖标准库与包自身（零第三方）；不依赖 runtime / roles / validators。
    runtime/execution/composer.py 通过 `profile_path(kind, name)` 寻址、
    自行解析 yaml（解析逻辑留在消费方，本包只做注册与寻址）。

数据真源：profiles/competition|research/*.yaml（单一真源，勿在别处复制）。
"""

from __future__ import annotations

from .base import AVAILABLE_PROFILES, PROFILE_KINDS, PROFILES_ROOT, ProfileError, profile_path

__all__ = [
    "AVAILABLE_PROFILES",
    "PROFILE_KINDS",
    "PROFILES_ROOT",
    "ProfileError",
    "profile_path",
]
