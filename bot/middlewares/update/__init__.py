from aiogram import Dispatcher

from .uow_middleware import UoWMiddleware
from .user_middleware import UserMiddleware


def connect_update_middlewares(dp: Dispatcher):
    # Order matters: provide infra (UoW, Sessions) first, then user context
    dp.update.middleware(UoWMiddleware())
    dp.update.middleware(UserMiddleware())
