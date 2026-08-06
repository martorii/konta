import datetime
from decimal import Decimal

from pydantic import Field

from konta.models.formats.base import RawTransaction
from konta.models.Transaction import Transaction


def _parse_german_decimal(value: str) -> Decimal:
    """Convert a German-formatted amount ("1.234,56" / "-6,6") to a Decimal."""
    return Decimal(value.replace(".", "").replace(",", "."))


class DkbTransaction(RawTransaction):
    """Raw row shape for the DKB (Deutsche Kreditbank) Girokonto CSV export."""

    # DKB exports carry a 4-line preamble (account/IBAN, blank, balance, blank) before the header.
    read_csv_kwargs = {"sep": ";", "skiprows": 4, "encoding": "utf-8-sig"}

    buchungsdatum: str = Field(alias="Buchungsdatum")
    zahlungspflichtige: str = Field(alias="Zahlungspflichtige*r")
    zahlungsempfaenger: str = Field(alias="Zahlungsempfänger*in")
    umsatztyp: str = Field(alias="Umsatztyp")
    betrag: str = Field(alias="Betrag (€)")
    verwendungszweck: str = Field(alias="Verwendungszweck")

    def to_canonical(self) -> Transaction:
        date_ = datetime.datetime.strptime(self.buchungsdatum, "%d.%m.%y").date()
        counterparty = (
            self.zahlungspflichtige if self.umsatztyp == "Eingang" else self.zahlungsempfaenger
        )
        return Transaction(
            date=date_,
            amount=_parse_german_decimal(self.betrag),
            currency="EUR",
            counterparty=counterparty,
            reference=self.verwendungszweck,
        )
