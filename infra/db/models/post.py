from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin


class PostStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DONE = "done"


class Post(Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin):
    group_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    bot_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("bots.id", ondelete="SET NULL"), index=True)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default=PostStatus.ACTIVE.value, server_default=text("'active'"))

    source_channel_username: Mapped[str] = mapped_column(String(255), nullable=False)
    source_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    last_attempt_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text)

    group = relationship("Group", lazy="joined")
    bot = relationship("Bot", lazy="joined")

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
