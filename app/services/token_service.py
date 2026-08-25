from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_auth import ApiToken
from app.models.user import ApplicationRole, User
from app.services.audit_service import AuditService

TOKEN_EXPIRATIONS = {30, 60, 90, 180, 365}
API_SCOPES = (
    "objects:read", "objects:write",
    "relationships:read", "relationships:write",
    "search:read", "impact:read",
    "findings:read", "findings:write",
    "reviews:read", "reviews:write",
    "analytics:read",
)


@dataclass(frozen=True)
class CreatedToken:
    token: ApiToken
    secret: str


class TokenService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _hash(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def create_token(self, *, owner: User, name: str, scopes: list[str], expiration_days: int | None,
                     creator: User, description: str = "") -> CreatedToken:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Token name is required")
        selected = sorted(set(scopes))
        invalid = set(selected) - set(API_SCOPES)
        if invalid:
            raise ValueError(f"Unsupported token scope: {sorted(invalid)[0]}")
        if not selected:
            raise ValueError("Select at least one token scope")
        if expiration_days is not None and expiration_days not in TOKEN_EXPIRATIONS:
            raise ValueError("Unsupported token expiration")
        prefix = secrets.token_hex(6)
        secret_part = secrets.token_urlsafe(32)
        raw = f"openea_{'svc' if owner.is_service_account else 'pat'}_{prefix}_{secret_part}"
        expires = None if expiration_days is None else datetime.now(timezone.utc) + timedelta(days=expiration_days)
        token = ApiToken(
            user_id=owner.id, name=clean_name, token_prefix=prefix, token_hash=self._hash(raw),
            scopes=selected, expires_at=expires, created_by=creator.id, description=description.strip(),
        )
        self.db.add(token)
        self.db.flush()
        AuditService(self.db).record(
            action="ApiTokenCreated", entity_type="api_token", entity_id=token.id, actor=creator,
            after={"owner_id": owner.id, "name": token.name, "scopes": selected, "expires_at": expires.isoformat() if expires else None},
            source="Administration" if owner.is_service_account else "Account",
        )
        self.db.commit()
        self.db.refresh(token)
        return CreatedToken(token=token, secret=raw)

    def authenticate(self, raw: str) -> ApiToken | None:
        parts = raw.split("_", 3)
        if len(parts) != 4 or parts[0] != "openea" or parts[1] not in {"pat", "svc"}:
            return None
        prefix = parts[2]
        token = self.db.scalar(select(ApiToken).where(ApiToken.token_prefix == prefix))
        if token is None or token.revoked_at is not None or not secrets.compare_digest(token.token_hash, self._hash(raw)):
            return None
        now = datetime.now(timezone.utc)
        if token.expires_at is not None:
            expires = token.expires_at if token.expires_at.tzinfo else token.expires_at.replace(tzinfo=timezone.utc)
            if expires <= now:
                return None
        if not token.owner.is_active:
            return None
        token.last_used_at = now
        self.db.commit()
        return token

    def list_all(self) -> list[ApiToken]:
        return list(self.db.scalars(select(ApiToken).order_by(ApiToken.created_at.desc())).unique().all())

    def list_for_user(self, user: User) -> list[ApiToken]:
        return list(self.db.scalars(select(ApiToken).where(ApiToken.user_id == user.id).order_by(ApiToken.created_at.desc())).all())

    def revoke(self, token_id: str, *, requesting_user: User, allow_any: bool = False) -> None:
        token = self.db.get(ApiToken, token_id)
        if token is None:
            raise ValueError("Token not found")
        if not allow_any and token.user_id != requesting_user.id:
            raise ValueError("Token not found")
        if token.revoked_at is None:
            token.revoked_at = datetime.now(timezone.utc)
            AuditService(self.db).record(
                action="ApiTokenRevoked", entity_type="api_token", entity_id=token.id, actor=requesting_user,
                after={"owner_id": token.user_id, "name": token.name}, source="Administration" if allow_any else "Account",
            )
            self.db.commit()

    def create_service_account(self, *, name: str, role_names: set[str], creator: User) -> User:
        clean = name.strip()
        if not clean:
            raise ValueError("Service account name is required")
        username = "svc-" + "".join(ch.lower() if ch.isalnum() else "-" for ch in clean).strip("-")
        base = username or "svc-account"
        suffix = 1
        while self.db.scalar(select(User).where(User.username == username)) is not None:
            suffix += 1
            username = f"{base}-{suffix}"
        roles = list(self.db.scalars(select(ApplicationRole).where(ApplicationRole.name.in_(role_names))).all())
        if len(roles) != len(role_names):
            raise ValueError("One or more roles are invalid")
        account = User(username=username, display_name=clean, password_hash="!service-account-no-password!", is_service_account=True, roles=roles)
        self.db.add(account)
        self.db.flush()
        AuditService(self.db).record(
            action="ServiceAccountCreated", entity_type="user", entity_id=account.id, actor=creator,
            after={"display_name": account.display_name, "username": account.username, "roles": sorted(role_names)}, source="Administration",
        )
        self.db.commit()
        self.db.refresh(account)
        return account

    def update_service_account(self, account: User, *, role_names: set[str], is_active: bool, actor: User) -> User:
        if not account.is_service_account:
            raise ValueError("Service account not found")
        roles = list(self.db.scalars(select(ApplicationRole).where(ApplicationRole.name.in_(role_names))).all())
        if len(roles) != len(role_names):
            raise ValueError("One or more roles are invalid")
        before = {"roles": sorted(role.name for role in account.roles), "is_active": account.is_active}
        account.roles = roles
        account.is_active = is_active
        AuditService(self.db).record(
            action="ServiceAccountUpdated", entity_type="user", entity_id=account.id, actor=actor, before=before,
            after={"roles": sorted(role_names), "is_active": is_active}, source="Administration",
        )
        self.db.commit()
        return account

    def list_service_accounts(self) -> list[User]:
        return list(self.db.scalars(select(User).where(User.is_service_account.is_(True)).order_by(User.display_name)).unique().all())
