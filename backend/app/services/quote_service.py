"""Market quote service backed by a persistent Quote table.

Prices are fetched from Yahoo Finance (B3 tickers get the ".SA" suffix) and
stored as daily end-of-day closes.  The stored rows are the source of truth
shown in the UI; fetching is only triggered when the user clicks
"Atualizar cotações".
"""

import logging
import math
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models.db_models import Quote

logger = logging.getLogger(__name__)


def get_latest_quotes(session: Session, tickers: list[str]) -> list[Quote]:
    """Return the most recent stored Quote row for each requested ticker."""
    if not tickers:
        return []
    upper = [t.upper() for t in tickers]
    rows = session.exec(
        select(Quote)
        .where(Quote.ticker.in_(upper))
        .order_by(Quote.quote_date.desc())
    ).all()
    seen: set[str] = set()
    latest: list[Quote] = []
    for row in rows:
        if row.ticker not in seen:
            seen.add(row.ticker)
            latest.append(row)
    return latest


def fetch_and_store_quotes(
    session: Session,
    tickers: list[str],
    start_date=None,        # date | None — when set, fetch from this date to today
) -> list[Quote]:
    """Fetch quotes from Yahoo Finance and upsert into the Quote table.

    Pass start_date to fetch full history from that date; omit for last 30 days.
    Returns the latest Quote row per ticker after the upsert.
    """
    if not tickers:
        logger.info("fetch_and_store_quotes: no tickers provided")
        return []

    upper = [t.upper() for t in tickers]
    logger.info("fetch_and_store_quotes: fetching %d tickers from %s: %s", len(upper), start_date or "30d", upper)

    rows = _download_closes(upper, start_date=start_date)   # {ticker: {date: price}}
    logger.info("fetch_and_store_quotes: _download_closes returned %d tickers", len(rows))

    if not rows:
        logger.warning("fetch_and_store_quotes: no data returned from Yahoo Finance")
        return []

    now = datetime.now(UTC)
    inserted = updated = 0

    for ticker, daily in rows.items():
        for trade_date, price in daily.items():
            existing = session.get(Quote, (ticker, trade_date))
            if existing is None:
                session.add(Quote(ticker=ticker, quote_date=trade_date, close_price=price, fetched_at=now))
                inserted += 1
            else:
                existing.close_price = price
                existing.fetched_at = now
                session.add(existing)
                updated += 1

    logger.info("fetch_and_store_quotes: committing %d inserts, %d updates", inserted, updated)
    try:
        session.commit()
        logger.info("fetch_and_store_quotes: commit OK")
    except Exception as exc:
        logger.error("fetch_and_store_quotes: commit failed: %s", exc)
        raise

    result = get_latest_quotes(session, upper)
    logger.info("fetch_and_store_quotes: returning %d quotes", len(result))
    return result


def _download_closes(tickers: list[str], start_date=None) -> dict[str, dict]:
    """Return {ticker: {date: Decimal}} for the requested period.

    If start_date is given, fetch from that date to today; otherwise last 30 days.
    """
    from decimal import Decimal

    try:
        import pandas as pd
        import yfinance as yf
        logger.info("_download_closes: yfinance %s loaded OK", yf.__version__)
    except ImportError as exc:
        logger.error("_download_closes: import failed — %s", exc)
        return {}

    symbols = [t + ".SA" for t in tickers]
    logger.info("_download_closes: downloading %s from %s", symbols, start_date or "30d")
    try:
        if start_date is not None:
            from datetime import date as _date
            end = _date.today().isoformat()
            raw = yf.download(
                symbols,
                start=start_date.isoformat(),
                end=end,
                auto_adjust=True,
                progress=False,
            )
        else:
            raw = yf.download(
                symbols,
                period="30d",
                auto_adjust=True,
                progress=False,
            )
        logger.info("_download_closes: raw shape=%s columns_type=%s", raw.shape, type(raw.columns).__name__)

        if raw.empty:
            logger.warning("_download_closes: empty DataFrame returned by yfinance")
            return {}

        if isinstance(raw.columns, pd.MultiIndex):
            close_df = raw["Close"]
        else:
            close_df = raw[["Close"]].rename(columns={"Close": symbols[0]})

        logger.info("_download_closes: close_df columns=%s", close_df.columns.tolist())

        result: dict[str, dict] = {}
        for sym in symbols:
            if sym not in close_df.columns:
                logger.warning("_download_closes: %s not in close_df columns", sym)
                continue
            series = close_df[sym].dropna()
            ticker = sym.replace(".SA", "")
            result[ticker] = {
                row_date.date(): Decimal(str(round(float(val), 6)))
                for row_date, val in series.items()
                if val is not None and not (isinstance(val, float) and math.isnan(val))
            }
            logger.info("_download_closes: %s → %d rows", ticker, len(result[ticker]))
        return result
    except Exception as exc:
        logger.error("_download_closes: exception: %s", exc, exc_info=True)
        return {}
