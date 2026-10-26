from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import PLATFORM_ADMIN, VIEWER
from app.cli import reset_admin_password
from app.models.governance import AuditEvent
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthenticationService


def create_user(db: Session, username: str, role: str, password: str = "ValidPassword123!"):
    return AuthenticationService(db).create_user(
        username,
        username.title(),
        password,
        {role},
    )


def test_reset_password_clears_lockout_and_audits(db: Session) -> None:
    user = create_user(db, "admin", PLATFORM_ADMIN)
    user.failed_login_count = 4
    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=5)
    db.commit()

    AuthenticationService(db).reset_password(
        user,
        "RecoveredPassword123!",
        source="Administration CLI",
    )

    db.refresh(user)
    assert user.failed_login_count == 0
    assert user.locked_until is None
    assert PasswordHasher().verify(user.password_hash, "RecoveredPassword123!")

    event = db.scalar(
        select(AuditEvent)
        .where(AuditEvent.entity_id == user.id, AuditEvent.action == "PasswordReset")
        .order_by(AuditEvent.timestamp.desc())
    )
    assert event is not None
    assert event.source == "Administration CLI"
    assert event.after_state["password_changed"] is True


def test_cli_reset_admin_password(db: Session, monkeypatch) -> None:
    user = create_user(db, "admin", PLATFORM_ADMIN)
    user.failed_login_count = 4
    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=5)
    db.commit()

    responses = iter(["RecoveredPassword123!", "RecoveredPassword123!"])
    monkeypatch.setattr("app.cli.getpass.getpass", lambda _: next(responses))

    assert reset_admin_password("admin") == 0

    db.expire_all()
    recovered = UserRepository(db).get_by_username("admin")
    assert recovered is not None
    assert recovered.failed_login_count == 0
    assert recovered.locked_until is None
    assert PasswordHasher().verify(recovered.password_hash, "RecoveredPassword123!")


def test_cli_reset_admin_password_rejects_non_admin(
    db: Session,
    monkeypatch,
    capsys,
) -> None:
    create_user(db, "viewer", VIEWER)

    def unexpected_prompt(_: str) -> str:
        raise AssertionError("Password prompt should not run for a non-administrator")

    monkeypatch.setattr("app.cli.getpass.getpass", unexpected_prompt)

    assert reset_admin_password("viewer") == 1
    assert "not a Platform Administrator" in capsys.readouterr().out
