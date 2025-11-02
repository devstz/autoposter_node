from __future__ import annotations

from typing import Optional

from common.dto import UserDTO
from infra.db.models import User
from infra.db.repo import SQLAlchemyUserRepository


class UserService:
    def __init__(self, repo: SQLAlchemyUserRepository) -> None:
        self._repo = repo

    async def get(self, user_id: int) -> Optional[UserDTO]:
        user = await self._repo.get(user_id)
        return UserDTO.from_model(user) if user else None

    async def get_by_username(self, username: str) -> Optional[UserDTO]:
        user = await self._repo.get_by_username(username)
        return UserDTO.from_model(user) if user else None

    async def count_users(
        self,
        *,
        is_superuser: Optional[bool] = None,
        username_like: Optional[str] = None,
    ) -> int:
        return await self._repo.count_users(
            is_superuser=is_superuser,
            username_like=username_like,
        )

    async def search(
        self,
        *,
        is_superuser: Optional[bool] = None,
        username_like: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserDTO]:
        users = await self._repo.search(
            is_superuser=is_superuser,
            username_like=username_like,
            limit=limit,
            offset=offset,
        )
        return [UserDTO.from_model(user) for user in users]

    async def add(self, user: User) -> UserDTO:
        await self._repo.add(user)
        return UserDTO.from_model(user)

    async def update(self, user: User) -> UserDTO:
        await self._repo.update(user)
        return UserDTO.from_model(user)

    async def delete(self, user_id: int) -> None:
        await self._repo.delete(user_id)
