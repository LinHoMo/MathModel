"""L3: Invariant Tracker - Track invariants through multi-stage pipeline."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class InvariantStatus(Enum):
    OK = auto()
    VIOLATED = auto()
    UNKNOWN = auto()


@dataclass
class InvariantRecord:
    id: str
    name: str
    stage: str
    before: Any
    after: Any
    status: InvariantStatus
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message: str = ""


@dataclass
class InvariantViolation:
    record_id: str
    name: str
    stage: str
    before: Any
    after: Any
    message: str
    timestamp: str


class InvariantTracker:
    """Track invariants through a multi-stage pipeline.

    Records before/after state at each step, detects invariant violations,
    and provides a full audit trail of invariant checks.
    """

    def __init__(self) -> None:
        self._records: List[InvariantRecord] = []
        self._invariants: Dict[str, Callable[[Any, Any], bool]] = {}
        self._violations: List[InvariantViolation] = []

    def register_invariant(self, name: str, check_fn: Callable[[Any, Any], bool]) -> None:
        """Register a named invariant check function.

        The check function receives (before_state, after_state) and returns
        True if the invariant holds.
        """
        self._invariants[name] = check_fn

    def record_invariant(
        self, name: str, stage: str, before: Any, after: Any
    ) -> InvariantRecord:
        """Record before/after state at a pipeline stage and check the invariant.

        Returns the created InvariantRecord.
        """
        check_fn = self._invariants.get(name)
        if check_fn is not None:
            try:
                status = InvariantStatus.OK if check_fn(before, after) else InvariantStatus.VIOLATED
            except Exception as exc:
                status = InvariantStatus.UNKNOWN
        else:
            status = InvariantStatus.UNKNOWN

        record = InvariantRecord(
            id=str(uuid.uuid4()),
            name=name,
            stage=stage,
            before=before,
            after=after,
            status=status,
        )

        if status == InvariantStatus.VIOLATED:
            violation = InvariantViolation(
                record_id=record.id,
                name=name,
                stage=stage,
                before=before,
                after=after,
                message=f"Invariant '{name}' violated at stage '{stage}'",
                timestamp=record.timestamp,
            )
            self._violations.append(violation)

        self._records.append(record)
        return record

    def check_invariant(self, name: str, before: Any, after: Any) -> bool:
        """Manually check an invariant without recording it."""
        check_fn = self._invariants.get(name)
        if check_fn is None:
            return False
        try:
            return check_fn(before, after)
        except Exception:
            return False

    def get_violations(self, stage: Optional[str] = None) -> List[InvariantViolation]:
        """Return all invariant violations, optionally filtered by stage."""
        if stage is None:
            return list(self._violations)
        return [v for v in self._violations if v.stage == stage]

    def get_records(self, stage: Optional[str] = None) -> List[InvariantRecord]:
        """Return all invariant records, optionally filtered by stage."""
        if stage is None:
            return list(self._records)
        return [r for r in self._records if r.stage == stage]

    def has_violations(self) -> bool:
        """Return True if any invariant violations have been detected."""
        return len(self._violations) > 0

    def summary(self) -> Dict[str, Any]:
        """Return a summary of all recorded invariants and violations."""
        return {
            "total_records": len(self._records),
            "total_violations": len(self._violations),
            "by_status": {
                status.name: sum(1 for r in self._records if r.status == status)
                for status in InvariantStatus
            },
        }


def create_invariant(name: str, check_fn: Callable[[Any, Any], bool]) -> InvariantTracker:
    """Convenience: create a tracker with one pre-registered invariant."""
    tracker = InvariantTracker()
    tracker.register_invariant(name, check_fn)
    return tracker
