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


class TransactionOut(BaseModel):
    id: str
    upload_id: str
    ticker: str
    trade_date: date
    side: str
    quantity: int
    price: Decimal
    market_type: str
