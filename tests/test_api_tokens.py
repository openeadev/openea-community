import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT, PLATFORM_ADMIN, VIEWER
from app.services.auth_service import AuthenticationError, AuthenticationService
from app.services.token_service import TokenService


def make_user(db: Session, username: str, role: str):
    return AuthenticationService(db).create_user(username, username.title(), "StrongPassword123!", {role})


def test_personal_token_authenticates_api_with_scope(client: TestClient, db: Session):
    user = make_user(db, "architect-token", ARCHITECT)
    created = TokenService(db).create_token(owner=user, name="automation", scopes=["objects:read"], expiration_days=30, creator=user)
    response = client.get("/api/v1/objects", headers={"Authorization": f"Bearer {created.secret}"})
    assert response.status_code == 200
    assert created.secret not in repr(TokenService(db).list_for_user(user))


def test_token_scope_is_enforced(client: TestClient, db: Session):
    user = make_user(db, "architect-scope", ARCHITECT)
    created = TokenService(db).create_token(owner=user, name="read only", scopes=["objects:read"], expiration_days=30, creator=user)
    response = client.post("/api/v1/objects", headers={"Authorization": f"Bearer {created.secret}"}, json={"object_type_key": "technology", "name": "Denied"})
    assert response.status_code == 403
    assert "objects:write" in response.json()["detail"]


def test_revoked_token_is_rejected(client: TestClient, db: Session):
    user = make_user(db, "architect-revoke", ARCHITECT)
    service = TokenService(db)
    created = service.create_token(owner=user, name="revoke", scopes=["objects:read"], expiration_days=None, creator=user)
    service.revoke(created.token.id, requesting_user=user)
    response = client.get("/api/v1/objects", headers={"Authorization": f"Bearer {created.secret}"})
    assert response.status_code == 401


def test_service_account_cannot_password_login_but_token_works(client: TestClient, db: Session):
    admin = make_user(db, "platform-service", PLATFORM_ADMIN)
    service = TokenService(db)
    account = service.create_service_account(name="CMDB Sync", role_names={VIEWER}, creator=admin)
    assert account.is_service_account is True
    created = service.create_token(owner=account, name="sync", scopes=["objects:read"], expiration_days=90, creator=admin)
    response = client.get("/api/v1/objects", headers={"Authorization": f"Bearer {created.secret}"})
    assert response.status_code == 200
    with pytest.raises(AuthenticationError):
        AuthenticationService(db).authenticate(account.username, "anything")


def test_docs_csp_allows_swagger_inline_bootstrap(client: TestClient):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text
    assert "'unsafe-inline'" in response.headers["content-security-policy"]
    schema = client.get("/openapi.json").json()
    assert "HTTPBearer" in schema["components"]["securitySchemes"]
