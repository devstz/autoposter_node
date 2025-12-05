from logging import getLogger

from aiogram import Bot

from .instance_bot import create_bot

logger = getLogger(__name__)


class BotManager:
    def __init__(self, token: str, webhook_url: str | None = None):
        self.webhook_url = webhook_url
        self.token = token
        self.bot: Bot | None = None
        logger.info('Init Bot Manager')

    def get_bot(self):
        if not self.bot:
            self.create_bot()
        if self.bot:
            return self.bot

    def create_bot(self):
        self.bot = create_bot(self.token)

    async def setup_bot(self):
        if not self.bot:
            self.create_bot()
        if self.bot:
            await self._configure_webhook(self.bot)

    async def _configure_webhook(self, bot: Bot):
        if not self.webhook_url:
            raise Exception('Webhook URL not found')
        
        webhook_url = self.webhook_url

        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(webhook_url, allowed_updates=['message', 'callback_query'])
        logger.info(f"Webhook configured for bot {bot.id}")

        return True

    async def close(self) -> None:
        """Закрывает сессию бота."""
        try:
            if self.bot and self.bot.session:
                await self.bot.session.close()
                logger.info("Bot session closed")
        except Exception as e:
            logger.error(f"Error closing bot session: {e}", exc_info=True)
