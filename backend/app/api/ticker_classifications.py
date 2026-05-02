from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import engine
from app.models.db_models import TickerClassification

router = APIRouter(tags=["ticker-classifications"])

VALID_TYPES = {"STOCK", "FII", "BDR", "ETF_RV", "ETF_RF", "SUBSCRICAO", "RF_POS", "RF_PRE"}


class ClassificationOut(BaseModel):
    ticker: str
    asset_type: str
    updated_at: str


class ClassificationPut(BaseModel):
    asset_type: str


def _to_out(c: TickerClassification) -> ClassificationOut:
    return ClassificationOut(
        ticker=c.ticker,
        asset_type=c.asset_type,
        updated_at=c.updated_at.isoformat(),
    )


@router.get("/ticker-classifications", response_model=list[ClassificationOut])
def list_classifications() -> list[ClassificationOut]:
    with Session(engine) as session:
        rows = session.exec(select(TickerClassification).order_by(TickerClassification.ticker)).all()
    return [_to_out(r) for r in rows]


@router.put("/ticker-classifications/{ticker}", response_model=ClassificationOut)
def set_classification(ticker: str, body: ClassificationPut) -> ClassificationOut:
    ticker = ticker.upper().strip()
    if body.asset_type not in VALID_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid asset_type {body.asset_type!r}. Valid: {sorted(VALID_TYPES)}")
    with Session(engine) as session:
        row = session.get(TickerClassification, ticker)
        if row is None:
            row = TickerClassification(ticker=ticker, asset_type=body.asset_type)
        else:
            row.asset_type = body.asset_type
            row.updated_at = datetime.now(UTC)
        session.add(row)
        session.commit()
        session.refresh(row)
    return _to_out(row)


@router.delete("/ticker-classifications/{ticker}", status_code=204)
def delete_classification(ticker: str) -> None:
    ticker = ticker.upper().strip()
    with Session(engine) as session:
        row = session.get(TickerClassification, ticker)
        if not row:
            raise HTTPException(status_code=404, detail="Classification not found")
        session.delete(row)
        session.commit()
