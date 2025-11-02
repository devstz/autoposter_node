from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from infra.db.models import PostAttempt


@dataclass(slots=True)
class PostAttemptDTO:
    id: UUID
    post_id: UUID
    bot_id: Optional[UUID]
    group_id: Optional[UUID]
    chat_id: Optional[int]
    message_id: Optional[int]
    success: bool
    deleted: bool
    error_code: Optional[str]
    error_msg: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: PostAttempt) -> "PostAttemptDTO":
        return cls(
            id=model.id,
            post_id=model.post_id,
            bot_id=model.bot_id,
            group_id=model.group_id,
            chat_id=model.chat_id,
            message_id=model.message_id,
            success=model.success,
            deleted=model.deleted,
            error_code=model.error_code,
            error_msg=model.error_msg,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
