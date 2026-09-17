from fastapi import APIRouter
from app.api.routes import applications, employers, resume_versions

api_router = APIRouter()
api_router.include_router(employers.router)
api_router.include_router(resume_versions.router)
api_router.include_router(applications.router)
