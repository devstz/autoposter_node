from aiogram.filters import BaseFilter
from aiogram.types import Update


class ChatTypeFilter(BaseFilter):
    def __init__(self, *chat_types: str):
        self.chat_types = list(chat_types)

    async def __call__(self, update: Update) -> bool: # noqa: C901
        chat = None

        if hasattr(update, 'chat') and update.chat: # type: ignore
            chat =  update.chat # type: ignore
        elif hasattr(update, "message") and update.message:
            chat = update.message.chat
        elif hasattr(update, "edited_message") and update.edited_message:
            chat = update.edited_message.chat
        elif hasattr(update, "channel_post") and update.channel_post:
            chat = update.channel_post.chat
        elif hasattr(update, "edited_channel_post") and update.edited_channel_post:
            chat = update.edited_channel_post.chat
        elif hasattr(update, "callback_query") and update.callback_query and update.callback_query.message:
            chat = update.callback_query.message.chat
        elif hasattr(update, "my_chat_member") and update.my_chat_member:
            chat = update.my_chat_member.chat
        elif hasattr(update, "chat_member") and update.chat_member:
            chat = update.chat_member.chat
        elif hasattr(update, "chat_join_request") and update.chat_join_request:
            chat = update.chat_join_request.chat

        if chat:
            return chat.type in self.chat_types

        return False
