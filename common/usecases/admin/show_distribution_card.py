from __future__ import annotations

from datetime import datetime
from typing import Dict
from uuid import UUID
import base64

from common.dto import DistributionCardDTO
from services import PostService

from logging import getLogger
logger = getLogger(__name__)

class ShowDistributionCardUseCase:
    def __init__(
        self,
        *,
        post_service: PostService,
        texts: Dict[str, str],
        status_labels: Dict[str, str],
        status_short: Dict[str, str],
        datetime_format: str | None = None,
    ) -> None:
        self._post_service = post_service
        self._texts = texts
        self._status_labels = status_labels
        self._status_short = status_short
        self._datetime_format = datetime_format or "%Y-%m-%d %H:%M"

    async def __call__(self, distribution_id: UUID | str) -> DistributionCardDTO:
        if isinstance(distribution_id, str):
            distribution_id = UUID(bytes=base64.urlsafe_b64decode(base64.urlsafe_b64decode(distribution_id + '==') + b'=='))

        logger.debug(f"Showing distribution card for ID: {distribution_id}")
            
        summary = await self._post_service.get_distribution_summary(distribution_id)
        if summary is None:
            raise ValueError("Distribution not found")

        name = summary.get("distribution_name") or self._texts.get("card_name_placeholder", "Без названия")
        status_counts = {
            "active": int(summary.get("active_count") or 0),
            "paused": int(summary.get("paused_count") or 0),
            "error": int(summary.get("error_count") or 0),
            "done": int(summary.get("done_count") or 0),
        }
        total_posts = int(summary.get("total_posts") or 0)

        source_label, source_link = self._format_source_line(
            summary.get("source_channel_username"),
            summary.get("source_channel_id"),
            summary.get("source_message_id"),
        )

        text_lines: list[str] = [
            self._texts["card_heading"].format(name=name),
        ]
        if source_link:
            text_lines.append(
                self._texts["card_source_link"].format(link=source_link, label=source_label)
            )
        else:
            text_lines.append(self._texts["card_source_plain"].format(label=source_label))

        text_lines.append(
            self._texts["card_created_at"].format(value=self._format_datetime(summary.get("created_at")))
        )
        text_lines.append(
            self._texts["card_statuses_title"].format(total=total_posts)
        )

        for key in ("active", "paused", "error", "done"):
            marker = self._status_short.get(key, "")
            label = self._status_labels.get(key, key)
            count = status_counts.get(key, 0)
            text_lines.append(
                self._texts["card_statuses_item"].format(
                    marker=marker,
                    label=label,
                    count=count,
                )
            )

        return DistributionCardDTO(
            distribution_id=distribution_id,
            name=name,
            source_channel_username=summary.get("source_channel_username"),
            source_channel_id=summary.get("source_channel_id"),
            source_message_id=summary.get("source_message_id"),
            created_at=summary.get("created_at"),
            updated_at=summary.get("updated_at"),
            total_posts=total_posts,
            status_counts=status_counts,
            items=[],
            text="\n".join(text_lines),
            notify_on_failure=bool(summary.get("notify_on_failure", True)),
        )

    def _format_source_line(self, username: str | None, channel_id: int | None, message_id: int | None) -> tuple[str, str | None]:
        if username:
            slug = username.lstrip("@")
            label = f"t.me/{slug}/{message_id}"
            href = f"https://t.me/{slug}/{message_id}"
            return label, href
        if channel_id is not None:
            label, href = self._format_channel_link(channel_id, message_id)
            return label, href
        label = self._texts["card_source_unknown"].format(message_id=message_id)
        return label, None

    def _format_datetime(self, value: datetime | None) -> str:
        if value is None:
            return self._texts.get("no_data", "—")
        return value.strftime(self._datetime_format)

    def _format_channel_link(self, channel_id: int, message_id: int | None) -> tuple[str, str | None]:
        if channel_id == 0:
            label = self._texts["card_source_unknown"].format(message_id=message_id)
            return label, None
        abs_id = abs(channel_id)
        if abs_id >= 1000000000000:
            slug = abs_id - 1000000000000
        else:
            slug = abs_id
        if message_id is None:
            label = f"t.me/c/{slug}"
            href = f"https://t.me/c/{slug}"
            return label, href
        label = f"t.me/c/{slug}/{message_id}"
        href = f"https://t.me/c/{slug}/{message_id}"
        return label, href
