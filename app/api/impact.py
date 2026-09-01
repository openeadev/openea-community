from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token
from app.auth.permissions import require_authenticated
from app.core.config import get_settings
from app.db.session import get_db
from app.models.metamodel import RelationshipType
from app.models.user import User
from app.repositories.object_repository import ObjectRepository
from app.services.impact_service import ImpactAnalysisError, ImpactService

router = APIRouter(prefix="/impact", include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


@router.get("/{object_id}", response_class=HTMLResponse)
def analyze_impact(
    object_id: str,
    request: Request,
    depth: int = ImpactService.DEFAULT_DEPTH,
    relationship_type: list[str] | None = Query(default=None),
    object_type: list[str] | None = Query(default=None),
    current_user: User = Depends(require_authenticated),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        analysis = ImpactService(db).analyze(
            object_id,
            depth=depth,
            relationship_type_keys=relationship_type,
            object_type_keys=object_type,
        )
    except ImpactAnalysisError as exc:
        status_code = 404 if str(exc) == "Object not found" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    relationship_types = list(
        db.scalars(
            select(RelationshipType)
            .where(RelationshipType.is_active.is_(True))
            .order_by(RelationshipType.name)
        ).all()
    )
    return templates.TemplateResponse(
        request=request,
        name="impact/index.html",
        context={
            "settings": get_settings(),
            "current_user": current_user,
            "csrf_token": get_csrf_token(request),
            "analysis": analysis,
            "direct_groups": analysis.grouped(direct=True),
            "indirect_groups": analysis.grouped(direct=False),
            "graph": analysis.graph_payload(),
            "object_types": ObjectRepository(db).list_object_types(),
            "relationship_types": relationship_types,
            "max_depth": ImpactService.MAX_DEPTH,
        },
    )
