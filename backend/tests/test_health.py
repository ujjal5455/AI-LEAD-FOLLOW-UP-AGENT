from fastapi.testclient import TestClient


def test_liveness(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_checks_the_database(client: TestClient) -> None:
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_every_response_has_a_request_id_and_security_headers(client: TestClient) -> None:
    response = client.get("/api/health")
    assert len(response.headers["X-Request-ID"]) == 32
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_a_safe_incoming_request_id_is_reused(client: TestClient) -> None:
    response = client.get("/api/health", headers={"X-Request-ID": "trace-123"})
    assert response.headers["X-Request-ID"] == "trace-123"


def test_an_unsafe_incoming_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/api/health", headers={"X-Request-ID": "bad id\nFAKE LOG LINE"})
    assert response.headers["X-Request-ID"] != "bad id\nFAKE LOG LINE"
    assert len(response.headers["X-Request-ID"]) == 32


def test_unexpected_errors_return_a_safe_500(app) -> None:
    @app.get("/api/test-crash")
    def crash() -> None:
        raise RuntimeError("secret internal detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/test-crash")

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Internal server error"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert "secret internal detail" not in response.text
