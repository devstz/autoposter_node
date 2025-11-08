from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from typing import Dict

from common.dto import BotCardDTO, BotDTO
from services import (
    BotService,
    PostService,
    PostAttemptService,
    SettingsService,
)


class ShowBotCardUseCase:
    def __init__(
        self,
        *,
        bot_service: BotService,
        post_service: PostService,
        post_attempt_service: PostAttemptService,
        settings_service: SettingsService,
        texts: Dict[str, str],
        metrics_texts: Dict[str, str],
        status_texts: Dict[str, str],
    ) -> None:
        self._bot_service = bot_service
        self._post_service = post_service
        self._post_attempt_service = post_attempt_service
        self._settings_service = settings_service
        self._texts = texts
        self._metrics_texts = metrics_texts
        self._status_texts = status_texts

    async def __call__(self, bot_id: UUID) -> BotCardDTO:
        bot = await self._bot_service.get(bot_id)
        if bot is None:
            raise RuntimeError("Bot not found")

        settings = await self._settings_service.get_current()
        if settings is None:
            raise RuntimeError("Settings profile is not configured")

        load_current = await self._post_service.count_active_for_bot(bot_id)
        errors_count = await self._post_service.count_errors_for_bot(bot_id)

        token_masked = self._mask_token(bot.token)
        display_name = bot.name or bot.username or self._texts.get("no_data", "—")
        username_display = bot.username or self._texts.get("no_data", "—")

        status_label = self._status_texts.get(
            self._detect_status(bot.last_heartbeat_at, settings), "—"
        )

        last_send = await self._post_attempt_service.last_send_time_for_bot(bot_id)
        success_min = await self._post_attempt_service.count_success_in_period(bot_id=bot_id, seconds=60)
        success_total = await self._post_attempt_service.count_total(bot_id=bot_id, success=True)
        fail_min = await self._post_attempt_service.count_fail_in_period(bot_id=bot_id, seconds=60)
        fail_total = await self._post_attempt_service.count_total(bot_id=bot_id, success=False)

        metrics_lines = [
            self._metrics_texts["last_send"].format(value=self._format_datetime(last_send)),
            self._metrics_texts["success_min"].format(count=success_min),
            self._metrics_texts["success_total"].format(count=success_total),
            self._metrics_texts["fail_min"].format(count=fail_min),
            self._metrics_texts["fail_total"].format(count=fail_total),
        ]

        if errors_count > 0:
            metrics_lines.append(self._texts["card_metrics_failures_hint"])

        repo_lines = self._build_repo_lines(bot)

        text = "\n".join(
            [
                self._texts["card_title"].format(name=display_name),
                self._texts["card_id"].format(bot_id=bot_id),
                self._texts["card_username"].format(username=username_display),
                self._texts["card_name"].format(name=display_name),
                self._texts["card_status"].format(status=status_label),
                self._texts["card_token"].format(masked=token_masked),
                self._texts["card_ip"].format(ip=bot.server_ip),
                self._texts["card_posts"].format(used=load_current, limit=bot.max_posts),
                self._texts["card_posts_errors"].format(count=errors_count),
                "",
                self._texts["card_metrics_title"],
                *metrics_lines,
                "",
                self._texts["card_repo_title"],
                *repo_lines,
                "",
                self._texts["card_posts_hint"].format(limit=bot.max_posts),
            ]
        )

        return BotCardDTO(
            bot_id=bot_id,
            telegram_id=bot.telegram_id,
            text=text,
            has_errors=errors_count > 0,
        )

    @staticmethod
    def _mask_token(token: str, visible: int = 5) -> str:
        if len(token) <= visible * 2:
            return token
        return f"{token[:visible]}{'*' * 5}{token[-visible:]}"

    @staticmethod
    def _format_datetime(value: datetime | None) -> str:
        if not value:
            return "—"
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    @staticmethod
    def _detect_status(heartbeat, settings) -> str:
        if heartbeat is None:
            return "offline"
        delta = (datetime.now(timezone.utc) - heartbeat).total_seconds()
        if delta <= settings.online_threshold_s:
            return "online"
        if delta <= settings.offline_threshold_s:
            return "warning"
        return "offline"

    def _build_repo_lines(self, bot: BotDTO) -> list[str]:
        lines: list[str] = []
        lines.append(self._texts["card_repo_branch"].format(branch=bot.tracked_branch))

        if bot.current_commit_hash:
            lines.append(
                self._texts["card_repo_current"].format(
                    commit=self._short_hash(bot.current_commit_hash)
                )
            )
        else:
            lines.append(self._texts["card_repo_unknown"])

        if bot.latest_available_commit_hash:
            lines.append(
                self._texts["card_repo_latest"].format(
                    commit=self._short_hash(bot.latest_available_commit_hash)
                )
            )

        if bot.commits_behind > 0:
            lines.append(self._texts["card_repo_updates"].format(count=bot.commits_behind))
        else:
            lines.append(self._texts["card_repo_status_ok"])

        lines.append(
            self._texts["card_repo_checked"].format(
                value=self._format_datetime(bot.last_update_check_at)
            )
        )
        return lines

    @staticmethod
    def _short_hash(value: str, length: int = 8) -> str:
        if len(value) <= length:
            return value
        return value[:length]
