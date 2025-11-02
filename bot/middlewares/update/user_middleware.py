from logging import getLogger
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from infra.db.models import User as UserDB
from infra.db.uow import SQLAlchemyUnitOfWork

logger = getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        uow: SQLAlchemyUnitOfWork = data['uow']
        user: User = data['event_from_user']

        if user.is_bot:
            return

        tg_user = await uow.user_repo.get(user.id)
        if tg_user is None:
            tg_user = await uow.user_repo.add(
                UserDB(
                    user_id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                )
            )
        else:
            if tg_user.full_name != user.full_name or tg_user.username != user.username:
                if tg_user.full_name != user.full_name:
                    tg_user.full_name = user.full_name
                if tg_user.username != user.username:
                    tg_user.username = user.username
                tg_user = await uow.user_repo.update(tg_user)

        data.update(user=tg_user)

        return await handler(event, data)
