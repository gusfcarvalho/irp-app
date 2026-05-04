from sqlmodel import Session, select

from app.models.db_models import Transaction, Upload


class UploadRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_all(self) -> list[Upload]:
        return list(self._s.exec(select(Upload).order_by(Upload.uploaded_at.desc())).all())

    def get_by_note_number(self, note_number: str) -> Upload | None:
        return self._s.exec(
            select(Upload).where(Upload.note_number == note_number)
        ).first()

    def get_all_transactions(self) -> list[Transaction]:
        return list(
            self._s.exec(select(Transaction).order_by(Transaction.trade_date.desc())).all()
        )

    def get_transactions_grouped(self) -> dict[str, list[Transaction]]:
        result: dict[str, list[Transaction]] = {}
        for tx in self._s.exec(select(Transaction)).all():
            result.setdefault(tx.upload_id, []).append(tx)
        return result

    def add_upload(self, upload: Upload) -> None:
        self._s.add(upload)

    def add_transaction(self, tx: Transaction) -> None:
        self._s.add(tx)
