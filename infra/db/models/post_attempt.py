from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import Base, TimestampMixin, UUIDPkMixin, ModelHelpersMixin


class PostAttempt(Base, TimestampMixin, UUIDPkMixin, ModelHelpersMixin):
    post_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    bot_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("bots.id", ondelete="SET NULL"), index=True)
    group_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("groups.id", ondelete="SET NULL"), index=True)

    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(64))
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
