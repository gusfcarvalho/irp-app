import logging
import os
from datetime import UTC, date, datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import engine
from app.models.db_models import Transaction, Upload
from app.repositories.ticker import TickerClassificationRepository
from app.services.parsers.b3_movimentacao_parser import parse_movimentacao
from app.services.parsers.b3_posicao_parser import parse_posicao
from app.services.ticker_service import TickerService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["b3-importer"])
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))


class B3ImportResponse(BaseModel):
    id: str
    filename: str
    transactions_created: int
    skipped: int = 0
    errors: list[str] = []
    pending_aliases: list[str] = []


def _check_duplicate(session: Session, filename: str) -> Upload | None:
    return session.exec(select(Upload).where(Upload.note_number == filename)).first()


@router.post("/b3/posicao", response_model=B3ImportResponse)
async def import_b3_posicao(file: UploadFile = File(...)) -> B3ImportResponse:
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only XLSX files are supported")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload = Upload(filename=file.filename, broker="B3", stored_path="")
    target = UPLOAD_DIR / f"{upload.id}.xlsx"

    data = await file.read()
    target.write_bytes(data)
    upload.stored_path = str(target)
    upload.note_number = file.filename  # dedup key

    with Session(engine) as session:
        existing = _check_duplicate(session, file.filename)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Arquivo '{file.filename}' já foi importado (upload id: {existing.id})",
            )

        result = parse_posicao(str(target))
        if not result.trades and result.errors:
            raise HTTPException(status_code=400, detail="; ".join(result.errors))

        session.add(upload)
        session.flush()

        ticker_svc = TickerService(session)
        classification_repo = TickerClassificationRepository(session)
        today = date.today()
        for trade in result.trades:
            ticker = ticker_svc.resolve(trade.ticker)
            session.add(Transaction(
                upload_id=upload.id,
                ticker=ticker,
                trade_date=today,
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
                market_type="SWING",
                source="B3_POSICAO",
                needs_review=True,
            ))
            if trade.asset_type:
                classification_repo.upsert(ticker, trade.asset_type)

        session.commit()
        upload_id = upload.id

    return B3ImportResponse(
        id=upload_id,
        filename=file.filename,
        transactions_created=len(result.trades),
        errors=result.errors,
        pending_aliases=ticker_svc.pending_aliases,
    )


@router.post("/b3/movimentacao", response_model=B3ImportResponse)
async def import_b3_movimentacao(file: UploadFile = File(...)) -> B3ImportResponse:
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only XLSX files are supported")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload = Upload(filename=file.filename, broker="B3", stored_path="")
    target = UPLOAD_DIR / f"{upload.id}.xlsx"

    data = await file.read()
    target.write_bytes(data)
    upload.stored_path = str(target)
    upload.note_number = file.filename  # dedup key

    with Session(engine) as session:
        existing = _check_duplicate(session, file.filename)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Arquivo '{file.filename}' já foi importado (upload id: {existing.id})",
            )

        result = parse_movimentacao(str(target))
        if not result.trades and result.errors:
            raise HTTPException(status_code=400, detail="; ".join(result.errors))

        session.add(upload)
        session.flush()

        ticker_svc = TickerService(session)
        classification_repo = TickerClassificationRepository(session)
        for trade in result.trades:
            ticker = ticker_svc.resolve(trade.ticker)
            session.add(Transaction(
                upload_id=upload.id,
                ticker=ticker,
                trade_date=trade.trade_date,
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
                market_type="SWING",
                source="B3_MOVIMENTACAO",
                needs_review=False,
            ))
            if trade.asset_type:
                classification_repo.upsert(ticker, trade.asset_type)

        session.commit()
        upload_id = upload.id

    return B3ImportResponse(
        id=upload_id,
        filename=file.filename,
        transactions_created=len(result.trades),
        skipped=result.skipped,
        errors=result.errors,
        pending_aliases=ticker_svc.pending_aliases,
    )
