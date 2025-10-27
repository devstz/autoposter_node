from logging import getLogger
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from infra.db.models import User

logger = getLogger(__name__)


class AdminCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        user: User = data['user']

        if not user.is_superuser:
            return

        return await handler(event, data)
