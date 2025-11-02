from aiogram import Dispatcher

from .uow_middleware import UoWMiddleware
from .settings_service_middleware import SettingsServiceMiddleware
from .bot_service_middleware import BotServiceMiddleware
from .group_service_middleware import GroupServiceMiddleware
from .post_service_middleware import PostServiceMiddleware
from .post_attempt_service_middleware import PostAttemptServiceMiddleware
from .user_service_middleware import UserServiceMiddleware
from .system_service_middleware import SystemServiceMiddleware
from .ux_middleware import UXMiddleware
from .bot_initialization_middleware import BotInitializationMiddleware
from .user_middleware import UserMiddleware


def connect_update_middlewares(dp: Dispatcher) -> None:
    # Order matters: first start the UoW, then expose service facades, then resolve user context
    dp.update.middleware(UoWMiddleware())
    dp.update.middleware(SettingsServiceMiddleware())
    dp.update.middleware(BotServiceMiddleware())
    dp.update.middleware(GroupServiceMiddleware())
    dp.update.middleware(PostServiceMiddleware())
    dp.update.middleware(PostAttemptServiceMiddleware())
    dp.update.middleware(UserServiceMiddleware())
    dp.update.middleware(SystemServiceMiddleware())
    dp.update.middleware(UXMiddleware())
    dp.update.middleware(BotInitializationMiddleware())
    dp.update.middleware(UserMiddleware())
