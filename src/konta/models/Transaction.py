import datetime
import hashlib
from decimal import Decimal

from pydantic import BaseModel


class Transaction(BaseModel):
    """Canonical transaction model shared across all issuer formats."""

    id: str
    date: datetime.date
    amount: Decimal
    currency: str
    counterparty: str

    @staticmethod
    def make_id(
        date_: datetime.date, amount: Decimal, currency: str, counterparty: str
    ) -> str:
        """Deterministic id hashed from (date, amount, currency, counterparty)."""
        raw = f"{date_.isoformat()}|{amount}|{currency}|{counterparty}"
        return hashlib.sha256(raw.encode()).hexdigest()
