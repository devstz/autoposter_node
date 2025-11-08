from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from infra.db.uow import SQLAlchemyUnitOfWork
from services.bot_service import BotService
from services.settings_service import SettingsService
from services.git_repository import GitRepositoryTracker, GitRepositoryError
from config.settings import get_settings

logger = logging.getLogger(__name__)

DEFAULT_HEARTBEAT_INTERVAL = 15


async def _heartbeat_worker(token: str, stop_event: asyncio.Event) -> None:
    """Periodically update bot heartbeat timestamp while respecting shutdown event."""
    logger.info("Heartbeat worker started")

    interval: int = DEFAULT_HEARTBEAT_INTERVAL
    last_bot_id: Optional[UUID] = None
    settings = get_settings()
    loop = asyncio.get_running_loop()

    git_tracker = GitRepositoryTracker(
        repo_path=settings.base_dir,
        remote=settings.GIT_REMOTE,
        branch=settings.GIT_BRANCH,
    )
    git_check_interval = max(0, settings.GIT_CHECK_INTERVAL_S)
    next_git_check_at = 0.0

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

                        runtime_settings = await settings_service.get_current()
                        if runtime_settings and runtime_settings.heartbeat_interval_s > 0:
                            interval = runtime_settings.heartbeat_interval_s

                        should_check_repo = git_check_interval > 0 and loop.time() >= next_git_check_at
                        if should_check_repo:
                            next_git_check_at = loop.time() + git_check_interval
                            try:
                                status = await asyncio.to_thread(git_tracker.check_status)
                            except GitRepositoryError:
                                logger.warning("Git revision check failed", exc_info=True)
                            else:
                                await bot_service.update_fields(
                                    bot.id,
                                    tracked_branch=status.branch,
                                    current_commit_hash=status.local_commit,
                                    latest_available_commit_hash=status.remote_commit,
                                    commits_behind=status.commits_behind,
                                    last_update_check_at=status.checked_at,
                                )
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
