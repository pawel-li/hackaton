from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import api_keys_router, auth_router, projects_router

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
        "**Authentication:** This API supports two authentication methods:\n\n"
        "- **JWT Bearer token** — Obtain a token via `POST /auth/login` and pass it as "
        "`Authorization: Bearer <token>`\n"
        "- **API Key** — Create a key via `POST /api-keys` and pass it as `X-API-Key: <key>`\n\n"
        "Both methods grant access to the same set of endpoints."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Authentication", "description": "Register, login, and get current user info."},
        {"name": "API Keys", "description": "Create and manage long-lived API keys."},
        {"name": "Projects", "description": "Create and manage projects."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(projects_router)


@app.get("/", tags=["Health"], summary="Health check")
async def root() -> dict[str, str]:
    return {"status": "ok", "docs": "/docs"}
