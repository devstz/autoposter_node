from __future__ import annotations

from logging import getLogger
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infra.db.models import Group

logger = getLogger(__name__)


class SQLAlchemyGroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def get(self, group_id: UUID) -> Optional[Group]:
        stmt = select(Group).where(Group.id == group_id)
        res = await self.__session.execute(stmt)
        return res.scalars().first()

    async def get_by_tg_chat_id(self, tg_chat_id: int) -> Optional[Group]:
        stmt = select(Group).where(Group.tg_chat_id == tg_chat_id)
        res = await self.__session.execute(stmt)
        return res.scalars().first()

    async def get_or_create(self, *, tg_chat_id: int, type: str, title: str | None = None) -> Group:
        obj = await self.get_by_tg_chat_id(tg_chat_id)
        if obj:
            return obj
        obj = Group(tg_chat_id=tg_chat_id, type=type, title=title)
        self.__session.add(obj)
        await self.__session.flush()
        return obj

    async def add(self, group: Group) -> Group:
        self.__session.add(group)
        await self.__session.flush()
        return group

    async def update(self, group: Group) -> Group:
        await self.__session.flush()
        return group

    async def delete(self, group_id: UUID) -> None:
        obj = await self.get(group_id)
        if obj:
            await self.__session.delete(obj)
            await self.__session.flush()

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Group]:
        stmt = select(Group).order_by(Group.created_at.desc()).limit(limit).offset(offset)
        res = await self.__session.execute(stmt)
        return list(res.scalars().all())

    async def count(self) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(Group)
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())
