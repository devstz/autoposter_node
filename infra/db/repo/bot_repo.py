from __future__ import annotations

from datetime import datetime, timezone
from logging import getLogger
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infra.db.models import Bot, Post

logger = getLogger(__name__)


class SQLAlchemyBotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def get(self, bot_id: UUID) -> Optional[Bot]:
        stmt = select(Bot).where(Bot.id == bot_id)
        res = await self.__session.execute(stmt)
        return res.scalars().first()

    async def get_by_ip(self, server_ip: str, *, active_only: bool = True) -> Optional[Bot]:
        stmt = select(Bot).where(Bot.server_ip == server_ip)
        if active_only:
            stmt = stmt.where(Bot.deactivated.is_(False))
        res = await self.__session.execute(stmt)
        return res.scalars().first()

    async def get_by_token(self, token: str) -> Optional[Bot]:
        stmt = select(Bot).where(Bot.token == token)
        res = await self.__session.execute(stmt)
        return res.scalars().first()

    async def add(self, bot: Bot) -> Bot:
        self.__session.add(bot)
        await self.__session.flush()
        return bot

    async def update(self, bot: Bot) -> Bot:
        await self.__session.flush()
        return bot

    async def delete(self, bot_id: UUID) -> None:
        obj = await self.get(bot_id)
        if obj:
            await self.__session.delete(obj)
            await self.__session.flush()

    async def update_heartbeat(self, bot_id: UUID, when: Optional[datetime] = None) -> None:
        when = when or datetime.now(timezone.utc)
        await self.__session.execute(
            update(Bot).where(Bot.id == bot_id).values(last_heartbeat_at=when)
        )
        await self.__session.flush()

    async def mark_self_destruction(self, bot_id: UUID) -> None:
        await self.__session.execute(
            update(Bot).where(Bot.id == bot_id).values(self_destruction=True)
        )
        await self.__session.flush()

    async def mark_deactivated(self, bot_id: UUID) -> None:
        await self.__session.execute(
            update(Bot).where(Bot.id == bot_id).values(deactivated=True)
        )
        await self.__session.flush()

    async def has_ip_conflict(self, server_ip: str, token: str) -> bool:
        # another active bot on the same IP with a different token
        stmt = select(func.count()).select_from(Bot).where(
            and_(
                Bot.server_ip == server_ip,
                Bot.token != token,
                Bot.deactivated.is_(False),
            )
        )
        res = await self.__session.execute(stmt)
        return int(res.scalar_one()) > 0

    async def count_active_posts(self, bot_id: UUID) -> int:
        stmt = select(func.count()).select_from(Post).where(
            and_(Post.bot_id == bot_id, Post.status.in_(["active", "paused", "error"]))
        )
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())

    async def loads_by_bot(self, bot_ids: Optional[list[UUID]] = None) -> dict[UUID, int]:
        stmt = select(Post.bot_id, func.count()).where(Post.status.in_(["active", "paused", "error"]))
        if bot_ids:
            stmt = stmt.where(Post.bot_id.in_(bot_ids))
        stmt = stmt.group_by(Post.bot_id)
        res = await self.__session.execute(stmt)
        rows = res.all()
        out: dict[UUID, int] = {}
        for bot_id_val, count in rows:
            if bot_id_val:
                out[bot_id_val] = int(count)
        return out

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Bot]:
        stmt = select(Bot).order_by(Bot.created_at.desc()).limit(limit).offset(offset)
        res = await self.__session.execute(stmt)
        return list(res.scalars().all())

    async def search(
        self,
        *,
        username_like: Optional[str] = None,
        name_like: Optional[str] = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Bot]:
        stmt = select(Bot)
        if username_like:
            stmt = stmt.where(Bot.username.ilike(f"%{username_like}%"))
        if name_like:
            stmt = stmt.where(Bot.name.ilike(f"%{name_like}%"))
        if active_only:
            stmt = stmt.where(Bot.deactivated.is_(False))
        stmt = stmt.order_by(Bot.created_at.desc()).limit(limit).offset(offset)
        res = await self.__session.execute(stmt)
        return list(res.scalars().all())

    async def count(
        self,
        *,
        active_only: bool = False,
        username_like: Optional[str] = None,
        name_like: Optional[str] = None,
    ) -> int:
        stmt = select(func.count()).select_from(Bot)
        if active_only:
            stmt = stmt.where(Bot.deactivated.is_(False))
        if username_like:
            stmt = stmt.where(Bot.username.ilike(f"%{username_like}%"))
        if name_like:
            stmt = stmt.where(Bot.name.ilike(f"%{name_like}%"))
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())
