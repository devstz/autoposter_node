from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config.settings import get_settings

settings = get_settings()


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)

SessionFactory = async_sessionmaker(  # type: ignore
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def dispose_engine() -> None:
    """Закрывает все соединения с базой данных."""
    await engine.dispose()
