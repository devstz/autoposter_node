import asyncio
import ssl
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

print("Проверяем подключение к базе...")

async def check_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL не найден в окружении")
        return False

    try:
        ssl_context = ssl.create_default_context()
        engine = create_async_engine(
            db_url,
            echo=False,
            connect_args={"ssl": ssl_context},
        )
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
            print("✅ Подключение к БД успешно!")
            await conn.close()
            await conn.close()

        await engine.dispose()
        return True

    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_database())
