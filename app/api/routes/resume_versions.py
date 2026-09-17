from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError
from app.db.session import get_db
from app.models.resume_version import ResumeVersion
from app.schemas.resume_version import ResumeVersionCreate, ResumeVersionRead

router = APIRouter(prefix="/resume-versions", tags=["resume versions"])


@router.post("", response_model=ResumeVersionRead, status_code=status.HTTP_201_CREATED)
def create_resume_version(payload: ResumeVersionCreate, db: Session = Depends(get_db)):
    version = ResumeVersion(label=payload.label.strip(), filename=payload.filename, notes=payload.notes)
    db.add(version)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(f"Resume version '{payload.label}' already exists")
    db.refresh(version)
    return version


@router.get("", response_model=list[ResumeVersionRead])
def list_resume_versions(db: Session = Depends(get_db)):
    stmt = select(ResumeVersion).order_by(ResumeVersion.created_at.desc())
    return list(db.scalars(stmt).all())
