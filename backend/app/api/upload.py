from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlmodel import Session, select

from app.db import engine
from app.models.db_models import Transaction, Upload
from app.models.schemas import TransactionOut, UploadResponse
from app.services.parsers.btg_adapter import BTGParserAdapter

router = APIRouter(tags=["importer"])
UPLOAD_DIR = Path("/data/uploads")
parser = BTGParserAdapter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload = Upload(filename=file.filename, stored_path="")
    target = UPLOAD_DIR / f"{upload.id}.pdf"

    data = await file.read()
    target.write_bytes(data)
    upload.stored_path = str(target)

    try:
        parsed_trades = parser.parse(str(target))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc

    with Session(engine) as session:
        session.add(upload)
        session.flush()

        for trade in parsed_trades:
            session.add(
                Transaction(
                    upload_id=upload.id,
                    ticker=trade.ticker,
                    trade_date=trade.trade_date,
                    side=trade.side,
                    quantity=trade.quantity,
                    price=trade.price,
                    market_type=trade.market_type,
                )
            )

        session.commit()

    return UploadResponse(
        id=upload.id,
        filename=upload.filename,
        transactions_created=len(parsed_trades),
    )


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions() -> list[TransactionOut]:
    with Session(engine) as session:
        rows = session.exec(select(Transaction).order_by(Transaction.trade_date.desc())).all()

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
