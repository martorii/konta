import datetime
from decimal import Decimal
from pathlib import Path

from konta.models.Transaction import Transaction
from konta.utils.report import generate_report, render_report


def _txn(
    amount: str,
    category: str | None,
    date: datetime.date = datetime.date(2025, 12, 31),
    counterparty: str = "SHOP",
) -> Transaction:
    return Transaction(
        date=date,
        amount=Decimal(amount),
        currency="EUR",
        counterparty=counterparty,
        category=category,
    )


def test_render_report_shows_no_transactions_message_when_empty() -> None:
    html = render_report([])

    assert "No outgoing transactions found." in html


def test_render_report_excludes_incoming_transactions_from_chart() -> None:
    html = render_report([_txn("100", "salary")])

    assert "No outgoing transactions found." in html
    chart_section = html.split("<div class=\"table-wrap\">")[0]
    assert "salary" not in chart_section


def test_render_report_groups_uncategorized_as_bucket() -> None:
    html = render_report([_txn("-10", None)])

    assert "Uncategorized" in html


def test_render_report_sorts_categories_descending_by_30d_average() -> None:
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


def test_render_report_normalizes_totals_to_30_day_average() -> None:
    # A 10-day spread means the 30-day average is 3x the raw total.
    html = render_report(
        [
            _txn("-10", "groceries", date=datetime.date(2025, 12, 1)),
            _txn("-10", "groceries", date=datetime.date(2025, 12, 11)),
        ]
    )

    assert "60.00 EUR" in html


def test_render_report_shows_30_day_average_total_spend() -> None:
    # A 30-day spread means the 30-day average equals the raw total.
    html = render_report(
        [
            _txn("-10", "groceries", date=datetime.date(2025, 12, 1)),
            _txn("-50", "rent", date=datetime.date(2025, 12, 31)),
        ]
    )

    assert "30-day average total spend" in html
    assert "60.00 EUR" in html


def test_render_report_excludes_ignored_category_from_chart() -> None:
    html = render_report(
        [
            _txn("-10", "groceries", counterparty="SUPERMARKET"),
            _txn("-500", "Ignore", counterparty="TRANSFER"),
        ]
    )

    chart_section = html.split('<div class="table-wrap">')[0]
    assert "Ignore" not in chart_section
    assert "500.00 EUR" not in chart_section
    assert "300.00 EUR" in chart_section


def test_render_report_keeps_ignored_category_in_table() -> None:
    html = render_report(
        [
            _txn("-10", "groceries", counterparty="SUPERMARKET"),
            _txn("-500", "Ignore", counterparty="TRANSFER"),
        ]
    )

    table_section = html.split('<div class="table-wrap">')[1]
    assert "TRANSFER" in table_section
    assert "Ignore" in table_section


def test_render_report_shows_no_transactions_message_when_only_ignored() -> None:
    html = render_report([_txn("-500", "Ignore", counterparty="TRANSFER")])

    assert "No outgoing transactions found." in html
    assert "TRANSFER" in html


def test_render_report_includes_all_transactions_in_table() -> None:
    html = render_report(
        [
            _txn("-10", "groceries", counterparty="SUPERMARKET"),
            _txn("100", "salary", counterparty="EMPLOYER"),
        ]
    )

    assert "SUPERMARKET" in html
    assert "EMPLOYER" in html
    assert 'id="tx-table"' in html


def test_render_report_table_is_sortable() -> None:
    html = render_report([_txn("-10", "groceries")])

    assert 'data-type="text"' in html
    assert 'data-type="number"' in html
    assert "addEventListener" in html


def test_generate_report_writes_file_and_creates_parents(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "report.html"

    result = generate_report([_txn("-10", "groceries")], output_path)

    assert result == output_path
    assert output_path.exists()
    assert "groceries" in output_path.read_text()
