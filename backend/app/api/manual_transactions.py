from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from app.db import engine
from app.models.db_models import ManualTransaction
from app.models.schemas import ManualTransactionCreate, ManualTransactionOut

router = APIRouter(tags=["manual-transactions"])


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
        depositary_fee=txn.depositary_fee,
        created_at=txn.created_at.isoformat(),
    )


@router.post("/manual-transactions", response_model=ManualTransactionOut)
def create_manual_transaction(body: ManualTransactionCreate) -> ManualTransactionOut:
    with Session(engine) as session:
        txn = ManualTransaction(**body.model_dump(exclude={"ticker"}), ticker=body.ticker.upper())
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
    with Session(engine) as session:
        txn = session.get(ManualTransaction, txn_id)
        if txn is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        for field, value in body.model_dump().items():
            setattr(txn, field, value)
        txn.ticker = body.ticker.upper()
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
