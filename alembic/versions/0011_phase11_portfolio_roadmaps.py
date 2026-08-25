"""Phase 11 portfolio, capability maps, and roadmaps release marker.

Revision ID: 0011_phase11
Revises: 0010_phase10
"""
from collections.abc import Sequence

revision: str = "0011_phase11"
down_revision: str | None = "0010_phase10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Phase 11 views derive entirely from existing repository, relationship,
    # date, and metric data. No authoritative schema change is required.
    pass


def downgrade() -> None:
    pass
