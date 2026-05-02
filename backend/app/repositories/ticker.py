from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models.db_models import ManualTransaction, TickerAlias, TickerClassification, Transaction


class TickerAliasRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_all(self) -> list[TickerAlias]:
        return list(self._s.exec(
            select(TickerAlias).order_by(TickerAlias.confirmed, TickerAlias.raw_name)
        ).all())

    def get_by_raw_name(self, raw_name: str) -> TickerAlias | None:
        return self._s.get(TickerAlias, raw_name)

    def save(self, alias: TickerAlias) -> None:
        self._s.add(alias)

    def delete(self, alias: TickerAlias) -> None:
        self._s.delete(alias)

    def rename_ticker_in_transactions(self, old: str, new: str) -> None:
        for tx in self._s.exec(select(Transaction).where(Transaction.ticker == old)).all():
            tx.ticker = new
            self._s.add(tx)
        for tx in self._s.exec(select(ManualTransaction).where(ManualTransaction.ticker == old)).all():
            tx.ticker = new
            self._s.add(tx)


class TickerClassificationRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_all(self) -> list[TickerClassification]:
        return list(self._s.exec(
            select(TickerClassification).order_by(TickerClassification.ticker)
        ).all())

    def get_by_ticker(self, ticker: str) -> TickerClassification | None:
        return self._s.get(TickerClassification, ticker)

    def upsert(self, ticker: str, asset_type: str) -> TickerClassification:
        row = self._s.get(TickerClassification, ticker)
        if row is None:
            row = TickerClassification(ticker=ticker, asset_type=asset_type)
        else:
            row.asset_type = asset_type
            row.updated_at = datetime.now(UTC)
        self._s.add(row)
        return row

    def delete(self, row: TickerClassification) -> None:
        self._s.delete(row)
