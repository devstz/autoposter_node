from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Iterable, Optional
from uuid import UUID

from common.dto import BotDTO, GroupAssignResultDTO
from common.enums import AdminMenuAction, AdminBotFreeMode
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
)
from services import BotService


class AdminUX:
    def __init__(
        self,
        *,
        bot_service: BotService,
        main_menu_uc: ShowMainMenuUseCase,
        bots_list_uc: ShowBotsListUseCase,
        bot_card_uc: ShowBotCardUseCase,
        groups_list_uc: ShowGroupsListUseCase,
        group_card_uc: ShowGroupCardUseCase,
        distributions_list_uc: ShowDistributionsListUseCase,
        distribution_card_uc: ShowDistributionCardUseCase,
        distribution_groups_uc: ShowDistributionGroupsUseCase,
        distribution_group_card_uc: ShowDistributionGroupCardUseCase,

        free_prompt_uc: PrepareFreeBotUseCase,
        free_uc: FreeBotUseCase,
        delete_prompt_uc: PrepareDeleteBotUseCase,
        delete_uc: DeleteBotUseCase,
        placeholder_uc: ShowPlaceholderUseCase,
        admin_texts: dict[str, str] | None = None,
        menu_texts: dict[str, str] | None = None,
        bots_texts: dict[str, str] | None = None,
        groups_texts: dict[str, str] | None = None,
        distributions_texts: dict[str, str] | None = None,
    ) -> None:
        self._main_menu_uc = main_menu_uc
        self._bots_list_uc = bots_list_uc
        self._bot_card_uc = bot_card_uc
        self._groups_list_uc = groups_list_uc
        self._group_card_uc = group_card_uc
        self._distributions_list_uc = distributions_list_uc
        self._distribution_card_uc = distribution_card_uc
        self._distribution_groups_uc = distribution_groups_uc
        self._distribution_group_card_uc = distribution_group_card_uc
        self._free_prompt_uc = free_prompt_uc
        self._free_uc = free_uc
        self._delete_prompt_uc = delete_prompt_uc
        self._delete_uc = delete_uc
        self._placeholder_uc = placeholder_uc
        self._bot_service = bot_service
        self._admin_texts = admin_texts or {}
        self._menu_texts = menu_texts or {}
        self._bots_texts = bots_texts or {}
        self._groups_texts = groups_texts or {}
        self._distributions_texts = distributions_texts or {}

    async def show_main_menu(self):
        return await self._main_menu_uc()

    async def show_bots_list(self, page: int = 1):
        return await self._bots_list_uc(page)

    async def show_bot_card(self, bot_id: UUID):
        return await self._bot_card_uc(bot_id)

    async def show_groups_list(self, page: int = 1):
        return await self._groups_list_uc(page)

    async def show_group_card(self, group_id: UUID):
        return await self._group_card_uc(group_id)

    async def prepare_free_bot(self, bot_id: UUID):
        return await self._free_prompt_uc(bot_id)

    async def free_bot(self, bot_id: UUID, mode: AdminBotFreeMode):
        return await self._free_uc(bot_id, mode)

    async def prepare_delete_bot(self, bot_id: UUID):
        return await self._delete_prompt_uc(bot_id)

    async def delete_bot(self, bot_id: UUID):
        return await self._delete_uc(bot_id)

    async def placeholder(self, action: AdminMenuAction) -> str:
        return await self._placeholder_uc(action)

    async def resolve_bot_uuid(self, telegram_id: str) -> UUID | None:
        bot = await self._bot_service.get_by_telegram_id(telegram_id)
        if bot is None:
            return None
        return bot.id

    async def show_distributions_list(self, page: int = 1):
        return await self._distributions_list_uc(page)

    async def show_distribution_card(self, distribution_id: UUID):
        return await self._distribution_card_uc(distribution_id)

    async def show_distribution_groups(self, distribution_id: UUID, *, page: int = 1):
        return await self._distribution_groups_uc(distribution_id, page)

    async def show_distribution_group_card(self, distribution_id: UUID, post_id: UUID):
        return await self._distribution_group_card_uc(distribution_id, post_id)

    async def get_start_text(self) -> str:
        return self._admin_texts.get("start", "")

    def groups_menu_text(self) -> str:
        return self._compose_section_text(
            self._groups_texts.get("section_title", ""),
            self._groups_texts.get("menu_hint", ""),
        )

    def distributions_menu_text(self) -> str:
        return self._compose_section_text(
            self._distributions_texts.get("section_title", ""),
            self._distributions_texts.get("menu_hint", ""),
        )

    def groups_add_prompt(self) -> str:
        return self._groups_texts.get("add_prompt", "")

    def groups_choose_bot_prompt(self) -> str:
        return self._groups_texts.get("choose_bot_prompt", "")

    def distribution_cancelled_text(self) -> str:
        return self._distributions_texts.get("cancelled", "Отменено.")

    def distribution_groups_not_found_text(self) -> str:
        return self._distributions_texts.get("groups_not_found", "Список групп пуст.")

    def distribution_bad_source_text(self) -> str:
        return self._distributions_texts.get("bad_source", "Не удалось распознать сообщение.")

    def distribution_error_no_groups_text(self) -> str:
        return self._distributions_texts.get("error_no_groups", "Нет групп.")

    def distribution_all_groups_selected_text(self, count: int) -> str:
        base = self._distributions_texts.get("all_groups_selected", "Будут использованы все группы.")
        resolved = self._distributions_texts.get("groups_resolved", "Найдено групп: {count}.")
        return base + "\n" + resolved.format(count=count)

    def distribution_name_prompt_text(self) -> str:
        lines = [
            self._distributions_texts.get("create_title", ""),
            self._distributions_texts.get("ask_name", "Отправь название рассылки."),
            self._distributions_texts.get("ask_name_hint", "Или нажми кнопку для автоматического названия."),
        ]
        return "\n\n".join(filter(None, lines))

    def distribution_name_invalid_text(self) -> str:
        return self._distributions_texts.get("name_invalid", "Укажи название или воспользуйся автоназванием.")

    def distribution_name_autoset_text(self, value: str) -> str:
        template = self._distributions_texts.get("name_autoset", "Название установлено: {name}")
        return template.format(name=value)

    def distribution_name_selected_text(self, value: str | None) -> str:
        return self._format_selected_name(value)

    def distribution_pause_prompt_text(self, prefix: str | None) -> str:
        lines = [
            self._distributions_texts.get("create_title", ""),
            prefix or "",
            self._distributions_texts.get("ask_pause", ""),
        ]
        return "\n\n".join(filter(None, lines))

    def distribution_pause_invalid_text(self) -> str:
        return self._distributions_texts.get("pause_invalid", "Отправь целое число секунд.")

    def distribution_delete_last_prompt_text(self) -> str:
        lines = [
            self._distributions_texts.get("create_title", ""),
            self._distributions_texts.get("ask_delete_last", ""),
        ]
        return "\n\n".join(filter(None, lines))

    def distribution_pin_prompt_text(self) -> str:
        lines = [
            self._distributions_texts.get("create_title", ""),
            self._distributions_texts.get("ask_pin", ""),
        ]
        return "\n\n".join(filter(None, lines))

    def distribution_pin_frequency_prompt_text(self) -> str:
        lines = [
            self._distributions_texts.get("create_title", ""),
            self._distributions_texts.get("ask_pin_frequency", ""),
        ]
        return "\n\n".join(filter(None, lines))

    def distribution_pin_frequency_invalid_text(self) -> str:
        return self._distributions_texts.get("pin_frequency_invalid", "Отправь неотрицательное целое число.")

    def distribution_target_attempts_prompt_text(self) -> str:
        lines = [
            self._distributions_texts.get("create_title", ""),
            self._distributions_texts.get("ask_target_attempts", ""),
        ]
        return "\n\n".join(filter(None, lines))

    def distribution_deleted_alert_text(self, name: str | None, count: int) -> str:
        template = self._distributions_texts.get(
            "deleted_alert",
            "Рассылка «{name}» удалена. Удалено постов: {count}.",
        )
        fallback = self._distributions_texts.get("card_name_placeholder", "Без названия")
        return template.format(name=name or fallback, count=count)

    def distribution_delete_missing_text(self) -> str:
        return self._distributions_texts.get(
            "delete_missing",
            "Рассылка не найдена или уже удалена.",
        )

    def distribution_target_attempts_invalid_text(self) -> str:
        return self._distributions_texts.get(
            "target_attempts_invalid",
            "Отправь -1 или положительное целое число.",
        )

    def distribution_bool_invalid_text(self) -> str:
        return self._distributions_texts.get("bool_invalid", "Ответь «да» или «нет».")

    def distribution_groups_resolved_text(self, count: int) -> str:
        template = self._distributions_texts.get("groups_resolved", "Найдено групп: {count}.")
        return template.format(count=count)

    def distribution_groups_missing_text(self, ids: Iterable[int]) -> str:
        template = self._distributions_texts.get("groups_missing", "Не найдены: {ids}")
        joined = ", ".join(str(item) for item in ids)
        return template.format(ids=joined)

    def distribution_mode_prompt_text(self, name: str | None = None) -> str:
        lines = [
            self._distributions_texts.get("create_title", ""),
            self._format_selected_name(name),
            self._distributions_texts.get("mode_prompt", ""),
            f"• {self._distributions_texts.get('mode_create_hint', '')}",
            f"• {self._distributions_texts.get('mode_replace_hint', '')}",
        ]
        return "\n".join(filter(None, lines))

    def distribution_target_prompt_text(self, mode: str, name: str | None = None) -> str:
        mode_hint = (
            self._distributions_texts.get("mode_create_hint")
            if mode == "create"
            else self._distributions_texts.get("mode_replace_hint", "")
        )
        lines = [
            self._distributions_texts.get("create_title", ""),
            self._format_selected_name(name),
            mode_hint,
            "",
            self._distributions_texts.get("target_prompt", ""),
        ]
        return "\n".join(filter(None, lines))

    def distribution_groups_input_text(self) -> str:
        lines = [
            self._distributions_texts.get("create_title", ""),
            self._distributions_texts.get("ask_group_ids", ""),
        ]
        return "\n\n".join(filter(None, lines))

    def distribution_bot_selection_intro(self) -> str:
        lines = [
            self._distributions_texts.get("bot_selection_title", ""),
            self._distributions_texts.get("bot_selection_hint", ""),
        ]
        return "\n\n".join(filter(None, lines))

    def distribution_bot_selection_selected_text(self, count: int) -> str:
        template = self._distributions_texts.get("bot_selection_selected", "Выбрано: {count}")
        return template.format(count=count)

    def distribution_bot_selection_empty_text(self) -> str:
        return self._distributions_texts.get("bot_selection_empty", "Выберите ботов.")

    def distribution_bot_selection_no_groups_text(self) -> str:
        return self._distributions_texts.get("bot_selection_no_groups", "Нет групп.")

    def distribution_source_prompt(self, prefix: str) -> str:
        lines = [
            self._distributions_texts.get("create_title", ""),
            prefix,
            self._distributions_texts.get("ask_source", ""),
        ]
        return "\n\n".join(filter(None, lines))

    def distribution_result_text(
        self,
        *,
        mode: str,
        deleted_count: int,
        created: int,
        skipped: int,
        errors: Iterable[str],
    ) -> str:
        lines = [self._distributions_texts.get("result_title", "Готово")]
        if mode == "replace" and deleted_count:
            lines.append(
                self._distributions_texts.get("result_replaced", "Удалено постов: {count}.").format(count=deleted_count)
            )
        lines.append(
            self._distributions_texts.get("result_created", "Создано: {created}.").format(created=created)
        )
        if skipped:
            lines.append(
                self._distributions_texts.get("result_skipped", "Пропущено: {skipped}.").format(skipped=skipped)
            )
        errors_list = [escape(item, quote=False) for item in errors]
        '''if errors_list:
            lines.append(
                self._distributions_texts.get("result_errors", "Ошибки:\n{items}").format(items="\n".join(errors_list))
            )'''
        return "\n\n".join(lines)

    def format_bot_label(self, bot: BotDTO | None) -> str:
        if bot is None:
            return self._groups_texts.get("card_not_bound", "—")
        name = bot.name or ""
        username = bot.username or ""
        if name and username:
            return f"{name} (@{username})"
        if name:
            return name
        if username:
            return f"@{username}"
        return bot.telegram_id

    def format_bot_load_label(self, bot: BotDTO, *, current: int, limit: int) -> str:
        display = self.format_bot_label(bot)
        template = self._bots_texts.get("item_template", "{status} {name} ({current}/{limit})")
        return template.format(status="", name=display, current=current, limit=limit)

    def format_group_bind_result(
        self,
        *,
        assign_result: GroupAssignResultDTO | None,
        fail: Iterable[int],
        previous_map: dict[UUID, Optional[BotDTO]],
    ) -> str:
        text_parts: list[str] = [self._groups_texts.get("bind_result_title", "")]

        if assign_result and assign_result.newly_assigned:
            ok_text = "\n".join(str(item.tg_chat_id) for item in assign_result.newly_assigned)
            text_parts.append(self._groups_texts.get("bind_ok", "").format(ok=ok_text))

        if assign_result and assign_result.reassigned:
            pairs = []
            for item in assign_result.reassigned:
                prev_label = self.format_bot_label(previous_map.get(item.previous_bot_id))
                pairs.append(f"{item.group.tg_chat_id} ({prev_label})")
            if pairs:
                text_parts.append(
                    self._groups_texts.get("bind_reassigned", "").format(pairs="\n".join(pairs))
                )

        if assign_result and assign_result.already_assigned:
            already_text = "\n".join(str(item.tg_chat_id) for item in assign_result.already_assigned)
            text_parts.append(
                self._groups_texts.get("bind_already", "").format(already=already_text)
            )

        fail_list = list(fail)
        if fail_list:
            text_parts.append(
                self._groups_texts.get("bind_fail", "").format(fail="\n".join(str(x) for x in fail_list))
            )

        return "\n\n".join(part for part in text_parts if part)

    def _compose_section_text(self, title: str, hint: str) -> str:
        return "\n\n".join(filter(None, [title, hint]))

    def _format_selected_name(self, name: str | None) -> str:
        if not name:
            return ""
        template = self._distributions_texts.get("name_selected", "Название: {name}")
        return template.format(name=name)


@dataclass(slots=True)
class UXContext:
    admin: AdminUX
