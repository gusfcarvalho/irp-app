from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.parsers.btg_adapter import BTGParserAdapter


def _make_correpy_note(ticker: str, side: str, quantity: int, price: str, ref_date: date):
    from correpy.domain.entities.brokerage_note import BrokerageNote
    from correpy.domain.entities.security import Security
    from correpy.domain.entities.transaction import Transaction
    from correpy.domain.enums import TransactionType

    security = MagicMock(spec=Security)
    security.ticker = ticker
    security.name = ticker

    txn = MagicMock(spec=Transaction)
    txn.security = security
    txn.transaction_type = TransactionType.BUY if side == "buy" else TransactionType.SELL
    txn.amount = Decimal(quantity)
    txn.unit_price = Decimal(price)

    note = MagicMock(spec=BrokerageNote)
    note.reference_id = 12345
    note.reference_date = ref_date
    note.transactions = [txn]
    note.settlement_fee = Decimal("0")
    note.registration_fee = Decimal("0")
    note.term_fee = Decimal("0")
    note.ana_fee = Decimal("0")
    note.emoluments = Decimal("1.50")
    note.operational_fee = Decimal("0")
    note.execution = Decimal("0")
    note.custody_fee = Decimal("0")
    note.taxes = Decimal("0")
    note.irrf = Decimal("0.75")
    note.others = Decimal("0")
    return note


def test_btg_adapter_uses_correpy(tmp_path, monkeypatch):
    pdf_file = tmp_path / "nota.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    note = _make_correpy_note("PETR4", "buy", 100, "30.15", date(2026, 4, 1))

    with patch("app.services.parsers.btg_adapter.ParserFactory") as MockFactory, \
         patch("app.services.parsers.btg_adapter._CORREPY_AVAILABLE", True):
        MockFactory.return_value.parse.return_value = [note]

        adapter = BTGParserAdapter()
        result = adapter.parse(str(pdf_file))

    assert result.note_number == "12345"
    assert len(result.trades) == 1
    assert result.trades[0].ticker == "PETR4"
    assert result.trades[0].side == "BUY"
    assert result.trades[0].quantity == 100
    assert result.emoluments == Decimal("1.50")
    assert result.irrf == Decimal("0.75")