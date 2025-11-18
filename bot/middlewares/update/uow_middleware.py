from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Chat
from aiogram.enums.chat_type import ChatType

from infra.db.uow import get_uow


class UoWMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:

        chat: Chat = data['event_from_chat']
        

        uow = get_uow()
        async with uow:
            data['uow'] = uow
            result = await handler(event, data)

        return result 
