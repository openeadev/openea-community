from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.token_service import TokenService

bearer_scheme = HTTPBearer(auto_error=False)


def get_api_identity(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    request.state.api_scopes = None
    request.state.api_token_id = None
    if credentials is not None:
        if credentials.scheme.lower() != "bearer":
            return None
        token = TokenService(db).authenticate(credentials.credentials)
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired API token")
        request.state.api_scopes = set(token.scopes)
        request.state.api_token_id = token.id
        return token.owner
    return get_current_user(request, db)


def require_api_access(*, roles: tuple[str, ...], scope: str) -> Callable[..., User]:
    def dependency(request: Request, user: User | None = Depends(get_api_identity)) -> User:
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        role_names = {role.name for role in user.roles}
        if not role_names.intersection(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
        token_scopes = getattr(request.state, "api_scopes", None)
        if token_scopes is not None and scope not in token_scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Token lacks required scope: {scope}")
        return user

    return dependency
