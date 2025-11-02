from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from common.dto import PostCardDTO, PostDTO
from services import PostService, GroupService, BotService


class ShowPostCardUseCase:
    def __init__(
        self,
        *,
        post_service: PostService,
        group_service: GroupService,
        bot_service: BotService,
        texts: Dict[str, str],
        datetime_format: str | None = None,
    ) -> None:
        self._post_service = post_service
        self._group_service = group_service
        self._bot_service = bot_service
        self._texts = texts
        self._datetime_format = datetime_format or "%Y-%m-%d %H:%M:%S"

    async def __call__(self, post_id: UUID) -> PostCardDTO:
        post = await self._post_service.get(post_id)
        if post is None:
            raise ValueError("Post not found")
        await self._ensure_group_metadata(post)

        status_label = self._texts["status_labels"].get(post.status, post.status)
        group_label = self._format_group(post)
        bot_label = self._format_bot(post)
        pin_label = self._texts["card_pin_true"] if post.pin_after_post else self._texts["card_pin_false"]

        text_lines: list[str] = [
            self._texts["card_title"].format(post_id=str(post.id)),
            self._texts["card_status"].format(status=status_label),
            self._texts["card_group"].format(group=group_label),
            self._texts["card_bot"].format(bot=bot_label),
            self._texts["card_source"].format(
                username=post.source_channel_username,
                message_id=post.source_message_id,
            ),
        ]
        if post.source_channel_id:
            text_lines.append(self._texts["card_source_channel_id"].format(channel_id=post.source_channel_id))
        text_lines.extend(
            [
                self._texts["card_target"].format(chat_id=post.target_chat_id),
                self._texts["card_attempts"].format(count=post.count_attempts, target=post.target_attempts),
                self._texts["card_pause_between"].format(seconds=post.pause_between_attempts_s),
                self._texts["card_last_attempt"].format(value=self._format_dt(post.last_attempt_at)),
                self._texts["card_last_error"].format(value=post.last_error or self._texts["no_data"]),
                self._texts["card_pin_after"].format(value=pin_label),
                self._texts["card_created_at"].format(value=self._format_dt(post.created_at)),
                self._texts["card_updated_at"].format(value=self._format_dt(post.updated_at)),
            ]
        )

        return PostCardDTO(
            post_id=post.id,
            status=post.status,
            text="\n".join(text_lines),
            bot_id=post.bot_id,
            group_id=post.group_id,
        )

    def _format_dt(self, value: Optional[datetime]) -> str:
        if value is None:
            return self._texts["no_data"]
        return value.strftime(self._datetime_format)

    def _format_group(self, post: PostDTO) -> str:
        title = post.group_title or (
            f"@{post.group_username}" if post.group_username else self._texts["card_group_placeholder"]
        )
        chat_id = post.group_chat_id or "—"
        return self._texts["item_target_template"].format(title=title, chat_id=chat_id)

    def _format_bot(self, post: PostDTO) -> str:
        if post.bot_name and post.bot_username:
            return f"{post.bot_name} (@{post.bot_username})"
        if post.bot_name:
            return post.bot_name
        if post.bot_username:
            return f"@{post.bot_username}"
        return self._texts["card_bot_placeholder"]

    async def _ensure_group_metadata(self, post: PostDTO) -> None:
        if not post.group_id:
            return
        group = await self._group_service.get(post.group_id)
        if group is None:
            return
        group = await self._group_service.ensure_metadata(group, self._bot_service)
        if group.title:
            post.group_title = group.title
        if getattr(group, "username", None):
            post.group_username = group.username
        if group.tg_chat_id and not post.group_chat_id:
            post.group_chat_id = group.tg_chat_id
