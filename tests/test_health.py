from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.5.2"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers.get("x-request-id")


def test_ready_when_database_available(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("app.api.health.check_database_ready", lambda: None)
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_ready_when_database_unavailable(client: TestClient, monkeypatch) -> None:
    from sqlalchemy.exc import OperationalError

    def fail() -> None:
        raise OperationalError("SELECT 1", {}, Exception("database unavailable"))

    monkeypatch.setattr("app.api.health.check_database_ready", fail)
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
