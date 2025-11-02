from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.locales import (
    RU_TEXT,
    RU_BUTTONS,
    RU_STATUS,
    RU_PAGINATION,
    RU_CONFIRMATION,
    RU_RESULTS,
)
from bot.ux import UXContext, AdminUX
from common.enums import AdminMenuAction
from common.usecases import (
    ShowMainMenuUseCase,
    ShowBotsListUseCase,
    ShowBotCardUseCase,
    ShowGroupsListUseCase,
    ShowGroupCardUseCase,
    PrepareFreeBotUseCase,
    FreeBotUseCase,
    PrepareDeleteBotUseCase,
    DeleteBotUseCase,
    ShowPlaceholderUseCase,
    ShowDistributionsListUseCase,
    ShowDistributionCardUseCase,
    ShowDistributionGroupsUseCase,
    ShowDistributionGroupCardUseCase,
    ShowPostCardUseCase,
    ShowPostsListUseCase
)
from services import BotService, GroupService, PostService, PostAttemptService, SettingsService


class UXMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        context = self._build_context(data)
        data["ux"] = context
        return await handler(event, data)

    def _build_context(self, data: dict[str, Any]) -> UXContext:
        bot_service: BotService = data["bot_service"]
        group_service: GroupService = data["group_service"]
        post_service: PostService = data["post_service"]
        post_attempt_service: PostAttemptService = data["post_attempt_service"]
        settings_service: SettingsService = data["settings_service"]

        main_menu_uc = ShowMainMenuUseCase(
            prompt_text=RU_TEXT["menu"]["main_prompt"],
            buttons={
                AdminMenuAction.DISTRIBUTIONS: RU_BUTTONS["menu"]["distributions"],
                AdminMenuAction.BOTS: RU_BUTTONS["menu"]["bots"],
                AdminMenuAction.GROUPS: RU_BUTTONS["menu"]["groups"],
                AdminMenuAction.STATS: RU_BUTTONS["menu"]["stats"],
                AdminMenuAction.SETTINGS: RU_BUTTONS["menu"]["settings"],
            },
        )

        bots_list_uc = ShowBotsListUseCase(
            bot_service=bot_service,
            post_service=post_service,
            settings_service=settings_service,
            texts=RU_TEXT["bots"],
            status_texts=RU_STATUS,
            pagination_texts=RU_PAGINATION,
        )

        bot_card_uc = ShowBotCardUseCase(
            bot_service=bot_service,
            post_service=post_service,
            post_attempt_service=post_attempt_service,
            settings_service=settings_service,
            texts=RU_TEXT["bots"],
            metrics_texts={
                "last_send": RU_TEXT["bots"]["card_metrics_last"],
                "success_min": RU_TEXT["bots"]["card_metrics_success_min"],
                "success_total": RU_TEXT["bots"]["card_metrics_success_total"],
                "fail_min": RU_TEXT["bots"]["card_metrics_fail_min"],
                "fail_total": RU_TEXT["bots"]["card_metrics_fail_total"],
            },
            status_texts=RU_STATUS,
        )

        groups_list_uc = ShowGroupsListUseCase(
            group_service=group_service,
            bot_service=bot_service,
            settings_service=settings_service,
            texts=RU_TEXT["groups"],
            pagination_texts=RU_PAGINATION,
        )

        group_card_uc = ShowGroupCardUseCase(
            group_service=group_service,
            bot_service=bot_service,
            texts=RU_TEXT["groups"],
        )

        posts_list_uc = ShowPostsListUseCase(
            post_service=post_service,
            settings_service=settings_service,
            group_service=group_service,
            bot_service=bot_service,
            texts=RU_TEXT["posts"],
            pagination_texts=RU_PAGINATION,
        )

        post_card_uc = ShowPostCardUseCase(
            post_service=post_service,
            group_service=group_service,
            bot_service=bot_service,
            texts=RU_TEXT["posts"],
        )

        distributions_list_uc = ShowDistributionsListUseCase(
            post_service=post_service,
            settings_service=settings_service,
            texts=RU_TEXT["distributions"],
            pagination_texts=RU_PAGINATION,
            status_short_texts=RU_TEXT["posts"].get("status_short", {}),
        )

        distribution_card_uc = ShowDistributionCardUseCase(
            post_service=post_service,
            texts=RU_TEXT["distributions"],
            status_labels=RU_TEXT["posts"].get("status_labels", {}),
            status_short=RU_TEXT["posts"].get("status_short", {}),
        )

        distribution_groups_uc = ShowDistributionGroupsUseCase(
            post_service=post_service,
            settings_service=settings_service,
            group_service=group_service,
            bot_service=bot_service,
            texts=RU_TEXT["distributions"],
            pagination_texts=RU_PAGINATION,
            status_short_texts=RU_TEXT["posts"].get("status_short", {}),
        )

        distribution_group_card_uc = ShowDistributionGroupCardUseCase(
            post_service=post_service,
            group_service=group_service,
            bot_service=bot_service,
            texts=RU_TEXT["distributions"],
            status_labels=RU_TEXT["posts"].get("status_labels", {}),
        )

        free_prompt_uc = PrepareFreeBotUseCase(
            bot_service=bot_service,
            texts=RU_TEXT["bots"],
            confirmation_texts=RU_CONFIRMATION,
        )

        free_uc = FreeBotUseCase(
            bot_service=bot_service,
            post_service=post_service,
            result_texts=RU_RESULTS,
        )

        delete_prompt_uc = PrepareDeleteBotUseCase(
            bot_service=bot_service,
            texts=RU_TEXT["bots"],
            confirmation_texts=RU_CONFIRMATION,
        )

        delete_uc = DeleteBotUseCase(
            bot_service=bot_service,
            post_service=post_service,
            result_texts=RU_RESULTS,
        )

        placeholder_base = RU_TEXT["menu"].get("placeholder", "Раздел в разработке")
        placeholder_uc = ShowPlaceholderUseCase(
            texts={
                AdminMenuAction.STATS: f"{RU_BUTTONS['menu']['stats']} — {placeholder_base}",
                AdminMenuAction.SETTINGS: f"{RU_BUTTONS['menu']['settings']} — {placeholder_base}",
                "placeholder": placeholder_base,
            }
        )

        admin_ux = AdminUX(
            bot_service=bot_service,
            main_menu_uc=main_menu_uc,
            bots_list_uc=bots_list_uc,
            bot_card_uc=bot_card_uc,
            groups_list_uc=groups_list_uc,
            group_card_uc=group_card_uc,
            distributions_list_uc=distributions_list_uc,
            distribution_card_uc=distribution_card_uc,
            distribution_groups_uc=distribution_groups_uc,
            distribution_group_card_uc=distribution_group_card_uc,
            free_prompt_uc=free_prompt_uc,
            free_uc=free_uc,
            delete_prompt_uc=delete_prompt_uc,
            delete_uc=delete_uc,
            placeholder_uc=placeholder_uc,
            admin_texts=RU_TEXT["admin"],
            menu_texts=RU_TEXT["menu"],
            bots_texts=RU_TEXT["bots"],
            groups_texts=RU_TEXT["groups"],
            distributions_texts=RU_TEXT["distributions"],
        )

        return UXContext(admin=admin_ux)
