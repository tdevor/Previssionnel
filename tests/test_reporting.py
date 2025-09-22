from decimal import Decimal
from pathlib import Path

import pytest

from gl_reporting.ledger import LedgerFormatError, load_ledger
from gl_reporting.mapping import MappingRule, MappingTable
from gl_reporting.report import aggregate_by_category


def test_load_ledger_handles_aliases_and_formats(tmp_path: Path) -> None:
    csv_content = """Date;Journal;Compte;Libellé;Débit;Crédit\n01/01/2024;VT;701100;Vente;0;1500\n"""
    file_path = tmp_path / "ledger.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    entries = load_ledger(str(file_path), encoding="utf-8")
    assert len(entries) == 1
    entry = entries[0]
    assert entry.date.year == 2024 and entry.date.month == 1 and entry.date.day == 1
    assert entry.journal == "VT"
    assert entry.account == "701100"
    assert entry.description == "Vente"
    assert entry.debit == Decimal("0")
    assert entry.credit == Decimal("1500")


def test_load_ledger_missing_columns_raises(tmp_path: Path) -> None:
    csv_content = """Date;Libellé;Montant\n2024-01-01;Test;100\n"""
    file_path = tmp_path / "invalid.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    with pytest.raises(LedgerFormatError):
        load_ledger(str(file_path), encoding="utf-8")


def test_mapping_specificity() -> None:
    table = MappingTable(
        [
            MappingRule(pattern="70*", category="CA générique", label=None, sign=-1),
            MappingRule(pattern="706*", category="CA services", label=None, sign=-1),
        ]
    )
    first_rule = table.match("706100")
    assert first_rule is not None
    assert first_rule.category == "CA services"


def test_aggregate_by_category(tmp_path: Path) -> None:
    ledger_content = """date,journal,account,description,debit,credit\n2024-01-01,VT,701100,Vente,0,1500\n2024-01-02,VT,706000,Prestations,0,500\n2024-01-03,AC,606100,Achat,200,0\n2024-01-04,OD,471000,A ventiler,100,0\n"""
    ledger_path = tmp_path / "ledger.csv"
    ledger_path.write_text(ledger_content, encoding="utf-8")

    mapping = MappingTable(
        [
            MappingRule("706*", "CA prestations", "", -1),
            MappingRule("70*", "CA marchandises", "", -1),
            MappingRule("606*", "Charges achats", "", 1),
        ]
    )

    entries = load_ledger(str(ledger_path))
    result = aggregate_by_category(entries, mapping, default_category="Non ventilé")
    assert result.totals["CA prestations"] == Decimal("500")
    assert result.totals["CA marchandises"] == Decimal("1500")
    assert result.totals["Charges achats"] == Decimal("200")
    assert result.totals["Non ventilé"] == Decimal("100")
    assert len(result.unmapped_entries) == 1
