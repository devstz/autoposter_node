from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from common.dto import BotInitializationResult
from common.usecases import BotInitializationUseCase
from services import BotService, SettingsService, SystemService


class BotInitializationMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._initialized = False
        self._lock = asyncio.Lock()
        self._result: Optional[BotInitializationResult] = None

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not self._initialized:
            async with self._lock:
                if not self._initialized:
                    bot_service: BotService = data["bot_service"]
                    settings_service: SettingsService = data["settings_service"]
                    system_service: SystemService = data["system_service"]
                    bot = data["bot"]
                    me = await bot.get_me()  # type: ignore[attr-defined]

                    usecase = BotInitializationUseCase(bot_service, settings_service, system_service)
                    self._result = await usecase(
                        bot_id=me.id,
                        token=bot.token,  # type: ignore[attr-defined]
                        username=me.username,
                        full_name=getattr(me, "full_name", None),
                    )
                    self._initialized = True

        if self._result:
            data["bot_initialization"] = self._result

        return await handler(event, data)
