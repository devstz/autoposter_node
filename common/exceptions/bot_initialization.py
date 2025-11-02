from __future__ import annotations


class BotInitializationError(RuntimeError):
    """Base error for bot initialization use case."""


class BotInitializationSettingsMissingError(BotInitializationError):
    """Raised when there is no active settings profile."""


class BotInitializationIPConflictError(BotInitializationError):
    """Raised when another active bot with the same IP already exists."""

