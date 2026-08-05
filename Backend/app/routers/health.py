from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.dependencies import get_db
from app.schemas.health import HealthResponse
from app.utils.ffmpeg import ffmpeg_available

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        database_ok = True
    except Exception:
        database_ok = False

    return HealthResponse(
        status="ok" if database_ok else "degraded",
        database=database_ok,
        ffmpeg=ffmpeg_available(),
        openai_configured=settings.openai_configured,
        runway_configured=settings.runway_configured,
        storage_configured=settings.storage_configured,
        instagram_configured=settings.instagram_configured,
    )
