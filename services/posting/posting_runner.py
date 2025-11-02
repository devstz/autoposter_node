from __future__ import annotations

import asyncio
from infra.db.uow import get_uow

from aiogram import Bot
from bot.builder.instance_bot import create_bot

from datetime import datetime, timezone, timedelta

from services.post_service import PostService
from services.post_attempt_service import PostAttemptService

from common.enums.post_status import PostStatus

from infra.db.models import Bot as BotDB, Post, PostAttempt

from .posting_service import PostingService
from .rate_limiter import RateLimiter

from asyncio import sleep

from logging import getLogger

logger = getLogger('PostingRunner')

SLEEP_INTERVAL_SECONDS = 1


class PostingRunner:
    def __init__(self, token: str) -> None:
        self.tg_bot: Bot = create_bot(token)
        self.posting_service = PostingService(self.tg_bot)
        self.sleep_interval = SLEEP_INTERVAL_SECONDS
        self.rate_limiter = RateLimiter(max_calls=25, period=1.0)

        self.running = True

    async def start(self, stop_event: asyncio.Event) -> None:
        while True:
            await sleep(self.sleep_interval)
            await self.run_once()

    async def stop(self) -> None:
        self.running = False

    async def run_once(self) -> None:
        async with get_uow() as uow:
            bot = await uow.bot_repo.get_by_token(self.tg_bot.token)
            if bot is None:
                logger.error("Bot not found in DB for PostingRunner.")
                return
            post_service = PostService(uow=uow)
            posts = await post_service.list_by_bot(bot_id=bot.id, limit=bot.settings.max_posts_per_bot)
            tasks = []
            for post in posts:
                tasks.append(self._process_post(bot, post))
            
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_post(self, bot: BotDB, post: Post) -> None:
        # Treat negative target_attempts as infinite
        if (
            post.status != PostStatus.ACTIVE.value
            or (post.target_attempts >= 0 and post.count_attempts >= post.target_attempts)
        ):
            return
        if post.last_attempt_at and (
            (post.last_attempt_at + timedelta(seconds=post.pause_between_attempts_s)) > datetime.now(timezone.utc)
        ):
            return
        
        async with self.rate_limiter():
            try:
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

                tg_msg = await self.posting_service.send_post(post)

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
                post.count_attempts += 1
                await self.posting_service.pin_post(post, tg_msg)
                post.last_attempt_at = datetime.now(timezone.utc)
                if post.target_attempts >= 0 and post.count_attempts >= post.target_attempts:
                    post.status = PostStatus.DONE.value
            except Exception as e:
                # Record failed attempt and mark post as error with message
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
                except Exception as inner:
                    logger.error(f"Failed to record error for post {post.id}: {inner}")
                logger.error(f"Error processing post {post.id} for bot {bot.id}: {e}")
