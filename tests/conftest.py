import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

TEST_DB = Path("/tmp/openea_phase2_test.db")
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "phase2-test-secret-key-that-is-long-enough"
os.environ["BASE_URL"] = "http://testserver"

from app.auth.permissions import ALL_APPLICATION_ROLES  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_engine, get_session_factory  # noqa: E402
from app.main import app  # noqa: E402
from app.models.analytics import Job, ObjectMetric  # noqa: E402
from app.models.findings import Finding, RuleDefinition  # noqa: E402
from app.models.governance import AuditEvent, Comment, Review  # noqa: E402
from app.models.imports import ImportBatch  # noqa: E402
from app.models.metamodel import (  # noqa: E402
    ArchitectureObject,
    ArchitectureRelationship,
    ObjectAlias,
    Tag,
    object_tags,
)
from app.models.user import ApplicationRole, User  # noqa: E402
from app.services.seed_service import SystemSeedService  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def database_schema() -> None:
    if TEST_DB.exists():
        TEST_DB.unlink()
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        for role_name in ALL_APPLICATION_ROLES:
            db.add(ApplicationRole(name=role_name, description=f"Test {role_name}"))
        db.commit()
        SystemSeedService(db).seed()
    yield
    get_engine().dispose()
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture(autouse=True)
def clean_users() -> None:
    with get_session_factory()() as db:
        db.execute(delete(ImportBatch))
        db.execute(delete(Finding))
        db.execute(delete(RuleDefinition).where(RuleDefinition.is_system.is_(False)))
        db.execute(delete(ObjectMetric))
        db.execute(delete(Job))
        db.execute(delete(AuditEvent))
        db.execute(delete(Comment))
        db.execute(delete(Review))
        db.execute(delete(ArchitectureRelationship))
        db.execute(object_tags.delete())
        db.execute(delete(ObjectAlias))
        db.execute(delete(ArchitectureObject))
        db.execute(delete(Tag))
        db.execute(delete(User))
        db.commit()


@pytest.fixture
def db() -> Session:
    with get_session_factory()() as session:
        yield session


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
