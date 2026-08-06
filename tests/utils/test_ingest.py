import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from konta.models.formats.base import RawTransaction
from konta.models.Transaction import Transaction
from konta.utils.ingest import _read_file, ingest_folder

DUMMY_HEADER = "Fecha,Concepto,Importe,Divisa\n"


class _SemicolonTransaction(RawTransaction):
    """Test-only format using ';' as the CSV delimiter."""

    read_csv_kwargs = {"sep": ";"}

    Concepto: str

    def to_canonical(self) -> Transaction:
        return Transaction(
            date=datetime.date.today(),
            amount=Decimal(0),
            currency="EUR",
            counterparty=self.Concepto,
        )


def test_ingest_folder_maps_dummy_format_to_canonical(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text(DUMMY_HEADER + "31/12/2025,AMAZON EU SARL,-45.99,EUR\n")
    (tmp_path / "b.csv").write_text(DUMMY_HEADER + "30/12/2025,NOMINA EMPRESA SL,1500.00,EUR\n")

    result = ingest_folder(tmp_path, format="dummy")

    assert list(result.columns) == ["id", "date", "amount", "currency", "counterparty"]
    assert len(result) == 2
    row = result.iloc[0]
    assert row["counterparty"] == "AMAZON EU SARL"
    assert Decimal(str(row["amount"])) == Decimal("-45.99")
    assert row["currency"] == "EUR"


def test_ingest_folder_ignores_non_csv_files(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text(DUMMY_HEADER + "31/12/2025,AMAZON EU SARL,-45.99,EUR\n")
    (tmp_path / "notes.txt").write_text("irrelevant")

    result = ingest_folder(tmp_path, format="dummy")

    assert len(result) == 1


def test_ingest_folder_raises_on_invalid_row(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text(DUMMY_HEADER + "31/12/2025,AMAZON EU SARL,-45.99,EUR\n")
    (tmp_path / "b.csv").write_text("Fecha,Concepto,Divisa\n30/12/2025,NOMINA EMPRESA SL,EUR\n")

    with pytest.raises(ValueError, match="Invalid row"):
        ingest_folder(tmp_path, format="dummy")


def test_ingest_folder_raises_on_unknown_format(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text(DUMMY_HEADER + "31/12/2025,AMAZON EU SARL,-45.99,EUR\n")

    with pytest.raises(ValueError, match="Unknown format"):
        ingest_folder(tmp_path, format="nope")


def test_read_file_applies_format_read_csv_kwargs(tmp_path: Path) -> None:
    path = tmp_path / "a.csv"
    path.write_text("Concepto;Importe\nAMAZON EU SARL;12\n")

    frame = _read_file(path, _SemicolonTransaction)

    assert list(frame.columns) == ["Concepto", "Importe"]


def test_raw_transaction_default_read_csv_kwargs_is_empty() -> None:
    assert RawTransaction.read_csv_kwargs == {}
