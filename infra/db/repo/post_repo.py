from __future__ import annotations

from datetime import datetime, timezone
from logging import getLogger
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, update, case, cast, String
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from infra.db.models import Post, PostStatus, Group

logger = getLogger(__name__)


ACTIVE_STATUSES = (PostStatus.ACTIVE.value, PostStatus.PAUSED.value, PostStatus.ERROR.value)


class SQLAlchemyPostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def get(self, post_id: UUID) -> Optional[Post]:
        stmt = select(Post).where(Post.id == post_id)
        res = await self.__session.execute(stmt)
        return res.unique().scalars().first()

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
    ) -> Post:
        # Ensure we don't violate uq_posts_group_source when admin repeats the same source
        await self.__session.execute(
            sa_delete(Post).where(
                and_(
                    Post.group_id == group_id,
                    Post.source_channel_username == source_channel_username,
                    Post.source_message_id == source_message_id,
                )
            )
        )
        await self.__session.flush()
        obj = Post(
            group_id=group_id,
            bot_id=bot_id if bot_id else None,
            status=status,
            target_chat_id=target_chat_id,
            distribution_name=distribution_name,
            source_channel_username=source_channel_username,
            source_channel_id=source_channel_id,
            source_message_id=source_message_id,
            pause_between_attempts_s=pause_between_attempts_s,
            delete_last_attempt=delete_last_attempt,
            pin_after_post=pin_after_post,
            num_attempt_for_pin_post=num_attempt_for_pin_post,
            target_attempts=target_attempts,
            notify_on_failure=notify_on_failure,
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
        return res.unique().scalars().first()

    async def find_unassigned_active(self, *, limit: int = 100, offset: int = 0) -> list[Post]:
        stmt = (
            select(Post)
            .where(and_(Post.bot_id.is_(None), Post.status.in_(ACTIVE_STATUSES)))
            .order_by(Post.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.__session.execute(stmt)
        return list(res.unique().scalars().all())

    async def count_active_for_bot(self, bot_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Post)
            .join(Group, Group.id == Post.group_id)
            .where(and_(Group.assigned_bot_id == bot_id, Post.status.in_(ACTIVE_STATUSES)))
        )
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())

    async def assign_to_bot(self, post_id: UUID, bot_id: UUID) -> None:
        # Deprecated in favor of permanent group bindings, but keep for compatibility.
        await self.__session.execute(
            update(Post).where(Post.id == post_id).values(bot_id=bot_id)
        )
        await self.__session.flush()

    async def bulk_unassign_by_bot(self, bot_id: UUID) -> int:
        # Unassign posts for all groups bound to the bot
        res = await self.__session.execute(
            update(Post)
            .where(
                and_(
                    Post.group_id.in_(select(Group.id).where(Group.assigned_bot_id == bot_id)),
                    Post.status.in_(ACTIVE_STATUSES),
                )
            )
            .values(bot_id=None)
            .returning(Post.id)
        )
        await self.__session.flush()
        return len(res.fetchall())

    async def bulk_pause_by_bot(self, bot_id: UUID) -> int:
        # Pause posts for all groups bound to the bot
        res = await self.__session.execute(
            update(Post)
            .where(
                and_(
                    Post.group_id.in_(select(Group.id).where(Group.assigned_bot_id == bot_id)),
                    Post.status == PostStatus.ACTIVE.value,
                )
            )
            .values(status=PostStatus.PAUSED.value)
            .returning(Post.id)
        )
        await self.__session.flush()
        return len(res.fetchall())

    def _distribution_filters(
        self,
        *,
        source_channel_username: str | None,
        source_channel_id: int | None,
        source_message_id: int,
    ):
        conditions = [Post.source_message_id == source_message_id]
        if source_channel_username is not None:
            conditions.append(Post.source_channel_username == source_channel_username)
        else:
            conditions.append(Post.source_channel_username.is_(None))
        if source_channel_id is not None:
            conditions.append(Post.source_channel_id == source_channel_id)
        else:
            conditions.append(Post.source_channel_id.is_(None))
        return conditions

    async def bulk_pause_by_distribution(
        self,
        *,
        distribution_name: str | None,
    ) -> int:
        """Pause all active posts in a distribution by name."""
        conditions = [Post.status == PostStatus.ACTIVE.value]
        if distribution_name is None:
            conditions.append(Post.distribution_name.is_(None))
        else:
            conditions.append(Post.distribution_name == distribution_name)
        res = await self.__session.execute(
            update(Post)
            .where(and_(*conditions))
            .values(status=PostStatus.PAUSED.value)
            .returning(Post.id)
        )
        await self.__session.flush()
        return len(res.fetchall())

    async def bulk_resume_by_distribution(
        self,
        *,
        distribution_name: str | None,
    ) -> int:
        """Resume all paused/error posts in a distribution by name."""
        conditions = [Post.status.in_((PostStatus.PAUSED.value, PostStatus.ERROR.value))]
        if distribution_name is None:
            conditions.append(Post.distribution_name.is_(None))
        else:
            conditions.append(Post.distribution_name == distribution_name)
        res = await self.__session.execute(
            update(Post)
            .where(and_(*conditions))
            .values(status=PostStatus.ACTIVE.value, last_error=None)
            .returning(Post.id)
        )
        await self.__session.flush()
        return len(res.fetchall())

    async def bulk_set_notify_by_distribution(
        self,
        *,
        distribution_name: str | None,
        value: bool,
    ) -> int:
        """Set notify_on_failure for all posts in a distribution by name."""
        conditions = []
        if distribution_name is None:
            conditions.append(Post.distribution_name.is_(None))
        else:
            conditions.append(Post.distribution_name == distribution_name)
        res = await self.__session.execute(
            update(Post)
            .where(and_(*conditions))
            .values(notify_on_failure=value)
            .returning(Post.id)
        )
        await self.__session.flush()
        return len(res.fetchall())

    async def delete_distribution(
        self,
        *,
        distribution_name: str | None,
    ) -> int:
        """Delete posts that belong to the same distribution name."""
        if distribution_name is None:
            stmt = sa_delete(Post).where(Post.distribution_name.is_(None))
        else:
            stmt = sa_delete(Post).where(Post.distribution_name == distribution_name)
        res = await self.__session.execute(stmt.returning(Post.id))
        await self.__session.flush()
        return len(res.fetchall())

    async def delete_distribution_groups(
        self,
        *,
        distribution_name: str | None,
        group_ids: list[UUID],
    ) -> int:
        """Delete posts that belong to the same distribution name and specified groups."""
        if not group_ids:
            return 0
        conditions = [Post.group_id.in_(group_ids)]
        if distribution_name is None:
            conditions.append(Post.distribution_name.is_(None))
        else:
            conditions.append(Post.distribution_name == distribution_name)
        res = await self.__session.execute(
            sa_delete(Post)
            .where(and_(*conditions))
            .returning(Post.id)
        )
        await self.__session.flush()
        return len(res.fetchall())

    async def resolve_distribution_id_by_name(
        self,
        *,
        distribution_name: str | None,
    ) -> UUID | None:
        """Resolve distribution_id by distribution_name (returns min post id for that distribution)."""
        stmt = select(func.min(cast(Post.id, String)))
        if distribution_name is None:
            stmt = stmt.where(Post.distribution_name.is_(None))
        else:
            stmt = stmt.where(Post.distribution_name == distribution_name)
        res = await self.__session.execute(stmt)
        raw = res.scalar()
        if not raw:
            return None
        try:
            return UUID(raw)
        except ValueError:
            logger.error("Failed to parse distribution id %s", raw)
            return None

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
        # Fetch posts by groups permanently assigned to the bot
        stmt = (
            select(Post)
            .join(Group, Group.id == Post.group_id)
            .where(Group.assigned_bot_id == bot_id)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.__session.execute(stmt)
        return list(res.unique().scalars().all())

    async def list_by_group(self, group_id: UUID, *, limit: int = 100, offset: int = 0) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.group_id == group_id)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.__session.execute(stmt)
        return list(res.unique().scalars().all())

    async def list_by_status(self, status: str, *, limit: int = 100, offset: int = 0) -> list[Post]:
        stmt = (
            select(Post)
            .options(selectinload(Post.group), selectinload(Post.bot))
            .where(Post.status == status)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.__session.execute(stmt)
        return list(res.unique().scalars().all())

    async def count_by_status(self, status: str) -> int:
        stmt = select(func.count()).select_from(Post).where(Post.status == status)
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())

    async def count_errors_for_bot(self, bot_id: UUID) -> int:
        stmt = (
            select(func.count()).select_from(Post)
            .join(Group, Group.id == Post.group_id)
            .where(and_(Group.assigned_bot_id == bot_id, Post.status == PostStatus.ERROR.value))
        )
        res = await self.__session.execute(stmt)
        return int(res.scalar_one())

    async def delete_active_by_groups(self, group_ids: list[UUID]) -> int:
        """Delete non-DONE posts for provided groups (cascade removes attempts)."""
        res = await self.__session.execute(
            sa_delete(Post)
            .where(and_(Post.group_id.in_(group_ids), Post.status.in_(ACTIVE_STATUSES)))
            .returning(Post.id)
        )
        await self.__session.flush()
        return len(res.fetchall())

    async def count_distributions(self) -> int:
        # Группируем по distribution_name: если у постов одинаковое название рассылки, это одна рассылка
        # NULL значения distribution_name группируются отдельно
        grouped = (
            select(Post.distribution_name)
            .group_by(Post.distribution_name)
        ).subquery()
        stmt = select(func.count()).select_from(grouped)
        res = await self.__session.execute(stmt)
        scalar = res.scalar_one()
        return int(scalar or 0)

    async def list_distributions(self, *, limit: int, offset: int) -> list[dict]:
        # Группируем по distribution_name: если у постов одинаковое название рассылки, это одна рассылка
        # NULL значения distribution_name группируются отдельно

        aggregated = (
            select(
                func.min(cast(Post.id, String)).label("distribution_id"),
                func.max(Post.source_channel_username).label("source_channel_username"),
                func.max(Post.source_channel_id).label("source_channel_id"),
                Post.distribution_name.label("distribution_name"),
                func.bool_and(Post.notify_on_failure).label("notify_on_failure"),
                func.max(Post.source_message_id).label("source_message_id"),
                func.min(Post.created_at).label("created_at"),
                func.max(Post.updated_at).label("updated_at"),
                func.count(Post.id).label("total_posts"),
                func.sum(case((Post.status == PostStatus.ACTIVE.value, 1), else_=0)).label("active_count"),
                func.sum(case((Post.status == PostStatus.PAUSED.value, 1), else_=0)).label("paused_count"),
                func.sum(case((Post.status == PostStatus.ERROR.value, 1), else_=0)).label("error_count"),
                func.sum(case((Post.status == PostStatus.DONE.value, 1), else_=0)).label("done_count"),
            )
            .group_by(Post.distribution_name)
        ).subquery()

        stmt = (
            select(aggregated)
            .order_by(aggregated.c.created_at.desc().nulls_last())
            .limit(limit)
            .offset(offset)
        )
        res = await self.__session.execute(stmt)
        return [dict(row._mapping) for row in res.fetchall()]

    async def get_distribution_summary(self, distribution_id: UUID) -> dict | None:
        # Группируем по distribution_name: если у постов одинаковое название рассылки, это одна рассылка
        # NULL значения distribution_name группируются отдельно
        # Сначала находим пост по distribution_id, чтобы получить его distribution_name
        post = await self.get(distribution_id)
        if post is None:
            return None
        
        distribution_name = post.distribution_name

        aggregated = (
            select(
                func.min(cast(Post.id, String)).label("distribution_id"),
                func.max(Post.source_channel_username).label("source_channel_username"),
                func.max(Post.source_channel_id).label("source_channel_id"),
                Post.distribution_name.label("distribution_name"),
                func.bool_and(Post.notify_on_failure).label("notify_on_failure"),
                func.max(Post.source_message_id).label("source_message_id"),
                func.min(Post.created_at).label("created_at"),
                func.max(Post.updated_at).label("updated_at"),
                func.count(Post.id).label("total_posts"),
                func.sum(case((Post.status == PostStatus.ACTIVE.value, 1), else_=0)).label("active_count"),
                func.sum(case((Post.status == PostStatus.PAUSED.value, 1), else_=0)).label("paused_count"),
                func.sum(case((Post.status == PostStatus.ERROR.value, 1), else_=0)).label("error_count"),
                func.sum(case((Post.status == PostStatus.DONE.value, 1), else_=0)).label("done_count"),
            )
            .group_by(Post.distribution_name)
        ).subquery()

        # Ищем рассылку по distribution_name
        if distribution_name is None:
            stmt = select(aggregated).where(aggregated.c.distribution_name.is_(None))
        else:
            stmt = select(aggregated).where(aggregated.c.distribution_name == distribution_name)
        res = await self.__session.execute(stmt)
        row = res.first()
        if row is None:
            return None
        return dict(row._mapping)

    async def get_distribution_config(
        self,
        *,
        distribution_name: str | None,
    ) -> dict | None:
        """Get configuration for a distribution by name."""
        conditions = []
        if distribution_name is None:
            conditions.append(Post.distribution_name.is_(None))
        else:
            conditions.append(Post.distribution_name == distribution_name)
        stmt = (
            select(
                Post.pause_between_attempts_s.label("pause_between_attempts_s"),
                Post.delete_last_attempt.label("delete_last_attempt"),
                Post.pin_after_post.label("pin_after_post"),
                Post.num_attempt_for_pin_post.label("num_attempt_for_pin_post"),
                Post.target_attempts.label("target_attempts"),
            )
            .where(and_(*conditions))
            .order_by(Post.created_at.asc())
            .limit(1)
        )
        res = await self.__session.execute(stmt)
        row = res.first()
        if row is None:
            return None
        return dict(row._mapping)

    async def list_distribution_posts(
        self,
        *,
        distribution_name: str | None,
    ) -> list[Post]:
        """List all posts in a distribution by name."""
        stmt = (
            select(Post)
            .options(selectinload(Post.group), selectinload(Post.bot))
        )
        if distribution_name is None:
            stmt = stmt.where(Post.distribution_name.is_(None))
        else:
            stmt = stmt.where(Post.distribution_name == distribution_name)

        stmt = stmt.order_by(Post.created_at.desc())
        res = await self.__session.execute(stmt)
        return list(res.unique().scalars().all())

    async def groups_distribution_usage(self, group_ids: list[UUID]) -> dict[UUID, str]:
        if not group_ids:
            return {}
        stmt = (
            select(
                Post.group_id,
                func.min(cast(Post.id, String)).label("distribution_id"),
            )
            .where(
                and_(
                    Post.group_id.in_(group_ids),
                    Post.status.in_(ACTIVE_STATUSES),
                )
            )
            .group_by(Post.group_id)
        )
        res = await self.__session.execute(stmt)
        return {row.group_id: row.distribution_id for row in res.fetchall()}

    async def pause(self, post_id: UUID) -> None:
        await self.__session.execute(
            update(Post).where(Post.id == post_id).values(status=PostStatus.PAUSED.value)
        )
        await self.__session.flush()

    async def resume(self, post_id: UUID) -> None:
        await self.__session.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(status=PostStatus.ACTIVE.value, last_error=None)
        )
        await self.__session.flush()
