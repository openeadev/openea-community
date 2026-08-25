from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

PLATFORM_ADMIN = "Platform Administrator"
ARCHITECTURE_ADMIN = "Architecture Administrator"
ARCHITECT = "Architect"
CONTRIBUTOR = "Contributor"
VIEWER = "Viewer"
ALL_APPLICATION_ROLES = (PLATFORM_ADMIN, ARCHITECTURE_ADMIN, ARCHITECT, CONTRIBUTOR, VIEWER)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = UserRepository(db).get_by_id(str(user_id))
    if user is None or not user.is_active:
        request.session.clear()
        return None
    return user


def require_authenticated(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return user


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    def dependency(user: User = Depends(require_authenticated)) -> User:
        user_roles = {role.name for role in user.roles}
        if not user_roles.intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission"
            )
        return user

    return dependency


require_platform_admin = require_roles(PLATFORM_ADMIN)
