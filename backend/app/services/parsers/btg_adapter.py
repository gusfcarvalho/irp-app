import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader

from app.models.schemas import Trade

LINE_RE = re.compile(
    r"(?P<date>\d{2}/\d{2}/\d{4}).*?\b(?P<side>C|V)\b\s+(?P<ticker>[A-Z]{4}\d{1,2}|[A-Z]{5}\d{1,2})\s+(?P<qty>\d+)\s+(?P<price>\d+[\.,]\d{2})"
)


class BTGParserAdapter:
    """Best-effort parser adapter for BTG SINACOR notes using extracted PDF text."""

    def parse(self, pdf_path: str) -> list[Trade]:
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
