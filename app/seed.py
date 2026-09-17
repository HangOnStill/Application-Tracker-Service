from datetime import date, datetime, timezone
from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.application import Application
from app.models.employer import Employer
from app.models.enums import ApplicationStatus, WorkMode
from app.models.resume_version import ResumeVersion
from app.models.status_history import StatusHistory


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(Employer).limit(1)):
            print("Seed skipped: database already contains employer records.")
            return

        employer = Employer(name="Northstar Systems", website="https://example.com")
        resume = ResumeVersion(label="Backend / Data Resume v1", filename="synthetic_resume_v1.pdf")
        db.add_all([employer, resume])
        db.flush()

        application = Application(
            employer_id=employer.id,
            resume_version_id=resume.id,
            role_title="Software Developer Intern",
            location="Ottawa, ON",
            work_mode=WorkMode.HYBRID,
            term_start=date(2027, 1, 11),
            term_length_months=8,
            status=ApplicationStatus.APPLIED,
            deadline=datetime(2026, 10, 15, 23, 59, tzinfo=timezone.utc),
            application_url="https://example.com/jobs/123",
            language_requirement="English",
            notes="Synthetic demonstration record only.",
        )
        db.add(application)
        db.flush()
        db.add(StatusHistory(application_id=application.id, status=ApplicationStatus.APPLIED, note="Synthetic seed record"))
        db.commit()
        print("Created synthetic employer, resume version, application, and status-history records.")


if __name__ == "__main__":
    main()
