"""Role 层 — Capability Composition 的命名模板（V3 P3）。

Role = 能力组合的命名模板；Agent = 承载 Role 的运行时执行器。
定义于 core/roles/*.yaml（5 个），加载后可校验 DAG 节点的 role 引用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .execution.yamlio import YamlSyntaxError, load_file

ROLE_IDS = ("analyst", "modeler", "experimenter", "critic", "writer")


class RoleError(ValueError):
    """Role 契约违反。"""


@dataclass
class Role:
    role: str
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    executes: list[str] = field(default_factory=list)   # 可执行的 DAG 节点名

    @classmethod
    def from_dict(cls, d: dict, where: str) -> "Role":
        role = d.get("role")
        if not isinstance(role, str) or role not in ROLE_IDS:
            raise RoleError(
                f"{where}: role 非法 {role!r}，须为 {ROLE_IDS} 之一")
        caps = d.get("capabilities")
        if not isinstance(caps, list) or not caps or \
                not all(isinstance(c, str) for c in caps):
            raise RoleError(f"{where}: capabilities 须为非空字符串列表")
        executes = d.get("executes", [])
        if not isinstance(executes, list) or \
                not all(isinstance(c, str) for c in executes):
            raise RoleError(f"{where}: executes 须为字符串列表")
        return cls(role=role, description=d.get("description", "") or "",
                   capabilities=caps, executes=executes)


def load_roles(roles_root: str | Path) -> dict[str, Role]:
    """加载 core/roles/*.yaml → {role_id: Role}（fail-closed，缺一不可）。"""
    root = Path(roles_root)
    roles: dict[str, Role] = {}
    for f in sorted(root.glob("*.yaml")):
        try:
            d = load_file(f)
        except YamlSyntaxError as exc:
            raise RoleError(f"core/roles/{f.name}: YAML 解析失败: {exc}") from exc
        if not isinstance(d, dict):
            raise RoleError(f"core/roles/{f.name}: 顶层须为映射")
        r = Role.from_dict(d, f"core/roles/{f.name}")
        if r.role in roles:
            raise RoleError(f"core/roles/{f.name}: role '{r.role}' 重复定义")
        roles[r.role] = r
    missing = set(ROLE_IDS) - set(roles)
    if missing:
        raise RoleError(f"core/roles/ 缺少 Role 定义: {sorted(missing)}")
    return roles


def validate_dag_roles(dag, roles: dict[str, Role]) -> list[str]:
    """校验 DAG 中每个节点的 role 引用合法（无 role 的节点不校验）。"""
    problems: list[str] = []
    for nid, node in dag.nodes.items():
        if not node.role:
            continue
        if node.role not in roles:
            problems.append(f"节点 {nid} 引用不存在的 role: {node.role}")
            continue
        r = roles[node.role]
        base = nid.split("@")[0]           # per_question 实例按基名校验
        if r.executes and base not in r.executes:
            problems.append(
                f"节点 {nid}（{base}）不在 role '{node.role}' 的 executes 列表中")
    return problems
