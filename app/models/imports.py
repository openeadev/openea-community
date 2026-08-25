import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.metamodel import JSON_TYPE
from app.models.user import User


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    import_kind: Mapped[str] = mapped_column(String(40), nullable=False, default="object", index=True)
    object_type_key: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="Uploaded", index=True)
    headers: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False, default=list)
    rows: Mapped[list[dict[str, object]]] = mapped_column(JSON_TYPE, nullable=False, default=list)
    mapping: Mapped[dict[str, str]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    preview: Mapped[dict[str, object]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    creator: Mapped[User | None] = relationship(lazy="joined")
