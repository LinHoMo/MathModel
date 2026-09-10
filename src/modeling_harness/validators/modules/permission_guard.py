"""L5: Permission Guard - Enforce file access permissions per domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set


class Permission(Enum):
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()


@dataclass
class AccessRule:
    path_pattern: str
    permissions: Set[Permission]
    domain: str = ""
    description: str = ""


@dataclass
class PermissionEntry:
    path: str
    granted: Set[Permission]
    domain: str = ""


@dataclass
class AccessViolation:
    path: str
    requested: Permission
    message: str
    timestamp: str = ""


class PermissionGuard:
    """Enforce file access permissions based on trust domains.

    Maintains a set of access rules and grants/revokes permissions for
    specific paths. Blocks unauthorized access attempts.
    """

    def __init__(self) -> None:
        self._rules: List[AccessRule] = []
        self._grants: Dict[str, PermissionEntry] = {}
        self._violations: List[AccessViolation] = []

    def add_rule(
        self,
        path_pattern: str,
        permissions: Set[Permission],
        domain: str = "",
        description: str = "",
    ) -> None:
        """Add an access rule for a path pattern."""
        self._rules.append(
            AccessRule(
                path_pattern=path_pattern,
                permissions=permissions,
                domain=domain,
                description=description,
            )
        )

    def check_permission(self, path: str, permission: Permission) -> bool:
        """Check if a permission is granted for a path.

        Returns True if allowed, False otherwise. Violations are recorded.
        """
        entry = self._grants.get(path)
        if entry is not None:
            if permission in entry.granted:
                return True

        for rule in self._rules:
            if self._match_path(path, rule.path_pattern):
                if permission in rule.permissions:
                    return True

        self._violations.append(
            AccessViolation(
                path=path,
                requested=permission,
                message=f"Permission {permission.name} denied for '{path}'",
            )
        )
        return False

    def grant_access(self, path: str, permissions: Set[Permission], domain: str = "") -> None:
        """Grant specific permissions for a path."""
        if path in self._grants:
            self._grants[path].granted.update(permissions)
        else:
            self._grants[path] = PermissionEntry(
                path=path, granted=set(permissions), domain=domain
            )

    def revoke_access(self, path: str, permissions: Optional[Set[Permission]] = None) -> None:
        """Revoke permissions for a path. If permissions is None, revoke all."""
        entry = self._grants.get(path)
        if entry is None:
            return
        if permissions is None:
            del self._grants[path]
        else:
            entry.granted -= permissions
            if not entry.granted:
                del self._grants[path]

    def get_violations(self) -> List[AccessViolation]:
        """Return all recorded access violations."""
        return list(self._violations)

    def clear_violations(self) -> None:
        """Clear all recorded violations."""
        self._violations.clear()

    def _match_path(self, path: str, pattern: str) -> bool:
        """Simple path matching: supports exact match, prefix, and wildcard."""
        if pattern == "*":
            return True
        if path == pattern:
            return True
        if pattern.endswith("*"):
            return path.startswith(pattern[:-1])
        return False


def create_permission_guard(
    rules: Optional[List[tuple[str, Set[Permission]]]] = None,
) -> PermissionGuard:
    """Convenience: create a guard with pre-configured rules."""
    guard = PermissionGuard()
    if rules:
        for pattern, perms in rules:
            guard.add_rule(pattern, perms)
    return guard
