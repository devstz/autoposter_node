from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import base64
from uuid import UUID

from bot.keyboards.callback_data import (
    AdminMenuCallback,
    AdminBotsListCallback,
    AdminBotActionCallback,
    AdminGroupsCallback,
    AdminGroupsBindCallback,
    AdminDistributionsCallback,
)
from common.dto import (
    MenuViewDTO,
    BotsListViewDTO,
    BotCardDTO,
    BotFreePromptDTO,
    BotDeletePromptDTO,
    GroupsListViewDTO,
    GroupCardDTO,
    DistributionsListViewDTO,
    DistributionCardDTO,
    DistributionGroupsViewDTO,
    DistributionGroupCardDTO,
)
from common.enums import (
    AdminBotsListAction,
    AdminBotAction,
    AdminBotFreeMode,
    AdminGroupsAction,
    AdminDistributionsAction,
)
from bot.locales import RU_BUTTONS

class AdminInlineKeyboards:
    @staticmethod
    def build_admin_menu_keyboard(menu_view: MenuViewDTO) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for row in menu_view.rows:
            buttons = [
                InlineKeyboardButton(
                    text=item.label,
                    callback_data=AdminMenuCallback(action=item.action).pack(),
                )
                for item in row
            ]
            builder.row(*buttons)
        return builder.as_markup()

    @staticmethod
    def build_admin_bots_list_keyboard(view: BotsListViewDTO) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for item in view.items:
            builder.row(
                InlineKeyboardButton(
                    text=item.label,
                    callback_data=AdminBotsListCallback(
                        action=AdminBotsListAction.VIEW,
                        bot_id=item.telegram_id,
                        page=view.page,
                    ).pack(),
                )
            )

        if view.total_pages > 1:
            controls: list[InlineKeyboardButton] = []
            if view.page > 1:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["prev"],
                        callback_data=AdminBotsListCallback(
                            action=AdminBotsListAction.PAGE,
                            page=view.page - 1,
                        ).pack(),
                    )
                )
            controls.append(
                InlineKeyboardButton(
                    text=RU_BUTTONS["pagination"]["indicator"].format(
                        current=view.page,
                        total=view.total_pages,
                    ),
                    callback_data=AdminBotsListCallback(
                        action=AdminBotsListAction.PAGE,
                        page=view.page,
                    ).pack(),
                )
            )
            if view.page < view.total_pages:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["next"],
                        callback_data=AdminBotsListCallback(
                            action=AdminBotsListAction.PAGE,
                            page=view.page + 1,
                        ).pack(),
                    )
                )
            builder.row(*controls)

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["common"]["back"],
                callback_data=AdminBotsListCallback(action=AdminBotsListAction.BACK).pack(),
            )
        )

        return builder.as_markup()

    @staticmethod
    def build_admin_bot_card_keyboard(card: BotCardDTO, page: int | None = None) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["bots"]["free_posts"],
                callback_data=AdminBotActionCallback(
                    action=AdminBotAction.FREE_PROMPT,
                    bot_id=card.telegram_id,
                    page=page,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["bots"]["delete"],
                callback_data=AdminBotActionCallback(
                    action=AdminBotAction.DELETE_PROMPT,
                    bot_id=card.telegram_id,
                    page=page,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["common"]["back"],
                callback_data=AdminBotActionCallback(
                    action=AdminBotAction.BACK_TO_LIST,
                    bot_id=card.telegram_id,
                    page=page,
                ).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_bot_free_prompt_keyboard(prompt: BotFreePromptDTO, page: int | None = None) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["confirm"]["mode_instant"],
                callback_data=AdminBotActionCallback(
                    action=AdminBotAction.FREE_EXECUTE,
                    bot_id=prompt.telegram_id,
                    mode=AdminBotFreeMode.INSTANT,
                    page=page,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["confirm"]["mode_graceful"],
                callback_data=AdminBotActionCallback(
                    action=AdminBotAction.FREE_EXECUTE,
                    bot_id=prompt.telegram_id,
                    mode=AdminBotFreeMode.GRACEFUL,
                    page=page,
                ).pack(),
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["confirm"]["decline"],
                callback_data=AdminBotActionCallback(
                    action=AdminBotAction.BACK_TO_LIST,
                    bot_id=prompt.telegram_id,
                    page=page,
                ).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_bot_delete_prompt_keyboard(prompt: BotDeletePromptDTO, page: int | None = None) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["confirm"]["yes"],
                callback_data=AdminBotActionCallback(
                    action=AdminBotAction.DELETE_CONFIRM,
                    bot_id=prompt.telegram_id,
                    page=page,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["confirm"]["no"],
                callback_data=AdminBotActionCallback(
                    action=AdminBotAction.BACK_TO_LIST,
                    bot_id=prompt.telegram_id,
                    page=page,
                ).pack(),
            ),
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_placeholder_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["common"]["back"],
                callback_data=AdminBotsListCallback(action=AdminBotsListAction.BACK).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distributions_menu_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["create"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.START_CREATE).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["list"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.LIST,
                    page=1,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["common"]["back"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.BACK).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distributions_list_keyboard(view: DistributionsListViewDTO) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for item in view.items:
            builder.row(
                InlineKeyboardButton(
                    text=item.label,
                    callback_data=AdminDistributionsCallback(
                        action=AdminDistributionsAction.LIST_VIEW,
                        distribution_id=str(base64.urlsafe_b64encode(item.distribution_id.bytes).rstrip(b'=').decode()),
                        page=view.page,
                    ).pack(),
                )
            )

        if view.total_pages > 1:
            controls: list[InlineKeyboardButton] = []
            if view.page > 1:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["prev"],
                        callback_data=AdminDistributionsCallback(
                            action=AdminDistributionsAction.LIST_PAGE,
                            page=view.page - 1,
                        ).pack(),
                    )
                )
            controls.append(
                InlineKeyboardButton(
                    text=RU_BUTTONS["pagination"]["indicator"].format(
                        current=view.page,
                        total=view.total_pages,
                    ),
                    callback_data=AdminDistributionsCallback(
                        action=AdminDistributionsAction.LIST_PAGE,
                        page=view.page,
                    ).pack(),
                )
            )
            if view.page < view.total_pages:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["next"],
                        callback_data=AdminDistributionsCallback(
                            action=AdminDistributionsAction.LIST_PAGE,
                            page=view.page + 1,
                        ).pack(),
                    )
                )
            builder.row(*controls)

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back_to_menu"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.OPEN).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_mode_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["mode_create"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.SET_MODE,
                    mode="create",
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["mode_replace"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.SET_MODE,
                    mode="replace",
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["cancel"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.CANCEL).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_target_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["target_groups"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.SET_TARGET,
                    target="groups",
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["target_bots"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.SET_TARGET,
                    target="bots",
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["target_all"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.SET_TARGET,
                    target="all",
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.START_CREATE).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["cancel"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.CANCEL).pack(),
            ),
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_bot_select_keyboard(
        items: list[tuple[str, str, bool]],
        *,
        page: int,
        total_pages: int,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for bot_id, label, selected in items:
            prefix = "✅ " if selected else "▫️ "
            builder.row(
                InlineKeyboardButton(
                    text=f"{prefix}{label}",
                    callback_data=AdminDistributionsCallback(
                        action=AdminDistributionsAction.SELECT_BOT,
                        bot_id=bot_id,
                        page=page,
                    ).pack(),
                )
            )

        if total_pages > 1:
            controls: list[InlineKeyboardButton] = []
            if page > 1:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["prev"],
                        callback_data=AdminDistributionsCallback(
                            action=AdminDistributionsAction.BOT_PAGE,
                            page=page - 1,
                        ).pack(),
                    )
                )
            controls.append(
                InlineKeyboardButton(
                    text=RU_BUTTONS["pagination"]["indicator"].format(current=page, total=total_pages),
                    callback_data=AdminDistributionsCallback(
                        action=AdminDistributionsAction.BOT_PAGE,
                        page=page,
                    ).pack(),
                )
            )
            if page < total_pages:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["next"],
                        callback_data=AdminDistributionsCallback(
                            action=AdminDistributionsAction.BOT_PAGE,
                            page=page + 1,
                        ).pack(),
                    )
                )
            builder.row(*controls)

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["continue"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.FINISH_BOT_SELECTION,
                    page=page,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.SELECT_TARGET).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["cancel"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.CANCEL).pack(),
            ),
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_card_keyboard(card: DistributionCardDTO, *, page: int | None = None) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        encoded_distribution_id = str(base64.urlsafe_b64encode(card.distribution_id.bytes).rstrip(b'=').decode())
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["refresh"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.LIST_REFRESH,
                    distribution_id=encoded_distribution_id,
                    page=page,
                ).pack(),
            )
        )

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["start_all"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.TOGGLE_STATUS,
                    distribution_id=encoded_distribution_id,
                    choice="resume",
                    page=page,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["stop_all"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.TOGGLE_STATUS,
                    distribution_id=encoded_distribution_id,
                    choice="pause",
                    page=page,
                ).pack(),
            )
        )

        notify_choice = "off" if card.notify_on_failure else "on"
        notify_label = (
            RU_BUTTONS["distributions"]["disable_notify"]
            if card.notify_on_failure
            else RU_BUTTONS["distributions"]["enable_notify"]
        )
        builder.row(
            InlineKeyboardButton(
                text=notify_label,
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.TOGGLE_NOTIFY,
                    distribution_id=encoded_distribution_id,
                    choice=notify_choice,
                    page=page,
                ).pack(),
            )
        )

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["groups"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.SHOW_GROUPS,
                    distribution_id=encoded_distribution_id,
                    page=1,
                    card_page=page,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["delete"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.DELETE,
                    distribution_id=encoded_distribution_id,
                    page=page,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back_to_list"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.LIST_BACK,
                    page=page,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back_to_menu"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.OPEN).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_groups_input_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.SELECT_TARGET).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["cancel"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.CANCEL).pack(),
            ),
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_source_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.SELECT_TARGET).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["cancel"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.CANCEL).pack(),
            ),
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_name_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["auto_name"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.NAME_AUTO,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["cancel"],
                callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.CANCEL).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_boolean_keyboard(
        action: AdminDistributionsAction,
        *,
        back_action: AdminDistributionsAction | None = None,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["confirm"]["yes"],
                callback_data=AdminDistributionsCallback(
                    action=action,
                    choice="yes",
                ).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["confirm"]["no"],
                callback_data=AdminDistributionsCallback(
                    action=action,
                    choice="no",
                ).pack(),
            ),
        )
        if back_action:
            builder.row(
                InlineKeyboardButton(
                    text=RU_BUTTONS["distributions"]["back"],
                    callback_data=AdminDistributionsCallback(action=back_action).pack(),
                ),
                InlineKeyboardButton(
                    text=RU_BUTTONS["distributions"]["cancel"],
                    callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.CANCEL).pack(),
                ),
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=RU_BUTTONS["distributions"]["cancel"],
                    callback_data=AdminDistributionsCallback(action=AdminDistributionsAction.CANCEL).pack(),
                )
            )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_groups_keyboard(
        view: DistributionGroupsViewDTO,
        *,
        distribution_id: UUID,
        card_page: int,
        anchor_post_id: UUID | None,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        encoded_distribution_id = str(base64.urlsafe_b64encode(distribution_id.bytes).rstrip(b'=').decode())
        encoded_anchor_post_id = (
            str(base64.urlsafe_b64encode(anchor_post_id.bytes).rstrip(b'=').decode())
            if anchor_post_id is not None
            else None
        )

        for item in view.items:
            encoded_post_id = str(base64.urlsafe_b64encode(item.post_id.bytes).rstrip(b'=').decode())
            builder.row(
                InlineKeyboardButton(
                    text=item.label,
                    callback_data=AdminDistributionsCallback(
                        action=AdminDistributionsAction.GROUP_VIEW,
                        post_id=encoded_post_id,
                        page=view.page,
                        card_page=card_page,
                    ).pack(),
                )
            )

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["groups_add"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_ADD,
                    distribution_id=encoded_distribution_id,
                    page=view.page,
                    card_page=card_page,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["groups_delete"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_DELETE,
                    distribution_id=encoded_distribution_id,
                    page=view.page,
                    card_page=card_page,
                ).pack(),
            ),
        )

        if view.total_pages > 1 and encoded_anchor_post_id is not None:
            controls: list[InlineKeyboardButton] = []
            if view.page > 1:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["prev"],
                        callback_data=AdminDistributionsCallback(
                            action=AdminDistributionsAction.GROUPS_PAGE,
                            page=view.page - 1,
                            post_id=encoded_anchor_post_id,
                            card_page=card_page,
                        ).pack(),
                    )
                )
            controls.append(
                InlineKeyboardButton(
                    text=RU_BUTTONS["pagination"]["indicator"].format(
                        current=view.page,
                        total=view.total_pages,
                    ),
                    callback_data=AdminDistributionsCallback(
                        action=AdminDistributionsAction.GROUPS_PAGE,
                        page=view.page,
                        post_id=encoded_anchor_post_id,
                        card_page=card_page,
                    ).pack(),
                )
            )
            if view.page < view.total_pages:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["next"],
                        callback_data=AdminDistributionsCallback(
                            action=AdminDistributionsAction.GROUPS_PAGE,
                            page=view.page + 1,
                            post_id=encoded_anchor_post_id,
                            card_page=card_page,
                        ).pack(),
                    )
                )
            builder.row(*controls)

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back_to_card"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.LIST_VIEW,
                    distribution_id=encoded_distribution_id,
                    page=card_page,
                ).pack(),
            )
        )

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back_to_list"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.LIST_BACK,
                    page=card_page,
                ).pack(),
            )
        )

        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_groups_add_method_keyboard(
        *,
        distribution_id: UUID,
        groups_page: int,
        card_page: int,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        encoded_distribution_id = str(base64.urlsafe_b64encode(distribution_id.bytes).rstrip(b'=').decode())
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["groups_add_manual"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_ADD_MANUAL,
                    distribution_id=encoded_distribution_id,
                    page=groups_page,
                    card_page=card_page,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["groups_add_bindings"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_ADD_BINDINGS,
                    distribution_id=encoded_distribution_id,
                    page=1,
                    card_page=card_page,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back_to_groups"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.SHOW_GROUPS,
                    distribution_id=encoded_distribution_id,
                    page=groups_page,
                    card_page=card_page,
                ).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_groups_add_manual_keyboard(
        *,
        distribution_id: UUID,
        groups_page: int,
        card_page: int,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        encoded_distribution_id = str(base64.urlsafe_b64encode(distribution_id.bytes).rstrip(b'=').decode())
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["groups_add_cancel"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_ADD_CANCEL,
                    distribution_id=encoded_distribution_id,
                    page=groups_page,
                    card_page=card_page,
                ).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_groups_bindings_keyboard(
        items: list[tuple[str, str, bool]],
        *,
        distribution_id: UUID,
        page: int,
        total_pages: int,
        groups_page: int,
        card_page: int,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        encoded_distribution_id = str(base64.urlsafe_b64encode(distribution_id.bytes).rstrip(b'=').decode())

        for group_id, label, selected in items:
            prefix = "✅ " if selected else "▫️ "
            builder.row(
                InlineKeyboardButton(
                    text=f"{prefix}{label}",
                    callback_data=AdminDistributionsCallback(
                        action=AdminDistributionsAction.GROUPS_ADD_TOGGLE,
                        distribution_id=encoded_distribution_id,
                        group_id=group_id,
                        page=page,
                        card_page=card_page,
                    ).pack(),
                )
            )

        if total_pages > 1:
            controls: list[InlineKeyboardButton] = []
            if page > 1:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["prev"],
                        callback_data=AdminDistributionsCallback(
                            action=AdminDistributionsAction.GROUPS_ADD_BINDINGS_PAGE,
                            distribution_id=encoded_distribution_id,
                            page=page - 1,
                            card_page=card_page,
                        ).pack(),
                    )
                )
            controls.append(
                InlineKeyboardButton(
                    text=RU_BUTTONS["pagination"]["indicator"].format(current=page, total=total_pages),
                    callback_data=AdminDistributionsCallback(
                        action=AdminDistributionsAction.GROUPS_ADD_BINDINGS_PAGE,
                        distribution_id=encoded_distribution_id,
                        page=page,
                        card_page=card_page,
                    ).pack(),
                )
            )
            if page < total_pages:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["next"],
                        callback_data=AdminDistributionsCallback(
                            action=AdminDistributionsAction.GROUPS_ADD_BINDINGS_PAGE,
                            distribution_id=encoded_distribution_id,
                            page=page + 1,
                            card_page=card_page,
                        ).pack(),
                    )
                )
            builder.row(*controls)

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["groups_add_apply"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_ADD_APPLY,
                    distribution_id=encoded_distribution_id,
                    page=page,
                    card_page=card_page,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["groups_add_cancel"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_ADD_CANCEL,
                    distribution_id=encoded_distribution_id,
                    page=groups_page,
                    card_page=card_page,
                ).pack(),
            ),
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_groups_delete_keyboard(
        view: DistributionGroupsViewDTO,
        *,
        distribution_id: UUID,
        card_page: int,
        selected_ids: set[str],
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        encoded_distribution_id = str(base64.urlsafe_b64encode(distribution_id.bytes).rstrip(b'=').decode())

        for item in view.items:
            group_id = str(item.group_id)
            prefix = "✅ " if group_id in selected_ids else "▫️ "
            builder.row(
                InlineKeyboardButton(
                    text=f"{prefix}{item.label}",
                    callback_data=AdminDistributionsCallback(
                        action=AdminDistributionsAction.GROUPS_DELETE_TOGGLE,
                        distribution_id=encoded_distribution_id,
                        group_id=group_id,
                        page=view.page,
                        card_page=card_page,
                    ).pack(),
                )
            )

        if view.total_pages > 1:
            controls: list[InlineKeyboardButton] = []
            if view.page > 1:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["prev"],
                        callback_data=AdminDistributionsCallback(
                            action=AdminDistributionsAction.GROUPS_DELETE_PAGE,
                            distribution_id=encoded_distribution_id,
                            page=view.page - 1,
                            card_page=card_page,
                        ).pack(),
                    )
                )
            controls.append(
                InlineKeyboardButton(
                    text=RU_BUTTONS["pagination"]["indicator"].format(current=view.page, total=view.total_pages),
                    callback_data=AdminDistributionsCallback(
                        action=AdminDistributionsAction.GROUPS_DELETE_PAGE,
                        distribution_id=encoded_distribution_id,
                        page=view.page,
                        card_page=card_page,
                    ).pack(),
                )
            )
            if view.page < view.total_pages:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["next"],
                        callback_data=AdminDistributionsCallback(
                            action=AdminDistributionsAction.GROUPS_DELETE_PAGE,
                            distribution_id=encoded_distribution_id,
                            page=view.page + 1,
                            card_page=card_page,
                        ).pack(),
                    )
                )
            builder.row(*controls)

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["groups_delete_cancel"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_DELETE_CANCEL,
                    distribution_id=encoded_distribution_id,
                    page=view.page,
                    card_page=card_page,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["groups_delete_apply"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_DELETE_CONFIRM,
                    distribution_id=encoded_distribution_id,
                    page=view.page,
                    card_page=card_page,
                ).pack(),
            ),
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_groups_delete_confirm_keyboard(
        *,
        distribution_id: UUID,
        page: int,
        card_page: int,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        encoded_distribution_id = str(base64.urlsafe_b64encode(distribution_id.bytes).rstrip(b'=').decode())
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["confirm"]["yes"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_DELETE_CONFIRM,
                    distribution_id=encoded_distribution_id,
                    page=page,
                    card_page=card_page,
                    choice="yes",
                ).pack(),
            ),
            InlineKeyboardButton(
                text=RU_BUTTONS["confirm"]["no"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.GROUPS_DELETE_CONFIRM,
                    distribution_id=encoded_distribution_id,
                    page=page,
                    card_page=card_page,
                    choice="no",
                ).pack(),
            ),
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_distribution_group_card_keyboard(
        card: DistributionGroupCardDTO,
        *,
        distribution_id: UUID,
        groups_page: int,
        card_page: int,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        encoded_distribution_id = str(base64.urlsafe_b64encode(distribution_id.bytes).rstrip(b'=').decode())
        encoded_post_id = str(base64.urlsafe_b64encode(card.post_id.bytes).rstrip(b'=').decode())
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back_to_groups"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.SHOW_GROUPS,
                    post_id=encoded_post_id,
                    page=groups_page,
                    card_page=card_page,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back_to_card"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.LIST_VIEW,
                    distribution_id=encoded_distribution_id,
                    page=card_page,
                ).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["distributions"]["back_to_list"],
                callback_data=AdminDistributionsCallback(
                    action=AdminDistributionsAction.LIST_BACK,
                    page=card_page,
                ).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_groups_menu_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["groups"]["add_bindings"],
                callback_data=AdminGroupsCallback(action=AdminGroupsAction.ADD).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["groups"]["list_bindings"],
                callback_data=AdminGroupsCallback(action=AdminGroupsAction.LIST).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["common"]["back"],
                callback_data=AdminBotsListCallback(action=AdminBotsListAction.BACK).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_groups_list_keyboard(view: GroupsListViewDTO) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for item in view.items:
            builder.row(
                InlineKeyboardButton(
                    text=item.label,
                    callback_data=AdminGroupsCallback(
                        action=AdminGroupsAction.VIEW,
                        group_id=str(item.group_id),
                        page=view.page,
                    ).pack(),
                )
            )

        if view.total_pages > 1:
            controls: list[InlineKeyboardButton] = []
            if view.page > 1:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["prev"],
                        callback_data=AdminGroupsCallback(
                            action=AdminGroupsAction.PAGE,
                            page=view.page - 1,
                        ).pack(),
                    )
                )
            controls.append(
                InlineKeyboardButton(
                    text=RU_BUTTONS["pagination"]["indicator"].format(
                        current=view.page,
                        total=view.total_pages,
                    ),
                    callback_data=AdminGroupsCallback(
                        action=AdminGroupsAction.PAGE,
                        page=view.page,
                    ).pack(),
                )
            )
            if view.page < view.total_pages:
                controls.append(
                    InlineKeyboardButton(
                        text=RU_BUTTONS["pagination"]["next"],
                        callback_data=AdminGroupsCallback(
                            action=AdminGroupsAction.PAGE,
                            page=view.page + 1,
                        ).pack(),
                    )
                )
            builder.row(*controls)

        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["groups"]["add_bindings"],
                callback_data=AdminGroupsCallback(action=AdminGroupsAction.ADD).pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["common"]["back"],
                callback_data=AdminGroupsCallback(action=AdminGroupsAction.OPEN).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_group_card_keyboard(card: GroupCardDTO, page: int | None = None) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["groups"]["refresh"],
                callback_data=AdminGroupsCallback(
                    action=AdminGroupsAction.CARD_REFRESH,
                    group_id=str(card.group_id),
                    page=page,
                ).pack(),
            )
        )
        if card.bot_id:
            builder.row(
                InlineKeyboardButton(
                    text=RU_BUTTONS["groups"]["unbind"],
                    callback_data=AdminGroupsCallback(
                        action=AdminGroupsAction.CARD_UNBIND,
                        group_id=str(card.group_id),
                        page=page,
                    ).pack(),
                )
            )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["groups"]["back_to_list"],
                callback_data=AdminGroupsCallback(
                    action=AdminGroupsAction.CARD_BACK,
                    page=page,
                ).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def build_admin_groups_choose_bot_keyboard(items: list[tuple[str, str]]) -> InlineKeyboardMarkup:
        """items: list of (label, bot_telegram_id)"""
        builder = InlineKeyboardBuilder()
        for label, telegram_id in items:
            builder.row(
                InlineKeyboardButton(
                    text=label,
                    callback_data=AdminGroupsBindCallback(action=AdminGroupsAction.CHOOSE_BOT, bot_id=telegram_id).pack(),
                )
            )
        builder.row(
            InlineKeyboardButton(
                text=RU_BUTTONS["common"]["cancel"],
                callback_data=AdminGroupsCallback(action=AdminGroupsAction.OPEN).pack(),
            )
        )
        return builder.as_markup()
