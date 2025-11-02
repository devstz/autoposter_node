from __future__ import annotations

import math
from typing import Dict, Optional
from uuid import UUID

from common.dto import BotDTO, GroupListItemDTO, GroupsListViewDTO
from services import GroupService, BotService, SettingsService


class ShowGroupsListUseCase:
    def __init__(
        self,
        *,
        group_service: GroupService,
        bot_service: BotService,
        settings_service: SettingsService,
        texts: Dict[str, str],
        pagination_texts: Dict[str, str],
    ) -> None:
        self._group_service = group_service
        self._bot_service = bot_service
        self._settings_service = settings_service
        self._texts = texts
        self._pagination_texts = pagination_texts

    async def __call__(self, page: int = 1) -> GroupsListViewDTO:
        settings = await self._settings_service.get_current()
        if settings is None:
            raise RuntimeError("Settings profile is not configured")

        page_size = max(1, settings.pagination_size)
        total = await self._group_service.count_bound()
        if total == 0:
            text = "\n".join([self._texts["list_title"], self._texts["list_empty"]])
            return GroupsListViewDTO(
                text=text,
                items=[],
                page=1,
                total_pages=1,
                total_items=0,
            )

        total_pages = max(1, math.ceil(total / page_size))
        page = min(max(1, page), total_pages)

        groups = await self._group_service.list_bound(limit=page_size, offset=(page - 1) * page_size)
        groups = await self._group_service.ensure_metadata_bulk(groups, self._bot_service)
        bot_map = await self._load_bots({g.assigned_bot_id for g in groups if g.assigned_bot_id})

        items: list[GroupListItemDTO] = []
        for group in groups:
            title = self._resolve_group_title(group)
            bot_label = self._resolve_bot_label(bot_map.get(group.assigned_bot_id))
            template = self._texts.get("item_template", "{chat_id} → {bot}")
            label = template.format(
                chat_id=group.tg_chat_id,
                title=title,
                bot=bot_label,
            )
            items.append(
                GroupListItemDTO(
                    group_id=group.id,
                    tg_chat_id=group.tg_chat_id,
                    label=label,
                    bot_id=group.assigned_bot_id,
                )
            )

        text_lines = [self._texts["list_title"]]
        list_hint = self._texts.get("list_hint")
        if list_hint:
            text_lines.append(list_hint)
        text_lines.append(
            self._pagination_texts["label"].format(current=page, total=total_pages)
        )
        text = "\n".join(text_lines)

        return GroupsListViewDTO(
            text=text,
            items=items,
            page=page,
            total_pages=total_pages,
            total_items=total,
        )

    async def _load_bots(self, bot_ids: set[UUID]) -> dict[UUID, Optional[BotDTO]]:
        out: dict[UUID, Optional[BotDTO]] = {}
        for bot_id in bot_ids:
            bot = await self._bot_service.get(bot_id)
            out[bot_id] = bot
        return out

    def _resolve_group_title(self, group) -> str:
        if group.title:
            return group.title
        if getattr(group, "username", None):
            return f"@{group.username}"
        return self._texts.get("item_title_placeholder", "—")

    def _resolve_bot_label(self, bot) -> str:
        if bot is None:
            return self._texts.get("item_bot_placeholder", "—")
        name = bot.name or ""
        username = bot.username or ""
        if name and username:
            return f"{name} (@{username})"
        if name:
            return name
        if username:
            return f"@{username}"
        return self._texts.get("item_bot_placeholder", "—")
