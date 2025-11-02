from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from infra.db.models import Group


@dataclass(slots=True)
class GroupDTO:
    id: UUID
    tg_chat_id: int
    type: str
    title: Optional[str]
    username: Optional[str]
    last_post_at: Optional[datetime]
    assigned_bot_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    metadata_refreshed_at: Optional[datetime]

    @classmethod
    def from_model(cls, model: Group) -> "GroupDTO":
        return cls(
            id=model.id,
            tg_chat_id=model.tg_chat_id,
            type=model.type,
            title=model.title,
            username=getattr(model, "username", None),
            last_post_at=model.last_post_at,
            assigned_bot_id=model.assigned_bot_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata_refreshed_at=getattr(model, "metadata_refreshed_at", None),
        )


@dataclass(slots=True)
class GroupReassignmentDTO:
    group: GroupDTO
    previous_bot_id: UUID


@dataclass(slots=True)
class GroupAssignResultDTO:
    newly_assigned: list[GroupDTO]
    already_assigned: list[GroupDTO]
    reassigned: list[GroupReassignmentDTO]
