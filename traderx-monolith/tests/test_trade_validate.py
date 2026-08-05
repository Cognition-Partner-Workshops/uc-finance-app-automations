"""Integration tests for trade order validation."""


def create_account(client, tenant="acme_corp"):
    response = client.post(
        "/account/",
        json={"displayName": "Validation Account"},
        headers={"X-Tenant-ID": tenant},
    )
    assert response.status_code == 200
    return response.json()["id"]


def validation_payload(account_id, **overrides):
    payload = {
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    }
    payload.update(overrides)
    return payload


def test_validate_trade_happy_path_does_not_create_records(client):
    account_id = create_account(client)

    response = client.post(
        "/trade/validate",
        json=validation_payload(account_id, price=125.50),
    )

    assert response.status_code == 200
    assert response.json() == {"valid": True, "errors": [], "warnings": []}
    assert client.get("/trades/").json() == []
    assert client.get("/positions/").json() == []


def test_validate_trade_unknown_security(client):
    account_id = create_account(client)

    response = client.post(
        "/trade/validate",
        json=validation_payload(account_id, security="NOT_A_SECURITY"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any("not found" in error for error in body["errors"])


def test_validate_trade_missing_account(client):
    response = client.post(
        "/trade/validate",
        json=validation_payload(9999),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any("Account 9999 not found" in error for error in body["errors"])


def test_validate_trade_invalid_side(client):
    account_id = create_account(client)

    response = client.post(
        "/trade/validate",
        json=validation_payload(account_id, side="Hold"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any("Invalid trade side" in error for error in body["errors"])


def test_validate_trade_quantity_out_of_range(client):
    account_id = create_account(client)

    for quantity in (0, 1_000_001):
        response = client.post(
            "/trade/validate",
            json=validation_payload(account_id, quantity=quantity),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert any(
            "Invalid trade quantity" in error for error in body["errors"]
        )


def test_validate_trade_invalid_price(client):
    account_id = create_account(client)

    for price in (-1, 0):
        response = client.post(
            "/trade/validate",
            json=validation_payload(account_id, price=price),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert any("Invalid trade price" in error for error in body["errors"])


def test_validate_trade_enforces_tenant_isolation(client):
    account_id = create_account(client, tenant="acme_corp")

    response = client.post(
        "/trade/validate",
        headers={"X-Tenant-ID": "globex_inc"},
        json=validation_payload(account_id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any("not found for tenant globex_inc" in error
               for error in body["errors"])


def test_validate_trade_sell_exceeds_position_warning(client):
    account_id = create_account(client)
    buy_response = client.post(
        "/trade/",
        json=validation_payload(account_id, quantity=10),
    )
    assert buy_response.status_code == 200

    response = client.post(
        "/trade/validate",
        json=validation_payload(account_id, side="Sell", quantity=25),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["errors"] == []
    assert len(body["warnings"]) == 1
    assert "exceeds current position 10" in body["warnings"][0]


def test_validate_trade_missing_required_field(client):
    response = client.post(
        "/trade/validate",
        json={
            "accountId": 1,
            "security": "AAPL",
            "side": "Buy",
        },
    )

    assert response.status_code == 422
