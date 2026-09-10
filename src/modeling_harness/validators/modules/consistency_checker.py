"""L4: Consistency Checker - Check numerical consistency between paper and code."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class NumberCheck:
    label: str
    paper_value: Any
    code_value: Any
    match: bool
    message: str = ""


@dataclass
class CitationCheck:
    reference: str
    found_in_paper: bool
    found_in_code: bool
    message: str = ""


@dataclass
class FigureCheck:
    figure_ref: str
    found_in_paper: bool
    found_in_code: bool
    message: str = ""


@dataclass
class ConsistencyReport:
    numbers: List[NumberCheck] = field(default_factory=list)
    citations: List[CitationCheck] = field(default_factory=list)
    figures: List[FigureCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return (
            all(c.match for c in self.numbers)
            and all(c.found_in_paper == c.found_in_code for c in self.citations)
            and all(c.found_in_paper == c.found_in_code for c in self.figures)
        )

    @property
    def failure_count(self) -> int:
        return (
            sum(1 for c in self.numbers if not c.match)
            + sum(1 for c in self.citations if c.found_in_paper != c.found_in_code)
            + sum(1 for c in self.figures if c.found_in_paper != c.found_in_code)
        )


class ConsistencyChecker:
    """Check numerical consistency between paper text and code output.

    Verifies that numbers, citations, and figure references in the paper
    match what the code produces or references.
    """

    def __init__(self) -> None:
        self._number_checks: List[Tuple[str, Any, Any]] = []
        self._paper_text: str = ""
        self._code_text: str = ""

    def set_paper_text(self, text: str) -> None:
        """Set the paper/source text to check against."""
        self._paper_text = text

    def set_code_text(self, text: str) -> None:
        """Set the code/source text to check against."""
        self._code_text = text

    def add_number_pair(self, label: str, paper_value: Any, code_value: Any) -> None:
        """Add a paper/code number pair for consistency checking."""
        self._number_checks.append((label, paper_value, code_value))

    def check_numbers(self) -> List[NumberCheck]:
        """Check all registered number pairs for consistency."""
        results: List[NumberCheck] = []
        for label, paper_val, code_val in self._number_checks:
            match = paper_val == code_val
            results.append(
                NumberCheck(
                    label=label,
                    paper_value=paper_val,
                    code_value=code_val,
                    match=match,
                    message="Match" if match else f"Mismatch: paper={paper_val}, code={code_val}",
                )
            )
        return results

    def check_citations(self, references: Optional[List[str]] = None) -> List[CitationCheck]:
        """Check that citations are present in both paper and code text."""
        if references is None:
            references = self._extract_citations(self._paper_text)

        results: List[CitationCheck] = []
        for ref in references:
            in_paper = ref in self._paper_text
            in_code = ref in self._code_text
            results.append(
                CitationCheck(
                    reference=ref,
                    found_in_paper=in_paper,
                    found_in_code=in_code,
                    message="Consistent" if in_paper == in_code else "Inconsistent reference",
                )
            )
        return results

    def check_figures(self, figure_refs: Optional[List[str]] = None) -> List[FigureCheck]:
        """Check that figure references appear in both paper and code."""
        if figure_refs is None:
            figure_refs = self._extract_figure_refs(self._paper_text)

        results: List[FigureCheck] = []
        for fig_ref in figure_refs:
            in_paper = fig_ref in self._paper_text
            in_code = fig_ref in self._code_text
            results.append(
                FigureCheck(
                    figure_ref=fig_ref,
                    found_in_paper=in_paper,
                    found_in_code=in_code,
                    message="Consistent" if in_paper == in_code else "Inconsistent figure ref",
                )
            )
        return results

    def full_report(self) -> ConsistencyReport:
        """Generate a full consistency report across numbers, citations, and figures."""
        return ConsistencyReport(
            numbers=self.check_numbers(),
            citations=self.check_citations(),
            figures=self.check_figures(),
        )

    def _extract_citations(self, text: str) -> List[str]:
        """Extract citation references like [1], [Smith 2020], etc."""
        bracket_cites = re.findall(r"\[\d+(?:,\s*\d+)*\]", text)
        author_cites = re.findall(r"\[[A-Z][a-z]+(?:\s+et\s+al\.?)?,\s*\d{4}\]", text)
        return list(set(bracket_cites + author_cites))

    def _extract_figure_refs(self, text: str) -> List[str]:
        """Extract figure references like Fig. 1, Figure 2, etc."""
        return list(set(re.findall(r"(?:Fig\.|Figure)\s*\d+", text)))


def create_consistency_checker(
    paper_text: str = "", code_text: str = ""
) -> ConsistencyChecker:
    """Convenience: create a checker with initial text set."""
    checker = ConsistencyChecker()
    if paper_text:
        checker.set_paper_text(paper_text)
    if code_text:
        checker.set_code_text(code_text)
    return checker
