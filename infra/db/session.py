import ssl
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config.settings import get_settings

settings = get_settings()

ssl_context = ssl.create_default_context()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"ssl": ssl_context},
)

SessionFactory = async_sessionmaker(  # type: ignore
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
