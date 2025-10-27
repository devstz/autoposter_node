from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression
from sqlalchemy import text

from .base import Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin


class Setting(Base, TimestampMixin, VersionedMixin, UUIDPkMixin, ModelHelpersMixin):
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
        index=True,
    )

    # Heartbeat / online thresholds (seconds)
    heartbeat_interval_s: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("15"))
    online_threshold_s: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("45"))
    offline_threshold_s: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("120"))

    # UI / pagination
    pagination_size: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("10"))

    # Limits
    max_posts_per_bot: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("10"))

    # Notifications
    notify_rights_error: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=expression.true())
    notify_failures: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=expression.false())

    # Retention controls
    retention_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=expression.false())
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("180"))

    # Default drain mode: 0=instant, 1=graceful
    default_drain_mode: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    __table_args__ = (
        # Exactly one current settings profile (partial unique index)
        Index(
            "uq_settings_is_current",
            "is_current",
            unique=True,
            postgresql_where=text("is_current = true"),
        ),
    )
