from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Upload(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    filename: str
    broker: str = "BTG"
    stored_path: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Transaction(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    upload_id: str = Field(index=True)
    ticker: str
    trade_date: date
    side: str
    quantity: int
    price: Decimal
    market_type: str = "SWING"
