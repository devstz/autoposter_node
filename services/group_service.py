from __future__ import annotations

from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import Optional, Iterable, TYPE_CHECKING
from uuid import UUID

from common.dto import GroupDTO, GroupAssignResultDTO, GroupReassignmentDTO
from infra.db.models import Group
from infra.db.repo import SQLAlchemyGroupRepository
from bot.builder.instance_bot import create_bot
from contextlib import suppress

try:  # pragma: no cover - aiogram may be optional in some environments
    from aiogram.exceptions import TelegramError  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    TelegramError = Exception

if TYPE_CHECKING:  # pragma: no cover
    from services.bot_service import BotService
    from common.dto import BotDTO

GROUP_METADATA_TTL = timedelta(days=7)
logger = getLogger(__name__)


class GroupService:
    def __init__(self, repo: SQLAlchemyGroupRepository) -> None:
        self._repo = repo

    async def get(self, group_id: UUID) -> Optional[GroupDTO]:
        group = await self._repo.get(group_id)
        return GroupDTO.from_model(group) if group else None

    async def get_by_tg_chat_id(self, tg_chat_id: int) -> Optional[GroupDTO]:
        group = await self._repo.get_by_tg_chat_id(tg_chat_id)
        return GroupDTO.from_model(group) if group else None

    async def get_or_create(self, *, tg_chat_id: int, type: str, title: str | None = None) -> GroupDTO:
        group = await self._repo.get_or_create(tg_chat_id=tg_chat_id, type=type, title=title)
        return GroupDTO.from_model(group)

    async def add(self, group: Group) -> GroupDTO:
        await self._repo.add(group)
        return GroupDTO.from_model(group)

    async def update(self, group: Group) -> GroupDTO:
        await self._repo.update(group)
        return GroupDTO.from_model(group)

    async def delete(self, group_id: UUID) -> None:
        await self._repo.delete(group_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[GroupDTO]:
        groups = await self._repo.list(limit=limit, offset=offset)
        return [GroupDTO.from_model(group) for group in groups]

    async def count(self) -> int:
        return await self._repo.count()

    async def list_by_bot(self, bot_id: UUID, *, limit: int = 500, offset: int = 0) -> list[GroupDTO]:
        groups = await self._repo.list_by_bot(bot_id, limit=limit, offset=offset)
        return [GroupDTO.from_model(group) for group in groups]

    async def list_bound(self, *, limit: int = 1000, offset: int = 0) -> list[GroupDTO]:
        groups = await self._repo.list_bound(limit=limit, offset=offset)
        return [GroupDTO.from_model(group) for group in groups]

    async def count_bound(self) -> int:
        return await self._repo.count_bound()

    async def ensure_metadata(
        self,
        group: GroupDTO,
        bot_service: "BotService",
        *,
        ttl: timedelta | None = GROUP_METADATA_TTL,
    ) -> GroupDTO:
        now = datetime.now(timezone.utc)
        if not self._should_refresh_metadata(group, ttl, now):
            return group

        if not group.assigned_bot_id:
            return group

        bot = await bot_service.get(group.assigned_bot_id)
        if bot is None:
            return group

        client = create_bot(bot.token)
        try:
            chat = await client.get_chat(group.tg_chat_id)
        except TelegramError as exc:  # pragma: no cover - network errors
            logger.warning(
                "Failed to fetch metadata for group %s via bot %s: %s",
                group.tg_chat_id,
                bot.id,
                exc,
            )
            return group
        except Exception as exc:  # pragma: no cover
            logger.exception(
                "Unexpected error fetching metadata for group %s: %s",
                group.tg_chat_id,
                exc,
            )
            return group
        finally:
            with suppress(Exception):
                await client.session.close()

        new_title = chat.title or group.title
        new_username = getattr(chat, "username", None) or group.username
        refreshed_at = now

        updated = await self._repo.update_metadata(
            group_id=group.id,
            title=new_title,
            username=new_username,
            refreshed_at=refreshed_at,
        )
        if updated:
            group.title = updated.title
            group.username = getattr(updated, "username", None)
            group.metadata_refreshed_at = updated.metadata_refreshed_at
        else:
            group.metadata_refreshed_at = refreshed_at
        return group

    async def ensure_metadata_bulk(
        self,
        groups: Iterable[GroupDTO],
        bot_service: "BotService",
        *,
        ttl: timedelta | None = GROUP_METADATA_TTL,
    ) -> list[GroupDTO]:
        result: list[GroupDTO] = []
        for group in groups:
            result.append(await self.ensure_metadata(group, bot_service, ttl=ttl))
        return result

    async def assign_to_bot(self, *, bot_id: UUID, tg_chat_ids: list[int]) -> GroupAssignResultDTO:
        result = await self._repo.assign_to_bot(bot_id=bot_id, tg_chat_ids=tg_chat_ids)
        newly_assigned = [GroupDTO.from_model(group) for group in result.newly_assigned]
        already_assigned = [GroupDTO.from_model(group) for group in result.already_assigned]
        reassigned = [
            GroupReassignmentDTO(
                group=GroupDTO.from_model(group),
                previous_bot_id=previous_bot_id,
            )
            for group, previous_bot_id in result.reassigned
        ]
        return GroupAssignResultDTO(
            newly_assigned=newly_assigned,
            already_assigned=already_assigned,
            reassigned=reassigned,
        )

    async def unassign_from_bot(self, *, bot_id: UUID, tg_chat_ids: list[int] | None = None) -> int:
        return await self._repo.unassign_from_bot(bot_id=bot_id, tg_chat_ids=tg_chat_ids)

    def _should_refresh_metadata(self, group: GroupDTO, ttl: timedelta | None, now: datetime) -> bool:
        if not (group.title or group.username):
            return True
        if ttl is None:
            return False
        if group.metadata_refreshed_at is None:
            return True
        return now - group.metadata_refreshed_at >= ttl
