import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")

object_tags = Table(
    "object_tags",
    Base.metadata,
    Column("object_id", String(36), ForeignKey("objects.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class EnumerationDefinition(Base):
    __tablename__ = "enumeration_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    values: Mapped[list["EnumerationValue"]] = relationship(back_populates="definition", cascade="all, delete-orphan", lazy="selectin")


class EnumerationValue(Base):
    __tablename__ = "enumeration_values"
    __table_args__ = (UniqueConstraint("enumeration_id", "value", name="uq_enumeration_value"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    enumeration_id: Mapped[str] = mapped_column(String(36), ForeignKey("enumeration_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(120), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    definition: Mapped[EnumerationDefinition] = relationship(back_populates="values")


class ObjectType(Base):
    __tablename__ = "object_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    schema_definition: Mapped[dict[str, object]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    objects: Mapped[list["ArchitectureObject"]] = relationship(back_populates="object_type")


class ArchitectureObject(Base):
    __tablename__ = "objects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("object_types.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    record_status: Mapped[str] = mapped_column(String(40), nullable=False, default="Draft", index=True)
    governance_status: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    lifecycle_stage: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    criticality: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    owner_organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("objects.id", ondelete="SET NULL"), nullable=True, index=True)
    owner_role_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("objects.id", ondelete="SET NULL"), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(40), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_reviewed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_frequency: Mapped[str | None] = mapped_column(String(80), nullable=True)
    properties: Mapped[dict[str, object]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    object_type: Mapped[ObjectType] = relationship(back_populates="objects", lazy="joined", foreign_keys=[object_type_id])
    owner_organization: Mapped["ArchitectureObject | None"] = relationship(remote_side="ArchitectureObject.id", foreign_keys=[owner_organization_id], lazy="joined")
    owner_role: Mapped["ArchitectureObject | None"] = relationship(remote_side="ArchitectureObject.id", foreign_keys=[owner_role_id], lazy="joined")
    aliases: Mapped[list["ObjectAlias"]] = relationship(back_populates="object", cascade="all, delete-orphan", lazy="selectin")
    tags: Mapped[list["Tag"]] = relationship(secondary=object_tags, back_populates="objects", lazy="selectin")


class ObjectAlias(Base):
    __tablename__ = "object_aliases"
    __table_args__ = (UniqueConstraint("object_id", "alias", name="uq_object_alias"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id: Mapped[str] = mapped_column(String(36), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    object: Mapped[ArchitectureObject] = relationship(back_populates="aliases")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    objects: Mapped[list[ArchitectureObject]] = relationship(secondary=object_tags, back_populates="tags")


class RelationshipType(Base):
    __tablename__ = "relationship_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    inverse_label: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    properties_schema: Mapped[dict[str, object]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rules: Mapped[list["RelationshipRule"]] = relationship(back_populates="relationship_type", cascade="all, delete-orphan", lazy="selectin")


class RelationshipRule(Base):
    __tablename__ = "relationship_rules"
    __table_args__ = (UniqueConstraint("relationship_type_id", "source_object_type_id", "target_object_type_id", name="uq_relationship_rule"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    relationship_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("relationship_types.id", ondelete="CASCADE"), nullable=False, index=True)
    source_object_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("object_types.id", ondelete="CASCADE"), nullable=False, index=True)
    target_object_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("object_types.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type: Mapped[RelationshipType] = relationship(back_populates="rules")


class ArchitectureRelationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint("relationship_type_id", "source_object_id", "target_object_id", name="uq_relationship_instance"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    relationship_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("relationship_types.id"), nullable=False, index=True)
    source_object_id: Mapped[str] = mapped_column(String(36), ForeignKey("objects.id"), nullable=False, index=True)
    target_object_id: Mapped[str] = mapped_column(String(36), ForeignKey("objects.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    criticality: Mapped[str | None] = mapped_column(String(40), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(40), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    properties: Mapped[dict[str, object]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    provenance: Mapped[dict[str, object]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    relationship_type: Mapped[RelationshipType] = relationship(lazy="joined")
    source_object: Mapped[ArchitectureObject] = relationship(foreign_keys=[source_object_id], lazy="joined")
    target_object: Mapped[ArchitectureObject] = relationship(foreign_keys=[target_object_id], lazy="joined")
