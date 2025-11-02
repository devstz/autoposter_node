from __future__ import annotations

import math
from datetime import datetime
from typing import Dict
from uuid import UUID

from common.dto import DistributionListItemDTO, DistributionsListViewDTO
from services import PostService, SettingsService


class ShowDistributionsListUseCase:
    def __init__(
        self,
        *,
        post_service: PostService,
        settings_service: SettingsService,
        texts: Dict[str, str],
        pagination_texts: Dict[str, str],
        status_short_texts: Dict[str, str],
        datetime_format: str | None = None,
    ) -> None:
        self._post_service = post_service
        self._settings_service = settings_service
        self._texts = texts
        self._pagination_texts = pagination_texts
        self._status_short_texts = status_short_texts
        self._datetime_format = datetime_format or "%Y-%m-%d %H:%M"

    async def __call__(self, page: int = 1) -> DistributionsListViewDTO:
        settings = await self._settings_service.get_current()
        if settings is None:
            raise RuntimeError("Settings profile is not configured")

        page_size = max(1, settings.pagination_size)
        total = await self._post_service.count_distributions()
        total_pages = max(1, math.ceil(total / page_size))
        page = min(max(1, page), total_pages)

        rows = await self._post_service.list_distributions(
            limit=page_size,
            offset=(page - 1) * page_size,
        )

        items: list[DistributionListItemDTO] = []
        for row in rows:
            distribution_id = row["distribution_id"]
            if isinstance(distribution_id, str):
                distribution_id = UUID(distribution_id)

            name = row.get("distribution_name") or self._texts.get("list_name_placeholder", "Без названия")
            status_counts = {
                "active": int(row.get("active_count") or 0),
                "paused": int(row.get("paused_count") or 0),
                "error": int(row.get("error_count") or 0),
                "done": int(row.get("done_count") or 0),
            }

            status_parts = []
            for key in ("active", "paused", "error", "done"):
                count = status_counts[key]
                if count <= 0:
                    continue
                marker = self._status_short_texts.get(key, key[:1].upper())
                status_parts.append(f"{marker} {count}")
            status_summary = " • ".join(status_parts) or self._texts.get("list_statuses_empty", "")

            label = self._texts["list_item_compact"].format(
                name=name,
                statuses=status_summary,
            )

            items.append(
                DistributionListItemDTO(
                    distribution_id=distribution_id,
                    name=name,
                    label=label,
                    created_at=row.get("created_at"),
                    total_posts=int(row.get("total_posts") or 0),
                    status_counts=status_counts,
                )
            )

        if not items:
            text = "\n".join([self._texts["list_title"], self._texts["list_empty"]])
        else:
            text_lines = [
                self._texts["list_title"],
                self._texts["list_hint"],
                self._pagination_texts["label"].format(current=page, total=total_pages),
            ]
            text = "\n".join(text_lines)

        return DistributionsListViewDTO(
            text=text,
            items=items,
            page=page,
            total_pages=total_pages,
            total_items=total,
        )

    def _format_source(self, username: str | None, channel_id: int | None) -> str:
        if username:
            return f"@{username.lstrip('@')}"
        if channel_id:
            return str(channel_id)
        return self._texts.get("source_unknown", "unknown")

    def _format_datetime(self, value: datetime | None) -> str:
        if value is None:
            return self._texts.get("no_data", "—")
        return value.strftime(self._datetime_format)
