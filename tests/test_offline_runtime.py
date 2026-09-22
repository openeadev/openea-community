from pathlib import Path

from fastapi.testclient import TestClient

PUBLIC_ASSET_HOSTS = (
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "validator.swagger.io",
    "fastapi.tiangolo.com/img/favicon",
)


def _assert_no_public_asset_hosts(text: str) -> None:
    lowered = text.lower()
    for host in PUBLIC_ASSET_HOSTS:
        assert host not in lowered


def test_public_shell_uses_only_local_browser_assets(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    _assert_no_public_asset_hosts(response.text)
    assert "/static/vendor/tabler/tabler.min.css" in response.text
    assert "/static/vendor/htmx/htmx.min.js" in response.text
    assert "/static/vendor/tabler/tabler.min.js" in response.text
    assert "/static/vendor/lucide/lucide.min.js" in response.text


def test_swagger_ui_uses_local_assets_and_disables_external_validator(
    client: TestClient,
) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    _assert_no_public_asset_hosts(response.text)
    assert "/static/vendor/swagger-ui/swagger-ui-bundle.js" in response.text
    assert "/static/vendor/swagger-ui/swagger-ui.css" in response.text
    assert '"validatorUrl": null' in response.text


def test_redoc_uses_local_assets_without_google_fonts(client: TestClient) -> None:
    response = client.get("/redoc")
    assert response.status_code == 200
    _assert_no_public_asset_hosts(response.text)
    assert "/static/vendor/redoc/redoc.standalone.js" in response.text


def test_security_policy_does_not_allow_public_asset_hosts(client: TestClient) -> None:
    response = client.get("/")
    csp = response.headers["Content-Security-Policy"]
    _assert_no_public_asset_hosts(csp)
    assert "style-src 'self'" in csp
    assert "script-src 'self'" in csp

    docs_response = client.get("/docs")
    docs_csp = docs_response.headers["Content-Security-Policy"]
    _assert_no_public_asset_hosts(docs_csp)
    assert "style-src 'self' 'unsafe-inline'" in docs_csp
    assert "script-src 'self' 'unsafe-inline'" in docs_csp


def test_impact_graph_template_uses_local_cytoscape_asset() -> None:
    template = Path("app/templates/impact/index.html").read_text()
    _assert_no_public_asset_hosts(template)
    assert "/vendor/cytoscape/cytoscape.min.js" in template


def test_runtime_templates_do_not_reference_public_asset_hosts() -> None:
    for path in Path("app/templates").rglob("*.html"):
        _assert_no_public_asset_hosts(path.read_text())


def test_docker_build_vendors_frontend_assets_and_compose_reuses_image() -> None:
    dockerfile = Path("Dockerfile").read_text()
    compose = Path("docker-compose.yml").read_text()

    assert "RUN python scripts/vendor_frontend_assets.py" in dockerfile
    assert "chmod -R a+rX app/static/vendor" in dockerfile
    assert "image: ${OPENEA_IMAGE:-openea-community:1.5.2}" in compose
    assert compose.count("image: ${OPENEA_IMAGE:-openea-community:1.5.2}") == 2
    assert compose.count("build: .") == 1


def test_vendor_downloader_makes_assets_runtime_readable() -> None:
    source = Path("scripts/vendor_frontend_assets.py").read_text()
    assert "destination.chmod(0o644)" in source
    assert 'with path.open("rb") as handle:' in source
