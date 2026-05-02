import json
import re
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, select

from app.db import engine
from app.models.db_models import TaxCalculationCache, TaxPayment
from app.models.schemas import MonthlyTaxReport, TaxPaymentOut, TaxPaymentUpsert
from app.services.tax_engine import calculate_monthly_tax

router = APIRouter(tags=["tax"])

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_TOLERANCE = Decimal("0.01")


def _payment_to_out(p: TaxPayment) -> TaxPaymentOut:
    return TaxPaymentOut(
        month=p.month,
        amount_paid=p.amount_paid,
        paid_at=p.paid_at.isoformat(),
        notes=p.notes,
    )


def _attach_payment(report: MonthlyTaxReport, session: Session) -> MonthlyTaxReport:
    payment = session.get(TaxPayment, report.month)
    if payment:
        report.amount_paid = payment.amount_paid
        report.payment_diverges = abs(payment.amount_paid - report.total_tax_due) > _TOLERANCE
    return report


def _save_cache(report: MonthlyTaxReport, session: Session) -> None:
    now = datetime.now(UTC)
    cache = session.get(TaxCalculationCache, report.month)
    if cache is None:
        cache = TaxCalculationCache(month=report.month, report_json="", calculated_at=now)
    cache.report_json = report.model_dump_json()
    cache.calculated_at = now
    session.add(cache)
    session.commit()


@router.get("/tax", response_model=MonthlyTaxReport)
def get_monthly_tax(
    month: str = Query(..., description="Month in YYYY-MM format", example="2024-01"),
) -> MonthlyTaxReport:
    if not _MONTH_RE.match(month):
        raise HTTPException(status_code=422, detail="month must be in YYYY-MM format")
    with Session(engine) as session:
        cache = session.get(TaxCalculationCache, month)
        if cache is None:
            raise HTTPException(status_code=404, detail="No cached calculation for this month. Click Calcular to compute.")
        report = MonthlyTaxReport.model_validate_json(cache.report_json)
        report.cached_at = cache.calculated_at
        _attach_payment(report, session)
    return report


@router.post("/tax/calculate", response_model=MonthlyTaxReport)
def calculate_and_cache_tax(
    month: str = Query(..., description="Month in YYYY-MM format", example="2024-01"),
) -> MonthlyTaxReport:
    if not _MONTH_RE.match(month):
        raise HTTPException(status_code=422, detail="month must be in YYYY-MM format")
    with Session(engine) as session:
        report = calculate_monthly_tax(session, month)
        _save_cache(report, session)
        _attach_payment(report, session)
        report.cached_at = session.get(TaxCalculationCache, month).calculated_at
    return report


@router.get("/tax-payments", response_model=list[TaxPaymentOut])
def list_tax_payments() -> list[TaxPaymentOut]:
    with Session(engine) as session:
        payments = session.exec(select(TaxPayment).order_by(TaxPayment.month.desc())).all()
    return [_payment_to_out(p) for p in payments]


@router.put("/tax-payments/{month}", response_model=TaxPaymentOut)
def upsert_tax_payment(month: str, body: TaxPaymentUpsert) -> TaxPaymentOut:
    if not _MONTH_RE.match(month):
        raise HTTPException(status_code=422, detail="month must be in YYYY-MM format")
    with Session(engine) as session:
        payment = session.get(TaxPayment, month)
        if payment is None:
            payment = TaxPayment(month=month, amount_paid=body.amount_paid, notes=body.notes)
        else:
            payment.amount_paid = body.amount_paid
            payment.notes = body.notes
            payment.paid_at = datetime.now(UTC)
        session.add(payment)
        session.commit()
        session.refresh(payment)
    return _payment_to_out(payment)


@router.delete("/tax-payments/{month}", status_code=204)
def delete_tax_payment(month: str) -> None:
    if not _MONTH_RE.match(month):
        raise HTTPException(status_code=422, detail="month must be in YYYY-MM format")
    with Session(engine) as session:
        payment = session.get(TaxPayment, month)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        session.delete(payment)
        session.commit()
