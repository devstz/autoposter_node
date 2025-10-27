from __future__ import annotations
from typing import Any, Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from sqlalchemy import text

from .base import Base, TimestampMixin, VersionedMixin, ModelHelpersMixin


class User(Base, TimestampMixin, VersionedMixin, ModelHelpersMixin):
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    username: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
    )

    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
    )

