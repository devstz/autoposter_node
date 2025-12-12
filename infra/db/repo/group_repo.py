from __future__ import annotations

import time
from logging import getLogger
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from infra.db.models import Group

logger = getLogger(__name__)


@dataclass(slots=True)
class AssignToBotResult:
    newly_assigned: list[Group]
    already_assigned: list[Group]
    reassigned: list[Tuple[Group, UUID]]


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

    async def list_by_bot(self, bot_id: UUID, *, limit: int = 500, offset: int = 0) -> list[Group]:
        stmt = (
            select(Group)
            .where(Group.assigned_bot_id == bot_id)
            .order_by(Group.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.__session.execute(stmt)
        return list(res.scalars().all())

    async def list_bound(self, *, limit: int = 1000, offset: int = 0) -> list[Group]:
        start_time = time.perf_counter()
        stmt = (
            select(Group)
            .where(Group.assigned_bot_id.is_not(None))
            .order_by(Group.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.__session.execute(stmt)
        groups = list(res.scalars().all())
        elapsed = time.perf_counter() - start_time
        logger.info(
            "list_bound: fetched %d groups (limit=%d, offset=%d) in %.3f seconds",
            len(groups),
            limit,
            offset,
            elapsed,
        )
        return groups

    async def count_bound(self) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(Group).where(Group.assigned_bot_id.is_not(None))
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())

    async def assign_to_bot(self, *, bot_id: UUID, tg_chat_ids: list[int]) -> AssignToBotResult:
        # Upsert-like: create Group entries if missing, set assigned_bot_id
        newly_assigned: list[Group] = []
        already_assigned: list[Group] = []
        reassigned: list[Tuple[Group, UUID]] = []

        seen: set[int] = set()
        for chat_id in tg_chat_ids:
            if chat_id in seen:
                continue
            seen.add(chat_id)

            group = await self.get_by_tg_chat_id(chat_id)
            if not group:
                # type unknown at this point; default to 'supergroup'
                group = Group(tg_chat_id=chat_id, type="supergroup")
                self.__session.add(group)
                group.assigned_bot_id = bot_id
                newly_assigned.append(group)
                continue

            previous_bot_id = group.assigned_bot_id
            if previous_bot_id == bot_id:
                already_assigned.append(group)
                continue

            group.assigned_bot_id = bot_id
            if previous_bot_id is None:
                newly_assigned.append(group)
            else:
                reassigned.append((group, previous_bot_id))

        await self.__session.flush()
        return AssignToBotResult(
            newly_assigned=newly_assigned,
            already_assigned=already_assigned,
            reassigned=reassigned,
        )

    async def unassign_from_bot(self, *, bot_id: UUID, tg_chat_ids: list[int] | None = None) -> int:
        # Clears assigned_bot_id for provided groups or all groups of the bot
        q = select(Group)
        q = q.where(Group.assigned_bot_id == bot_id)
        if tg_chat_ids:
            q = q.where(Group.tg_chat_id.in_(tg_chat_ids))
        res = await self.__session.execute(q)
        groups = list(res.scalars().all())
        for g in groups:
            g.assigned_bot_id = None
        await self.__session.flush()
        return len(groups)

    async def update_metadata(
        self,
        group_id: UUID,
        *,
        title: str | None = None,
        username: str | None = None,
        refreshed_at: datetime | None = None,
    ) -> Optional[Group]:
        # Используем прямой UPDATE statement для избежания проблем с optimistic locking
        # Это более эффективно и безопасно при параллельных обновлениях
        update_values = {}
        if title is not None and title:
            update_values["title"] = title
        if username is not None and username:
            update_values["username"] = username
        if refreshed_at is not None:
            update_values["metadata_refreshed_at"] = refreshed_at
        
        if not update_values:
            # Если нечего обновлять, просто возвращаем группу
            return await self.get(group_id)
        
        # Выполняем прямой UPDATE - это избегает StaleDataError из-за optimistic locking
        stmt = update(Group).where(Group.id == group_id).values(**update_values)
        await self.__session.execute(stmt)
        await self.__session.flush()
        
        # Перезагружаем обновленную запись
        return await self.get(group_id)
