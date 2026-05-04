import re
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import update
from sqlmodel import Session, select

from app.db import engine
from app.models.db_models import ManualTransaction, Position, TickerAlias, Transaction
from app.models.schemas import TickerAliasCreate, TickerAliasOut, TickerAliasPatch

router = APIRouter(tags=["ticker-aliases"])

_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9]{2,4}\d{1,2}$")


def _normalize(s: str) -> str:
    return " ".join(s.split()).upper()


def _rename_position(session: Session, old_ticker: str, new_ticker: str) -> None:
    """Rename a Position row to new_ticker, preserving any manual overrides.

    SQLite has no ALTER PRIMARY KEY, so we copy-then-delete.
    If a Position already exists for new_ticker we merge manual overrides from the old row
    only when the new row has none set.
    """
    old_pos = session.get(Position, old_ticker)
    if not old_pos:
        return
    new_pos = session.get(Position, new_ticker)
    if new_pos is None:
        new_pos = Position(
            ticker=new_ticker,
            quantity=old_pos.quantity,
            mean_price=old_pos.mean_price,
            manual_mean_price=old_pos.manual_mean_price,
            manual_quantity=old_pos.manual_quantity,
        )
        session.add(new_pos)
    else:
        # Preserve manual overrides from old row if new row doesn't have them
        if new_pos.manual_mean_price is None and old_pos.manual_mean_price is not None:
            new_pos.manual_mean_price = old_pos.manual_mean_price
        if new_pos.manual_quantity is None and old_pos.manual_quantity is not None:
            new_pos.manual_quantity = old_pos.manual_quantity
        session.add(new_pos)
    session.delete(old_pos)


def _to_out(a: TickerAlias) -> TickerAliasOut:
    return TickerAliasOut(
        raw_name=a.raw_name,
        ticker=a.ticker,
        confirmed=a.confirmed,
        created_at=a.created_at.isoformat(),
        updated_at=a.updated_at.isoformat(),
    )


@router.get("/ticker-aliases", response_model=list[TickerAliasOut])
def list_aliases() -> list[TickerAliasOut]:
    with Session(engine) as session:
        aliases = session.exec(
            select(TickerAlias).order_by(TickerAlias.confirmed, TickerAlias.raw_name)
        ).all()
    return [_to_out(a) for a in aliases]


@router.post("/ticker-aliases", response_model=TickerAliasOut, status_code=201)
def create_alias(body: TickerAliasCreate) -> TickerAliasOut:
    """Create a confirmed alias (e.g. EMBR3 → EMBJ3 rename). Propagates to existing transactions."""
    ticker = body.ticker.upper().strip()
    if not _TICKER_RE.match(ticker):
        raise HTTPException(status_code=422, detail=f"Invalid B3 ticker: {ticker!r}")
    raw_name = _normalize(body.raw_name)
    with Session(engine) as session:
        existing = session.get(TickerAlias, raw_name)
        if existing:
            raise HTTPException(status_code=409, detail=f"Alias for {raw_name!r} already exists")
        alias = TickerAlias(raw_name=raw_name, ticker=ticker, confirmed=True)
        session.add(alias)

        # Propagate to Transaction and ManualTransaction rows
        for model in (Transaction, ManualTransaction):
            session.execute(
                update(model).where(model.ticker == raw_name).values(ticker=ticker)
            )

        # Rename Position row to new ticker (preserves manual overrides)
        _rename_position(session, raw_name, ticker)

        session.commit()
        session.refresh(alias)
    return _to_out(alias)


@router.patch("/ticker-aliases/{raw_name:path}", response_model=TickerAliasOut)
def confirm_alias(raw_name: str, body: TickerAliasPatch) -> TickerAliasOut:
    """Confirm or update an alias. Propagates ticker to all matching Transactions."""
    ticker = body.ticker.upper().strip()
    if not _TICKER_RE.match(ticker):
        raise HTTPException(status_code=422, detail=f"Invalid B3 ticker: {ticker!r}")

    raw_name = _normalize(raw_name)
    with Session(engine) as session:
        alias = session.get(TickerAlias, raw_name)
        if not alias:
            alias = TickerAlias(raw_name=raw_name)
            session.add(alias)

        old_ticker = alias.ticker
        alias.ticker = ticker
        alias.confirmed = True
        alias.updated_at = datetime.now(UTC)

        # Propagate to Transaction and ManualTransaction rows
        for match_key in {raw_name, old_ticker} - {None}:
            for model in (Transaction, ManualTransaction):
                session.execute(
                    update(model).where(model.ticker == match_key).values(ticker=ticker)
                )

        # Rename stale Position entries to the new ticker (preserves manual overrides)
        for match_key in {raw_name, old_ticker} - {None, ticker}:
            _rename_position(session, match_key, ticker)

        session.commit()
        session.refresh(alias)
    return _to_out(alias)


@router.delete("/ticker-aliases/{raw_name:path}", status_code=204)
def delete_alias(raw_name: str) -> None:
    raw_name = _normalize(raw_name)
    with Session(engine) as session:
        alias = session.get(TickerAlias, raw_name)
        if not alias:
            raise HTTPException(status_code=404, detail="Alias not found")
        session.delete(alias)
        session.commit()
