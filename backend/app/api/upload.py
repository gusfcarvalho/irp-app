import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlmodel import Session, select

from app.db import engine
from app.models.db_models import Transaction, Upload
from app.models.schemas import TransactionOut, UploadOut, UploadResponse
from app.repositories.upload import UploadRepository
from app.services.parsers.base import BrokerageParserPort
from app.services.parsers.btg_adapter import BTGParserAdapter
from app.services.ticker_service import TickerService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["importer"])
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))
parser: BrokerageParserPort = BTGParserAdapter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    password: str | None = Form(None),
) -> UploadResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload = Upload(filename=file.filename, stored_path="")
    target = UPLOAD_DIR / f"{upload.id}.pdf"

    data = await file.read()
    target.write_bytes(data)
    upload.stored_path = str(target)

    try:
        result = parser.parse(str(target), password=password)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc) or f"Failed to parse PDF: {type(exc).__name__}") from exc

    with Session(engine) as session:
        if result.note_number is not None:
            existing = session.exec(
                select(Upload).where(Upload.note_number == result.note_number)
            ).first()
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Nota {result.note_number} already imported (upload id: {existing.id})",
                )

        upload.note_number = result.note_number
        upload.settlement_fee = result.settlement_fee
        upload.registration_fee = result.registration_fee
        upload.term_fee = result.term_fee
        upload.ana_fee = result.ana_fee
        upload.emoluments = result.emoluments
        upload.operational_fee = result.operational_fee
        upload.execution = result.execution
        upload.custody_fee = result.custody_fee
        upload.taxes = result.taxes
        upload.irrf = result.irrf
        upload.other_fees = result.other_fees
        upload.depositary_fee = result.depositary_fee
        session.add(upload)
        session.flush()

        ticker_svc = TickerService(session)
        for trade in result.trades:
            if trade.quantity == 0:
                logger.warning(
                    "PDF %s (nota %s): parsed trade with quantity=0 — ticker=%s date=%s side=%s price=%s",
                    file.filename, result.note_number, trade.ticker, trade.trade_date, trade.side, trade.price,
                )

            ticker = ticker_svc.resolve(trade.ticker)
            session.add(
                Transaction(
                    upload_id=upload.id,
                    ticker=ticker,
                    trade_date=trade.trade_date,
                    side=trade.side,
                    quantity=trade.quantity,
                    price=trade.price,
                    market_type=trade.market_type,
                )
            )

        session.commit()
        session.refresh(upload)

    return UploadResponse(
        id=upload.id,
        filename=upload.filename,
        transactions_created=len(result.trades),
        pending_aliases=ticker_svc.pending_aliases,
    )


@router.get("/uploads", response_model=list[UploadOut])
def list_uploads() -> list[UploadOut]:
    with Session(engine) as session:
        repo = UploadRepository(session)
        uploads = repo.get_all()
        txns_by_upload = repo.get_transactions_grouped()

    return [
        UploadOut(
            id=u.id,
            filename=u.filename,
            broker=u.broker,
            note_number=u.note_number,
            uploaded_at=u.uploaded_at.isoformat(),
            settlement_fee=u.settlement_fee,
            registration_fee=u.registration_fee,
            term_fee=u.term_fee,
            ana_fee=u.ana_fee,
            emoluments=u.emoluments,
            operational_fee=u.operational_fee,
            execution=u.execution,
            custody_fee=u.custody_fee,
            taxes=u.taxes,
            irrf=u.irrf,
            other_fees=u.other_fees,
            depositary_fee=u.depositary_fee,
            transactions=[
                TransactionOut(
                    id=t.id,
                    upload_id=t.upload_id,
                    ticker=t.ticker,
                    trade_date=t.trade_date,
                    side=t.side,
                    quantity=t.quantity,
                    price=t.price,
                    market_type=t.market_type,
                )
                for t in txns_by_upload.get(u.id, [])
            ],
        )
        for u in uploads
    ]


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions() -> list[TransactionOut]:
    with Session(engine) as session:
        rows = UploadRepository(session).get_all_transactions()

    return [
        TransactionOut(
            id=row.id,
            upload_id=row.upload_id,
            ticker=row.ticker,
            trade_date=row.trade_date,
            side=row.side,
            quantity=row.quantity,
            price=row.price,
            market_type=row.market_type,
        )
        for row in rows
    ]
