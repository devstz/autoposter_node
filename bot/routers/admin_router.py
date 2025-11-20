from __future__ import annotations

import math
import base64
from datetime import datetime
from logging import getLogger
from uuid import UUID

from aiogram import F
from aiogram.enums.chat_type import ChatType
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.middlewares.admin import connect_admin_middlewares
from bot.routers.base import BaseRouter
from bot.ux import UXContext
from bot.keyboards.inline import AdminInlineKeyboards
from bot.keyboards.callback_data import (
AdminMenuCallback,
AdminBotsListCallback,
AdminBotActionCallback,
AdminGroupsCallback,
AdminGroupsBindCallback,
AdminDistributionsCallback,
)
from common.enums import (
AdminMenuAction,
AdminBotsListAction,
AdminBotAction,
AdminBotFreeMode,
AdminGroupsAction,
AdminDistributionsAction,
)
from common.dto import BotDTO, GroupDTO
from .helper import edit_message
from bot.states.admin.admin_states import AdminStates
from services import BotService, GroupService, PostService

logger = getLogger(__name__)

class AdminRouter(BaseRouter):
    chat_types = ChatType.PRIVATE
    def setup_middlewares(self):
        connect_admin_middlewares(self)

    def setup_handlers(self):
        # ==========================
        # /help и старт
        # ==========================
        @self.message(Command("help"))
        async def help_command(message: Message, ux: UXContext):
            start_text = await ux.admin.get_start_text()
            await message.answer(start_text)

        @self.message(CommandStart())
        async def admin_panel(message: Message, ux: UXContext):
            menu_view = await ux.admin.show_main_menu()
            keyboard = AdminInlineKeyboards.build_admin_menu_keyboard(menu_view)
            await edit_message(message, menu_view.text, reply_markup=keyboard)

        # ==========================
        # Главное меню
        # ==========================
        @self.callback_query(AdminMenuCallback.filter(F.action == AdminMenuAction.BOTS))
        async def menu_bots(callback: CallbackQuery, ux: UXContext, state: FSMContext):
            await state.clear()
            await self._render_bots_list(callback, ux, page=1)

        @self.callback_query(AdminMenuCallback.filter(F.action == AdminMenuAction.GROUPS))
        async def menu_groups(callback: CallbackQuery, ux: UXContext, state: FSMContext):
            await state.clear()
            text = ux.admin.groups_menu_text()
            keyboard = AdminInlineKeyboards.build_admin_groups_menu_keyboard()
            await edit_message(callback, text, reply_markup=keyboard)

        @self.callback_query(AdminMenuCallback.filter(F.action == AdminMenuAction.DISTRIBUTIONS))
        async def menu_distributions(callback: CallbackQuery, ux: UXContext, state: FSMContext):
            await state.clear()
            await self._render_distributions_menu(callback, ux)

        @self.callback_query(AdminMenuCallback.filter())
        async def menu_placeholder(callback: CallbackQuery, callback_data: AdminMenuCallback, ux: UXContext, state: FSMContext):
            # всё остальное, что сейчас плейсхолдер
            await state.clear()
            placeholder_text = await ux.admin.placeholder(callback_data.action)
            keyboard = AdminInlineKeyboards.build_admin_placeholder_keyboard()
            await edit_message(callback, placeholder_text, reply_markup=keyboard)

        # ==========================
        # Список ботов
        # ==========================
        @self.callback_query(AdminBotsListCallback.filter())
        async def handle_bots_list(callback: CallbackQuery, callback_data: AdminBotsListCallback, ux: UXContext):
            action = callback_data.action
            page = callback_data.page or 1

            if action in (AdminBotsListAction.OPEN, AdminBotsListAction.PAGE):
                await self._render_bots_list(callback, ux, page=page)
                return

            if action == AdminBotsListAction.VIEW and callback_data.bot_id:
                bot_uuid = await ux.admin.resolve_bot_uuid(callback_data.bot_id)
                if bot_uuid is None:
                    await callback.answer("Бот не найден", show_alert=True)
                    return
                await self._render_bot_card(callback, ux, bot_uuid, page)
                return

            if action == AdminBotsListAction.BACK:
                menu_view = await ux.admin.show_main_menu()
                keyboard = AdminInlineKeyboards.build_admin_menu_keyboard(menu_view)
                await edit_message(callback, menu_view.text, reply_markup=keyboard)
                return

        # ==========================
        # Действия с ботом
        # ==========================
        @self.callback_query(AdminBotActionCallback.filter())
        async def handle_bot_actions(callback: CallbackQuery, callback_data: AdminBotActionCallback, ux: UXContext):
            action = callback_data.action
            telegram_id = callback_data.bot_id
            if not telegram_id:
                await callback.answer("Бот не найден", show_alert=True)
                return
            bot_uuid = await ux.admin.resolve_bot_uuid(telegram_id)
            if bot_uuid is None:
                await callback.answer("Бот не найден", show_alert=True)
                return
            page = callback_data.page or 1

            if action == AdminBotAction.BACK_TO_LIST:
                await self._render_bots_list(callback, ux, page=page)
                return

            if action == AdminBotAction.FREE_PROMPT:
                prompt = await ux.admin.prepare_free_bot(bot_uuid)
                keyboard = AdminInlineKeyboards.build_admin_bot_free_prompt_keyboard(prompt, page)
                await edit_message(callback, prompt.text, reply_markup=keyboard)
                return

            if action == AdminBotAction.FREE_EXECUTE:
                mode = callback_data.mode
                if mode is None:
                    await callback.answer("Не выбран режим", show_alert=True)
                    return
                if not isinstance(mode, AdminBotFreeMode):
                    mode = AdminBotFreeMode(mode)
                result = await ux.admin.free_bot(bot_uuid, mode)
                await callback.answer(result.text, show_alert=True)
                await self._render_bot_card(callback, ux, bot_uuid, page)
                return

            if action == AdminBotAction.DELETE_PROMPT:
                prompt = await ux.admin.prepare_delete_bot(bot_uuid)
                keyboard = AdminInlineKeyboards.build_admin_bot_delete_prompt_keyboard(prompt, page)
                await edit_message(callback, prompt.text, reply_markup=keyboard)
                return

            if action == AdminBotAction.DELETE_CONFIRM:
                result = await ux.admin.delete_bot(bot_uuid)
                await callback.answer(result.text, show_alert=True)
                await self._render_bots_list(callback, ux, page=page)
                return

            if action == AdminBotAction.REFRESH:
                await self._render_bot_card(callback, ux, bot_uuid, page)
                return

            await callback.answer()

        # ==========================
        # Группы
        # ==========================
        @self.callback_query(AdminGroupsCallback.filter(F.action.in_({AdminGroupsAction.OPEN, AdminGroupsAction.BACK})))
        async def groups_open(callback: CallbackQuery, state: FSMContext, ux: UXContext):
            await state.clear()
            text = ux.admin.groups_menu_text()
            keyboard = AdminInlineKeyboards.build_admin_groups_menu_keyboard()
            await edit_message(callback, text, reply_markup=keyboard)

        @self.callback_query(AdminGroupsCallback.filter(F.action == AdminGroupsAction.ADD))
        async def groups_add(callback: CallbackQuery, state: FSMContext, ux: UXContext):
            await state.set_state(AdminStates.SEND_GROUP_IDS)
            await edit_message(callback, ux.admin.groups_add_prompt())

        @self.callback_query(AdminGroupsCallback.filter(F.action.in_({AdminGroupsAction.LIST, AdminGroupsAction.PAGE})))
        async def groups_list(callback: CallbackQuery, callback_data: AdminGroupsCallback, ux: UXContext):
            page = callback_data.page or 1
            await self._render_groups_list(callback, ux, page=page)

        # карточка группы / обновление / отвязка
        @self.callback_query(AdminGroupsCallback.filter(F.action.in_({
            AdminGroupsAction.VIEW,
            AdminGroupsAction.CARD_REFRESH,
            AdminGroupsAction.CARD_UNBIND,
        })))
        async def groups_card(
            callback: CallbackQuery,
            callback_data: AdminGroupsCallback,
            state: FSMContext,
            ux: UXContext,
            group_service: GroupService,
        ):
            action = callback_data.action
            page = callback_data.page or 1
            if not callback_data.group_id:
                await callback.answer("Группа не найдена", show_alert=True)
                return
            try:
                group_uuid = UUID(callback_data.group_id)
            except ValueError:
                await callback.answer("Группа не найдена", show_alert=True)
                return

            if action == AdminGroupsAction.CARD_UNBIND:
                group = await group_service.get(group_uuid)
                if group is None:
                    await callback.answer("Группа не найдена", show_alert=True)
                    return
                if not group.assigned_bot_id:
                    await callback.answer("Группа уже отвязана", show_alert=True)
                    await self._render_group_card(callback, ux, group_uuid, page)
                    return
                await group_service.unassign_from_bot(
                    bot_id=group.assigned_bot_id,
                    tg_chat_ids=[group.tg_chat_id],
                )
                await callback.answer("Группа отвязана", show_alert=True)
                await self._render_group_card(callback, ux, group_uuid, page)
                return

            await self._render_group_card(callback, ux, group_uuid, page)

        @self.callback_query(AdminGroupsCallback.filter(F.action == AdminGroupsAction.CARD_BACK))
        async def groups_card_back(callback: CallbackQuery, callback_data: AdminGroupsCallback, ux: UXContext):
            page = callback_data.page or 1
            await self._render_groups_list(callback, ux, page=page)

        # ==========================
        # Группы: принятие id от админа
        # ==========================
        @self.message(AdminStates.SEND_GROUP_IDS)
        async def receive_group_ids(message: Message, state: FSMContext, bot_service: BotService, ux: UXContext):
            raw = message.text or ""
            ids: list[int] = []
            for line in raw.replace(',', ' ').split():
                s = line.strip()
                if not s:
                    continue
                try:
                    if s.startswith('-100'):
                        ids.append(int(s))
                    else:
                        if s.startswith('-'):
                            ids.append(int(s))
                        else:
                            ids.append(int("-100" + s))
                except ValueError:
                    continue

            await state.update_data(group_ids=ids)

            bots = await bot_service.list(limit=1000)
            loads = await bot_service.loads_by_bot([b.id for b in bots])
            items: list[tuple[str, str]] = []
            for b in bots:
                current = loads.get(b.id, 0)
                limit = b.max_posts
                label = ux.admin.format_bot_load_label(b, current=current, limit=limit)
                items.append((label, b.telegram_id))

            keyboard = AdminInlineKeyboards.build_admin_groups_choose_bot_keyboard(items)
            await message.answer(ux.admin.groups_choose_bot_prompt(), reply_markup=keyboard)

        # ==========================
        # Группы: привязка к боту
        # ==========================
        @self.callback_query(AdminGroupsBindCallback.filter(F.action == AdminGroupsAction.CHOOSE_BOT))
        async def handle_groups_bind(
            callback: CallbackQuery,
            callback_data: AdminGroupsBindCallback,
            state: FSMContext,
            bot_service: BotService,
            group_service: GroupService,
            ux: UXContext,
        ):
            if not callback_data.bot_id:
                return

            bot_uuid = await ux.admin.resolve_bot_uuid(callback_data.bot_id)
            if bot_uuid is None:
                await callback.answer("Бот не найден", show_alert=True)
                return
            bot_dto = await bot_service.get(bot_uuid)
            if not bot_dto:
                await callback.answer("Бот не найден", show_alert=True)
                return

            data = await state.get_data()
            group_ids: list[int] = data.get('group_ids', [])
            if not group_ids:
                await callback.answer("Список групп пуст", show_alert=True)
                return

            from aiogram import Bot as AioBot
            ok: list[int] = []
            fail: list[int] = []
            test_bot = AioBot(token=bot_dto.token)
            try:
                me = await test_bot.get_me()
                for gid in group_ids:
                    try:
                        member = await test_bot.get_chat_member(gid, me.id)
                        status = getattr(member, 'status', None)
                        logger.info(f'{status=} for bot {me.id} in group {gid}')
                        is_admin = str(status) in ("administrator", "creator")
                        if is_admin:
                            ok.append(gid)
                        else:
                            fail.append(gid)
                    except Exception as e:
                        logger.exception(f"Error checking admin status for bot {me.id} in group {gid}. {type(e).__name__}: {e}")
                        fail.append(gid)
            finally:
                await test_bot.session.close()

            assign_result = None
            if ok:
                assign_result = await group_service.assign_to_bot(bot_id=bot_uuid, tg_chat_ids=ok)

            previous_map: dict[UUID, BotDTO | None] = {}
            if assign_result and assign_result.reassigned:
                previous_ids = {item.previous_bot_id for item in assign_result.reassigned}
                previous_map = await self._load_bots(bot_service, previous_ids)
            text = ux.admin.format_group_bind_result(
                assign_result=assign_result,
                fail=fail,
                previous_map=previous_map,
            )

            await state.clear()
            keyboard = AdminInlineKeyboards.build_admin_groups_menu_keyboard()
            await edit_message(callback, text, reply_markup=keyboard)

        # ==========================
        # РАССЫЛКИ (разнесено)
        # ==========================

        # назад в главное меню
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.BACK))
        async def dist_back(callback: CallbackQuery, state: FSMContext, ux: UXContext):
            await state.clear()
            menu_view = await ux.admin.show_main_menu()
            keyboard = AdminInlineKeyboards.build_admin_menu_keyboard(menu_view)
            await edit_message(callback, menu_view.text, reply_markup=keyboard)

        # открыть меню рассылок
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.OPEN))
        async def dist_open(callback: CallbackQuery, ux: UXContext, state: FSMContext):
            await state.clear()
            await self._render_distributions_menu(callback, ux)

        # список рассылок (все варианты страниц)
        @self.callback_query(AdminDistributionsCallback.filter(F.action.in_({
            AdminDistributionsAction.LIST,
            AdminDistributionsAction.LIST_PAGE,
            AdminDistributionsAction.LIST_BACK,
        })))
        async def dist_list(callback: CallbackQuery, callback_data: AdminDistributionsCallback, ux: UXContext):
            page = callback_data.page or 1
            await self._render_distributions_list(callback, ux, page=page)

        # просмотр карточки рассылки
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.LIST_VIEW))
        async def dist_view(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id: UUID | None = None
            if callback_data.distribution_id:
                dist_id = self._decode_distribution_id(callback_data.distribution_id)
            elif callback_data.post_id:
                post_id = self._decode_post_id(callback_data.post_id)
                if post_id is None:
                    await callback.answer("Рассылка не найдена", show_alert=True)
                    return
                dist_id = await post_service.resolve_distribution_id_by_post(post_id)
            else:
                return

            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            page = callback_data.page or 1
            await self._render_distribution_card(callback, ux, dist_id, page=page)

        # обновить карточку рассылки
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.LIST_REFRESH))
        async def dist_refresh_card(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id: UUID | None = None
            if callback_data.distribution_id:
                dist_id = self._decode_distribution_id(callback_data.distribution_id)
            elif callback_data.post_id:
                post_id = self._decode_post_id(callback_data.post_id)
                if post_id is None:
                    await callback.answer("Рассылка не найдена", show_alert=True)
                    return
                dist_id = await post_service.resolve_distribution_id_by_post(post_id)
            else:
                return

            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            page = callback_data.page or 1
            await self._render_distribution_card(callback, ux, dist_id, page=page)
        
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.TOGGLE_STATUS))
        async def dist_start_all_postings(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            ux: UXContext,
            post_service: PostService,
        ):
            if not callback_data.distribution_id:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            dist_id = self._decode_distribution_id(callback_data.distribution_id)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            choice = (callback_data.choice or "").lower()
            if choice not in {"pause", "resume"}:
                await callback.answer("Неизвестное действие", show_alert=True)
                return

            summary = await post_service.get_distribution_summary(dist_id)
            if summary is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            source_message_id = summary.get("source_message_id")
            if source_message_id is None:
                await callback.answer("Не удалось определить рассылку", show_alert=True)
                return

            try:
                normalized_message_id = int(source_message_id)
            except (TypeError, ValueError):
                await callback.answer("Не удалось определить рассылку", show_alert=True)
                return

            source_channel_id = summary.get("source_channel_id")
            try:
                normalized_channel_id = int(source_channel_id) if source_channel_id is not None else None
            except (TypeError, ValueError):
                normalized_channel_id = None

            source_username = summary.get("source_channel_username")

            if choice == "pause":
                affected = await post_service.bulk_pause_distribution(
                    source_channel_username=source_username,
                    source_channel_id=normalized_channel_id,
                    source_message_id=normalized_message_id,
                )
                feedback = "Нет активных рассылок для остановки" if affected == 0 else f"Остановлено {affected} пост(ов)"
            else:
                affected = await post_service.bulk_resume_distribution(
                    source_channel_username=source_username,
                    source_channel_id=normalized_channel_id,
                    source_message_id=normalized_message_id,
                )
                feedback = "Нет рассылок для запуска" if affected == 0 else f"Запущено {affected} пост(ов)"

            await callback.answer(feedback, show_alert=True)
            page = callback_data.page or 1
            await self._render_distribution_card(callback, ux, dist_id, page=page)

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.TOGGLE_NOTIFY))
        async def dist_toggle_notify(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            ux: UXContext,
            post_service: PostService,
        ):
            if not callback_data.distribution_id:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            dist_id = self._decode_distribution_id(callback_data.distribution_id)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            choice = (callback_data.choice or "").lower()
            if choice not in {"on", "off"}:
                await callback.answer("Неизвестное действие", show_alert=True)
                return

            summary = await post_service.get_distribution_summary(dist_id)
            if summary is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            source_message_id = summary.get("source_message_id")
            if source_message_id is None:
                await callback.answer("Не удалось определить рассылку", show_alert=True)
                return

            try:
                normalized_message_id = int(source_message_id)
            except (TypeError, ValueError):
                await callback.answer("Не удалось определить рассылку", show_alert=True)
                return

            source_channel_id = summary.get("source_channel_id")
            try:
                normalized_channel_id = int(source_channel_id) if source_channel_id is not None else None
            except (TypeError, ValueError):
                normalized_channel_id = None

            source_username = summary.get("source_channel_username")
            value = choice == "on"
            affected = await post_service.bulk_set_notify_distribution(
                source_channel_username=source_username,
                source_channel_id=normalized_channel_id,
                source_message_id=normalized_message_id,
                value=value,
            )

            feedback = (
                "Уведомления включены" if value else "Уведомления отключены"
            )
            if affected == 0:
                feedback = "Рассылок для обновления не найдено"

            await callback.answer(feedback, show_alert=True)
            page = callback_data.page or 1
            await self._render_distribution_card(callback, ux, dist_id, page=page)

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.DELETE))
        async def dist_delete(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            ux: UXContext,
            post_service: PostService,
        ):
            if not callback_data.distribution_id:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            dist_id = self._decode_distribution_id(callback_data.distribution_id)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            summary = await post_service.get_distribution_summary(dist_id)
            if summary is None:
                await callback.answer(ux.admin.distribution_delete_missing_text(), show_alert=True)
                page = callback_data.page or 1
                await self._render_distributions_list(callback, ux, page=page)
                return

            distribution_name = summary.get("distribution_name")
            deleted = await post_service.delete_distribution(
                distribution_name=distribution_name,
            )

            if deleted == 0:
                feedback = ux.admin.distribution_delete_missing_text()
            else:
                feedback = ux.admin.distribution_deleted_alert_text(summary.get("distribution_name"), deleted)

            await callback.answer(feedback, show_alert=True)
            page = callback_data.page or 1
            await self._render_distributions_list(callback, ux, page=page)

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.SHOW_GROUPS))
        async def dist_show_list_groups(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id: UUID | None = None
            if callback_data.distribution_id:
                dist_id = self._decode_distribution_id(callback_data.distribution_id)
            elif callback_data.post_id:
                post_id = self._decode_post_id(callback_data.post_id)
                if post_id is None:
                    await callback.answer("Рассылка не найдена", show_alert=True)
                    return
                dist_id = await post_service.resolve_distribution_id_by_post(post_id)
            else:
                return

            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            page = callback_data.page or 1
            card_page = callback_data.card_page or 1

            await self._render_distribution_groups_list(
                callback,
                ux,
                dist_id,
                page=page,
                card_page=card_page,
            )

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_PAGE))
        async def dist_groups_paginate(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id: UUID | None = None
            if callback_data.distribution_id:
                dist_id = self._decode_distribution_id(callback_data.distribution_id)
            elif callback_data.post_id:
                post_id = self._decode_post_id(callback_data.post_id)
                if post_id is None:
                    await callback.answer("Рассылка не найдена", show_alert=True)
                    return
                dist_id = await post_service.resolve_distribution_id_by_post(post_id)
            else:
                return

            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            page = callback_data.page or 1
            card_page = callback_data.card_page or 1
            await self._render_distribution_groups_list(
                callback,
                ux,
                dist_id,
                page=page,
                card_page=card_page,
            )

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUP_VIEW))
        async def dist_show_group_card(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            ux: UXContext,
            post_service: PostService,
        ):
            if not callback_data.post_id:
                return

            post_id = self._decode_post_id(callback_data.post_id)
            if post_id is None:
                await callback.answer("Группа не найдена", show_alert=True)
                return

            if callback_data.distribution_id:
                dist_id = self._decode_distribution_id(callback_data.distribution_id)
            else:
                dist_id = await post_service.resolve_distribution_id_by_post(post_id)

            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return

            groups_page = callback_data.page or 1
            card_page = callback_data.card_page or 1

            try:
                card = await ux.admin.show_distribution_group_card(dist_id, post_id)
            except ValueError as exc:
                logger.error(f"Error rendering distribution group card: {exc}")
                await callback.answer("Данные не найдены", show_alert=True)
                return

            keyboard = AdminInlineKeyboards.build_admin_distribution_group_card_keyboard(
                card,
                distribution_id=dist_id,
                groups_page=groups_page,
                card_page=card_page,
            )
            await edit_message(callback, card.text, reply_markup=keyboard)

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_ADD))
        async def dist_groups_add_menu(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            groups_page = callback_data.page or 1
            card_page = callback_data.card_page or 1
            await state.update_data(
                dist_edit_distribution=str(dist_id),
                dist_edit_groups_page=groups_page,
                dist_edit_card_page=card_page,
                dist_edit_bindings_selected=[],
            )
            keyboard = AdminInlineKeyboards.build_admin_distribution_groups_add_method_keyboard(
                distribution_id=dist_id,
                groups_page=groups_page,
                card_page=card_page,
            )
            await edit_message(callback, ux.admin.distribution_groups_add_intro_text(), reply_markup=keyboard)

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_ADD_MANUAL))
        async def dist_groups_add_manual(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            groups_page = callback_data.page or 1
            card_page = callback_data.card_page or 1
            await state.clear()
            await state.update_data(
                dist_edit_distribution=str(dist_id),
                dist_edit_groups_page=groups_page,
                dist_edit_card_page=card_page,
            )
            await state.set_state(AdminStates.DISTRIBUTION_EDIT_WAIT_GROUP_IDS)
            keyboard = AdminInlineKeyboards.build_admin_distribution_groups_add_manual_keyboard(
                distribution_id=dist_id,
                groups_page=groups_page,
                card_page=card_page,
            )
            await edit_message(callback, ux.admin.distribution_groups_add_manual_prompt_text(), reply_markup=keyboard)

        @self.callback_query(
            AdminDistributionsCallback.filter(
                F.action.in_({
                    AdminDistributionsAction.GROUPS_ADD_BINDINGS,
                    AdminDistributionsAction.GROUPS_ADD_BINDINGS_PAGE,
                })
            )
        )
        async def dist_groups_add_bindings(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            group_service: GroupService,
            bot_service: BotService,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                dist_id = await self._get_distribution_id_from_state(state)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            desired_page = callback_data.page or 1
            await self._prepare_bindings_pool(state, dist_id, group_service, bot_service, post_service, ux)
            await self._render_bindings_selection(
                callback,
                ux,
                state,
                distribution_id=dist_id,
                page=desired_page,
            )

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_ADD_TOGGLE))
        async def dist_groups_add_toggle(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                dist_id = await self._get_distribution_id_from_state(state)
            if dist_id is None or not callback_data.group_id:
                await callback.answer("Группа не найдена", show_alert=True)
                return
            group_uuid = self._decode_group_id(callback_data.group_id)
            if group_uuid is None:
                await callback.answer("Группа не найдена", show_alert=True)
                return
            data = await state.get_data()
            selected: set[str] = set(data.get("dist_edit_bindings_selected", []))
            key = str(group_uuid)
            if key in selected:
                selected.remove(key)
            else:
                selected.add(key)
            await state.update_data(dist_edit_bindings_selected=list(selected))
            page = callback_data.page or data.get("dist_edit_bindings_page", 1) or 1
            await self._render_bindings_selection(
                callback,
                ux,
                state,
                distribution_id=dist_id,
                page=page,
            )

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_ADD_APPLY))
        async def dist_groups_add_apply(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            group_service: GroupService,
            bot_service: BotService,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                dist_id = await self._get_distribution_id_from_state(state)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            data = await state.get_data()
            selected_ids: list[str] = data.get("dist_edit_bindings_selected", [])
            if not selected_ids:
                await callback.answer(ux.admin.distribution_groups_add_nothing_text(), show_alert=True)
                return
            groups: list[GroupDTO] = []
            for raw_id in selected_ids:
                try:
                    group_uuid = UUID(raw_id)
                except ValueError:
                    continue
                group = await group_service.get(group_uuid)
                if not group:
                    continue
                group = await group_service.ensure_metadata(group, bot_service)
                groups.append(group)
            if not groups:
                await callback.answer(ux.admin.distribution_groups_add_not_found_text(), show_alert=True)
                return
            context = await post_service.get_distribution_context(dist_id)
            if context is None:
                await callback.answer("Не удалось получить параметры рассылки", show_alert=True)
                return
            usage_map = await post_service.groups_distribution_usage([group.id for group in groups])
            cleanup_ids = [
                group_id
                for group_id, linked_dist in usage_map.items()
                if linked_dist and linked_dist != dist_id
            ]
            existing_ids = set(data.get("dist_edit_current_groups", []))
            filtered_groups = [group for group in groups if str(group.id) not in existing_ids]
            if not filtered_groups:
                await callback.answer(ux.admin.distribution_groups_add_nothing_text(), show_alert=True)
                return
            created, skipped_chat_ids = await post_service.add_groups_to_distribution(
                context=context,
                groups=filtered_groups,
                cleanup_group_ids=cleanup_ids,
            )
            skipped_total = len(skipped_chat_ids)
            await state.update_data(
                dist_edit_bindings_selected=[],
                dist_edit_bindings_items=[],
            )
            await callback.answer(ux.admin.distribution_groups_add_result_text(created=created, skipped=skipped_total), show_alert=True)
            groups_page = data.get("dist_edit_groups_page", 1) or 1
            card_page = data.get("dist_edit_card_page", 1) or 1
            await self._render_distribution_groups_list(
                callback,
                ux,
                dist_id,
                page=groups_page,
                card_page=card_page,
            )

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_ADD_CANCEL))
        async def dist_groups_add_cancel(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                dist_id = await self._get_distribution_id_from_state(state)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            data = await state.get_data()
            groups_page = data.get("dist_edit_groups_page", callback_data.page or 1) or 1
            card_page = data.get("dist_edit_card_page", callback_data.card_page or 1) or 1
            await state.update_data(
                dist_edit_bindings_selected=[],
                dist_edit_bindings_items=[],
            )
            await self._render_distribution_groups_list(
                callback,
                ux,
                dist_id,
                page=groups_page,
                card_page=card_page,
            )

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_DELETE))
        async def dist_groups_delete_mode(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                dist_id = await self._get_distribution_id_from_state(state)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            groups_page = callback_data.page or 1
            card_page = callback_data.card_page or 1
            await state.set_state(AdminStates.DISTRIBUTION_EDIT_DELETE_MODE)
            await state.update_data(
                dist_edit_distribution=str(dist_id),
                dist_edit_groups_page=groups_page,
                dist_edit_card_page=card_page,
                dist_delete_selection=[],
            )
            await self._render_distribution_delete_mode(
                callback,
                ux,
                dist_id,
                page=groups_page,
                card_page=card_page,
                state=state,
            )

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_DELETE_PAGE))
        async def dist_groups_delete_page(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                dist_id = await self._get_distribution_id_from_state(state)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            data = await state.get_data()
            card_page = data.get("dist_edit_card_page", callback_data.card_page or 1) or 1
            page = callback_data.page or data.get("dist_edit_groups_page", 1) or 1
            await self._render_distribution_delete_mode(
                callback,
                ux,
                dist_id,
                page=page,
                card_page=card_page,
                state=state,
            )

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_DELETE_TOGGLE))
        async def dist_groups_delete_toggle(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                dist_id = await self._get_distribution_id_from_state(state)
            if dist_id is None or not callback_data.group_id:
                await callback.answer("Группа не найдена", show_alert=True)
                return
            group_uuid = self._decode_group_id(callback_data.group_id)
            if group_uuid is None:
                await callback.answer("Группа не найдена", show_alert=True)
                return
            data = await state.get_data()
            selection: set[str] = set(data.get("dist_delete_selection", []))
            key = str(group_uuid)
            if key in selection:
                selection.remove(key)
            else:
                selection.add(key)
            await state.update_data(dist_delete_selection=list(selection))
            page = callback_data.page or data.get("dist_edit_groups_page", 1) or 1
            card_page = data.get("dist_edit_card_page", callback_data.card_page or 1) or 1
            await self._render_distribution_delete_mode(
                callback,
                ux,
                dist_id,
                page=page,
                card_page=card_page,
                state=state,
            )

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_DELETE_CANCEL))
        async def dist_groups_delete_cancel(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                dist_id = await self._get_distribution_id_from_state(state)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            await state.clear()
            page = callback_data.page or 1
            card_page = callback_data.card_page or 1
            await self._render_distribution_groups_list(
                callback,
                ux,
                dist_id,
                page=page,
                card_page=card_page,
            )

        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.GROUPS_DELETE_CONFIRM))
        async def dist_groups_delete_confirm(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            post_service: PostService,
        ):
            dist_id = await self._resolve_distribution_id_from_callback(callback_data, post_service)
            if dist_id is None:
                await callback.answer("Рассылка не найдена", show_alert=True)
                return
            data = await state.get_data()
            selection: list[str] = data.get("dist_delete_selection", [])
            if not selection:
                await callback.answer(ux.admin.distribution_groups_delete_none_text(), show_alert=True)
                return
            page = callback_data.page or data.get("dist_edit_groups_page", 1) or 1
            card_page = callback_data.card_page or data.get("dist_edit_card_page", 1) or 1
            choice = (callback_data.choice or "").lower()
            if choice == "yes":
                group_ids: list[UUID] = []
                for raw_id in selection:
                    try:
                        group_ids.append(UUID(raw_id))
                    except ValueError:
                        continue
                deleted = await post_service.delete_distribution_groups(dist_id, group_ids)
                await callback.answer(ux.admin.distribution_groups_delete_done_text(deleted), show_alert=True)
                await state.clear()
                await self._render_distribution_groups_list(
                    callback,
                    ux,
                    dist_id,
                    page=page,
                    card_page=card_page,
                )
                return
            if choice == "no":
                await self._render_distribution_delete_mode(
                    callback,
                    ux,
                    dist_id,
                    page=page,
                    card_page=card_page,
                    state=state,
                )
                return
            confirm_text = ux.admin.distribution_groups_delete_confirm_text(len(selection))
            keyboard = AdminInlineKeyboards.build_admin_distribution_groups_delete_confirm_keyboard(
                distribution_id=dist_id,
                page=page,
                card_page=card_page,
            )
            await edit_message(callback, confirm_text, reply_markup=keyboard)

        # отмена создания
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.CANCEL))
        async def dist_cancel(callback: CallbackQuery, state: FSMContext, ux: UXContext):
            await state.clear()
            text = ux.admin.distribution_cancelled_text()
            keyboard = AdminInlineKeyboards.build_admin_distributions_menu_keyboard()
            await edit_message(callback, text, reply_markup=keyboard)

        # старт создания
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.START_CREATE))
        async def dist_start_create(callback: CallbackQuery, state: FSMContext, ux: UXContext):
            await state.clear()
            await state.set_state(AdminStates.DISTRIBUTION_WAIT_NAME)
            await state.update_data(
                dist_name=None,
                dist_mode="replace",
                dist_target=None,
                dist_groups=[],
                dist_selected_bots=[],
                dist_bot_list=[],
                dist_bot_page=1,
                dist_summary_prefix="",
                dist_pause_between_attempts_s=60,
                dist_delete_last_attempt=False,
                dist_pin_after_post=False,
                dist_num_attempt_for_pin_post=None,
                dist_target_attempts=1,
                dist_notify_on_failure=True,
            )
            await self._prompt_distribution_name(callback, ux)

        # автоимя
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.NAME_AUTO))
        async def dist_name_auto(callback: CallbackQuery, state: FSMContext, ux: UXContext):
            auto_name = self._generate_distribution_name()
            await state.update_data(dist_name=auto_name, dist_mode="replace")
            await self._render_distribution_target(callback, ux, mode="replace", name=auto_name)
            await callback.answer(ux.admin.distribution_name_autoset_text(auto_name), show_alert=False)

        # выбор режима create / replace
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.SET_MODE))
        async def dist_set_mode(callback: CallbackQuery, callback_data: AdminDistributionsCallback, state: FSMContext, ux: UXContext):
            if not callback_data.mode:
                return
            if callback_data.mode not in {"create", "replace"}:
                return
            data = await state.get_data()
            name = data.get("dist_name")
            await state.update_data(dist_mode=callback_data.mode)
            await self._render_distribution_target(callback, ux, mode=callback_data.mode, name=name)

        # открыть выбор цели (all/groups/bots)
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.SELECT_TARGET))
        async def dist_select_target(callback: CallbackQuery, state: FSMContext, ux: UXContext):
            data = await state.get_data()
            mode = "replace"
            await state.update_data(dist_mode="replace", dist_summary_prefix="")
            await self._render_distribution_target(callback, ux, mode=mode, name=data.get("dist_name"))

        # установка цели
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.SET_TARGET))
        async def dist_set_target(
            callback: CallbackQuery,
            callback_data: AdminDistributionsCallback,
            state: FSMContext,
            ux: UXContext,
            bot_service: BotService,
            group_service: GroupService,
        ):
            if not callback_data.target:
                return
            target = callback_data.target
            data = await state.get_data()
            mode = "replace"
            await state.update_data(dist_target=target, dist_groups=[], dist_mode="replace")

            # 1) выбор групп вручную
            if target == "groups":
                await state.set_state(AdminStates.DISTRIBUTION_WAIT_GROUP_IDS)
                await self._prompt_distribution_groups_input(callback, ux)
                return

            # 2) выбор ботов -> из них получаем группы
            if target == "bots":
                bots = await bot_service.list(limit=1000)
                bot_entries = [
                    {
                        "id": bot.telegram_id,
                        "uuid": str(bot.id),
                        "label": ux.admin.format_bot_label(bot),
                    }
                    for bot in bots
                ]
                await state.set_state(AdminStates.DISTRIBUTION_SELECT_BOTS)
                await state.update_data(
                    dist_bot_list=bot_entries,
                    dist_selected_bots=[],
                    dist_bot_page=callback_data.page or 1,
                )
                await self._render_distribution_bot_select(callback, ux, state, page=callback_data.page or 1)
                return

            # 3) all -> собираем все привязанные группы
            if target == "all":
                groups = await group_service.list_bound(limit=2000)
                groups = await group_service.ensure_metadata_bulk(groups, bot_service)
                if not groups:
                    await callback.answer(ux.admin.distribution_error_no_groups_text(), show_alert=True)
                    return
                packed = [self._pack_group_dto(g) for g in groups]
                summary = ux.admin.distribution_all_groups_selected_text(len(packed))
                await state.update_data(
                    dist_groups=packed,
                    dist_summary_prefix=summary,
                )
                await state.set_state(AdminStates.DISTRIBUTION_WAIT_PAUSE)
                await self._prompt_distribution_pause(callback, ux, summary)
                return

        # установить "удалять предыдущее"
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.SET_DELETE_LAST))
        async def dist_set_delete_last(callback: CallbackQuery, callback_data: AdminDistributionsCallback, state: FSMContext, ux: UXContext):
            choice = (callback_data.choice or "").lower()
            if choice not in {"yes", "no"}:
                await callback.answer(ux.admin.distribution_bool_invalid_text(), show_alert=True)
                return
            await state.update_data(dist_delete_last_attempt=choice == "yes")
            await state.set_state(AdminStates.DISTRIBUTION_WAIT_PIN)
            await self._prompt_distribution_pin(callback, ux)
            await callback.answer()

        # установить "закреплять"
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.SET_PIN))
        async def dist_set_pin(callback: CallbackQuery, callback_data: AdminDistributionsCallback, state: FSMContext, ux: UXContext):
            choice = (callback_data.choice or "").lower()
            if choice not in {"yes", "no"}:
                await callback.answer(ux.admin.distribution_bool_invalid_text(), show_alert=True)
                return
            await state.update_data(dist_pin_after_post=choice == "yes")
            if choice == "yes":
                await state.set_state(AdminStates.DISTRIBUTION_WAIT_PIN_FREQUENCY)
                await self._prompt_distribution_pin_frequency(callback, ux)
            else:
                await state.update_data(dist_num_attempt_for_pin_post=None)
                await state.set_state(AdminStates.DISTRIBUTION_WAIT_TARGET_ATTEMPTS)
                await self._prompt_distribution_target_attempts(callback, ux)
            await callback.answer()

        # выбор бота из списка при target == bots
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.SELECT_BOT))
        async def dist_select_bot(callback: CallbackQuery, callback_data: AdminDistributionsCallback, state: FSMContext, ux: UXContext, group_service: GroupService):
            data = await state.get_data()
            bot_list: list[dict] = data.get("dist_bot_list", [])
            if not bot_list:
                await callback.answer()
                return
            selected: set[str] = set(data.get("dist_selected_bots", []))
            bot_id = callback_data.bot_id or ''
            if bot_id in selected:
                selected.remove(bot_id)
            else:
                selected.add(bot_id)
            await state.update_data(dist_selected_bots=list(selected))
            page = callback_data.page or data.get("dist_bot_page", 1) or 1
            await self._render_distribution_bot_select(callback, ux, state, page=page)

        # пагинация по ботам при выборе цели "bots"
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.BOT_PAGE))
        async def dist_bot_page(callback: CallbackQuery, callback_data: AdminDistributionsCallback, state: FSMContext, ux: UXContext):
            data = await state.get_data()
            page = callback_data.page or data.get("dist_bot_page", 1) or 1
            await self._render_distribution_bot_select(callback, ux, state, page=page)

        # завершить выбор ботов -> получить группы по этим ботам
        @self.callback_query(AdminDistributionsCallback.filter(F.action == AdminDistributionsAction.FINISH_BOT_SELECTION))
        async def dist_finish_bot_selection(
            callback: CallbackQuery,
            state: FSMContext,
            ux: UXContext,
            group_service: GroupService,
            bot_service: BotService,
        ):
            data = await state.get_data()
            selected_ids: list[str] = data.get("dist_selected_bots", [])
            bot_list: list[dict] = data.get("dist_bot_list", [])
            if not selected_ids:
                await callback.answer(ux.admin.distribution_bot_selection_empty_text(), show_alert=True)
                return
            groups_map: dict[str, dict] = {}
            uuid_lookup = {
                entry["id"]: entry.get("uuid") or entry.get("id")
                for entry in bot_list
                if entry.get("id")
            }
            resolved_cache: dict[str, UUID] = {}
            for bot_key in selected_ids:
                if bot_key in resolved_cache:
                    bot_uuid = resolved_cache[bot_key]
                else:
                    bot_uuid: UUID | None = None
                    for candidate in (uuid_lookup.get(bot_key), bot_key):
                        if not candidate:
                            continue
                        try:
                            bot_uuid = UUID(candidate)
                            break
                        except ValueError:
                            continue
                    if bot_uuid is None:
                        bot = await bot_service.get_by_telegram_id(bot_key)
                        if bot:
                            bot_uuid = bot.id
                    if bot_uuid is None:
                        continue
                    resolved_cache[bot_key] = bot_uuid
                bot_groups = await group_service.list_by_bot(bot_uuid, limit=1000)
                bot_groups = await group_service.ensure_metadata_bulk(bot_groups, bot_service)
                for group in bot_groups:
                    groups_map[str(group.id)] = self._pack_group_dto(group)
            if not groups_map:
                await callback.answer(ux.admin.distribution_bot_selection_no_groups_text(), show_alert=True)
                return
            packed = list(groups_map.values())
            info = ux.admin.distribution_groups_resolved_text(len(packed))
            await state.update_data(dist_groups=packed, dist_summary_prefix=info)
            await state.set_state(AdminStates.DISTRIBUTION_WAIT_PAUSE)
            await self._prompt_distribution_pause(callback, ux, info)

        # ==========================
        # Сообщения, которые продолжают создание рассылки
        # ==========================
        @self.message(AdminStates.DISTRIBUTION_EDIT_WAIT_GROUP_IDS)
        async def distribution_edit_receive_group_ids(
            message: Message,
            state: FSMContext,
            group_service: GroupService,
            bot_service: BotService,
            post_service: PostService,
            ux: UXContext,
        ):
            data = await state.get_data()
            dist_raw = data.get("dist_edit_distribution")
            if not dist_raw:
                await message.answer("Рассылка не выбрана")
                await state.clear()
                return
            try:
                dist_id = UUID(dist_raw)
            except ValueError:
                await message.answer("Рассылка не найдена")
                await state.clear()
                return
            groups_page = data.get("dist_edit_groups_page", 1) or 1
            card_page = data.get("dist_edit_card_page", 1) or 1
            text = message.text or ""
            chat_ids: list[int] = []
            for token in text.replace(',', ' ').split():
                token = token.strip()
                if not token:
                    continue
                try:
                    if token.startswith('-100') or token.startswith('-'):
                        chat_ids.append(int(token))
                    else:
                        chat_ids.append(int("-100" + token))
                except ValueError:
                    continue
            if not chat_ids:
                await message.answer(ux.admin.distribution_groups_add_not_found_text())
                return
            unique_ids = list(dict.fromkeys(chat_ids))
            groups: list[GroupDTO] = []
            for chat_id in unique_ids:
                group = await group_service.get_by_tg_chat_id(chat_id)
                if not group:
                    continue
                group = await group_service.ensure_metadata(group, bot_service)
                groups.append(group)
            if not groups:
                await message.answer(ux.admin.distribution_groups_add_not_found_text())
                return
            context = await post_service.get_distribution_context(dist_id)
            if context is None:
                await message.answer("Не удалось получить параметры рассылки")
                await state.clear()
                return
            summary = await post_service.get_distribution_summary(dist_id)
            if summary is None or summary.get("source_message_id") is None:
                await message.answer("Рассылка не найдена")
                await state.clear()
                return
            posts = await post_service.list_distribution_posts(
                source_channel_username=summary.get("source_channel_username"),
                source_channel_id=summary.get("source_channel_id"),
                source_message_id=summary.get("source_message_id"),
            )
            existing_ids = {str(post.group_id) for post in posts if post.group_id}
            usage_map = await post_service.groups_distribution_usage([group.id for group in groups])
            cleanup_ids = [
                group_id
                for group_id, linked_dist in usage_map.items()
                if linked_dist and linked_dist != dist_id
            ]
            filtered_groups = [group for group in groups if str(group.id) not in existing_ids]
            if not filtered_groups:
                await message.answer(ux.admin.distribution_groups_add_nothing_text())
                return
            created, skipped_chat_ids = await post_service.add_groups_to_distribution(
                context=context,
                groups=filtered_groups,
                cleanup_group_ids=cleanup_ids,
            )
            await state.clear()
            summary_text = ux.admin.distribution_groups_add_result_text(
                created=created,
                skipped=len(skipped_chat_ids),
            )
            await message.answer(summary_text)
            await self._render_distribution_groups_list(
                message,
                ux,
                dist_id,
                page=groups_page,
                card_page=card_page,
            )

        @self.message(AdminStates.DISTRIBUTION_WAIT_NAME)
        async def distribution_receive_name(message: Message, state: FSMContext, ux: UXContext):
            name = (message.text or "").strip()
            if not name:
                await message.answer(ux.admin.distribution_name_invalid_text())
                return
            await state.update_data(dist_name=name, dist_mode="replace")
            await self._render_distribution_target(message, ux, mode="replace", name=name)

        @self.message(AdminStates.DISTRIBUTION_WAIT_GROUP_IDS)
        async def distribution_receive_group_ids(
            message: Message,
            state: FSMContext,
            group_service: GroupService,
            bot_service: BotService,
            ux: UXContext,
        ):
            text = message.text or ""
            chat_ids: list[int] = []
            for token in text.replace(',', ' ').split():
                token = token.strip()
                if not token:
                    continue
                try:
                    if token.startswith('-100'):
                        chat_ids.append(int(token))
                    elif token.startswith('-'):
                        chat_ids.append(int(token))
                    else:
                        chat_ids.append(int("-100" + token))
                except ValueError:
                    continue
            if not chat_ids:
                await message.answer(ux.admin.distribution_groups_not_found_text())
                return
            unique_ids = list(dict.fromkeys(chat_ids))
            groups: list[dict] = []
            missing: list[int] = []
            for chat_id in unique_ids:
                group = await group_service.get_by_tg_chat_id(chat_id)
                if not group:
                    missing.append(chat_id)
                    continue
                group = await group_service.ensure_metadata(group, bot_service)
                groups.append(self._pack_group_dto(group))
            if not groups:
                await message.answer(ux.admin.distribution_groups_not_found_text())
                return
            await state.update_data(dist_groups=groups, dist_target="groups")
            summary = ux.admin.distribution_groups_resolved_text(len(groups))
            if missing:
                summary += "\n" + ux.admin.distribution_groups_missing_text(missing)
            await state.update_data(dist_summary_prefix=summary)
            await state.set_state(AdminStates.DISTRIBUTION_WAIT_PAUSE)
            await self._prompt_distribution_pause(message, ux, summary)

        @self.message(AdminStates.DISTRIBUTION_WAIT_PAUSE)
        async def distribution_receive_pause(message: Message, state: FSMContext, ux: UXContext):
            text = (message.text or "").strip()
            if not text:
                pause = 60
            else:
                try:
                    pause = int(text)
                except ValueError:
                    await message.answer(ux.admin.distribution_pause_invalid_text())
                    return
                if pause < 0:
                    await message.answer(ux.admin.distribution_pause_invalid_text())
                    return
            await state.update_data(dist_pause_between_attempts_s=pause)
            await state.set_state(AdminStates.DISTRIBUTION_WAIT_DELETE_LAST)
            await self._prompt_distribution_delete_last(message, ux)

        @self.message(AdminStates.DISTRIBUTION_WAIT_DELETE_LAST)
        async def distribution_receive_delete_last(message: Message, state: FSMContext, ux: UXContext):
            choice = self._parse_bool(message.text, default=False)
            if choice is None:
                await message.answer(ux.admin.distribution_bool_invalid_text())
                return
            await state.update_data(dist_delete_last_attempt=choice)
            await state.set_state(AdminStates.DISTRIBUTION_WAIT_PIN)
            await self._prompt_distribution_pin(message, ux)

        @self.message(AdminStates.DISTRIBUTION_WAIT_PIN)
        async def distribution_receive_pin(message: Message, state: FSMContext, ux: UXContext):
            choice = self._parse_bool(message.text, default=False)
            if choice is None:
                await message.answer(ux.admin.distribution_bool_invalid_text())
                return
            await state.update_data(dist_pin_after_post=choice)
            if not choice:
                await state.update_data(dist_num_attempt_for_pin_post=None)
                await state.set_state(AdminStates.DISTRIBUTION_WAIT_TARGET_ATTEMPTS)
                await self._prompt_distribution_target_attempts(message, ux)
                return
            await state.set_state(AdminStates.DISTRIBUTION_WAIT_PIN_FREQUENCY)
            await self._prompt_distribution_pin_frequency(message, ux)

        @self.message(AdminStates.DISTRIBUTION_WAIT_PIN_FREQUENCY)
        async def distribution_receive_pin_frequency(message: Message, state: FSMContext, ux: UXContext):
            text = (message.text or "").strip()
            if not text:
                frequency: int | None = None
            else:
                try:
                    value = int(text)
                except ValueError:
                    await message.answer(ux.admin.distribution_pin_frequency_invalid_text())
                    return
                if value < 0:
                    await message.answer(ux.admin.distribution_pin_frequency_invalid_text())
                    return
                frequency = value
            normalized_frequency = None if frequency is None or frequency == 0 else frequency
            await state.update_data(dist_num_attempt_for_pin_post=normalized_frequency)
            await state.set_state(AdminStates.DISTRIBUTION_WAIT_TARGET_ATTEMPTS)
            await self._prompt_distribution_target_attempts(message, ux)

        @self.message(AdminStates.DISTRIBUTION_WAIT_TARGET_ATTEMPTS)
        async def distribution_receive_target_attempts(message: Message, state: FSMContext, ux: UXContext):
            text = (message.text or "").strip()
            if not text:
                attempts = 1
            else:
                try:
                    attempts = int(text)
                except ValueError:
                    await message.answer(ux.admin.distribution_target_attempts_invalid_text())
                    return
                if attempts == 0 or attempts < -1:
                    await message.answer(ux.admin.distribution_target_attempts_invalid_text())
                    return
            await state.update_data(dist_target_attempts=attempts)
            data = await state.get_data()
            summary_prefix = data.get("dist_summary_prefix", "")
            name_line = ux.admin.distribution_name_selected_text(data.get("dist_name"))
            config_summary = self._compose_distribution_config_summary(data)
            combined_summary = "\n".join(filter(None, [name_line, summary_prefix, config_summary]))
            await state.update_data(dist_summary_prefix=summary_prefix)
            await state.set_state(AdminStates.DISTRIBUTION_WAIT_SOURCE)
            await self._prompt_distribution_source(message, ux, combined_summary)

        @self.message(AdminStates.DISTRIBUTION_WAIT_SOURCE)
        async def distribution_receive_source(
            message: Message,
            state: FSMContext,
            post_service: PostService,
            ux: UXContext,
        ):
            parsed = self._extract_distribution_source(message)
            if parsed is None:
                await message.reply(ux.admin.distribution_bad_source_text())
                return
            source_username, source_channel_id, source_message_id = parsed
            data = await state.get_data()
            groups: list[dict] = data.get("dist_groups", [])
            if not groups:
                await message.reply(ux.admin.distribution_error_no_groups_text())
                await state.clear()
                return
            mode = data.get("dist_mode", "create")
            pause_between_attempts_s = int(data.get("dist_pause_between_attempts_s", 60))
            delete_last_attempt = bool(data.get("dist_delete_last_attempt", False))
            pin_after_post = bool(data.get("dist_pin_after_post", False))
            num_attempt_for_pin_post = data.get("dist_num_attempt_for_pin_post")
            target_attempts = int(data.get("dist_target_attempts", 1))
            distribution_name = data.get("dist_name") or self._generate_distribution_name()
            notify_on_failure = bool(data.get("dist_notify_on_failure", True))
            group_ids = [UUID(group["id"]) for group in groups]
            deleted_count = 0
            if mode == "replace" and group_ids:
                deleted_count = await post_service.delete_active_by_groups(group_ids)

            created = 0
            skipped = 0
            errors: list[str] = []
            for group in groups:
                assigned_bot_id = group.get("assigned_bot_id")
                if not assigned_bot_id:
                    skipped += 1
                    continue
                try:
                    await post_service.create(
                        group_id=UUID(group["id"]),
                        target_chat_id=group["tg_chat_id"],
                        distribution_name=distribution_name,
                        source_channel_username=source_username,
                        source_channel_id=source_channel_id,
                        source_message_id=source_message_id,
                        bot_id=UUID(assigned_bot_id),
                        pause_between_attempts_s=pause_between_attempts_s,
                        delete_last_attempt=delete_last_attempt,
                        pin_after_post=pin_after_post,
                        num_attempt_for_pin_post=num_attempt_for_pin_post,
                        target_attempts=target_attempts,
                        notify_on_failure=notify_on_failure,
                    )
                    created += 1
                except Exception as exc:  # оставляю, чтобы не ломать твой UX
                    skipped += 1
                    errors.append(f"{group['tg_chat_id']}: {exc}")

            await state.clear()
            result_text = ux.admin.distribution_result_text(
                mode=mode,
                deleted_count=deleted_count,
                created=created,
                skipped=skipped,
                errors=errors,
            )
            keyboard = AdminInlineKeyboards.build_admin_distributions_menu_keyboard()
            await message.answer(result_text, reply_markup=keyboard)

    # ==========================
    # ХЕЛПЕРЫ
    # ==========================
    async def _render_bots_list(self, event: CallbackQuery | Message, ux: UXContext, *, page: int) -> None:
        view = await ux.admin.show_bots_list(page=page)
        keyboard = AdminInlineKeyboards.build_admin_bots_list_keyboard(view)
        await edit_message(event, view.text, reply_markup=keyboard)

    async def _render_bot_card(self, event: CallbackQuery | Message, ux: UXContext, bot_id: UUID, page: int) -> None:
        card = await ux.admin.show_bot_card(bot_id)
        keyboard = AdminInlineKeyboards.build_admin_bot_card_keyboard(card, page=page)
        await edit_message(event, card.text, reply_markup=keyboard)

    async def _render_groups_list(self, event: CallbackQuery | Message, ux: UXContext, *, page: int) -> None:
        view = await ux.admin.show_groups_list(page=page)
        keyboard = AdminInlineKeyboards.build_admin_groups_list_keyboard(view)
        await edit_message(event, view.text, reply_markup=keyboard)

    async def _render_group_card(self, event: CallbackQuery | Message, ux: UXContext, group_id: UUID, page: int) -> None:
        card = await ux.admin.show_group_card(group_id)
        keyboard = AdminInlineKeyboards.build_admin_group_card_keyboard(card, page=page)
        await edit_message(event, card.text, reply_markup=keyboard)

    async def _render_distributions_list(self, event: CallbackQuery | Message, ux: UXContext, *, page: int) -> None:
        view = await ux.admin.show_distributions_list(page=page)
        keyboard = AdminInlineKeyboards.build_admin_distributions_list_keyboard(view)
        await edit_message(event, view.text, reply_markup=keyboard)

    async def _render_distribution_card(
        self,
        event: CallbackQuery,
        ux: UXContext,
        distribution_id: UUID,
        *,
        page: int | None,
    ) -> None:
        try:
            card = await ux.admin.show_distribution_card(distribution_id)
        except ValueError as e:
            logger.error(f"Error rendering distribution card: {e}")
            if isinstance(event, CallbackQuery):
                await event.answer("Рассылка не найдена", show_alert=True)
            # Возвращаем пользователя к списку рассылок
            await self._render_distributions_list(event, ux, page=page or 1)
            return
        except Exception as e:
            logger.error(f"Unexpected error rendering distribution card: {e}", exc_info=True)
            if isinstance(event, CallbackQuery):
                await event.answer("Произошла ошибка при загрузке карточки", show_alert=True)
            # Возвращаем пользователя к списку рассылок
            await self._render_distributions_list(event, ux, page=page or 1)
            return
            
        keyboard = AdminInlineKeyboards.build_admin_distribution_card_keyboard(card, page=page)
        
        await edit_message(event, card.text, reply_markup=keyboard)

    async def _render_distribution_groups_list(
        self,
        event: CallbackQuery,
        ux: UXContext,
        distribution_id: UUID,
        *,
        page: int,
        card_page: int,
    ) -> None:
        try:
            view = await ux.admin.show_distribution_groups(distribution_id, page=page)
        except ValueError as exc:
            logger.error(f"Error rendering distribution groups list: {exc}")
            await event.answer("Рассылка не найдена", show_alert=True)
            return

        keyboard = AdminInlineKeyboards.build_admin_distribution_groups_keyboard(
            view,
            distribution_id=distribution_id,
            card_page=card_page,
            anchor_post_id=view.anchor_post_id,
        )
        await edit_message(event, view.text, reply_markup=keyboard)

    async def _prepare_bindings_pool(
        self,
        state: FSMContext,
        distribution_id: UUID,
        group_service: GroupService,
        bot_service: BotService,
        post_service: PostService,
        ux: UXContext,
    ) -> None:
        data = await state.get_data()
        if data.get("dist_edit_bindings_items"):
            return
        summary = await post_service.get_distribution_summary(distribution_id)
        if summary is None or summary.get("source_message_id") is None:
            return
        posts = await post_service.list_distribution_posts(
            source_channel_username=summary.get("source_channel_username"),
            source_channel_id=summary.get("source_channel_id"),
            source_message_id=summary.get("source_message_id"),
        )
        existing_ids = {str(post.group_id) for post in posts if post.group_id}
        groups = await group_service.list_bound(limit=2000)
        groups = await group_service.ensure_metadata_bulk(groups, bot_service)
        usage_map = await post_service.groups_distribution_usage([group.id for group in groups])
        items: list[dict[str, object]] = []
        for group in groups:
            if not group.assigned_bot_id:
                continue
            group_id_str = str(group.id)
            if group_id_str in existing_ids:
                continue
            status = "free"
            linked = usage_map.get(group.id)
            if linked and linked != distribution_id:
                status = "busy"
            elif linked == distribution_id:
                continue
            title = group.title or (group.username and f"@{group.username}") or str(group.tg_chat_id)
            items.append(
                {
                    "uuid": group_id_str,
                    "title": title,
                    "chat_id": group.tg_chat_id,
                    "status": status,
                }
            )
        await state.update_data(
            dist_edit_bindings_items=items,
            dist_edit_current_groups=list(existing_ids),
            dist_edit_bindings_selected=data.get("dist_edit_bindings_selected", []),
        )

    async def _render_bindings_selection(
        self,
        event: CallbackQuery,
        ux: UXContext,
        state: FSMContext,
        *,
        distribution_id: UUID,
        page: int,
    ) -> None:
        data = await state.get_data()
        items: list[dict] = data.get("dist_edit_bindings_items", [])
        groups_page = data.get("dist_edit_groups_page", 1) or 1
        card_page = data.get("dist_edit_card_page", 1) or 1
        if not items:
            keyboard = AdminInlineKeyboards.build_admin_distribution_groups_add_method_keyboard(
                distribution_id=distribution_id,
                groups_page=groups_page,
                card_page=card_page,
            )
            await edit_message(event, ux.admin.distribution_groups_add_not_found_text(), reply_markup=keyboard)
            return
        page_size = 6
        total_pages = max(1, math.ceil(len(items) / page_size))
        page = max(1, min(page, total_pages))
        start = (page - 1) * page_size
        subset = items[start:start + page_size]
        selected = set(data.get("dist_edit_bindings_selected", []))
        rows: list[tuple[str, str, bool]] = []
        for item in subset:
            status_icon = "🟢" if item.get("status") == "free" else "🟠"
            title = item.get("title") or "—"
            chat_id = item.get("chat_id")
            group_uuid = str(item.get("uuid"))
            label = f"{status_icon} {title} • {chat_id}"
            rows.append((group_uuid, label, group_uuid in selected))
        keyboard = AdminInlineKeyboards.build_admin_distribution_groups_bindings_keyboard(
            rows,
            distribution_id=distribution_id,
            page=page,
            total_pages=total_pages,
            groups_page=groups_page,
            card_page=card_page,
        )
        text_lines = [
            ux.admin.distribution_groups_add_bindings_intro_text(),
            ux.admin.distribution_groups_delete_hint_text(len(selected)),
        ]
        await edit_message(event, "\n\n".join(filter(None, text_lines)), reply_markup=keyboard)
        await state.update_data(dist_edit_bindings_page=page)

    async def _render_distribution_delete_mode(
        self,
        event: CallbackQuery,
        ux: UXContext,
        distribution_id: UUID,
        *,
        page: int,
        card_page: int,
        state: FSMContext,
    ) -> None:
        view = await ux.admin.show_distribution_groups(distribution_id, page=page)
        data = await state.get_data()
        selection = set(data.get("dist_delete_selection", []))
        text_lines = [
            ux.admin.distribution_groups_delete_intro_text(),
            ux.admin.distribution_groups_delete_hint_text(len(selection)),
            view.text,
        ]
        keyboard = AdminInlineKeyboards.build_admin_distribution_groups_delete_keyboard(
            view,
            distribution_id=distribution_id,
            card_page=card_page,
            selected_ids=selection,
        )
        await edit_message(event, "\n\n".join(filter(None, text_lines)), reply_markup=keyboard)
        await state.update_data(
            dist_edit_groups_page=view.page,
            dist_edit_card_page=card_page,
        )

    async def _render_distributions_menu(self, event: CallbackQuery | Message, ux: UXContext) -> None:
        text = ux.admin.distributions_menu_text()
        keyboard = AdminInlineKeyboards.build_admin_distributions_menu_keyboard()
        await edit_message(event, text, reply_markup=keyboard)

    async def _prompt_distribution_name(self, event: CallbackQuery | Message, ux: UXContext) -> None:
        text = ux.admin.distribution_name_prompt_text()
        keyboard = AdminInlineKeyboards.build_admin_distribution_name_keyboard()
        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        else:
            await edit_message(event, text, reply_markup=keyboard)

    async def _render_distribution_mode(self, event: CallbackQuery | Message, ux: UXContext, *, name: str | None = None) -> None:
        text = ux.admin.distribution_mode_prompt_text(name)
        keyboard = AdminInlineKeyboards.build_admin_distribution_mode_keyboard()
        await edit_message(event, text, reply_markup=keyboard)

    async def _render_distribution_target(self, event: CallbackQuery | Message, ux: UXContext, *, mode: str, name: str | None = None) -> None:
        text = ux.admin.distribution_target_prompt_text(mode, name)
        keyboard = AdminInlineKeyboards.build_admin_distribution_target_keyboard()
        await edit_message(event, text, reply_markup=keyboard)

    async def _prompt_distribution_groups_input(self, event: CallbackQuery | Message, ux: UXContext) -> None:
        text = ux.admin.distribution_groups_input_text()
        keyboard = AdminInlineKeyboards.build_admin_distribution_groups_input_keyboard()
        await edit_message(event, text, reply_markup=keyboard)

    async def _render_distribution_bot_select(self, event: CallbackQuery | Message, ux: UXContext, state: FSMContext, *, page: int) -> None:
        data = await state.get_data()
        bot_entries: list[dict] = data.get('dist_bot_list', [])
        selected_ids = set(data.get('dist_selected_bots', []))
        if not bot_entries:
            await edit_message(
                event,
                ux.admin.distribution_bot_selection_no_groups_text(),
                reply_markup=AdminInlineKeyboards.build_admin_distribution_target_keyboard(),
            )
            return

        page_size = 6
        total_pages = max(1, math.ceil(len(bot_entries) / page_size))
        page = max(1, min(page, total_pages))
        start = (page - 1) * page_size
        subset = bot_entries[start:start + page_size]
        items = [(entry['id'], entry['label'], entry['id'] in selected_ids) for entry in subset]
        keyboard = AdminInlineKeyboards.build_admin_distribution_bot_select_keyboard(items, page=page, total_pages=total_pages)

        text_lines = [ux.admin.distribution_bot_selection_intro()]
        text_lines.append(ux.admin.distribution_bot_selection_selected_text(len(selected_ids)))
        await edit_message(event, "\n\n".join(filter(None, text_lines)), reply_markup=keyboard)
        await state.update_data(dist_bot_page=page)

    async def _prompt_distribution_pause(self, event: CallbackQuery | Message, ux: UXContext, prefix: str | None = None) -> None:
        text = ux.admin.distribution_pause_prompt_text(prefix)
        keyboard = AdminInlineKeyboards.build_admin_distribution_source_keyboard()
        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        else:
            await edit_message(event, text, reply_markup=keyboard)

    async def _prompt_distribution_delete_last(self, event: CallbackQuery | Message, ux: UXContext) -> None:
        text = ux.admin.distribution_delete_last_prompt_text()
        keyboard = AdminInlineKeyboards.build_admin_distribution_boolean_keyboard(AdminDistributionsAction.SET_DELETE_LAST)
        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        else:
            await edit_message(event, text, reply_markup=keyboard)

    async def _prompt_distribution_pin(self, event: CallbackQuery | Message, ux: UXContext) -> None:
        text = ux.admin.distribution_pin_prompt_text()
        keyboard = AdminInlineKeyboards.build_admin_distribution_boolean_keyboard(AdminDistributionsAction.SET_PIN)
        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        else:
            await edit_message(event, text, reply_markup=keyboard)

    async def _prompt_distribution_pin_frequency(self, event: CallbackQuery | Message, ux: UXContext) -> None:
        text = ux.admin.distribution_pin_frequency_prompt_text()
        keyboard = AdminInlineKeyboards.build_admin_distribution_source_keyboard()
        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        else:
            await edit_message(event, text, reply_markup=keyboard)

    async def _prompt_distribution_target_attempts(self, event: CallbackQuery | Message, ux: UXContext) -> None:
        text = ux.admin.distribution_target_attempts_prompt_text()
        keyboard = AdminInlineKeyboards.build_admin_distribution_source_keyboard()
        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        else:
            await edit_message(event, text, reply_markup=keyboard)

    async def _prompt_distribution_source(self, event: CallbackQuery | Message, ux: UXContext, prefix: str) -> None:
        text = ux.admin.distribution_source_prompt(prefix)
        keyboard = AdminInlineKeyboards.build_admin_distribution_source_keyboard()
        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        else:
            await edit_message(event, text, reply_markup=keyboard)

    async def _resolve_distribution_id_from_callback(
        self,
        callback_data: AdminDistributionsCallback,
        post_service: PostService,
    ) -> UUID | None:
        if callback_data.distribution_id:
            return self._decode_distribution_id(callback_data.distribution_id)
        if callback_data.post_id:
            post_id = self._decode_post_id(callback_data.post_id)
            if post_id is None:
                return None
            return await post_service.resolve_distribution_id_by_post(post_id)
        return None

    def _pack_group_dto(self, group) -> dict[str, object]:
        assigned_bot_id = str(group.assigned_bot_id) if group.assigned_bot_id else None
        return {
            "id": str(group.id),
            "tg_chat_id": group.tg_chat_id,
            "assigned_bot_id": assigned_bot_id,
            "title": group.title or "",
            "username": getattr(group, "username", None) or "",
        }

    def _extract_distribution_source(self, message: Message) -> tuple[str, int, int] | None:
        if message.forward_from_chat and message.forward_from_message_id:
            chat = message.forward_from_chat
            if chat.type != ChatType.CHANNEL:
                return None
            username = chat.username or str(chat.id)
            channel_id = chat.id
            message_id = message.forward_from_message_id
            return username, channel_id, message_id
        return None

    def _parse_bool(self, value: str | None, *, default: bool | None = None) -> bool | None:
        if value is None:
            return default
        normalized = value.strip().lower()
        if not normalized:
            return default
        true_tokens = {"да", "yes", "y", "true", "1", "+"}
        false_tokens = {"нет", "no", "n", "false", "0", "-"}
        if normalized in true_tokens:
            return True
        if normalized in false_tokens:
            return False
        return None

    def _compose_distribution_config_summary(self, data: dict) -> str:
        pause = int(data.get("dist_pause_between_attempts_s", 60))
        delete_last = bool(data.get("dist_delete_last_attempt", False))
        pin_after = bool(data.get("dist_pin_after_post", False))
        frequency = data.get("dist_num_attempt_for_pin_post")
        attempts = int(data.get("dist_target_attempts", 1))

        lines: list[str] = [
            f"⏳ Пауза между попытками: {pause} с",
            f"♻️ Удалять предыдущее сообщение: {'да' if delete_last else 'нет'}",
        ]

        if pin_after:
            if frequency in (None, 0):
                freq_text = "каждую отправку"
            else:
                freq_text = f"каждое {frequency}-е сообщение"
            lines.append(f"📌 Закреплять: да ({freq_text})")
        else:
            lines.append("📌 Закреплять: нет")

        attempts_text = "бесконечно" if attempts == -1 else str(attempts)
        lines.append(f"🎯 Количество попыток: {attempts_text}")
        return "\n".join(lines)

    async def _load_bots(self, bot_service: BotService, bot_ids: set[UUID]) -> dict[UUID, BotDTO | None]:
        out: dict[UUID, BotDTO | None] = {}
        for bot_id in bot_ids:
            bot = await bot_service.get(bot_id)
            out[bot_id] = bot
        return out

    def _generate_distribution_name(self) -> str:
        return datetime.now().strftime("Рассылка %d.%m %H:%M")

    def _decode_distribution_id(self, value: str) -> UUID | None:
        return self._decode_uuid_token(value, "distribution")

    def _decode_post_id(self, value: str) -> UUID | None:
        return self._decode_uuid_token(value, "post")

    def _decode_group_id(self, value: str) -> UUID | None:
        return self._decode_uuid_token(value, "group")

    def _decode_uuid_token(self, value: str, label: str) -> UUID | None:
        try:
            padded = value + "=" * (-len(value) % 4)
            return UUID(bytes=base64.urlsafe_b64decode(padded.encode()))
        except (ValueError, TypeError) as exc:
            logger.error("Error decoding %s ID: %s", label, exc)
            return None

    async def _get_distribution_id_from_state(self, state: FSMContext) -> UUID | None:
        data = await state.get_data()
        dist_raw = data.get("dist_edit_distribution")
        if not dist_raw:
            return None
        try:
            return UUID(dist_raw)
        except ValueError:
            return None
