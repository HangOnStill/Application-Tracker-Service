from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401 — ensure ORM models are registered

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # For the preliminary MVP we create tables automatically.
    # Replace this with Alembic migrations before production use.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Portfolio MVP for searchable job-application tracking.",
    lifespan=lifespan,
)
app.add_exception_handler(AppError, app_error_handler)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["meta"])
def root():
    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "environment": settings.app_env}
