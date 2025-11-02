from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from services import SystemService


class SystemServiceMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._service = SystemService()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["system_service"] = self._service
        return await handler(event, data)
