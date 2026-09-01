from fastapi.testclient import TestClient

from app.main import create_app


def _app_with_failure_routes():
    app = create_app()

    @app.get("/_test/unhandled")
    async def unhandled_failure():
        raise RuntimeError("sensitive database detail")

    @app.get("/api/_test/unhandled")
    async def api_unhandled_failure():
        raise RuntimeError("sensitive API detail")

    return app


def test_unhandled_web_error_returns_branded_safe_page() -> None:
    with TestClient(_app_with_failure_routes(), raise_server_exceptions=False) as client:
        response = client.get("/_test/unhandled")

    assert response.status_code == 500
    assert "We couldn't complete that request." in response.text
    assert "Request ID" in response.text
    assert "sensitive database detail" not in response.text
    assert response.headers.get("X-Request-ID")


def test_unhandled_api_error_returns_safe_json_with_request_id() -> None:
    with TestClient(_app_with_failure_routes(), raise_server_exceptions=False) as client:
        response = client.get("/api/_test/unhandled")

    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"] == "OpenEA encountered an unexpected error."
    assert payload["request_id"]
    assert "sensitive API detail" not in response.text
