from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Chat
from aiogram.enums.chat_type import ChatType

from infra.db.uow import get_uow
import logging

class UoWMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:

        logging.info(f'{', '.join(data.keys())}')
    
        if event.chat.type != ChatType.PRIVATE.value:
            return

        uow = get_uow()
        async with uow:
            data['uow'] = uow
            result = await handler(event, data)

        return result 
