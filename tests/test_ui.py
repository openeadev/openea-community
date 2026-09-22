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
    assert "/static/vendor/tabler/tabler.min.css" in response.text
    assert "/static/vendor/tabler/tabler.min.js" in response.text
    assert "/static/vendor/htmx/htmx.min.js" in response.text
    assert "/static/vendor/lucide/lucide.min.js" in response.text
    assert "/static/img/openea-wordmark.svg" in response.text
    assert "/static/img/openea-wordmark-dark.svg" in response.text
    assert "/static/js/theme.js" in response.text


def test_theme_script_uses_browser_local_storage() -> None:
    from pathlib import Path

    script = Path("app/static/js/theme.js").read_text()
    assert 'localStorage.getItem(key)' in script
    assert 'openea-theme' in script


def test_wordmark_has_theme_specific_assets() -> None:
    from pathlib import Path

    css = Path("app/static/css/app.css").read_text()
    dark_wordmark = Path("app/static/img/openea-wordmark-dark.svg").read_text()

    assert '.openea-wordmark-dark { display: none; }' in css
    assert '[data-bs-theme="dark"] .openea-wordmark-light { display: none; }' in css
    assert '[data-bs-theme="dark"] .openea-wordmark-dark { display: block; }' in css
    assert 'filter: brightness(0) invert(1)' not in css
    assert 'fill="#f8fafc">Open' in dark_wordmark
    assert '<tspan fill="#206bc4">EA</tspan>' in dark_wordmark
