"""Tools for mapping a French general ledger to management reporting lines."""
from __future__ import annotations

import importlib
from typing import Any

from .ledger import LedgerEntry, LedgerFormatError, load_ledger
from .mapping import MappingRule, MappingTable, load_mapping

_REPORT_EXPORTS = {
    "CategorisedEntry",
    "ReportResult",
    "aggregate_by_category",
    "build_report",
    "print_summary",
    "write_details_csv",
    "write_summary_csv",
}


def __getattr__(name: str) -> Any:  # pragma: no cover - simple lazy import
    if name in _REPORT_EXPORTS:
        module = importlib.import_module(".report", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(name)


__all__ = [
    "LedgerEntry",
    "LedgerFormatError",
    "load_ledger",
    "MappingRule",
    "MappingTable",
    "load_mapping",
    *_REPORT_EXPORTS,
]
