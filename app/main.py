from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth_router, projects_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Create tables on startup (for development convenience).
    # In production, run: alembic upgrade head
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created / verified OK")
    except Exception as exc:
        logger.warning(
            "Could not connect to database on startup: %s\n"
            "Make sure PostgreSQL is running and DATABASE_URL in .env is correct.\n"
            "The server will start, but database operations will fail until the DB is available.",
            exc,
        )
    yield


app = FastAPI(
    title="Hackaton API",
    description=(
        "**Authentication:** Obtain a token via `POST /auth/login` and pass it as "
        "`Authorization: Bearer <token>`"
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Authentication", "description": "Register, login, and get current user info."},
        {"name": "Projects", "description": "Create and manage projects."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://frontend-puce-psi-37.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)


@app.get("/", tags=["Health"], summary="Health check")
async def root() -> dict[str, str]:
    return {"status": "ok", "docs": "/docs"}
