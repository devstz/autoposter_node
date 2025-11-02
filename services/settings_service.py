from __future__ import annotations

from typing import Optional
from uuid import UUID

from common.dto import SettingDTO
from infra.db.models import Setting
from infra.db.repo import SQLAlchemySettingsRepository


class SettingsService:
    def __init__(self, repo: SQLAlchemySettingsRepository) -> None:
        self._repo = repo

    async def get(self, setting_id: UUID) -> Optional[SettingDTO]:
        setting = await self._repo.get(setting_id)
        return SettingDTO.from_model(setting) if setting else None

    async def get_current(self) -> Optional[SettingDTO]:
        setting = await self._repo.get_current()
        return SettingDTO.from_model(setting) if setting else None

    async def set_current(self, setting_id: UUID) -> SettingDTO:
        setting = await self._repo.set_current(setting_id)
        return SettingDTO.from_model(setting)

    async def add(self, setting: Setting) -> SettingDTO:
        await self._repo.add(setting)
        return SettingDTO.from_model(setting)

    async def update(self, setting: Setting) -> SettingDTO:
        await self._repo.update(setting)
        return SettingDTO.from_model(setting)

    async def delete(self, setting_id: UUID) -> None:
        await self._repo.delete(setting_id)

    async def count(self, *, name_like: Optional[str] = None) -> int:
        return await self._repo.count(name_like=name_like)

    async def list(
        self,
        *,
        name_like: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SettingDTO]:
        settings = await self._repo.list(name_like=name_like, limit=limit, offset=offset)
        return [SettingDTO.from_model(setting) for setting in settings]
