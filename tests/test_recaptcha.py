import re

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import PLATFORM_ADMIN
from app.core.config import get_settings
from app.models.governance import AuditEvent
from app.repositories.user_repository import UserRepository
from app.services.application_setting_service import ApplicationSettingService
from app.services.auth_service import AuthenticationService
from app.services.recaptcha_service import (
    RecaptchaService,
    RecaptchaVerificationResult,
    RecaptchaVerificationUnavailable,
)


def csrf_from(response_text: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', response_text)
    assert match
    return match.group(1)


def create_admin(db: Session) -> None:
    AuthenticationService(db).create_user(
        "admin", "OpenEA Administrator", "ValidPassword123!", {PLATFORM_ADMIN}
    )


def login_without_recaptcha(client: TestClient) -> None:
    page = client.get("/login")
    token = csrf_from(page.text)
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "ValidPassword123!",
            "csrf_token": token,
            "next": "/dashboard",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def configure_test_keys(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "recaptcha_site_key", "test-site-key")
    monkeypatch.setattr(settings, "recaptcha_secret_key", "test-secret-key")


def enable_recaptcha(db: Session, monkeypatch) -> None:
    configure_test_keys(monkeypatch)
    admin = UserRepository(db).get_by_username("admin")
    assert admin is not None
    ApplicationSettingService(db).set_recaptcha_enabled(True, actor=admin)


def test_recaptcha_is_disabled_by_default_and_login_remains_offline_capable(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    response = client.get("/login")
    assert response.status_code == 200
    assert "www.google.com/recaptcha" not in response.text
    assert "openea-recaptcha" not in response.text
    assert "www.google.com/recaptcha" not in response.headers["Content-Security-Policy"]


def test_platform_admin_cannot_enable_recaptcha_without_both_environment_keys(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    login_without_recaptcha(client)
    page = client.get("/admin/settings/security")
    assert page.status_code == 200
    assert "Not configured" in page.text
    token = csrf_from(page.text)

    response = client.post(
        "/admin/settings/security",
        data={"csrf_token": token, "recaptcha_enabled": "1"},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "cannot be enabled" in response.text
    assert not ApplicationSettingService(db).recaptcha_enabled()


def test_platform_admin_can_enable_recaptcha_when_keys_are_configured(
    client: TestClient, db: Session, monkeypatch
) -> None:
    create_admin(db)
    configure_test_keys(monkeypatch)
    login_without_recaptcha(client)

    page = client.get("/admin/settings/security")
    token = csrf_from(page.text)
    response = client.post(
        "/admin/settings/security",
        data={"csrf_token": token, "recaptcha_enabled": "1"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/settings/security?updated=1"
    assert ApplicationSettingService(db).recaptcha_enabled()

    audit = db.scalar(
        select(AuditEvent)
        .where(AuditEvent.action == "ApplicationSettingUpdated")
        .order_by(AuditEvent.timestamp.desc())
    )
    assert audit is not None
    assert audit.entity_id == "login_recaptcha_enabled"
    assert audit.after_state == {"enabled": True}


def test_enabled_login_renders_checkbox_script_and_recaptcha_csp(
    client: TestClient, db: Session, monkeypatch
) -> None:
    create_admin(db)
    enable_recaptcha(db, monkeypatch)

    response = client.get("/login")
    assert response.status_code == 200
    assert 'id="openea-recaptcha"' in response.text
    assert 'data-sitekey="test-site-key"' in response.text
    assert "/static/js/recaptcha-login.js" in response.text
    assert "https://www.google.com/recaptcha/api.js" in response.text
    csp = response.headers["Content-Security-Policy"]
    assert "https://www.google.com/recaptcha/" in csp
    assert "https://www.gstatic.com/recaptcha/" in csp
    assert "frame-src" in csp

    public_response = client.get("/")
    assert "www.google.com/recaptcha" not in public_response.headers["Content-Security-Policy"]


def test_missing_recaptcha_response_blocks_password_authentication(
    client: TestClient, db: Session, monkeypatch
) -> None:
    create_admin(db)
    enable_recaptcha(db, monkeypatch)
    page = client.get("/login")
    token = csrf_from(page.text)

    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "wrong-password",
            "csrf_token": token,
            "next": "/dashboard",
        },
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "Please complete the security challenge" in response.text

    db.expire_all()
    admin = UserRepository(db).get_by_username("admin")
    assert admin is not None
    assert admin.failed_login_count == 0


def test_successful_recaptcha_allows_normal_login(
    client: TestClient, db: Session, monkeypatch
) -> None:
    create_admin(db)
    enable_recaptcha(db, monkeypatch)
    monkeypatch.setattr(
        RecaptchaService,
        "verify",
        lambda self, token: RecaptchaVerificationResult(success=token == "good-token"),
    )
    page = client.get("/login")
    token = csrf_from(page.text)

    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "ValidPassword123!",
            "csrf_token": token,
            "next": "/dashboard",
            "g-recaptcha-response": "good-token",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


def test_failed_recaptcha_does_not_test_password(
    client: TestClient, db: Session, monkeypatch
) -> None:
    create_admin(db)
    enable_recaptcha(db, monkeypatch)
    monkeypatch.setattr(
        RecaptchaService,
        "verify",
        lambda self, token: RecaptchaVerificationResult(
            success=False, error_codes=("invalid-input-response",)
        ),
    )
    page = client.get("/login")
    token = csrf_from(page.text)
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "wrong-password",
            "csrf_token": token,
            "g-recaptcha-response": "bad-token",
        },
    )
    assert response.status_code == 400
    assert "Security challenge verification failed" in response.text

    db.expire_all()
    admin = UserRepository(db).get_by_username("admin")
    assert admin is not None
    assert admin.failed_login_count == 0


def test_recaptcha_verification_outage_fails_closed(
    client: TestClient, db: Session, monkeypatch
) -> None:
    create_admin(db)
    enable_recaptcha(db, monkeypatch)

    def unavailable(self, token):
        raise RecaptchaVerificationUnavailable("test outage")

    monkeypatch.setattr(RecaptchaService, "verify", unavailable)
    page = client.get("/login")
    token = csrf_from(page.text)
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "ValidPassword123!",
            "csrf_token": token,
            "g-recaptcha-response": "token",
        },
    )
    assert response.status_code == 503
    assert "could not verify the security challenge" in response.text


def test_enabled_recaptcha_with_removed_keys_blocks_login_without_exposing_secret(
    client: TestClient, db: Session, monkeypatch
) -> None:
    create_admin(db)
    enable_recaptcha(db, monkeypatch)
    settings = get_settings()
    monkeypatch.setattr(settings, "recaptcha_site_key", "")
    monkeypatch.setattr(settings, "recaptcha_secret_key", "")

    response = client.get("/login")
    assert response.status_code == 503
    assert "Login security is temporarily unavailable" in response.text
    assert "www.google.com/recaptcha/api.js" not in response.text
    assert "<button class=\"btn btn-primary btn-lg mt-2\" type=\"submit\" disabled" in response.text


def test_platform_admin_can_disable_recaptcha(client: TestClient, db: Session, monkeypatch) -> None:
    create_admin(db)
    configure_test_keys(monkeypatch)
    login_without_recaptcha(client)
    admin = UserRepository(db).get_by_username("admin")
    assert admin is not None
    ApplicationSettingService(db).set_recaptcha_enabled(True, actor=admin)

    page = client.get("/admin/settings/security")
    token = csrf_from(page.text)
    response = client.post(
        "/admin/settings/security",
        data={"csrf_token": token},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert not ApplicationSettingService(db).recaptcha_enabled()
