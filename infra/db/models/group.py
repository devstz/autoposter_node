from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin


class Group(Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin):
    tg_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # group | supergroup | channel
    title: Mapped[Optional[str]] = mapped_column(String(128))
    last_post_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
