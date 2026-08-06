import datetime
from decimal import Decimal
from pathlib import Path

from konta.models.Transaction import Transaction
from konta.utils.report import generate_report, render_report


def _txn(amount: str, category: str | None, counterparty: str = "SHOP") -> Transaction:
    return Transaction(
        date=datetime.date(2025, 12, 31),
        amount=Decimal(amount),
        currency="EUR",
        counterparty=counterparty,
        category=category,
    )


def test_render_report_shows_no_transactions_message_when_empty() -> None:
    html = render_report([])

    assert "No outgoing transactions found." in html


def test_render_report_excludes_incoming_transactions() -> None:
    html = render_report([_txn("100", "salary")])

    assert "salary" not in html
    assert "No outgoing transactions found." in html


def test_render_report_groups_uncategorized_as_bucket() -> None:
    html = render_report([_txn("-10", None)])

    assert "Uncategorized" in html


def test_render_report_sums_per_category_and_sorts_descending() -> None:
    html = render_report(
        [
            _txn("-10", "groceries"),
            _txn("-5", "groceries"),
            _txn("-50", "rent"),
        ]
    )

    rent_index = html.index("rent")
    groceries_index = html.index("groceries")
    assert rent_index < groceries_index
    assert "50.00 EUR" in html
    assert "15.00 EUR" in html


def test_generate_report_writes_file_and_creates_parents(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "report.html"

    result = generate_report([_txn("-10", "groceries")], output_path)

    assert result == output_path
    assert output_path.exists()
    assert "groceries" in output_path.read_text()
