from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import DateTime, MetaData, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class VersionedMixin:
    version_id: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    __mapper_args__ = {
        "version_id_col": version_id,
        "version_id_generator": lambda v: (v or 0) + 1,
    }


class UUIDPkMixin:
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

class ModelHelpersMixin:
    def to_dict(self, exclude: list[str] | None = None) -> Dict[str, Any]:
        exclude = list(set(exclude or []))
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in exclude} # type: ignore

    def update(self, **kwargs: Dict[str, Any]) -> None:
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
