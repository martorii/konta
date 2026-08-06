import datetime
from decimal import Decimal

from konta.models.formats.base import RawTransaction
from konta.models.Transaction import Transaction


class DummyTransaction(RawTransaction):
    """Raw row shape for the dummy (Spanish-bank-like) CSV format."""

    Fecha: str
    Concepto: str
    Importe: Decimal
    Divisa: str

    def to_canonical(self) -> Transaction:
        date_ = datetime.datetime.strptime(self.Fecha, "%d/%m/%Y").date()
        return Transaction(
            date=date_,
            amount=self.Importe,
            currency=self.Divisa,
            counterparty=self.Concepto,
        )
