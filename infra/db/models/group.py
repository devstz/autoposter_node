from __future__ import annotations

from typing import Optional
from uuid import UUID

from uuid import UUID

from sqlalchemy import BigInteger, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import ForeignKey

from .base import Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin


class Group(Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin):
    tg_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # group | supergroup | channel
    title: Mapped[Optional[str]] = mapped_column(String(128))
    username: Mapped[Optional[str]] = mapped_column(String(64))
    last_post_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    metadata_refreshed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    assigned_bot_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("bots.id", ondelete="SET NULL"), index=True)
    assigned_bot: Mapped["Bot"] = relationship("Bot", lazy="select")

from .bot import Bot  # noqa: E402
