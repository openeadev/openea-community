"""Phase 4 repository UI ownership fields.

Revision ID: 0004_phase4
Revises: 0003_phase3
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_phase4"
down_revision: str | None = "0003_phase3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("objects", sa.Column("owner_organization_id", sa.String(length=36), nullable=True))
    op.add_column("objects", sa.Column("owner_role_id", sa.String(length=36), nullable=True))
    op.create_index("ix_objects_owner_organization_id", "objects", ["owner_organization_id"])
    op.create_index("ix_objects_owner_role_id", "objects", ["owner_role_id"])
    op.create_foreign_key(
        "fk_objects_owner_organization",
        "objects",
        "objects",
        ["owner_organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_objects_owner_role",
        "objects",
        "objects",
        ["owner_role_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_objects_owner_role", "objects", type_="foreignkey")
    op.drop_constraint("fk_objects_owner_organization", "objects", type_="foreignkey")
    op.drop_index("ix_objects_owner_role_id", table_name="objects")
    op.drop_index("ix_objects_owner_organization_id", table_name="objects")
    op.drop_column("objects", "owner_role_id")
    op.drop_column("objects", "owner_organization_id")
