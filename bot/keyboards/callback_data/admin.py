from __future__ import annotations

from aiogram.filters.callback_data import CallbackData

from common.enums import (
    AdminMenuAction,
    AdminBotsListAction,
    AdminBotAction,
    AdminBotFreeMode,
    AdminGroupsAction,
    AdminDistributionsAction,
)


class AdminMenuCallback(CallbackData, prefix="adm_menu"):
    action: AdminMenuAction


class AdminBotsListCallback(CallbackData, prefix="adm_bots"):
    action: AdminBotsListAction
    page: int | None = None
    bot_id: str | None = None


class AdminBotActionCallback(CallbackData, prefix="adm_bot"):
    action: AdminBotAction
    bot_id: str
    mode: AdminBotFreeMode | None = None
    page: int | None = None


class AdminGroupsCallback(CallbackData, prefix="adm_groups"):
    action: AdminGroupsAction
    page: int | None = None
    group_id: str | None = None


class AdminGroupsBindCallback(CallbackData, prefix="adm_groups_bind"):
    action: AdminGroupsAction
    bot_id: str | None = None


class AdminDistributionsCallback(CallbackData, prefix="adm_dist"):
    action: AdminDistributionsAction
    mode: str | None = None
    target: str | None = None
    bot_id: str | None = None
    page: int | None = None
    distribution_id: str | None = None
    choice: str | None = None
    group_id: str | None = None
    post_id: str | None = None
    card_page: int | None = None
