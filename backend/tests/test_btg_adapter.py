import types

from app.services.parsers.btg_adapter import BTGParserAdapter


def test_btg_adapter_prefers_correpy_result(monkeypatch):
    adapter = BTGParserAdapter()

    def fake_parse(_path):
        return {
            "operations": [
                {
                    "ticker": "PETR4",
                    "side": "C",
                    "quantity": 100,
                    "price": "30,15",
                    "date": "01/04/2026",
                }
            ]
        }

    fake_module = types.SimpleNamespace(parse_brokerage_note=fake_parse)

    def fake_import_module(name):
        if name == "correpy.parsers":
            return fake_module
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("importlib.import_module", fake_import_module)

    result = adapter.parse("dummy.pdf")

    assert len(result) == 1
    assert result[0].ticker == "PETR4"
    assert result[0].side == "BUY"