# Example: Workflow Tests

These examples are based on the real tests in `traderx-monolith/tests/test_trade_submit.py`. Workflow tests exercise multi-step business processes where one operation depends on another.

## Trade submission (depends on account)

```python
def test_submitTrade(client):
    # create an account first
    acct = client.post("/account/", json={'displayName': 'Trading Account'})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body['success'] is True
    assert body["trade"]["state"] in ("New", "Settled")
    assert body["trade"]['quantity'] == 100
```

**Pattern:**
1. Set up prerequisite data (create an account)
2. Perform the main action (submit a trade)
3. Assert the full response structure (success flag, nested trade object, state)

## Full lifecycle: create → trade → check position

```python
def test_trade_creates_position(client):
    """Verify that submitting a trade creates or updates a position."""
    # Step 1: Create account
    acct = client.post("/account/", json={"displayName": "Position Test"})
    account_id = acct.json()["id"]

    # Step 2: Submit a buy trade
    trade_resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": "MSFT",
        "side": "Buy",
        "quantity": 50,
    })
    assert trade_resp.status_code == 200
    assert trade_resp.json()["success"] is True

    # Step 3: Check positions for this account
    pos_resp = client.get(f"/positions/{account_id}")
    assert pos_resp.status_code == 200
    positions = pos_resp.json()
    # Should have at least one position for MSFT
    msft_positions = [p for p in positions if p["security"] == "MSFT"]
    assert len(msft_positions) >= 1
```

**Pattern:**
1. Set up prerequisite chain (account → trade)
2. Query a downstream resource (positions)
3. Assert the side effects are correct

## Tips for workflow tests

- **Always create prerequisites in the test** — don't rely on seed data (the test DB starts empty)
- **Assert intermediate steps** — check the account was created before submitting a trade
- **Use descriptive test names** — `test_trade_creates_position` is better than `test_trade_2`
- **Test both positive and negative paths** — verify that invalid trades are rejected
