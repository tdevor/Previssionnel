"""Utilities for parsing a general ledger exported to CSV."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, List, Optional
import csv


@dataclass(frozen=True)
class LedgerEntry:
    """Represents a single movement in the general ledger."""

    date: Optional[date]
    journal: Optional[str]
    account: str
    description: Optional[str]
    debit: Decimal
    credit: Decimal

    @property
    def amount(self) -> Decimal:
        """Returns the signed amount of the movement (debit - credit)."""

        return self.debit - self.credit


_HEADER_ALIASES: Dict[str, tuple[str, ...]] = {
    "date": ("date", "Date", "DATE"),
    "journal": ("journal", "Journal", "JOURNAL"),
    "account": (
        "account",
        "compte",
        "Compte",
        "ACCOUNT",
        "COMPTE",
        "numéro de compte",
        "numero_compte",
    ),
    "description": (
        "description",
        "libellé",
        "libelle",
        "Libellé",
        "Libelle",
        "DESCRIPTION",
        "LIBELLE",
    ),
    "debit": ("debit", "Débit", "Debit", "DEBIT", "DEBITO"),
    "credit": ("credit", "Crédit", "Credit", "CREDIT", "CREDITO"),
}


class LedgerFormatError(RuntimeError):
    """Raised when the ledger CSV does not contain the expected columns."""


def _normalize_header(field: str) -> str:
    for normalized, aliases in _HEADER_ALIASES.items():
        if field in aliases:
            return normalized
    return field.lower()


def _map_headers(fieldnames: Iterable[str]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for name in fieldnames:
        norm = _normalize_header(name)
        if norm not in normalized:
            normalized[norm] = name
    missing = {"account", "debit", "credit"} - set(normalized)
    if missing:
        raise LedgerFormatError(
            "Missing required columns in ledger: " + ", ".join(sorted(missing))
        )
    return normalized


def _parse_decimal(value: str) -> Decimal:
    cleaned = value.strip().replace(" ", "")
    if not cleaned:
        return Decimal("0")
    if cleaned.count(",") > 0 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:  # pragma: no cover - defensive
        raise LedgerFormatError(f"Invalid decimal value: {value!r}") from exc


def _parse_date(value: str) -> Optional[date]:
    cleaned = value.strip()
    if not cleaned:
        return None
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def load_ledger(path: str, encoding: str = "utf-8") -> List[LedgerEntry]:
    """Loads the ledger CSV file.

    The file must at least contain the columns "account", "debit" and "credit".
    Additional optional columns such as date, journal or description are detected
    automatically using common French aliases ("libellé", "compte", ...).
    """

    entries: List[LedgerEntry] = []
    with open(path, "r", encoding=encoding, newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        if reader.fieldnames is None:
            raise LedgerFormatError("Ledger file must contain a header row")
        header_map = _map_headers(reader.fieldnames)
        for row in reader:
            account = row.get(header_map["account"], "").strip()
            if not account:
                # Ignore lines without account number: they are usually totals.
                continue
            debit = _parse_decimal(row.get(header_map["debit"], "0"))
            credit = _parse_decimal(row.get(header_map["credit"], "0"))
            date_value = None
            if "date" in header_map:
                date_value = _parse_date(row.get(header_map["date"], ""))
            journal_value = None
            if "journal" in header_map:
                journal_value = row.get(header_map["journal"], "").strip() or None
            description_value = None
            if "description" in header_map:
                description_value = row.get(header_map["description"], "").strip() or None
            entries.append(
                LedgerEntry(
                    date=date_value,
                    journal=journal_value,
                    account=account,
                    description=description_value,
                    debit=debit,
                    credit=credit,
                )
            )
    return entries


__all__ = ["LedgerEntry", "LedgerFormatError", "load_ledger"]
