"""Phase 2 identity and authorization.

Revision ID: 0002_phase2
Revises: 0001_phase1
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_phase2"
down_revision: str | None = "0001_phase1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE_ROWS = [
    (
        "0b0ad301-2bd1-4ac7-9f66-0b15137d1001",
        "Platform Administrator",
        "Manages users, authentication, application roles, platform configuration, security, "
        "and system administration.",
    ),
    (
        "0b0ad301-2bd1-4ac7-9f66-0b15137d1002",
        "Architecture Administrator",
        "Manages architecture governance and metamodel configuration.",
    ),
    (
        "0b0ad301-2bd1-4ac7-9f66-0b15137d1003",
        "Architect",
        "Creates and manages architecture repository content and analysis.",
    ),
    (
        "0b0ad301-2bd1-4ac7-9f66-0b15137d1004",
        "Contributor",
        "Maintains permitted architecture records and relationships.",
    ),
    (
        "0b0ad301-2bd1-4ac7-9f66-0b15137d1005",
        "Viewer",
        "Provides read-only access to architecture information.",
    ),
]


def upgrade() -> None:
    op.create_table(
        "application_roles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_application_roles_name", "application_roles", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["application_roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    role_table = sa.table(
        "application_roles",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("is_system", sa.Boolean),
    )
    op.bulk_insert(
        role_table,
        [
            {"id": role_id, "name": name, "description": description, "is_system": True}
            for role_id, name, description in ROLE_ROWS
        ],
    )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_application_roles_name", table_name="application_roles")
    op.drop_table("application_roles")
