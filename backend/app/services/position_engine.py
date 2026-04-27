from decimal import Decimal

from app.models.schemas import Position, Trade


def apply_trade(position: Position | None, trade: Trade) -> Position:
    if position is None:
        position = Position(ticker=trade.ticker, quantity=0, avg_price=Decimal("0"))

    if trade.side == "BUY":
        total_cost = (position.avg_price * position.quantity) + (trade.price * trade.quantity)
        new_qty = position.quantity + trade.quantity
        new_avg = total_cost / new_qty if new_qty else Decimal("0")
        return Position(ticker=trade.ticker, quantity=new_qty, avg_price=new_avg)

    new_qty = position.quantity - trade.quantity
    return Position(ticker=trade.ticker, quantity=new_qty, avg_price=position.avg_price)
