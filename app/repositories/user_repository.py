from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.user import ApplicationRole, User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def count_users(self) -> int:
        return self.db.scalar(select(func.count()).select_from(User)) or 0

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.scalar(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(
            select(User)
            .options(selectinload(User.roles))
            .where(func.lower(User.username) == username.strip().lower())
        )

    def list_users(self) -> list[User]:
        return list(
            self.db.scalars(
                select(User).options(selectinload(User.roles)).where(User.is_service_account.is_(False)).order_by(User.username)
            ).all()
        )

    def list_roles(self) -> list[ApplicationRole]:
        return list(self.db.scalars(select(ApplicationRole).order_by(ApplicationRole.name)).all())

    def get_roles_by_names(self, names: set[str]) -> list[ApplicationRole]:
        if not names:
            return []
        return list(
            self.db.scalars(
                select(ApplicationRole).where(ApplicationRole.name.in_(names))
            ).all()
        )

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user
