import asyncio
import logging

from bot.builder.bot_manager import BotManager
from bot.builder.dispatcher_manager import DispatcherManager

from config.app_setup import setup_application
from config.settings import get_settings

logger = logging.getLogger(__name__)


async def init_app():
    settings = get_settings()
    setup_application(settings)

    bot_manager = BotManager(settings.TOKEN)
    dp_manager = DispatcherManager(bot_manager)
    await dp_manager.setup()

    stop_event = asyncio.Event()

    async def bot_worker() -> None:
        try:
            logger.info("Starting polling...")
            await dp_manager.start_polling()
        finally:
            stop_event.set()
            logger.info("Polling stopped.")

    await asyncio.gather(
        bot_worker(),
    )
