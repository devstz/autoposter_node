from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from common.dto import BotDTO, GroupCardDTO
from services import GroupService, BotService


class ShowGroupCardUseCase:
    def __init__(
        self,
        *,
        group_service: GroupService,
        bot_service: BotService,
        texts: Dict[str, str],
        datetime_format: str | None = None,
    ) -> None:
        self._group_service = group_service
        self._bot_service = bot_service
        self._texts = texts
        self._datetime_format = datetime_format or "%Y-%m-%d %H:%M:%S"

    async def __call__(self, group_id: UUID) -> GroupCardDTO:
        group = await self._group_service.get(group_id)
        if group is None:
            raise ValueError("Group not found")

        group = await self._group_service.ensure_metadata(group, self._bot_service)

        bot: Optional[BotDTO] = None
        if group.assigned_bot_id:
            bot = await self._bot_service.get(group.assigned_bot_id)

        text_lines: list[str] = [
            self._texts["card_title"].format(chat_id=group.tg_chat_id),
            self._texts["card_chat_id"].format(chat_id=group.tg_chat_id),
            self._texts["card_type"].format(type=self._resolve_group_type(group.type)),
            self._texts["card_title_field"].format(
                title=group.title or self._texts.get("card_title_placeholder", "—")
            ),
            self._texts["card_username_field"].format(
                username=self._format_username(group)
            ),
            self._texts["card_bot"].format(bot=self._resolve_bot_label(bot)),
            self._texts["card_last_post"].format(value=self._format_dt(group.last_post_at)),
            self._texts["card_bound_at"].format(value=self._format_dt(group.created_at)),
            self._texts["card_updated_at"].format(value=self._format_dt(group.updated_at)),
        ]

        return GroupCardDTO(
            group_id=group.id,
            tg_chat_id=group.tg_chat_id,
            bot_id=bot.id if bot else None,
            bot_telegram_id=bot.telegram_id if bot else None,
            text="\n".join(text_lines),
        )

    def _format_dt(self, value: Optional[datetime]) -> str:
        if value is None:
            return self._texts.get("no_data", "—")
        return value.strftime(self._datetime_format)

    def _resolve_group_type(self, value: str) -> str:
        # Allow localization overrides like type_channel, type_supergroup, etc.
        return self._texts.get(f"type_{value}", value)

    def _format_username(self, group) -> str:
        if getattr(group, "username", None):
            return f"@{group.username}"
        return self._texts.get("card_username_placeholder", "—")

    def _resolve_bot_label(self, bot: Optional[BotDTO]) -> str:
        if bot is None:
            return self._texts.get("card_not_bound", "—")
        name = bot.name or ""
        username = bot.username or ""
        if name and username:
            return f"{name} (@{username})"
        if name:
            return name
        if username:
            return f"@{username}"
        return bot.telegram_id
