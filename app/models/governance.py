import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.metamodel import JSON_TYPE, ArchitectureObject
from app.models.user import User


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id: Mapped[str] = mapped_column(String(36), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    object: Mapped[ArchitectureObject] = relationship(lazy="joined")
    reviewer: Mapped[User | None] = relationship(lazy="joined")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id: Mapped[str] = mapped_column(String(36), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    object: Mapped[ArchitectureObject] = relationship(lazy="joined")
    user: Mapped[User | None] = relationship(lazy="joined")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    before_state: Mapped[dict[str, object] | None] = mapped_column(JSON_TYPE, nullable=True)
    after_state: Mapped[dict[str, object] | None] = mapped_column(JSON_TYPE, nullable=True)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="Web")
    correlation_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    user: Mapped[User | None] = relationship(lazy="joined")
