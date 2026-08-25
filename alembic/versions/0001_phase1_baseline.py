"""Phase 1 schema baseline.

Revision ID: 0001_phase1
Revises: None
"""
from collections.abc import Sequence

revision: str = "0001_phase1"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Phase 1 intentionally introduces no business tables.
    pass


def downgrade() -> None:
    pass
