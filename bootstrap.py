from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
from config.settings import Config
from bot.builder.bot_manager import BotManager
from bot.builder.dispatcher_manager import DispatcherManager
from config.app_setup import setup_application
from config.settings import get_settings
from services.heartbeat import _heartbeat_worker

from services.posting import PostingRunner

logger = logging.getLogger(__name__)


async def _start_polling(dp_manager: DispatcherManager, stop_event: asyncio.Event) -> None:
    logger.info("Starting polling...")
    try:
        await dp_manager.start_polling()
    finally:
        logger.info("Polling stopped.")
        stop_event.set()


def _install_signal_handlers(stop: asyncio.Event, loop: asyncio.AbstractEventLoop) -> None:
    def _handler() -> None:
        if not stop.is_set():
            logger.info("Shutdown signal received. Stopping gracefully...")
            stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _handler)

async def _init_posting_runner(settings: Config):
    posting_runner = PostingRunner(token=settings.TOKEN)
    return posting_runner


async def init_app() -> None:
    """Bootstrap application, run dispatcher polling and gracefull shutdown."""
    settings = get_settings()
    setup_application(settings)

    bot_manager = BotManager(settings.TOKEN)
    dp_manager = DispatcherManager(bot_manager)
    posting_runner = await _init_posting_runner(settings)
    await dp_manager.setup()

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    _install_signal_handlers(stop_event, loop)

    polling_task = asyncio.create_task(_start_polling(dp_manager, stop_event), name="bot-polling")
    heartbeat_task = asyncio.create_task(
        _heartbeat_worker(settings.TOKEN, stop_event),
        name="bot-heartbeat",
    )
    posting_task = asyncio.create_task(
        posting_runner.start(stop_event),
        name="posting-runner",
    )

    await stop_event.wait()

    polling_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await polling_task

    heartbeat_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await heartbeat_task
    
    posting_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await posting_task

    logger.info("Application shutdown complete.")


__all__ = ["init_app"]
