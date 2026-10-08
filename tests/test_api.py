"""Tests for FastAPI backend routes."""

from fastapi.testclient import TestClient

from scanner.api.main import app

client = TestClient(app)


def test_api_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["live_trading_enabled"] is False  # Must strictly be False
    assert data["market"] == "NSE"


def test_api_stocks_list():
    res = client.get("/api/stocks?universe=NIFTY_50")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 50
    assert any(s["symbol"] == "RELIANCE" for s in data)


def test_api_paper_trading_lifecycle():
    # 1. Fetch initial portfolio
    res = client.get("/api/paper/portfolio")
    assert res.status_code == 200
    init_data = res.json()
    init_cash = init_data["cash_balance"]

    # 2. Open paper position
    order_payload = {
        "symbol": "TCS",
        "entry_price": 3500.0,
        "quantity": 5,
        "stop_loss": 3400.0,
        "target1": 3750.0,
        "target2": 3900.0,
        "strategy": "TREND_PULLBACK_V1",
        "score": 85,
    }
    res = client.post("/api/paper/order", json=order_payload)
    assert res.status_code == 200
    order_data = res.json()
    assert order_data["status"] == "SUCCESS"
    pos_id = order_data["position"]["id"]

    # 3. Check portfolio has open position
    res = client.get("/api/paper/portfolio")
    port = res.json()
    assert any(p["id"] == pos_id for p in port["open_positions"])
    assert port["cash_balance"] < init_cash

    # 4. Close paper position at profit
    close_payload = {
        "position_id": pos_id,
        "exit_price": 3750.0,
        "exit_reason": "TARGET",
    }
    res = client.post("/api/paper/close", json=close_payload)
    assert res.status_code == 200
    close_data = res.json()
    assert close_data["status"] == "SUCCESS"
    assert close_data["closed_trade"]["net_pnl"] > 0
