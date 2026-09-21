from datetime import date, datetime
from typing import Literal
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
        if self.deadline is not None and self.deadline.utcoffset() is None:
            raise ValueError("deadline must include a timezone offset")
        return self


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

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

    @model_validator(mode="after")
    def required_fields_cannot_be_cleared(self):
        for field in ("role_title", "work_mode"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        if self.deadline is not None and self.deadline.utcoffset() is None:
            raise ValueError("deadline must include a timezone offset")
        return self


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


class ApplicationListParams(BaseModel):
    search: str | None = Field(default=None, max_length=120)
    status: ApplicationStatus | None = None
    work_mode: WorkMode | None = None
    employer_id: int | None = Field(default=None, gt=0)
    location: str | None = Field(default=None, max_length=120)
    term_length_months: int | None = Field(default=None, ge=1, le=24)
    deadline_before: datetime | None = None
    deadline_after: datetime | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: Literal["updated_at", "created_at", "deadline", "role_title"] = "updated_at"
    sort_order: Literal["asc", "desc"] = "desc"

    @model_validator(mode="after")
    def validate_deadline_window(self):
        for value in (self.deadline_after, self.deadline_before):
            if value is not None and value.utcoffset() is None:
                raise ValueError("deadline filters must include a timezone offset")
        if self.deadline_after and self.deadline_before and self.deadline_after > self.deadline_before:
            raise ValueError("deadline_after must not be later than deadline_before")
        return self


class ApplicationPage(BaseModel):
    items: list[ApplicationRead]
    total: int
    limit: int
    offset: int
    has_more: bool


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
