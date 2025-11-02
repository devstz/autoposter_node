from __future__ import annotations

from dataclasses import dataclass

from .bot import BotDTO
from common.enums import BotInitializationAction


@dataclass(slots=True)
class BotInitializationResult:
    bot: BotDTO
    action: BotInitializationAction
