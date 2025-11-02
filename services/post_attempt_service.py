from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from infra.db.models import PostAttempt
from infra.db.uow import SQLAlchemyUnitOfWork


class PostAttemptService:
    def __init__(self, uow: SQLAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, attempt: PostAttempt):
        await self._uow.post_attempt_repo.add(attempt)
        return attempt

    async def count_success_in_period(self, *, bot_id: Optional[UUID], seconds: int) -> int:
        return await self._uow.post_attempt_repo.count_success_in_period(bot_id=bot_id, seconds=seconds)

    async def count_fail_in_period(self, *, bot_id: Optional[UUID], seconds: int) -> int:
        return await self._uow.post_attempt_repo.count_fail_in_period(bot_id=bot_id, seconds=seconds)

    async def last_send_time_for_bot(self, bot_id: UUID) -> Optional[datetime]:
        return await self._uow.post_attempt_repo.last_send_time_for_bot(bot_id)

    async def count_total(self, *, bot_id: Optional[UUID] = None, success: Optional[bool] = None) -> int:
        return await self._uow.post_attempt_repo.count_total(bot_id=bot_id, success=success)
