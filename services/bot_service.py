from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from common.dto import BotDTO
from infra.db.models import Bot
from infra.db.repo import SQLAlchemyBotRepository


class BotService:
    def __init__(self, repo: SQLAlchemyBotRepository) -> None:
        self._repo = repo

    async def get(self, bot_id: UUID) -> Optional[BotDTO]:
        bot = await self._repo.get(bot_id)
        return BotDTO.from_model(bot) if bot else None

    async def get_by_ip(self, server_ip: str, *, active_only: bool = True) -> Optional[BotDTO]:
        bot = await self._repo.get_by_ip(server_ip, active_only=active_only)
        return BotDTO.from_model(bot) if bot else None

    async def get_by_token(self, token: str) -> Optional[BotDTO]:
        bot = await self._repo.get_by_token(token)
        return BotDTO.from_model(bot) if bot else None

    async def get_by_telegram_id(self, telegram_id: str | int) -> Optional[BotDTO]:
        bot = await self._repo.get_by_telegram_id(str(telegram_id))
        return BotDTO.from_model(bot) if bot else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[BotDTO]:
        bots = await self._repo.list(limit=limit, offset=offset)
        return [BotDTO.from_model(bot) for bot in bots]

    async def search(
        self,
        *,
        username_like: Optional[str] = None,
        name_like: Optional[str] = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BotDTO]:
        bots = await self._repo.search(
            username_like=username_like,
            name_like=name_like,
            active_only=active_only,
            limit=limit,
            offset=offset,
        )
        return [BotDTO.from_model(bot) for bot in bots]

    async def count(
        self,
        *,
        active_only: bool = False,
        username_like: Optional[str] = None,
        name_like: Optional[str] = None,
    ) -> int:
        return await self._repo.count(
            active_only=active_only,
            username_like=username_like,
            name_like=name_like,
        )

    async def add(self, bot: Bot) -> BotDTO:
        await self._repo.add(bot)
        return BotDTO.from_model(bot)

    async def update(self, bot: Bot) -> BotDTO:
        await self._repo.update(bot)
        return BotDTO.from_model(bot)

    async def update_fields(self, bot_id: UUID, **fields: Any) -> BotDTO:
        bot = await self._repo.get(bot_id)
        if not bot:
            raise ValueError(f"Bot {bot_id} not found")
        if fields:
            bot.update(**fields)
            await self._repo.update(bot)
        return BotDTO.from_model(bot)

    async def delete(self, bot_id: UUID) -> None:
        await self._repo.delete(bot_id)

    async def update_heartbeat(self, bot_id: UUID, when: Optional[datetime] = None) -> None:
        await self._repo.update_heartbeat(bot_id, when)

    async def mark_self_destruction(self, bot_id: UUID) -> None:
        await self._repo.mark_self_destruction(bot_id)

    async def mark_deactivated(self, bot_id: UUID) -> None:
        await self._repo.mark_deactivated(bot_id)

    async def has_ip_conflict(self, server_ip: str, token: str) -> bool:
        return await self._repo.has_ip_conflict(server_ip, token)

    async def count_active_posts(self, bot_id: UUID) -> int:
        return await self._repo.count_active_posts(bot_id)

    async def loads_by_bot(self, bot_ids: Optional[list[UUID]] = None) -> dict[UUID, int]:
        return await self._repo.loads_by_bot(bot_ids)

    async def set_force_update_all(self) -> int:
        """Set force_update flag to True for all active bots."""
        return await self._repo.set_force_update_all()

    async def clear_force_update(self, bot_id: UUID) -> None:
        """Clear force_update flag for a specific bot."""
        await self._repo.clear_force_update(bot_id)

    async def count_bots_needing_update(self) -> int:
        """Count bots that need update."""
        return await self._repo.count_bots_needing_update()
