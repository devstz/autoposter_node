from __future__ import annotations

from logging import getLogger
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infra.db.models import User

logger = getLogger(__name__)


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def count_users(
        self,
        *,
        is_superuser: Optional[bool] = None,
        username_like: Optional[str] = None,
    ) -> int:
        stmt = select(func.count()).select_from(User)

        conditions = []
        if is_superuser is not None:
            conditions.append(User.is_superuser == is_superuser)
        if username_like:
            conditions.append(User.username.ilike(f"%{username_like}%"))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def search(
        self,
        *,
        is_superuser: Optional[bool] = None,
        username_like: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        stmt = select(User)

        conditions = []
        if is_superuser is not None:
            conditions.append(User.is_superuser == is_superuser)
        if username_like:
            conditions.append(User.username.ilike(f"%{username_like}%"))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User) -> User:
        await self.session.flush()
        return user

    async def delete(self, user_id: int) -> None:
        user = await self.get(user_id)
        if user is not None:
            await self.session.delete(user)
            await self.session.flush()
