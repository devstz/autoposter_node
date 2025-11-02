from __future__ import annotations

from datetime import datetime
from typing import Dict
from uuid import UUID

from common.dto import DistributionGroupCardDTO, PostDTO
from services import PostService, GroupService, BotService


class ShowDistributionGroupCardUseCase:
    def __init__(
        self,
        *,
        post_service: PostService,
        group_service: GroupService,
        bot_service: BotService,
        texts: Dict[str, str],
        status_labels: Dict[str, str],
        datetime_format: str | None = None,
    ) -> None:
        self._post_service = post_service
        self._group_service = group_service
        self._bot_service = bot_service
        self._texts = texts
        self._status_labels = status_labels
        self._datetime_format = datetime_format or "%Y-%m-%d %H:%M"

    async def __call__(self, distribution_id: UUID, post_id: UUID) -> DistributionGroupCardDTO:
        summary = await self._post_service.get_distribution_summary(distribution_id)
        if summary is None:
            raise ValueError("Distribution not found")

        post = await self._post_service.get(post_id)
        if post is None:
            raise ValueError("Post not found")

        if not self._belongs_to_distribution(post, summary):
            raise ValueError("Post does not belong to distribution")

        await self._ensure_group_metadata(post)

        text = self._build_text(post)
        return DistributionGroupCardDTO(
            post_id=post.id,
            group_id=post.group_id,
            text=text,
        )

    def _belongs_to_distribution(self, post: PostDTO, summary: dict) -> bool:
        return (
            post.source_message_id == summary.get("source_message_id")
            and post.source_channel_username == summary.get("source_channel_username")
            and post.source_channel_id == summary.get("source_channel_id")
        )

    def _build_text(self, post: PostDTO) -> str:
        title = self._resolve_group_title(post)
        status_label = self._status_labels.get(post.status, post.status)
        chat_line = self._texts.get("group_card_chat", "Чат: {chat_id}").format(
            chat_id=post.group_chat_id or post.target_chat_id,
        )
        status_line = self._texts.get("group_card_status", "Статус: {status}").format(status=status_label)

        attempts_target = self._format_target_attempts(post.target_attempts)
        attempts_line = self._texts.get("group_card_attempts", "Попытки: {current}/{target}").format(
            current=post.count_attempts,
            target=attempts_target,
        )

        pause_line = self._texts.get("group_card_pause", "Пауза: {seconds} с").format(
            seconds=post.pause_between_attempts_s,
        )

        last_attempt_value = self._format_datetime(post.last_attempt_at)
        if last_attempt_value is None:
            last_attempt_line = self._texts.get("group_card_last_attempt_none", "Последняя попытка: —")
        else:
            last_attempt_line = self._texts.get("group_card_last_attempt", "Последняя попытка: {value}").format(
                value=last_attempt_value,
            )

        if post.last_error:
            last_error_line = self._texts.get("group_card_last_error", "Последняя ошибка: {error}").format(
                error=post.last_error,
            )
        else:
            last_error_line = self._texts.get("group_card_no_error", "Ошибок нет.")

        bot_label = self._format_bot(post)
        bot_line = self._texts.get("group_card_bot", "Бот: {bot}").format(bot=bot_label)

        notify_key = "group_card_notify_on" if post.notify_on_failure else "group_card_notify_off"
        notify_value = self._texts.get(notify_key, "—")
        notify_line = self._texts.get("group_card_notify", "Уведомления: {value}").format(value=notify_value)

        pin_line = self._build_pin_line(post)

        lines = [
            self._texts.get("group_card_title", "{title}").format(title=title),
            chat_line,
            self._texts.get("group_card_username", "<b>Юзернейм:</b> {value}").format(
                value=self._format_username(post)
            ),
            status_line,
            attempts_line,
            pause_line,
            last_attempt_line,
            last_error_line,
            bot_line,
            notify_line,
            pin_line,
        ]

        hint = self._texts.get("group_card_back_hint")
        if hint:
            lines.append("")
            lines.append(hint)

        return "\n".join(filter(None, lines))

    def _format_target_attempts(self, target: int) -> str:
        if target < 0:
            return self._texts.get("group_card_attempts_infinite", "∞")
        return str(target)

    def _format_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.strftime(self._datetime_format)

    def _format_bot(self, post: PostDTO) -> str:
        if post.bot_name and post.bot_username:
            return f"{post.bot_name} (@{post.bot_username})"
        if post.bot_name:
            return post.bot_name
        if post.bot_username:
            return f"@{post.bot_username}"
        return self._texts.get("group_card_bot_placeholder", "—")

    def _build_pin_line(self, post: PostDTO) -> str:
        if not post.pin_after_post:
            value = self._texts.get("group_card_pin_off", "выключено")
        else:
            if post.num_attempt_for_pin_post in (None, 0, 1):
                value = self._texts.get("group_card_pin_on_always", "включено для каждого сообщения")
            else:
                value = self._texts.get("group_card_pin_on", "включено, каждые {frequency}").format(
                    frequency=post.num_attempt_for_pin_post,
                )
        return self._texts.get("group_card_pin", "Закрепление: {value}").format(value=value)

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

    def _resolve_group_title(self, post: PostDTO) -> str:
        if post.group_title:
            return post.group_title
        if post.group_username:
            return f"@{post.group_username}"
        return self._texts.get("group_card_title_placeholder", "Без названия")

    def _format_username(self, post: PostDTO) -> str:
        if post.group_username:
            return f"@{post.group_username}"
        return self._texts.get("group_card_username_placeholder", "—")
