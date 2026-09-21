from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.application import Application
from app.models.employer import Employer
from app.models.enums import ApplicationStatus
from app.models.resume_version import ResumeVersion
from app.models.status_history import StatusHistory
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListParams,
    ApplicationPage,
    ApplicationRead,
    ApplicationUpdate,
    StatusHistoryCreate,
    StatusHistoryRead,
)
from app.schemas.common import DeleteResponse
from app.services.applications import search_applications

router = APIRouter(prefix="/applications", tags=["applications"])


def get_application_or_404(db: Session, application_id: int) -> Application:
    stmt = (
        select(Application)
        .where(Application.id == application_id)
        .options(selectinload(Application.employer), selectinload(Application.resume_version))
    )
    application = db.scalar(stmt)
    if not application:
        raise NotFoundError(f"Application {application_id} was not found")
    return application


def require_relations(db: Session, employer_id: int, resume_version_id: int | None) -> None:
    if not db.get(Employer, employer_id):
        raise NotFoundError(f"Employer {employer_id} was not found")
    if resume_version_id is not None and not db.get(ResumeVersion, resume_version_id):
        raise NotFoundError(f"Resume version {resume_version_id} was not found")


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    require_relations(db, payload.employer_id, payload.resume_version_id)
    data = payload.model_dump()
    if payload.application_url:
        data["application_url"] = str(payload.application_url)
    application = Application(**data)
    db.add(application)
    db.flush()
    db.add(StatusHistory(application_id=application.id, status=application.status, note="Application record created"))
    db.commit()
    return get_application_or_404(db, application.id)


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    params: Annotated[ApplicationListParams, Query()],
    db: Session = Depends(get_db),
):
    items, _ = search_applications(db, **params.model_dump())
    return items


@router.get("/page", response_model=ApplicationPage)
def page_applications(
    params: Annotated[ApplicationListParams, Query()],
    db: Session = Depends(get_db),
):
    items, total = search_applications(db, **params.model_dump())
    return ApplicationPage(
        items=items,
        total=total,
        limit=params.limit,
        offset=params.offset,
        has_more=params.offset + len(items) < total,
    )


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(application_id: int, db: Session = Depends(get_db)):
    return get_application_or_404(db, application_id)


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(application_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db)):
    application = get_application_or_404(db, application_id)
    changes = payload.model_dump(exclude_unset=True)

    if "resume_version_id" in changes and changes["resume_version_id"] is not None:
        if not db.get(ResumeVersion, changes["resume_version_id"]):
            raise NotFoundError(f"Resume version {changes['resume_version_id']} was not found")
    if "application_url" in changes and changes["application_url"] is not None:
        changes["application_url"] = str(changes["application_url"])

    for key, value in changes.items():
        setattr(application, key, value)

    if application.term_length_months is not None and application.term_start is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="term_start is required when term_length_months is provided")

    db.commit()
    return get_application_or_404(db, application_id)


@router.delete("/{application_id}", response_model=DeleteResponse)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    application = get_application_or_404(db, application_id)
    db.delete(application)
    db.commit()
    return DeleteResponse(id=application_id)


@router.post("/{application_id}/status-history", response_model=StatusHistoryRead, status_code=status.HTTP_201_CREATED)
def add_status_history(
    application_id: int,
    payload: StatusHistoryCreate,
    db: Session = Depends(get_db),
):
    application = get_application_or_404(db, application_id)
    application.status = payload.status
    history = StatusHistory(application_id=application_id, status=payload.status, note=payload.note)
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


@router.get("/{application_id}/status-history", response_model=list[StatusHistoryRead])
def list_status_history(application_id: int, db: Session = Depends(get_db)):
    get_application_or_404(db, application_id)
    stmt = (
        select(StatusHistory)
        .where(StatusHistory.application_id == application_id)
        .order_by(StatusHistory.changed_at.desc(), StatusHistory.id.desc())
    )
    return list(db.scalars(stmt).all())
