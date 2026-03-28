import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginResponse, RegisterRequest, UserResponse
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def _parse_body(request: Request) -> dict:
    """Parse request body regardless of Content-Type header."""
    raw = await request.body()
    try:
        return json.loads(raw)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid JSON body")


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(request: Request, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    data = await _parse_body(request)
    body = RegisterRequest.model_validate(data)

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return LoginResponse(access_token=token)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login with email and password",
)
async def login(request: Request, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    data = await _parse_body(request)
    body = RegisterRequest.model_validate(data)

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = create_access_token(user.id)
    return LoginResponse(access_token=token)


@router.get("/me", response_model=UserResponse, summary="Get current user info")
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
