"""
FastAPI dependency that authenticates a request via either:
  - Authorization: Bearer <jwt>
  - X-API-Key: <api_key>

Returns the authenticated User ORM object or raises HTTP 401.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.api_key import APIKey
from app.models.user import User
from app.security import decode_access_token, parse_api_key, verify_api_key_secret

_bearer_scheme = HTTPBearer(auto_error=False)
_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    bearer: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
    api_key_header: Optional[str] = Security(_api_key_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    # --- Try JWT Bearer first ---
    if bearer is not None:
        try:
            user_id_str = decode_access_token(bearer.credentials)
        except JWTError:
            raise _CREDENTIALS_EXCEPTION

        result = await db.execute(select(User).where(User.id == user_id_str))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise _CREDENTIALS_EXCEPTION
        return user

    # --- Try API key ---
    if api_key_header is not None:
        parsed = parse_api_key(api_key_header)
        if parsed is None:
            raise _CREDENTIALS_EXCEPTION

        key_id, secret = parsed
        result = await db.execute(
            select(APIKey).where(APIKey.id == key_id, APIKey.is_active == True)  # noqa: E712
        )
        api_key_obj = result.scalar_one_or_none()
        if api_key_obj is None or not verify_api_key_secret(secret, api_key_obj.key_hash):
            raise _CREDENTIALS_EXCEPTION

        # Load the associated user
        user_result = await db.execute(select(User).where(User.id == api_key_obj.user_id))
        user = user_result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise _CREDENTIALS_EXCEPTION

        # Update last_used_at asynchronously (fire-and-forget in same session)
        api_key_obj.last_used_at = datetime.now(timezone.utc)
        await db.commit()

        return user

    raise _CREDENTIALS_EXCEPTION
