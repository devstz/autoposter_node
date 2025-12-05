from logging import getLogger

from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import Update
from aiogram.types import BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats, BotCommand

from bot.middlewares.update import connect_update_middlewares
from bot.routers import setup_routers

from .bot_manager import BotManager

logger = getLogger(__name__)

class DispatcherManager:
    _instance: 'DispatcherManager' = None # type: ignore

    def __init__(self, bot_manager: BotManager, storage: BaseStorage | None = None):
        if DispatcherManager._instance is not None:
            raise RuntimeError("DispatcherManager is a singleton class. Use get_instance().")
        self.bot_manager = bot_manager
        self.dispatcher = Dispatcher(storage=storage, name=__name__)
        DispatcherManager._instance = self

    @classmethod
    def get_instance(cls) -> 'DispatcherManager':
        if cls._instance is None:
            raise RuntimeError("DispatcherManager has not been initialized yet.")
        return cls._instance

    @classmethod
    def initialize(cls, bot_manager: BotManager, storage: BaseStorage | None = None) -> 'DispatcherManager':
        if cls._instance is None:
            cls(bot_manager, storage)
        return cls._instance

    async def setup(self):
        self._setup_middlewares()
        self._setup_routers()
        await self._setup_default_commands()
        logger.info("Dispatcher Manager initialized")


    async def _setup_default_commands(self):
        bot = self.bot_manager.get_bot()
        if bot:
            for lang in ["en", "ru"]:
                await bot.set_my_commands([
                    BotCommand(command='start', description=("Start the bot" if lang == "en" else "Запустить бота")),
                    BotCommand(command='help', description="Get help information" if lang == "en" else "Получить справку"),
                ], scope=BotCommandScopeAllPrivateChats(), language_code=lang)
                await bot.set_my_commands([
                    BotCommand(command='start', description='Information about the current group' if lang == "en" else 'Информация о текущей группе'),
                ], scope=BotCommandScopeAllGroupChats(), language_code=lang)
            logger.info("Default commands set up successfully")
        else:
            logger.warning("Bot instance is not available, cannot set default commands")

    async def setup_bot(self):
        await self.bot_manager.setup_bot()

    def _setup_middlewares(self):
        connect_update_middlewares(self.dispatcher)

    def _setup_routers(self):
        setup_routers(self.dispatcher)

    async def start_polling(self):
        bot = self.bot_manager.get_bot()
        if bot:
            await self.dispatcher.start_polling(bot)

    async def feed_update(self, update: Update) -> None:
        try:
            await self.dispatcher.feed_update( # type: ignore
                self.bot_manager.bot, # type: ignore
                update
            )
        except Exception as e:
            logger.error(f"Update processing error: {str(e)}")

    async def close(self) -> None:
        """Закрывает dispatcher и его ресурсы."""
        try:
            if self.dispatcher and self.dispatcher.fsm and self.dispatcher.fsm.storage:
                await self.dispatcher.fsm.storage.close()
                logger.info("Dispatcher storage closed")
        except Exception as e:
            logger.error(f"Error closing dispatcher storage: {e}", exc_info=True)
