"""L6: Rule Iterator - Automated rule update based on error patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Rule:
    id: str
    name: str
    condition: str  # human-readable condition description
    check_fn: Optional[Callable[[Any], bool]] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorPattern:
    pattern_id: str
    description: str
    count: int = 0
    affected_rules: List[str] = field(default_factory=list)
    suggested_fix: str = ""


@dataclass
class RuleUpdate:
    rule_id: str
    old_condition: str
    new_condition: str
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RuleIterator:
    """Automated rule update based on error patterns.

    Analyzes failure modes and suggests rule changes to prevent future errors.
    Tracks which rules are triggered by errors and iteratively improves them.
    """

    def __init__(self) -> None:
        self._rules: Dict[str, Rule] = {}
        self._error_patterns: Dict[str, ErrorPattern] = {}
        self._rule_errors: Dict[str, List[str]] = {}  # rule_id -> [error_messages]
        self._updates: List[RuleUpdate] = []
        self._counter: int = 0

    def add_rule(
        self,
        name: str,
        condition: str,
        check_fn: Optional[Callable[[Any], bool]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Rule:
        """Add a new validation rule."""
        self._counter += 1
        rule_id = f"rule_{self._counter}"
        rule = Rule(
            id=rule_id,
            name=name,
            condition=condition,
            check_fn=check_fn,
            metadata=metadata or {},
        )
        self._rules[rule_id] = rule
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def record_error(self, rule_id: str, error_message: str) -> None:
        """Record that a rule failed with a specific error message."""
        self._rule_errors.setdefault(rule_id, []).append(error_message)

        pattern_key = error_message
        if pattern_key not in self._error_patterns:
            self._error_patterns[pattern_key] = ErrorPattern(
                pattern_id=pattern_key,
                description=error_message,
            )
        self._error_patterns[pattern_key].count += 1
        if rule_id not in self._error_patterns[pattern_key].affected_rules:
            self._error_patterns[pattern_key].affected_rules.append(rule_id)

    def analyze_patterns(self, min_count: int = 2) -> List[ErrorPattern]:
        """Analyze error patterns that occur at least min_count times.

        Returns patterns sorted by frequency (most common first).
        """
        patterns = [
            p for p in self._error_patterns.values() if p.count >= min_count
        ]
        patterns.sort(key=lambda p: p.count, reverse=True)
        return patterns

    def suggest_updates(self, min_count: int = 2) -> List[Dict[str, Any]]:
        """Suggest rule updates based on recurring error patterns.

        Returns a list of suggestions with rule_id, pattern, and suggested fix.
        """
        patterns = self.analyze_patterns(min_count)
        suggestions: List[Dict[str, Any]] = []

        for pattern in patterns:
            for rule_id in pattern.affected_rules:
                rule = self._rules.get(rule_id)
                if rule is None:
                    continue
                suggestions.append({
                    "rule_id": rule_id,
                    "rule_name": rule.name,
                    "pattern": pattern.description,
                    "occurrence_count": pattern.count,
                    "current_condition": rule.condition,
                    "suggested_fix": pattern.suggested_fix or f"Refine rule to handle: {pattern.description}",
                })

        return suggestions

    def apply_updates(self, updates: List[RuleUpdate]) -> List[bool]:
        """Apply a list of rule updates.

        Returns a list of booleans indicating success for each update.
        """
        results: List[bool] = []
        for update in updates:
            rule = self._rules.get(update.rule_id)
            if rule is None:
                results.append(False)
                continue
            rule.condition = update.new_condition
            self._updates.append(update)
            results.append(True)
        return results

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Retrieve a rule by ID."""
        return self._rules.get(rule_id)

    def get_rules(self) -> List[Rule]:
        """Return all rules."""
        return list(self._rules.values())

    def get_updates(self) -> List[RuleUpdate]:
        """Return all applied rule updates."""
        return list(self._updates)

    def get_rule_errors(self, rule_id: str) -> List[str]:
        """Return error messages associated with a rule."""
        return list(self._rule_errors.get(rule_id, []))


def create_rule_iterator() -> RuleIterator:
    """Convenience: create an empty rule iterator."""
    return RuleIterator()
