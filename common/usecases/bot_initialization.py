from __future__ import annotations

from typing import Optional

from common.dto import BotInitializationResult
from common.enums import BotInitializationAction
from common.exceptions import (
    BotInitializationError,
    BotInitializationIPConflictError,
    BotInitializationSettingsMissingError,
)
from infra.db.models import Bot
from services import BotService, SettingsService, SystemService


class BotInitializationUseCase:
    def __init__(
        self,
        bot_service: BotService,
        settings_service: SettingsService,
        system_service: SystemService,
    ) -> None:
        self._bot_service = bot_service
        self._settings_service = settings_service
        self._system_service = system_service

    async def __call__(
        self,
        *,
        bot_id: int,
        token: str,
        username: Optional[str],
        full_name: Optional[str],
        server_ip: Optional[str] = None,
    ) -> BotInitializationResult:
        detected_ip = server_ip or self._system_service.detect_primary_ip()

        settings = await self._settings_service.get_current()
        if settings is None:
            raise BotInitializationSettingsMissingError("Active settings profile is not configured")

        if await self._bot_service.has_ip_conflict(detected_ip, token):
            raise BotInitializationIPConflictError(
                f"Bot with different token already registered on IP {detected_ip}"
            )

        existing = await self._bot_service.get_by_token(token)

        if existing is None:
            bot_model = Bot(
                bot_id=bot_id,
                username=username,
                name=full_name or username,
                token=token,
                server_ip=detected_ip,
                settings_id=settings.id,
                max_posts=settings.max_posts_per_bot,
            )
            bot_dto = await self._bot_service.add(bot_model)
        else:
            bot_dto = await self._bot_service.update_fields(
                existing.id,
                username=username,
                name=full_name or existing.name,
                server_ip=detected_ip,
                settings_id=settings.id,
                max_posts=settings.max_posts_per_bot,
            )

        refreshed = await self._bot_service.get(bot_dto.id)
        if refreshed is None:
            raise BotInitializationError("Failed to load bot after initialization")

        if refreshed.self_destruction:
            if not refreshed.deactivated:
                refreshed = await self._bot_service.update_fields(refreshed.id, deactivated=True)
            return BotInitializationResult(refreshed, BotInitializationAction.SELF_DESTRUCT)

        if refreshed.deactivated:
            return BotInitializationResult(refreshed, BotInitializationAction.STOP)

        refreshed = await self._bot_service.update_fields(refreshed.id, deactivated=False)
        await self._bot_service.update_heartbeat(refreshed.id)
        final_state = await self._bot_service.get(refreshed.id)
        if final_state is None:
            raise BotInitializationError("Failed to load bot after heartbeat update")

        return BotInitializationResult(final_state, BotInitializationAction.CONTINUE)
