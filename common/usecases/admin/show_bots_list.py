from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict

from common.dto import BotListItemDTO, BotsListViewDTO
from services import BotService, PostService, SettingsService


class ShowBotsListUseCase:
    def __init__(
        self,
        *,
        bot_service: BotService,
        post_service: PostService,
        settings_service: SettingsService,
        texts: Dict[str, str],
        status_texts: Dict[str, str],
        pagination_texts: Dict[str, str],
    ) -> None:
        self._bot_service = bot_service
        self._post_service = post_service
        self._settings_service = settings_service
        self._texts = texts
        self._status_texts = status_texts
        self._pagination_texts = pagination_texts

    async def __call__(self, page: int = 1) -> BotsListViewDTO:
        settings = await self._settings_service.get_current()
        if settings is None:
            raise RuntimeError("Settings profile is not configured")

        page_size = max(1, settings.pagination_size)
        total = await self._bot_service.count()
        total_pages = max(1, math.ceil(total / page_size))
        page = min(max(1, page), total_pages)

        bots = await self._bot_service.list(limit=page_size, offset=(page - 1) * page_size)
        bot_ids = [bot.id for bot in bots]
        load_map = await self._bot_service.loads_by_bot(bot_ids)

        items: list[BotListItemDTO] = []
        now = datetime.now(timezone.utc)

        for bot in bots:
            load_used = load_map.get(bot.id, 0)
            load_limit = bot.max_posts

            status_key = self._detect_status(bot.last_heartbeat_at, now, settings)
            status_display = self._status_texts.get(status_key, "")
            status = status_display.split()[0] if status_display else ""

            if bot.username:
                username = bot.username
                if not username.startswith("@"):
                    username = f"@{username}"
                display_name = username
            else:
                display_name = bot.name or self._texts.get("item_placeholder", "—")
            label = self._texts["item_template"].format(
                status=status,
                name=display_name,
                current=load_used,
                limit=load_limit,
            )

            error_count = await self._post_service.count_errors_for_bot(bot.id)
            has_errors = error_count > 0
            if has_errors:
                label = self._texts["item_with_alert"].format(item=label)

            items.append(
                BotListItemDTO(
                    bot_id=bot.id,
                    telegram_id=bot.telegram_id,
                    label=label,
                    status=status,
                    load_current=load_used,
                    load_limit=load_limit,
                    has_errors=has_errors,
                )
            )

        if not items:
            text = "\n".join([self._texts["list_title"], self._texts["list_empty"]])
        else:
            text_lines = [self._texts["list_title"], self._texts["list_hint"]]
            text_lines.append(self._pagination_texts["label"].format(current=page, total=total_pages))
            text = "\n".join(text_lines)

        return BotsListViewDTO(
            text=text,
            items=items,
            page=page,
            total_pages=total_pages,
            total_items=total,
        )

    def _detect_status(self, heartbeat, now: datetime, settings) -> str:
        if heartbeat is None:
            return "offline"
        delta = (now - heartbeat).total_seconds()
        if delta <= settings.online_threshold_s:
            return "online"
        if delta <= settings.offline_threshold_s:
            return "warning"
        return "offline"
