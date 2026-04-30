from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Upload(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    filename: str
    broker: str = "BTG"
    stored_path: str
    note_number: str | None = Field(default=None, unique=True, index=True)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
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


class Position(SQLModel, table=True):
    ticker: str = Field(primary_key=True)
    quantity: int = Field(default=0)
    mean_price: Decimal = Field(default=Decimal(0))
    manual_mean_price: Decimal | None = Field(default=None)
    manual_quantity: int | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Transaction(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    upload_id: str = Field(index=True)
    ticker: str
    trade_date: date
    side: str
    quantity: int
    price: Decimal
    market_type: str = "SWING"


class ManualTransaction(SQLModel, table=True):
    """Manual transactions entered by user (not from PDF import)."""
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    ticker: str = Field(index=True)
    trade_date: date
    transaction_type: str  # BUY, SELL, GROUPING, SPLITTING, BONUS
    quantity: int | None = Field(default=None)  # For BUY/SELL/BONUS
    price: Decimal | None = Field(default=None)  # For BUY/SELL
    ratio_from: int | None = Field(default=None)  # For GROUPING/SPLITTING
    ratio_to: int | None = Field(default=None)  # For GROUPING/SPLITTING
    # Fee fields (same as Upload)
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
