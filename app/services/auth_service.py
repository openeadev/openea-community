from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.auth.passwords import hash_password, needs_rehash, verify_password
from app.auth.permissions import PLATFORM_ADMIN
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService

MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 5


class AuthenticationError(Exception):
    pass


class AuthenticationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.audit = AuditService(db)

    def initial_setup_required(self) -> bool:
        return self.users.count_users() == 0

    def create_initial_admin(self, username: str, display_name: str, password: str) -> User:
        if not self.initial_setup_required():
            raise ValueError("Initial administrator has already been created")
        return self.create_user(username, display_name, password, {PLATFORM_ADMIN})

    def create_user(
        self, username: str, display_name: str, password: str, role_names: set[str], actor: User | None = None
    ) -> User:
        username = username.strip()
        display_name = display_name.strip()
        if len(username) < 3 or len(username) > 80:
            raise ValueError("Username must be between 3 and 80 characters")
        if not display_name:
            raise ValueError("Display name is required")
        self._validate_password(password)
        if self.users.get_by_username(username):
            raise ValueError("Username already exists")
        roles = self.users.get_roles_by_names(role_names)
        if len(roles) != len(role_names):
            raise ValueError("One or more selected roles are invalid")
        user = User(
            username=username,
            display_name=display_name,
            password_hash=hash_password(password),
            roles=roles,
        )
        self.users.add(user)
        self.audit.record(action="UserCreated", entity_type="user", entity_id=user.id, actor=actor, after={"username": user.username, "display_name": user.display_name, "roles": sorted(role.name for role in roles), "is_active": True}, source="Administration" if actor else "Setup")
        self.db.commit()
        return user

    def authenticate(self, username: str, password: str) -> User:
        user = self.users.get_by_username(username)
        if user is None or not user.is_active or user.is_service_account:
            raise AuthenticationError("Invalid username or password")

        now = datetime.now(timezone.utc)
        locked_until = user.locked_until
        if locked_until is not None:
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if locked_until > now:
                raise AuthenticationError("Login temporarily locked after repeated failures")

        if not verify_password(user.password_hash, password):
            user.failed_login_count += 1
            if user.failed_login_count >= MAX_FAILED_LOGINS:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
                user.failed_login_count = 0
            self.db.commit()
            raise AuthenticationError("Invalid username or password")

        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = now
        self.db.commit()
        return user

    def update_user(
        self,
        user: User,
        display_name: str,
        is_active: bool,
        role_names: set[str],
        new_password: str | None = None,
        actor: User | None = None,
    ) -> User:
        before = {"display_name": user.display_name, "roles": sorted(role.name for role in user.roles), "is_active": user.is_active}
        display_name = display_name.strip()
        if not display_name:
            raise ValueError("Display name is required")
        roles = self.users.get_roles_by_names(role_names)
        if len(roles) != len(role_names):
            raise ValueError("One or more selected roles are invalid")
        if new_password:
            self._validate_password(new_password)
            user.password_hash = hash_password(new_password)
        user.display_name = display_name
        user.is_active = is_active
        user.roles = roles
        self.audit.record(action="UserUpdated", entity_type="user", entity_id=user.id, actor=actor, before=before, after={"display_name": user.display_name, "roles": sorted(role.name for role in roles), "is_active": user.is_active, "password_changed": bool(new_password)}, source="Administration")
        self.db.commit()
        return user

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters")
