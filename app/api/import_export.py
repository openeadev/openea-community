from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token, validate_csrf
from app.auth.permissions import ARCHITECT, ARCHITECTURE_ADMIN, require_authenticated, require_roles
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.object_repository import ObjectRepository
from app.services.import_service import ImportService, RelationshipImportService
from app.services.search_service import SearchService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")
import_writer = require_roles(ARCHITECTURE_ADMIN, ARCHITECT)


def context(request: Request, current_user: User) -> dict[str, object]:
    return {
        "settings": get_settings(),
        "current_user": current_user,
        "csrf_token": get_csrf_token(request),
    }


@router.get("/imports", response_class=HTMLResponse)
def imports_page(
    request: Request,
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="imports/index.html",
        context={**context(request, current_user), "object_types": ObjectRepository(db).list_object_types()},
    )


@router.post("/imports/upload")
async def upload_import(
    request: Request,
    object_type_key: str = Form(...),
    csv_file: UploadFile = File(...),
    csrf_token: str = Form(...),
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    if not (csv_file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Upload must be a .csv file")
    try:
        batch = ImportService(db).create_batch(
            object_type_key=object_type_key,
            filename=csv_file.filename or "import.csv",
            content=await csv_file.read(),
            actor=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(f"/imports/{batch.id}/map", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/imports/{batch_id}/map", response_class=HTMLResponse)
def map_import(
    batch_id: str,
    request: Request,
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ImportService(db)
    batch = service.get_batch(batch_id)
    if batch is None or batch.import_kind != "object":
        raise HTTPException(status_code=404, detail="Object import batch not found")
    return templates.TemplateResponse(
        request=request,
        name="imports/map.html",
        context={
            **context(request, current_user),
            "batch": batch,
            "allowed_fields": service.allowed_fields(batch.object_type_key),
        },
    )


@router.post("/imports/{batch_id}/validate")
async def validate_import(
    batch_id: str,
    request: Request,
    csrf_token: str = Form(...),
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    service = ImportService(db)
    batch = service.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch not found")
    form = await request.form()
    mapping = {
        header: str(form.get(f"map::{header}") or "")
        for header in batch.headers
        if str(form.get(f"map::{header}") or "")
    }
    try:
        service.validate(batch, mapping)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(f"/imports/{batch.id}/preview", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/imports/{batch_id}/preview", response_class=HTMLResponse)
def preview_import(
    batch_id: str,
    request: Request,
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    batch = ImportService(db).get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch not found")
    return templates.TemplateResponse(
        request=request,
        name="imports/preview.html",
        context={**context(request, current_user), "batch": batch, "preview": batch.preview or {}},
    )


@router.post("/imports/{batch_id}/commit")
def commit_import(
    batch_id: str,
    request: Request,
    csrf_token: str = Form(...),
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    service = ImportService(db)
    batch = service.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch not found")
    try:
        service.commit(batch, actor=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(f"/imports/{batch.id}/preview", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/imports/relationships/upload")
async def upload_relationship_import(
    request: Request,
    csv_file: UploadFile = File(...),
    csrf_token: str = Form(...),
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    if not (csv_file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Upload must be a .csv file")
    try:
        batch = RelationshipImportService(db).create_batch(
            filename=csv_file.filename or "relationships.csv",
            content=await csv_file.read(),
            actor=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(f"/imports/relationships/{batch.id}/map", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/imports/relationships/{batch_id}/map", response_class=HTMLResponse)
def map_relationship_import(
    batch_id: str,
    request: Request,
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = RelationshipImportService(db)
    batch = service.get_batch(batch_id)
    if batch is None or batch.import_kind != "relationship":
        raise HTTPException(status_code=404, detail="Relationship import batch not found")
    return templates.TemplateResponse(
        request=request,
        name="imports/relationship_map.html",
        context={**context(request, current_user), "batch": batch, "allowed_fields": service.allowed_fields()},
    )


@router.post("/imports/relationships/{batch_id}/validate")
async def validate_relationship_import(
    batch_id: str,
    request: Request,
    csrf_token: str = Form(...),
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    service = RelationshipImportService(db)
    batch = service.get_batch(batch_id)
    if batch is None or batch.import_kind != "relationship":
        raise HTTPException(status_code=404, detail="Relationship import batch not found")
    form = await request.form()
    mapping = {
        header: str(form.get(f"map::{header}") or "")
        for header in batch.headers
        if str(form.get(f"map::{header}") or "")
    }
    try:
        service.validate(batch, mapping)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(f"/imports/relationships/{batch.id}/preview", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/imports/relationships/{batch_id}/preview", response_class=HTMLResponse)
def preview_relationship_import(
    batch_id: str,
    request: Request,
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    batch = RelationshipImportService(db).get_batch(batch_id)
    if batch is None or batch.import_kind != "relationship":
        raise HTTPException(status_code=404, detail="Relationship import batch not found")
    return templates.TemplateResponse(
        request=request,
        name="imports/relationship_preview.html",
        context={**context(request, current_user), "batch": batch, "preview": batch.preview or {}},
    )


@router.post("/imports/relationships/{batch_id}/commit")
def commit_relationship_import(
    batch_id: str,
    request: Request,
    csrf_token: str = Form(...),
    current_user: User = Depends(import_writer),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    service = RelationshipImportService(db)
    batch = service.get_batch(batch_id)
    if batch is None or batch.import_kind != "relationship":
        raise HTTPException(status_code=404, detail="Relationship import batch not found")
    try:
        service.commit(batch, actor=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(f"/imports/relationships/{batch.id}/preview", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/exports/objects.csv")
def export_objects_csv(
    q: str | None = None,
    object_type: str | None = None,
    record_status: str | None = None,
    criticality: str | None = None,
    current_user: User = Depends(require_authenticated),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    del current_user
    result = SearchService(db).search(
        query=q,
        object_type_key=object_type,
        record_status=record_status,
        criticality=criticality,
        per_page=100,
        page=1,
    )
    # CSV export must honor filters across the whole result set, not only one UI page.
    items = result.items
    if result.total > len(items):
        items = SearchService(db).search(
            query=q,
            object_type_key=object_type,
            record_status=record_status,
            criticality=criticality,
            per_page=min(result.total, 100),
            page=1,
        ).items
        # SearchService deliberately caps page size; fetch additional pages.
        page = 2
        while len(items) < result.total:
            next_page = SearchService(db).search(
                query=q,
                object_type_key=object_type,
                record_status=record_status,
                criticality=criticality,
                per_page=100,
                page=page,
            )
            if not next_page.items:
                break
            items.extend(next_page.items)
            page += 1
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "object_type", "name", "description", "record_status", "governance_status", "lifecycle_stage", "criticality", "source", "confidence", "aliases", "tags"])
    for obj in items:
        writer.writerow([
            obj.id,
            obj.object_type.key,
            obj.name,
            obj.description,
            obj.record_status,
            obj.governance_status or "",
            obj.lifecycle_stage or "",
            obj.criticality or "",
            obj.source or "",
            obj.confidence or "",
            ", ".join(alias.alias for alias in obj.aliases),
            ", ".join(tag.name for tag in obj.tags),
        ])
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="openea-objects.csv"'},
    )
