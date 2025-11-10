from enum import Enum
from typing import Optional


class TelegramErrorType(str, Enum):
    """Типы критических ошибок Telegram, требующих удаления группы"""
    CHAT_NOT_FOUND = "chat_not_found"
    BOT_KICKED = "bot_kicked"
    BOT_BLOCKED = "bot_blocked"
    FORBIDDEN = "forbidden"
    USER_DEACTIVATED = "user_deactivated"
    UNKNOWN = "unknown"


def classify_telegram_error(exception: Exception) -> TelegramErrorType:
    """
    Классифицирует исключение Telegram для определения критичности
    
    Критические ошибки (требуют удаления группы):
    - CHAT_NOT_FOUND: чат удален
    - BOT_KICKED: бот кикнут из группы
    - BOT_BLOCKED: бот заблокирован
    - FORBIDDEN: нет доступа
    - USER_DEACTIVATED: пользователь деактивирован
    
    Args:
        exception: Исключение от aiogram
        
    Returns:
        TelegramErrorType: Тип ошибки
    """
    error_str = str(exception).lower()
    error_type_name = type(exception).__name__
    
    # Проверка по типу исключения
    if error_type_name == "ChatNotFound":
        return TelegramErrorType.CHAT_NOT_FOUND
    
    # Проверка по тексту ошибки
    if "chat not found" in error_str:
        return TelegramErrorType.CHAT_NOT_FOUND
    
    if "bot was kicked" in error_str:
        return TelegramErrorType.BOT_KICKED
    
    if "bot was blocked" in error_str or "bot is blocked" in error_str:
        return TelegramErrorType.BOT_BLOCKED
    
    if "user is deactivated" in error_str or "user_deactivated" in error_str:
        return TelegramErrorType.USER_DEACTIVATED
    
    if "forbidden" in error_str and error_type_name == "TelegramForbiddenError":
        return TelegramErrorType.FORBIDDEN
    
    return TelegramErrorType.UNKNOWN


def is_critical_error(error_type: TelegramErrorType) -> bool:
    """
    Проверяет, является ли ошибка критической (требует удаления группы)
    
    Args:
        error_type: Тип ошибки
        
    Returns:
        bool: True если ошибка критическая
    """
    return error_type in {
        TelegramErrorType.CHAT_NOT_FOUND,
        TelegramErrorType.BOT_KICKED,
        TelegramErrorType.BOT_BLOCKED,
        TelegramErrorType.FORBIDDEN,
        TelegramErrorType.USER_DEACTIVATED,
    }

