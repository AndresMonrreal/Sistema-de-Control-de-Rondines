from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=(settings.entorno == "desarrollo"),
    pool_pre_ping=True,
)

fabrica_sessions = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)

async def obtener_sesion() -> AsyncIterator[AsyncSession, None]:
    async with fabrica_sessions() as sesion:
        yield sesion