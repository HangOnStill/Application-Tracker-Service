from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError
from app.db.session import get_db
from app.models.employer import Employer
from app.schemas.employer import EmployerCreate, EmployerRead

router = APIRouter(prefix="/employers", tags=["employers"])


@router.post("", response_model=EmployerRead, status_code=status.HTTP_201_CREATED)
def create_employer(payload: EmployerCreate, db: Session = Depends(get_db)):
    employer = Employer(
        name=payload.name.strip(),
        website=str(payload.website) if payload.website else None,
        notes=payload.notes,
    )
    db.add(employer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(f"Employer '{payload.name}' already exists")
    db.refresh(employer)
    return employer


@router.get("", response_model=list[EmployerRead])
def list_employers(
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Employer).order_by(Employer.name).limit(limit)
    if search:
        stmt = stmt.where(func.lower(Employer.name).like(f"%{search.lower()}%"))
    return list(db.scalars(stmt).all())
