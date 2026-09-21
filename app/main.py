from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler
from app.core.security import configured_api_key
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401 — ensure ORM models are registered

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().app_env.lower() in {"production", "prod"} and configured_api_key() is None:
        raise RuntimeError("API_KEY must be configured when APP_ENV=production")
    # Automatic table creation is still intended for local/demo use only.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Job-application tracking with protected API access, search, pagination, and pipeline analytics.",
    lifespan=lifespan,
)
app.add_exception_handler(AppError, app_error_handler)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["meta"])
def root():
    return {
        "service": settings.app_name,
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "environment": settings.app_env}
