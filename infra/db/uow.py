from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from infra.db.repo import (
    SQLAlchemyUserRepository,
)

from .session import SessionFactory


class SQLAlchemyUnitOfWork:
    _session_factory: async_sessionmaker[AsyncSession]
    _session: Optional[AsyncSession]

    _user_repo: Optional[SQLAlchemyUserRepository]

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] = SessionFactory) -> None:
        self._session_factory = session_factory
        self._session = None

        self._user_repo = None
        self._group_repo = None
        self._admin_repo = None
        self._spammer_repo = None

    # ---------- public accessors ----------

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("SQLAlchemyUnitOfWork is not entered. Use 'async with SQLAlchemyUnitOfWork(...) as uow:'")
        return self._session

    @property
    def user_repo(self) -> SQLAlchemyUserRepository:
        assert self._user_repo is not None, "user_repo is not initialized (use within context manager)"
        return self._user_repo

    # ---------- context manager ----------

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = self._session_factory()
        await self._session.begin()

        self._user_repo = SQLAlchemyUserRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, traceback) -> bool:
        if self._session is None:
            return False

        try:
            if exc_type:
                await self._session.rollback()
            else:
                await self._session.commit()
        finally:
            await self._session.close()
            self._session = None
            self._user_repo = None

        return False

    # ---------- optional helpers ----------

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


def get_uow() -> SQLAlchemyUnitOfWork:
    return SQLAlchemyUnitOfWork(SessionFactory)
