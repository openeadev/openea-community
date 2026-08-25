"""Phase 3 metamodel foundation.

Revision ID: 0003_phase3
Revises: 0002_phase2
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import context, op

revision: str = "0003_phase3"
down_revision: str | None = "0002_phase2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "enumeration_definitions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_enumeration_definitions_key", "enumeration_definitions", ["key"], unique=True)

    op.create_table(
        "enumeration_values",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("enumeration_id", sa.String(length=36), nullable=False),
        sa.Column("value", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["enumeration_id"], ["enumeration_definitions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enumeration_id", "value", name="uq_enumeration_value"),
    )
    op.create_index("ix_enumeration_values_enumeration_id", "enumeration_values", ["enumeration_id"])

    op.create_table(
        "object_types",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("domain", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("schema_definition", JSON_TYPE, nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_object_types_key", "object_types", ["key"], unique=True)
    op.create_index("ix_object_types_domain", "object_types", ["domain"])

    op.create_table(
        "objects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("object_type_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("record_status", sa.String(length=40), nullable=False, server_default="Draft"),
        sa.Column("governance_status", sa.String(length=40), nullable=True),
        sa.Column("lifecycle_stage", sa.String(length=80), nullable=True),
        sa.Column("criticality", sa.String(length=40), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("confidence", sa.String(length=40), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("last_reviewed_date", sa.Date(), nullable=True),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("review_frequency", sa.String(length=80), nullable=True),
        sa.Column("properties", JSON_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["object_type_id"], ["object_types.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for index_name, columns in [
        ("ix_objects_object_type_id", ["object_type_id"]),
        ("ix_objects_name", ["name"]),
        ("ix_objects_record_status", ["record_status"]),
        ("ix_objects_governance_status", ["governance_status"]),
        ("ix_objects_lifecycle_stage", ["lifecycle_stage"]),
        ("ix_objects_criticality", ["criticality"]),
        ("ix_objects_archived_at", ["archived_at"]),
    ]:
        op.create_index(index_name, "objects", columns)

    op.create_table(
        "object_aliases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("object_id", sa.String(length=36), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_id", "alias", name="uq_object_alias"),
    )
    op.create_index("ix_object_aliases_object_id", "object_aliases", ["object_id"])
    op.create_index("ix_object_aliases_alias", "object_aliases", ["alias"])

    op.create_table(
        "tags",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_tags_name", "tags", ["name"], unique=True)
    op.create_table(
        "object_tags",
        sa.Column("object_id", sa.String(length=36), nullable=False),
        sa.Column("tag_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("object_id", "tag_id"),
    )

    op.create_table(
        "relationship_types",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("inverse_label", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("properties_schema", JSON_TYPE, nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_relationship_types_key", "relationship_types", ["key"], unique=True)

    op.create_table(
        "relationship_rules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("relationship_type_id", sa.String(length=36), nullable=False),
        sa.Column("source_object_type_id", sa.String(length=36), nullable=False),
        sa.Column("target_object_type_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["relationship_type_id"], ["relationship_types.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_object_type_id"], ["object_types.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_object_type_id"], ["object_types.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("relationship_type_id", "source_object_type_id", "target_object_type_id", name="uq_relationship_rule"),
    )
    op.create_index("ix_relationship_rules_relationship_type_id", "relationship_rules", ["relationship_type_id"])
    op.create_index("ix_relationship_rules_source_object_type_id", "relationship_rules", ["source_object_type_id"])
    op.create_index("ix_relationship_rules_target_object_type_id", "relationship_rules", ["target_object_type_id"])

    # Seed mandatory system metamodel data during real upgrades. Offline SQL generation
    # intentionally emits DDL only because the idempotent seed service performs reads.
    if not context.is_offline_mode():
        from sqlalchemy.orm import Session

        from app.services.seed_service import SystemSeedService

        session = Session(bind=op.get_bind())
        SystemSeedService(session).seed(commit=False, include_finding_rules=False)


def downgrade() -> None:
    op.drop_table("relationship_rules")
    op.drop_index("ix_relationship_types_key", table_name="relationship_types")
    op.drop_table("relationship_types")
    op.drop_table("object_tags")
    op.drop_index("ix_tags_name", table_name="tags")
    op.drop_table("tags")
    op.drop_index("ix_object_aliases_alias", table_name="object_aliases")
    op.drop_index("ix_object_aliases_object_id", table_name="object_aliases")
    op.drop_table("object_aliases")
    for index_name in ["ix_objects_archived_at", "ix_objects_criticality", "ix_objects_lifecycle_stage", "ix_objects_governance_status", "ix_objects_record_status", "ix_objects_name", "ix_objects_object_type_id"]:
        op.drop_index(index_name, table_name="objects")
    op.drop_table("objects")
    op.drop_index("ix_object_types_domain", table_name="object_types")
    op.drop_index("ix_object_types_key", table_name="object_types")
    op.drop_table("object_types")
    op.drop_index("ix_enumeration_values_enumeration_id", table_name="enumeration_values")
    op.drop_table("enumeration_values")
    op.drop_index("ix_enumeration_definitions_key", table_name="enumeration_definitions")
    op.drop_table("enumeration_definitions")
