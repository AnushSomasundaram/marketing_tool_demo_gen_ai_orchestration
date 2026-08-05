from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.background.recovery import run_startup_recovery
from app.config import get_settings
from app.database import SessionLocal
from app.logging_config import configure_logging, get_logger
from app.models.user import DEV_USER_ID, User
from app.routers import assets, campaigns, captions, health, instagram

configure_logging()
logger = get_logger(__name__)

STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage"


def _ensure_dev_user() -> None:
    db = SessionLocal()
    try:
        if db.get(User, DEV_USER_ID) is None:
            db.add(User(id=DEV_USER_ID, email="dev@campaignstudio.local", display_name="Dev User"))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    _ensure_dev_user()
    run_startup_recovery()
    logger.info("Campaign Studio API started.")
    yield
    logger.info("Campaign Studio API shutting down.")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="API-ready backend for Campaign Studio, an AI social media campaign generator.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for sub in ("uploads", "generated", "composed"):
        (STORAGE_ROOT / sub).mkdir(parents=True, exist_ok=True)
    app.mount("/storage", StaticFiles(directory=str(STORAGE_ROOT)), name="storage")

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(campaigns.router, prefix=settings.api_prefix)
    app.include_router(captions.router, prefix=settings.api_prefix)
    app.include_router(assets.router, prefix=settings.api_prefix)
    app.include_router(instagram.router, prefix=settings.api_prefix)

    return app


app = create_app()
