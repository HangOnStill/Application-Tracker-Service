from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ApplicationStatus, WorkMode


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("employers.id", ondelete="RESTRICT"), index=True)
    resume_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    role_title: Mapped[str] = mapped_column(String(240), index=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    work_mode: Mapped[WorkMode] = mapped_column(Enum(WorkMode), default=WorkMode.UNSPECIFIED, index=True)
    term_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    term_length_months: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.INTERESTED, index=True
    )
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    application_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    language_requirement: Mapped[str | None] = mapped_column(String(240), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    employer = relationship("Employer", back_populates="applications")
    resume_version = relationship("ResumeVersion", back_populates="applications")
    status_history = relationship(
        "StatusHistory", back_populates="application", cascade="all, delete-orphan", order_by="StatusHistory.changed_at"
    )
