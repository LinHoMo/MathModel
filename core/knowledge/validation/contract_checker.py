"""L3: Contract Checker - Pre-condition and post-condition checking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Contract:
    name: str
    preconditions: List[Callable[..., bool]] = field(default_factory=list)
    postconditions: List[Callable[..., bool]] = field(default_factory=list)
    description: str = ""


@dataclass
class ContractViolation:
    contract_name: str
    kind: str  # "precondition" or "postcondition"
    index: int
    message: str


class ContractChecker:
    """Define and enforce pre-condition / post-condition contracts on functions.

    Each contract is associated with a function name and contains lists of
    precondition and postcondition check functions.
    """

    def __init__(self) -> None:
        self._contracts: Dict[str, Contract] = {}
        self._violations: List[ContractViolation] = []

    def define_contract(
        self,
        name: str,
        preconditions: Optional[List[Callable[..., bool]]] = None,
        postconditions: Optional[List[Callable[..., bool]]] = None,
        description: str = "",
    ) -> Contract:
        """Define a contract for a named function or stage.

        Args:
            name: Identifier for the contract (typically the function name).
            preconditions: List of callables that receive the same args as the
                function and return True if the precondition holds.
            postconditions: List of callables that receive the function's return
                value and return True if the postcondition holds.
            description: Human-readable description of the contract.

        Returns:
            The created Contract object.
        """
        contract = Contract(
            name=name,
            preconditions=preconditions or [],
            postconditions=postconditions or [],
            description=description,
        )
        self._contracts[name] = contract
        return contract

    def get_contract(self, name: str) -> Optional[Contract]:
        """Retrieve a contract by name."""
        return self._contracts.get(name)

    def check_precondition(self, name: str, *args: Any, **kwargs: Any) -> bool:
        """Check all preconditions for a contract.

        Returns True if all preconditions pass.  Violations are recorded.
        """
        contract = self._contracts.get(name)
        if contract is None:
            return True  # No contract defined, vacuously true

        all_pass = True
        for idx, pre in enumerate(contract.preconditions):
            try:
                if not pre(*args, **kwargs):
                    all_pass = False
                    self._violations.append(
                        ContractViolation(
                            contract_name=name,
                            kind="precondition",
                            index=idx,
                            message=f"Precondition {idx} failed for '{name}'",
                        )
                    )
            except Exception as exc:
                all_pass = False
                self._violations.append(
                    ContractViolation(
                        contract_name=name,
                        kind="precondition",
                        index=idx,
                        message=f"Precondition {idx} raised exception for '{name}': {exc}",
                    )
                )
        return all_pass

    def check_postcondition(self, name: str, result: Any) -> bool:
        """Check all postconditions for a contract given a result value.

        Returns True if all postconditions pass.  Violations are recorded.
        """
        contract = self._contracts.get(name)
        if contract is None:
            return True

        all_pass = True
        for idx, post in enumerate(contract.postconditions):
            try:
                if not post(result):
                    all_pass = False
                    self._violations.append(
                        ContractViolation(
                            contract_name=name,
                            kind="postcondition",
                            index=idx,
                            message=f"Postcondition {idx} failed for '{name}'",
                        )
                    )
            except Exception as exc:
                all_pass = False
                self._violations.append(
                    ContractViolation(
                        contract_name=name,
                        kind="postcondition",
                        index=idx,
                        message=f"Postcondition {idx} raised exception for '{name}': {exc}",
                    )
                )
        return all_pass

    def get_violations(self, name: Optional[str] = None) -> List[ContractViolation]:
        """Return recorded violations, optionally filtered by contract name."""
        if name is None:
            return list(self._violations)
        return [v for v in self._violations if v.contract_name == name]

    def clear_violations(self) -> None:
        """Clear all recorded violations."""
        self._violations.clear()


def define_contract(
    name: str,
    preconditions: Optional[List[Callable[..., bool]]] = None,
    postconditions: Optional[List[Callable[..., bool]]] = None,
) -> ContractChecker:
    """Convenience: create a checker with one pre-defined contract."""
    checker = ContractChecker()
    checker.define_contract(name, preconditions, postconditions)
    return checker
