from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ResumeVersionCreate(BaseModel):
    label: str = Field(min_length=2, max_length=160)
    filename: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=4000)


class ResumeVersionRead(BaseModel):
    id: int
    label: str
    filename: str | None
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
