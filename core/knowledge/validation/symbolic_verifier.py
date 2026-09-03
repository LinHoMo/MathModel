"""L4: Symbolic Verifier - Symbolic verification of results."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Constraint:
    name: str
    check_fn: Callable[[Any], bool]
    description: str = ""


@dataclass
class VerificationResult:
    result_name: str
    passed: bool
    constraints_checked: int
    constraints_passed: int
    failures: List[str] = field(default_factory=list)


class SymbolicVerifier:
    """Symbolic verification of results against known constraints.

    Unlike neural verification, this uses explicit constraint functions and
    symbolic reasoning to verify that results satisfy required properties.
    """

    def __init__(self) -> None:
        self._constraints: Dict[str, Constraint] = {}
        self._results: List[VerificationResult] = []

    def add_constraint(
        self, name: str, check_fn: Callable[[Any], bool], description: str = ""
    ) -> None:
        """Add a named constraint that results must satisfy."""
        self._constraints[name] = Constraint(name=name, check_fn=check_fn, description=description)

    def remove_constraint(self, name: str) -> bool:
        """Remove a constraint by name. Returns True if it existed."""
        if name in self._constraints:
            del self._constraints[name]
            return True
        return False

    def verify_result(
        self,
        result_name: str,
        value: Any,
        constraint_names: Optional[List[str]] = None,
    ) -> VerificationResult:
        """Verify a result value against specified constraints.

        Args:
            result_name: Identifier for the result being verified.
            value: The result value to check.
            constraint_names: Specific constraints to check. If None, all
                constraints are checked.

        Returns:
            VerificationResult with pass/fail status and details.
        """
        names = constraint_names or list(self._constraints.keys())
        failures: List[str] = []
        passed_count = 0

        for cname in names:
            constraint = self._constraints.get(cname)
            if constraint is None:
                failures.append(f"Constraint '{cname}' not found")
                continue
            try:
                if constraint.check_fn(value):
                    passed_count += 1
                else:
                    failures.append(f"Constraint '{cname}' failed")
            except Exception as exc:
                failures.append(f"Constraint '{cname}' raised: {exc}")

        verification = VerificationResult(
            result_name=result_name,
            passed=len(failures) == 0,
            constraints_checked=len(names),
            constraints_passed=passed_count,
            failures=failures,
        )
        self._results.append(verification)
        return verification

    def check_constraints(self, value: Any) -> Dict[str, bool]:
        """Check all constraints against a value, returning name -> pass/fail."""
        results: Dict[str, bool] = {}
        for name, constraint in self._constraints.items():
            try:
                results[name] = constraint.check_fn(value)
            except Exception:
                results[name] = False
        return results

    def symbolic_check(
        self, value: Any, expression: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Perform a symbolic check by evaluating an expression with the value.

        The expression is evaluated in a restricted namespace where 'x' is the
        value and math functions are available.
        """
        namespace: Dict[str, Any] = {"x": value, "math": math}
        if context:
            namespace.update(context)
        try:
            result = eval(expression, {"__builtins__": {}}, namespace)  # noqa: S307
            return bool(result)
        except Exception:
            return False

    def get_results(self) -> List[VerificationResult]:
        """Return all verification results."""
        return list(self._results)

    def get_constraints(self) -> List[str]:
        """Return names of all registered constraints."""
        return list(self._constraints.keys())


def create_verifier(constraints: Optional[Dict[str, Callable[[Any], bool]]] = None) -> SymbolicVerifier:
    """Convenience: create a verifier with pre-registered constraints."""
    verifier = SymbolicVerifier()
    if constraints:
        for name, fn in constraints.items():
            verifier.add_constraint(name, fn)
    return verifier
