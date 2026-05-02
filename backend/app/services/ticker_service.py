"""Resolves raw ticker strings from PDF imports to canonical B3 tickers."""
import re

from sqlmodel import Session

from app.models.db_models import TickerAlias
from app.repositories.ticker import TickerAliasRepository

_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9]{2,4}\d{1,2}$")


def _normalize(s: str) -> str:
    return " ".join(s.split()).upper()


class TickerService:
    """Resolves raw tickers and manages alias lifecycle within a session."""

    def __init__(self, session: Session) -> None:
        self._s = session
        self._repo = TickerAliasRepository(session)
        self._pending: list[str] = []

    def resolve(self, raw_ticker: str) -> str:
        """Return the canonical ticker for *raw_ticker*.

        If *raw_ticker* already looks like a valid B3 code (regex match), return it as-is.
        Otherwise check the alias table: if a confirmed alias exists, return the mapped ticker.
        If no alias exists yet, create a pending one and return the raw_name so the caller
        can store the transaction under the unresolved name.

        Call :attr:`pending_aliases` after processing all trades to find what needs confirmation.
        """
        ticker = raw_ticker.strip()
        if _TICKER_RE.match(ticker.upper()):
            return ticker.upper()

        raw_name = _normalize(ticker)
        alias = self._repo.get_by_raw_name(raw_name)

        if alias and alias.confirmed and alias.ticker:
            return alias.ticker

        if alias is None:
            alias = TickerAlias(raw_name=raw_name)
            self._repo.save(alias)

        if raw_name not in self._pending:
            self._pending.append(raw_name)

        return raw_name

    @property
    def pending_aliases(self) -> list[str]:
        return list(self._pending)
