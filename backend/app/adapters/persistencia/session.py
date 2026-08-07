from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

#El AsyncEngine es una clase de SQLAlchemy que representa la conexión a la base de datos y permite ejecutar
#consultas de manera asíncrona.
#El pro_pre_ping=True es una opción que permite verificar la conexión a la base de datos antes de ejecutar una consulta
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=(settings.entorno == "desarrollo"),
    pool_pre_ping=True,
)

#El async_sessionmaker es una fábrica de sesiones asíncronas que permite crear instancias de AsyncSession para interactuar con la base de datos.
#El expire_on_commit=False evita que los objetos cargados en la sesión se expiren automáticamente después de un commit, y el
#autoflush=False evita que la sesión realice un flush automático antes de ejecutar una consulta.
fabrica_sessions = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)

async def obtener_sesion() -> AsyncIterator[AsyncSession, None]:
    async with fabrica_sessions() as sesion:
        yield sesion