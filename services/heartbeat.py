from __future__ import annotations

import asyncio
import logging
from typing import Optional
from uuid import UUID

from infra.db.uow import SQLAlchemyUnitOfWork
from services.bot_service import BotService
from services.settings_service import SettingsService

logger = logging.getLogger(__name__)

DEFAULT_HEARTBEAT_INTERVAL = 15


async def _heartbeat_worker(token: str, stop_event: asyncio.Event) -> None:
    """Periodically update bot heartbeat timestamp while respecting shutdown event."""
    logger.info("Heartbeat worker started")

    interval: int = DEFAULT_HEARTBEAT_INTERVAL
    last_bot_id: Optional[UUID] = None

    try:
        while not stop_event.is_set():
            interval = DEFAULT_HEARTBEAT_INTERVAL
            try:
                async with SQLAlchemyUnitOfWork() as uow:
                    bot_service = BotService(uow.bot_repo)
                    settings_service = SettingsService(uow.settings_repo)

                    bot = await bot_service.get_by_token(token)
                    if bot is None:
                        logger.warning("Heartbeat worker: bot with configured token not found")
                    else:
                        last_bot_id = bot.id
                        await bot_service.update_heartbeat(bot.id)

                        settings = await settings_service.get_current()
                        if settings and settings.heartbeat_interval_s > 0:
                            interval = settings.heartbeat_interval_s
            except Exception:
                logger.exception("Heartbeat worker iteration failed")

            interval = max(1, interval)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue
    except asyncio.CancelledError:
        logger.info("Heartbeat worker cancelled")
        raise
    finally:
        if last_bot_id:
            logger.debug("Heartbeat worker stopped for bot %s", last_bot_id)
        else:
            logger.debug("Heartbeat worker stopped (bot not resolved)")
        logger.info("Heartbeat worker stopped")


__all__ = ["_heartbeat_worker"]
