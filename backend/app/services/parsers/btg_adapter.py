import importlib
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from app.models.schemas import Trade

LINE_RE = re.compile(
    r"(?P<date>\d{2}/\d{2}/\d{4}).*?\b(?P<side>C|V)\b\s+(?P<ticker>[A-Z]{4}\d{1,2}|[A-Z]{5}\d{1,2})\s+(?P<qty>\d+)\s+(?P<price>\d+[\.,]\d{2})"
)


class BTGParserAdapter:
    """Parser adapter for BTG SINACOR notes.

    Strategy:
    1) Try CorrePy-based parsing if library is available.
    2) Fallback to local text+regex extraction.
    """

    def parse(self, pdf_path: str) -> list[Trade]:
        correpy_trades = self._parse_with_correpy(pdf_path)
        if correpy_trades:
            return correpy_trades
        return self._parse_with_regex_fallback(pdf_path)

    def _parse_with_correpy(self, pdf_path: str) -> list[Trade]:
        """Best-effort CorrePy integration using dynamic API discovery.

        This supports different CorrePy versions without hard-coding a single API path.
        """
        callables = [
            "correpy.parsers.parse_brokerage_note",
            "correpy.parsers.brokerage_notes.parse",
            "correpy.parsers.brokerage_notes.sinacor.parse",
        ]

        for dotted in callables:
            fn = self._load_callable(dotted)
            if fn is None:
                continue
            try:
                result = fn(pdf_path)
            except TypeError:
                # Some versions may accept Path objects.
                result = fn(Path(pdf_path))
            except Exception:
                continue

            trades = self._normalize_correpy_result(result)
            if trades:
                return trades

        return []

    def _load_callable(self, dotted_path: str):
        module_name, attr_name = dotted_path.rsplit(".", 1)
        try:
            module = importlib.import_module(module_name)
        except Exception:
            return None
        return getattr(module, attr_name, None)

    def _normalize_correpy_result(self, result: Any) -> list[Trade]:
        """Normalize CorrePy output to `list[Trade]`.

        Supports dict-based payloads and object-based payloads with common attribute names.
        """
        items = self._extract_operations(result)
        trades: list[Trade] = []

        for item in items:
            ticker = self._read(item, "ticker", "symbol", "asset")
            side_raw = self._read(item, "side", "operation", "buy_sell")
            quantity = self._read(item, "quantity", "qty")
            price = self._read(item, "price", "unit_price")
            trade_date = self._read(item, "trade_date", "date", "dt")

            if not all([ticker, side_raw, quantity, price, trade_date]):
                continue

            side = self._normalize_side(side_raw)
            if side is None:
                continue

            trades.append(
                Trade(
                    ticker=str(ticker),
                    trade_date=self._normalize_date(trade_date),
                    quantity=int(quantity),
                    price=self._normalize_decimal(price),
                    side=side,
                )
            )

        return trades

    def _extract_operations(self, result: Any) -> list[Any]:
        if result is None:
            return []
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return result.get("operations") or result.get("trades") or []

        for attr in ("operations", "trades", "items"):
            value = getattr(result, attr, None)
            if isinstance(value, list):
                return value

        return []

    def _read(self, obj: Any, *keys: str) -> Any:
        if isinstance(obj, dict):
            for key in keys:
                if key in obj:
                    return obj[key]
            return None

        for key in keys:
            if hasattr(obj, key):
                return getattr(obj, key)
        return None

    def _normalize_side(self, raw: Any) -> str | None:
        value = str(raw).strip().upper()
        if value in {"BUY", "C", "COMPRA"}:
            return "BUY"
        if value in {"SELL", "V", "VENDA"}:
            return "SELL"
        return None

    def _normalize_date(self, raw: Any):
        if hasattr(raw, "year") and hasattr(raw, "month") and hasattr(raw, "day"):
            return raw

        text = str(raw).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Unrecognized trade date format: {raw}")

    def _normalize_decimal(self, raw: Any) -> Decimal:
        text = str(raw).strip().replace(".", "").replace(",", ".")
        return Decimal(text)

    def _parse_with_regex_fallback(self, pdf_path: str) -> list[Trade]:
        path = Path(pdf_path)
        reader = PdfReader(str(path))
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