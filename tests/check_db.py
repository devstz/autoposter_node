import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
import os

print("Проверяем подключение к базе...")

async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL не найден в окружении")
        return

    engine = create_async_engine(
        database_url,
        echo=False,
    )

    SessionFactory = async_sessionmaker(  # type: ignore
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with SessionFactory() as session:
            await session.execute(text("SELECT 1;"))
            print("✅ Подключение к БД успешно!")
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
