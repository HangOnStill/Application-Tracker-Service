from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.application import Application
from app.models.employer import Employer
from app.models.enums import ApplicationStatus
from app.schemas.analytics import PipelineSummary, UpcomingDeadline

router = APIRouter(prefix="/analytics", tags=["analytics"])

TERMINAL_STATUSES = {
    ApplicationStatus.REJECTED,
    ApplicationStatus.WITHDRAWN,
    ApplicationStatus.CLOSED,
}
ACTIVE_STATUSES = tuple(status for status in ApplicationStatus if status not in TERMINAL_STATUSES)


@router.get("/pipeline", response_model=PipelineSummary)
def pipeline_summary(
    as_of: datetime | None = None,
    window_days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    reference = as_of or datetime.now(timezone.utc)
    if reference.utcoffset() is None:
        raise HTTPException(status_code=422, detail="as_of must include a timezone offset")
    reference = reference.astimezone(timezone.utc)
    horizon = reference + timedelta(days=window_days)

    counts = {status: 0 for status in ApplicationStatus}
    for application_status, count in db.execute(
        select(Application.status, func.count(Application.id)).group_by(Application.status)
    ):
        counts[application_status] = count

    open_deadlines = Application.status.in_(ACTIVE_STATUSES)
    overdue = db.scalar(
        select(func.count(Application.id)).where(open_deadlines, Application.deadline < reference)
    ) or 0
    due_soon = db.scalar(
        select(func.count(Application.id)).where(
            open_deadlines,
            Application.deadline >= reference,
            Application.deadline <= horizon,
        )
    ) or 0

    deadline_rows = db.execute(
        select(Application.id, Employer.name, Application.role_title, Application.deadline)
        .join(Employer)
        .where(
            open_deadlines,
            Application.deadline >= reference,
            Application.deadline <= horizon,
        )
        .order_by(Application.deadline.asc(), Application.id.asc())
        .limit(10)
    ).all()

    return PipelineSummary(
        as_of=reference,
        window_days=window_days,
        total=sum(counts.values()),
        active=sum(counts[status] for status in ACTIVE_STATUSES),
        by_status=counts,
        overdue_deadlines=overdue,
        due_soon=due_soon,
        upcoming_deadlines=[
            UpcomingDeadline(
                application_id=application_id,
                employer_name=employer_name,
                role_title=role_title,
                deadline=deadline,
            )
            for application_id, employer_name, role_title, deadline in deadline_rows
        ],
    )
