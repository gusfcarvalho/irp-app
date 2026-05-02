import io
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pypdf import PdfReader

from app.models.schemas import Trade

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    note_number: str | None
    trades: list[Trade]
    settlement_fee: Decimal = field(default_factory=Decimal)
    registration_fee: Decimal = field(default_factory=Decimal)
    term_fee: Decimal = field(default_factory=Decimal)
    ana_fee: Decimal = field(default_factory=Decimal)
    emoluments: Decimal = field(default_factory=Decimal)
    operational_fee: Decimal = field(default_factory=Decimal)
    execution: Decimal = field(default_factory=Decimal)
    custody_fee: Decimal = field(default_factory=Decimal)
    taxes: Decimal = field(default_factory=Decimal)
    irrf: Decimal = field(default_factory=Decimal)
    other_fees: Decimal = field(default_factory=Decimal)
    depositary_fee: Decimal = field(default_factory=Decimal)

try:
    from correpy.parsers.brokerage_notes.parser_factory import ParserFactory
    from correpy.parsers.exceptions import InvalidPasswordException
    import correpy.parsers.brokerage_notes.base_parser as _correpy_base_parser

    # correpy's AMOUNT_STRUCTURE_REGEX only handles up to 3-digit standalone integers
    # (e.g. matches "1.200" but not plain "1200").  BTG writes quantities without a
    # thousands separator, so we patch the imported name in base_parser's namespace.
    _PLAIN_INT_AMOUNT_RE = re.compile(
        r"(?<![\d.,])(?:0|[1-9]\d{0,2}(?:\.\d{3})+|[1-9]\d*)(?![\d.,])"
    )

    def _patched_extract_amount_from_line(*, line: str) -> Decimal:
        if matches := _PLAIN_INT_AMOUNT_RE.findall(line):
            return Decimal(matches[-1].replace(".", ""))
        return Decimal(0)

    _correpy_base_parser.extract_amount_from_line = _patched_extract_amount_from_line  # type: ignore[attr-defined]
    _CORREPY_AVAILABLE = True
except ImportError:
    ParserFactory = None          # type: ignore[assignment,misc]
    InvalidPasswordException = Exception  # type: ignore[assignment,misc]
    _CORREPY_AVAILABLE = False

_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9]{2,4}\d{1,2}$")

LINE_RE = re.compile(
    r"(?P<date>\d{2}/\d{2}/\d{4}).*?\b(?P<side>C|V)\b\s+(?P<ticker>[A-Z]{4}\d{1,2}|[A-Z]{5}\d{1,2})\s+(?P<qty>\d+)\s+(?P<price>\d+[\.,]\d{2})"
)

# Parses lines from "Resumo dos Negócios":
# e.g. "AZUL54F PN 1000 2.160,00 216,00 C"
#       ticker_name  qty  unit_price total   side
# Matches the trailing numeric columns of any trade line:  qty  unit_price  total  C|D
# Used to detect lot sizes without requiring a specific section header.
_TRADE_NUMS_RE = re.compile(
    r"\b(?P<qty>\d[\d.]*)\s+(?P<price>[\d.]+,\d{2})\s+(?P<total>[\d.]+,\d{2})\s+(?P<side>[CD])\b"
)

_VALID_LOT_SIZES = {1, 100, 10_000}

# "Total CBLC" line — value may be on the same or following line after pypdf extraction.
_TOTAL_CBLC_RE = re.compile(
    r"Total\s+CBLC[\s\S]{0,60}?([\d.]+,\d{2})\s*([CD])\b",
    re.IGNORECASE,
)

# BTG format (pypdf extraction):
#   "Taxa de Transferencia de Ativos 2,64\nDepositária\nD\n"
# Value is on the label line; "Depositária" and then standalone "D" follow on separate lines.
_TRANSFER_FEE_RE = re.compile(
    r"Transfer[eê]ncia\s+de\s+Ativos\s+([\d.]+,\d{2})[\s\S]{0,40}?\bD\b",
    re.IGNORECASE,
)


def _parse_decimal_br(s: str) -> Decimal:
    return Decimal(s.replace(".", "").replace(",", "."))


class BTGParserAdapter:
    """Parser adapter for BTG SINACOR notes.

    Uses correpy 0.6.0 (ParserFactory) as the primary parser.
    Falls back to local regex extraction only if correpy is not installed.
    Errors are always printed so failures are visible.
    """

    def parse(self, pdf_path: str, password: str | None = None) -> ParseResult:
        """Parse a PDF and return a ParseResult with note_number, trades, and fees."""
        if not _CORREPY_AVAILABLE:
            print("[btg_adapter] correpy not installed, using regex fallback")
            return ParseResult(note_number=None, trades=self._parse_with_regex_fallback(pdf_path, password=password))

        pdf_bytes = Path(pdf_path).read_bytes()

        try:
            notes = ParserFactory(
                brokerage_note=io.BytesIO(pdf_bytes),
                password=password,
            ).parse()
        except InvalidPasswordException:
            hint = " (dica: notas da Clear enviadas por e-mail usam o CPF como senha)" if password is None else ""
            raise ValueError(f"PDF protegido por senha — forneça a senha no campo correspondente{hint}")
        except Exception as exc:
            logger.warning(
                "correpy falhou (%s: %s) — usando fallback regex", type(exc).__name__, exc
            )
            return ParseResult(note_number=None, trades=self._parse_with_regex_fallback(pdf_path, password=password))

        print(f"[btg_adapter] correpy returned {len(notes)} brokerage note(s)")

        note_numbers: list[str] = []
        trades: list[Trade] = []
        result = ParseResult(note_number=None, trades=[])

        for note in notes:
            note_numbers.append(str(note.reference_id))
            print(f"[btg_adapter]   note #{note.reference_id} date={note.reference_date}, transactions={len(note.transactions)}")
            result.settlement_fee += note.settlement_fee
            result.registration_fee += note.registration_fee
            result.term_fee += note.term_fee
            result.ana_fee += note.ana_fee
            result.emoluments += note.emoluments
            result.operational_fee += note.operational_fee
            result.execution += note.execution
            result.custody_fee += note.custody_fee
            result.taxes += note.taxes
            result.irrf += note.irrf
            result.other_fees += note.others
            for txn in note.transactions:
                # Use security.name rather than security.ticker: correpy's BASIC_TICKER_PATTERN
                # only recognises standard B3 suffixes (2,3,4,5,6,11,12), so non-standard
                # tickers like AZUL54F get truncated to AZUL5 by the ticker extractor.
                raw_name = txn.security.name or ""
                first_word = raw_name.split()[0] if raw_name else txn.security.ticker or ""
                # If first word looks like a valid B3 ticker, use it; otherwise
                # keep the full description so the alias UI shows the complete name.
                if first_word and _TICKER_RE.match(first_word.upper()):
                    ticker = first_word
                else:
                    ticker = raw_name or txn.security.ticker or ""

                if txn.security.ticker and txn.security.ticker != ticker:
                    logger.debug(
                        "correpy ticker %r from name %r; using %r",
                        txn.security.ticker, raw_name, ticker,
                    )

                side = "BUY" if txn.transaction_type.value == "buy" else "SELL"
                print(f"[btg_adapter]     {side} {ticker} qty={txn.amount} price={txn.unit_price}")
                trades.append(
                    Trade(
                        ticker=ticker,
                        trade_date=note.reference_date,
                        quantity=int(txn.amount),
                        price=txn.unit_price,
                        side=side,
                    )
                )

        if not trades:
            print("[btg_adapter] correpy returned 0 trades — trying regex fallback")
            fallback = self._parse_with_regex_fallback(pdf_path, password=password)
            if fallback:
                print(f"[btg_adapter] regex fallback found {len(fallback)} trades")
                return ParseResult(note_number=None, trades=fallback)
            print("[btg_adapter] regex fallback also found 0 trades")

        # Correct prices for non-unit lot sizes (e.g. debentures traded in lots of 10,000)
        trades = self._correct_lot_sizes(pdf_path, trades, password=password)

        # Infer Taxa Depositária (not in correpy) via:
        #   depositary_fee = ops_value − settlement_fee − registration_fee − Total CBLC
        result.depositary_fee = self._infer_depositary_fee(
            pdf_path, trades, result.settlement_fee, result.registration_fee, password=password
        )
        if result.depositary_fee:
            print(f"[btg_adapter] depositary_fee={result.depositary_fee}")

        result.note_number = "|".join(note_numbers) if note_numbers else None
        result.trades = trades
        return result

    def _correct_lot_sizes(self, pdf_path: str, trades: list[Trade], password: str | None = None) -> list[Trade]:
        """Detect non-unit lot sizes by cross-referencing the 'Resumo dos Negócios' section.

        When a security is traded in lots of 100 or 10,000, correpy reports the per-lot
        unit price (e.g. 2,160.00 per lot of 10,000).  We compute the implied lot size from
        the gross total reported on the nota and divide the price accordingly so the stored
        price always reflects the per-share/per-unit value.
        """
        resumo = self._extract_resumo_totals(pdf_path, password=password)
        if not resumo:
            return trades

        corrected: list[Trade] = []
        for trade in trades:
            key = (trade.quantity, trade.price)
            print(f"[btg_adapter] lot-size lookup: ticker={trade.ticker} key={key} found={key in resumo}")
            if key in resumo:
                gross_total, lot_size = resumo[key]
                if lot_size != 1:
                    corrected_price = trade.price / Decimal(lot_size)
                    logger.warning(
                        "Lot-size correction for %s: qty=%d unit_price=%s gross=%s "
                        "lot_size=%d → corrected price=%s",
                        trade.ticker, trade.quantity, trade.price, gross_total,
                        lot_size, corrected_price,
                    )
                    trade = Trade(
                        ticker=trade.ticker,
                        trade_date=trade.trade_date,
                        quantity=trade.quantity,
                        price=corrected_price,
                        side=trade.side,
                    )
            corrected.append(trade)
        return corrected

    def _extract_resumo_totals(self, pdf_path: str, password: str | None = None) -> dict[tuple[int, Decimal], tuple[Decimal, int]]:
        """Scan the full PDF text for trade lines and return (qty, unit_price) → (gross_total, lot_size).

        Does not require a specific section header — any line whose trailing columns match
        <qty>  <price_br>  <total_br>  C|D  is a candidate.  Only entries where the implied
        lot size is in {1, 100, 10 000} and is != 1 are kept (unit-lot trades don't need fixing).
        """
        reader = PdfReader(str(pdf_path))
        if password and reader.is_encrypted:
            reader.decrypt(password)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        result: dict[tuple[int, Decimal], tuple[Decimal, int]] = {}

        for m in _TRADE_NUMS_RE.finditer(text):
            try:
                qty = int(m.group("qty").replace(".", ""))
                unit_price = _parse_decimal_br(m.group("price"))
                gross_total = _parse_decimal_br(m.group("total"))

                if gross_total == 0 or unit_price == 0 or qty == 0:
                    continue

                raw_lot = (Decimal(qty) * unit_price) / gross_total
                lot_size = int(round(raw_lot))

                if lot_size not in _VALID_LOT_SIZES:
                    continue

                key = (qty, unit_price)
                result[key] = (gross_total, lot_size)

                if lot_size != 1:
                    print(f"[btg_adapter] lot-size candidate: qty={qty} price={unit_price} total={gross_total} lot={lot_size}")
            except (InvalidOperation, ValueError, ZeroDivisionError):
                continue

        print(f"[btg_adapter] lot-size map has {len(result)} entries; non-unit: {sum(1 for _,ls in result.values() if ls!=1)}")
        return result

    def _infer_depositary_fee(
        self,
        pdf_path: str,
        trades: list[Trade],
        settlement_fee: Decimal,
        registration_fee: Decimal,
        password: str | None = None,
    ) -> Decimal:
        """Determine Taxa de Transferência de Ativos (depositary fee).

        Primary: infer from Total CBLC printed on the nota.
          depositary_fee = ops_value − settlement_fee − registration_fee − Total CBLC
        Fallback: read the 'Taxa de Transferência de Ativos' label directly from the PDF.
        """
        reader = PdfReader(str(pdf_path))
        if password and reader.is_encrypted:
            reader.decrypt(password)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        # --- primary: CBLC inference ---
        total_cblc = self._parse_total_cblc(text)
        if total_cblc is not None:
            ops_value = (
                sum(t.price * t.quantity for t in trades if t.side == "SELL")
                - sum(t.price * t.quantity for t in trades if t.side == "BUY")
            )
            depositary_fee = ops_value - settlement_fee - registration_fee - total_cblc
            print(
                f"[btg_adapter] CBLC inference: ops={ops_value} cblc={total_cblc} "
                f"settlement={settlement_fee} registration={registration_fee} "
                f"→ depositary_fee={depositary_fee}"
            )
            if depositary_fee >= 0:
                return depositary_fee
            logger.warning(
                "CBLC-inferred depositary_fee=%s is negative — falling back to direct parse",
                depositary_fee,
            )

        # --- fallback: direct label parse ---
        # Use the LAST match — the label appears on multiple pages but the value
        # is only on the last page where the fee summary is printed.
        print("[btg_adapter] Total CBLC not found or negative result — trying direct label parse")
        m = None
        for m in _TRANSFER_FEE_RE.finditer(text):
            pass  # keep iterating to land on the last match
        if m:
            try:
                val = _parse_decimal_br(m.group(1))
                print(f"[btg_adapter] direct depositary_fee parse: {val}")
                return val
            except InvalidOperation:
                pass

        logger.debug("depositary_fee not found in %s", pdf_path)
        return Decimal(0)

    def _parse_total_cblc(self, text: str) -> Decimal | None:
        """Extract signed Total CBLC from already-extracted PDF text (C→+, D→−)."""
        m = _TOTAL_CBLC_RE.search(text)
        if not m:
            return None
        try:
            val = _parse_decimal_br(m.group(1))
            return val if m.group(2).upper() == "C" else -val
        except InvalidOperation:
            return None

    def _parse_with_regex_fallback(self, pdf_path: str, password: str | None = None) -> list[Trade]:
        path = Path(pdf_path)
        reader = PdfReader(str(path))
        if password and reader.is_encrypted:
            reader.decrypt(password)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        trades: list[Trade] = []
        for match in LINE_RE.finditer(text):
            date_value = datetime.strptime(match.group("date"), "%d/%m/%Y").date()
            price = Decimal(match.group("price").replace(".", "").replace(",", "."))
            trades.append(
                Trade(
                    ticker=match.group("ticker"),
                    trade_date=date_value,
                    quantity=int(match.group("qty")),
                    price=price,
                    side="BUY" if match.group("side") == "C" else "SELL",
                )
            )

        return trades
