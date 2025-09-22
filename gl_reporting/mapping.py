"""Mapping rules between general ledger accounts and reporting lines."""
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import List, Optional, Sequence
import csv


@dataclass(frozen=True)
class MappingRule:
    """Associates an account pattern to a reporting category."""

    pattern: str
    category: str
    label: Optional[str] = None
    sign: int = 1

    def matches(self, account: str) -> bool:
        return fnmatch(account, self.pattern)

    @property
    def specificity(self) -> int:
        return sum(1 for char in self.pattern if char not in {"*", "?"})


class MappingTable:
    """Ordered collection of mapping rules with helper methods."""

    def __init__(self, rules: Sequence[MappingRule]):
        # Sort once to avoid recomputing at lookup time. More specific rules first.
        self._rules: List[MappingRule] = sorted(
            rules, key=lambda rule: (-rule.specificity, rule.pattern)
        )

    def __iter__(self):  # pragma: no cover - simple iterator
        return iter(self._rules)

    def match(self, account: str) -> Optional[MappingRule]:
        for rule in self._rules:
            if rule.matches(account):
                return rule
        return None


def _parse_sign(value: str) -> int:
    cleaned = value.strip()
    if not cleaned:
        return 1
    try:
        numeric = int(cleaned)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid sign value: {value!r}") from exc
    if numeric not in {1, -1}:
        raise ValueError(f"Sign must be 1 or -1, got {numeric}")
    return numeric


def load_mapping(path: str, encoding: str = "utf-8") -> MappingTable:
    """Loads the mapping table from a CSV file.

    The file must contain the columns ``pattern`` and ``category``. Optional
    columns are ``label`` (a human readable description) and ``sign`` which allows
    you to invert the sign of the amount (useful for revenue accounts recorded on
    the credit side).
    """

    rules: List[MappingRule] = []
    with open(path, "r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"pattern", "category"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            missing = required - set(reader.fieldnames or [])
            raise RuntimeError(
                "Mapping file must define columns: " + ", ".join(sorted(missing))
            )
        for row in reader:
            pattern = row.get("pattern", "").strip()
            category = row.get("category", "").strip()
            if not pattern or not category:
                continue
            label = row.get("label", "").strip() or None
            sign_value = _parse_sign(row.get("sign", "1"))
            rules.append(MappingRule(pattern=pattern, category=category, label=label, sign=sign_value))
    return MappingTable(rules)


__all__ = ["MappingRule", "MappingTable", "load_mapping"]
