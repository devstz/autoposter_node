from __future__ import annotations

from logging import getLogger
from pathlib import Path
from aiogram.enums.chat_type import ChatType

from .base import BaseRouter

logger = getLogger('ExampleRouter')

class ExampleRouter(BaseRouter):
    chat_types = ChatType.PRIVATE

    def setup_middlewares(self):
        pass

    def setup_handlers(self):
        pass