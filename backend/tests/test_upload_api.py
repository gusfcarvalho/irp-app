import importlib

from fastapi.testclient import TestClient


def _build_test_client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    uploads_path = tmp_path / "uploads"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("UPLOAD_DIR", str(uploads_path))

    import app.db as db_module
    import app.api.upload as upload_module
    import app.main as main_module

    importlib.reload(db_module)
    importlib.reload(upload_module)
    importlib.reload(main_module)

    client = TestClient(main_module.app, raise_server_exceptions=True)
    client.__enter__()
    return client, upload_module


def test_upload_pdf_persists_and_returns_transactions_count(tmp_path, monkeypatch):
    client, upload_module = _build_test_client(tmp_path, monkeypatch)

    def fake_parse(_path: str):
        from app.models.schemas import Trade
        from app.services.parsers.btg_adapter import ParseResult

        return ParseResult(
            note_number="99001",
            trades=[
                Trade(
                    ticker="PETR4",
                    trade_date="2026-04-01",
                    quantity=100,
                    price="30.15",
                    side="BUY",
                )
            ],
        )

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
    client, upload_module = _build_test_client(tmp_path, monkeypatch)

    def fake_parse(_path: str):
        from app.models.schemas import Trade
        from app.services.parsers.btg_adapter import ParseResult

        return ParseResult(
            note_number="99002",
            trades=[
                Trade(
                    ticker="VALE3",
                    trade_date="2026-04-02",
                    quantity=50,
                    price="55.99",
                    side="SELL",
                )
            ],
        )

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
