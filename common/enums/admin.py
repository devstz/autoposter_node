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
    FINISH_BOT_SELECTION = "finish_bot_selection"
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
    SHOW_GROUPS = "show_groups"
    GROUPS_PAGE = "groups_page"
    GROUP_VIEW = "group_view"
    GROUPS_ADD = "groups_add"
    GROUPS_ADD_MANUAL = "groups_add_manual"
    GROUPS_ADD_BINDINGS = "groups_add_bindings"
    GROUPS_ADD_BINDINGS_PAGE = "groups_add_bindings_page"
    GROUPS_ADD_TOGGLE = "groups_add_toggle"
    GROUPS_ADD_APPLY = "groups_add_apply"
    GROUPS_ADD_CANCEL = "groups_add_cancel"
    GROUPS_DELETE = "groups_delete"
    GROUPS_DELETE_PAGE = "groups_delete_page"
    GROUPS_DELETE_TOGGLE = "groups_delete_toggle"
    GROUPS_DELETE_CANCEL = "groups_delete_cancel"
    GROUPS_DELETE_CONFIRM = "groups_delete_confirm"
