from datetime import date

from sqlmodel import Session

from app.services.position_engine import (
    ClosedPosition,
    ComputedPosition,
    TradeStep,
    build_txns_with_fees,
    compute_positions,
    compute_positions_with_steps,
)


class PositionService:
    """Encapsulates the build-then-compute pipeline so routes stay thin."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def compute(self, as_of_date: date | None = None) -> dict[str, ComputedPosition]:
        txns, corp_actions = build_txns_with_fees(self._session, as_of_date=as_of_date)
        return compute_positions(txns, corp_actions)

    def compute_with_steps(
        self, as_of_date: date | None = None
    ) -> tuple[
        dict[str, ComputedPosition],
        dict[str, list[TradeStep]],
        list[ClosedPosition],
    ]:
        txns, corp_actions = build_txns_with_fees(self._session, as_of_date=as_of_date)
        return compute_positions_with_steps(txns, corp_actions)
