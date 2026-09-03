"""L6: Error Attribution - Automatically trace errors to their source."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ErrorNode:
    id: str
    message: str
    source: str  # file, function, stage, etc.
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    context: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None


@dataclass
class ErrorChain:
    error_id: str
    chain: List[ErrorNode] = field(default_factory=list)
    root_cause_id: Optional[str] = None


class ErrorAttribution:
    """Automatically trace errors to their source with root cause analysis.

    Maintains a graph of error nodes and their causal relationships,
    enabling automatic tracing from symptoms to root causes.
    """

    def __init__(self) -> None:
        self._errors: Dict[str, ErrorNode] = {}
        self._causes: Dict[str, List[str]] = {}  # error_id -> [caused_by_ids]
        self._effects: Dict[str, List[str]] = {}  # error_id -> [cause_of_ids]
        self._counter: int = 0

    def attribute_error(
        self,
        message: str,
        source: str,
        caused_by: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorNode:
        """Record an error and attribute it to a source.

        Args:
            message: Error message description.
            source: Where the error originated (file, function, stage).
            caused_by: ID of the error that caused this one (optional).
            context: Additional context about the error.

        Returns:
            The created ErrorNode.
        """
        self._counter += 1
        error_id = f"err_{self._counter}"

        node = ErrorNode(
            id=error_id,
            message=message,
            source=source,
            context=context or {},
            parent_id=caused_by,
        )
        self._errors[error_id] = node

        if caused_by:
            self._causes.setdefault(error_id, []).append(caused_by)
            self._effects.setdefault(caused_by, []).append(error_id)

        return node

    def find_root_cause(self, error_id: str) -> Optional[ErrorNode]:
        """Trace an error back to its root cause.

        Follows the cause chain until no further parent is found.
        """
        current_id = error_id
        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)
            causes = self._causes.get(current_id, [])
            if not causes:
                return self._errors.get(current_id)
            current_id = causes[0]

        return self._errors.get(current_id)

    def get_error_chain(self, error_id: str) -> ErrorChain:
        """Build the full causal chain for an error.

        Returns an ErrorChain with nodes ordered from root cause to symptom.
        """
        chain_nodes: List[ErrorNode] = []
        current_id = error_id
        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)
            node = self._errors.get(current_id)
            if node:
                chain_nodes.append(node)
            causes = self._causes.get(current_id, [])
            current_id = causes[0] if causes else None

        chain_nodes.reverse()

        root_cause = chain_nodes[0].id if chain_nodes else None
        return ErrorChain(error_id=error_id, chain=chain_nodes, root_cause_id=root_cause)

    def get_effects(self, error_id: str) -> List[ErrorNode]:
        """Get all errors caused by a given error."""
        effect_ids = self._effects.get(error_id, [])
        return [self._errors[eid] for eid in effect_ids if eid in self._errors]

    def get_error(self, error_id: str) -> Optional[ErrorNode]:
        """Retrieve an error node by ID."""
        return self._errors.get(error_id)

    def get_all_errors(self) -> List[ErrorNode]:
        """Return all recorded error nodes."""
        return list(self._errors.values())

    def get_source_errors(self, source: str) -> List[ErrorNode]:
        """Get all errors from a specific source."""
        return [e for e in self._errors.values() if e.source == source]


def create_error_attribution() -> ErrorAttribution:
    """Convenience: create an error attribution tracker."""
    return ErrorAttribution()
