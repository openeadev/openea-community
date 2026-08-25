from fastapi.testclient import TestClient


def test_landing_page(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "OpenEA Community" in response.text
    assert "OpenEA Community · 1.5.2" in response.text
    assert "/static/css/app.css" in response.text


def test_missing_page_returns_html(client: TestClient) -> None:
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert "Page not found" in response.text


def test_landing_page_exposes_login_and_tabler_branding(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/login"' in response.text
    assert "@tabler/core@1.4.0" in response.text
    assert "/static/img/openea-wordmark.svg" in response.text
    assert "/static/js/theme.js" in response.text


def test_theme_script_uses_browser_local_storage() -> None:
    from pathlib import Path

    script = Path("app/static/js/theme.js").read_text()
    assert 'localStorage.getItem(key)' in script
    assert 'openea-theme' in script
