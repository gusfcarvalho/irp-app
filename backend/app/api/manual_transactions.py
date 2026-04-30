from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from app.db import engine
from app.models.db_models import ManualTransaction
from app.models.schemas import ManualTransactionCreate, ManualTransactionOut

router = APIRouter(tags=["manual-transactions"])


def _validate_transaction(body: ManualTransactionCreate) -> None:
    """Validate that required fields are present based on transaction type."""
    if body.transaction_type in ("BUY", "SELL"):
        if body.quantity is None or body.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="quantity is required and must be positive for BUY/SELL",
            )
        if body.price is None or body.price <= 0:
            raise HTTPException(
                status_code=400,
                detail="price is required and must be positive for BUY/SELL",
            )
    elif body.transaction_type in ("GROUPING", "SPLITTING"):
        if body.ratio_from is None or body.ratio_from <= 0:
            raise HTTPException(
                status_code=400,
                detail="ratio_from is required and must be positive for GROUPING/SPLITTING",
            )
        if body.ratio_to is None or body.ratio_to <= 0:
            raise HTTPException(
                status_code=400,
                detail="ratio_to is required and must be positive for GROUPING/SPLITTING",
            )
    elif body.transaction_type == "BONUS":
        if body.quantity is None or body.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="quantity is required and must be positive for BONUS",
            )


def _to_out(txn: ManualTransaction) -> ManualTransactionOut:
    return ManualTransactionOut(
        id=txn.id,
        ticker=txn.ticker,
        trade_date=txn.trade_date,
        transaction_type=txn.transaction_type,
        quantity=txn.quantity,
        price=txn.price,
        ratio_from=txn.ratio_from,
        ratio_to=txn.ratio_to,
        settlement_fee=txn.settlement_fee,
        registration_fee=txn.registration_fee,
        term_fee=txn.term_fee,
        ana_fee=txn.ana_fee,
        emoluments=txn.emoluments,
        operational_fee=txn.operational_fee,
        execution=txn.execution,
        custody_fee=txn.custody_fee,
        taxes=txn.taxes,
        irrf=txn.irrf,
        other_fees=txn.other_fees,
        created_at=txn.created_at.isoformat(),
    )


@router.post("/manual-transactions", response_model=ManualTransactionOut)
def create_manual_transaction(body: ManualTransactionCreate) -> ManualTransactionOut:
    _validate_transaction(body)
    with Session(engine) as session:
        txn = ManualTransaction(
            ticker=body.ticker.upper(),
            trade_date=body.trade_date,
            transaction_type=body.transaction_type,
            quantity=body.quantity,
            price=body.price,
            ratio_from=body.ratio_from,
            ratio_to=body.ratio_to,
            settlement_fee=body.settlement_fee,
            registration_fee=body.registration_fee,
            term_fee=body.term_fee,
            ana_fee=body.ana_fee,
            emoluments=body.emoluments,
            operational_fee=body.operational_fee,
            execution=body.execution,
            custody_fee=body.custody_fee,
            taxes=body.taxes,
            irrf=body.irrf,
            other_fees=body.other_fees,
        )
        session.add(txn)
        session.commit()
        session.refresh(txn)
        return _to_out(txn)


@router.get("/manual-transactions", response_model=list[ManualTransactionOut])
def list_manual_transactions() -> list[ManualTransactionOut]:
    with Session(engine) as session:
        txns = session.exec(
            select(ManualTransaction).order_by(ManualTransaction.trade_date.desc())
        ).all()
        return [_to_out(t) for t in txns]


@router.get("/manual-transactions/{txn_id}", response_model=ManualTransactionOut)
def get_manual_transaction(txn_id: str) -> ManualTransactionOut:
    with Session(engine) as session:
        txn = session.get(ManualTransaction, txn_id)
        if txn is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return _to_out(txn)


@router.put("/manual-transactions/{txn_id}", response_model=ManualTransactionOut)
def update_manual_transaction(
    txn_id: str, body: ManualTransactionCreate
) -> ManualTransactionOut:
    _validate_transaction(body)
    with Session(engine) as session:
        txn = session.get(ManualTransaction, txn_id)
        if txn is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        txn.ticker = body.ticker.upper()
        txn.trade_date = body.trade_date
        txn.transaction_type = body.transaction_type
        txn.quantity = body.quantity
        txn.price = body.price
        txn.ratio_from = body.ratio_from
        txn.ratio_to = body.ratio_to
        txn.settlement_fee = body.settlement_fee
        txn.registration_fee = body.registration_fee
        txn.term_fee = body.term_fee
        txn.ana_fee = body.ana_fee
        txn.emoluments = body.emoluments
        txn.operational_fee = body.operational_fee
        txn.execution = body.execution
        txn.custody_fee = body.custody_fee
        txn.taxes = body.taxes
        txn.irrf = body.irrf
        txn.other_fees = body.other_fees
        session.add(txn)
        session.commit()
        session.refresh(txn)
        return _to_out(txn)


@router.delete("/manual-transactions/{txn_id}")
def delete_manual_transaction(txn_id: str) -> dict[str, str]:
    with Session(engine) as session:
        txn = session.get(ManualTransaction, txn_id)
        if txn is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        session.delete(txn)
        session.commit()
        return {"status": "deleted"}
