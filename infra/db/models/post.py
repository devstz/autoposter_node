from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from common.enums.post_status import PostStatus

from datetime import datetime

from .base import Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin


class Post(Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin):
    group_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    bot_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("bots.id", ondelete="SET NULL"), index=True)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default=PostStatus.ACTIVE.value, server_default=text("'active'"))

    target_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    distribution_name: Mapped[Optional[str]] = mapped_column(String(255))
    notify_on_failure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    source_channel_username: Mapped[str] = mapped_column(String(255), nullable=False)
    source_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    source_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text)

    count_attempts: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default=text("0"))
    target_attempts: Mapped[int] = mapped_column(BigInteger, nullable=False)

    delete_last_attempt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    pin_after_post: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    num_attempt_for_pin_post: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=None, server_default=None)

    pause_between_attempts_s: Mapped[int] = mapped_column(BigInteger, nullable=False, default=60, server_default=text("60"))

    group: Mapped['Group'] = relationship("Group", lazy="joined")
    bot: Mapped['Bot'] = relationship("Bot", lazy="joined")
    post_attempts: Mapped[list['PostAttempt']] = relationship("PostAttempt", lazy="select")

    __table_args__ = (
        # Only one active/paused/error post per group (allow history via DONE)
        Index(
            "uq_posts_active_per_group",
            "group_id",
            unique=True,
            postgresql_where=text("status IN ('active','paused','error')"),
        ),
        # Prevent duplicate source messages within a group
        Index(
            "uq_posts_group_source",
            "group_id",
            "source_channel_username",
            "source_message_id",
            unique=True,
        ),
    )

from .post_attempt import PostAttempt  # noqa: E402
from .bot import Bot  # noqa: E402
from .group import Group  # noqa: E402
