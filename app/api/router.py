from fastapi import APIRouter, Depends
from app.api.routes import applications, analytics, employers, resume_versions
from app.core.security import require_api_key

api_router = APIRouter(dependencies=[Depends(require_api_key)])
api_router.include_router(employers.router)
api_router.include_router(resume_versions.router)
api_router.include_router(applications.router)
api_router.include_router(analytics.router)
