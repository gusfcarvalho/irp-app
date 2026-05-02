from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class Trade(BaseModel):
    ticker: str
    trade_date: date
    quantity: int
    price: Decimal
    side: str = Field(pattern="^(BUY|SELL)$")
    market_type: str = Field(default="SWING")


class BrokerageNote(BaseModel):
    note_number: str
    broker: str = "BTG"
    trades: list[Trade] = []


class Position(BaseModel):
    ticker: str
    quantity: int
    avg_price: Decimal


class MonthlyReport(BaseModel):
    month: str
    swing_profit_loss: Decimal
    day_trade_profit_loss: Decimal
    fii_profit_loss: Decimal
    tax_due: Decimal


class UploadResponse(BaseModel):
    id: str
    filename: str
    transactions_created: int
    pending_aliases: list[str] = []


class TickerAliasOut(BaseModel):
    raw_name: str
    ticker: str | None
    confirmed: bool
    created_at: str
    updated_at: str


class TickerAliasPatch(BaseModel):
    ticker: str


class TickerAliasCreate(BaseModel):
    raw_name: str
    ticker: str


class TransactionOut(BaseModel):
    id: str
    upload_id: str
    ticker: str
    trade_date: date
    side: str
    quantity: int
    price: Decimal
    market_type: str


class UploadOut(BaseModel):
    id: str
    filename: str
    broker: str
    note_number: str | None
    uploaded_at: str
    settlement_fee: Decimal = Decimal(0)
    registration_fee: Decimal = Decimal(0)
    term_fee: Decimal = Decimal(0)
    ana_fee: Decimal = Decimal(0)
    emoluments: Decimal = Decimal(0)
    operational_fee: Decimal = Decimal(0)
    execution: Decimal = Decimal(0)
    custody_fee: Decimal = Decimal(0)
    taxes: Decimal = Decimal(0)
    irrf: Decimal = Decimal(0)
    other_fees: Decimal = Decimal(0)
    depositary_fee: Decimal = Decimal(0)
    transactions: list[TransactionOut] = []


class ManualTransactionCreate(BaseModel):
    ticker: str
    trade_date: date
    transaction_type: str = Field(pattern="^(BUY|SELL|GROUPING|SPLITTING|BONUS)$")
    quantity: int | None = None  # Required for BUY/SELL/BONUS
    price: Decimal | None = None  # Required for BUY/SELL
    ratio_from: int | None = None  # Required for GROUPING/SPLITTING
    ratio_to: int | None = None  # Required for GROUPING/SPLITTING
    settlement_fee: Decimal = Decimal(0)
    registration_fee: Decimal = Decimal(0)
    term_fee: Decimal = Decimal(0)
    ana_fee: Decimal = Decimal(0)
    emoluments: Decimal = Decimal(0)
    operational_fee: Decimal = Decimal(0)
    execution: Decimal = Decimal(0)
    custody_fee: Decimal = Decimal(0)
    taxes: Decimal = Decimal(0)
    irrf: Decimal = Decimal(0)
    other_fees: Decimal = Decimal(0)
    depositary_fee: Decimal = Decimal(0)


class ManualTransactionOut(BaseModel):
    id: str
    ticker: str
    trade_date: date
    transaction_type: str
    quantity: int | None
    price: Decimal | None
    ratio_from: int | None
    ratio_to: int | None
    settlement_fee: Decimal
    registration_fee: Decimal
    term_fee: Decimal
    ana_fee: Decimal
    emoluments: Decimal
    operational_fee: Decimal
    execution: Decimal
    custody_fee: Decimal
    taxes: Decimal
    irrf: Decimal
    other_fees: Decimal
    depositary_fee: Decimal
    created_at: str


class ClosedPositionTaxOut(BaseModel):
    ticker: str
    asset_type: str         # "STOCK" | "BDR" | "FII"
    direction: str          # "LONG" | "SHORT"
    close_date: date
    quantity: int
    open_mean_price: Decimal
    close_price: Decimal
    realized_pnl: Decimal


class AssetTaxReport(BaseModel):
    asset_type: str
    total_sold_value: Decimal
    profit_loss: Decimal
    accumulated_loss_before: Decimal  # loss carried in from prior months
    accumulated_loss_applied: Decimal  # portion used to offset this month's profit
    accumulated_loss_after: Decimal   # remaining loss to carry forward
    taxable_profit: Decimal           # profit after applying accumulated loss
    irrf_withheld: Decimal
    tax_rate: Decimal
    gross_tax: Decimal
    tax_due: Decimal
    exempt: bool
    closed_positions: list[ClosedPositionTaxOut]


class MonthlyTaxReport(BaseModel):
    month: str              # "YYYY-MM"
    stocks: AssetTaxReport
    bdr: AssetTaxReport
    fii: AssetTaxReport
    total_tax_due: Decimal
    amount_paid: Decimal | None = None   # None = not marked as paid
    payment_diverges: bool = False       # True if amount_paid != total_tax_due


class TaxPaymentOut(BaseModel):
    month: str
    amount_paid: Decimal
    paid_at: str
    notes: str | None


class TaxPaymentUpsert(BaseModel):
    amount_paid: Decimal
    notes: str | None = None
