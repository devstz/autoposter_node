from __future__ import annotations

from uuid import UUID
from typing import Dict

from common.dto import BotFreePromptDTO, ActionResultDTO
from common.enums import AdminBotFreeMode
from services import BotService, PostService


class PrepareFreeBotUseCase:
    def __init__(
        self,
        *,
        bot_service: BotService,
        texts: Dict[str, str],
        confirmation_texts: Dict[str, str],
    ) -> None:
        self._bot_service = bot_service
        self._texts = texts
        self._confirmation_texts = confirmation_texts

    async def __call__(self, bot_id: UUID) -> BotFreePromptDTO:
        bot = await self._bot_service.get(bot_id)
        if bot is None:
            raise RuntimeError("Bot not found")

        display_name = bot.name or bot.username or self._texts.get("no_data", "—")
        text = "\n".join(
            [
                self._confirmation_texts["free_posts_title"],
                self._confirmation_texts["free_posts_prompt"].format(name=display_name),
                "",
                self._confirmation_texts["free_posts_mode_prompt"],
                self._confirmation_texts["mode_instant_hint"],
                self._confirmation_texts["mode_graceful_hint"],
            ]
        )
        return BotFreePromptDTO(bot_id=bot_id, telegram_id=bot.telegram_id, text=text)


class FreeBotUseCase:
    def __init__(
        self,
        *,
        bot_service: BotService,
        post_service: PostService,
        result_texts: Dict[str, str],
    ) -> None:
        self._bot_service = bot_service
        self._post_service = post_service
        self._result_texts = result_texts

    async def __call__(self, bot_id: UUID, mode: AdminBotFreeMode) -> ActionResultDTO:
        bot = await self._bot_service.get(bot_id)
        if bot is None:
            raise RuntimeError("Bot not found")

        if mode == AdminBotFreeMode.INSTANT:
            await self._post_service.bulk_unassign_by_bot(bot_id)
            message = self._result_texts["free_posts_instant"]
        else:
            await self._post_service.bulk_pause_by_bot(bot_id)
            message = self._result_texts["free_posts_graceful"]

        return ActionResultDTO(bot_id=bot_id, text=message, mode=mode)
