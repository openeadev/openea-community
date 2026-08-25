from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.session import check_database_ready

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse, include_in_schema=False)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", version=settings.app_version)


@router.get("/health/ready", response_model=HealthResponse, include_in_schema=False)
def readiness(response: Response) -> HealthResponse:
    settings = get_settings()
    try:
        check_database_ready()
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="not_ready", version=settings.app_version)
    return HealthResponse(status="ready", version=settings.app_version)
