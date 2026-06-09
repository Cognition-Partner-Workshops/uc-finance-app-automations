"""Tests for analytics endpoints."""
import pytest


def test_get_trade_analytics_empty(client):
    """Test getting trade analytics when no trades exist."""
    resp = client.get("/analytics/trades")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["averageQuantity"] == 0
    assert data["buyCount"] == 0
    assert data["sellCount"] == 0
    assert data["buySellRatio"] == 0
    assert data["tradesByState"] == {}
    assert data["tradesBySecurity"] == {}
    assert data["recentActivity"]["last7Days"] == 0
    assert data["recentActivity"]["last30Days"] == 0


def test_get_trade_analytics_with_data(client):
    """Test getting trade analytics with existing trade data."""
    # First create an account
    account_resp = client.post("/account/", json={"displayName": "Test Account"})
    account_id = account_resp.json()["id"]
    
    # Submit some trades
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100
    })
    
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "MSFT",
        "side": "Sell",
        "quantity": 50
    })
    
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 200
    })
    
    # Get analytics
    resp = client.get("/analytics/trades")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["totalTrades"] == 3
    assert data["averageQuantity"] == 116.67  # (100 + 50 + 200) / 3
    assert data["buyCount"] == 2
    assert data["sellCount"] == 1
    assert data["buySellRatio"] == 2.0
    assert "tradesByState" in data
    assert "tradesBySecurity" in data
    assert "AAPL" in data["tradesBySecurity"]
    assert "MSFT" in data["tradesBySecurity"]
    assert data["recentActivity"]["last7Days"] == 3
    assert data["recentActivity"]["last30Days"] == 3


def test_get_account_trade_analytics_empty(client):
    """Test getting account trade analytics when account has no trades."""
    # Create an account
    account_resp = client.post("/account/", json={"displayName": "Test Account"})
    account_id = account_resp.json()["id"]
    
    # Get analytics for the account
    resp = client.get(f"/analytics/trades/{account_id}")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["accountId"] == account_id
    assert data["totalTrades"] == 0
    assert data["averageQuantity"] == 0
    assert data["buyCount"] == 0
    assert data["sellCount"] == 0
    assert data["tradesByState"] == {}
    assert data["tradesBySecurity"] == {}


def test_get_account_trade_analytics_with_data(client):
    """Test getting account trade analytics with existing trade data."""
    # Create an account
    account_resp = client.post("/account/", json={"displayName": "Test Account"})
    account_id = account_resp.json()["id"]
    
    # Submit trades for the account
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "GOOGL",
        "side": "Buy",
        "quantity": 150
    })
    
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "TSLA",
        "side": "Sell",
        "quantity": 75
    })
    
    # Get analytics for the account
    resp = client.get(f"/analytics/trades/{account_id}")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["accountId"] == account_id
    assert data["totalTrades"] == 2
    assert data["averageQuantity"] == 112.5  # (150 + 75) / 2
    assert data["buyCount"] == 1
    assert data["sellCount"] == 1
    assert "tradesByState" in data
    assert "tradesBySecurity" in data
    assert "GOOGL" in data["tradesBySecurity"]
    assert "TSLA" in data["tradesBySecurity"]


def test_get_account_trade_analytics_nonexistent_account(client):
    """Test getting analytics for a non-existent account."""
    resp = client.get("/analytics/trades/99999")
    assert resp.status_code == 200  # Analytics returns empty stats for non-existent account
    data = resp.json()
    
    assert data["accountId"] == 99999
    assert data["totalTrades"] == 0
    assert data["averageQuantity"] == 0