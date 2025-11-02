from __future__ import annotations

import math
from typing import Any, Dict
from uuid import UUID

from common.dto import PostDTO, PostListItemDTO, PostsListViewDTO, GroupDTO
from services import PostService, SettingsService, GroupService, BotService


class ShowPostsListUseCase:
    def __init__(
        self,
        *,
        post_service: PostService,
        settings_service: SettingsService,
        group_service: GroupService,
        bot_service: BotService,
        texts: Dict[str, Any],
        pagination_texts: Dict[str, str],
    ) -> None:
        self._post_service = post_service
        self._settings_service = settings_service
        self._group_service = group_service
        self._bot_service = bot_service
        self._texts = texts
        self._pagination_texts = pagination_texts

    async def __call__(self, status: str, page: int = 1) -> PostsListViewDTO:
        settings = await self._settings_service.get_current()
        if settings is None:
            raise RuntimeError("Settings profile is not configured")

        page_size = max(1, settings.pagination_size)
        total = await self._post_service.count_by_status(status)
        status_label = self._texts["status_labels"].get(status, status)

        if total == 0:
            text = "\n".join(
                [
                    self._texts["list_title"].format(status=status_label),
                    self._texts["list_empty"],
                ]
            )
            return PostsListViewDTO(
                text=text,
                items=[],
                status=status,
                page=1,
                total_pages=1,
                total_items=0,
            )

        total_pages = max(1, math.ceil(total / page_size))
        page = min(max(1, page), total_pages)

        posts = await self._post_service.list_by_status(status, limit=page_size, offset=(page - 1) * page_size)
        await self._ensure_groups_metadata(posts)
        items = [self._build_item(post) for post in posts]

        text_lines = [self._texts["list_title"].format(status=status_label)]
        list_hint = self._texts.get("list_hint")
        if list_hint:
            text_lines.append(list_hint)
        text_lines.append(self._pagination_texts["label"].format(current=page, total=total_pages))
        text = "\n".join(text_lines)

        return PostsListViewDTO(
            text=text,
            items=items,
            status=status,
            page=page,
            total_pages=total_pages,
            total_items=total,
        )

    def _build_item(self, post: PostDTO) -> PostListItemDTO:
        status_short = self._texts["status_short"].get(post.status, post.status)
        source = self._texts["item_source_template"].format(
            username=post.source_channel_username,
            message_id=post.source_message_id,
        )
        group_title = self._resolve_group_title(post)
        group_chat_id = post.group_chat_id or "—"
        target = self._texts["item_target_template"].format(
            title=group_title,
            chat_id=group_chat_id,
        )
        bot_label = self._format_bot(post)

        label = self._texts["item_template"].format(
            status=status_short,
            source=source,
            target=target,
            bot=bot_label,
        )
        return PostListItemDTO(
            post_id=post.id,
            label=label,
            status=post.status,
            bot_id=post.bot_id,
            group_id=post.group_id,
        )

    def _format_bot(self, post: PostDTO) -> str:
        if post.bot_name and post.bot_username:
            return f"{post.bot_name} (@{post.bot_username})"
        if post.bot_name:
            return post.bot_name
        if post.bot_username:
            return f"@{post.bot_username}"
        return self._texts["item_bot_placeholder"]

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
        return self._texts["item_group_placeholder"]
