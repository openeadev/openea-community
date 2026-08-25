"""OpenEA Community 1.4.0 relationship CSV import.

Revision ID: 0014_phase14
Revises: 0013_phase13
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_phase14"
down_revision: str | None = "0013_phase13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "import_batches",
        sa.Column("import_kind", sa.String(length=40), nullable=False, server_default="object"),
    )
    op.create_index("ix_import_batches_import_kind", "import_batches", ["import_kind"])
    op.alter_column("import_batches", "object_type_key", existing_type=sa.String(length=80), nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM import_batches WHERE import_kind = 'relationship'")
    op.alter_column("import_batches", "object_type_key", existing_type=sa.String(length=80), nullable=False)
    op.drop_index("ix_import_batches_import_kind", table_name="import_batches")
    op.drop_column("import_batches", "import_kind")
