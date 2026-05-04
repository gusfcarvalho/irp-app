from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models.db_models import Position


class PositionRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_all(self) -> list[Position]:
        return list(self._s.exec(select(Position)).all())

    def get_by_ticker(self, ticker: str) -> Position | None:
        return self._s.get(Position, ticker)

    def upsert_computed(self, ticker: str, quantity, mean_price) -> Position:
        pos = self._s.get(Position, ticker) or Position(ticker=ticker)
        pos.quantity = quantity
        pos.mean_price = mean_price
        pos.updated_at = datetime.now(UTC)
        self._s.add(pos)
        return pos

    def save(self, pos: Position) -> None:
        self._s.add(pos)
