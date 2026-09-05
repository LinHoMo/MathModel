"""L5: Trust Domain - Three-level trust domain definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional, Set


class DomainLevel(Enum):
    INPUT = 1      # Read-only
    WORK = 2       # Read-write
    DELIVERY = 3   # Write-only


@dataclass
class DomainDefinition:
    level: DomainLevel
    name: str
    description: str = ""
    allowed_paths: Set[str] = field(default_factory=set)


@dataclass
class AccessAttempt:
    path: str
    level: DomainLevel
    operation: str  # "read", "write", "execute"
    allowed: bool
    message: str = ""


class TrustDomain:
    """Three-level trust domain system.

    Domain 1 (INPUT): Read-only access to input data.
    Domain 2 (WORK): Read-write access to working files.
    Domain 3 (DELIVERY): Write-only access to output/delivery files.
    """

    def __init__(self) -> None:
        self._domains: Dict[str, DomainDefinition] = {}
        self._access_log: list[AccessAttempt] = []
        self._initialize_default_domains()

    def _initialize_default_domains(self) -> None:
        """Set up the three default trust domains."""
        self._domains["input"] = DomainDefinition(
            level=DomainLevel.INPUT,
            name="Input Domain",
            description="Read-only access to input data",
        )
        self._domains["work"] = DomainDefinition(
            level=DomainLevel.WORK,
            name="Work Domain",
            description="Read-write access to working files",
        )
        self._domains["delivery"] = DomainDefinition(
            level=DomainLevel.DELIVERY,
            name="Delivery Domain",
            description="Write-only access to output files",
        )

    def define_domains(self, definitions: Dict[str, DomainDefinition]) -> None:
        """Define or override trust domains."""
        self._domains.update(definitions)

    def get_domain(self, path: str) -> Optional[str]:
        """Determine which domain a path belongs to."""
        for name, domain in self._domains.items():
            if path in domain.allowed_paths:
                return name
        return None

    def assign_path(self, domain_name: str, path: str) -> bool:
        """Assign a path to a domain. Returns True if domain exists."""
        domain = self._domains.get(domain_name)
        if domain is None:
            return False
        domain.allowed_paths.add(path)
        return True

    def check_access(self, path: str, operation: str) -> bool:
        """Check if an operation is allowed on a path based on its domain.

        Rules:
        - INPUT domain: only read allowed
        - WORK domain: read and write allowed
        - DELIVERY domain: only write allowed
        """
        domain_name = self.get_domain(path)
        if domain_name is None:
            attempt = AccessAttempt(
                path=path,
                level=DomainLevel.INPUT,
                operation=operation,
                allowed=False,
                message=f"Path '{path}' not assigned to any domain",
            )
            self._access_log.append(attempt)
            return False

        domain = self._domains[domain_name]
        allowed = False
        message = ""

        if domain.level == DomainLevel.INPUT:
            allowed = operation == "read"
            message = "OK" if allowed else "INPUT domain is read-only"
        elif domain.level == DomainLevel.WORK:
            allowed = operation in ("read", "write")
            message = "OK" if allowed else "WORK domain does not allow execute"
        elif domain.level == DomainLevel.DELIVERY:
            allowed = operation == "write"
            message = "OK" if allowed else "DELIVERY domain is write-only"

        attempt = AccessAttempt(
            path=path,
            level=domain.level,
            operation=operation,
            allowed=allowed,
            message=message,
        )
        self._access_log.append(attempt)
        return allowed

    def get_access_log(self) -> list[AccessAttempt]:
        """Return the full access attempt log."""
        return list(self._access_log)

    def get_domains(self) -> Dict[str, DomainDefinition]:
        """Return all domain definitions."""
        return dict(self._domains)


def create_trust_domain() -> TrustDomain:
    """Convenience: create a trust domain with default three-level setup."""
    return TrustDomain()
