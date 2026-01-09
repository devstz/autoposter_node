from __future__ import annotations

import asyncio
from infra.db.uow import get_uow

from aiogram import Bot
from bot.builder.instance_bot import create_bot

from datetime import datetime, timezone, timedelta

from services.post_service import PostService
from services.post_attempt_service import PostAttemptService
from services.group_service import GroupService
from services.user_service import UserService
from services.notification_service import NotificationService

from common.enums.post_status import PostStatus
from common.enums.telegram_error import (
    TelegramErrorType,
    classify_telegram_error,
    is_critical_error,
)

from infra.db.models import Bot as BotDB, Post, PostAttempt
from sqlalchemy.exc import IntegrityError

from .posting_service import PostingService

from asyncio import sleep

from logging import getLogger
from config.settings import get_settings

# Попытка импортировать исключения aiogram для сетевых/серверных ошибок
try:
    from aiogram.exceptions import TelegramNetworkError, TelegramServerError
except ImportError:
    # Если исключения не существуют в этой версии aiogram, используем проверку по имени класса
    TelegramNetworkError = None
    TelegramServerError = None

logger = getLogger('PostingRunner')

SLEEP_INTERVAL_SECONDS = 5 


class PostingRunner:
    def __init__(self, token: str) -> None:
        self.tg_bot: Bot = create_bot(token)
        self.posting_service = PostingService(self.tg_bot)
        self.notification_service = NotificationService(self.tg_bot)
        self.sleep_interval = SLEEP_INTERVAL_SECONDS
        self.running = True
        self.settings = get_settings()

    async def start(self, stop_event: asyncio.Event) -> None:
        while True:
            try:
                await sleep(self.sleep_interval)
                await self.run_once()
            except asyncio.CancelledError:
                logger.info("PostingRunner cancelled")
                raise
            except Exception as e:
                logger.error(f"Error in PostingRunner.start loop: {type(e).__name__}: {e}", exc_info=True)
                # Продолжаем работу даже при ошибке

    async def stop(self) -> None:
        self.running = False

    async def close(self) -> None:
        """Закрывает ресурсы PostingRunner."""
        try:
            if self.tg_bot and self.tg_bot.session:
                await self.tg_bot.session.close()
                logger.info("PostingRunner bot session closed")
        except Exception as e:
            logger.error(f"Error closing posting runner bot session: {e}", exc_info=True)

    def _is_post_ready(self, post: Post) -> bool:
        """Проверяет, готов ли пост к отправке"""
        # Проверка статуса
        if post.status != PostStatus.ACTIVE.value:
            return False
        
        # Проверка лимита попыток (negative target_attempts = infinite)
        if post.target_attempts >= 0 and post.count_attempts >= post.target_attempts:
            return False
        
        # Проверка времени паузы
        if post.last_attempt_at:
            next_attempt_time = post.last_attempt_at + timedelta(seconds=post.pause_between_attempts_s)
            if next_attempt_time > datetime.now(timezone.utc):
                return False
        
        return True

    def _is_network_or_server_error(self, exception: Exception) -> bool:
        """Проверяет, является ли ошибка сетевой или серверной (некритической)"""
        error_type = classify_telegram_error(exception)
        return error_type in {
            TelegramErrorType.NETWORK_ERROR,
            TelegramErrorType.SERVER_ERROR,
        }

    async def run_once(self) -> None:
        try:
            async with get_uow() as uow:
                bot = await uow.bot_repo.get_by_token(self.tg_bot.token)
                if bot is None:
                    logger.error("Bot not found in DB for PostingRunner.")
                    return
                
                post_service = PostService(uow=uow)
                posts = await post_service.list_by_bot(bot_id=bot.id, limit=bot.settings.max_posts_per_bot)
                
                # Фильтруем готовые к отправке посты
                ready_posts = [post for post in posts if self._is_post_ready(post)]
                
                if not ready_posts:
                    return
                
                # Отправляем посты с лимитом из настроек
                MAX_POSTS_PER_SECOND = self.settings.MAX_POSTS_PER_SECOND
                DELAY_BETWEEN_POSTS = 1.0 / MAX_POSTS_PER_SECOND
                
                logger.info(f"Sending {len(ready_posts)} posts with rate limit {MAX_POSTS_PER_SECOND} posts/sec")
                
                # Отправляем посты последовательно с задержкой для соблюдения лимита
                for i, post in enumerate(ready_posts):
                    # Перед отправкой заново проверяем готовность (могла измениться)
                    if self._is_post_ready(post):
                        await self._process_post(bot, post, post_service)
                    
                    # Задержка после всех постов кроме последнего
                    if i < len(ready_posts) - 1:
                        await sleep(DELAY_BETWEEN_POSTS)
        except Exception as e:
            logger.error(f"Error in PostingRunner.run_once: {type(e).__name__}: {e}", exc_info=True)
            # Не пробрасываем исключение дальше, чтобы цикл продолжался

    async def _process_post(self, bot: BotDB, post: Post, post_service: PostService) -> None:
        """Отправляет пост в Telegram (без проверок готовности)"""
        # Константы для повторных попыток
        MAX_IMMEDIATE_RETRIES = 3
        RETRY_DELAY = 2.0  # секунды между попытками
        
        try:
            # Удаляем предыдущую попытку, если требуется
            if post.delete_last_attempt and post.post_attempts:
                attempts_to_delete = [
                    attempt
                    for attempt in post.post_attempts
                    if not attempt.deleted and attempt.chat_id and attempt.message_id
                ]
                if attempts_to_delete:
                    last_post_attempt = max(attempts_to_delete, key=lambda attempt: attempt.created_at)
                    result_deleted = await self.posting_service.delete_post_attempt(last_post_attempt)
                    if result_deleted:
                        last_post_attempt.deleted = True

            # Отправляем пост с повторными попытками для сетевых/серверных ошибок
            tg_msg = None
            last_error = None
            
            for retry_attempt in range(MAX_IMMEDIATE_RETRIES):
                try:
                    tg_msg = await self.posting_service.send_post(post)
                    # Успешная отправка - выходим из цикла повторных попыток
                    break
                except Exception as e:
                    last_error = e
                    # Проверяем, является ли это сетевой/серверной ошибкой
                    if self._is_network_or_server_error(e):
                        if retry_attempt < MAX_IMMEDIATE_RETRIES - 1:
                            # Еще есть попытки - логируем и повторяем
                            logger.warning(
                                f"Network/server error sending post {post.id} (attempt {retry_attempt + 1}/{MAX_IMMEDIATE_RETRIES}): "
                                f"{type(e).__name__}: {e}. Retrying in {RETRY_DELAY} seconds..."
                            )
                            await sleep(RETRY_DELAY)
                            continue
                        else:
                            # Все попытки исчерпаны - пропускаем пост без записи ошибки
                            logger.warning(
                                f"Skipping post {post.id} after {MAX_IMMEDIATE_RETRIES} retries due to network/server error: "
                                f"{type(e).__name__}: {e}. Post will be retried in next cycle."
                            )
                            return  # Пропускаем пост, он останется активным для следующего цикла
                    else:
                        # Это не сетевая/серверная ошибка - пробрасываем дальше для обычной обработки
                        raise
            
            # Если tg_msg все еще None, значит все попытки неудачны, но это не должно произойти
            # (мы уже вернулись выше), но на всякий случай проверяем
            if tg_msg is None:
                if last_error:
                    raise last_error
                raise ValueError(f"Failed to send post {post.id} for unknown reason")

            # Записываем успешную попытку в БД
            try:
                async with get_uow() as uow:
                    post_attempt_service = PostAttemptService(uow=uow)

                    await post_attempt_service.add(PostAttempt(
                        post_id=post.id,
                        bot_id=bot.id,
                        group_id=post.group_id,
                        chat_id=post.target_chat_id,
                        message_id=tg_msg.message_id,
                        deleted=False,
                        success=True,
                    ))
            except IntegrityError as e:
                # Если пост был удален между отправкой и записью попытки, логируем предупреждение
                error_str = str(e).lower()
                if "foreign key constraint" in error_str and "post_id" in error_str:
                    logger.warning(f"Post {post.id} was deleted before recording success attempt. Skipping.")
                    return
                # Если это другая IntegrityError, пробрасываем дальше
                raise
            
            # Обновляем счетчики и статус через сервис (избегаем StaleDataError)
            await post_service.increment_attempt_count(post.id)
            await self.posting_service.pin_post(post, tg_msg)
            
            # Проверяем, нужно ли отметить пост как выполненный
            # Используем текущие значения поста, т.к. мы только что увеличили count_attempts на 1
            if post.target_attempts >= 0 and (post.count_attempts + 1) >= post.target_attempts:
                await post_service.mark_done(post.id)
        except Exception as e:
            # Классифицируем ошибку
            error_type = classify_telegram_error(e)
            is_critical = is_critical_error(error_type)
            
            # Записываем неудачную попытку и отмечаем пост как ошибочный
            try:
                async with get_uow() as uow:
                    post_attempt_service = PostAttemptService(uow=uow)
                    post_service = PostService(uow=uow)

                    await post_attempt_service.add(PostAttempt(
                        post_id=post.id,
                        bot_id=bot.id,
                        group_id=post.group_id,
                        chat_id=post.target_chat_id,
                        message_id=None,
                        deleted=False,
                        success=False,
                        error_code=type(e).__name__,
                        error_msg=str(e),
                    ))
                    await post_service.mark_error(post.id, f"{type(e).__name__}: {e}")
            except IntegrityError as inner:
                # Если пост был удален между обработкой ошибки и записью попытки, логируем предупреждение
                error_str = str(inner).lower()
                if "foreign key constraint" in error_str and "post_id" in error_str:
                    logger.warning(f"Post {post.id} was deleted before recording error attempt. Skipping.")
                    return
                # Если это другая IntegrityError, логируем как ошибку
                logger.error(f"Failed to record error for post {post.id}: {inner}")
            except Exception as inner:
                logger.error(f"Failed to record error for post {post.id}: {inner}")
            
            logger.error(f"Error processing post {post.id} for bot {bot.id}: {e}")
            
            # Обработка критических ошибок (удаление группы, нотификация)
            if is_critical and post.notify_on_failure:
                try:
                    await self._handle_critical_error(bot, post, error_type, str(e))
                except Exception as critical_error:
                    logger.error(f"Failed to handle critical error for post {post.id}: {critical_error}")
    
    async def _handle_critical_error(
        self,
        bot: BotDB,
        post: Post,
        error_type,
        error_message: str,
    ) -> None:
        """
        Обрабатывает критические ошибки: уведомляет админов и удаляет группу
        
        Args:
            bot: Модель бота
            post: Модель поста
            error_type: Тип ошибки Telegram
            error_message: Текст ошибки
        """
        async with get_uow() as uow:
            # Получаем список админов (superuser)
            user_service = UserService(uow.user_repo)
            admins = await user_service.search(is_superuser=True, limit=100)
            admin_ids = [admin.user_id for admin in admins]
            
            if not admin_ids:
                logger.warning("No admins found to notify about critical error")
                return
            
            # Получаем информацию о группе
            group_service = GroupService(uow.group_repo)
            group = await group_service.get(post.group_id)
            
            if group is None:
                logger.warning(f"Group {post.group_id} not found for notification")
                return
            
            # Отправляем уведомления админам
            await self.notification_service.notify_group_failure(
                bot=bot,
                group=group,
                post=post,
                error_type=error_type,
                error_message=error_message,
                admin_ids=admin_ids,
            )
            
            # Удаляем группу из системы
            await group_service.delete(post.group_id)
            logger.info(
                f"Group {post.group_id} ({group.title}) deleted due to critical error: {error_type.value}"
            )
