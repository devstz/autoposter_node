from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infra.db.models import PostAttempt


class SQLAlchemyPostAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def add(self, attempt: PostAttempt) -> PostAttempt:
        self.__session.add(attempt)
        await self.__session.flush()
        return attempt
    
    async def count_success_in_period(self, *, bot_id: Optional[UUID], seconds: int) -> int:
        since = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        stmt = select(func.count()).select_from(PostAttempt).where(
            and_(
                PostAttempt.created_at >= since,
                PostAttempt.success.is_(True),
                (PostAttempt.bot_id == bot_id) if bot_id else True,
            )
        )
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())

    async def count_fail_in_period(self, *, bot_id: Optional[UUID], seconds: int) -> int:
        since = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        stmt = select(func.count()).select_from(PostAttempt).where(
            and_(
                PostAttempt.created_at >= since,
                PostAttempt.success.is_(False),
                (PostAttempt.bot_id == bot_id) if bot_id else True,
            )
        )
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())

    async def last_send_time_for_bot(self, bot_id: UUID) -> Optional[datetime]:
        stmt = (
            select(PostAttempt.created_at)
            .where(PostAttempt.bot_id == bot_id)
            .order_by(PostAttempt.created_at.desc())
            .limit(1)
        )
        res = await self.__session.execute(stmt)
        return res.scalar_one_or_none()

    async def count_total(self, *, bot_id: Optional[UUID] = None, success: Optional[bool] = None) -> int:
        stmt = select(func.count()).select_from(PostAttempt)
        if bot_id is not None:
            stmt = stmt.where(PostAttempt.bot_id == bot_id)
        if success is not None:
            stmt = stmt.where(PostAttempt.success.is_(success))
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())
