"""Regression test for Sentry issue TRADER-DEMO-APP-1 (ZeroDivisionError on /sentry-debug)."""


def test_sentry_debug_does_not_raise_500(client):
    response = client.get("/sentry-debug")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error captured"
    assert "division by zero" in body["error"]
