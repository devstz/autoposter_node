from __future__ import annotations

from uuid import UUID
from typing import Dict

from common.dto import BotDeletePromptDTO, ActionResultDTO
from services import BotService, PostService


class PrepareDeleteBotUseCase:
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

    async def __call__(self, bot_id: UUID) -> BotDeletePromptDTO:
        bot = await self._bot_service.get(bot_id)
        if bot is None:
            raise RuntimeError("Bot not found")

        display_name = bot.name or bot.username or self._texts.get("no_data", "—")
        text = "\n".join(
            [
                self._confirmation_texts["delete_title"],
                self._confirmation_texts["delete_prompt"].format(name=display_name),
            ]
        )
        return BotDeletePromptDTO(bot_id=bot_id, telegram_id=bot.telegram_id, text=text)


class DeleteBotUseCase:
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

    async def __call__(self, bot_id: UUID) -> ActionResultDTO:
        bot = await self._bot_service.get(bot_id)
        if bot is None:
            raise RuntimeError("Bot not found")

        await self._post_service.bulk_unassign_by_bot(bot_id)
        await self._bot_service.mark_self_destruction(bot_id)
        await self._bot_service.update_fields(bot_id, deactivated=True)

        return ActionResultDTO(bot_id=bot_id, text=self._result_texts["bot_deleted"])
