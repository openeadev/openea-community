from __future__ import annotations

import os
import sys

from sqlalchemy import text

from app.auth.permissions import ARCHITECT
from app.db.session import get_engine, get_session_factory
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthenticationService
from app.services.demo_service import DemoDataService
from app.services.findings_service import FindingsService
from app.services.seed_service import SystemSeedService

STATE_TABLE = "openea_demo_deploy_state"

PRESERVED_TABLES = {
    "alembic_version",
    "application_roles",
    STATE_TABLE,
}


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def ensure_state_table() -> None:
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {STATE_TABLE} (
                    id INTEGER PRIMARY KEY,
                    git_commit VARCHAR(64) NOT NULL,
                    reset_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )


def get_last_commit() -> str | None:
    engine = get_engine()

    with engine.connect() as connection:
        return connection.scalar(
            text(
                f"""
                SELECT git_commit
                FROM {STATE_TABLE}
                WHERE id = 1
                """
            )
        )


def record_commit(commit: str) -> None:
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                INSERT INTO {STATE_TABLE} (
                    id,
                    git_commit,
                    reset_at
                )
                VALUES (
                    1,
                    :git_commit,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT (id)
                DO UPDATE SET
                    git_commit = EXCLUDED.git_commit,
                    reset_at = CURRENT_TIMESTAMP
                """
            ),
            {"git_commit": commit},
        )


def truncate_application_data() -> None:
    engine = get_engine()

    with engine.begin() as connection:
        table_names = list(
            connection.scalars(
                text(
                    """
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                    """
                )
            )
        )

        tables_to_clear = [
            table_name
            for table_name in table_names
            if table_name not in PRESERVED_TABLES
        ]

        if not tables_to_clear:
            return

        preparer = connection.dialect.identifier_preparer

        quoted_tables = ", ".join(
            preparer.quote(table_name)
            for table_name in tables_to_clear
        )

        connection.execute(
            text(
                f"""
                TRUNCATE TABLE {quoted_tables}
                RESTART IDENTITY
                CASCADE
                """
            )
        )


def seed_demo() -> None:
    admin_password = os.environ.get("DEMO_ADMIN_PASSWORD")
    demo_password = os.environ.get("DEMO_USER_PASSWORD")

    if not admin_password:
        raise RuntimeError("DEMO_ADMIN_PASSWORD is required")

    if not demo_password:
        raise RuntimeError("DEMO_USER_PASSWORD is required")

    session_factory = get_session_factory()

    with session_factory() as db:
        auth = AuthenticationService(db)

        admin = auth.create_initial_admin(
            username="demo-admin",
            display_name="OpenEA Demo Administrator",
            password=admin_password,
        )

        demo_user = auth.create_user(
            username="demo",
            display_name="OpenEA Community Demo",
            password=demo_password,
            role_names={ARCHITECT},
            actor=admin,
        )

        SystemSeedService(db).seed()

        DemoDataService(db).seed(demo_user)

        AnalyticsService(db).calculate_all()

        FindingsService(db).evaluate_all()


def main() -> int:
    if not env_bool("DEMO_RESET_ON_DEPLOY"):
        print("Demo reset disabled.")
        return 0

    if os.getenv("RENDER") != "true":
        print("Not running on Render. Demo reset skipped.")
        return 0

    current_commit = os.getenv("RENDER_GIT_COMMIT", "").strip()

    if not current_commit:
        print("RENDER_GIT_COMMIT is unavailable. Demo reset skipped.")
        return 0

    ensure_state_table()

    previous_commit = get_last_commit()

    force_reset = env_bool("DEMO_FORCE_RESET")

    if previous_commit == current_commit and not force_reset:
        print(
            "Demo repository already initialized for commit "
            f"{current_commit[:12]}."
        )
        return 0

    print(
        "New OpenEA Community deployment detected: "
        f"{current_commit[:12]}"
    )

    if previous_commit:
        print(
            "Previous seeded commit: "
            f"{previous_commit[:12]}"
        )

    print("Resetting demo repository...")

    truncate_application_data()

    print("Seeding OpenEA Community...")
    seed_demo()

    record_commit(current_commit)

    print(
        "Demo repository initialized for commit "
        f"{current_commit[:12]}."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())