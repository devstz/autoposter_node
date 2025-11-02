from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from infra.db.models import Setting


@dataclass(slots=True)
class SettingDTO:
    id: UUID
    name: str
    is_current: bool
    heartbeat_interval_s: int
    online_threshold_s: int
    offline_threshold_s: int
    pagination_size: int
    max_posts_per_bot: int
    notify_rights_error: bool
    notify_failures: bool
    retention_enabled: bool
    retention_days: int
    default_drain_mode: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: Setting) -> "SettingDTO":
        return cls(
            id=model.id,
            name=model.name,
            is_current=model.is_current,
            heartbeat_interval_s=model.heartbeat_interval_s,
            online_threshold_s=model.online_threshold_s,
            offline_threshold_s=model.offline_threshold_s,
            pagination_size=model.pagination_size,
            max_posts_per_bot=model.max_posts_per_bot,
            notify_rights_error=model.notify_rights_error,
            notify_failures=model.notify_failures,
            retention_enabled=model.retention_enabled,
            retention_days=model.retention_days,
            default_drain_mode=model.default_drain_mode,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
