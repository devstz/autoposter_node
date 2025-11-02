from __future__ import annotations

from enum import Enum


class BotInitializationAction(str, Enum):
    CONTINUE = "continue"
    STOP = "stop"
    SELF_DESTRUCT = "self_destruction"

