from aiogram import Bot
from aiogram.types import Message
from infra.db.models import Post, PostAttempt
from logging import getLogger

logger = getLogger('PostingService')


class PostingService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

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
            logger.error(f"Failed to send post ({post.id}):\n{chat_id=}\n{from_chat_id=}\n{message_id}\nError: {type(e).__name__}: {e}")
            raise e
    
    async def delete_post_attempt(self, post_attempt: PostAttempt) -> bool:
        try:
            if post_attempt.message_id is None or post_attempt.chat_id is None:
                logger.warning(f"Last attempt message_id or chat_id is None for attempt {post_attempt.message_id}. Skipping deletion.")
                return False
            
            await self.bot.delete_message(
                chat_id=post_attempt.chat_id,
                message_id=post_attempt.message_id,
            )
            logger.info(f"Deleted last attempt message {post_attempt.message_id} in chat {post_attempt.chat_id}.")

            return True
        except Exception as e:
            logger.error(f"Failed to delete last attempt message {post_attempt.message_id} in chat {post_attempt.chat_id}: {type(e).__name__}: {e}")
            raise e
        
    async def pin_post(self, post: Post, tg_msg: Message) -> bool:
        try:
            if post.pin_after_post and (not post.num_attempt_for_pin_post or (post.num_attempt_for_pin_post and post.count_attempts % post.num_attempt_for_pin_post == 0)):
                result = await self.bot.pin_chat_message(
                    chat_id=post.target_chat_id,
                    message_id=tg_msg.message_id,
                )
                if result:
                    logger.info(f"Pinned message {tg_msg.message_id} in chat {post.target_chat_id} for post {post.id}.")
                    await self.bot.delete_message(
                        chat_id=post.target_chat_id,
                        message_id=tg_msg.message_id + 1,
                    )
                    logger.info(f"Deleted pin notification message {tg_msg.message_id + 1} in chat {post.target_chat_id}.")
                return result
            return False
        except Exception as e:
            logger.error(f"Failed to pin message {tg_msg.message_id} in chat {post.target_chat_id} for post {post.id}: {type(e).__name__}: {e}")
            raise e