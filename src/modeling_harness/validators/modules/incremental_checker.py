"""L5: Incremental Checker - Runtime validation that runs incrementally."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


@dataclass
class DirtyRegion:
    start: int
    end: int
    description: str = ""

    def overlaps(self, other: "DirtyRegion") -> bool:
        return self.start <= other.end and other.start <= self.end

    def merge(self, other: "DirtyRegion") -> "DirtyRegion":
        return DirtyRegion(
            start=min(self.start, other.start),
            end=max(self.end, other.end),
            description=f"merged({self.description}, {other.description})",
        )


@dataclass
class ValidationResult:
    region: DirtyRegion
    passed: bool
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class IncrementalChecker:
    """Runtime validation that runs incrementally, only re-checking changed portions.

    Tracks dirty regions and runs validators only on those regions, avoiding
    redundant full re-checks.
    """

    def __init__(self) -> None:
        self._dirty_regions: List[DirtyRegion] = []
        self._validators: List[Tuple[str, Callable[[DirtyRegion], bool]]] = []
        self._results: List[ValidationResult] = []
        self._content: str = ""
        self._last_checked_length: int = 0

    def set_content(self, content: str) -> None:
        """Set the current content to validate."""
        self._content = content

    def add_validator(self, name: str, validator_fn: Callable[[DirtyRegion], bool]) -> None:
        """Add a named validator function that checks a dirty region."""
        self._validators.append((name, validator_fn))

    def mark_dirty(self, start: int, end: int, description: str = "") -> None:
        """Mark a region as dirty (changed)."""
        region = DirtyRegion(start=start, end=end, description=description)
        self._dirty_regions.append(region)
        self._merge_dirty_regions()

    def mark_all_dirty(self) -> None:
        """Mark the entire content as dirty."""
        self._dirty_regions = [DirtyRegion(start=0, end=len(self._content), description="full")]

    def get_dirty_regions(self) -> List[DirtyRegion]:
        """Return the current list of dirty regions (merged)."""
        self._merge_dirty_regions()
        return list(self._dirty_regions)

    def clear_dirty(self) -> None:
        """Clear all dirty regions after successful validation."""
        self._dirty_regions.clear()
        self._last_checked_length = len(self._content)

    def check_incremental(self) -> List[ValidationResult]:
        """Run validators only on dirty regions.

        Returns a list of validation results, one per region-validator pair.
        """
        self._merge_dirty_regions()
        results: List[ValidationResult] = []

        for region in self._dirty_regions:
            for validator_name, validator_fn in self._validators:
                try:
                    passed = validator_fn(region)
                except Exception as exc:
                    passed = False
                result = ValidationResult(
                    region=region,
                    passed=passed,
                    message=f"Validator '{validator_name}' {'passed' if passed else 'failed'}",
                )
                results.append(result)

        self._results.extend(results)
        if results and all(r.passed for r in results):
            self.clear_dirty()

        return results

    def validate_changes(self) -> List[ValidationResult]:
        """Validate only changes since last check.

        Automatically detects dirty regions by comparing content length.
        """
        current_len = len(self._content)
        if current_len != self._last_checked_length:
            if current_len > self._last_checked_length:
                self.mark_dirty(self._last_checked_length, current_len, "appended content")
            else:
                self.mark_dirty(current_len, self._last_checked_length, "truncated content")
        return self.check_incremental()

    def get_results(self) -> List[ValidationResult]:
        """Return all validation results."""
        return list(self._results)

    def _merge_dirty_regions(self) -> None:
        """Merge overlapping dirty regions."""
        if len(self._dirty_regions) <= 1:
            return
        self._dirty_regions.sort(key=lambda r: r.start)
        merged: List[DirtyRegion] = [self._dirty_regions[0]]
        for region in self._dirty_regions[1:]:
            if merged[-1].overlaps(region):
                merged[-1] = merged[-1].merge(region)
            else:
                merged.append(region)
        self._dirty_regions = merged


def create_incremental_checker() -> IncrementalChecker:
    """Convenience: create an incremental checker with default setup."""
    return IncrementalChecker()
