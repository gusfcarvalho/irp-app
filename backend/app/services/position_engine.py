"""Position engine: fee-adjusted custo médio (Brazilian weighted average cost).

Fee distribution
----------------
Each Upload (nota) carries broker fees that must be spread across the transactions
in that nota.  IRRF is excluded — it is a withholding tax on profit, not a cost
basis component.

Fees are distributed proportionally by notional value
    weight_i = (qty_i × price_i) / Σ(qty_j × price_j)
    fee_per_unit_i = (total_fees × weight_i) / qty_i

BUY  → adjusted_price = price + fee_per_unit  (cost basis increases)
SELL → adjusted_price = price - fee_per_unit  (net proceeds decrease)

Custo médio
-----------
Processes transactions chronologically (trade_date, then upload date).

BUY (long or covering short):
    If currently long (qty >= 0):
        new_mean = (old_qty × old_mean + buy_qty × adj_price) / (old_qty + buy_qty)
        new_qty  = old_qty + buy_qty
    If currently short (qty < 0) and new_qty <= 0 (still short after partial cover):
        mean_price unchanged, new_qty = old_qty + buy_qty
    If currently short (qty < 0) and new_qty > 0 (covered short, now long):
        new_mean = adj_price (new long established at buy price), new_qty = new_qty
    if new_qty == 0: mean resets to 0

SELL (long or going short):
    If currently long (qty >= 0) and new_qty >= 0 (partial or full close):
        mean_price unchanged, new_qty = old_qty − sell_qty
    If currently long (qty >= 0) and new_qty < 0 (oversell → opens short):
        new_mean = adj_price (short established at sell price), new_qty = new_qty
    If currently short (qty < 0):
        weighted average of existing short and new short quantity
        new_qty = old_qty − sell_qty (more negative)
    if new_qty == 0: mean resets to 0

Corporate Actions
-----------------
GROUPING: N shares become M shares where M < N (e.g., 2:1 means 200 → 100)
          new_qty = old_qty × (ratio_to / ratio_from)
          new_mean = old_mean × (ratio_from / ratio_to)  (total cost preserved)
          Applies to both long (qty > 0) and short (qty < 0) positions.

SPLITTING: N shares become M shares where M > N (e.g., 1:2 means 100 → 200)
           Same formula as grouping.

BONUS: Free shares given to shareholder
       Treated as BUY at price = 0 (or specified cost basis)
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

logger = logging.getLogger(__name__)


_FEE_FIELDS = (
    "settlement_fee",
    "registration_fee",
    "term_fee",
    "ana_fee",
    "emoluments",
    "operational_fee",
    "execution",
    "custody_fee",
    "taxes",
    "other_fees",
)

_ZERO = Decimal(0)
_QUANTIZE = Decimal("0.00000001")


@dataclass
class TxnWithFees:
    """A transaction row plus the fee context from its parent upload."""
    txn_id: str
    upload_id: str | None  # None for manual transactions
    ticker: str
    trade_date: object          # datetime.date
    uploaded_at: datetime
    side: str                   # "BUY" | "SELL" | "BONUS"
    quantity: int
    raw_price: Decimal
    total_nota_fees: Decimal    # sum of non-IRRF fees for the whole nota
    nota_notional: Decimal      # sum of qty×price for all txns in the nota


@dataclass
class CorporateAction:
    """A grouping or splitting corporate action."""
    txn_id: str
    ticker: str
    trade_date: object          # datetime.date
    created_at: datetime
    action_type: str            # "GROUPING" | "SPLITTING"
    ratio_from: int
    ratio_to: int


@dataclass
class ComputedPosition:
    ticker: str
    quantity: int
    mean_price: Decimal


@dataclass
class ClosedPosition:
    """A position that was fully or partially closed when qty crossed through zero."""
    ticker: str
    direction: str              # "LONG" | "SHORT" — what was closed
    open_date: object           # datetime.date — when this position segment was opened
    close_date: object          # datetime.date — trade_date of the closing transaction
    quantity: int               # shares closed (always positive)
    open_mean_price: Decimal    # cost basis / avg short entry at time of close
    close_price: Decimal        # fee-adjusted price of the closing transaction
    realized_pnl: Decimal       # (close - open) × qty for LONG; (open - close) × qty for SHORT


@dataclass
class TradeStep:
    """One row in the custo médio history for a ticker."""
    trade_date: object          # datetime.date
    side: str                   # "BUY" | "SELL" | "BONUS" | "GROUPING" | "SPLITTING"
    quantity: int
    raw_price: Decimal
    fee_per_unit: Decimal       # allocated broker fee per share (IRRF excluded)
    adjusted_price: Decimal     # raw_price ± fee_per_unit
    qty_after: int
    mean_price_after: Decimal   # running custo médio after this trade
    closes_quantity: int | None = None   # shares closed by this step (set when qty crosses zero)
    realized_pnl: Decimal | None = None  # fee-adjusted P&L on the closed portion


def _total_non_irrf_fees(obj) -> Decimal:
    """Sum non-IRRF fees from an Upload or ManualTransaction."""
    return sum(
        (getattr(obj, f, _ZERO) or _ZERO) for f in _FEE_FIELDS
    )


def _fee_per_unit(txn: TxnWithFees) -> Decimal:
    if txn.nota_notional == _ZERO or txn.quantity == 0:
        return _ZERO
    txn_notional = txn.raw_price * txn.quantity
    fee_share = txn.total_nota_fees * (txn_notional / txn.nota_notional)
    return fee_share / txn.quantity


def _adjusted_price(txn: TxnWithFees) -> Decimal:
    fpu = _fee_per_unit(txn)
    if txn.side in ("BUY", "BONUS"):
        return txn.raw_price + fpu
    else:
        return txn.raw_price - fpu


def compute_positions(
    txns_with_fees: list[TxnWithFees],
    corporate_actions: list[CorporateAction] | None = None,
) -> dict[str, ComputedPosition]:
    """Return a dict of ticker → ComputedPosition from transactions and corporate actions."""
    return compute_positions_with_steps(txns_with_fees, corporate_actions)[0]


def compute_positions_with_steps(
    txns_with_fees: list[TxnWithFees],
    corporate_actions: list[CorporateAction] | None = None,
) -> tuple[dict[str, ComputedPosition], dict[str, list[TradeStep]], list[ClosedPosition]]:
    """Return (positions, steps, closed_positions).

    steps[ticker] is the full custo médio history for that ticker.
    closed_positions lists every time a position crossed through zero (realized P&L events).
    """
    corporate_actions = corporate_actions or []

    # Create unified event list for chronological processing
    events: list[tuple] = []
    for txn in txns_with_fees:
        events.append((txn.trade_date, txn.uploaded_at, "txn", txn))
    for ca in corporate_actions:
        events.append((ca.trade_date, ca.created_at, "ca", ca))

    events.sort(key=lambda e: (e[0], e[1]))

    # (qty, mean_price, open_date)
    positions: dict[str, tuple[int, Decimal, object]] = {}
    steps: dict[str, list[TradeStep]] = {}
    closed_positions: list[ClosedPosition] = []

    for _, _, event_type, event in events:
        if event_type == "txn":
            txn = event
            if txn.quantity == 0:
                logger.warning(
                    "Skipping zero-quantity transaction: txn_id=%s upload_id=%s ticker=%s side=%s trade_date=%s",
                    txn.txn_id, txn.upload_id, txn.ticker, txn.side, txn.trade_date,
                )
                continue
            fpu = _fee_per_unit(txn).quantize(_QUANTIZE, rounding=ROUND_HALF_UP)
            adj = _adjusted_price(txn).quantize(_QUANTIZE, rounding=ROUND_HALF_UP)
            curr_qty, curr_mean, curr_open_date = positions.get(txn.ticker, (0, _ZERO, None))

            closes_quantity: int | None = None
            realized_pnl: Decimal | None = None

            if txn.side in ("BUY", "BONUS"):
                new_qty = curr_qty + txn.quantity

                if curr_qty >= 0:
                    # Adding to long position (or opening one from zero)
                    new_mean = (
                        (curr_mean * curr_qty + adj * txn.quantity) / new_qty
                    ).quantize(_QUANTIZE, rounding=ROUND_HALF_UP)
                    new_open_date = curr_open_date or txn.trade_date
                elif new_qty < 0:
                    # Partial short cover: realizes P&L on the covered qty; mean unchanged
                    closed_qty = txn.quantity
                    pnl = (curr_mean - adj) * closed_qty
                    closed_positions.append(ClosedPosition(
                        ticker=txn.ticker,
                        direction="SHORT",
                        open_date=curr_open_date,
                        close_date=txn.trade_date,
                        quantity=closed_qty,
                        open_mean_price=curr_mean,
                        close_price=adj,
                        realized_pnl=pnl.quantize(_QUANTIZE, rounding=ROUND_HALF_UP),
                    ))
                    closes_quantity = closed_qty
                    realized_pnl = pnl.quantize(_QUANTIZE, rounding=ROUND_HALF_UP)
                    new_mean = curr_mean
                    new_open_date = curr_open_date
                else:
                    # Short position fully closed (new_qty == 0) or crossed into long (new_qty > 0)
                    closed_qty = abs(curr_qty)
                    pnl = (curr_mean - adj) * closed_qty
                    closed_positions.append(ClosedPosition(
                        ticker=txn.ticker,
                        direction="SHORT",
                        open_date=curr_open_date,
                        close_date=txn.trade_date,
                        quantity=closed_qty,
                        open_mean_price=curr_mean,
                        close_price=adj,
                        realized_pnl=pnl.quantize(_QUANTIZE, rounding=ROUND_HALF_UP),
                    ))
                    closes_quantity = closed_qty
                    realized_pnl = pnl.quantize(_QUANTIZE, rounding=ROUND_HALF_UP)
                    new_mean = adj if new_qty > 0 else _ZERO
                    new_open_date = txn.trade_date if new_qty > 0 else None

                positions[txn.ticker] = (new_qty, new_mean, new_open_date)

            else:  # SELL
                new_qty = curr_qty - txn.quantity

                if curr_qty <= 0:
                    # Deepening short (or opening one from zero); weighted average
                    short_qty_before = abs(curr_qty)
                    new_mean = (
                        (curr_mean * short_qty_before + adj * txn.quantity) / abs(new_qty)
                    ).quantize(_QUANTIZE, rounding=ROUND_HALF_UP)
                    new_open_date = curr_open_date or txn.trade_date
                elif new_qty > 0:
                    # Partial long sell: realizes P&L on the sold qty; mean unchanged
                    closed_qty = txn.quantity
                    pnl = (adj - curr_mean) * closed_qty
                    closed_positions.append(ClosedPosition(
                        ticker=txn.ticker,
                        direction="LONG",
                        open_date=curr_open_date,
                        close_date=txn.trade_date,
                        quantity=closed_qty,
                        open_mean_price=curr_mean,
                        close_price=adj,
                        realized_pnl=pnl.quantize(_QUANTIZE, rounding=ROUND_HALF_UP),
                    ))
                    closes_quantity = closed_qty
                    realized_pnl = pnl.quantize(_QUANTIZE, rounding=ROUND_HALF_UP)
                    new_mean = curr_mean
                    new_open_date = curr_open_date
                else:
                    # Long position fully closed (new_qty == 0) or crossed into short (new_qty < 0)
                    closed_qty = curr_qty
                    pnl = (adj - curr_mean) * closed_qty
                    closed_positions.append(ClosedPosition(
                        ticker=txn.ticker,
                        direction="LONG",
                        open_date=curr_open_date,
                        close_date=txn.trade_date,
                        quantity=closed_qty,
                        open_mean_price=curr_mean,
                        close_price=adj,
                        realized_pnl=pnl.quantize(_QUANTIZE, rounding=ROUND_HALF_UP),
                    ))
                    closes_quantity = closed_qty
                    realized_pnl = pnl.quantize(_QUANTIZE, rounding=ROUND_HALF_UP)
                    new_mean = adj if new_qty < 0 else _ZERO
                    new_open_date = txn.trade_date if new_qty < 0 else None

                positions[txn.ticker] = (new_qty, new_mean, new_open_date)

            steps.setdefault(txn.ticker, []).append(TradeStep(
                trade_date=txn.trade_date,
                side=txn.side,
                quantity=txn.quantity,
                raw_price=txn.raw_price,
                fee_per_unit=fpu,
                adjusted_price=adj,
                qty_after=new_qty,
                mean_price_after=new_mean,
                closes_quantity=closes_quantity,
                realized_pnl=realized_pnl,
            ))

        else:  # corporate action
            ca = event
            curr_qty, curr_mean, curr_open_date = positions.get(ca.ticker, (0, _ZERO, None))

            if curr_qty != 0:
                # Apply ratio using integer arithmetic to avoid rounding issues
                # e.g., 300 shares with 3:1 grouping -> (300 * 1) // 3 = 100
                # Works for both long (positive) and short (negative) positions
                new_qty = (curr_qty * ca.ratio_to) // ca.ratio_from
                if new_qty != 0:
                    # Adjust mean price inversely to preserve total cost basis
                    ratio = Decimal(ca.ratio_to) / Decimal(ca.ratio_from)
                    new_mean = (curr_mean / ratio).quantize(_QUANTIZE, rounding=ROUND_HALF_UP)
                else:
                    new_mean = _ZERO
            else:
                new_qty = 0
                new_mean = _ZERO

            positions[ca.ticker] = (new_qty, new_mean, curr_open_date)

            steps.setdefault(ca.ticker, []).append(TradeStep(
                trade_date=ca.trade_date,
                side=ca.action_type,
                quantity=ca.ratio_to,  # Store ratio_to for display
                raw_price=Decimal(ca.ratio_from),  # Store ratio_from for display
                fee_per_unit=_ZERO,
                adjusted_price=_ZERO,
                qty_after=new_qty,
                mean_price_after=new_mean,
            ))

    computed = {
        ticker: ComputedPosition(ticker=ticker, quantity=qty, mean_price=mean)
        for ticker, (qty, mean, _) in positions.items()
    }
    return computed, steps, closed_positions


def build_txns_with_fees(
    session, as_of_date=None
) -> tuple[list[TxnWithFees], list[CorporateAction]]:
    """Load all transactions + uploads from DB and annotate with fee context.

    Parameters
    ----------
    as_of_date : datetime.date | None
        When set, only transactions with trade_date <= as_of_date are included.

    Returns
    -------
    tuple[list[TxnWithFees], list[CorporateAction]]
        A tuple of (transactions, corporate_actions) for position calculation.
    """
    from sqlmodel import select
    from app.models.db_models import ManualTransaction, Transaction, Upload

    # Load uploads for fee context
    uploads: dict[str, Upload] = {
        u.id: u for u in session.exec(select(Upload)).all()
    }

    # Load imported transactions
    nota_notionals: dict[str, Decimal] = {}
    stmt = select(Transaction)
    if as_of_date is not None:
        stmt = stmt.where(Transaction.trade_date <= as_of_date)
    all_txns = session.exec(stmt).all()
    for t in all_txns:
        nota_notionals[t.upload_id] = (
            nota_notionals.get(t.upload_id, _ZERO)
            + Decimal(t.price) * t.quantity
        )

    result: list[TxnWithFees] = []
    for t in all_txns:
        if t.quantity == 0:
            logger.warning(
                "Imported transaction with quantity=0 in DB: id=%s upload_id=%s ticker=%s side=%s trade_date=%s price=%s",
                t.id, t.upload_id, t.ticker, t.side, t.trade_date, t.price,
            )
        upload = uploads.get(t.upload_id)
        total_fees = _total_non_irrf_fees(upload) if upload else _ZERO
        result.append(TxnWithFees(
            txn_id=t.id,
            upload_id=t.upload_id,
            ticker=t.ticker,
            trade_date=t.trade_date,
            uploaded_at=upload.uploaded_at if upload else datetime.min.replace(tzinfo=UTC),
            side=t.side,
            quantity=t.quantity,
            raw_price=Decimal(t.price),
            total_nota_fees=total_fees,
            nota_notional=nota_notionals.get(t.upload_id, _ZERO),
        ))

    # Load manual transactions
    manual_stmt = select(ManualTransaction)
    if as_of_date is not None:
        manual_stmt = manual_stmt.where(ManualTransaction.trade_date <= as_of_date)
    manual_txns = session.exec(manual_stmt).all()

    corporate_actions: list[CorporateAction] = []

    for mt in manual_txns:
        if mt.transaction_type in ("BUY", "SELL", "BONUS"):
            # These are regular transactions (with self-contained fees)
            total_fees = _total_non_irrf_fees(mt)
            notional = Decimal(mt.price or 0) * (mt.quantity or 0)
            result.append(TxnWithFees(
                txn_id=mt.id,
                upload_id=None,
                ticker=mt.ticker,
                trade_date=mt.trade_date,
                uploaded_at=mt.created_at,
                side=mt.transaction_type,  # BUY, SELL, or BONUS
                quantity=mt.quantity or 0,
                raw_price=Decimal(mt.price or 0),
                total_nota_fees=total_fees,
                nota_notional=notional if notional > 0 else Decimal(1),
            ))
        elif mt.transaction_type in ("GROUPING", "SPLITTING"):
            corporate_actions.append(CorporateAction(
                txn_id=mt.id,
                ticker=mt.ticker,
                trade_date=mt.trade_date,
                created_at=mt.created_at,
                action_type=mt.transaction_type,
                ratio_from=mt.ratio_from or 1,
                ratio_to=mt.ratio_to or 1,
            ))

    return result, corporate_actions
