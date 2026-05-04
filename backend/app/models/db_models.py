from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel


class FeeFields(SQLModel):
    """Mixin for the 12 standard brokerage fee columns."""
    settlement_fee: Decimal = Field(default=Decimal(0))
    registration_fee: Decimal = Field(default=Decimal(0))
    term_fee: Decimal = Field(default=Decimal(0))
    ana_fee: Decimal = Field(default=Decimal(0))
    emoluments: Decimal = Field(default=Decimal(0))
    operational_fee: Decimal = Field(default=Decimal(0))
    execution: Decimal = Field(default=Decimal(0))
    custody_fee: Decimal = Field(default=Decimal(0))
    taxes: Decimal = Field(default=Decimal(0))
    irrf: Decimal = Field(default=Decimal(0))
    other_fees: Decimal = Field(default=Decimal(0))
    depositary_fee: Decimal = Field(default=Decimal(0))


class Quote(SQLModel, table=True):
    """End-of-day close price for a ticker, fetched from Yahoo Finance."""
    ticker: str = Field(primary_key=True)
    quote_date: date = Field(primary_key=True)
    close_price: Decimal
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TaxCalculationCache(SQLModel, table=True):
    """Cached result of a monthly tax calculation, serialised as JSON."""
    month: str = Field(primary_key=True)  # "YYYY-MM"
    report_json: str = Field(sa_column=Column(sa.Text, nullable=False))
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TaxPayment(SQLModel, table=True):
    """Records that the user actually paid DARF for a given month."""
    month: str = Field(primary_key=True)  # "YYYY-MM"
    amount_paid: Decimal
    paid_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = Field(default=None)


class TickerClassification(SQLModel, table=True):
    """User-supplied asset-type override for a ticker."""
    ticker: str = Field(primary_key=True)
    asset_type: str  # STOCK | FII | BDR | ETF_RV | ETF_RF | SUBSCRICAO | RF_POS | RF_PRE
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TickerAlias(SQLModel, table=True):
    """Maps raw descriptions (e.g. 'AMBEV S/A ON') or old tickers to current B3 tickers."""
    raw_name: str = Field(primary_key=True)   # normalized: " ".join(s.split()).upper()
    ticker: str | None = Field(default=None)
    confirmed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Upload(FeeFields, SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    filename: str
    broker: str = "BTG"
    stored_path: str
    note_number: str | None = Field(default=None, unique=True, index=True)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Position(SQLModel, table=True):
    ticker: str = Field(primary_key=True)
    quantity: Decimal = Field(default=Decimal(0))
    mean_price: Decimal = Field(default=Decimal(0))
    manual_mean_price: Decimal | None = Field(default=None)
    manual_quantity: Decimal | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Transaction(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    upload_id: str = Field(index=True)
    ticker: str
    trade_date: date
    side: str
    quantity: Decimal
    price: Decimal
    market_type: str = "SWING"
    source: str = "NOTA"          # NOTA | B3_POSICAO | B3_MOVIMENTACAO
    needs_review: bool = False    # True for B3 posição imports (price/date unconfirmed)


class ManualTransaction(FeeFields, SQLModel, table=True):
    """Manual transactions entered by user (not from PDF import)."""
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    ticker: str = Field(index=True)
    trade_date: date
    transaction_type: str  # BUY, SELL, GROUPING, SPLITTING, BONUS
    quantity: Decimal | None = Field(default=None)  # For BUY/SELL/BONUS
    price: Decimal | None = Field(default=None)  # For BUY/SELL
    ratio_from: int | None = Field(default=None)  # For GROUPING/SPLITTING
    ratio_to: int | None = Field(default=None)  # For GROUPING/SPLITTING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
