from __future__ import annotations

from typing import TYPE_CHECKING
from logging import getLogger

from aiogram import Bot
from common.enums.telegram_error import TelegramErrorType

if TYPE_CHECKING:
    from infra.db.models import Bot as BotDB, Post
    from common.dto import GroupDTO

logger = getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений админам"""
    
    def __init__(self, bot: Bot) -> None:
        """
        Args:
            bot: Aiogram Bot для отправки сообщений
        """
        self.bot = bot
    
    async def notify_admins(self, message: str, admin_ids: list[int]) -> None:
        """
        Отправляет сообщение всем админам
        
        Args:
            message: Текст сообщения
            admin_ids: Список user_id админов
        """
        for admin_id in admin_ids:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode="HTML"
                )
                logger.info(f"Notification sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin_id}: {type(e).__name__}: {e}")
    
    async def notify_group_failure(
        self,
        bot: BotDB,
        group: GroupDTO,
        post: Post,
        error_type: TelegramErrorType,
        error_message: str,
        admin_ids: list[int],
    ) -> None:
        """
        Отправляет уведомление о критической ошибке с группой
        
        Args:
            bot: Модель бота из БД
            group: DTO группы
            post: Модель поста
            error_type: Тип ошибки
            error_message: Текст ошибки
            admin_ids: Список user_id админов для уведомления
        """
        # Формируем красивое название ошибки
        error_names = {
            TelegramErrorType.CHAT_NOT_FOUND: "Чат не найден (удален)",
            TelegramErrorType.BOT_KICKED: "Бот кикнут из группы",
            TelegramErrorType.BOT_BLOCKED: "Бот заблокирован",
            TelegramErrorType.FORBIDDEN: "Нет доступа",
            TelegramErrorType.USER_DEACTIVATED: "Пользователь деактивирован",
            TelegramErrorType.UNKNOWN: "Неизвестная ошибка",
        }
        
        error_name = error_names.get(error_type, error_type.value)
        bot_username = bot.username or "неизвестно"
        group_title = group.title or "без названия"
        post_name = post.distribution_name or str(post.id)
        
        message = (
            "⚠️ <b>ОШИБКА РАССЫЛКИ</b>\n\n"
            f"<b>Бот:</b> @{bot_username} (<code>{bot.bot_id}</code>)\n"
            f"<b>Группа:</b> {group_title} (<code>{group.tg_chat_id}</code>)\n"
            f"<b>Пост:</b> {post_name}\n\n"
            f"<b>Причина:</b> {error_name}\n"
            f"<b>Детали:</b> <code>{error_message}</code>\n\n"
            "✅ <b>Группа автоматически удалена из рассылки</b>"
        )
        
        await self.notify_admins(message, admin_ids)
        logger.info(
            f"Sent failure notification for group {group.id} to {len(admin_ids)} admins"
        )

    async def notify_update_error(
        self,
        bot: BotDB,
        error_details: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        admin_ids: list[int],
    ) -> None:
        """
        Отправляет уведомление админам об ошибке обновления бота
        
        Args:
            bot: Модель бота
            error_details: Детали ошибки
            exit_code: Код возврата команды
            stdout: Стандартный вывод команды
            stderr: Стандартный поток ошибок
            admin_ids: Список user_id админов
        """
        bot_username = bot.username or "без имени"
        if bot_username and not bot_username.startswith("@"):
            bot_username = f"@{bot_username}"
        
        message_lines = [
            "⚠️ <b>ОШИБКА ОБНОВЛЕНИЯ БОТА</b>\n",
            f"<b>Бот:</b> {bot_username} (<code>{bot.bot_id}</code>)",
            f"<b>IP сервера:</b> <code>{bot.server_ip}</code>\n",
            f"<b>Код возврата:</b> <code>{exit_code}</code>",
        ]
        
        if error_details:
            message_lines.append(f"<b>Ошибка:</b> <code>{error_details}</code>")
        
        if stderr:
            stderr_preview = stderr[:500] + "..." if len(stderr) > 500 else stderr
            message_lines.append(f"\n<b>Stderr:</b>\n<code>{stderr_preview}</code>")
        
        if stdout:
            stdout_preview = stdout[:500] + "..." if len(stdout) > 500 else stdout
            message_lines.append(f"\n<b>Stdout:</b>\n<code>{stdout_preview}</code>")
        
        message = "\n".join(message_lines)
        
        await self.notify_admins(message, admin_ids)
        logger.info(
            f"Sent update error notification for bot {bot.id} to {len(admin_ids)} admins"
        )

