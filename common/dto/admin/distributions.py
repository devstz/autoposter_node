from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID


@dataclass(slots=True)
class DistributionListItemDTO:
    distribution_id: UUID
    name: Optional[str]
    label: str
    created_at: datetime
    total_posts: int
    status_counts: Dict[str, int]


@dataclass(slots=True)
class DistributionsListViewDTO:
    text: str
    items: List[DistributionListItemDTO]
    page: int
    total_pages: int
    total_items: int


@dataclass(slots=True)
class DistributionPostItemDTO:
    group_title: str
    chat_id: int
    bot_label: str
    status: str


@dataclass(slots=True)
class DistributionCardDTO:
    distribution_id: UUID
    name: Optional[str]
    source_channel_username: Optional[str]
    source_channel_id: Optional[int]
    source_message_id: int
    created_at: datetime
    updated_at: datetime
    total_posts: int
    status_counts: Dict[str, int]
    items: List[DistributionPostItemDTO]
    text: str
    notify_on_failure: bool


@dataclass(slots=True)
class DistributionGroupListItemDTO:
    post_id: UUID
    group_id: UUID
    chat_id: int
    label: str
    status: str


@dataclass(slots=True)
class DistributionGroupsViewDTO:
    text: str
    items: List[DistributionGroupListItemDTO]
    page: int
    total_pages: int
    total_items: int
    anchor_post_id: Optional[UUID]


@dataclass(slots=True)
class DistributionGroupCardDTO:
    post_id: UUID
    group_id: UUID
    text: str


@dataclass(slots=True)
class DistributionContextDTO:
    distribution_id: UUID
    name: Optional[str]
    source_channel_username: Optional[str]
    source_channel_id: Optional[int]
    source_message_id: int
    pause_between_attempts_s: int
    delete_last_attempt: bool
    pin_after_post: bool
    num_attempt_for_pin_post: Optional[int]
    target_attempts: int
    notify_on_failure: bool
