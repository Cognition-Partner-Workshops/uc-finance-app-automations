"""Regression test for the /sentry-debug endpoint (Sentry issue TRADER-DEMO-APP-9)."""


def test_sentry_debug_does_not_return_500(client):
    """The demo ZeroDivisionError must be captured, not surfaced as an HTTP 500."""
    response = client.get("/sentry-debug")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error captured"
    assert "division by zero" in body["error"]
