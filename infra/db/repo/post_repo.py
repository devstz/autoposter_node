from __future__ import annotations

from datetime import datetime, timezone, timedelta
from logging import getLogger
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infra.db.models import Post, PostStatus

logger = getLogger(__name__)


ACTIVE_STATUSES = (PostStatus.ACTIVE.value, PostStatus.PAUSED.value, PostStatus.ERROR.value)


class SQLAlchemyPostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def get(self, post_id: UUID) -> Optional[Post]:
        stmt = select(Post).where(Post.id == post_id)
        res = await self.__session.execute(stmt)
        return res.scalars().first()

    async def create(
        self,
        *,
        group_id: UUID,
        source_channel_username: str,
        source_message_id: int,
        status: str = PostStatus.ACTIVE.value,
        bot_id: Optional[UUID] = None,
    ) -> Post:
        obj = Post(
            group_id=group_id,
            bot_id=bot_id if bot_id else None,
            status=status,
            source_channel_username=source_channel_username,
            source_message_id=source_message_id,
        )
        self.__session.add(obj)
        await self.__session.flush()
        return obj

    async def get_by_source(self, *, group_id: UUID, source_channel_username: str, source_message_id: int) -> Optional[Post]:
        stmt = select(Post).where(
            and_(
                Post.group_id == group_id,
                Post.source_channel_username == source_channel_username,
                Post.source_message_id == source_message_id,
            )
        )
        res = await self.__session.execute(stmt)
        return res.scalars().first()

    async def find_unassigned_active(self, *, limit: int = 100, offset: int = 0) -> list[Post]:
        stmt = (
            select(Post)
            .where(and_(Post.bot_id.is_(None), Post.status.in_(ACTIVE_STATUSES)))
            .order_by(Post.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.__session.execute(stmt)
        return list(res.scalars().all())

    async def count_active_for_bot(self, bot_id: UUID) -> int:
        stmt = select(func.count()).select_from(Post).where(
            and_(Post.bot_id == bot_id, Post.status.in_(ACTIVE_STATUSES))
        )
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())

    async def assign_to_bot(self, post_id: UUID, bot_id: UUID) -> None:
        await self.__session.execute(
            update(Post).where(Post.id == post_id).values(bot_id=bot_id)
        )
        await self.__session.flush()

    async def bulk_unassign_by_bot(self, bot_id: UUID) -> int:
        res = await self.__session.execute(
            update(Post)
            .where(and_(Post.bot_id == bot_id, Post.status.in_(ACTIVE_STATUSES)))
            .values(bot_id=None)
            .returning(Post.id)
        )
        await self.__session.flush()
        return len(res.fetchall())

    async def bulk_pause_by_bot(self, bot_id: UUID) -> int:
        res = await self.__session.execute(
            update(Post)
            .where(and_(Post.bot_id == bot_id, Post.status == PostStatus.ACTIVE.value))
            .values(status=PostStatus.PAUSED.value)
            .returning(Post.id)
        )
        await self.__session.flush()
        return len(res.fetchall())

    async def mark_error(self, post_id: UUID, error: str) -> None:
        await self.__session.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(status=PostStatus.ERROR.value, last_error=error, last_attempt_at=datetime.now(timezone.utc))
        )
        await self.__session.flush()

    async def mark_done(self, post_id: UUID) -> None:
        await self.__session.execute(
            update(Post).where(Post.id == post_id).values(status=PostStatus.DONE.value)
        )
        await self.__session.flush()

    async def touch_attempt_time(self, post_id: UUID) -> None:
        await self.__session.execute(
            update(Post).where(Post.id == post_id).values(last_attempt_at=datetime.now(timezone.utc))
        )
        await self.__session.flush()

    async def list_by_bot(self, bot_id: UUID, *, limit: int = 100, offset: int = 0) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.bot_id == bot_id)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.__session.execute(stmt)
        return list(res.scalars().all())

    async def list_by_group(self, group_id: UUID, *, limit: int = 100, offset: int = 0) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.group_id == group_id)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.__session.execute(stmt)
        return list(res.scalars().all())
