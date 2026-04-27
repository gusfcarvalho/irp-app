from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine

from app.main import app
from app.models.schemas import Trade


def _build_test_client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    test_engine = create_engine(f"sqlite:///{db_path}")

    import app.db as db_module
    import app.api.upload as upload_module

    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(upload_module, "engine", test_engine)
    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path / "uploads")

    SQLModel.metadata.create_all(test_engine)

    client = TestClient(app)
    return client


def test_upload_pdf_persists_and_returns_transactions_count(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    def fake_parse(_path: str):
        return [
            Trade(
                ticker="PETR4",
                trade_date="2026-04-01",
                quantity=100,
                price="30.15",
                side="BUY",
            )
        ]

    import app.api.upload as upload_module

    monkeypatch.setattr(upload_module.parser, "parse", fake_parse)

    response = client.post(
        "/api/upload",
        files={"file": ("nota.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "nota.pdf"
    assert payload["transactions_created"] == 1

    saved_files = list((tmp_path / "uploads").glob("*.pdf"))
    assert len(saved_files) == 1


def test_list_transactions_returns_imported_rows(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    def fake_parse(_path: str):
        return [
            Trade(
                ticker="VALE3",
                trade_date="2026-04-02",
                quantity=50,
                price="55.99",
                side="SELL",
            )
        ]

    import app.api.upload as upload_module

    monkeypatch.setattr(upload_module.parser, "parse", fake_parse)

    upload_response = client.post(
        "/api/upload",
        files={"file": ("nota.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert upload_response.status_code == 200

    response = client.get("/api/transactions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "VALE3"
    assert data[0]["side"] == "SELL"
