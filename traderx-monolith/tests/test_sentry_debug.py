"""Regression test for the /sentry-debug endpoint (Sentry issue TRADER-DEMO-APP-8)."""


def test_sentry_debug_does_not_return_500(client):
    """The demo error must be captured, not raised as an unhandled 500."""
    response = client.get("/sentry-debug")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
