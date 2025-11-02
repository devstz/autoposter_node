from __future__ import annotations

import math
from typing import Dict, Optional
from uuid import UUID

from common.dto import DistributionGroupListItemDTO, DistributionGroupsViewDTO, PostDTO, GroupDTO
from services import PostService, SettingsService, GroupService, BotService


class ShowDistributionGroupsUseCase:
    def __init__(
        self,
        *,
        post_service: PostService,
        settings_service: SettingsService,
        group_service: GroupService,
        bot_service: BotService,
        texts: Dict[str, str],
        pagination_texts: Dict[str, str],
        status_short_texts: Dict[str, str],
    ) -> None:
        self._post_service = post_service
        self._settings_service = settings_service
        self._group_service = group_service
        self._bot_service = bot_service
        self._texts = texts
        self._pagination_texts = pagination_texts
        self._status_short_texts = status_short_texts

    async def __call__(self, distribution_id: UUID, page: int = 1) -> DistributionGroupsViewDTO:
        summary = await self._post_service.get_distribution_summary(distribution_id)
        if summary is None:
            raise ValueError("Distribution not found")

        settings = await self._settings_service.get_current()
        if settings is None:
            raise RuntimeError("Settings profile is not configured")

        posts = await self._post_service.list_distribution_posts(
            source_channel_username=summary.get("source_channel_username"),
            source_channel_id=summary.get("source_channel_id"),
            source_message_id=summary.get("source_message_id"),
        )
        await self._ensure_groups_metadata(posts)

        total = len(posts)
        page_size = max(1, settings.pagination_size)

        if total == 0:
            text = "\n".join(
                [
                    self._texts.get("groups_list_title", ""),
                    self._texts.get("groups_list_empty", ""),
                ]
            ).strip()
            return DistributionGroupsViewDTO(
                text=text or self._texts.get("groups_list_empty", "Нет групп."),
                items=[],
                page=1,
                total_pages=1,
                total_items=0,
                anchor_post_id=None,
            )

        total_pages = max(1, math.ceil(total / page_size))
        page = min(max(1, page), total_pages)
        start = (page - 1) * page_size
        end = start + page_size
        page_posts = posts[start:end]

        anchor_post_id: Optional[UUID] = None
        if posts:
            anchor_post_id = min((post.id for post in posts), key=lambda value: str(value))

        items = [self._build_item(post) for post in page_posts]

        header_lines = [
            self._texts.get("groups_list_title", ""),
        ]
        hint = self._texts.get("groups_list_hint")
        if hint:
            header_lines.append(hint)
        header_lines.append(
            self._pagination_texts["label"].format(current=page, total=total_pages)
        )

        text = "\n".join(line for line in header_lines if line)

        return DistributionGroupsViewDTO(
            text=text,
            items=items,
            page=page,
            total_pages=total_pages,
            total_items=total,
            anchor_post_id=anchor_post_id,
        )

    def _build_item(self, post: PostDTO) -> DistributionGroupListItemDTO:
        marker = self._status_short_texts.get(post.status, post.status[:1].upper())
        title = post.group_title or self._texts.get("groups_item_title_placeholder", "Без названия")
        chat_id = post.group_chat_id or post.target_chat_id
        chat_label = self._texts.get("groups_item_chat_template", "{chat_id}").format(chat_id=chat_id)
        bot_label = self._format_bot(post)
        label = self._texts.get("groups_item_template", "{marker} {title} • {chat} • {bot}").format(
            marker=marker,
            title=title,
            chat=chat_label,
            bot=bot_label,
        )
        return DistributionGroupListItemDTO(
            post_id=post.id,
            group_id=post.group_id,
            label=label,
            status=post.status,
        )

    def _format_bot(self, post: PostDTO) -> str:
        template = self._texts.get("groups_item_bot_template", "{value}")
        placeholder = self._texts.get("groups_item_bot_placeholder", "—")
        if post.bot_name and post.bot_username:
            value = f"{post.bot_name} (@{post.bot_username})"
        elif post.bot_name:
            value = post.bot_name
        elif post.bot_username:
            value = f"@{post.bot_username}"
        else:
            value = placeholder
        return template.format(value=value)

    async def _ensure_groups_metadata(self, posts: list[PostDTO]) -> None:
        group_ids = {post.group_id for post in posts if post.group_id}
        if not group_ids:
            return
        groups: dict[UUID, GroupDTO] = {}
        for group_id in group_ids:
            group = await self._group_service.get(group_id)
            if group is None:
                continue
            group = await self._group_service.ensure_metadata(group, self._bot_service)
            groups[group_id] = group
        for post in posts:
            if not post.group_id:
                continue
            group = groups.get(post.group_id)
            if not group:
                continue
            if group.title:
                post.group_title = group.title
            if getattr(group, "username", None):
                post.group_username = group.username
            if group.tg_chat_id and not post.group_chat_id:
                post.group_chat_id = group.tg_chat_id

    def _resolve_group_title(self, post: PostDTO) -> str:
        if post.group_title:
            return post.group_title
        if post.group_username:
            return f"@{post.group_username}"
        return self._texts.get("groups_item_title_placeholder", "Без названия")
