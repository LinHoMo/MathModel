"""L4: Cross-Model Checker - Verify results using different approaches."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class VerificationMethod:
    name: str
    check_fn: Callable[[Any], bool]
    priority: int = 0


@dataclass
class CrossVerifyResult:
    result_name: str
    methods_used: List[str]
    all_agree: bool
    method_results: Dict[str, bool] = field(default_factory=dict)
    fallback_used: Optional[str] = None


class CrossModelChecker:
    """Verify results using multiple independent approaches.

    Uses heterogeneous models/methods to cross-check the same result.
    If primary methods disagree, a fallback method can be used.
    """

    def __init__(self) -> None:
        self._methods: Dict[str, VerificationMethod] = {}
        self._fallbacks: List[VerificationMethod] = []
        self._results: List[CrossVerifyResult] = []

    def add_method(
        self, name: str, check_fn: Callable[[Any], bool], priority: int = 0
    ) -> None:
        """Add a verification method with a priority (higher = preferred)."""
        self._methods[name] = VerificationMethod(name=name, check_fn=check_fn, priority=priority)

    def add_fallback(self, name: str, check_fn: Callable[[Any], bool]) -> None:
        """Add a fallback method used when primary methods disagree."""
        self._fallbacks.append(VerificationMethod(name=name, check_fn=check_fn))

    def remove_method(self, name: str) -> bool:
        """Remove a verification method. Returns True if it existed."""
        if name in self._methods:
            del self._methods[name]
            return True
        return False

    def cross_verify(
        self,
        result_name: str,
        value: Any,
        method_names: Optional[List[str]] = None,
    ) -> CrossVerifyResult:
        """Cross-verify a result using multiple methods.

        Args:
            result_name: Identifier for the result.
            value: The value to verify.
            method_names: Specific methods to use. If None, all methods are used.

        Returns:
            CrossVerifyResult with agreement status and per-method results.
        """
        names = method_names or sorted(
            self._methods.keys(), key=lambda n: self._methods[n].priority, reverse=True
        )

        method_results: Dict[str, bool] = {}
        for name in names:
            method = self._methods.get(name)
            if method is None:
                continue
            try:
                method_results[name] = method.check_fn(value)
            except Exception:
                method_results[name] = False

        results_list = list(method_results.values())
        all_agree = len(results_list) > 1 and all(r == results_list[0] for r in results_list)
        if len(results_list) == 1:
            all_agree = results_list[0]

        fallback_used: Optional[str] = None
        if not all_agree and results_list:
            for fb in self._fallbacks:
                try:
                    fb_result = fb.check_fn(value)
                    fallback_used = fb.name
                    method_results[f"fallback:{fb.name}"] = fb_result
                    all_agree = fb_result
                    break
                except Exception:
                    continue

        cross_result = CrossVerifyResult(
            result_name=result_name,
            methods_used=names,
            all_agree=all_agree,
            method_results=method_results,
            fallback_used=fallback_used,
        )
        self._results.append(cross_result)
        return cross_result

    def fallback_check(self, value: Any) -> Optional[bool]:
        """Run all fallback methods and return the consensus result.

        Returns True if all fallbacks agree True, False if all agree False,
        or None if fallbacks disagree or none exist.
        """
        if not self._fallbacks:
            return None

        results: List[bool] = []
        for fb in self._fallbacks:
            try:
                results.append(fb.check_fn(value))
            except Exception:
                continue

        if not results:
            return None
        if all(r == results[0] for r in results):
            return results[0]
        return None

    def get_results(self) -> List[CrossVerifyResult]:
        """Return all cross-verification results."""
        return list(self._results)

    def get_methods(self) -> List[str]:
        """Return names of all registered verification methods."""
        return list(self._methods.keys())


def create_cross_checker(
    methods: Optional[Dict[str, Callable[[Any], bool]]] = None
) -> CrossModelChecker:
    """Convenience: create a checker with pre-registered methods."""
    checker = CrossModelChecker()
    if methods:
        for name, fn in methods.items():
            checker.add_method(name, fn)
    return checker
