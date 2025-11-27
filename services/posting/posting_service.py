from asyncio import sleep

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import Message
from infra.db.models import Post, PostAttempt
from logging import getLogger

logger = getLogger('PostingService')


class PostingService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def _delete_message_safe(
        self,
        chat_id: int,
        message_id: int,
        max_retries: int = 3,
        operation_name: str = "message"
    ) -> bool:
        """Безопасное удаление сообщения с обработкой исключений и повторными попытками."""
        for attempt in range(max_retries):
            try:
                await self.bot.delete_message(
                    chat_id=chat_id,
                    message_id=message_id,
                )
                logger.info(f"Deleted {operation_name} {message_id} in chat {chat_id}.")
                return True
            except TelegramRetryAfter as e:
                retry_after = e.retry_after
                logger.warning(
                    f"Flood control (attempt {attempt + 1}/{max_retries}): "
                    f"waiting {retry_after} seconds before deleting {operation_name} {message_id} in chat {chat_id}."
                )
                await sleep(retry_after)
            except TelegramBadRequest as e:
                error_msg = str(e).lower()
                if "message to delete not found" in error_msg:
                    logger.warning(
                        f"{operation_name.capitalize()} {message_id} in chat {chat_id} already deleted. "
                        f"Considering deletion successful."
                    )
                    return True
                logger.warning(
                    f"BadRequest when deleting {operation_name} {message_id} in chat {chat_id}: {e}. "
                    f"Considering deletion successful."
                )
                return True
            except Exception as e:
                logger.error(
                    f"Unexpected error deleting {operation_name} {message_id} in chat {chat_id} "
                    f"(attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}"
                )
                if attempt == max_retries - 1:
                    logger.warning(
                        f"Failed to delete {operation_name} after {max_retries} attempts. "
                        f"Considering operation non-critical."
                    )
                    return False
                await sleep(1)
        
        logger.warning(f"Failed to delete {operation_name} {message_id} in chat {chat_id} after {max_retries} attempts.")
        return False

    async def _pin_message_safe(
        self,
        chat_id: int,
        message_id: int,
        max_retries: int = 3
    ) -> bool:
        """Безопасное закрепление сообщения с обработкой исключений и повторными попытками."""
        for attempt in range(max_retries):
            try:
                result = await self.bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=message_id,
                )
                if result:
                    logger.info(f"Pinned message {message_id} in chat {chat_id}.")
                return result
            except TelegramRetryAfter as e:
                retry_after = e.retry_after
                logger.warning(
                    f"Flood control (attempt {attempt + 1}/{max_retries}): "
                    f"waiting {retry_after} seconds before pinning message {message_id} in chat {chat_id}."
                )
                await sleep(retry_after)
            except Exception as e:
                logger.error(
                    f"Unexpected error pinning message {message_id} in chat {chat_id} "
                    f"(attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}"
                )
                if attempt == max_retries - 1:
                    logger.warning(f"Failed to pin message after {max_retries} attempts. Continuing without pin.")
                    return False
                await sleep(1)
        
        return False

    async def send_post(self, post: Post) -> Message:
        try:
            from_chat_id = post.source_channel_id
            if from_chat_id is None:
                raise ValueError(f"Post {post.id} has no source_channel_id")
            
            message_id = post.source_message_id
            to_chat_id = post.target_chat_id

            logger.info(f"Sending post {post.id} from {from_chat_id} message {message_id} to chat {to_chat_id}")

            msg = await self.bot.forward_message(
                chat_id=to_chat_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
            )
            return msg
        except Exception as e:
            logger.error(f"Failed to send post ({post.id}):\n{to_chat_id=}\n{from_chat_id=}\n{message_id}\nError: {type(e).__name__}: {e}")
            raise e
    
    async def delete_post_attempt(self, post_attempt: PostAttempt) -> bool:
        if post_attempt.message_id is None or post_attempt.chat_id is None:
            logger.warning(f"Last attempt message_id or chat_id is None for attempt {post_attempt.message_id}. Skipping deletion.")
            return False
        
        return await self._delete_message_safe(
            chat_id=post_attempt.chat_id,
            message_id=post_attempt.message_id,
            operation_name="last attempt message"
        )
        
    async def pin_post(self, post: Post, tg_msg: Message) -> bool:
        if not post.pin_after_post or (post.num_attempt_for_pin_post and post.count_attempts % post.num_attempt_for_pin_post != 0):
            return False
        
        result = await self._pin_message_safe(
            chat_id=post.target_chat_id,
            message_id=tg_msg.message_id
        )
        
        if result:
            logger.info(f"Pinned message {tg_msg.message_id} in chat {post.target_chat_id} for post {post.id}.")
            # Пытаемся удалить уведомление о пине
            await self._delete_message_safe(
                chat_id=post.target_chat_id,
                message_id=tg_msg.message_id + 1,
                operation_name="pin notification message"
            )
        
        return result