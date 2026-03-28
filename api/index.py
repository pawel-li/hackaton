import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangum import Mangum
from app.main import app
from app.database import Base, engine

logger = logging.getLogger(__name__)


async def _init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


try:
    asyncio.run(_init_db())
    logger.info("DB tables created/verified OK")
except Exception as exc:
    logger.warning("DB init failed (tables may not exist): %s", exc)

handler = Mangum(app, lifespan="off")
