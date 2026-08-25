"""Phase 6 PostgreSQL search indexes.

Revision ID: 0006_phase6
Revises: 0005_phase5
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0006_phase6"
down_revision: str | None = "0005_phase5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE INDEX ix_objects_name_trgm ON objects USING gin (name gin_trgm_ops)")
    op.execute("CREATE INDEX ix_object_aliases_alias_trgm ON object_aliases USING gin (alias gin_trgm_ops)")
    op.execute("CREATE INDEX ix_tags_name_trgm ON tags USING gin (name gin_trgm_ops)")
    op.execute("CREATE INDEX ix_objects_search_fts ON objects USING gin (to_tsvector('simple', coalesce(name,'') || ' ' || coalesce(description,'')))")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_objects_search_fts")
    op.execute("DROP INDEX IF EXISTS ix_tags_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_object_aliases_alias_trgm")
    op.execute("DROP INDEX IF EXISTS ix_objects_name_trgm")
