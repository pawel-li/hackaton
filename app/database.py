from collections.abc import AsyncGenerator
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _clean_db_url(url: str) -> tuple[str, dict]:
    """Strip asyncpg-incompatible query params and return (clean_url, connect_args)."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    # Remove params asyncpg doesn't understand
    needs_ssl = bool(
        params.pop("sslmode", None)
        or params.pop("ssl", None)
        or params.pop("channel_binding", None)
    )

    clean_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=clean_query))

    # Ensure scheme is postgresql+asyncpg
    clean_url = clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    clean_url = clean_url.replace("postgres://", "postgresql+asyncpg://", 1)

    connect_args = {"ssl": "require"} if needs_ssl or "neon.tech" in url else {}
    return clean_url, connect_args


_db_url, _connect_args = _clean_db_url(settings.DATABASE_URL)
engine = create_async_engine(_db_url, echo=False, connect_args=_connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

