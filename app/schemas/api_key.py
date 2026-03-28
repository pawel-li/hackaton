import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    name: str

    model_config = {"json_schema_extra": {"example": {"name": "my-cli-key"}}}


class APIKeyResponse(BaseModel):
    """Returned for list/revoke — does NOT include the full key."""
    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(APIKeyResponse):
    """Returned only on creation — includes the full key (shown once)."""
    key: str
