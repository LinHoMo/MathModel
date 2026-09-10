"""L3: Stage Gate - Gate between Modeler, Programmer, and Writer stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class GateStatus(Enum):
    CLOSED = auto()
    OPEN = auto()
    LOCKED = auto()


@dataclass
class GateCheck:
    name: str
    passed: bool
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class StageGate:
    name: str
    status: GateStatus = GateStatus.CLOSED
    checks: List[GateCheck] = field(default_factory=list)
    checks_required: List[str] = field(default_factory=list)


class StageGateController:
    """Gate controller between Modeler -> Programmer -> Writer stages.

    Each stage transition must pass all registered checks before the gate
    opens and allows the next stage to begin.
    """

    def __init__(self) -> None:
        self._gates: Dict[str, StageGate] = {}
        self._check_fns: Dict[str, Callable[[], bool]] = {}

    def register_check(self, name: str, check_fn: Callable[[], bool]) -> None:
        """Register a named check function that must pass for a gate to open."""
        self._check_fns[name] = check_fn

    def create_gate(self, name: str, required_checks: Optional[List[str]] = None) -> StageGate:
        """Create a new stage gate with optional required check names."""
        gate = StageGate(name=name, checks_required=required_checks or [])
        self._gates[name] = gate
        return gate

    def open_gate(self, name: str) -> bool:
        """Attempt to open a gate by running all required checks.

        Returns True if the gate opened successfully.
        """
        gate = self._gates.get(name)
        if gate is None:
            return False

        if gate.status == GateStatus.LOCKED:
            return False

        all_passed = True
        for check_name in gate.checks_required:
            check_fn = self._check_fns.get(check_name)
            if check_fn is None:
                all_passed = False
                gate.checks.append(
                    GateCheck(name=check_name, passed=False, message="Check function not registered")
                )
                continue
            try:
                passed = check_fn()
            except Exception as exc:
                passed = False
            gate.checks.append(
                GateCheck(
                    name=check_name,
                    passed=passed,
                    message="OK" if passed else f"Check '{check_name}' failed",
                )
            )
            if not passed:
                all_passed = False

        if all_passed:
            gate.status = GateStatus.OPEN
        return all_passed

    def check_stage(self, name: str) -> bool:
        """Check if a gate is currently open."""
        gate = self._gates.get(name)
        if gate is None:
            return False
        return gate.status == GateStatus.OPEN

    def close_gate(self, name: str) -> None:
        """Close a gate, resetting it to CLOSED status."""
        gate = self._gates.get(name)
        if gate is not None:
            gate.status = GateStatus.CLOSED
            gate.checks.clear()

    def lock_gate(self, name: str) -> None:
        """Lock a gate so it cannot be opened."""
        gate = self._gates.get(name)
        if gate is not None:
            gate.status = GateStatus.LOCKED

    def get_gate(self, name: str) -> Optional[StageGate]:
        """Retrieve a gate by name."""
        return self._gates.get(name)

    def gate_summary(self) -> Dict[str, str]:
        """Return a mapping of gate name -> status string."""
        return {name: gate.status.name for name, gate in self._gates.items()}


def create_stage_gate(
    name: str, required_checks: Optional[List[str]] = None
) -> StageGateController:
    """Convenience: create a controller with one pre-defined gate."""
    controller = StageGateController()
    controller.create_gate(name, required_checks)
    return controller
