"""Regression tests: the API is single-tenant and ignores any X-Tenant-ID header."""

STRAY_TENANT_HEADER = {"X-Tenant-ID": "globex_inc"}


def _assert_no_tenant_key(payload):
    if isinstance(payload, dict):
        assert "tenant_id" not in payload
        for value in payload.values():
            _assert_no_tenant_key(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_tenant_key(item)


def test_responses_do_not_contain_tenant_id(client):
    account = client.post("/account/", json={"displayName": "Acct"}).json()
    account_id = account["id"]
    user = client.post("/accountuser/",
                       json={"accountId": account_id, "username": "user01"}).json()
    trade = client.post("/trade/", json={"accountId": account_id, "security": "AAPL",
                                         "side": "Buy", "quantity": 10}).json()

    for payload in (
        account,
        user,
        trade,
        client.get("/account/").json(),
        client.get(f"/account/{account_id}").json(),
        client.get("/accountuser/").json(),
        client.get("/trades/").json(),
        client.get(f"/trades/{account_id}").json(),
        client.get("/positions/").json(),
        client.get(f"/positions/{account_id}").json(),
        client.get("/analytics/trades").json(),
        client.get(f"/analytics/trades/{account_id}").json(),
    ):
        _assert_no_tenant_key(payload)


def test_stray_tenant_header_is_ignored(client):
    created = client.post("/account/", json={"displayName": "Shared"},
                          headers=STRAY_TENANT_HEADER)
    assert created.status_code == 200
    account_id = created.json()["id"]

    assert client.post("/trade/", json={"accountId": account_id, "security": "MSFT",
                                        "side": "Buy", "quantity": 5}).status_code == 200
    assert client.post("/trade/", json={"accountId": account_id, "security": "MSFT",
                                        "side": "Buy", "quantity": 7},
                       headers=STRAY_TENANT_HEADER).status_code == 200

    for path in ("/account/", f"/account/{account_id}", "/accountuser/", "/trades/",
                 f"/trades/{account_id}", "/positions/", f"/positions/{account_id}",
                 "/analytics/trades", f"/analytics/trades/{account_id}"):
        without_header = client.get(path)
        with_header = client.get(path, headers=STRAY_TENANT_HEADER)
        assert without_header.status_code == with_header.status_code == 200, path
        assert without_header.json() == with_header.json(), path

    positions = client.get(f"/positions/{account_id}").json()
    assert [(p["security"], p["quantity"]) for p in positions] == [("MSFT", 12)]
