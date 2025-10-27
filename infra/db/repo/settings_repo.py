from __future__ import annotations

from logging import getLogger
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infra.db.models import Setting

logger = getLogger(__name__)


class SQLAlchemySettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def get(self, setting_id: UUID) -> Optional[Setting]:
        stmt = select(Setting).where(Setting.id == setting_id)
        res = await self.__session.execute(stmt)
        return res.scalars().first()

    async def get_current(self) -> Optional[Setting]:
        stmt = select(Setting).where(Setting.is_current.is_(True))
        res = await self.__session.execute(stmt)
        return res.scalars().first()

    async def set_current(self, setting_id: UUID) -> Setting:
        # Unset previous current
        await self.__session.execute(update(Setting).values(is_current=False))
        # Set new current
        await self.__session.execute(
            update(Setting)
            .where(Setting.id == setting_id)
            .values(is_current=True)
        )
        await self.__session.flush()
        obj = await self.get(setting_id)
        assert obj is not None
        return obj

    async def add(self, setting: Setting) -> Setting:
        self.__session.add(setting)
        await self.__session.flush()
        return setting

    async def update(self, setting: Setting) -> Setting:
        await self.__session.flush()
        return setting

    async def delete(self, setting_id: UUID) -> None:
        obj = await self.get(setting_id)
        if obj:
            await self.__session.delete(obj)
            await self.__session.flush()

    async def count(self, *, name_like: Optional[str] = None) -> int:
        stmt = select(func.count()).select_from(Setting)
        if name_like:
            stmt = stmt.where(Setting.name.ilike(f"%{name_like}%"))
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())

    async def list(self, *, name_like: Optional[str] = None, limit: int = 100, offset: int = 0) -> list[Setting]:
        stmt = select(Setting)
        if name_like:
            stmt = stmt.where(Setting.name.ilike(f"%{name_like}%"))
        stmt = stmt.order_by(Setting.created_at.desc()).limit(limit).offset(offset)
        res = await self.__session.execute(stmt)
        return list(res.scalars().all())

