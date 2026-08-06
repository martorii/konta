import datetime
from decimal import Decimal

from konta.models.Transaction import Transaction


def _make(
    date_: datetime.date = datetime.date(2025, 12, 31),
    amount: Decimal = Decimal("-45.99"),
    currency: str = "EUR",
    counterparty: str = "AMAZON EU SARL",
) -> Transaction:
    return Transaction(date=date_, amount=amount, currency=currency, counterparty=counterparty)


def test_id_is_auto_generated_when_omitted() -> None:
    txn = _make()

    assert txn.id != ""
    assert txn.id == Transaction.make_id(
        txn.date, txn.amount, txn.currency, txn.counterparty
    )


def test_id_generation_is_deterministic() -> None:
    assert _make().id == _make().id


def test_id_differs_for_different_transactions() -> None:
    assert _make().id != _make(counterparty="OTHER SL").id


def test_explicit_id_is_preserved() -> None:
    txn = Transaction(
        id="custom-id",
        date=datetime.date(2025, 12, 31),
        amount=Decimal("-45.99"),
        currency="EUR",
        counterparty="AMAZON EU SARL",
    )

    assert txn.id == "custom-id"


def test_make_id_is_deterministic_and_pure() -> None:
    date_ = datetime.date(2025, 12, 31)
    amount = Decimal("-45.99")

    assert Transaction.make_id(date_, amount, "EUR", "AMAZON EU SARL") == Transaction.make_id(
        date_, amount, "EUR", "AMAZON EU SARL"
    )


def test_make_id_differs_on_any_field_change() -> None:
    base = Transaction.make_id(datetime.date(2025, 12, 31), Decimal("-45.99"), "EUR", "AMAZON")

    assert base != Transaction.make_id(
        datetime.date(2026, 1, 1), Decimal("-45.99"), "EUR", "AMAZON"
    )
    assert base != Transaction.make_id(
        datetime.date(2025, 12, 31), Decimal("-46.99"), "EUR", "AMAZON"
    )
    assert base != Transaction.make_id(
        datetime.date(2025, 12, 31), Decimal("-45.99"), "USD", "AMAZON"
    )
    assert base != Transaction.make_id(
        datetime.date(2025, 12, 31), Decimal("-45.99"), "EUR", "OTHER"
    )
