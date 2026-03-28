import json
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, model_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com", "password": "strongpassword"}}}

    @model_validator(mode="before")
    @classmethod
    def _coerce_string_body(cls, data):
        if isinstance(data, (str, bytes)):
            return json.loads(data)
        return data


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
