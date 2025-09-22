"""Generate a management reporting from a general ledger and a mapping table."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, Iterable, List, Optional
import argparse
import csv
import sys

from .ledger import LedgerEntry, load_ledger
from .mapping import MappingRule, MappingTable, load_mapping


TWO_PLACES = Decimal("0.01")


@dataclass(frozen=True)
class CategorisedEntry:
    entry: LedgerEntry
    category: str
    rule: Optional[MappingRule]
    amount: Decimal


@dataclass
class ReportResult:
    totals: Dict[str, Decimal]
    categorised_entries: List[CategorisedEntry]
    default_category: str

    @property
    def unmapped_entries(self) -> List[CategorisedEntry]:
        return [item for item in self.categorised_entries if item.rule is None]


def _format_decimal(value: Decimal) -> str:
    return str(value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP))


def aggregate_by_category(
    entries: Iterable[LedgerEntry],
    mapping: MappingTable,
    default_category: str = "Non affecté",
) -> ReportResult:
    totals: Dict[str, Decimal] = {}
    categorised: List[CategorisedEntry] = []
    for entry in entries:
        rule = mapping.match(entry.account)
        if rule is None:
            category = default_category
            amount = entry.amount
        else:
            category = rule.category
            amount = entry.amount * Decimal(rule.sign)
        totals[category] = totals.get(category, Decimal("0")) + amount
        categorised.append(
            CategorisedEntry(entry=entry, category=category, rule=rule, amount=amount)
        )
    return ReportResult(totals=totals, categorised_entries=categorised, default_category=default_category)


def build_report(
    ledger_path: str,
    mapping_path: str,
    *,
    default_category: str = "Non affecté",
    encoding: str = "utf-8",
) -> ReportResult:
    entries = load_ledger(ledger_path, encoding=encoding)
    mapping = load_mapping(mapping_path, encoding=encoding)
    return aggregate_by_category(entries, mapping, default_category=default_category)


def write_summary_csv(result: ReportResult, path: str, *, encoding: str = "utf-8") -> None:
    with open(path, "w", encoding=encoding, newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["category", "amount"])
        for category, amount in sorted(result.totals.items()):
            writer.writerow([category, _format_decimal(amount)])


def write_details_csv(result: ReportResult, path: str, *, encoding: str = "utf-8") -> None:
    with open(path, "w", encoding=encoding, newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "date",
                "journal",
                "account",
                "description",
                "debit",
                "credit",
                "amount",
                "category",
                "rule_label",
            ]
        )
        for item in result.categorised_entries:
            entry = item.entry
            writer.writerow(
                [
                    entry.date.isoformat() if entry.date else "",
                    entry.journal or "",
                    entry.account,
                    entry.description or "",
                    _format_decimal(entry.debit),
                    _format_decimal(entry.credit),
                    _format_decimal(item.amount),
                    item.category,
                    item.rule.label if item.rule else "",
                ]
            )


def print_summary(result: ReportResult, file=sys.stdout) -> None:
    print("Catégorie".ljust(40) + "Montant", file=file)
    print("-" * 55, file=file)
    for category, amount in sorted(result.totals.items()):
        print(category.ljust(40) + _format_decimal(amount), file=file)
    if result.unmapped_entries:
        print("\nComptes non affectés:", file=file)
        for item in result.unmapped_entries:
            entry = item.entry
            line = f"  - {entry.account} : {entry.description or 'Sans libellé'}"
            print(line, file=file)


def _parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Génère un reporting à partir d'un grand livre et d'un mapping"
    )
    parser.add_argument("--ledger", required=True, help="Chemin vers le grand livre CSV")
    parser.add_argument("--mapping", required=True, help="Chemin vers le mapping CSV")
    parser.add_argument("--output", help="Chemin du fichier CSV de synthèse")
    parser.add_argument("--details", help="Chemin du fichier CSV détaillant les écritures")
    parser.add_argument(
        "--default-category",
        default="Non affecté",
        help="Nom de la catégorie utilisée si aucune règle n'est trouvée",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Encodage des fichiers d'entrée et de sortie",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_arguments(argv)
    result = build_report(
        args.ledger,
        args.mapping,
        default_category=args.default_category,
        encoding=args.encoding,
    )
    if args.output:
        write_summary_csv(result, args.output, encoding=args.encoding)
    else:
        print_summary(result)
    if args.details:
        write_details_csv(result, args.details, encoding=args.encoding)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())


__all__ = [
    "CategorisedEntry",
    "ReportResult",
    "aggregate_by_category",
    "build_report",
    "print_summary",
    "write_summary_csv",
    "write_details_csv",
]
