import datetime
from decimal import Decimal
from pathlib import Path

from konta.utils.ingest import ingest_folder

HEADER = (
    '"Girokonto";"DE47120300001064289786"\n'
    "\n"
    '"Kontostand vom 06.08.2026:";"3.077,01 \xa0€"\n'
    '""\n'
    '"Buchungsdatum";"Wertstellung";"Status";"Zahlungspflichtige*r";'
    '"Zahlungsempfänger*in";"Verwendungszweck";"Umsatztyp";"IBAN";'
    '"Betrag (€)";"Gläubiger-ID";"Mandatsreferenz";"Kundenreferenz"\n'
)


def test_ingest_folder_maps_dkb_format_to_canonical(tmp_path: Path) -> None:
    rows = (
        '"04.08.26";"04.08.26";"Gebucht";"ISSUER";"SUPREMO.KAFFEEROSTEREI";'
        '"VISA Debitkartenumsatz vom 03.08.2026";"Ausgang";"DE96120300009005290904";'
        '"-6,6";"";"";"486215523499995"\n'
        '"31.07.26";"31.07.26";"Gebucht";"YOLANDA LOPEZ ROYO";"ERIK MARTORI";"YAYOS";'
        '"Eingang";"ES7220800806393040087884";"1.500,49";"";"";"NOT PROVIDED"\n'
    )
    (tmp_path / "a.csv").write_text(HEADER + rows, encoding="utf-8-sig")

    result = ingest_folder(tmp_path, format="dkb")

    assert list(result.columns) == ["id", "date", "amount", "currency", "counterparty", "category"]
    assert len(result) == 2

    outgoing = result.iloc[0]
    assert outgoing["date"] == datetime.date(2026, 8, 4)
    assert Decimal(str(outgoing["amount"])) == Decimal("-6.6")
    assert outgoing["currency"] == "EUR"
    assert outgoing["counterparty"] == "SUPREMO.KAFFEEROSTEREI"

    incoming = result.iloc[1]
    assert incoming["date"] == datetime.date(2026, 7, 31)
    assert Decimal(str(incoming["amount"])) == Decimal("1500.49")
    assert incoming["counterparty"] == "YOLANDA LOPEZ ROYO"
