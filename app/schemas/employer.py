from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class EmployerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    website: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=4000)


class EmployerRead(BaseModel):
    id: int
    name: str
    website: str | None
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
