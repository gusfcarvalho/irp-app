"""Port (protocol) definition for brokerage PDF parsers."""
from typing import Protocol

from app.services.parsers.btg_adapter import ParseResult


class BrokerageParserPort(Protocol):
    """Any object that can parse a brokerage PDF into a ParseResult."""

    def parse(self, pdf_path: str, password: str | None = None) -> ParseResult:
        ...
