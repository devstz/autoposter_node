from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode


def create_bot(token: str, session: AiohttpSession | None = None):
    return Bot(
        token=token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True
        ),
        session=session
    )
