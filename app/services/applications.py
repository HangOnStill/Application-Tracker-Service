from datetime import datetime
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.application import Application
from app.models.employer import Employer
from app.models.enums import ApplicationStatus, WorkMode


def literal_contains(value: str) -> str:
    escaped = value.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def application_query(
    *,
    search: str | None = None,
    status: ApplicationStatus | None = None,
    work_mode: WorkMode | None = None,
    employer_id: int | None = None,
    location: str | None = None,
    term_length_months: int | None = None,
    deadline_before: datetime | None = None,
    deadline_after: datetime | None = None,
):
    stmt = select(Application).join(Employer)

    if search:
        needle = literal_contains(search)
        stmt = stmt.where(
            or_(
                func.lower(Application.role_title).like(needle, escape="\\"),
                func.lower(Employer.name).like(needle, escape="\\"),
                func.lower(func.coalesce(Application.location, "")).like(needle, escape="\\"),
            )
        )
    if status:
        stmt = stmt.where(Application.status == status)
    if work_mode:
        stmt = stmt.where(Application.work_mode == work_mode)
    if employer_id is not None:
        stmt = stmt.where(Application.employer_id == employer_id)
    if location:
        stmt = stmt.where(func.lower(func.coalesce(Application.location, "")).like(literal_contains(location), escape="\\"))
    if term_length_months is not None:
        stmt = stmt.where(Application.term_length_months == term_length_months)
    if deadline_before:
        stmt = stmt.where(Application.deadline <= deadline_before)
    if deadline_after:
        stmt = stmt.where(Application.deadline >= deadline_after)
    return stmt


def search_applications(
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
    sort_by: Literal["updated_at", "created_at", "deadline", "role_title"] = "updated_at",
    sort_order: Literal["asc", "desc"] = "desc",
) -> tuple[list[Application], int]:
    filtered = application_query(
        search=search,
        status=status,
        work_mode=work_mode,
        employer_id=employer_id,
        location=location,
        term_length_months=term_length_months,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
    )
    total = db.scalar(select(func.count()).select_from(filtered.subquery())) or 0

    sort_columns = {
        "updated_at": Application.updated_at,
        "created_at": Application.created_at,
        "deadline": Application.deadline,
        "role_title": Application.role_title,
    }
    column = sort_columns[sort_by]
    direction = column.asc() if sort_order == "asc" else column.desc()
    if sort_by == "deadline":
        direction = direction.nulls_last()
    tie_breaker = Application.id.asc() if sort_order == "asc" else Application.id.desc()

    stmt = (
        filtered.options(selectinload(Application.employer), selectinload(Application.resume_version))
        .order_by(direction, tie_breaker)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt).all()), total
