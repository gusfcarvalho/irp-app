"""Tax calculation engine for Brazilian IRPF.

Asset classification (B3 naming conventions):
- Ends in "11"               → FII  (20% tax, no R$20k exempt threshold)
- Ends in two digits 32–39   → BDR  (15% tax, no R$20k exempt threshold)
- Everything else             → STOCK (15% tax, exempt if total sold ≤ R$20k/month)

Accumulated loss carry-forward rules:
- A net loss in any month always accumulates into the carry-forward balance.
- An exempt month (stocks sold ≤ R$20k) with a profit does NOT consume the balance
  because there is no taxable event — the balance is preserved for future months.
- A non-exempt profitable month reduces the balance by the profit amount (floored at 0),
  and tax is applied only on the remaining taxable profit after the offset.
- Losses and profits do NOT cross between STOCK / BDR / FII categories.
"""

import re
from calendar import monthrange
from collections import defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from sqlmodel import Session, select

from app.models.db_models import ManualTransaction, TickerClassification, Upload
from app.models.schemas import AssetTaxReport, ClosedPositionTaxOut, MonthlyTaxReport
from app.services.position_engine import build_txns_with_fees, compute_positions_with_steps

_ZERO = Decimal(0)
_TWO_DP = Decimal("0.01")
_EXEMPT_THRESHOLD = Decimal("20000")

# All recognised asset types
AssetType = Literal["STOCK", "FII", "BDR", "ETF_RV", "ETF_RF", "SUBSCRICAO", "RF_POS", "RF_PRE"]

# Tax-calculation bucket: maps asset type → report section (None = skip entirely)
_TAX_BUCKET: dict[str, str | None] = {
    "STOCK":     "STOCK",
    "FII":       "FII",
    "BDR":       "BDR",
    "ETF_RV":    "BDR",   # same rules as BDR
    "SUBSCRICAO": "BDR",  # same rules as BDR
    "ETF_RF":    None,    # fixed-income ETF — no tax
    "RF_POS":    None,
    "RF_PRE":    None,
}

_ASSET_TYPES: tuple[str, ...] = ("STOCK", "BDR", "FII")

_BDR_SUFFIX = re.compile(r"3[2-9]$")


def classify_ticker(ticker: str, overrides: dict[str, str] | None = None) -> str:
    """Return the asset type for *ticker*, checking user overrides first."""
    t = ticker.upper().strip()
    if overrides and t in overrides:
        return overrides[t]
    if t.endswith("11"):
        return "FII"
    if _BDR_SUFFIX.search(t):
        return "BDR"
    return "STOCK"


def load_classification_overrides(session: Session) -> dict[str, str]:
    from sqlmodel import select
    rows = session.exec(select(TickerClassification)).all()
    return {r.ticker.upper(): r.asset_type for r in rows}


def _zero_by_type() -> dict[AssetType, Decimal]:
    return {k: _ZERO for k in _ASSET_TYPES}


def calculate_monthly_tax(session: Session, month: str) -> MonthlyTaxReport:
    """Calculate tax owed for the given month (format: 'YYYY-MM').

    Walks the full transaction history month-by-month to compute the accumulated
    loss balance entering the requested month, then applies it to reduce taxes.
    """
    target_year, target_month_int = int(month[:4]), int(month[5:7])
    start_date = date(target_year, target_month_int, 1)
    end_date = date(target_year, target_month_int, monthrange(target_year, target_month_int)[1])

    # ── 1. Full position engine run (no date cutoff) ─────────────────────────
    txns_with_fees, corp_actions = build_txns_with_fees(session)
    _, _, all_closed = compute_positions_with_steps(txns_with_fees, corp_actions)

    overrides = load_classification_overrides(session)

    def _bucket(ticker: str) -> str | None:
        return _TAX_BUCKET.get(classify_ticker(ticker, overrides))

    # ── 2. Build per-month P&L and sold-value maps ───────────────────────────
    # month_str → tax_bucket → value  (None buckets skipped)
    monthly_pnl: dict[str, dict[str, Decimal]] = defaultdict(lambda: _zero_by_type())
    monthly_sold: dict[str, dict[str, Decimal]] = defaultdict(lambda: _zero_by_type())

    for cp in all_closed:
        bucket = _bucket(cp.ticker)
        if bucket is None:
            continue
        m = cp.close_date.strftime("%Y-%m")
        monthly_pnl[m][bucket] += cp.realized_pnl

    for txn in txns_with_fees:
        if txn.side == "SELL":
            bucket = _bucket(txn.ticker)
            if bucket is None:
                continue
            m = txn.trade_date.strftime("%Y-%m")
            monthly_sold[m][bucket] += txn.raw_price * txn.quantity

    # ── 3. Walk all months before the target to build the carry-forward balance
    acc_loss = _zero_by_type()

    all_months_seen = sorted(
        {m for m in list(monthly_pnl.keys()) + list(monthly_sold.keys()) if m <= month}
    )

    for m in all_months_seen:
        if m == month:
            break  # stop before target month; handled separately below
        for atype in _ASSET_TYPES:
            pnl = monthly_pnl[m][atype]
            sold = monthly_sold[m][atype]
            exempt = atype == "STOCK" and sold <= _EXEMPT_THRESHOLD

            if pnl < _ZERO:
                # Loss always accumulates
                acc_loss[atype] += abs(pnl)
            elif pnl > _ZERO:
                # Any profit (taxable or exempt) consumes the carry-forward balance
                acc_loss[atype] = max(_ZERO, acc_loss[atype] - pnl)

    # ── 4. Target month: P&L, sold value, and closed-position detail ─────────
    target_pnl = monthly_pnl[month]
    target_sold = monthly_sold[month]

    positions_by_type: dict[str, list[ClosedPositionTaxOut]] = {k: [] for k in _ASSET_TYPES}
    for cp in all_closed:
        if not (start_date <= cp.close_date <= end_date):
            continue
        bucket = _bucket(cp.ticker)
        if bucket is None:
            continue
        positions_by_type[bucket].append(ClosedPositionTaxOut(
            ticker=cp.ticker,
            asset_type=classify_ticker(cp.ticker, overrides),
            direction=cp.direction,
            close_date=cp.close_date,
            quantity=cp.quantity,
            open_mean_price=cp.open_mean_price,
            close_price=cp.close_price,
            realized_pnl=cp.realized_pnl,
        ))

    # ── 5. IRRF for the target month ─────────────────────────────────────────
    irrf_by_type = _zero_by_type()

    sell_upload_notionals: dict[str, dict[str, Decimal]] = {}
    for txn in txns_with_fees:
        if txn.side == "SELL" and txn.upload_id and start_date <= txn.trade_date <= end_date:
            bucket = _bucket(txn.ticker)
            if bucket is None:
                continue
            if txn.upload_id not in sell_upload_notionals:
                sell_upload_notionals[txn.upload_id] = _zero_by_type()
            sell_upload_notionals[txn.upload_id][bucket] += txn.raw_price * txn.quantity

    if sell_upload_notionals:
        uploads = session.exec(
            select(Upload).where(Upload.id.in_(list(sell_upload_notionals.keys())))
        ).all()
        for upload in uploads:
            irrf = Decimal(upload.irrf or 0)
            if irrf == _ZERO:
                continue
            notionals = sell_upload_notionals[upload.id]
            total_notional = sum(notionals.values())
            if total_notional == _ZERO:
                continue
            for atype in _ASSET_TYPES:
                share = notionals[atype] / total_notional
                irrf_by_type[atype] += (irrf * share).quantize(_TWO_DP, rounding=ROUND_HALF_UP)

    manual_sells = session.exec(
        select(ManualTransaction).where(
            ManualTransaction.transaction_type == "SELL",
            ManualTransaction.trade_date >= start_date,
            ManualTransaction.trade_date <= end_date,
        )
    ).all()
    for mt in manual_sells:
        irrf = Decimal(mt.irrf or 0)
        if irrf != _ZERO:
            bucket = _bucket(mt.ticker)
            if bucket is not None:
                irrf_by_type[bucket] += irrf

    # ── 6. Build per-asset report applying accumulated losses ─────────────────
    def build_report(atype: AssetType, tax_rate: Decimal) -> AssetTaxReport:
        pnl = target_pnl[atype]
        sold = target_sold[atype]
        acc_before = acc_loss[atype]
        irrf = irrf_by_type[atype]
        exempt = atype == "STOCK" and sold <= _EXEMPT_THRESHOLD

        if pnl <= _ZERO:
            # Loss month: accumulate, no tax
            loss_applied = _ZERO
            taxable_profit = _ZERO
            gross_tax = _ZERO
            acc_after = acc_before + abs(pnl)
        elif exempt:
            # Exempt profit: no tax due, but losses are still consumed by the profit
            loss_applied = min(pnl, acc_before)
            taxable_profit = _ZERO
            gross_tax = _ZERO
            acc_after = acc_before - loss_applied
        else:
            # Taxable profit: apply carry-forward first
            loss_applied = min(pnl, acc_before)
            taxable_profit = pnl - loss_applied
            gross_tax = (taxable_profit * tax_rate).quantize(_TWO_DP, rounding=ROUND_HALF_UP)
            acc_after = acc_before - loss_applied

        tax_due = max(_ZERO, gross_tax - irrf)

        return AssetTaxReport(
            asset_type=atype,
            total_sold_value=sold,
            profit_loss=pnl,
            accumulated_loss_before=acc_before,
            accumulated_loss_applied=loss_applied,
            accumulated_loss_after=acc_after,
            taxable_profit=taxable_profit,
            irrf_withheld=irrf,
            tax_rate=tax_rate,
            gross_tax=gross_tax,
            tax_due=tax_due,
            exempt=exempt,
            closed_positions=positions_by_type[atype],
        )

    stocks = build_report("STOCK", Decimal("0.15"))
    bdr = build_report("BDR", Decimal("0.15"))
    fii = build_report("FII", Decimal("0.20"))

    return MonthlyTaxReport(
        month=month,
        stocks=stocks,
        bdr=bdr,
        fii=fii,
        total_tax_due=stocks.tax_due + bdr.tax_due + fii.tax_due,
    )
