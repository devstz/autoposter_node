from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from infra.db.uow import SQLAlchemyUnitOfWork
from services.bot_service import BotService
from services.settings_service import SettingsService
from services.user_service import UserService
from services.system_service import SystemService
from services.notification_service import NotificationService
from services.git_repository import GitRepositoryTracker, GitRepositoryError
from bot.builder.instance_bot import create_bot
from config.settings import get_settings
from common.usecases import BotInitializationUseCase

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
                        logger.warning("Heartbeat worker: bot with configured token not found, attempting to create bot")
                        try:
                            # Создаем Bot через aiogram для получения информации
                            tg_bot = create_bot(token)
                            me = await tg_bot.get_me()
                            
                            # Создаем сервисы для use case
                            system_service = SystemService()
                            usecase = BotInitializationUseCase(
                                bot_service=bot_service,
                                settings_service=settings_service,
                                system_service=system_service,
                            )
                            
                            # Создаем бота через use case
                            result = await usecase(
                                bot_id=me.id,
                                token=token,
                                username=me.username,
                                full_name=getattr(me, "full_name", None),
                            )
                            
                            # Закрываем сессию бота
                            await tg_bot.session.close()
                            
                            # Получаем созданного бота
                            bot = await bot_service.get_by_token(token)
                            if bot:
                                logger.info(f"Bot successfully created in database: bot_id={bot.id}, username={me.username}")
                            else:
                                logger.error("Bot was created but could not be retrieved from database")
                        except Exception as e:
                            logger.error(f"Failed to create bot in heartbeat worker: {e}", exc_info=True)
                    
                    # Если бот существует (был найден или только что создан), продолжаем обработку
                    if bot is not None:
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
                                
                                # Reload bot to get updated force_update flag
                                updated_bot = await bot_service.get(bot.id)
                                if updated_bot is None:
                                    logger.warning("Failed to reload bot after git status update")
                                    continue
                                
                                # Check if force_update is set
                                if updated_bot.force_update:
                                    # Check if version is up to date
                                    is_up_to_date = (
                                        status.commits_behind == 0
                                        and status.local_commit
                                        and status.remote_commit
                                        and status.local_commit == status.remote_commit
                                    )
                                    
                                    # Log current status
                                    if is_up_to_date:
                                        logger.info(
                                            f"Force update requested for bot {updated_bot.id}, "
                                            f"bot is already up-to-date, executing update command"
                                        )
                                    else:
                                        logger.info(
                                            f"Force update requested for bot {updated_bot.id}, "
                                            f"bot is {status.commits_behind} commit(s) behind, "
                                            f"executing update command (includes git pull)"
                                        )
                                    
                                    # Clear force_update flag BEFORE executing update command
                                    # This prevents infinite restart loop since the command restarts the service
                                    await bot_service.clear_force_update(updated_bot.id)
                                    
                                    # CRITICAL: Commit changes immediately to ensure flag is cleared in DB
                                    # before the service restarts. Without this, the transaction will rollback
                                    # and the bot will restart in an infinite loop.
                                    await uow.commit()
                                    logger.info(f"Cleared and committed force_update flag for bot {updated_bot.id}")
                                    
                                    # Execute update command (includes git pull + restart)
                                    update_result = await asyncio.to_thread(SystemService.execute_update_command)
                                    
                                    if update_result.success:
                                        logger.info(f"Update completed successfully for bot {updated_bot.id}")
                                    else:
                                        # Send error notification to admins
                                        try:
                                            user_service = UserService(uow.user_repo)
                                            admins = await user_service.search(is_superuser=True, limit=100)
                                            admin_ids = [admin.user_id for admin in admins]
                                            
                                            if admin_ids:
                                                notification_bot = create_bot(token)
                                                notification_service = NotificationService(notification_bot)
                                                
                                                # Get bot model for notification
                                                from infra.db.models import Bot as BotModel
                                                bot_model = await uow.bot_repo.get(updated_bot.id)
                                                
                                                if bot_model:
                                                    await notification_service.notify_update_error(
                                                        bot=bot_model,
                                                        error_details=f"Update command failed with exit code {update_result.exit_code}",
                                                        exit_code=update_result.exit_code,
                                                        stdout=update_result.stdout,
                                                        stderr=update_result.stderr,
                                                        admin_ids=admin_ids,
                                                    )
                                                
                                                await notification_bot.session.close()
                                                
                                        except Exception as notify_error:
                                            logger.error(f"Failed to send update error notification: {notify_error}", exc_info=True)
                                        
                                        logger.error(
                                            f"Update failed for bot {updated_bot.id}: exit_code={update_result.exit_code}, "
                                            f"stderr={update_result.stderr[:200]}"
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