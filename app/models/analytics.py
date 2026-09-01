import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.metamodel import JSON_TYPE, ArchitectureObject


class ObjectMetric(Base):
    __tablename__ = "object_metrics"
    __table_args__ = (UniqueConstraint("object_id", "metric_type", name="uq_object_metric_type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id: Mapped[str] = mapped_column(String(36), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    band: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    explanation: Mapped[dict[str, object]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    object: Mapped[ArchitectureObject] = relationship(lazy="joined")


class ScheduledJobSetting(Base):
    __tablename__ = "scheduled_job_settings"

    job_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    last_enqueued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_status: Mapped[str] = mapped_column(String(30), nullable=False, default="Never run")
    last_result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
