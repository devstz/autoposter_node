from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass(slots=True)
class PostListItemDTO:
    post_id: UUID
    label: str
    status: str
    bot_id: Optional[UUID]
    group_id: UUID


@dataclass(slots=True)
class PostsListViewDTO:
    text: str
    items: List[PostListItemDTO]
    status: str
    page: int
    total_pages: int
    total_items: int


@dataclass(slots=True)
class PostCardDTO:
    post_id: UUID
    status: str
    text: str
    bot_id: Optional[UUID]
    group_id: UUID
