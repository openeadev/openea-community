"""Live Playwright coverage for the OpenEA Community 1.0 critical workflows.

Run against a deployed OpenEA instance with an Architect account:
OPENEA_E2E_BASE_URL=http://localhost:8000 OPENEA_E2E_USERNAME=architect OPENEA_E2E_PASSWORD=... pytest tests/e2e -q
"""
import os

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Page  # noqa: E402

BASE_URL = os.getenv("OPENEA_E2E_BASE_URL")
USERNAME = os.getenv("OPENEA_E2E_USERNAME")
PASSWORD = os.getenv("OPENEA_E2E_PASSWORD")
pytestmark = pytest.mark.skipif(
    not (BASE_URL and USERNAME and PASSWORD), reason="Live OpenEA E2E credentials not configured"
)


def login(page: Page) -> None:
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("Username").fill(USERNAME)
    page.get_by_label("Password").fill(PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url(f"{BASE_URL}/dashboard")


def test_repository_relationship_search_and_impact(page: Page) -> None:
    login(page)
    app_response = page.request.post(
        f"{BASE_URL}/api/v1/objects",
        data={"object_type_key": "application", "name": "Playwright MVP Application", "record_status": "Active", "properties": {}},
    )
    assert app_response.ok
    app = app_response.json()
    cap_response = page.request.post(
        f"{BASE_URL}/api/v1/objects",
        data={"object_type_key": "business_capability", "name": "Playwright MVP Capability", "record_status": "Active", "properties": {}},
    )
    assert cap_response.ok
    capability = cap_response.json()
    relationship = page.request.post(
        f"{BASE_URL}/api/v1/relationships",
        data={"relationship_key": "supports", "source_object_id": app["id"], "target_object_id": capability["id"]},
    )
    assert relationship.ok

    page.goto(f"{BASE_URL}/explore?q=Playwright+MVP+Application")
    assert page.get_by_text("Playwright MVP Application").is_visible()
    page.goto(f"{BASE_URL}/impact/{app['id']}")
    assert page.get_by_text("Playwright MVP Capability").is_visible()


def test_decision_submit_and_approve(page: Page) -> None:
    login(page)
    response = page.request.post(
        f"{BASE_URL}/api/v1/objects",
        data={
            "object_type_key": "architecture_decision",
            "name": "Playwright Architecture Decision",
            "record_status": "Active",
            "properties": {"context": "E2E decision context", "decision": "Use the E2E option."},
        },
    )
    assert response.ok
    decision = response.json()
    page.goto(f"{BASE_URL}/explore/{decision['id']}?tab=lifecycle")
    page.locator('select[name="status"]').select_option(label="Proposed")
    page.get_by_role("button", name="Apply").click()
    page.locator('select[name="status"]').select_option(label="Accepted")
    page.get_by_role("button", name="Apply").click()
    assert page.get_by_text("Accepted", exact=True).is_visible()


def test_csv_import_and_api_docs(page: Page) -> None:
    login(page)
    page.goto(f"{BASE_URL}/imports")
    page.get_by_label("Object type").select_option("application")
    page.get_by_label("CSV file").set_input_files(
        {"name": "e2e.csv", "mimeType": "text/csv", "buffer": b"name,record_status\nPlaywright Imported Application,Active\n"}
    )
    page.get_by_role("button", name="Upload").click()
    page.locator('select[name="map::name"]').select_option("name")
    page.locator('select[name="map::record_status"]').select_option("record_status")
    page.get_by_role("button", name="Validate and preview").click()
    assert page.get_by_text("Playwright Imported Application").is_visible()
    page.get_by_role("button", name="Commit import").click()
    assert page.get_by_text("Import committed successfully").is_visible()

    page.goto(f"{BASE_URL}/docs")
    assert page.locator("body").contains_text("OpenEA Community")
