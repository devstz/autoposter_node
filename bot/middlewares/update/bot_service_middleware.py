from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from infra.db.uow import SQLAlchemyUnitOfWork
from services import BotService


class BotServiceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        uow: SQLAlchemyUnitOfWork = data["uow"]
        data["bot_service"] = BotService(uow.bot_repo)
        return await handler(event, data)
