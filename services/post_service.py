from __future__ import annotations

from typing import Optional, Iterable
from uuid import UUID

from common.dto import PostDTO, GroupDTO, DistributionContextDTO
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

    async def increment_attempt_count(self, post_id: UUID) -> None:
        """Atomically increment count_attempts and update last_attempt_at."""
        await self._uow.post_repo.increment_attempt_count(post_id)

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
        distribution_name: str | None,
    ) -> int:
        return await self._uow.post_repo.bulk_pause_by_distribution(
            distribution_name=distribution_name,
        )

    async def bulk_resume_distribution(
        self,
        *,
        distribution_name: str | None,
    ) -> int:
        return await self._uow.post_repo.bulk_resume_by_distribution(
            distribution_name=distribution_name,
        )

    async def bulk_set_notify_distribution(
        self,
        *,
        distribution_name: str | None,
        value: bool,
    ) -> int:
        return await self._uow.post_repo.bulk_set_notify_by_distribution(
            distribution_name=distribution_name,
            value=value,
        )

    async def delete_distribution(
        self,
        *,
        distribution_name: str | None,
    ) -> int:
        return await self._uow.post_repo.delete_distribution(
            distribution_name=distribution_name,
        )

    async def pause(self, post_id: UUID) -> None:
        await self._uow.post_repo.pause(post_id)

    async def resolve_distribution_id_by_post(self, post_id: UUID) -> UUID | None:
        """Resolve distribution_id by post_id using distribution_name."""
        post = await self._uow.post_repo.get(post_id)
        if post is None:
            return None
        return await self._uow.post_repo.resolve_distribution_id_by_name(
            distribution_name=post.distribution_name,
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
        distribution_name: str | None,
    ):
        posts = await self._uow.post_repo.list_distribution_posts(
            distribution_name=distribution_name,
        )
        return [PostDTO.from_model(post) for post in posts]

    async def get_distribution_context(self, distribution_id: UUID) -> DistributionContextDTO | None:
        summary = await self.get_distribution_summary(distribution_id)
        if summary is None:
            return None
        source_message_id = summary.get("source_message_id")
        if source_message_id is None:
            return None
        distribution_name = summary.get("distribution_name")
        config = await self._uow.post_repo.get_distribution_config(
            distribution_name=distribution_name,
        )
        if config is None:
            return None
        return DistributionContextDTO(
            distribution_id=distribution_id,
            name=distribution_name,
            source_channel_username=summary.get("source_channel_username"),
            source_channel_id=summary.get("source_channel_id"),
            source_message_id=int(source_message_id),
            pause_between_attempts_s=int(config.get("pause_between_attempts_s") or 60),
            delete_last_attempt=bool(config.get("delete_last_attempt")),
            pin_after_post=bool(config.get("pin_after_post")),
            num_attempt_for_pin_post=config.get("num_attempt_for_pin_post"),
            target_attempts=int(config.get("target_attempts") or 1),
            notify_on_failure=bool(summary.get("notify_on_failure", True)),
        )

    async def delete_distribution_groups(self, distribution_id: UUID, group_ids: list[UUID]) -> int:
        if not group_ids:
            return 0
        summary = await self.get_distribution_summary(distribution_id)
        if summary is None:
            return 0
        return await self._uow.post_repo.delete_distribution_groups(
            distribution_name=summary.get("distribution_name"),
            group_ids=group_ids,
        )

    async def groups_distribution_usage(self, group_ids: list[UUID]) -> dict[UUID, UUID]:
        raw = await self._uow.post_repo.groups_distribution_usage(group_ids)
        result: dict[UUID, UUID] = {}
        for group_id, distribution_id in raw.items():
            if not distribution_id:
                continue
            try:
                result[group_id] = UUID(distribution_id)
            except ValueError:
                continue
        return result

    async def add_groups_to_distribution(
        self,
        *,
        context: DistributionContextDTO,
        groups: Iterable[GroupDTO],
        cleanup_group_ids: Iterable[UUID] | None = None,
    ) -> tuple[int, list[int]]:
        cleanup_ids = list(dict.fromkeys(cleanup_group_ids or []))
        if cleanup_ids:
            await self.delete_active_by_groups(cleanup_ids)

        created = 0
        skipped: list[int] = []
        for group in groups:
            if not group.assigned_bot_id:
                skipped.append(group.tg_chat_id)
                continue
            await self.create(
                group_id=group.id,
                target_chat_id=group.tg_chat_id,
                distribution_name=context.name,
                source_channel_username=context.source_channel_username or "",
                source_channel_id=context.source_channel_id,
                source_message_id=context.source_message_id,
                bot_id=group.assigned_bot_id,
                pause_between_attempts_s=context.pause_between_attempts_s,
                delete_last_attempt=context.delete_last_attempt,
                pin_after_post=context.pin_after_post,
                num_attempt_for_pin_post=context.num_attempt_for_pin_post,
                target_attempts=context.target_attempts,
                notify_on_failure=context.notify_on_failure,
            )
            created += 1
        return created, skipped
