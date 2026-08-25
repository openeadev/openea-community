from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT, VIEWER
from app.services.auth_service import AuthenticationService
from app.services.object_service import ObjectService
from app.services.search_service import SearchService

PASSWORD = "ValidPassword123!"


def make_user(db: Session, username: str, role: str):
    return AuthenticationService(db).create_user(username, username.title(), PASSWORD, {role})


def create_app(db: Session, actor, name: str, *, aliases: str = "", tags: str = "", criticality: str = "Medium", owner_id: str | None = None):
    return ObjectService(db).create_object(
        object_type_key="application", name=name, description="Architecture search test",
        record_status="Active", governance_status="Approved", lifecycle_stage="Active",
        criticality=criticality, owner_organization_id=owner_id, owner_role_id=None,
        source="Manual", confidence="Confirmed", valid_from=None, valid_until=None,
        aliases=aliases, tags=tags, properties={}, actor=actor,
    )


def test_search_name_alias_tag_and_fuzzy(db: Session) -> None:
    actor = make_user(db, "architect", ARCHITECT)
    create_app(db, actor, "Customer Portal", aliases="Client Gateway", tags="digital, customer")
    service = SearchService(db)
    assert [x.name for x in service.search(query="Customer Portal").items] == ["Customer Portal"]
    assert [x.name for x in service.search(query="Client Gateway").items] == ["Customer Portal"]
    assert [x.name for x in service.search(query="digital").items] == ["Customer Portal"]
    assert [x.name for x in service.search(query="Custmer Portal").items] == ["Customer Portal"]


def test_search_filters_owner_governance_and_review(db: Session) -> None:
    actor = make_user(db, "architect", ARCHITECT)
    org = ObjectService(db).create_object(
        object_type_key="organization", name="Digital Banking", description="", record_status="Active",
        governance_status=None, lifecycle_stage=None, criticality="Medium", owner_organization_id=None,
        owner_role_id=None, source="Manual", confidence="Confirmed", valid_from=None, valid_until=None,
        aliases="", tags="", properties={}, actor=actor,
    )
    app = create_app(db, actor, "Banking Portal", tags="banking", criticality="High", owner_id=org.id)
    from app.services.governance_service import GovernanceService
    GovernanceService(db).transition(app, "Submitted", actor)
    GovernanceService(db).transition(app, "Approved", actor)
    app.next_review_date = date.today() - timedelta(days=1)
    db.commit()
    result = SearchService(db).search(object_type_key="application", criticality="High", governance_status="Approved", owner_id=org.id, tag="banking", review_status="overdue")
    assert [x.name for x in result.items] == ["Banking Portal"]


def test_search_paginates(db: Session) -> None:
    actor = make_user(db, "architect", ARCHITECT)
    for number in range(30):
        create_app(db, actor, f"Application {number:02d}")
    first = SearchService(db).search(page=1, per_page=25)
    second = SearchService(db).search(page=2, per_page=25)
    assert first.total == 30
    assert first.pages == 2
    assert len(first.items) == 25
    assert len(second.items) == 5


def test_search_page_requires_authentication(client) -> None:
    response = client.get("/explore?q=portal", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")


def test_viewer_can_search_read_only(client, db: Session) -> None:
    actor = make_user(db, "architect", ARCHITECT)
    create_app(db, actor, "Searchable Application")
    make_user(db, "viewer", VIEWER)
    page = client.get("/login")
    import re
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    client.post("/login", data={"username":"viewer","password":PASSWORD,"csrf_token":token,"next":"/explore"})
    response = client.get("/explore?q=Searchable")
    assert response.status_code == 200
    assert "Searchable Application" in response.text
    assert "Create object" not in response.text
