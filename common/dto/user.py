from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from infra.db.models import User


@dataclass(slots=True)
class UserDTO:
    user_id: int
    username: Optional[str]
    is_superuser: bool
    full_name: Optional[str]
    meta: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: User) -> "UserDTO":
        return cls(
            user_id=model.user_id,
            username=model.username,
            is_superuser=model.is_superuser,
            full_name=model.full_name,
            meta=model.meta,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
