from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from infra.db.models import Post


@dataclass(slots=True)
class PostDTO:
    id: UUID
    group_id: UUID
    bot_id: Optional[UUID]
    status: str
    target_chat_id: int
    distribution_name: Optional[str]
    source_channel_username: str
    source_channel_id: int | None
    source_message_id: int
    last_attempt_at: Optional[datetime]
    last_error: Optional[str]
    count_attempts: int
    target_attempts: int
    delete_last_attempt: bool
    pin_after_post: bool
    num_attempt_for_pin_post: int | None
    pause_between_attempts_s: int
    notify_on_failure: bool
    created_at: datetime
    updated_at: datetime
    group_chat_id: Optional[int] = None
    group_title: Optional[str] = None
    group_username: Optional[str] = None
    bot_username: Optional[str] = None
    bot_name: Optional[str] = None
    bot_telegram_id: Optional[str] = None

    @classmethod
    def from_model(cls, model: Post) -> "PostDTO":
        group = getattr(model, "group", None)
        bot = getattr(model, "bot", None)
        bot_token = getattr(bot, "token", None) if bot else None
        bot_telegram_id = None
        if bot_token:
            prefix, _, _ = bot_token.partition(":")
            bot_telegram_id = prefix or None
        return cls(
            id=model.id,
            group_id=model.group_id,
            bot_id=model.bot_id,
            status=model.status,
            target_chat_id=model.target_chat_id,
            distribution_name=model.distribution_name,
            source_channel_username=model.source_channel_username,
            source_channel_id=model.source_channel_id,
            source_message_id=model.source_message_id,
            last_attempt_at=model.last_attempt_at,
            last_error=model.last_error,
            count_attempts=model.count_attempts,
            target_attempts=model.target_attempts,
            delete_last_attempt=model.delete_last_attempt,
            pin_after_post=model.pin_after_post,
            num_attempt_for_pin_post=model.num_attempt_for_pin_post,
            pause_between_attempts_s=model.pause_between_attempts_s,
            notify_on_failure=model.notify_on_failure,
            created_at=model.created_at,
            updated_at=model.updated_at,
            group_chat_id=getattr(group, "tg_chat_id", None),
            group_title=getattr(group, "title", None),
            group_username=getattr(group, "username", None),
            bot_username=getattr(bot, "username", None),
            bot_name=getattr(bot, "name", None),
            bot_telegram_id=bot_telegram_id,
        )
