from __future__ import annotations

from typing import Optional
from uuid import UUID

from common.dto import PostDTO
from infra.db.models import PostStatus, Post
from infra.db.uow import SQLAlchemyUnitOfWork

class PostService:
    def __init__(self, uow: SQLAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def get(self, post_id: UUID) -> Optional[PostDTO]:
        async with self._uow:
            post = await self._uow.post_repo.get(post_id)
        return PostDTO.from_model(post) if post else None

    async def get_by_source(
        self,
        *,
        group_id: UUID,
        source_channel_username: str,
        source_message_id: int,
    ) -> Optional[PostDTO]:
        post = await self._uow.post_repo.get_by_source(
            group_id=group_id,
            source_channel_username=source_channel_username,
            source_message_id=source_message_id,
        )
        return PostDTO.from_model(post) if post else None

    async def create(
        self,
        *,
        group_id: UUID,
        target_chat_id: int,
        distribution_name: str | None,
        source_channel_username: str,
        source_message_id: int,
        source_channel_id: Optional[int] = None,
        status: str = PostStatus.ACTIVE.value,
        bot_id: Optional[UUID] = None,
        pause_between_attempts_s: int = 60,
        delete_last_attempt: bool = False,
        pin_after_post: bool = False,
        num_attempt_for_pin_post: Optional[int] = None,
        target_attempts: int = 1,
        notify_on_failure: bool = True,
    ):
        post = await self._uow.post_repo.create(
            group_id=group_id,
            target_chat_id=target_chat_id,
            distribution_name=distribution_name,
            source_channel_username=source_channel_username,
            source_message_id=source_message_id,
            source_channel_id=source_channel_id,
            status=status,
            bot_id=bot_id,
            pause_between_attempts_s=pause_between_attempts_s,
            delete_last_attempt=delete_last_attempt,
            pin_after_post=pin_after_post,
            num_attempt_for_pin_post=num_attempt_for_pin_post,
            target_attempts=target_attempts,
            notify_on_failure=notify_on_failure,
        )
        return post

    async def find_unassigned_active(self, *, limit: int = 100, offset: int = 0) -> list[PostDTO]:
        posts = await self._uow.post_repo.find_unassigned_active(limit=limit, offset=offset)
        return [PostDTO.from_model(post) for post in posts]

    async def count_active_for_bot(self, bot_id: UUID) -> int:
        return await self._uow.post_repo.count_active_for_bot(bot_id)

    async def assign_to_bot(self, post_id: UUID, bot_id: UUID) -> None:
        await self._uow.post_repo.assign_to_bot(post_id, bot_id)

    async def bulk_unassign_by_bot(self, bot_id: UUID) -> int:
        return await self._uow.post_repo.bulk_unassign_by_bot(bot_id)

    async def bulk_pause_by_bot(self, bot_id: UUID) -> int:
        return await self._uow.post_repo.bulk_pause_by_bot(bot_id)

    async def mark_error(self, post_id: UUID, error: str) -> None:
        await self._uow.post_repo.mark_error(post_id, error)

    async def mark_done(self, post_id: UUID) -> None:
        await self._uow.post_repo.mark_done(post_id)

    async def touch_attempt_time(self, post_id: UUID) -> None:
        await self._uow.post_repo.touch_attempt_time(post_id)

    async def list_by_bot(self, bot_id: UUID, *, limit: int = 100, offset: int = 0):
        posts = await self._uow.post_repo.list_by_bot(bot_id, limit=limit, offset=offset)
        return posts

    async def list_by_group(self, group_id: UUID, *, limit: int = 100, offset: int = 0) -> list[PostDTO]:
        posts = await self._uow.post_repo.list_by_group(group_id, limit=limit, offset=offset)
        return [PostDTO.from_model(post) for post in posts]

    async def list_by_status(self, status: str, *, limit: int = 100, offset: int = 0) -> list[PostDTO]:
        posts = await self._uow.post_repo.list_by_status(status, limit=limit, offset=offset)
        return [PostDTO.from_model(post) for post in posts]

    async def count_by_status(self, status: str) -> int:
        return await self._uow.post_repo.count_by_status(status)

    async def count_errors_for_bot(self, bot_id: UUID) -> int:
        return await self._uow.post_repo.count_errors_for_bot(bot_id)

    async def delete_active_by_groups(self, group_ids: list[UUID]) -> int:
        return await self._uow.post_repo.delete_active_by_groups(group_ids)

    async def bulk_pause_distribution(
        self,
        *,
        source_channel_username: str | None,
        source_channel_id: int | None,
        source_message_id: int,
    ) -> int:
        return await self._uow.post_repo.bulk_pause_by_distribution(
            source_channel_username=source_channel_username,
            source_channel_id=source_channel_id,
            source_message_id=source_message_id,
        )

    async def bulk_resume_distribution(
        self,
        *,
        source_channel_username: str | None,
        source_channel_id: int | None,
        source_message_id: int,
    ) -> int:
        return await self._uow.post_repo.bulk_resume_by_distribution(
            source_channel_username=source_channel_username,
            source_channel_id=source_channel_id,
            source_message_id=source_message_id,
        )

    async def bulk_set_notify_distribution(
        self,
        *,
        source_channel_username: str | None,
        source_channel_id: int | None,
        source_message_id: int,
        value: bool,
    ) -> int:
        return await self._uow.post_repo.bulk_set_notify_by_distribution(
            source_channel_username=source_channel_username,
            source_channel_id=source_channel_id,
            source_message_id=source_message_id,
            value=value,
        )

    async def pause(self, post_id: UUID) -> None:
        await self._uow.post_repo.pause(post_id)

    async def resolve_distribution_id_by_post(self, post_id: UUID) -> UUID | None:
        post = await self._uow.post_repo.get(post_id)
        if post is None:
            return None
        return await self._uow.post_repo.resolve_distribution_id_by_source(
            source_channel_username=post.source_channel_username,
            source_channel_id=post.source_channel_id,
            source_message_id=post.source_message_id,
        )

    async def resume(self, post_id: UUID) -> None:
        await self._uow.post_repo.resume(post_id)

    async def count_distributions(self) -> int:
        return await self._uow.post_repo.count_distributions()

    async def list_distributions(self, *, limit: int, offset: int) -> list[dict]:
        return await self._uow.post_repo.list_distributions(limit=limit, offset=offset)

    async def get_distribution_summary(self, distribution_id: UUID) -> dict | None:
        return await self._uow.post_repo.get_distribution_summary(distribution_id)

    async def list_distribution_posts(
        self,
        *,
        source_channel_username: str | None,
        source_channel_id: int | None,
        source_message_id: int,
    ):
        posts = await self._uow.post_repo.list_distribution_posts(
            source_channel_username=source_channel_username,
            source_channel_id=source_channel_id,
            source_message_id=source_message_id,
        )
        return [PostDTO.from_model(post) for post in posts]
