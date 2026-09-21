from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ApplicationStatus


class UpcomingDeadline(BaseModel):
    application_id: int
    employer_name: str
    role_title: str
    deadline: datetime


class PipelineSummary(BaseModel):
    as_of: datetime
    window_days: int
    total: int
    active: int
    by_status: dict[ApplicationStatus, int]
    overdue_deadlines: int
    due_soon: int
    upcoming_deadlines: list[UpcomingDeadline]
