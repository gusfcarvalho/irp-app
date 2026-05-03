"""Portfolio history endpoint — market-value evolution over time."""

from bisect import bisect_right
from collections import defaultdict
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import engine
from app.models.db_models import Quote
from app.services.position_engine import build_txns_with_fees, compute_positions_with_steps
from app.services.tax_engine import classify_ticker, load_classification_overrides

router = APIRouter(tags=["dashboard"])


class HistoryPoint(BaseModel):
    date: str                                    # ISO YYYY-MM-DD
    by_category: dict[str, float]                # category → market value
    breakdown: dict[str, dict[str, float]]       # category → ticker → market value
    total: float                                  # total market value
    cost_total: float                             # total cost basis (reference line)


class PortfolioHistoryResponse(BaseModel):
    points: list[HistoryPoint]
    asset_types: list[str]                       # ordered list of categories present
    last_quote_date: str | None = None           # ISO date of the most recent stored quote


@router.get("/portfolio-history", response_model=PortfolioHistoryResponse)
def get_portfolio_history(
    mode: str = Query(default="monthly", pattern="^(daily|weekly|monthly)$"),
) -> PortfolioHistoryResponse:
    with Session(engine) as session:
        txns, corp_actions = build_txns_with_fees(session)
        _, steps, _ = compute_positions_with_steps(txns, corp_actions)
        overrides = load_classification_overrides(session)
        quotes_raw = session.exec(select(Quote)).all()
        last_quote_date_val = session.exec(select(func.max(Quote.quote_date))).first()

    # Build binary-search-friendly quote lookup per ticker
    raw: dict[str, list[tuple[date, Decimal]]] = defaultdict(list)
    for q in quotes_raw:
        raw[q.ticker].append((q.quote_date, q.close_price))
    quotes_by_ticker: dict[str, tuple[list[date], list[Decimal]]] = {}
    for ticker, entries in raw.items():
        entries.sort()
        quotes_by_ticker[ticker] = ([e[0] for e in entries], [e[1] for e in entries])

    def get_market_price(ticker: str, snap_date: date, fallback: Decimal) -> Decimal:
        if ticker not in quotes_by_ticker:
            return fallback
        dates, prices = quotes_by_ticker[ticker]
        idx = bisect_right(dates, snap_date) - 1
        return prices[idx] if idx >= 0 else fallback

    last_quote_date = last_quote_date_val.isoformat() if last_quote_date_val else None

    if not steps:
        return PortfolioHistoryResponse(points=[], asset_types=[], last_quote_date=last_quote_date)

    # ── 1. Flatten all trade steps into a sorted event list ──────────────────
    events: list[tuple[date, str, int, Decimal]] = []
    for ticker, ticker_steps in steps.items():
        for s in ticker_steps:
            events.append((s.trade_date, ticker, s.qty_after, s.mean_price_after))
    events.sort(key=lambda e: e[0])

    # ── 2. Walk events chronologically, maintaining portfolio state ───────────
    portfolio: dict[str, tuple[int, Decimal]] = {}   # ticker → (qty, mean_price)
    raw_snapshots: list[tuple[date, dict]] = []

    i = 0
    while i < len(events):
        current_date = events[i][0]
        while i < len(events) and events[i][0] == current_date:
            _, ticker, qty_after, mean_price_after = events[i]
            if qty_after != 0:
                portfolio[ticker] = (abs(qty_after), mean_price_after)
            else:
                portfolio.pop(ticker, None)
            i += 1
        raw_snapshots.append((current_date, dict(portfolio)))

    # ── 2.5. Forward-fill to cover all quote dates ───────────────────────────
    # raw_snapshots only has trade dates; expand to every date we have a quote
    # so the chart shows continuous market-value evolution, not just trade events.
    if raw_snapshots and quotes_raw:
        portfolio_by_trade_date = {d: port for d, port in raw_snapshots}
        first_trade_date = raw_snapshots[0][0]
        quote_dates = {q.quote_date for q in quotes_raw if q.quote_date >= first_trade_date}
        all_dates = sorted({d for d, _ in raw_snapshots} | quote_dates)

        expanded: list[tuple[date, dict]] = []
        current_port: dict = {}
        for d in all_dates:
            if d in portfolio_by_trade_date:
                current_port = portfolio_by_trade_date[d]
            if current_port:
                expanded.append((d, dict(current_port)))
        raw_snapshots = expanded

    # ── 3. Resample ───────────────────────────────────────────────────────────
    resampled = _resample(raw_snapshots, mode)[-30:]

    # ── 4. Build output ───────────────────────────────────────────────────────
    all_categories: set[str] = set()
    points: list[HistoryPoint] = []

    for snap_date, port in resampled:
        by_cat: dict[str, float] = defaultdict(float)
        breakdown: dict[str, dict[str, float]] = defaultdict(dict)
        cost_total = 0.0

        for ticker, (qty, mean_price) in port.items():
            cat = classify_ticker(ticker, overrides)
            mkt_price = get_market_price(ticker, snap_date, mean_price)
            mkt_val = float(qty * mkt_price)
            cost_val = float(qty * mean_price)

            by_cat[cat] += mkt_val
            breakdown[cat][ticker] = round(mkt_val, 2)
            cost_total += cost_val
            all_categories.add(cat)

        total = sum(by_cat.values())
        points.append(HistoryPoint(
            date=snap_date.isoformat(),
            by_category={k: round(v, 2) for k, v in by_cat.items()},
            breakdown={k: v for k, v in breakdown.items()},
            total=round(total, 2),
            cost_total=round(cost_total, 2),
        ))

    # Order categories: STOCK → BDR → FII → ETF_RV → rest
    ordered = [c for c in (
        "STOCK", "BDR", "FII", "ETF_RV", "ETF_RF", "SUBSCRICAO",
        "TD", "CDB", "LCI", "LCA", "LCF", "LIG", "CRI", "CRA", "DEB",
        "RF_POS", "RF_PRE",
    ) if c in all_categories]
    ordered += sorted(all_categories - set(ordered))

    return PortfolioHistoryResponse(points=points, asset_types=ordered, last_quote_date=last_quote_date)


def _resample(
    snapshots: list[tuple[date, dict]],
    mode: str,
) -> list[tuple[date, dict]]:
    if mode == "daily" or not snapshots:
        return snapshots

    period_buckets: dict = {}
    for snap_date, port in snapshots:
        key = _period_key(snap_date, mode)
        period_buckets[key] = (snap_date, port)

    return [period_buckets[key] for key in sorted(period_buckets)]


def _period_key(d: date, mode: str) -> tuple:
    if mode == "weekly":
        iso = d.isocalendar()
        return (iso.year, iso.week)
    return (d.year, d.month)
