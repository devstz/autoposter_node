from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID
from typing import List, Optional

from common.enums import AdminBotFreeMode


@dataclass(slots=True)
class BotListItemDTO:
    bot_id: UUID
    telegram_id: str
    label: str
    status: str
    load_current: int
    load_limit: int
    has_errors: bool


@dataclass(slots=True)
class BotsListViewDTO:
    text: str
    items: List[BotListItemDTO]
    page: int
    total_pages: int
    total_items: int


@dataclass(slots=True)
class BotCardDTO:
    bot_id: UUID
    telegram_id: str
    text: str
    has_errors: bool


@dataclass(slots=True)
class BotFreePromptDTO:
    bot_id: UUID
    telegram_id: str
    text: str


@dataclass(slots=True)
class BotDeletePromptDTO:
    bot_id: UUID
    telegram_id: str
    text: str


@dataclass(slots=True)
class ActionResultDTO:
    bot_id: UUID
    text: str
    mode: Optional[AdminBotFreeMode] = None
