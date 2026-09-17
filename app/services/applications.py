from datetime import datetime
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.application import Application
from app.models.employer import Employer
from app.models.enums import ApplicationStatus, WorkMode


def application_query():
    return (
        select(Application)
        .join(Employer)
        .options(selectinload(Application.employer), selectinload(Application.resume_version))
    )


def filter_applications(
    db: Session,
    *,
    search: str | None = None,
    status: ApplicationStatus | None = None,
    work_mode: WorkMode | None = None,
    employer_id: int | None = None,
    location: str | None = None,
    term_length_months: int | None = None,
    deadline_before: datetime | None = None,
    deadline_after: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Application]:
    stmt = application_query()

    if search:
        needle = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Application.role_title).like(needle),
                func.lower(Employer.name).like(needle),
                func.lower(func.coalesce(Application.location, "")).like(needle),
            )
        )
    if status:
        stmt = stmt.where(Application.status == status)
    if work_mode:
        stmt = stmt.where(Application.work_mode == work_mode)
    if employer_id:
        stmt = stmt.where(Application.employer_id == employer_id)
    if location:
        stmt = stmt.where(func.lower(func.coalesce(Application.location, "")).like(f"%{location.lower()}%"))
    if term_length_months:
        stmt = stmt.where(Application.term_length_months == term_length_months)
    if deadline_before:
        stmt = stmt.where(Application.deadline <= deadline_before)
    if deadline_after:
        stmt = stmt.where(Application.deadline >= deadline_after)

    stmt = stmt.order_by(Application.updated_at.desc(), Application.id.desc()).offset(offset).limit(limit)
    return list(db.scalars(stmt).unique().all())
