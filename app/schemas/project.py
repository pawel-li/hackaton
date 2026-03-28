import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    date: Optional[date] = None

    model_config = {"json_schema_extra": {"example": {"name": "Wrocław Flood Monitor", "description": "Flood prediction for 2025 season", "date": "2025-06-01"}}}


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    date: Optional[date]
    created_at: datetime

    model_config = {"from_attributes": True}
