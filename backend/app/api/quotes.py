from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import engine
from app.models.db_models import ManualTransaction, Transaction
from app.services.position_service import PositionService
from app.services.quote_service import fetch_and_store_quotes, get_latest_quotes

router = APIRouter(tags=["quotes"])


class QuoteOut(BaseModel):
    ticker: str
    date: date
    close_price: Decimal
    fetched_at: str


def _to_out(q) -> QuoteOut:
    return QuoteOut(
        ticker=q.ticker,
        date=q.quote_date,
        close_price=q.close_price,
        fetched_at=q.fetched_at.isoformat(),
    )


@router.get("/quotes", response_model=list[QuoteOut])
def get_quotes(
    tickers: list[str] = Query(default=None, description="B3 ticker symbols"),
) -> list[QuoteOut]:
    """Return the latest stored close price for each requested ticker."""
    with Session(engine) as session:
        if not tickers:
            computed = PositionService(session).compute()
            tickers = list(computed.keys())
        rows = get_latest_quotes(session, tickers)
    return [_to_out(r) for r in rows]


@router.post("/quotes/refresh", response_model=list[QuoteOut])
def refresh_quotes(
    tickers: list[str] = Query(default=None, description="B3 ticker symbols to refresh (omit for all open positions)"),
    full: bool = Query(default=False, description="When true, fetch from the earliest transaction date"),
) -> list[QuoteOut]:
    """Fetch fresh quotes from Yahoo Finance and persist them.

    Pass full=true to fetch full history from the earliest portfolio transaction date.
    """
    with Session(engine) as session:
        if not tickers:
            computed = PositionService(session).compute()
            tickers = list(computed.keys())

        start_date = None
        if full and tickers:
            t_min = session.exec(select(func.min(Transaction.trade_date))).first()
            m_min = session.exec(select(func.min(ManualTransaction.trade_date))).first()
            candidates = [d for d in [t_min, m_min] if d is not None]
            start_date = min(candidates) if candidates else None

        rows = fetch_and_store_quotes(session, tickers, start_date=start_date)
    return [_to_out(r) for r in rows]
