from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass(slots=True)
class GroupListItemDTO:
    group_id: UUID
    tg_chat_id: int
    label: str
    bot_id: Optional[UUID]


@dataclass(slots=True)
class GroupsListViewDTO:
    text: str
    items: List[GroupListItemDTO]
    page: int
    total_pages: int
    total_items: int


@dataclass(slots=True)
class GroupCardDTO:
    group_id: UUID
    tg_chat_id: int
    bot_id: Optional[UUID]
    bot_telegram_id: Optional[str]
    text: str
