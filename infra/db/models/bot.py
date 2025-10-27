from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin


class Bot(Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin):
    username: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    token: Mapped[str] = mapped_column(String(128), nullable=False)

    server_ip: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    last_heartbeat_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Shutdown lifecycle flags
    self_destruction: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=expression.false())
    deactivated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=expression.false(), index=True)

    # Settings snapshot / linkage
    settings_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("settings.id", ondelete="SET NULL"), index=True)
    max_posts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("10"))

    settings = relationship("Setting", lazy="joined")

    __table_args__ = (
        # Only one active bot per IP (deactivated = false)
        Index(
            "uq_bots_server_ip_active",
            "server_ip",
            unique=True,
            postgresql_where=text("deactivated = false"),
        ),
    )
