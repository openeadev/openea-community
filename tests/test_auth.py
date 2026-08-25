import re
from contextlib import suppress

from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.permissions import PLATFORM_ADMIN, VIEWER
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthenticationError, AuthenticationService


def csrf_from(response_text: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', response_text)
    assert match
    return match.group(1)


def create_user(db: Session, username: str, role: str, password: str = "ValidPassword123!"):
    return AuthenticationService(db).create_user(username, username.title(), password, {role})


def login(client: TestClient, username: str, password: str = "ValidPassword123!") -> None:
    page = client.get("/login")
    token = csrf_from(page.text)
    response = client.post(
        "/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": token,
            "next": "/dashboard",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_initial_setup_creates_platform_admin(client: TestClient, db: Session) -> None:
    page = client.get("/setup")
    assert page.status_code == 200
    token = csrf_from(page.text)
    response = client.post(
        "/setup",
        data={
            "username": "admin",
            "display_name": "OpenEA Administrator",
            "password": "InitialPassword123!",
            "password_confirm": "InitialPassword123!",
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"

    user = UserRepository(db).get_by_username("admin")
    assert user is not None
    assert {role.name for role in user.roles} == {PLATFORM_ADMIN}
    assert user.password_hash.startswith("$argon2id$")
    assert PasswordHasher().verify(user.password_hash, "InitialPassword123!")


def test_setup_cannot_run_after_user_exists(client: TestClient, db: Session) -> None:
    create_user(db, "admin", PLATFORM_ADMIN)
    response = client.get("/setup", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_protected_page_redirects_unauthenticated_user(client: TestClient, db: Session) -> None:
    create_user(db, "admin", PLATFORM_ADMIN)
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=/dashboard"


def test_login_and_logout(client: TestClient, db: Session) -> None:
    create_user(db, "admin", PLATFORM_ADMIN)
    login(client, "admin")
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Admin" in dashboard.text

    token = csrf_from(dashboard.text)
    logout = client.post("/logout", data={"csrf_token": token}, follow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["location"] == "/"
    protected = client.get("/dashboard", follow_redirects=False)
    assert protected.status_code == 303


def test_invalid_csrf_is_rejected(client: TestClient, db: Session) -> None:
    create_user(db, "admin", PLATFORM_ADMIN)
    response = client.post(
        "/login",
        data={"username": "admin", "password": "ValidPassword123!", "csrf_token": "invalid"},
    )
    assert response.status_code == 403


def test_viewer_cannot_manage_users(client: TestClient, db: Session) -> None:
    create_user(db, "viewer", VIEWER)
    login(client, "viewer")
    response = client.get("/admin/users")
    assert response.status_code == 403
    assert "Access denied" in response.text


def test_platform_admin_can_manage_users(client: TestClient, db: Session) -> None:
    create_user(db, "admin", PLATFORM_ADMIN)
    login(client, "admin")
    response = client.get("/admin/users")
    assert response.status_code == 200
    assert "Manage local OpenEA identities" in response.text


def test_repeated_failed_logins_trigger_temporary_lock(db: Session) -> None:
    create_user(db, "admin", PLATFORM_ADMIN)
    service = AuthenticationService(db)
    for _ in range(5):
        with suppress(AuthenticationError):
            service.authenticate("admin", "wrong-password")
    user = UserRepository(db).get_by_username("admin")
    assert user is not None
    assert user.locked_until is not None
    try:
        service.authenticate("admin", "ValidPassword123!")
    except AuthenticationError as exc:
        assert "temporarily locked" in str(exc)
    else:
        raise AssertionError("Locked account authenticated unexpectedly")


def test_session_cookie_is_httponly_and_samesite(client: TestClient) -> None:
    response = client.get("/setup")
    cookie = response.headers.get("set-cookie", "").lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_platform_admin_can_create_user_with_role(client: TestClient, db: Session) -> None:
    create_user(db, "admin", PLATFORM_ADMIN)
    login(client, "admin")
    page = client.get("/admin/users/new")
    token = csrf_from(page.text)
    response = client.post(
        "/admin/users/new",
        data={
            "username": "reader",
            "display_name": "Repository Reader",
            "password": "AnotherValidPassword123!",
            "roles": VIEWER,
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    user = UserRepository(db).get_by_username("reader")
    assert user is not None
    assert {role.name for role in user.roles} == {VIEWER}


def test_authenticated_dashboard_uses_left_sidebar(client: TestClient, db: Session) -> None:
    create_user(db, "architect", VIEWER)
    login(client, "architect")
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "openea-sidebar" in response.text
    assert "Dashboard" in response.text
    assert "Explore" in response.text
    assert "Portfolio" in response.text
    assert "Findings" in response.text
