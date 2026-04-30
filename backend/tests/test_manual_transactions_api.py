import importlib

from fastapi.testclient import TestClient


def _build_test_client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    uploads_path = tmp_path / "uploads"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("UPLOAD_DIR", str(uploads_path))

    import app.db as db_module
    import app.api.manual_transactions as manual_txns_module
    import app.api.positions as positions_module
    import app.main as main_module

    importlib.reload(db_module)
    importlib.reload(manual_txns_module)
    importlib.reload(positions_module)
    importlib.reload(main_module)

    client = TestClient(main_module.app, raise_server_exceptions=True)
    client.__enter__()
    return client


def test_create_buy_transaction(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/manual-transactions",
        json={
            "ticker": "PETR4",
            "trade_date": "2026-04-01",
            "transaction_type": "BUY",
            "quantity": 100,
            "price": "30.50",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "PETR4"
    assert data["transaction_type"] == "BUY"
    assert data["quantity"] == 100
    assert float(data["price"]) == 30.50


def test_create_sell_transaction(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/manual-transactions",
        json={
            "ticker": "VALE3",
            "trade_date": "2026-04-02",
            "transaction_type": "SELL",
            "quantity": 50,
            "price": "55.00",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "VALE3"
    assert data["transaction_type"] == "SELL"


def test_create_splitting_transaction(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/manual-transactions",
        json={
            "ticker": "ITUB4",
            "trade_date": "2026-04-03",
            "transaction_type": "SPLITTING",
            "ratio_from": 1,
            "ratio_to": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "ITUB4"
    assert data["transaction_type"] == "SPLITTING"
    assert data["ratio_from"] == 1
    assert data["ratio_to"] == 2


def test_create_grouping_transaction(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/manual-transactions",
        json={
            "ticker": "BBDC4",
            "trade_date": "2026-04-04",
            "transaction_type": "GROUPING",
            "ratio_from": 2,
            "ratio_to": 1,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_type"] == "GROUPING"


def test_create_bonus_transaction(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/manual-transactions",
        json={
            "ticker": "WEGE3",
            "trade_date": "2026-04-05",
            "transaction_type": "BONUS",
            "quantity": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_type"] == "BONUS"
    assert data["quantity"] == 10


def test_validation_buy_requires_quantity(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/manual-transactions",
        json={
            "ticker": "PETR4",
            "trade_date": "2026-04-01",
            "transaction_type": "BUY",
            "price": "30.50",
        },
    )

    assert response.status_code == 400
    assert "quantity" in response.json()["detail"]


def test_validation_splitting_requires_ratios(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/manual-transactions",
        json={
            "ticker": "ITUB4",
            "trade_date": "2026-04-03",
            "transaction_type": "SPLITTING",
        },
    )

    assert response.status_code == 400
    assert "ratio_from" in response.json()["detail"]


def test_list_manual_transactions(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    # Create two transactions
    client.post(
        "/api/manual-transactions",
        json={
            "ticker": "PETR4",
            "trade_date": "2026-04-01",
            "transaction_type": "BUY",
            "quantity": 100,
            "price": "30.50",
        },
    )
    client.post(
        "/api/manual-transactions",
        json={
            "ticker": "VALE3",
            "trade_date": "2026-04-02",
            "transaction_type": "SELL",
            "quantity": 50,
            "price": "55.00",
        },
    )

    response = client.get("/api/manual-transactions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_manual_transaction(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    create_response = client.post(
        "/api/manual-transactions",
        json={
            "ticker": "PETR4",
            "trade_date": "2026-04-01",
            "transaction_type": "BUY",
            "quantity": 100,
            "price": "30.50",
        },
    )
    txn_id = create_response.json()["id"]

    response = client.get(f"/api/manual-transactions/{txn_id}")
    assert response.status_code == 200
    assert response.json()["id"] == txn_id


def test_update_manual_transaction(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    create_response = client.post(
        "/api/manual-transactions",
        json={
            "ticker": "PETR4",
            "trade_date": "2026-04-01",
            "transaction_type": "BUY",
            "quantity": 100,
            "price": "30.50",
        },
    )
    txn_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/manual-transactions/{txn_id}",
        json={
            "ticker": "PETR4",
            "trade_date": "2026-04-01",
            "transaction_type": "BUY",
            "quantity": 200,
            "price": "31.00",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["quantity"] == 200
    assert float(update_response.json()["price"]) == 31.00


def test_delete_manual_transaction(tmp_path, monkeypatch):
    client = _build_test_client(tmp_path, monkeypatch)

    create_response = client.post(
        "/api/manual-transactions",
        json={
            "ticker": "PETR4",
            "trade_date": "2026-04-01",
            "transaction_type": "BUY",
            "quantity": 100,
            "price": "30.50",
        },
    )
    txn_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/manual-transactions/{txn_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "deleted"

    # Verify it's gone
    get_response = client.get(f"/api/manual-transactions/{txn_id}")
    assert get_response.status_code == 404
