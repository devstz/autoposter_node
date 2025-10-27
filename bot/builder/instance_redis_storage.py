from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis


def create_redis_storage(DATABASE_URL: str) -> RedisStorage:
    redis_storage = RedisStorage(
        Redis.from_url(DATABASE_URL),
        key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True)
        )

    return redis_storage
