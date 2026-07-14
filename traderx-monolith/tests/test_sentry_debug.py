"""Regression tests for the /sentry-debug endpoint.

Covers Sentry issue TRADER-DEMO-APP-1 (ZeroDivisionError: division by zero),
where the endpoint hard-coded ``1 / 0`` and returned an uncaught HTTP 500 on
every request.
"""


def test_sentry_debug_default_does_not_raise(client):
    """Regression: default request must no longer 500 (was ZeroDivisionError)."""
    resp = client.get("/sentry-debug")
    assert resp.status_code == 200
    assert resp.json() == {"result": 100}


def test_sentry_debug_custom_divisor(client):
    resp = client.get("/sentry-debug", params={"divisor": 4})
    assert resp.status_code == 200
    assert resp.json() == {"result": 25}
