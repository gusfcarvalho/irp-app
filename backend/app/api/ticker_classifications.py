from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import engine
from app.models.enums import AssetType
from app.repositories.ticker import TickerClassificationRepository

router = APIRouter(tags=["ticker-classifications"])

VALID_TYPES = {a.value for a in AssetType}


class ClassificationOut(BaseModel):
    ticker: str
    asset_type: str
    updated_at: str


class ClassificationPut(BaseModel):
    asset_type: str


@router.get("/ticker-classifications", response_model=list[ClassificationOut])
def list_classifications() -> list[ClassificationOut]:
    with Session(engine) as session:
        rows = TickerClassificationRepository(session).get_all()
    return [ClassificationOut(ticker=r.ticker, asset_type=r.asset_type, updated_at=r.updated_at.isoformat()) for r in rows]


@router.put("/ticker-classifications/{ticker}", response_model=ClassificationOut)
def set_classification(ticker: str, body: ClassificationPut) -> ClassificationOut:
    ticker = ticker.upper().strip()
    if body.asset_type not in VALID_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid asset_type {body.asset_type!r}. Valid: {sorted(VALID_TYPES)}")
    with Session(engine) as session:
        repo = TickerClassificationRepository(session)
        row = repo.upsert(ticker, body.asset_type)
        session.commit()
        session.refresh(row)
    return ClassificationOut(ticker=row.ticker, asset_type=row.asset_type, updated_at=row.updated_at.isoformat())


@router.delete("/ticker-classifications/{ticker}", status_code=204)
def delete_classification(ticker: str) -> None:
    ticker = ticker.upper().strip()
    with Session(engine) as session:
        repo = TickerClassificationRepository(session)
        row = repo.get_by_ticker(ticker)
        if not row:
            raise HTTPException(status_code=404, detail="Classification not found")
        repo.delete(row)
        session.commit()
