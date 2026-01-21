from __future__ import annotations

from enum import Enum


class AdminMenuAction(str, Enum):
    DISTRIBUTIONS = "distributions"
    BOTS = "bots"
    GROUPS = "groups"
    STATS = "stats"
    SETTINGS = "settings"


class AdminBotsListAction(str, Enum):
    OPEN = "open"
    PAGE = "page"
    VIEW = "view"
    BACK = "back"
    UPDATE_ALL = "update_all"


class AdminBotAction(str, Enum):
    REFRESH = "refresh"
    BACK_TO_LIST = "back_to_list"
    FREE_PROMPT = "free_prompt"
    FREE_EXECUTE = "free_execute"
    DELETE_PROMPT = "delete_prompt"
    DELETE_CONFIRM = "delete_confirm"


class AdminBotFreeMode(str, Enum):
    INSTANT = "instant"
    GRACEFUL = "graceful"


class AdminGroupsAction(str, Enum):
    OPEN = "open"
    ADD = "add"
    LIST = "list"
    PAGE = "page"
    VIEW = "view"
    BACK = "back"
    CHOOSE_BOT = "choose_bot"
    CARD_BACK = "card_back"
    CARD_REFRESH = "card_refresh"
    CARD_UNBIND = "card_unbind"


class AdminDistributionsAction(str, Enum):
    OPEN = "open"
    BACK = "back"
    START_CREATE = "start_create"
    NAME_AUTO = "name_auto"
    SET_MODE = "set_mode"
    SELECT_TARGET = "select_target"
    SET_TARGET = "set_target"
    CANCEL = "cancel"
    SELECT_BOT = "select_bot"
    FINISH_BOT_SELECTION = "fin_bot_sel"
    BOT_PAGE = "bot_page"
    LIST = "list"
    LIST_PAGE = "list_page"
    LIST_VIEW = "list_view"
    LIST_BACK = "list_back"
    LIST_REFRESH = "list_refresh"
    SET_DELETE_LAST = "set_delete_last"
    SET_PIN = "set_pin"
    TOGGLE_STATUS = "toggle_status"
    TOGGLE_NOTIFY = "toggle_notify"
    DELETE = "delete"
    SHOW_GROUPS = "grp_show"
    GROUPS_PAGE = "grp_pg"
    GROUP_VIEW = "grp_view"
    GROUPS_ADD = "grp_add"
    GROUPS_ADD_MANUAL = "grp_add_man"
    GROUPS_ADD_BINDINGS = "grp_add_bind"
    GROUPS_ADD_BINDINGS_PAGE = "grp_add_bind_pg"
    GROUPS_ADD_TOGGLE = "grp_add_tgl"
    GROUPS_ADD_APPLY = "grp_add_apl"
    GROUPS_ADD_CANCEL = "grp_add_cncl"
    GROUPS_DELETE = "grp_del"
    GROUPS_DELETE_PAGE = "grp_del_pg"
    GROUPS_DELETE_TOGGLE = "grp_del_tgl"
    GROUPS_DELETE_CANCEL = "grp_del_cncl"
    GROUPS_DELETE_CONFIRM = "grp_del_conf"
