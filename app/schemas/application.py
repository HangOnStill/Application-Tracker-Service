from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models.enums import ApplicationStatus, WorkMode
from app.schemas.employer import EmployerRead
from app.schemas.resume_version import ResumeVersionRead


class ApplicationBase(BaseModel):
    employer_id: int
    resume_version_id: int | None = None
    role_title: str = Field(min_length=2, max_length=240)
    location: str | None = Field(default=None, max_length=200)
    work_mode: WorkMode = WorkMode.UNSPECIFIED
    term_start: date | None = None
    term_length_months: int | None = Field(default=None, ge=1, le=24)
    status: ApplicationStatus = ApplicationStatus.INTERESTED
    deadline: datetime | None = None
    application_url: HttpUrl | None = None
    language_requirement: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=8000)

    @model_validator(mode="after")
    def validate_term(self):
        if self.term_length_months is not None and self.term_start is None:
            raise ValueError("term_start is required when term_length_months is provided")
        return self


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    resume_version_id: int | None = None
    role_title: str | None = Field(default=None, min_length=2, max_length=240)
    location: str | None = Field(default=None, max_length=200)
    work_mode: WorkMode | None = None
    term_start: date | None = None
    term_length_months: int | None = Field(default=None, ge=1, le=24)
    deadline: datetime | None = None
    application_url: HttpUrl | None = None
    language_requirement: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=8000)


class ApplicationRead(BaseModel):
    id: int
    employer_id: int
    resume_version_id: int | None
    role_title: str
    location: str | None
    work_mode: WorkMode
    term_start: date | None
    term_length_months: int | None
    status: ApplicationStatus
    deadline: datetime | None
    application_url: str | None
    language_requirement: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    employer: EmployerRead
    resume_version: ResumeVersionRead | None

    model_config = ConfigDict(from_attributes=True)


class StatusHistoryCreate(BaseModel):
    status: ApplicationStatus
    note: str | None = Field(default=None, max_length=4000)


class StatusHistoryRead(BaseModel):
    id: int
    application_id: int
    status: ApplicationStatus
    note: str | None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)
