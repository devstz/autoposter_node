from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from infra.db.models import Bot


@dataclass(slots=True)
class BotDTO:
    id: UUID
    bot_id: int
    username: Optional[str]
    name: Optional[str]
    token: str
    server_ip: str
    last_heartbeat_at: Optional[datetime]
    self_destruction: bool
    deactivated: bool
    settings_id: Optional[UUID]
    max_posts: int
    tracked_branch: str
    current_commit_hash: Optional[str]
    latest_available_commit_hash: Optional[str]
    commits_behind: int
    last_update_check_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: Bot) -> "BotDTO":
        return cls(
            id=model.id,
            bot_id=model.bot_id,
            username=model.username,
            name=model.name,
            token=model.token,
            server_ip=model.server_ip,
            last_heartbeat_at=model.last_heartbeat_at,
            self_destruction=model.self_destruction,
            deactivated=model.deactivated,
            settings_id=model.settings_id,
            max_posts=model.max_posts,
            tracked_branch=model.tracked_branch,
            current_commit_hash=model.current_commit_hash,
            latest_available_commit_hash=model.latest_available_commit_hash,
            commits_behind=model.commits_behind,
            last_update_check_at=model.last_update_check_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @property
    def telegram_id(self) -> str:
        prefix, _, _ = self.token.partition(":")
        if not prefix:
            raise ValueError("Bot token does not contain Telegram bot ID part")
        return prefix
