from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from infra.db.repo import (
    SQLAlchemyUserRepository,
    SQLAlchemySettingsRepository,
    SQLAlchemyBotRepository,
    SQLAlchemyGroupRepository,
    SQLAlchemyPostRepository,
    SQLAlchemyPostAttemptRepository,
)

from .session import SessionFactory


class SQLAlchemyUnitOfWork:
    _session_factory: async_sessionmaker[AsyncSession]
    _session: Optional[AsyncSession]

    _user_repo: Optional[SQLAlchemyUserRepository]
    _settings_repo: Optional[SQLAlchemySettingsRepository]
    _bot_repo: Optional[SQLAlchemyBotRepository]
    _group_repo: Optional[SQLAlchemyGroupRepository]
    _post_repo: Optional[SQLAlchemyPostRepository]
    _post_attempt_repo: Optional[SQLAlchemyPostAttemptRepository]

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] = SessionFactory) -> None:
        self._session_factory = session_factory
        self._session = None

        self._user_repo = None
        self._settings_repo = None
        self._bot_repo = None
        self._group_repo = None
        self._post_repo = None
        self._post_attempt_repo = None

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

    @property
    def settings_repo(self) -> SQLAlchemySettingsRepository:
        assert self._settings_repo is not None, "settings_repo is not initialized (use within context manager)"
        return self._settings_repo

    @property
    def bot_repo(self) -> SQLAlchemyBotRepository:
        assert self._bot_repo is not None, "bot_repo is not initialized (use within context manager)"
        return self._bot_repo

    @property
    def group_repo(self) -> SQLAlchemyGroupRepository:
        assert self._group_repo is not None, "group_repo is not initialized (use within context manager)"
        return self._group_repo

    @property
    def post_repo(self) -> SQLAlchemyPostRepository:
        assert self._post_repo is not None, "post_repo is not initialized (use within context manager)"
        return self._post_repo

    @property
    def post_attempt_repo(self) -> SQLAlchemyPostAttemptRepository:
        assert self._post_attempt_repo is not None, "post_attempt_repo is not initialized (use within context manager)"
        return self._post_attempt_repo

    # ---------- context manager ----------

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = self._session_factory()
        await self._session.begin()

        self._user_repo = SQLAlchemyUserRepository(self._session)
        self._settings_repo = SQLAlchemySettingsRepository(self._session)
        self._bot_repo = SQLAlchemyBotRepository(self._session)
        self._group_repo = SQLAlchemyGroupRepository(self._session)
        self._post_repo = SQLAlchemyPostRepository(self._session)
        self._post_attempt_repo = SQLAlchemyPostAttemptRepository(self._session)
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
            self._settings_repo = None
            self._bot_repo = None
            self._group_repo = None
            self._post_repo = None
            self._post_attempt_repo = None

        return False

    # ---------- optional helpers ----------

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


def get_uow() -> SQLAlchemyUnitOfWork:
    return SQLAlchemyUnitOfWork(SessionFactory)
