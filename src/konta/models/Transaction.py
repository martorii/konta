import datetime
import hashlib
from decimal import Decimal

from pydantic import BaseModel, model_validator


class Transaction(BaseModel):
    """Canonical transaction model shared across all issuer formats."""

    id: str = ""
    date: datetime.date
    amount: Decimal
    currency: str
    counterparty: str

    @model_validator(mode="after")
    def _set_id(self) -> "Transaction":
        if not self.id:
            self.id = self.make_id(self.date, self.amount, self.currency, self.counterparty)
        return self

    @staticmethod
    def make_id(
        date_: datetime.date, amount: Decimal, currency: str, counterparty: str
    ) -> str:
        """Deterministic id hashed from (date, amount, currency, counterparty)."""
        raw = f"{date_.isoformat()}|{amount}|{currency}|{counterparty}"
        return hashlib.sha256(raw.encode()).hexdigest()
