import asyncio
import ssl
import socket
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

print("Проверяем, не дублируется ли IP сервера в таблице bots...")

async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL не найден в окружении")
        return

    ssl_context = ssl.create_default_context()

    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"ssl": ssl_context},
    )

    SessionFactory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with SessionFactory() as session:
            hostname = socket.gethostname()
            server_ip = socket.gethostbyname(hostname)

            result = await session.execute(text("SELECT server_ip FROM bots;"))
            ips = [row[0] for row in result.fetchall() if row[0]]

            if server_ip in ips:
                print(f"⚠️ IP {server_ip} уже зарегистрирован в таблице bots!")
            else:
                print(f"✅ IP {server_ip} не найден в списке — всё ок.")

    except Exception as e:
        print(f"❌ Ошибка проверки IP: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
