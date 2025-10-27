from typing import List

from aiogram.dispatcher.event.telegram import TelegramEventObserver

from .chat_type_filter import ChatTypeFilter


def connect_chat_type_filter(observers: List[TelegramEventObserver], *chat_types: str):
    for observer in observers:
        observer.filter(ChatTypeFilter(*chat_types))
