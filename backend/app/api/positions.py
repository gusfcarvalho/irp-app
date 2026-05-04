from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session

from app.db import engine
from app.models.db_models import Position
from app.repositories.position import PositionRepository
from app.services.position_service import PositionService
from app.services.tax_engine import classify_ticker, load_classification_overrides

router = APIRouter(tags=["positions"])


class ClosedPositionOut(BaseModel):
    ticker: str
    direction: str          # "LONG" | "SHORT"
    open_date: date | None
    close_date: date
    quantity: Decimal
    open_mean_price: Decimal
    close_price: Decimal
    realized_pnl: Decimal


class PositionOut(BaseModel):
    ticker: str
    computed_quantity: Decimal
    computed_mean_price: Decimal
    manual_quantity: Decimal | None
    manual_mean_price: Decimal | None
    effective_quantity: Decimal
    effective_mean_price: Decimal
    is_overridden: bool
    asset_type: str


class PositionPatch(BaseModel):
    manual_mean_price: Decimal | None = None
    manual_quantity: Decimal | None = None


class TradeStepOut(BaseModel):
    trade_date: date
    side: str
    quantity: Decimal
    raw_price: Decimal
    fee_per_unit: Decimal
    adjusted_price: Decimal
    qty_after: Decimal
    mean_price_after: Decimal
    closes_quantity: Decimal | None = None
    realized_pnl: Decimal | None = None


def _to_out(pos: Position, computed: dict, overrides: dict | None = None) -> PositionOut:
    cp = computed.get(pos.ticker)
    comp_qty = cp.quantity if cp else Decimal(0)
    comp_mean = cp.mean_price if cp else Decimal(0)
    eff_qty = pos.manual_quantity if pos.manual_quantity is not None else comp_qty
    eff_mean = pos.manual_mean_price if pos.manual_mean_price is not None else comp_mean
    return PositionOut(
        ticker=pos.ticker,
        computed_quantity=comp_qty,
        computed_mean_price=comp_mean,
        manual_quantity=pos.manual_quantity,
        manual_mean_price=pos.manual_mean_price,
        effective_quantity=eff_qty,
        effective_mean_price=eff_mean,
        is_overridden=pos.manual_mean_price is not None or pos.manual_quantity is not None,
        asset_type=classify_ticker(pos.ticker, overrides),
    )


@router.post("/positions/recalculate", response_model=list[PositionOut])
def recalculate_positions() -> list[PositionOut]:
    with Session(engine) as session:
        computed = PositionService(session).compute()
        overrides = load_classification_overrides(session)
        repo = PositionRepository(session)

        for ticker, cp in computed.items():
            repo.upsert_computed(ticker, cp.quantity, cp.mean_price)

        session.commit()
        return [_to_out(p, computed, overrides) for p in repo.get_all()]


@router.get("/positions", response_model=list[PositionOut])
def list_positions(
    as_of: Optional[date] = Query(default=None, description="Include transactions up to this date (YYYY-MM-DD)"),
) -> list[PositionOut]:
    with Session(engine) as session:
        computed = PositionService(session).compute(as_of_date=as_of)
        overrides = load_classification_overrides(session)
        repo = PositionRepository(session)
        all_positions = repo.get_all()
        tickers_in_db = {p.ticker for p in all_positions}
        for ticker, cp in computed.items():
            if ticker not in tickers_in_db:
                pos = Position(ticker=ticker, quantity=cp.quantity, mean_price=cp.mean_price)
                repo.save(pos)
                all_positions = list(all_positions) + [pos]
        session.commit()
        return [
            _to_out(p, computed, overrides)
            for p in all_positions
            if computed.get(p.ticker) and (
                computed[p.ticker].quantity != 0
                or p.manual_quantity is not None
            )
        ]


@router.get("/positions/{ticker}/breakdown", response_model=list[TradeStepOut])
def get_breakdown(
    ticker: str,
    as_of: Optional[date] = Query(default=None, description="Include transactions up to this date"),
) -> list[TradeStepOut]:
    with Session(engine) as session:
        _, steps, _ = PositionService(session).compute_with_steps(as_of_date=as_of)
    ticker_steps = steps.get(ticker)
    if ticker_steps is None:
        raise HTTPException(status_code=404, detail=f"No transactions found for {ticker!r}")
    return [
        TradeStepOut(
            trade_date=s.trade_date,
            side=s.side,
            quantity=s.quantity,
            raw_price=s.raw_price,
            fee_per_unit=s.fee_per_unit,
            adjusted_price=s.adjusted_price,
            qty_after=s.qty_after,
            mean_price_after=s.mean_price_after,
            closes_quantity=s.closes_quantity,
            realized_pnl=s.realized_pnl,
        )
        for s in ticker_steps
    ]


@router.get("/closed-positions", response_model=list[ClosedPositionOut])
def list_closed_positions(
    from_date: Optional[date] = Query(default=None, description="Only include positions closed on or after this date"),
    to_date: Optional[date] = Query(default=None, description="Only include positions closed on or before this date (also used as computation cutoff)"),
    ticker: Optional[str] = Query(default=None, description="Filter by ticker"),
) -> list[ClosedPositionOut]:
    with Session(engine) as session:
        _, _, closed = PositionService(session).compute_with_steps(as_of_date=to_date)
    if from_date:
        closed = [c for c in closed if c.close_date >= from_date]
    if to_date:
        closed = [c for c in closed if c.close_date <= to_date]
    if ticker:
        closed = [c for c in closed if c.ticker == ticker.upper()]
    return [
        ClosedPositionOut(
            ticker=c.ticker,
            direction=c.direction,
            open_date=c.open_date,
            close_date=c.close_date,
            quantity=c.quantity,
            open_mean_price=c.open_mean_price,
            close_price=c.close_price,
            realized_pnl=c.realized_pnl,
        )
        for c in closed
    ]


@router.patch("/positions/{ticker}", response_model=PositionOut)
def patch_position(ticker: str, body: PositionPatch) -> PositionOut:
    with Session(engine) as session:
        repo = PositionRepository(session)
        pos = repo.get_by_ticker(ticker)
        if pos is None:
            raise HTTPException(status_code=404, detail=f"Position {ticker!r} not found")
        if body.manual_mean_price is not None:
            pos.manual_mean_price = body.manual_mean_price
        if body.manual_quantity is not None:
            pos.manual_quantity = body.manual_quantity
        pos.updated_at = datetime.now(UTC)
        repo.save(pos)
        session.commit()
        session.refresh(pos)

        computed = PositionService(session).compute()
        overrides = load_classification_overrides(session)
        return _to_out(pos, computed, overrides)


@router.delete("/positions/{ticker}/override", response_model=PositionOut)
def clear_override(ticker: str) -> PositionOut:
    with Session(engine) as session:
        repo = PositionRepository(session)
        pos = repo.get_by_ticker(ticker)
        if pos is None:
            raise HTTPException(status_code=404, detail=f"Position {ticker!r} not found")
        pos.manual_mean_price = None
        pos.manual_quantity = None
        pos.updated_at = datetime.now(UTC)
        repo.save(pos)
        session.commit()
        session.refresh(pos)

        computed = PositionService(session).compute()
        overrides = load_classification_overrides(session)
        return _to_out(pos, computed, overrides)
